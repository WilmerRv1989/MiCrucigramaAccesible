# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Prepara el banco de palabras y pistas del crucigrama.

Se usa una sola vez (o cuando cambian las pistas), desde la raíz del repositorio:

	uv run python herramientas/preparar_banco.py candidatos VOLCADO.xml.bz2 FRECUENCIAS.txt SALIDA.tsv
	uv run python herramientas/preparar_banco.py construir
	uv run python herramientas/preparar_banco.py muestra [cantidad] [semilla]

1. candidatos: cruza la lista de frecuencias (FrequencyWords, CC BY-SA 4.0) con el volcado del
   Wikcionario en español (CC BY-SA 4.0). Deja las palabras comunes de 3 a 10 letras que son
   sustantivos, adjetivos, verbos en infinitivo o adverbios, en orden de frecuencia, con sus
   definiciones limpias. Ni el volcado ni la lista se suben al repositorio.
2. A partir de esas definiciones se escriben a mano las pistas cortas en banco_fuente/*.tsv.
3. construir: comprueba las pistas (ninguna contiene su propia palabra) y escribe los JSON
   del complemento en addon/globalPlugins/miCrucigramaAccesible/banco/.
4. muestra: unas cuantas pistas generales al azar, para revisarlas con calma.
"""

import bz2
import csv
import os
import random
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_RAIZ, "addon", "globalPlugins", "miCrucigramaAccesible"))

from crucigrama import banco  # noqa: E402
from crucigrama.banco import Dificultad, Entrada  # noqa: E402
from crucigrama.generador import largos  # noqa: E402
from crucigrama.texto import normalizar  # noqa: E402

FUENTE = os.path.join(_RAIZ, "banco_fuente")
DESTINO = os.path.join(_RAIZ, "addon", "globalPlugins", "miCrucigramaAccesible", "banco")

# Categorías del Wikcionario que pueden ser palabras del crucigrama (lo demás son formas
# conjugadas o plurales, nombres propios, siglas, locuciones...).
_CATEGORIAS = re.compile(r"^(sustantivo (masculino|femenino|ambiguo|neutro)|adjetivo|verbo|adverbio)")
# Usos que no queremos en un juego para todas las edades, o que la mayoría no conoce.
# Si la palabra es también una de estas, es una palabra gramatical («pero», «este», «como»...),
# aunque tenga alguna acepción rara como sustantivo.
_GRAMATICALES = re.compile(
	r"^(pronombre|preposición|conjunción|artículo|interjección|contracción|"
	r"adjetivo (demostrativo|posesivo|indefinido|interrogativo|exclamativo|relativo|cardinal|ordinal)|"
	r"adverbio (relativo|interrogativo|exclamativo|comparativo|de negación|de afirmación))",
)
_USOS_FUERA = (
	"malsonante",
	"vulgar",
	"despectivo",
	"peyorativo",
	"obsceno",
	"obsoleto",
	"desusado",
	"anticuado",
	"germanía",
	"jergal",
	"lunfardismo",
	"sexual",
	"insulto",
)
_TEMAS_FUERA = ("sexualidad", "drogas", "insultos")


@dataclass
class Acepcion:
	categoria: str
	definicion: str
	notas: str  # uso, ámbito y tema, para decidir a mano


# --- Limpieza del código wiki ---

_REF = re.compile(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", re.S)
_ENLACE = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]")
_PLANTILLA = re.compile(r"\{\{([^{}]*)\}\}")
_PLANTILLAS_CON_TEXTO = {"plm", "l", "l+", "impropia", "csem2", "nombre científico", "neologismo"}


def _plantilla(coincidencia: re.Match[str]) -> str:
	partes = [p for p in coincidencia.group(1).split("|") if "=" not in p]
	nombre = partes[0].strip().lower()
	if nombre == "plm":
		return partes[1] if len(partes) > 1 else ""
	if nombre in ("l", "l+") and len(partes) > 2:
		return partes[2]
	if nombre in _PLANTILLAS_CON_TEXTO and len(partes) > 1:
		return partes[-1]
	return ""


def limpiar(texto: str) -> str:
	texto = _REF.sub("", texto)
	for _ in range(3):
		texto = _PLANTILLA.sub(_plantilla, texto)
	texto = _ENLACE.sub(r"\1", texto)
	texto = texto.replace("'''", "").replace("''", "")
	texto = re.sub(r"<[^>]+>", "", texto)
	texto = re.sub(r"\s+", " ", texto).strip(" .;:")
	return texto[:1].upper() + texto[1:]


def _plantillas_de(linea: str, nombre: str) -> list[str]:
	return [m.group(1) for m in re.finditer(r"\{\{" + nombre + r"\|([^{}]*)\}\}", linea)]


def acepciones_en_espanol(texto: str) -> list[Acepcion]:
	"""Las acepciones de la sección en español de una página del Wikcionario."""
	inicio = texto.find("{{lengua|es}}")
	if inicio < 0:
		return []
	fin = texto.find("\n== ", inicio)
	seccion = texto[inicio : fin if fin > 0 else len(texto)]
	for cabecera in re.finditer(r"^===+\s*\{\{([^|}]+)", seccion, re.M):
		if _GRAMATICALES.match(cabecera.group(1).strip().lower()):
			return []
	acepciones: list[Acepcion] = []
	categoria = ""
	actual: Acepcion | None = None
	for linea in seccion.splitlines():
		cabecera = re.match(r"^===+\s*\{\{([^|}]+)", linea)
		if cabecera:
			categoria = cabecera.group(1).strip().lower()
			actual = None
			continue
		if linea.startswith("=="):
			categoria = ""
			actual = None
			continue
		if not _CATEGORIAS.match(categoria):
			continue
		definicion = re.match(r"^;\s*\d+[^:]*:\s*(.*)$", linea)
		if definicion:
			temas = " ".join(_plantillas_de(linea, "csem"))
			actual = Acepcion(categoria, limpiar(definicion.group(1)), f"tema={temas}" if temas else "")
			acepciones.append(actual)
			continue
		if actual is not None:
			for nombre in ("uso", "ámbito"):
				for valor in _plantillas_de(linea, nombre):
					actual.notas += f" {nombre}={valor}"
	return acepciones


def aceptable(acepcion: Acepcion, palabra: str) -> bool:
	notas = acepcion.notas.lower()
	if any(u in notas for u in _USOS_FUERA) or any(t in notas for t in _TEMAS_FUERA):
		return False
	definicion = acepcion.definicion
	if len(definicion) < 4 or "{" in definicion or "|" in definicion:
		return False
	if categoria_verbal_conjugada(acepcion, palabra):
		return False
	return not contiene_la_palabra(definicion, palabra)


def categoria_verbal_conjugada(acepcion: Acepcion, palabra: str) -> bool:
	"""Los verbos solo valen en infinitivo."""
	return acepcion.categoria.startswith("verbo") and not re.search(r"(ar|er|ir|ír)$", palabra)


def raiz(palabra: str) -> str:
	"""Una raíz aproximada: la palabra sin tildes, sin las últimas letras si es larga."""
	clave = normalizar(palabra)
	return clave[: max(4, len(clave) - 3)] if len(clave) > 5 else clave


def contiene_la_palabra(texto: str, palabra: str) -> bool:
	"""Si la pista contiene la palabra o su raíz (una pista circular no ayuda)."""
	buscada = raiz(palabra)
	for trozo in re.findall(r"[^\W\d_]+", texto):
		if normalizar(trozo).startswith(buscada):
			return True
	return False


# --- Candidatos ---


def paginas(ruta: str) -> Iterator[tuple[str, str]]:
	with bz2.open(ruta, "rb") as archivo:
		for _, elemento in ET.iterparse(archivo, events=("end",)):
			if elemento.tag.endswith("}page"):
				prefijo = elemento.tag[:-4]
				titulo = elemento.findtext(f"{prefijo}ns") == "0" and elemento.findtext(f"{prefijo}title")
				texto = elemento.findtext(f".//{prefijo}text")
				if titulo and texto:
					yield titulo, texto
				elemento.clear()


def candidatos(volcado: str, frecuencias: str, salida: str) -> None:
	orden: dict[str, int] = {}
	with open(frecuencias, encoding="utf-8") as archivo:
		for numero, linea in enumerate(archivo, start=1):
			palabra = linea.split(" ")[0].strip()
			if palabra == palabra.lower() and 3 <= len(normalizar(palabra)) <= 10 and palabra not in orden:
				orden[palabra] = numero
	encontradas: list[tuple[int, str, list[Acepcion]]] = []
	for titulo, texto in paginas(volcado):
		if titulo in orden:
			acepciones = [a for a in acepciones_en_espanol(texto) if aceptable(a, titulo)]
			if acepciones:
				encontradas.append((orden[titulo], titulo, acepciones))
	encontradas.sort()
	with open(salida, "w", encoding="utf-8", newline="") as archivo:
		escritor = csv.writer(archivo, delimiter="\t", lineterminator="\n")
		escritor.writerow(["posicion", "frecuencia", "palabra", "categoria", "definiciones"])
		for posicion, (frecuencia, palabra, acepciones) in enumerate(encontradas, start=1):
			definiciones = " || ".join(
				f"{a.definicion}" + (f" [{a.notas.strip()}]" if a.notas.strip() else "")
				for a in acepciones[:4]
			)
			escritor.writerow([posicion, frecuencia, palabra, acepciones[0].categoria, definiciones])
	print(f"{len(encontradas)} palabras con definición de {len(orden)} de la lista de frecuencias.")


# --- Construir el banco ---


def leer_fuente(nombre: str) -> list[Entrada]:
	"""Lee un archivo de banco_fuente: palabra, pista, dificultad, directa (sí/no), tema, origen."""
	entradas: list[Entrada] = []
	with open(os.path.join(FUENTE, nombre), encoding="utf-8") as archivo:
		for numero, fila in enumerate(csv.reader(archivo, delimiter="\t"), start=1):
			if not fila or fila[0].startswith("#") or fila[0] == "palabra":
				continue
			if len(fila) != 6:
				raise ValueError(f"{nombre}, línea {numero}: hacen falta 6 columnas y hay {len(fila)}")
			palabra, pista, dificultad, directa, tema, origen = (c.strip() for c in fila)
			entradas.append(
				banco.entrada_desde_dict(
					{
						"palabra": palabra,
						"pista": pista,
						"dificultad": dificultad,
						"directa": directa == "sí",
						"tema": tema or None,
						"origen": origen,
					},
				),
			)
	return entradas


def comprobar(entradas: list[Entrada], nombre: str) -> list[str]:
	problemas: list[str] = []
	vistas: set[tuple[str, str | None]] = set()
	for entrada in entradas:
		if (entrada.clave, entrada.tema) in vistas:
			problemas.append(f"{nombre}: {entrada.palabra} está repetida")
		vistas.add((entrada.clave, entrada.tema))
		if contiene_la_palabra(entrada.pista, entrada.palabra):
			problemas.append(f"{nombre}: la pista de {entrada.palabra} contiene la palabra: {entrada.pista}")
		if len(entrada.pista) > 90:
			problemas.append(f"{nombre}: la pista de {entrada.palabra} es muy larga ({len(entrada.pista)})")
		# La primera letra va en mayúscula, aunque la pista empiece con comillas o con «¡».
		primera = entrada.pista.lstrip('«¡¿"')[:1]
		if not primera.isupper() or entrada.pista.endswith("."):
			problemas.append(
				f"{nombre}: la pista de {entrada.palabra} debe empezar en mayúscula y sin punto final",
			)
	return problemas


def leer_banco(nombre: str) -> list[Entrada]:
	"""Todas las entradas de un banco, que puede estar repartido en varios archivos (general_01.tsv...)."""
	entradas: list[Entrada] = []
	for archivo in sorted(os.listdir(FUENTE)):
		if archivo.endswith(".tsv") and archivo.split("_")[0].removesuffix(".tsv") == nombre:
			entradas += leer_fuente(archivo)
	return entradas


def construir() -> None:
	os.makedirs(DESTINO, exist_ok=True)
	problemas: list[str] = []
	nombres = sorted({a.split("_")[0].removesuffix(".tsv") for a in os.listdir(FUENTE) if a.endswith(".tsv")})
	for nombre in nombres:
		entradas = leer_banco(nombre)
		problemas += comprobar(entradas, nombre)
		for entrada in entradas:
			minimo, maximo = largos(entrada.dificultad)
			if entrada.tema is None and not minimo <= len(entrada.clave) <= maximo:
				problemas.append(
					f"{nombre}: {entrada.palabra} no cabe en el largo de {entrada.dificultad.value}",
				)
		banco.guardar(os.path.join(DESTINO, f"{nombre}.json"), entradas)
		por_nivel = {d.value: sum(1 for e in entradas if e.dificultad is d) for d in Dificultad}
		print(f"{nombre}: {len(entradas)} entradas {por_nivel}")
	for problema in problemas:
		print(problema)
	if problemas:
		sys.exit(1)


def muestra(cantidad: int, semilla: int) -> None:
	entradas = leer_banco("general")
	for entrada in random.Random(semilla).sample(entradas, min(cantidad, len(entradas))):
		print(f"{entrada.palabra} ({entrada.dificultad.value}): {entrada.pista}")


def main() -> None:
	sys.stdout.reconfigure(encoding="utf-8")  # pyright: ignore[reportAttributeAccessIssue]
	orden, *argumentos = sys.argv[1:]
	if orden == "candidatos":
		candidatos(*argumentos)
	elif orden == "construir":
		construir()
	elif orden == "muestra":
		muestra(int(argumentos[0]) if argumentos else 100, int(argumentos[1]) if len(argumentos) > 1 else 1)
	else:
		sys.exit(__doc__)


if __name__ == "__main__":
	main()

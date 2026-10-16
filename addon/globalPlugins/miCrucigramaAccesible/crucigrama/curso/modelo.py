# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Bloques, lecciones y ejercicios del curso, leídos de los archivos JSON de `lecciones/<idioma>/`.

Cada archivo es un bloque. Cada ejercicio trae su crucigrama hecho a mano:

	"palabras": [{"palabra": "sol", "pista": "...", "fila": 1, "columna": 1, "direccion": "horizontal"}]

Las filas y las columnas cuentan desde 1, y el tablero empieza en la fila 1 y la columna 1.
Los números de las palabras se ponen solos, en orden de lectura, como en el juego.

- «escritas»: palabras que ya están escritas al empezar.
- «letras»: letras sueltas ya escritas, [fila, columna, letra]; pueden estar mal a propósito.
- «objetivos»: palabras que hay que dejar bien escritas; «casillas»: casillas sueltas, [fila, columna].
- «inicio»: [fila, columna, dirección] donde empieza el cursor.

Los crucigramas enteros (bloque C) los escribe `herramientas/preparar_lecciones.py` a partir de su
campo «generar» (tema, tamaño, dificultad y semilla). Al cargar el curso, ese campo solo indica
que el ejercicio es un crucigrama entero.
"""

import glob
import json
import os
from dataclasses import dataclass

from ..banco import Dificultad, Entrada
from ..generador import Casilla, Crucigrama, Direccion, Tamano, numerar
from ..texto import normalizar_letra

CARPETA_LECCIONES = os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"lecciones",
)
IDIOMA_POR_DEFECTO = "es"


@dataclass(frozen=True)
class Ejercicio:
	id: str
	crucigrama: Crucigrama
	# Letras ya escritas al empezar (casillas desde 0).
	letras: tuple[tuple[Casilla, str], ...]
	# Casillas que tienen que quedar con su letra buena.
	objetivos: tuple[Casilla, ...]
	inicio: Casilla
	direccion: Direccion
	instruccion: str
	# Un crucigrama entero: las estrellas dependen de cuántas ayudas se piden, y se guarda a medias.
	entero: bool = False


@dataclass(frozen=True)
class Leccion:
	id: str
	titulo: str
	explicacion: tuple[str, ...]
	ejercicios: tuple[Ejercicio, ...]

	@property
	def estrellas_posibles(self) -> int:
		return 3 * len(self.ejercicios)


@dataclass(frozen=True)
class Bloque:
	id: str
	titulo: str
	mensaje_final: str
	lecciones: tuple[Leccion, ...]


class Curso:
	def __init__(self, bloques: list[Bloque]) -> None:
		self.bloques = bloques
		self.lecciones = [leccion for bloque in bloques for leccion in bloque.lecciones]

	def bloque_de(self, leccion: Leccion) -> Bloque:
		return next(bloque for bloque in self.bloques if leccion in bloque.lecciones)

	def siguiente(self, leccion: Leccion) -> Leccion | None:
		indice = self.lecciones.index(leccion)
		return self.lecciones[indice + 1] if indice + 1 < len(self.lecciones) else None


def _casilla(datos: list, id_ejercicio: str) -> Casilla:
	fila, columna = int(datos[0]), int(datos[1])
	if fila < 1 or columna < 1:
		raise ValueError(f"Ejercicio {id_ejercicio}: casilla fuera del tablero: {datos}")
	return (fila - 1, columna - 1)


def _ejercicio(datos: dict) -> Ejercicio:
	id_ejercicio = str(datos["id"])
	puestas = []
	por_palabra: dict[str, list[Casilla]] = {}
	for p in datos["palabras"]:
		entrada = Entrada(str(p["palabra"]), str(p["pista"]), Dificultad.FACIL)
		inicio = _casilla([p["fila"], p["columna"]], id_ejercicio)
		direccion = Direccion(p["direccion"])
		puestas.append((entrada, inicio, direccion))
		df, dc = direccion.paso
		por_palabra[entrada.clave] = [
			(inicio[0] + df * i, inicio[1] + dc * i) for i in range(len(entrada.clave))
		]
	if min(f for _, (f, _c), _d in puestas) != 0 or min(c for _, (_f, c), _d in puestas) != 0:
		raise ValueError(
			f"Ejercicio {id_ejercicio}: el tablero tiene que empezar en la fila 1 y la columna 1",
		)
	crucigrama = numerar(puestas, Tamano.PEQUENO, Dificultad.FACIL, 0, None)
	letras: dict[Casilla, str] = {}
	for palabra in datos.get("escritas", []):
		clave = Entrada(palabra, "-", Dificultad.FACIL).clave
		for casilla, letra in zip(por_palabra[clave], clave):
			letras[casilla] = letra
	for f, c, letra in datos.get("letras", []):
		letras[_casilla([f, c], id_ejercicio)] = normalizar_letra(letra)
	objetivos: list[Casilla] = []
	for palabra in datos.get("objetivos", []):
		objetivos += por_palabra[Entrada(palabra, "-", Dificultad.FACIL).clave]
	objetivos += [_casilla(c, id_ejercicio) for c in datos.get("casillas", [])]
	if not objetivos:
		raise ValueError(f"Ejercicio {id_ejercicio}: no tiene objetivos")
	fila, columna, direccion = datos["inicio"]
	return Ejercicio(
		id=id_ejercicio,
		crucigrama=crucigrama,
		letras=tuple(sorted(letras.items())),
		objetivos=tuple(dict.fromkeys(objetivos)),
		inicio=_casilla([fila, columna], id_ejercicio),
		direccion=Direccion(direccion),
		instruccion=str(datos["instruccion"]),
		entero="generar" in datos,
	)


def _leccion(datos: dict) -> Leccion:
	return Leccion(
		id=str(datos["id"]),
		titulo=str(datos["titulo"]),
		explicacion=tuple(datos["explicacion"]),
		ejercicios=tuple(_ejercicio(e) for e in datos["ejercicios"]),
	)


def carpeta_de_idioma(idioma: str) -> str:
	"""La carpeta de lecciones del idioma, o la del idioma por defecto si no existe."""
	for codigo in (idioma, idioma.split("_")[0], IDIOMA_POR_DEFECTO):
		carpeta = os.path.join(CARPETA_LECCIONES, codigo)
		if os.path.isdir(carpeta):
			return carpeta
	return os.path.join(CARPETA_LECCIONES, IDIOMA_POR_DEFECTO)


def cargar_curso(carpeta: str) -> Curso:
	bloques = []
	for ruta in sorted(glob.glob(os.path.join(carpeta, "bloque_*.json"))):
		with open(ruta, encoding="utf-8") as archivo:
			datos = json.load(archivo)
		bloques.append(
			Bloque(
				id=str(datos["id"]),
				titulo=str(datos["titulo"]),
				mensaje_final=str(datos["mensaje_final"]),
				lecciones=tuple(_leccion(leccion) for leccion in datos["lecciones"]),
			),
		)
	return Curso(bloques)

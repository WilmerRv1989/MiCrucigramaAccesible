# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Banco de palabras y pistas.

El banco está en archivos JSON preparados de antemano (ver herramientas/), con esta forma:

	{"version":1,"entradas":[
	{"palabra":"canción","pista":"Música con letra para cantar","dificultad":"facil"},
	{"palabra":"oriente","pista":"Por donde sale el sol","dificultad":"normal","directa":false}
	]}

- palabra: como se escribe en español, con sus tildes; la voz la lee así.
- dificultad: lo común que es la palabra (facil, normal o dificil).
- directa: si la pista describe la palabra sin rodeos («Animal que ladra») o con un giro (false).
- tema: el tema de los crucigramas infantiles (animales, comida...).
- origen: de dónde sale la pista, para los créditos.

Los campos directa, tema y origen se omiten cuando tienen su valor de siempre: true, ninguno y «propia».
"""

import enum
import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .texto import normalizar

VERSION = 1


class Dificultad(enum.Enum):
	FACIL = "facil"
	NORMAL = "normal"
	DIFICIL = "dificil"


@dataclass(frozen=True)
class Entrada:
	"""Una palabra del banco con su pista."""

	palabra: str
	pista: str
	dificultad: Dificultad
	directa: bool = True
	tema: str | None = None
	origen: str = "propia"

	@property
	def clave(self) -> str:
		"""La palabra como va en el tablero: mayúsculas sin tildes (con Ñ)."""
		return normalizar(self.palabra)


class BancoInvalido(ValueError):
	"""El archivo del banco no tiene la forma esperada."""


def entrada_desde_dict(datos: dict[str, Any]) -> Entrada:
	try:
		entrada = Entrada(
			palabra=str(datos["palabra"]),
			pista=str(datos["pista"]),
			dificultad=Dificultad(datos["dificultad"]),
			directa=bool(datos.get("directa", True)),
			tema=datos.get("tema"),
			origen=str(datos.get("origen", "propia")),
		)
	except (KeyError, ValueError) as error:
		raise BancoInvalido(f"Entrada no válida: {datos!r}") from error
	if not entrada.clave or not entrada.pista.strip():
		raise BancoInvalido(f"Entrada sin palabra o sin pista: {datos!r}")
	return entrada


def entrada_a_dict(entrada: Entrada) -> dict[str, Any]:
	"""La entrada como diccionario, sin los campos que tienen su valor por omisión (ocupa menos)."""
	datos: dict[str, Any] = {
		"palabra": entrada.palabra,
		"pista": entrada.pista,
		"dificultad": entrada.dificultad.value,
	}
	if not entrada.directa:
		datos["directa"] = False
	if entrada.tema is not None:
		datos["tema"] = entrada.tema
	if entrada.origen != "propia":
		datos["origen"] = entrada.origen
	return datos


def cargar(ruta: str) -> list[Entrada]:
	"""Las entradas de un archivo del banco."""
	with open(ruta, encoding="utf-8") as archivo:
		datos = json.load(archivo)
	if not isinstance(datos, dict) or datos.get("version") != VERSION:
		raise BancoInvalido(f"Versión del banco no reconocida en {ruta}")
	return [entrada_desde_dict(e) for e in datos["entradas"]]


def guardar(ruta: str, entradas: Iterable[Entrada]) -> None:
	"""Escribe un archivo del banco (lo usan las herramientas que lo preparan), una entrada por línea."""
	lineas = [json.dumps(entrada_a_dict(e), ensure_ascii=False, separators=(",", ":")) for e in entradas]
	with open(ruta, "w", encoding="utf-8", newline="\n") as archivo:
		archivo.write(f'{{"version":{VERSION},"entradas":[\n')
		archivo.write(",\n".join(lineas))
		archivo.write("\n]}\n")

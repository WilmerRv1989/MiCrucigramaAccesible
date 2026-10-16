# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Dónde se guardan los datos del complemento: la carpeta de configuración de NVDA."""

import os

import globalVars
from logHandler import log


def carpeta_configuracion() -> str:
	return os.path.join(globalVars.appArgs.configPath, "miCrucigramaAccesible")


def ruta_guardado_automatico() -> str:
	"""El crucigrama sin terminar, para continuarlo."""
	return os.path.join(carpeta_configuracion(), "crucigrama_en_curso.json")


def ruta_guardado_del_dia() -> str:
	"""El crucigrama del día sin terminar: tiene su propio archivo y no pisa el normal."""
	return os.path.join(carpeta_configuracion(), "crucigrama_del_dia.json")


def ruta_progreso() -> str:
	"""El progreso del curso «Aprender a jugar»."""
	return os.path.join(carpeta_configuracion(), "progreso.json")


def ruta_leccion_en_curso() -> str:
	"""El crucigrama entero de una lección (bloque C) que quedó a medias."""
	return os.path.join(carpeta_configuracion(), "leccion_en_curso.json")


def ruta_estadisticas() -> str:
	return os.path.join(carpeta_configuracion(), "estadisticas.json")


def leer(ruta: str) -> str:
	with open(ruta, encoding="utf-8-sig") as archivo:
		return archivo.read()


def escribir(ruta: str, texto: str) -> None:
	"""Escribe primero en un archivo temporal, para no dejar nunca un archivo a medias."""
	os.makedirs(os.path.dirname(ruta), exist_ok=True)
	temporal = ruta + ".tmp"
	with open(temporal, "w", encoding="utf-8", newline="\n") as archivo:
		archivo.write(texto)
	os.replace(temporal, ruta)


def borrar(ruta: str) -> None:
	try:
		os.remove(ruta)
	except FileNotFoundError:
		pass
	except OSError:
		log.debugWarning("No se pudo borrar %s", ruta, exc_info=True)

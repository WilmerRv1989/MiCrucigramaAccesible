# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Preferencias del complemento, guardadas en la configuración de NVDA (sección miCrucigramaAccesible).

Lo último elegido en el diálogo de nuevo crucigrama y las opciones del panel de NVDA.
"""

import config

from ..crucigrama import anunciador, vista
from ..crucigrama.banco import Dificultad
from ..crucigrama.generador import Tamano

SECCION = "miCrucigramaAccesible"
ESPECIFICACION = {
	# Tema infantil elegido; vacío es el crucigrama general.
	"tema": 'string(default="")',
	"tamano": 'option("pequeno", "mediano", "grande", default="mediano")',
	"dificultad": 'option("facil", "normal", "dificil", default="normal")',
	# Las ayudas empiezan desactivadas: se eligen al empezar cada crucigrama.
	"ayudas": "boolean(default=False)",
	# Panel de opciones.
	"sonidos": "boolean(default=True)",
	"decir_cruces": "boolean(default=True)",
	"decir_escrito": "boolean(default=True)",
}


def registrar() -> None:
	config.conf.spec[SECCION] = ESPECIFICACION
	config.post_configProfileSwitch.register(aplicar)
	aplicar()


def quitar() -> None:
	config.post_configProfileSwitch.unregister(aplicar)


def seccion():
	"""La sección del complemento en la configuración de NVDA."""
	return config.conf[SECCION]


def aplicar() -> None:
	"""Pasa al anunciador las opciones de lo que se dice al moverse."""
	datos = seccion()
	anunciador.configurar(bool(datos["decir_cruces"]), bool(datos["decir_escrito"]))


def sonidos_activados() -> bool:
	return bool(seccion()["sonidos"])


def tema_guardado() -> str | None:
	tema = str(seccion()["tema"])
	return tema if tema in vista.TEMAS else None


def tamano_guardado() -> Tamano:
	try:
		return Tamano(seccion()["tamano"])
	except ValueError:
		return Tamano.MEDIANO


def dificultad_guardada() -> Dificultad:
	try:
		return Dificultad(seccion()["dificultad"])
	except ValueError:
		return Dificultad.NORMAL


def ayudas_guardadas() -> bool:
	return bool(seccion()["ayudas"])


def guardar(tema: str | None, tamano: Tamano, dificultad: Dificultad, ayudas: bool) -> None:
	datos = seccion()
	datos["tema"] = tema or ""
	datos["tamano"] = tamano.value
	datos["dificultad"] = dificultad.value
	datos["ayudas"] = ayudas

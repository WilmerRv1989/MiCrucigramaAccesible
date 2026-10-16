# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""«Atajos de teclado»: las teclas del tablero, tal como las tiene asignadas cada persona.

Las teclas se consultan a NVDA en el momento (como el diálogo Gestos de entrada), así que la
lista refleja los cambios hechos en Gestos de entrada.
"""

from collections.abc import Iterable
from html import escape

import inputCore
import ui
from logHandler import log
from . import traduccion

traduccion.iniciar()

# Paquete del complemento, para reconocer las órdenes globales (las del menú Herramientas).
_PAQUETE = __name__.rsplit(".interfaz", 1)[0]

# Una entrada: las órdenes que agrupa (o None si la tecla es fija, como las letras), las teclas fijas
# en ese caso, y la descripción.
Entrada = tuple[tuple[str, ...] | None, str, str]


def secciones() -> list[tuple[str, list[Entrada]]]:
	return [
		(
			# Translators: heading in the list of keyboard shortcuts.
			_("Moving around the board"),
			[
				(
					("arriba", "abajo", "izquierda", "derecha"),
					"",
					# Translators: description in the list of keyboard shortcuts.
					_("Follow the words cell by cell; a bump sound means there is no letter that way"),
				),
				# Translators: description in the list of keyboard shortcuts.
				(("inicio_palabra", "fin_palabra"), "", _("First or last letter of the word")),
				# Translators: description in the list of keyboard shortcuts.
				(("siguiente_palabra", "anterior_palabra"), "", _("Next or previous word")),
				# Translators: description in the list of keyboard shortcuts.
				(("lista_pistas",), "", _("List of all the clues, to go to a word")),
			],
		),
		(
			# Translators: heading in the list of keyboard shortcuts.
			_("Writing"),
			[
				(
					None,
					# Translators: the keys that write on the board, in the list of keyboard shortcuts.
					_("Letters"),
					# Translators: description in the list of keyboard shortcuts.
					_("Write the letter and move on along the word; accents do not count, Ñ does"),
				),
				# Translators: description in the list of keyboard shortcuts.
				(("retroceso",), "", _("Delete the letter of the cell or, if it is empty, the one before")),
				# Translators: description in the list of keyboard shortcuts.
				(("borrar",), "", _("Delete the letter of the cell")),
				# Translators: description in the list of keyboard shortcuts.
				(("deshacer",), "", _("Undo the last change")),
			],
		),
		(
			# Translators: heading in the list of keyboard shortcuts.
			_("Listening"),
			[
				# Translators: description in the list of keyboard shortcuts.
				(("pista",), "", _("Repeat the clue of the word")),
				# Translators: description in the list of keyboard shortcuts.
				(("pista_cruce",), "", _("At a crossing, the clue of the other word")),
				# Translators: description in the list of keyboard shortcuts.
				(("patron",), "", _("Letters of the word, with the empty cells")),
				# Translators: description in the list of keyboard shortcuts.
				(("palabra_escrita",), "", _("The word as it is written, with the gaps")),
				# Translators: description in the list of keyboard shortcuts.
				(("leer_casilla",), "", _("Read the current cell again")),
				# Translators: description in the list of keyboard shortcuts.
				(("estado",), "", _("How many words are complete and which are missing")),
				# Translators: description in the list of keyboard shortcuts.
				(("posicion",), "", _("Row and column of the cell")),
			],
		),
		(
			# Translators: heading in the list of keyboard shortcuts.
			_("Help"),
			[
				# Translators: description in the list of keyboard shortcuts.
				(("ayuda_letra",), "", _("The letter that goes in the cell; you write it")),
				# Translators: description in the list of keyboard shortcuts.
				(("ayuda_palabra",), "", _("The whole word, spelled; you write it")),
			],
		),
		(
			# Translators: heading in the list of keyboard shortcuts.
			_("Menu and window"),
			[
				(
					("menu",),
					"",
					# Translators: description in the list of keyboard shortcuts.
					_("Board menu: check, restart, new crossword, keyboard shortcuts and close"),
				),
				# Translators: description in the list of keyboard shortcuts.
				(("atajos",), "", _("This list of keyboard shortcuts")),
				# Translators: description in the list of keyboard shortcuts.
				(("cerrar",), "", _("Close the board; the crossword is kept")),
				# Translators: description in the list of keyboard shortcuts.
				(None, "Alt+F4", _("Close the board")),
			],
		),
	]


def _lecciones() -> tuple[str, list[Entrada]]:
	return (
		# Translators: heading in the list of keyboard shortcuts.
		_("Lessons"),
		[
			# Translators: description in the list of keyboard shortcuts.
			(("repetir_instruccion",), "", _("Repeat the instruction of the exercise")),
			# Translators: description in the list of keyboard shortcuts.
			(("repetir_explicacion",), "", _("Repeat the explanation of the lesson")),
			(
				None,
				"",
				# Translators: description in the list of keyboard shortcuts, in lessons.
				_("In the lessons a letter that does not fit is not written, and Control+Z does nothing"),
			),
		],
	)


def _globales() -> tuple[str, list[Entrada]]:
	return (
		# Translators: heading in the list of keyboard shortcuts: commands that work from anywhere.
		_("From anywhere"),
		[
			(
				("abrir_tablero",),
				"",
				# Translators: description in the list of keyboard shortcuts.
				_("Open the board: continue the unfinished crossword or start a new one"),
			),
			# Translators: description in the list of keyboard shortcuts.
			(("crucigrama_del_dia",), "", _("Open the crossword of the day")),
			# Translators: description in the list of keyboard shortcuts.
			(("aprender_a_jugar",), "", _("Open Learn to play")),
			# Translators: description in the list of keyboard shortcuts.
			(("estadisticas",), "", _("Show My statistics")),
		],
	)


def teclas_asignadas(objeto: object) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
	"""Teclas de cada orden: (las del tablero de `objeto`, las globales del complemento).

	Se consultan a NVDA como en Gestos de entrada, incluidos los cambios de cada persona.
	"""
	tablero: dict[str, list[str]] = {}
	globales: dict[str, list[str]] = {}
	try:
		mapeos = inputCore.manager.getAllGestureMappings(obj=objeto, ancestors=[])
	except Exception:
		log.debugWarning("No se pudieron consultar los gestos", exc_info=True)
		return tablero, globales
	for categoria in mapeos.values():
		for info in categoria.values():
			nombre = info.scriptName
			if isinstance(objeto, info.cls):
				tablero.setdefault(nombre, []).extend(info.gestures)
			elif info.cls.__module__ == _PAQUETE:
				globales.setdefault(nombre, []).extend(info.gestures)
	return tablero, globales


def _texto_teclas(gestos: Iterable[str]) -> str:
	textos = []
	for gesto in gestos:
		try:
			texto = inputCore.getDisplayTextForGestureIdentifier(gesto)[1]
		except Exception:
			texto = gesto.split(":", 1)[-1]
		if texto not in textos:
			textos.append(texto)
	# Translators: shown in the list of keyboard shortcuts when a command has no key.
	return ", ".join(textos) if textos else _("no key assigned")


def _html_seccion(titulo: str, entradas: list[Entrada], teclas: dict[str, list[str]]) -> str:
	elementos = []
	for ordenes, fija, descripcion in entradas:
		if ordenes is None:
			linea = f"{fija}: {descripcion}" if fija else descripcion
		else:
			gestos = [g for orden in ordenes for g in teclas.get(orden, [])]
			linea = f"{_texto_teclas(gestos)}: {descripcion}"
		elementos.append(f"<li>{escape(linea)}.</li>")
	return f"<h2>{escape(titulo)}</h2><ul>{''.join(elementos)}</ul>"


def html_atajos(celda: object, leccion: bool = False) -> str:
	"""La lista de teclas. `celda` es una casilla del tablero, para consultar sus órdenes."""
	intro = _(
		# Translators: introduction of the list of keyboard shortcuts.
		"You can change these keys in the NVDA menu, Preferences, Input gestures, "
		"category MiCrucigramaAccesible (with the focus on the board for the board keys).",
	)
	partes = [f"<p>{escape(intro)}</p>"]
	teclas, globales = teclas_asignadas(celda)
	lista = secciones()
	if leccion:
		lista.insert(-1, _lecciones())
	for titulo, entradas in lista:
		partes.append(_html_seccion(titulo, entradas, teclas))
	titulo, entradas = _globales()
	partes.append(_html_seccion(titulo, entradas, globales))
	return "".join(partes)


def mostrar(celda: object, leccion: bool = False) -> None:
	ui.browseableMessage(
		html_atajos(celda, leccion),
		# Translators: title of the window with the list of keyboard shortcuts.
		title=_("Keyboard shortcuts"),
		isHtml=True,
		closeButton=True,
		copyButton=True,
	)

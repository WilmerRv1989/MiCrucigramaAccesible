# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Textos para presentar un crucigrama: nombres de tamaños, dificultades y temas, y la vista previa.

La vista previa es un crucigrama entero en texto, por secciones: el tablero fila por fila,
las pistas horizontales, las verticales y, al final, las soluciones.
"""

from .banco import Dificultad
from .generador import Crucigrama, Direccion, Tamano
from .idioma import _, ngettext

# Los temas de los crucigramas infantiles, en el orden en que se ofrecen.
TEMAS = ("animales", "comida", "colores", "cuerpo", "casa", "escuela")

# Lo que se escribe en una casilla sin letra.
VACIA = "."


def nombre_tamano(tamano: Tamano) -> str:
	return {
		# Translators: a crossword size: about 6 words.
		Tamano.PEQUENO: _("Small"),
		# Translators: a crossword size: about 12 words.
		Tamano.MEDIANO: _("Medium"),
		# Translators: a crossword size: about 20 words.
		Tamano.GRANDE: _("Large"),
	}[tamano]


def nombre_dificultad(dificultad: Dificultad) -> str:
	return {
		# Translators: a crossword difficulty level.
		Dificultad.FACIL: _("Easy"),
		# Translators: a crossword difficulty level.
		Dificultad.NORMAL: _("Normal"),
		# Translators: a crossword difficulty level.
		Dificultad.DIFICIL: _("Hard"),
	}[dificultad]


def nombre_tema(tema: str) -> str:
	return {
		# Translators: a theme of the children's crosswords.
		"animales": _("Animals"),
		# Translators: a theme of the children's crosswords.
		"comida": _("Food"),
		# Translators: a theme of the children's crosswords.
		"colores": _("Colours"),
		# Translators: a theme of the children's crosswords.
		"cuerpo": _("The body"),
		# Translators: a theme of the children's crosswords.
		"casa": _("The house"),
		# Translators: a theme of the children's crosswords.
		"escuela": _("School"),
	}[tema]


def descripcion(crucigrama: Crucigrama) -> str:
	"""Qué crucigrama es: «Mediano, normal, 12 palabras» o «Infantil: animales, 6 palabras»."""
	palabras = len(crucigrama.palabras)
	if crucigrama.tema is not None:
		return ngettext(
			# Translators: describes a children's crossword, for example "Children's: Animals, 6 words".
			"Children's: {theme}, {count} word",
			"Children's: {theme}, {count} words",
			palabras,
		).format(theme=nombre_tema(crucigrama.tema), count=palabras)
	return ngettext(
		# Translators: describes a crossword, for example "Medium, Normal, 12 words".
		"{size}, {difficulty}, {count} word",
		"{size}, {difficulty}, {count} words",
		palabras,
	).format(
		size=nombre_tamano(crucigrama.tamano),
		difficulty=nombre_dificultad(crucigrama.dificultad),
		count=palabras,
	)


def titulo_direccion(direccion: Direccion) -> str:
	if direccion is Direccion.HORIZONTAL:
		# Translators: heading of the across clues (the words that are read from left to right).
		return _("Across")
	# Translators: heading of the down clues (the words that are read from top to bottom).
	return _("Down")


def linea_pista(numero: int, pista: str, largo: int, fila: int, columna: int) -> str:
	"""Una pista con su número, su largo y dónde empieza la palabra (fila y columna desde 1)."""
	letras = ngettext(
		# Translators: the length of a crossword word, for example "5 letters".
		"{count} letter",
		"{count} letters",
		largo,
	).format(count=largo)
	# Translators: a clue in the preview, for example "3. Colour of the sky (4 letters; row 2, column 5)".
	return _("{number}. {clue} ({letters}; row {row}, column {column})").format(
		number=numero,
		clue=pista,
		letters=letras,
		row=fila,
		column=columna,
	)


def secciones(crucigrama: Crucigrama) -> list[tuple[str, list[str]]]:
	"""La vista previa: un título y sus líneas por cada sección."""
	tablero = [
		# Translators: size of the board in the crossword preview.
		_("{rows} rows and {columns} columns.").format(rows=crucigrama.alto, columns=crucigrama.ancho),
		# Translators: explains the board of the preview, where each letter is a cell.
		_("Each letter is a cell; a dot is a cell without a letter."),
	]
	for fila in range(crucigrama.alto):
		casillas = " ".join(crucigrama.letra(fila, columna) or VACIA for columna in range(crucigrama.ancho))
		# Translators: a row of the board in the preview, for example "Row 1: . . C A S A".
		tablero.append(_("Row {row}: {cells}").format(row=fila + 1, cells=casillas))
	resultado = [
		# Translators: heading of the board in the crossword preview.
		(_("Board"), tablero),
	]
	for direccion in Direccion:
		resultado.append(
			(
				titulo_direccion(direccion),
				[
					linea_pista(p.numero, p.entrada.pista, p.largo, p.fila + 1, p.columna + 1)
					for p in crucigrama.de_direccion(direccion)
				],
			),
		)
	soluciones = [
		"{title}: {words}.".format(
			title=titulo_direccion(direccion),
			words=", ".join(f"{p.numero} {p.entrada.palabra}" for p in crucigrama.de_direccion(direccion)),
		)
		for direccion in Direccion
	]
	# Translators: heading of the solutions at the end of the crossword preview.
	resultado.append((_("Solutions"), soluciones))
	return resultado

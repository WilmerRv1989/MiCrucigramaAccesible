# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Lo que se dice en el tablero: palabras, casillas, cruces, patrones y resultados.

Se habla de palabras, no de coordenadas: «2 horizontal, letra 3 de 5». La fila y la columna
solo se dicen cuando se piden (F6).
"""

from .generador import Casilla, Direccion, PalabraColocada
from .idioma import _, ngettext
from .partida import Escritura, Partida

# Opciones del panel de NVDA: lo que se dice al moverse.
_decir_cruces = True
_decir_escrito = True


def configurar(decir_cruces: bool, decir_escrito: bool) -> None:
	"""Si se dice con qué palabra se cruza cada casilla y lo escrito al entrar en una palabra."""
	global _decir_cruces, _decir_escrito
	_decir_cruces = decir_cruces
	_decir_escrito = decir_escrito


def unir(elementos: list[str]) -> str:
	"""«3 horizontal», «3 horizontal y 5 vertical», «1 vertical, 3 horizontal y 5 vertical»."""
	if len(elementos) < 2:
		return "".join(elementos)
	# Translators: joins the last item of a list, as in "3 across, 4 across and 5 down".
	return _("{items} and {last}").format(items=", ".join(elementos[:-1]), last=elementos[-1])


def nombre_palabra(palabra: PalabraColocada) -> str:
	"""«2 horizontal» o «5 vertical»."""
	if palabra.direccion is Direccion.HORIZONTAL:
		# Translators: a crossword word by its number, for example "2 across".
		return _("{number} across").format(number=palabra.numero)
	# Translators: a crossword word by its number, for example "5 down".
	return _("{number} down").format(number=palabra.numero)


def describir_palabra(palabra: PalabraColocada) -> str:
	"""Al entrar en una palabra: «2 horizontal, 4 letras: Hace cuac y nada en el estanque»."""
	letras = ngettext(
		# Translators: length of a crossword word, as in "2 across, 4 letters: clue".
		"{count} letter",
		"{count} letters",
		palabra.largo,
	).format(count=palabra.largo)
	# Translators: a crossword word with its clue, for example "2 across, 4 letters: Says quack".
	return _("{word}, {letters}: {clue}").format(
		word=nombre_palabra(palabra),
		letters=letras,
		clue=palabra.entrada.pista,
	)


def describir_escrito(partida: Partida, palabra: PalabraColocada) -> str | None:
	"""Lo que lleva escrito una palabra: completa, como palabra («pato»); a medias, letra a letra.

	None si no tiene nada escrito.
	"""
	letras = [partida.letra(c) for c in palabra.casillas()]
	if not any(letras):
		return None
	if all(letras):
		return "".join(letra for letra in letras if letra).lower()
	return describir_patron(partida, palabra)


def describir_palabra_al_entrar(partida: Partida, palabra: PalabraColocada) -> str:
	"""La pista y, si la palabra tiene algo escrito, lo que lleva: «… Escrito: pato»."""
	texto = describir_palabra(palabra)
	escrito = describir_escrito(partida, palabra) if _decir_escrito else None
	if escrito is None:
		return texto
	# Translators: what a word already has written, said after its clue, as in "Written: duck".
	return "{clue}. {written}".format(clue=texto, written=_("Written: {letters}").format(letters=escrito))


def describir_palabra_escrita(partida: Partida, palabra: PalabraColocada) -> str:
	"""Mayúsculas+F3: lo escrito como palabra; los huecos se dicen entre los trozos («pa, hueco, o»)."""
	trozos: list[str] = []
	actual = ""
	for casilla in palabra.casillas():
		letra = partida.letra(casilla)
		if letra:
			actual += letra.lower()
			continue
		if actual:
			trozos.append(actual)
			actual = ""
		# Translators: an empty cell when reading a word as written, as in "du, gap, k".
		trozos.append(_("gap"))
	if actual:
		trozos.append(actual)
	if all(not partida.letra(c) for c in palabra.casillas()):
		# Translators: said when reading a word that has no letters written.
		return _("nothing written")
	return ", ".join(trozos)


def contenido(letra: str | None) -> str:
	# Translators: a crossword cell without a letter written yet.
	return letra if letra else _("empty")


def describir_casilla(partida: Partida, casilla: Casilla, palabra: PalabraColocada) -> str:
	"""«C, letra 3 de 5» y, en un cruce, «cruza con 1 vertical, letra 2»."""
	# Translators: a cell of the current word, as in "C, letter 3 of 5" or "empty, letter 3 of 5".
	texto = _("{content}, letter {position} of {length}").format(
		content=contenido(partida.letra(casilla)),
		position=partida.posicion_en(palabra, casilla),
		length=palabra.largo,
	)
	otra = partida.cruce(casilla, palabra.direccion) if _decir_cruces else None
	if otra is not None:
		# Translators: added when the cell is shared with another word, as in "crosses 1 down, letter 2".
		cruce = _("crosses {word}, letter {position}").format(
			word=nombre_palabra(otra),
			position=partida.posicion_en(otra, casilla),
		)
		texto = f"{texto}, {cruce}"
	return texto


def describir_cruce(partida: Partida) -> str | None:
	"""Mayúsculas+F2: la otra palabra del cruce con su pista, o None si la casilla no es un cruce."""
	otra = partida.cruce()
	if otra is None:
		return None
	# Translators: the other word at a crossing, as in "1 down, letter 2. 1 down, 4 letters: clue".
	return _("Letter {position} of {word}").format(
		position=partida.posicion_en(otra, partida.casilla),
		word=describir_palabra(otra),
	)


def describir_patron(partida: Partida, palabra: PalabraColocada) -> str:
	"""F3: las letras de la palabra, «C, vacía, S, A»."""
	return ", ".join(contenido(partida.letra(c)) for c in palabra.casillas())


def describir_posicion(casilla: Casilla) -> str:
	# Translators: the position of a cell on the board, as in "Row 3, column 5".
	return _("Row {row}, column {column}").format(row=casilla[0] + 1, column=casilla[1] + 1)


def describir_estado(partida: Partida) -> str:
	"""F5: «5 de 12 palabras completas. Faltan: 2 horizontal, 4 vertical»."""
	total = len(partida.orden)
	completas = len(partida.palabras_completas())
	texto = ngettext(
		# Translators: how many words are full, as in "5 of 12 words complete".
		"{done} of {total} word complete",
		"{done} of {total} words complete",
		total,
	).format(done=completas, total=total)
	pendientes = [nombre_palabra(p) for p in partida.orden if not partida.completa(p)]
	if pendientes:
		# Translators: the words that still have empty cells, as in "Missing: 2 across, 4 down".
		faltan = _("Missing: {words}").format(words=", ".join(pendientes))
		texto = f"{texto}. {faltan}"
	return f"{texto}."


def describir_escritura(partida: Partida, resultado: Escritura) -> str:
	"""Lo que se dice tras escribir, además de la casilla a la que se pasa."""
	partes = [resultado.letra]
	for palabra in resultado.completadas:
		# Translators: said when the last empty cell of a word is filled (it does not say if it is right).
		partes.append(_("{word} complete").format(word=nombre_palabra(palabra)))
	if resultado.lleno_con_errores and not partida.con_ayudas:
		# Translators: said when every cell is filled but some letter is wrong, in a crossword without help.
		partes.append(_("The crossword is full, but there are wrong letters"))
	elif resultado.lleno_con_errores:
		palabras = unir([nombre_palabra(p) for p in partida.palabras_con_errores()])
		partes.append(
			# Translators: said when every cell is filled but some letter is wrong, as in "... wrong letters in 3 across".
			_("The crossword is full, but there are wrong letters in {words}").format(words=palabras),
		)
	return ". ".join(partes)


def describir_borrado(letra: str | None) -> str:
	if letra is None:
		# Translators: said when deleting in a cell that has no letter.
		return _("nothing to delete")
	# Translators: said after deleting a letter, as in "C deleted".
	return _("{letter} deleted").format(letter=letra)


def describir_comprobacion(partida: Partida) -> str:
	"""Cuántas letras están mal, sin decir cuáles, y cuántas casillas faltan."""
	errores = partida.errores()
	vacias = partida.vacias()
	if errores and not partida.con_ayudas:
		texto = ngettext(
			# Translators: result of Check in a crossword without help, as in "2 wrong letters".
			"{count} wrong letter",
			"{count} wrong letters",
			errores,
		).format(count=errores)
	elif errores:
		texto = ngettext(
			# Translators: result of Check, as in "2 wrong letters, in 3 across and 5 down".
			"{count} wrong letter, in {words}",
			"{count} wrong letters, in {words}",
			errores,
		).format(count=errores, words=unir([nombre_palabra(p) for p in partida.palabras_con_errores()]))
	else:
		# Translators: result of Check when every written letter is right.
		texto = _("All the letters you wrote are right")
	if vacias:
		faltan = ngettext(
			# Translators: added to the result of Check, as in "7 empty cells left".
			"{count} empty cell left",
			"{count} empty cells left",
			vacias,
		).format(count=vacias)
		texto = f"{texto}. {faltan}"
	return f"{texto}."


def describir_ayuda_letra(partida: Partida) -> str:
	"""F7: qué letra va en la casilla, sin escribirla."""
	solucion = partida.solucion(partida.casilla)
	if partida.letra(partida.casilla) == solucion:
		# Translators: help for a cell whose letter is already right, as in "The R of this cell is already right."
		return _("The {letter} of this cell is already right.").format(letter=solucion)
	# Translators: help that tells the letter of the cell without writing it, as in "Help: here goes R".
	return _("Help: here goes {letter}").format(letter=solucion)


def describir_ayuda_palabra(partida: Partida) -> str:
	"""Mayúsculas+F7: la palabra entera, sin escribirla, y deletreada para escribirla."""
	palabra = partida.palabra_actual
	# Translators: help that tells the whole word, as in "Help: 3 across is duck: D, U, C, K".
	return _("Help: {word} is {answer}: {letters}").format(
		word=nombre_palabra(palabra),
		answer=palabra.entrada.palabra,
		letters=", ".join(palabra.clave),
	)

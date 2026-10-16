# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""El tablero de crucigrama como cuadrícula virtual: casillas, caminitos y teclas.

Las letras no son órdenes: llegan al panel del tablero como caracteres escritos (ver
`PanelTablero` en ventana_tablero.py), así funcionan la Ñ y las vocales con tilde de cualquier teclado.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

import braille
import core
import tones
import ui
import wx
from logHandler import log
from scriptHandler import script

from ..crucigrama import anunciador
from ..crucigrama.generador import Direccion, PalabraColocada
from ..nucleo.tablero_virtual import CeldaVirtual, CuadriculaVirtual, sonar_borde
from . import sonidos, traduccion

if TYPE_CHECKING:
	from ..crucigrama.partida import Partida
	from .ventana_tablero import VentanaBase

traduccion.iniciar()

# Translators: category of the add-on commands in the Input gestures dialog.
CATEGORIA = _("MiCrucigramaAccesible")

# Tono de que no se puede (no es una letra, nada que deshacer, crucigrama resuelto).
TONO_ERROR = (220, 80)

# Si tras un menú o un diálogo el foco no vuelve a la casilla, el mensaje pendiente se dice igual.
_ESPERA_FOCO_MS = 1500


class CeldaCrucigrama(CeldaVirtual):
	"""Casilla del tablero. Aquí están todas las teclas que funcionan dentro del tablero."""

	cuadricula: "CuadriculaCrucigrama"

	def event_typedCharacter(self, ch: str) -> None:
		# Las letras se escriben en el tablero, que ya dice lo que pasa: NVDA no las repite.
		pass

	# Moverse.

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Moves up, if there is a cell with a letter above"),
		category=CATEGORIA,
		gesture="kb:upArrow",
	)
	def script_arriba(self, gesture) -> None:
		self.cuadricula.mover(Direccion.VERTICAL, -1)

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Moves down, if there is a cell with a letter below"),
		category=CATEGORIA,
		gesture="kb:downArrow",
	)
	def script_abajo(self, gesture) -> None:
		self.cuadricula.mover(Direccion.VERTICAL, 1)

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Moves left, if there is a cell with a letter on the left"),
		category=CATEGORIA,
		gesture="kb:leftArrow",
	)
	def script_izquierda(self, gesture) -> None:
		self.cuadricula.mover(Direccion.HORIZONTAL, -1)

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Moves right, if there is a cell with a letter on the right"),
		category=CATEGORIA,
		gesture="kb:rightArrow",
	)
	def script_derecha(self, gesture) -> None:
		self.cuadricula.mover(Direccion.HORIZONTAL, 1)

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Moves to the first letter of the word"),
		category=CATEGORIA,
		gesture="kb:home",
	)
	def script_inicio_palabra(self, gesture) -> None:
		self.cuadricula.extremo_palabra(final=False)

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Moves to the last letter of the word"),
		category=CATEGORIA,
		gesture="kb:end",
	)
	def script_fin_palabra(self, gesture) -> None:
		self.cuadricula.extremo_palabra(final=True)

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Moves to the next word"),
		category=CATEGORIA,
		gesture="kb:tab",
	)
	def script_siguiente_palabra(self, gesture) -> None:
		self.cuadricula.otra_palabra(1)

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Moves to the previous word"),
		category=CATEGORIA,
		gesture="kb:shift+tab",
	)
	def script_anterior_palabra(self, gesture) -> None:
		self.cuadricula.otra_palabra(-1)

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Shows the list of all the clues, to go to a word"),
		category=CATEGORIA,
		gesture="kb:f4",
	)
	def script_lista_pistas(self, gesture) -> None:
		self.cuadricula.ventana.mostrar_pistas()

	# Escribir.

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Deletes the letter of the cell or, if it is empty, the one before"),
		category=CATEGORIA,
		gesture="kb:backspace",
	)
	def script_retroceso(self, gesture) -> None:
		self.cuadricula.retroceder()

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Deletes the letter of the cell"),
		category=CATEGORIA,
		gesture="kb:delete",
	)
	def script_borrar(self, gesture) -> None:
		self.cuadricula.borrar()

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Undoes the last change"),
		category=CATEGORIA,
		gesture="kb:control+z",
	)
	def script_deshacer(self, gesture) -> None:
		self.cuadricula.deshacer()

	# Escuchar.

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Repeats the clue of the word"),
		category=CATEGORIA,
		gesture="kb:f2",
	)
	def script_pista(self, gesture) -> None:
		ui.message(anunciador.describir_palabra(self.cuadricula.partida.palabra_actual))

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("At a crossing, reports the clue of the other word"),
		category=CATEGORIA,
		gesture="kb:shift+f2",
	)
	def script_pista_cruce(self, gesture) -> None:
		texto = anunciador.describir_cruce(self.cuadricula.partida)
		if texto is None:
			tones.beep(*TONO_ERROR)
			# Translators: said when asking for the crossing word in a cell that is not a crossing.
			texto = _("No other word crosses here.")
		ui.message(texto)

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Reports the letters of the word, with the empty cells"),
		category=CATEGORIA,
		gesture="kb:f3",
	)
	def script_patron(self, gesture) -> None:
		partida = self.cuadricula.partida
		ui.message(anunciador.describir_patron(partida, partida.palabra_actual))

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Reads the word as it is written, with the gaps"),
		category=CATEGORIA,
		gesture="kb:shift+f3",
	)
	def script_palabra_escrita(self, gesture) -> None:
		partida = self.cuadricula.partida
		ui.message(anunciador.describir_palabra_escrita(partida, partida.palabra_actual))

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Reads the current cell again"),
		category=CATEGORIA,
		gesture="kb:space",
	)
	def script_leer_casilla(self, gesture) -> None:
		partida = self.cuadricula.partida
		ui.message(anunciador.describir_casilla(partida, partida.casilla, partida.palabra_actual))

	# Ayudas.

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Help: tells the letter that goes in the cell, without writing it"),
		category=CATEGORIA,
		gesture="kb:f7",
	)
	def script_ayuda_letra(self, gesture) -> None:
		self.cuadricula.dar_ayuda(anunciador.describir_ayuda_letra)

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Help: tells the whole word, without writing it"),
		category=CATEGORIA,
		gesture="kb:shift+f7",
	)
	def script_ayuda_palabra(self, gesture) -> None:
		self.cuadricula.dar_ayuda(anunciador.describir_ayuda_palabra)

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Reports how many words are complete and which are missing"),
		category=CATEGORIA,
		gesture="kb:f5",
	)
	def script_estado(self, gesture) -> None:
		ui.message(anunciador.describir_estado(self.cuadricula.partida))

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Reports the row and the column of the cell"),
		category=CATEGORIA,
		gesture="kb:f6",
	)
	def script_posicion(self, gesture) -> None:
		ui.message(anunciador.describir_posicion(self.cuadricula.partida.casilla))

	# Ventana.

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Opens the menu of the board"),
		category=CATEGORIA,
		gestures=["kb:applications", "kb:shift+f10"],
	)
	def script_menu(self, gesture) -> None:
		self.cuadricula.ventana.mostrar_menu_tablero()

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Shows the keyboard shortcuts of the board"),
		category=CATEGORIA,
	)
	def script_atajos(self, gesture) -> None:
		self.cuadricula.ventana.mostrar_atajos()

	@script(
		# Translators: description of a crossword board command in the Input gestures dialog.
		description=_("Closes the board; the crossword is kept to continue it later"),
		category=CATEGORIA,
		gesture="kb:escape",
	)
	def script_cerrar(self, gesture) -> None:
		wx.CallAfter(self.cuadricula.ventana.Close)


class CuadriculaCrucigrama(CuadriculaVirtual):
	"""El tablero. La cuadrícula tiene todas las casillas del rectángulo, pero el cursor solo
	pisa las que tienen letra: los caminitos los decide la partida."""

	clase_celda = CeldaCrucigrama

	def __init__(self, panel: wx.Window, ventana: "VentanaBase") -> None:
		crucigrama = ventana.partida.crucigrama
		super().__init__(panel, crucigrama.alto, crucigrama.ancho)
		self.ventana = ventana
		# La palabra que se anunció por última vez; al entrar en otra se dice su pista.
		self._palabra_anunciada: PalabraColocada | None = None
		# Lo que se dice antes de la próxima casilla (por ejemplo, la letra recién escrita).
		self._prefijo: str | None = None
		# Mensaje que se dirá cuando NVDA termine de anunciar la casilla (ver `decir_al_volver`).
		self._pendiente: str | None = None
		self._sincronizar()

	@property
	def partida(self) -> "Partida":
		return self.ventana.partida

	def _sincronizar(self) -> None:
		self.fila, self.columna = self.partida.casilla

	def anunciar_antes(self, texto: str) -> None:
		"""La próxima vez que NVDA anuncie la casilla del cursor, dirá antes este texto."""
		self._prefijo = texto

	def olvidar_palabra(self) -> None:
		"""La próxima casilla que se anuncie dirá también su palabra y su pista."""
		self._palabra_anunciada = None

	# Lo que se oye.

	def nombre_celda(self, fila: int, columna: int) -> str:
		partida = self.partida
		casilla = (fila, columna)
		palabra = partida.palabra_en(casilla, partida.direccion) or partida.palabra_en(
			casilla,
			partida.direccion.otra,
		)
		if palabra is None:
			return ""
		partes = []
		if self._prefijo:
			partes.append(self._prefijo)
		if palabra != self._palabra_anunciada:
			partes.append(anunciador.describir_palabra_al_entrar(partida, palabra))
		partes.append(anunciador.describir_casilla(partida, casilla, palabra))
		return ". ".join(partes)

	def al_enfocar_celda(self, fila: int, columna: int) -> None:
		if (fila, columna) == self.partida.casilla:
			self._palabra_anunciada = self.partida.palabra_actual
			self._prefijo = None
		super().al_enfocar_celda(fila, columna)
		self._decir_pendiente()

	def decir_al_volver(self, texto: str) -> None:
		"""Dice un texto después de que NVDA anuncie la ventana y la casilla al cerrar un menú o un diálogo.

		`ui.delayedMessage` no basta: espera solo un instante, y el anuncio de la casilla lo corta.
		"""
		self._pendiente = texto
		core.callLater(_ESPERA_FOCO_MS, self._decir_pendiente)

	def _decir_pendiente(self) -> None:
		if self._pendiente is None:
			return
		texto, self._pendiente = self._pendiente, None
		ui.message(texto)

	def _ir_a_la_casilla(self, prefijo: str | None = None) -> None:
		"""Lleva el foco a la casilla del cursor; NVDA la anuncia (con `prefijo` delante)."""
		self._prefijo = prefijo
		self._sincronizar()
		self.enfocar_celda_actual()
		self.panel.Refresh()

	def _decir_en_el_sitio(self, texto: str) -> None:
		"""Cuando el cursor no se mueve: se dice el texto y se actualiza la línea braille."""
		self.panel.Refresh()
		ui.message(texto)
		try:
			braille.handler.handleUpdate(self.celda_actual)
		except Exception:
			log.debugWarning("No se pudo actualizar el braille de la casilla", exc_info=True)

	# Moverse.

	def mover(self, direccion: Direccion, paso: int) -> None:
		if not self.partida.mover(direccion, paso):
			sonar_borde()
			return
		self._ir_a_la_casilla()

	def extremo_palabra(self, final: bool) -> None:
		partida = self.partida
		antes = partida.casilla
		partida.ir_a_palabra(partida.palabra_actual, final=final)
		if partida.casilla == antes:
			sonar_borde()
			return
		self._ir_a_la_casilla()

	def otra_palabra(self, paso: int) -> None:
		partida = self.partida
		partida.ir_a_palabra(partida.siguiente_palabra(paso))
		self._ir_a_la_casilla()

	def ir_a_palabra(self, palabra: PalabraColocada) -> None:
		"""Desde la lista de pistas: el foco vuelve solo al cerrarse el diálogo."""
		self.partida.ir_a_palabra(palabra)
		self._sincronizar()
		self.panel.Refresh()

	# Ayudas.

	def dar_ayuda(self, describir: Callable[["Partida"], str]) -> None:
		"""Dice la ayuda sin escribir nada: la letra o la palabra las escribe quien juega."""
		partida = self.partida
		if not partida.con_ayudas:
			tones.beep(*TONO_ERROR)
			# Translators: said when asking for help in a crossword without help.
			ui.message(_("This crossword is without help."))
			return
		if partida.resuelto:
			tones.beep(*TONO_ERROR)
		else:
			partida.ayudas += 1
			self.ventana.al_cambiar()
		ui.message(describir(partida))

	# Cambios.

	def _avisar_si_resuelto(self) -> bool:
		"""Un crucigrama resuelto ya no se cambia: suena el tono de error."""
		if not self.partida.resuelto:
			return False
		tones.beep(*TONO_ERROR)
		# Translators: reported when trying to change a solved crossword.
		ui.message(_("The crossword is solved. To play another one, open the menu and choose New crossword."))
		return True

	def escribir(self, caracter: str) -> None:
		if self._avisar_si_resuelto():
			return
		partida = self.partida
		antes = partida.casilla
		resultado = partida.escribir(caracter)
		if resultado is None:
			tones.beep(*TONO_ERROR)
			# Translators: said when typing something that is not a letter on the board.
			ui.message(_("Only letters can be written."))
			return
		self.ventana.al_cambiar()
		if resultado.resuelto:
			texto = resultado.letra
		else:
			if resultado.completadas:
				sonidos.reproducir(sonidos.COMPLETADO)
			texto = anunciador.describir_escritura(partida, resultado)
		if partida.casilla != antes:
			self._ir_a_la_casilla(prefijo=texto)
		else:
			self._decir_en_el_sitio(texto)
		if resultado.resuelto:
			self.ventana.al_resolver()

	def borrar(self) -> None:
		if self._avisar_si_resuelto():
			return
		letra = self.partida.borrar()
		if letra is not None:
			self.ventana.al_cambiar()
		self._decir_en_el_sitio(anunciador.describir_borrado(letra))

	def retroceder(self) -> None:
		if self._avisar_si_resuelto():
			return
		letra, movido = self.partida.retroceder()
		if letra is not None:
			self.ventana.al_cambiar()
		if movido:
			self._ir_a_la_casilla(prefijo=anunciador.describir_borrado(letra))
		elif letra is None:
			sonar_borde()
		else:
			self._decir_en_el_sitio(anunciador.describir_borrado(letra))

	def deshacer(self) -> None:
		if self._avisar_si_resuelto():
			return
		antes = self.partida.casilla
		casilla = self.partida.deshacer()
		if casilla is None:
			tones.beep(*TONO_ERROR)
			# Translators: reported when there is nothing to undo.
			ui.message(_("There is nothing to undo."))
			return
		self.ventana.al_cambiar()
		# Translators: said after undoing, before the cell that changed.
		deshecho = _("Undone")
		if casilla != antes:
			self._ir_a_la_casilla(prefijo=deshecho)
		else:
			partida = self.partida
			celda = anunciador.describir_casilla(partida, casilla, partida.palabra_actual)
			self._decir_en_el_sitio(f"{deshecho}. {celda}")

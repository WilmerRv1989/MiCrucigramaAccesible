# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Ventana de una lección: el tablero del ejercicio, la instrucción y el menú de la lección."""

from typing import TYPE_CHECKING

import ui
import wx

from ..crucigrama.curso.modelo import Leccion
from ..crucigrama.curso.sesion import SesionEjercicio
from ..crucigrama.partida import Partida
from . import atajos
from .tablero_leccion import CuadriculaLeccion
from .ventana_tablero import VentanaBase
from . import traduccion

if TYPE_CHECKING:
	from .curso import ControladorCurso

traduccion.iniciar()


def titulo_leccion(leccion: Leccion) -> str:
	# Translators: title of a lesson, as in "Lesson 1: What is a crossword?".
	return _("Lesson {id}: {title}").format(id=leccion.id, title=leccion.titulo)


class VentanaLeccion(VentanaBase):
	"""Ventana de una lección. Se cierra con Escape, con Alt+F4 o desde su menú.

	El progreso se guarda al superar cada ejercicio.
	"""

	cuadricula: CuadriculaLeccion

	def __init__(
		self,
		controlador: "ControladorCurso",
		leccion: Leccion,
		sesion: SesionEjercicio,
		numero: int,
		total: int,
	) -> None:
		super().__init__(
			titulo_leccion(leccion),
			# Translators: accessible name of the crossword board.
			_("Crossword board"),
			controlador.al_cerrar_ventana,
		)
		self.controlador = controlador
		self.leccion = leccion
		self.sesion = sesion
		self.numero = numero
		self.total = total
		self._instalar(CuadriculaLeccion(self.panel, self))
		# Al mostrarse la ventana, la instrucción se dice antes que la casilla.
		texto = self.texto_instruccion()
		if sesion.continuada:
			# Translators: said when a whole crossword of a lesson continues where it was left.
			continuada = _("You continue where you left it.")
			texto = f"{texto} {continuada}"
		self.cuadricula.anunciar_antes(texto)

	@property
	def partida(self) -> Partida:  # type: ignore[override]
		return self.sesion.partida

	def _al_activar(self, evento: wx.ActivateEvent) -> None:
		if evento.GetActive():
			# Al volver a la ventana se dice también la palabra y su pista.
			self.cuadricula.olvidar_palabra()
		super()._al_activar(evento)

	def cargar(self, sesion: SesionEjercicio, numero: int, felicitacion: str) -> None:
		"""Pasa al ejercicio siguiente en la misma ventana, con un tablero nuevo.

		NVDA anuncia la primera casilla con la felicitación y la nueva instrucción delante.
		"""
		self.sesion = sesion
		self.numero = numero
		self.cuadricula.cerrar()
		self._instalar(CuadriculaLeccion(self.panel, self))
		self.cuadricula.anunciar_antes(f"{felicitacion} {self.texto_instruccion()}")
		self.panel.Refresh()
		# NVDA tenía el foco en una casilla de la cuadrícula anterior: pasa a la nueva.
		self.cuadricula.enfocar_celda_actual()

	def texto_instruccion(self) -> str:
		# Translators: before the instruction of an exercise, as in "Exercise 2 of 3."
		ejercicio = _("Exercise {number} of {total}.").format(number=self.numero + 1, total=self.total)
		return f"{ejercicio} {self.sesion.ejercicio.instruccion}"

	def repetir_instruccion(self) -> None:
		ui.message(self.texto_instruccion())

	def repetir_explicacion(self) -> None:
		ui.message(" ".join(self.leccion.explicacion))

	def al_superar(self, mensaje: str) -> None:
		self.controlador.al_superar(mensaje)

	def al_cambiar(self) -> None:
		"""Tras cada cambio o ayuda: un crucigrama entero de una lección se guarda para continuarlo."""
		self.controlador.guardar_en_curso()

	def mostrar_menu_tablero(self) -> None:
		controlador = self.controlador
		hay_siguiente = controlador.curso.siguiente(self.leccion) is not None
		self.mostrar_menu(
			[
				# Translators: item of the menu of a lesson.
				(_("&Next lesson"), controlador.siguiente_leccion, hay_siguiente),
				# Translators: item of the menu of a lesson.
				(_("&List of lessons..."), controlador.abrir_lista, True),
				# Translators: item of the menu of a lesson.
				(_("&Keyboard shortcuts"), self.mostrar_atajos, True),
				# Translators: item of the menu of a lesson.
				(_("&Close the lesson"), self.Close, True),
			],
		)

	def mostrar_atajos(self) -> None:
		wx.CallAfter(atajos.mostrar, self.cuadricula.celda_actual, True)

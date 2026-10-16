# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""El tablero de las lecciones: las mismas teclas que el juego, pero cada cambio lo decide el ejercicio."""

from collections.abc import Callable
from typing import TYPE_CHECKING

import tones
import ui
from scriptHandler import script

from ..crucigrama import anunciador
from ..crucigrama.curso.sesion import Respuesta
from . import sonidos
from .tablero_crucigrama import CATEGORIA, TONO_ERROR, CeldaCrucigrama, CuadriculaCrucigrama
from . import traduccion

if TYPE_CHECKING:
	from ..crucigrama.partida import Partida
	from .ventana_leccion import VentanaLeccion

traduccion.iniciar()


class CeldaLeccion(CeldaCrucigrama):
	cuadricula: "CuadriculaLeccion"

	@script(
		# Translators: description of a lesson command in the Input gestures dialog.
		description=_("Repeats the instruction of the exercise"),
		category=CATEGORIA,
		gesture="kb:f9",
	)
	def script_repetir_instruccion(self, gesture) -> None:
		self.cuadricula.ventana.repetir_instruccion()

	@script(
		# Translators: description of a lesson command in the Input gestures dialog.
		description=_("Repeats the explanation of the lesson"),
		category=CATEGORIA,
		gesture="kb:shift+f9",
	)
	def script_repetir_explicacion(self, gesture) -> None:
		self.cuadricula.ventana.repetir_explicacion()


class CuadriculaLeccion(CuadriculaCrucigrama):
	clase_celda = CeldaLeccion
	ventana: "VentanaLeccion"

	def escribir(self, caracter: str) -> None:
		antes = self.partida.casilla
		respuesta = self.ventana.sesion.escribir(caracter)
		self._responder(respuesta, movido=self.partida.casilla != antes)

	def borrar(self) -> None:
		self._responder(self.ventana.sesion.borrar(), movido=False)

	def retroceder(self) -> None:
		respuesta, movido = self.ventana.sesion.retroceder()
		self._responder(respuesta, movido)

	def deshacer(self) -> None:
		tones.beep(*TONO_ERROR)
		# Translators: said when pressing Control+Z in a lesson.
		ui.message(_("In the lessons there is nothing to undo: a letter that does not fit is not written."))

	def dar_ayuda(self, describir: Callable[["Partida"], str]) -> None:
		palabra = describir is anunciador.describir_ayuda_palabra
		ui.message(self.ventana.sesion.ayuda(palabra))
		# Las ayudas pedidas cuentan para las estrellas: se guardan aunque se cierre la ventana.
		self.ventana.al_cambiar()

	def _responder(self, respuesta: Respuesta, movido: bool) -> None:
		if respuesta.error:
			tones.beep(*TONO_ERROR)
		if respuesta.aceptada:
			self.ventana.al_cambiar()
		if respuesta.superado:
			self.panel.Refresh()
			self.ventana.al_superar(respuesta.mensaje)
			return
		if respuesta.completadas:
			sonidos.reproducir(sonidos.COMPLETADO)
		if movido:
			self._ir_a_la_casilla(prefijo=respuesta.mensaje)
		else:
			self._decir_en_el_sitio(respuesta.mensaje)

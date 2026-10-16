# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Ventana del tablero: el dibujo para quien ve la pantalla, las letras, el menú del tablero y el guardado."""

import time
from collections.abc import Callable

import ui
import winUser
import wx
from gui.message import MessageDialog, ReturnCode, displayDialogAsModal
from logHandler import log

from ..crucigrama import anunciador, vista
from ..crucigrama.estadisticas import texto_tiempo
from ..crucigrama.partida import Partida
from ..nucleo.tablero_virtual import CuadriculaVirtual
from . import archivos, atajos, sonidos
from .dialogos import DialogoPistas
from .tablero_crucigrama import CuadriculaCrucigrama
from . import traduccion

traduccion.iniciar()

# Colores del dibujo: contraste alto entre casillas, letras, huecos y foco.
_COLOR_FONDO = wx.Colour(40, 40, 40)
_COLOR_CASILLA = wx.Colour(255, 255, 255)
_COLOR_HUECO = wx.Colour(0, 0, 0)
_COLOR_LINEA = wx.Colour(120, 120, 120)
_COLOR_FOCO = wx.Colour(30, 111, 217)
_COLOR_PALABRA = wx.Colour(210, 228, 255)
_COLOR_LETRA = wx.Colour(20, 70, 170)
_COLOR_NUMERO = wx.Colour(60, 60, 60)

_MARGEN = 20
_TAMANO_INICIAL = 640


class PanelTablero(wx.Panel):
	"""Dibuja el tablero y recibe el foco del sistema. NVDA lo cambia por la casilla virtual.

	Las teclas que no son órdenes llegan aquí como caracteres: las letras se escriben en el tablero.
	"""

	def __init__(self, padre: wx.Window, nombre: str) -> None:
		super().__init__(padre, style=wx.WANTS_CHARS)
		self.SetLabel(nombre)
		self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
		self.cuadricula: CuadriculaVirtual | None = None
		self.Bind(wx.EVT_PAINT, self._al_pintar)
		self.Bind(wx.EVT_SIZE, lambda evento: self.Refresh())
		self.Bind(wx.EVT_CHAR, self._al_escribir)

	def AcceptsFocus(self) -> bool:
		return True

	def _al_escribir(self, evento: wx.KeyEvent) -> None:
		codigo = evento.GetUnicodeKey()
		cuadricula = self.cuadricula
		# Las teclas sin carácter visible (Intro, Espacio, teclas de control) no hacen nada.
		if codigo == wx.WXK_NONE or not isinstance(cuadricula, CuadriculaCrucigrama):
			return
		caracter = chr(codigo)
		if caracter.isprintable() and not caracter.isspace():
			cuadricula.escribir(caracter)

	def _lado_casilla(self) -> int:
		ancho, alto = self.GetClientSize()
		if self.cuadricula is None:
			return 8
		filas, columnas = self.cuadricula.filas, self.cuadricula.columnas
		return max(8, min((ancho - 2 * _MARGEN) // columnas, (alto - 2 * _MARGEN) // filas))

	def _esquina_tablero(self, lado: int) -> tuple[int, int]:
		"""Dónde empieza el tablero: centrado en el panel, con al menos el margen alrededor.

		Al maximizar la ventana sobra ancho (o alto): el espacio se reparte a los dos lados.
		"""
		if self.cuadricula is None:
			return _MARGEN, _MARGEN
		ancho, alto = self.GetClientSize()
		x = max(_MARGEN, (ancho - self.cuadricula.columnas * lado) // 2)
		y = max(_MARGEN, (alto - self.cuadricula.filas * lado) // 2)
		return x, y

	def rectangulo_casilla(self, fila: int, columna: int) -> tuple[int, int, int, int]:
		lado = self._lado_casilla()
		x, y = self._esquina_tablero(lado)
		return (x + columna * lado, y + fila * lado, lado, lado)

	def _al_pintar(self, evento: wx.PaintEvent) -> None:
		dc = wx.AutoBufferedPaintDC(self)
		dc.SetBackground(wx.Brush(_COLOR_FONDO))
		dc.Clear()
		cuadricula = self.cuadricula
		if not isinstance(cuadricula, CuadriculaCrucigrama):
			return
		partida = cuadricula.partida
		lado = self._lado_casilla()
		palabra = set(partida.palabra_actual.casillas())
		inicios = {(p.fila, p.columna): p.numero for p in partida.crucigrama.palabras}
		fuente_letra = wx.Font(wx.FontInfo(max(6, int(lado * 0.5))).Bold())
		fuente_numero = wx.Font(wx.FontInfo(max(5, int(lado * 0.22))))
		dc.SetPen(wx.Pen(_COLOR_LINEA, 1))
		for fila in range(cuadricula.filas):
			for columna in range(cuadricula.columnas):
				x, y, _ancho, _alto = self.rectangulo_casilla(fila, columna)
				casilla = (fila, columna)
				if not partida.es_casilla(casilla):
					# Casilla sin letra: negra, como en los crucigramas de papel.
					dc.SetBrush(wx.Brush(_COLOR_HUECO))
					dc.DrawRectangle(x, y, lado, lado)
					continue
				dc.SetBrush(wx.Brush(_COLOR_PALABRA if casilla in palabra else _COLOR_CASILLA))
				dc.DrawRectangle(x, y, lado, lado)
				if casilla in inicios:
					dc.SetFont(fuente_numero)
					dc.SetTextForeground(_COLOR_NUMERO)
					dc.DrawText(str(inicios[casilla]), x + 2, y + 1)
				letra = partida.letra(casilla)
				if letra:
					dc.SetFont(fuente_letra)
					dc.SetTextForeground(_COLOR_LETRA)
					ancho_texto, alto_texto = dc.GetTextExtent(letra)
					dc.DrawText(
						letra,
						x + (lado - ancho_texto) // 2,
						y + (lado - alto_texto) // 2 + lado // 10,
					)
		x, y, _ancho, _alto = self.rectangulo_casilla(cuadricula.fila, cuadricula.columna)
		dc.SetBrush(wx.TRANSPARENT_BRUSH)
		dc.SetPen(wx.Pen(_COLOR_FOCO, max(3, lado // 10)))
		dc.DrawRectangle(x, y, lado, lado)


class VentanaBase(wx.Frame):
	"""Ventana con un tablero: lo que comparten el juego y las lecciones."""

	cuadricula: CuadriculaCrucigrama
	partida: Partida

	def __init__(self, titulo: str, nombre_tablero: str, al_cerrar: Callable[[], None]) -> None:
		super().__init__(None, title=titulo, size=(_TAMANO_INICIAL, _TAMANO_INICIAL))
		self._al_cerrar = al_cerrar
		self._cerrando_sin_preguntar = False
		self._iniciada = False
		self.panel = PanelTablero(self, nombre_tablero)
		self.Bind(wx.EVT_CLOSE, self._al_cerrar_ventana)
		self.Bind(wx.EVT_ACTIVATE, self._al_activar)
		self.CentreOnScreen()

	def _instalar(self, cuadricula: CuadriculaVirtual) -> None:
		"""Cada subclase crea su cuadrícula después de inicializar la ventana y la instala aquí."""
		self.cuadricula = cuadricula
		self.panel.cuadricula = cuadricula

	def _al_mostrar_por_primera_vez(self) -> None:
		"""Se llama una sola vez, cuando la ventana se muestra por primera vez."""

	def mostrar(self) -> None:
		self.Show()
		self.Raise()
		winUser.setForegroundWindow(self.GetHandle())
		self.panel.SetFocus()
		if not self._iniciada:
			self._iniciada = True
			self._al_mostrar_por_primera_vez()

	def cerrar_sin_preguntar(self) -> None:
		self._cerrando_sin_preguntar = True
		self.Close(force=True)

	def _al_activar(self, evento: wx.ActivateEvent) -> None:
		if evento.GetActive():
			self.panel.SetFocus()
		evento.Skip()

	def _al_cerrar_ventana(self, evento: wx.CloseEvent) -> None:
		self._antes_de_destruir()
		self.cuadricula.cerrar()
		self._al_cerrar()
		self.Destroy()

	def _antes_de_destruir(self) -> None:
		"""Se llama justo antes de cerrar la ventana."""

	def _confirmar(self, mensaje: str, titulo: str) -> bool:
		"""Pregunta Aceptar o Cancelar."""
		return MessageDialog.confirm(mensaje, titulo, parent=self) == ReturnCode.OK

	def mostrar_menu(self, opciones: list[tuple[str, Callable[[], None], bool]]) -> None:
		"""Menú emergente sobre la casilla actual. Cada opción: (texto, acción, habilitada)."""
		menu = wx.Menu()
		for texto, accion, habilitada in opciones:
			elemento = menu.Append(wx.ID_ANY, texto)
			elemento.Enable(habilitada)
			menu.Bind(wx.EVT_MENU, lambda evento, accion=accion: wx.CallAfter(accion), elemento)
		wx.CallAfter(self._abrir_menu, menu)

	def _abrir_menu(self, menu: wx.Menu) -> None:
		x, y, lado, _alto = self.panel.rectangulo_casilla(self.cuadricula.fila, self.cuadricula.columna)
		try:
			self.panel.PopupMenu(menu, wx.Point(x + lado // 2, y + lado // 2))
		finally:
			menu.Destroy()

	# Lo que necesita el tablero de su ventana (el juego y las lecciones lo redefinen).

	def mostrar_pistas(self) -> None:
		"""F4: la lista de pistas. Al cerrarla, el foco vuelve a la casilla de la palabra elegida."""
		wx.CallAfter(self._mostrar_pistas)

	def _mostrar_pistas(self) -> None:
		dialogo = DialogoPistas(self, self.partida)
		try:
			if displayDialogAsModal(dialogo) == wx.ID_OK:
				self.cuadricula.ir_a_palabra(dialogo.palabra_elegida())
		finally:
			dialogo.Destroy()

	def al_cambiar(self) -> None:
		"""Se llama después de cada cambio en el tablero."""

	def al_resolver(self) -> None:
		"""Se llama cuando el crucigrama queda resuelto."""

	def mostrar_menu_tablero(self) -> None:
		raise NotImplementedError

	def mostrar_atajos(self) -> None:
		raise NotImplementedError


def titulo_ventana(partida: Partida) -> str:
	"""«MiCrucigramaAccesible - Mediano, Normal, 12 palabras» y, si es sin ayudas, «…, sin ayudas»."""
	descripcion = vista.descripcion(partida.crucigrama)
	if partida.del_dia:
		# Translators: added before the description in the title of the crossword of the day.
		del_dia = _("Crossword of the day")
		descripcion = f"{del_dia}, {descripcion}"
	if not partida.con_ayudas:
		# Translators: added to the title of the board window of a crossword without help.
		sin_ayudas = _("without help")
		descripcion = f"{descripcion}, {sin_ayudas}"
	# Translators: title of the board window, as in "MiCrucigramaAccesible - Medium, Normal, 12 words".
	return _("MiCrucigramaAccesible - {description}").format(description=descripcion)


class VentanaCrucigrama(VentanaBase):
	"""Ventana del crucigrama. Se cierra con Escape, con Alt+F4 o desde su menú, sin perder nada:
	cada cambio se guarda, y el tiempo cuenta solo mientras la ventana está activa."""

	cuadricula: CuadriculaCrucigrama

	def __init__(
		self,
		partida: Partida,
		al_cerrar: Callable[[], None],
		al_pedir_nuevo: Callable[[], None],
		al_resolver: Callable[[Partida], str],
	) -> None:
		super().__init__(
			titulo_ventana(partida),
			# Translators: accessible name of the crossword board.
			_("Crossword board"),
			al_cerrar,
		)
		self.partida = partida
		self._al_pedir_nuevo = al_pedir_nuevo
		self._al_resolver = al_resolver
		# Momento en que la ventana se activó por última vez (None si no está activa).
		self._activa_desde: float | None = None
		self._instalar(CuadriculaCrucigrama(self.panel, self))

	# Tiempo.

	def _al_activar(self, evento: wx.ActivateEvent) -> None:
		if evento.GetActive():
			# Al volver a la ventana se dice también la palabra y su pista.
			self.cuadricula.olvidar_palabra()
			if not self.partida.resuelto:
				self._activa_desde = time.monotonic()
		else:
			self._sumar_tiempo()
			self._activa_desde = None
		super()._al_activar(evento)

	def _sumar_tiempo(self) -> None:
		if self._activa_desde is None:
			return
		ahora = time.monotonic()
		self.partida.segundos += ahora - self._activa_desde
		self._activa_desde = ahora

	# Guardado.

	def guardar_automatico(self) -> None:
		"""Guarda el crucigrama para continuarlo. Uno resuelto se borra: ya no hay nada que continuar."""
		self._sumar_tiempo()
		# El crucigrama del día tiene su propio archivo: no pisa el normal que esté a medias.
		ruta = (
			archivos.ruta_guardado_del_dia() if self.partida.del_dia else archivos.ruta_guardado_automatico()
		)
		if self.partida.resuelto:
			archivos.borrar(ruta)
			return
		try:
			archivos.escribir(ruta, self.partida.a_json())
		except OSError:
			log.error("No se pudo guardar el crucigrama en curso", exc_info=True)

	def al_cambiar(self) -> None:
		"""Se llama después de cada cambio en el tablero."""
		self.guardar_automatico()

	def al_resolver(self) -> None:
		self._sumar_tiempo()
		self._activa_desde = None
		self.guardar_automatico()
		sonidos.reproducir(sonidos.RESUELTO)
		# Quien abrió la ventana anota las estadísticas y puede añadir algo: un récord o los días seguidos.
		extra = self._al_resolver(self.partida)
		# Translators: said when the whole crossword is solved; the time is only informative.
		resuelto = _("Crossword solved! Congratulations! Time: {time}.").format(
			time=texto_tiempo(self.partida.segundos),
		)
		ui.message(f"{resuelto} {extra}".strip())

	def _antes_de_destruir(self) -> None:
		self.guardar_automatico()

	# Menú del tablero.

	def mostrar_menu_tablero(self) -> None:
		self.mostrar_menu(
			[
				# Translators: item of the menu of the crossword board.
				(_("C&heck"), self._comprobar, not self.partida.resuelto),
				# Translators: item of the menu of the crossword board.
				(_("&Restart"), self._reiniciar, self.partida.empezado),
				# Translators: item of the menu of the crossword board.
				(_("&New crossword..."), self._al_pedir_nuevo, True),
				# Translators: item of the menu of the crossword board.
				(_("&Keyboard shortcuts"), self.mostrar_atajos, True),
				# Translators: item of the menu of the crossword board.
				(_("&Close the board"), self.Close, True),
			],
		)

	def mostrar_atajos(self) -> None:
		wx.CallAfter(atajos.mostrar, self.cuadricula.celda_actual)

	def _comprobar(self) -> None:
		# Al cerrar el menú, NVDA anuncia la casilla: el resultado se dice después.
		self.cuadricula.decir_al_volver(anunciador.describir_comprobacion(self.partida))

	def _reiniciar(self) -> None:
		if not self._confirmar(
			# Translators: asked before restarting the crossword.
			_("All the letters you wrote will be deleted. Restart?"),
			# Translators: title of the confirmation to restart the crossword.
			_("Restart"),
		):
			return
		self.partida.reiniciar()
		if self.IsActive():
			self._activa_desde = time.monotonic()
		self.cuadricula.ir_a_palabra(self.partida.palabra_actual)
		self.cuadricula.olvidar_palabra()
		self.guardar_automatico()
		# Translators: said after restarting the crossword.
		self.cuadricula.decir_al_volver(_("Crossword restarted."))

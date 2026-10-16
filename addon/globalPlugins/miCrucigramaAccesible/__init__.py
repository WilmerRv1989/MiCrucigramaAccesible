# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Punto de entrada del complemento: el submenú en Herramientas de NVDA y el tablero abierto."""

import datetime
import os
import threading
from collections.abc import Callable

import globalPluginHandler
import globalVars
import gui
import ui
import wx
from gui.message import MessageDialog, ReturnCode, displayDialogAsModal
from logHandler import log
from NVDAObjects import NVDAObject
from NVDAObjects.window import Window
from scriptHandler import script

from .crucigrama import diario, idioma
from .crucigrama.estadisticas import Estadisticas, texto_racha
from .crucigrama.partida import Partida
from .interfaz import archivos, atajos, dialogos, estadisticas, preferencias
from .interfaz.curso import ControladorCurso
from .interfaz.panel_configuracion import PanelMiCrucigrama
from .interfaz.tablero_crucigrama import CeldaCrucigrama
from .interfaz.ventana_tablero import VentanaCrucigrama
from .nucleo import tablero_virtual
from .interfaz import traduccion

traduccion.iniciar()
idioma.configurar(_, ngettext)

# Translators: name of the add-on, used as the submenu label and the input gestures category.
NOMBRE = _("MiCrucigramaAccesible")

# Lo último elegido en el diálogo de nuevo crucigrama y las opciones del panel.
preferencias.registrar()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = NOMBRE

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._elemento_submenu: wx.MenuItem | None = None
		self._elemento_continuar: wx.MenuItem | None = None
		self._ventana: VentanaCrucigrama | None = None
		self._curso: ControladorCurso | None = None
		# Mientras se genera un crucigrama en otro hilo, no se empieza otro.
		self._generando = False
		self._terminado = False
		# En las pantallas seguras (inicio de sesión, control de cuentas) no hay menús ni ventanas.
		if globalVars.appArgs.secure:
			return
		self._crear_menu()
		self._actualizar_menu()
		PanelMiCrucigrama.al_borrar_estadisticas = self._borrar_estadisticas
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(PanelMiCrucigrama)

	# Menú en Herramientas.

	def _crear_menu(self) -> None:
		bandeja = gui.mainFrame.sysTrayIcon
		self._submenu = wx.Menu()
		nuevo = self._submenu.Append(
			wx.ID_ANY,
			# Translators: item of the add-on submenu that starts a new crossword.
			_("&New crossword..."),
			# Translators: help text of the "New crossword" menu item.
			_("Choose a crossword and start it"),
		)
		bandeja.Bind(wx.EVT_MENU, lambda evento: self.nuevo_crucigrama(), nuevo)
		del_dia = self._submenu.Append(
			wx.ID_ANY,
			# Translators: item of the add-on submenu that opens the crossword of the day.
			_("Crossword of the &day"),
			# Translators: help text of the "Crossword of the day" menu item.
			_("A new crossword every day, the same for everyone"),
		)
		bandeja.Bind(wx.EVT_MENU, lambda evento: self.crucigrama_del_dia(), del_dia)
		aprender = self._submenu.Append(
			wx.ID_ANY,
			# Translators: item of the add-on submenu that opens the crossword course.
			_("&Learn to play..."),
			# Translators: help text of the "Learn to play" menu item.
			_("Guided lessons to learn how to solve crosswords"),
		)
		bandeja.Bind(wx.EVT_MENU, lambda evento: self.aprender_a_jugar(), aprender)
		elemento_estadisticas = self._submenu.Append(
			wx.ID_ANY,
			# Translators: item of the add-on submenu that shows the statistics.
			_("My &statistics..."),
			# Translators: help text of the "My statistics" menu item.
			_("Crosswords solved, best times and days in a row"),
		)
		bandeja.Bind(wx.EVT_MENU, lambda evento: wx.CallAfter(estadisticas.mostrar), elemento_estadisticas)
		elemento_atajos = self._submenu.Append(
			wx.ID_ANY,
			# Translators: item of the add-on submenu that shows all the keyboard shortcuts.
			_("&Keyboard shortcuts..."),
			# Translators: help text of the "Keyboard shortcuts" menu item.
			_("The keys of the board"),
		)
		bandeja.Bind(wx.EVT_MENU, lambda evento: self.mostrar_atajos(), elemento_atajos)
		self._elemento_continuar = wx.MenuItem(
			self._submenu,
			wx.ID_ANY,
			# Translators: item of the add-on submenu that opens the crossword in progress.
			_("&Continue the crossword"),
			# Translators: help text of the "Continue the crossword" menu item.
			_("Open the crossword you left unfinished"),
		)
		bandeja.Bind(wx.EVT_MENU, lambda evento: self.continuar_crucigrama(), self._elemento_continuar)
		self._elemento_submenu = bandeja.toolsMenu.AppendSubMenu(
			self._submenu,
			# Translators: label of the add-on submenu inside NVDA's Tools menu.
			_("Mi&CrucigramaAccesible"),
			# Translators: help text of the add-on submenu.
			_("Accessible crosswords"),
		)

	def _ventana_normal(self) -> VentanaCrucigrama | None:
		"""La ventana abierta si es de un crucigrama normal (no del crucigrama del día)."""
		if self._ventana is not None and not self._ventana.partida.del_dia:
			return self._ventana
		return None

	def _hay_para_continuar(self) -> bool:
		"""Si hay un crucigrama normal sin terminar: abierto o guardado."""
		ventana = self._ventana_normal()
		if ventana is not None:
			return not ventana.partida.resuelto
		return os.path.isfile(archivos.ruta_guardado_automatico())

	def _actualizar_menu(self) -> None:
		"""«Continuar el crucigrama» solo aparece si hay uno sin terminar."""
		elemento = self._elemento_continuar
		if elemento is None:
			return
		hay = self._hay_para_continuar()
		esta_en_menu = self._submenu.FindItemById(elemento.GetId()) is not None
		if hay and not esta_en_menu:
			# Justo después de «Nuevo crucigrama...».
			self._submenu.Insert(1, elemento)
		elif not hay and esta_en_menu:
			self._submenu.Remove(elemento)

	def terminate(self) -> None:
		self._terminado = True
		if PanelMiCrucigrama in gui.settingsDialogs.NVDASettingsDialog.categoryClasses:
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(PanelMiCrucigrama)
		PanelMiCrucigrama.al_borrar_estadisticas = None
		preferencias.quitar()
		if self._curso is not None:
			self._curso.cerrar()
			self._curso = None
		if self._ventana is not None:
			# Se guarda al cerrarse, para continuarlo al volver a NVDA.
			self._ventana.cerrar_sin_preguntar()
			self._ventana = None
		if (
			self._elemento_continuar is not None
			and self._submenu.FindItemById(self._elemento_continuar.GetId()) is None
		):
			# Si no está en el menú, nadie más lo destruye.
			self._elemento_continuar.Destroy()
		self._elemento_continuar = None
		if self._elemento_submenu is not None:
			try:
				gui.mainFrame.sysTrayIcon.toolsMenu.Remove(self._elemento_submenu)
				self._elemento_submenu.Destroy()
			except (RuntimeError, AttributeError):
				log.debugWarning("No se pudo quitar el menú de MiCrucigramaAccesible", exc_info=True)
			self._elemento_submenu = None
		super().terminate()

	# Crucigramas guardados.

	def _leer_guardado(self, ruta: str | None = None) -> Partida | None:
		"""El crucigrama sin terminar que quedó guardado. Si el archivo está dañado, se borra."""
		ruta = ruta or archivos.ruta_guardado_automatico()
		if not os.path.isfile(ruta):
			return None
		try:
			return Partida.desde_json(archivos.leer(ruta))
		except (OSError, ValueError):
			log.debugWarning("No se pudo leer el crucigrama guardado", exc_info=True)
			archivos.borrar(ruta)
			return None

	def _hay_crucigrama_a_medias(self) -> bool:
		"""Si hay un crucigrama normal sin terminar con algo escrito, que se perdería al empezar otro."""
		ventana = self._ventana_normal()
		partida = ventana.partida if ventana is not None else self._leer_guardado()
		return partida is not None and partida.empezado and not partida.resuelto

	# Tablero.

	def nuevo_crucigrama(self) -> None:
		wx.CallAfter(self._nuevo_crucigrama)

	def _nuevo_crucigrama(self) -> None:
		if self._generando:
			# Translators: reported when asking for a crossword while another one is being prepared.
			ui.message(_("A crossword is already being prepared."))
			return
		padre = self._ventana if self._ventana is not None and self._ventana.IsShown() else gui.mainFrame
		dialogo = dialogos.DialogoNuevoCrucigrama(
			padre,
			preferencias.tema_guardado(),
			preferencias.tamano_guardado(),
			preferencias.dificultad_guardada(),
			preferencias.ayudas_guardadas(),
		)
		try:
			if displayDialogAsModal(dialogo) != wx.ID_OK:
				return
			tamano = dialogo.tamano_elegido()
			dificultad = dialogo.dificultad_elegida()
			tema = dialogo.tema_elegido()
			ayudas = dialogo.ayudas_elegidas()
			preferencias.guardar(tema, dialogo.tamano_de_la_lista(), dialogo.dificultad_de_la_lista(), ayudas)
		finally:
			dialogo.Destroy()
		if self._hay_crucigrama_a_medias():
			respuesta = MessageDialog.confirm(
				_(
					# Translators: asked when starting a new crossword while another one is unfinished.
					"You have an unfinished crossword. If you start a new one, it will be lost. Start a new crossword?",
				),
				# Translators: title of the confirmation to start a new crossword.
				_("New crossword"),
				parent=padre,
			)
			if respuesta != ReturnCode.OK:
				return
		self._generar(
			# Translators: said while a new crossword is generated.
			_("Preparing the crossword..."),
			lambda: Partida(dialogos.crear(tamano, dificultad, tema), con_ayudas=ayudas),
		)

	def _generar(self, aviso: str, crear: Callable[[], Partida]) -> None:
		"""En otro hilo: el banco se lee y el crucigrama se genera sin que NVDA se pare."""
		self._generando = True
		ui.message(aviso)

		def generar() -> None:
			try:
				partida: Partida | None = crear()
			except Exception:
				log.error("No se pudo generar el crucigrama", exc_info=True)
				partida = None
			wx.CallAfter(self._al_generar, partida)

		threading.Thread(target=generar, daemon=True).start()

	def _al_generar(self, partida: Partida | None) -> None:
		self._generando = False
		if self._terminado:
			return
		if partida is None:
			# Translators: reported when a crossword could not be generated.
			ui.message(_("The crossword could not be prepared. Please try again."))
			return
		self._abrir(partida)

	def continuar_crucigrama(self) -> None:
		wx.CallAfter(self._continuar_crucigrama)

	def _continuar_crucigrama(self) -> None:
		ventana = self._ventana_normal()
		if ventana is not None:
			ventana.mostrar()
			return
		partida = self._leer_guardado()
		if partida is None:
			self._actualizar_menu()
			MessageDialog.alert(
				# Translators: reported when the saved crossword cannot be opened.
				_("The unfinished crossword could not be opened. You can start a new one."),
				# Translators: title of the message about the saved crossword.
				_("Continue the crossword"),
			)
			return
		self._abrir(partida)

	def _abrir(self, partida: Partida) -> None:
		"""Abre un crucigrama. La ventana que hubiera se cierra: su crucigrama queda guardado."""
		if self._ventana is not None:
			self._ventana.cerrar_sin_preguntar()
			self._ventana = None
		self._ventana = VentanaCrucigrama(
			partida,
			al_cerrar=self._al_cerrar_ventana,
			al_pedir_nuevo=self.nuevo_crucigrama,
			al_resolver=self._al_resolver,
		)
		# Un crucigrama nuevo sustituye al que quedó guardado.
		self._ventana.guardar_automatico()
		self._ventana.mostrar()
		self._actualizar_menu()

	def _al_cerrar_ventana(self) -> None:
		self._ventana = None
		self._actualizar_menu()

	def _al_resolver(self, partida: Partida) -> str:
		"""Anota el crucigrama resuelto en las estadísticas. Devuelve lo que se añade a la felicitación."""
		datos = Estadisticas(archivos.ruta_estadisticas())
		crucigrama = partida.crucigrama
		partes = []
		if datos.registrar_resuelto(
			crucigrama.tamano,
			crucigrama.dificultad,
			crucigrama.tema,
			partida.segundos,
			partida.con_ayudas,
			partida.ayudas,
		):
			# Translators: said after solving a crossword faster than ever in that size and difficulty.
			partes.append(_("It is your best time in this kind of crossword!"))
		if partida.del_dia:
			racha = datos.registrar_del_dia(datetime.date.fromisoformat(partida.del_dia))
			partes.append(texto_racha(racha))
		try:
			datos.guardar()
		except OSError:
			log.error("No se pudieron guardar las estadísticas", exc_info=True)
		self._actualizar_menu()
		return " ".join(partes)

	def _borrar_estadisticas(self) -> bool:
		"""Cierra la lección abierta y borra el progreso del curso y las estadísticas."""
		if self._curso is not None:
			self._curso.cerrar()
			# Se vuelve a crear al abrirlo, ya sin progreso.
			self._curso = None
		archivos.borrar(archivos.ruta_progreso())
		archivos.borrar(archivos.ruta_leccion_en_curso())
		archivos.borrar(archivos.ruta_estadisticas())
		return True

	# Curso «Aprender a jugar».

	def aprender_a_jugar(self) -> None:
		if self._curso is None:
			try:
				self._curso = ControladorCurso()
			except Exception:
				log.error("No se pudo cargar el curso de MiCrucigramaAccesible", exc_info=True)
				return
		self._curso.abrir_lista()

	@script(
		# Translators: description of the command that opens the crossword course, shown in the Input gestures dialog.
		description=_("Opens the crossword course Learn to play"),
	)
	def script_aprender_a_jugar(self, gesture) -> None:
		self.aprender_a_jugar()

	# Crucigrama del día.

	def crucigrama_del_dia(self) -> None:
		wx.CallAfter(self._crucigrama_del_dia)

	def _crucigrama_del_dia(self) -> None:
		hoy = datetime.date.today()
		ventana = self._ventana
		if (
			ventana is not None
			and ventana.partida.del_dia == hoy.isoformat()
			and not ventana.partida.resuelto
		):
			ventana.mostrar()
			return
		datos = Estadisticas(archivos.ruta_estadisticas())
		if datos.resuelto_hoy(hoy):
			MessageDialog.alert(
				# Translators: said when opening the crossword of the day after solving it, as in "You already solved today's crossword. You have solved it 3 days in a row. Come back tomorrow for a new one."
				_("You already solved today's crossword. {streak} Come back tomorrow for a new one.").format(
					streak=texto_racha(datos.racha_actual(hoy)),
				),
				# Translators: title of the message about the crossword of the day.
				_("Crossword of the day"),
			)
			return
		ruta = archivos.ruta_guardado_del_dia()
		guardado = self._leer_guardado(ruta)
		if guardado is not None and guardado.del_dia == hoy.isoformat():
			self._abrir(guardado)
			return
		# El de otro día ya no se puede jugar.
		archivos.borrar(ruta)
		if self._generando:
			ui.message(_("A crossword is already being prepared."))
			return
		respuesta = MessageDialog.ask(
			# Translators: asked before starting the crossword of the day.
			_("How do you want to play today's crossword?"),
			# Translators: title of the message about the crossword of the day.
			_("Crossword of the day"),
			# Translators: button to play the crossword of the day with help.
			yesLabel=_("&With help"),
			# Translators: button to play the crossword of the day without help.
			noLabel=_("With&out help"),
		)
		if respuesta not in (ReturnCode.YES, ReturnCode.NO):
			return
		ayudas = respuesta == ReturnCode.YES

		def crear() -> Partida:
			partida = Partida(
				diario.crucigrama_del_dia(dialogos.cargar_banco("general"), hoy),
				con_ayudas=ayudas,
			)
			partida.del_dia = hoy.isoformat()
			return partida

		# Translators: said while the crossword of the day is generated.
		self._generar(_("Preparing the crossword of the day..."), crear)

	def mostrar_atajos(self) -> None:
		"""La lista de teclas, consultada con una casilla creada solo para eso."""
		# NVDA solo acepta crear sus objetos con argumentos por nombre.
		wx.CallAfter(atajos.mostrar, CeldaCrucigrama(cuadricula=None, fila=0, columna=0))

	# Integración con NVDA.

	def chooseNVDAObjectOverlayClasses(self, obj: NVDAObject, clsList: list[type[NVDAObject]]) -> None:
		# El panel que dibuja el tablero pasa el foco a la casilla virtual actual.
		if isinstance(obj, Window) and tablero_virtual.cuadricula_de_ventana(obj.windowHandle):
			clsList.insert(0, tablero_virtual.PanelCuadricula)

	@script(
		# Translators: description of the command that opens the crossword board, shown in the Input gestures dialog.
		description=_("Opens the crossword board: continues the unfinished crossword or starts a new one"),
	)
	def script_abrir_tablero(self, gesture) -> None:
		if self._hay_para_continuar():
			self.continuar_crucigrama()
		else:
			self.nuevo_crucigrama()

	@script(
		# Translators: description of the command that opens the crossword of the day, shown in the Input gestures dialog.
		description=_("Opens the crossword of the day"),
	)
	def script_crucigrama_del_dia(self, gesture) -> None:
		self.crucigrama_del_dia()

	@script(
		# Translators: description of the command that shows the statistics, shown in the Input gestures dialog.
		description=_("Shows your crossword statistics"),
	)
	def script_estadisticas(self, gesture) -> None:
		wx.CallAfter(estadisticas.mostrar)

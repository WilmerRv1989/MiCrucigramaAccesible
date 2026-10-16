# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""«Aprender a jugar»: lista de lecciones, presentación y ejercicios."""

import os

import languageHandler
import ui
import wx
from gui import guiHelper
from gui.message import displayDialogAsModal
from logHandler import log

from ..crucigrama.curso.modelo import Curso, Ejercicio, Leccion, cargar_curso, carpeta_de_idioma
from ..crucigrama.curso.progreso import Progreso
from ..crucigrama.curso.sesion import SesionEjercicio
from . import archivos, sonidos
from .ventana_leccion import VentanaLeccion, titulo_leccion
from . import traduccion

traduccion.iniciar()


def texto_estado(leccion: Leccion, progreso: Progreso) -> str:
	total = len(leccion.ejercicios)
	hechos = sum(1 for e in leccion.ejercicios if progreso.superado(e.id))
	if hechos == total:
		# Translators: state of a completed lesson in the list of lessons.
		return _("Completed, {stars} of {total} stars.").format(
			stars=progreso.estrellas_de(leccion),
			total=leccion.estrellas_posibles,
		)
	if hechos:
		# Translators: state of a lesson started but not finished, in the list of lessons.
		return _("In progress: {done} of {total} exercises.").format(done=hechos, total=total)
	# Translators: state of a lesson not started, in the list of lessons.
	return _("Pending.")


class DialogoLecciones(wx.Dialog):
	def __init__(self, curso: Curso, progreso: Progreso, seleccion: Leccion | None) -> None:
		# Translators: title of the list of lessons of the course.
		super().__init__(None, title=_("Learn to play"))
		self._lecciones = curso.lecciones
		textos = []
		for leccion in self._lecciones:
			texto = f"{leccion.id}. {leccion.titulo}. {texto_estado(leccion, progreso)}"
			bloque = curso.bloque_de(leccion)
			if bloque.lecciones[0] == leccion:
				# Translators: block heading before the first lesson of a block, as in "Block A, Getting to know the crossword."
				encabezado = _("Block {block}, {title}.").format(block=bloque.id, title=bloque.titulo)
				texto = f"{encabezado} {texto}"
			textos.append(texto)
		principal = wx.BoxSizer(wx.VERTICAL)
		ayudante = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.lista: wx.ListBox = ayudante.addLabeledControl(
			# Translators: label of the list of lessons.
			_("&Lessons:"),
			wx.ListBox,
			choices=textos,
			size=(560, 320),
		)
		botones = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that starts the selected lesson.
		empezar = botones.addButton(self, id=wx.ID_OK, label=_("&Start"))
		# Translators: button that closes the list of lessons.
		botones.addButton(self, id=wx.ID_CANCEL, label=_("&Close"))
		ayudante.addDialogDismissButtons(botones, separated=True)
		principal.Add(ayudante.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(principal)
		principal.Fit(self)
		empezar.SetDefault()
		self.SetEscapeId(wx.ID_CANCEL)
		self.lista.SetSelection(self._indice_inicial(progreso, seleccion))
		self.lista.Bind(wx.EVT_LISTBOX_DCLICK, lambda evento: self.EndModal(wx.ID_OK))
		self.CentreOnScreen()
		self.lista.SetFocus()

	def _indice_inicial(self, progreso: Progreso, seleccion: Leccion | None) -> int:
		if seleccion is not None and seleccion in self._lecciones:
			return self._lecciones.index(seleccion)
		for indice, leccion in enumerate(self._lecciones):
			if not progreso.leccion_completada(leccion):
				return indice
		return 0

	def leccion_elegida(self) -> Leccion:
		return self._lecciones[max(0, self.lista.GetSelection())]


class DialogoPresentacion(wx.Dialog):
	"""Explicación de la lección. NVDA lee el texto al abrirse; NVDA+B lo vuelve a leer."""

	def __init__(self, leccion: Leccion, indice_inicial: int) -> None:
		super().__init__(None, title=titulo_leccion(leccion))
		parrafos = list(leccion.explicacion)
		cantidad = len(leccion.ejercicios)
		parrafos.append(
			ngettext(
				# Translators: said at the end of a lesson explanation.
				"This lesson has {count} exercise.",
				"This lesson has {count} exercises.",
				cantidad,
			).format(count=cantidad),
		)
		if indice_inicial:
			# Translators: said when a lesson is resumed, as in "You will continue from exercise 3."
			parrafos.append(_("You will continue from exercise {number}.").format(number=indice_inicial + 1))
		principal = wx.BoxSizer(wx.VERTICAL)
		ayudante = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		for parrafo in parrafos:
			texto = wx.StaticText(self, label=parrafo)
			texto.Wrap(520)
			ayudante.addItem(texto)
		botones = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that starts the exercises of a lesson.
		empezar = botones.addButton(self, id=wx.ID_OK, label=_("&Start"))
		# Translators: button that goes back to the list of lessons.
		botones.addButton(self, id=wx.ID_CANCEL, label=_("&Back"))
		ayudante.addDialogDismissButtons(botones, separated=True)
		principal.Add(ayudante.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(principal)
		principal.Fit(self)
		empezar.SetDefault()
		self.SetEscapeId(wx.ID_CANCEL)
		self.CentreOnScreen()
		empezar.SetFocus()


class ControladorCurso:
	"""Lleva la lección en curso. Solo hay una ventana de lección a la vez."""

	def __init__(self) -> None:
		self.curso = cargar_curso(carpeta_de_idioma(languageHandler.getLanguage()))
		self.progreso = Progreso(archivos.ruta_progreso())
		self.ventana: VentanaLeccion | None = None
		self.leccion: Leccion | None = None
		self.indice = 0

	def cerrar(self) -> None:
		if self.ventana is not None:
			self.ventana.cerrar_sin_preguntar()
			self.ventana = None

	def al_cerrar_ventana(self) -> None:
		self.ventana = None

	# Lista y presentación.

	def abrir_lista(self, seleccion: Leccion | None = None) -> None:
		wx.CallAfter(self._abrir_lista, seleccion or self.leccion)

	def _abrir_lista(self, seleccion: Leccion | None) -> None:
		dialogo = DialogoLecciones(self.curso, self.progreso, seleccion)
		try:
			respuesta = displayDialogAsModal(dialogo)
			leccion = dialogo.leccion_elegida()
		finally:
			dialogo.Destroy()
		if respuesta == wx.ID_OK:
			self._presentar(leccion)

	def _presentar(self, leccion: Leccion) -> None:
		indice = self.progreso.primer_pendiente(leccion)
		dialogo = DialogoPresentacion(leccion, indice)
		try:
			respuesta = displayDialogAsModal(dialogo)
		finally:
			dialogo.Destroy()
		if respuesta != wx.ID_OK:
			self._abrir_lista(leccion)
			return
		self._empezar(leccion, indice)

	def siguiente_leccion(self) -> None:
		if self.leccion is None:
			return
		siguiente = self.curso.siguiente(self.leccion)
		if siguiente is not None:
			wx.CallAfter(self._presentar, siguiente)

	# Ejercicios de la lección.

	def _empezar(self, leccion: Leccion, indice: int) -> None:
		self.cerrar()
		self.leccion = leccion
		self.indice = indice
		sesion = self._sesion(leccion.ejercicios[indice])
		self.ventana = VentanaLeccion(self, leccion, sesion, indice, len(leccion.ejercicios))
		self.ventana.mostrar()

	def _sesion(self, ejercicio: Ejercicio) -> SesionEjercicio:
		"""Un ejercicio de la lección. Si es un crucigrama entero que quedó a medias, sigue donde estaba."""
		sesion = SesionEjercicio(ejercicio)
		ruta = archivos.ruta_leccion_en_curso()
		if sesion.se_guarda and os.path.isfile(ruta):
			try:
				sesion.continuar(archivos.leer(ruta))
			except OSError:
				log.debugWarning("No se pudo leer la lección en curso", exc_info=True)
		return sesion

	def guardar_en_curso(self) -> None:
		"""Tras cada cambio o ayuda en un crucigrama entero de una lección."""
		ventana = self.ventana
		if ventana is None or not ventana.sesion.se_guarda:
			return
		try:
			archivos.escribir(archivos.ruta_leccion_en_curso(), ventana.sesion.a_json())
		except OSError:
			log.error("No se pudo guardar la lección en curso", exc_info=True)

	def al_superar(self, mensaje: str) -> None:
		ventana = self.ventana
		leccion = self.leccion
		if ventana is None or leccion is None:
			return
		sesion = ventana.sesion
		felicitacion = f"{mensaje}. {sesion.texto_superado()}"
		self.progreso.registrar(sesion.ejercicio.id, sesion.estrellas)
		self._guardar_progreso()
		if sesion.ejercicio.entero:
			archivos.borrar(archivos.ruta_leccion_en_curso())
		siguiente = self.indice + 1
		if siguiente < len(leccion.ejercicios):
			sonidos.reproducir(sonidos.EXITO)
			self.indice = siguiente
			nueva = self._sesion(leccion.ejercicios[siguiente])
			ventana.cargar(nueva, siguiente, felicitacion)
			return
		sonidos.reproducir(sonidos.RESUELTO)
		ui.message(felicitacion)
		ui.message(self._texto_final(leccion))

	def _guardar_progreso(self) -> None:
		try:
			self.progreso.guardar()
		except OSError:
			log.error("No se pudo guardar el progreso del curso", exc_info=True)

	def _texto_final(self, leccion: Leccion) -> str:
		partes = [
			# Translators: said when a lesson is finished, as in "You finished lesson 1! You have 5 of 6 stars."
			_("You finished lesson {id}! You have {stars} of {total} stars.").format(
				id=leccion.id,
				stars=self.progreso.estrellas_de(leccion),
				total=leccion.estrellas_posibles,
			),
		]
		bloque = self.curso.bloque_de(leccion)
		if bloque.lecciones[-1] == leccion:
			partes.append(bloque.mensaje_final)
		if self.curso.siguiente(leccion) is not None:
			# Translators: said at the end of a lesson.
			partes.append(_("Open the menu with the Applications key to go on to the next lesson."))
		return " ".join(partes)

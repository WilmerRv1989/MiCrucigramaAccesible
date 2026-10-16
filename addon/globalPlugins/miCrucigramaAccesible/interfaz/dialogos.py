# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Diálogos del complemento: elegir un crucigrama nuevo y la lista de pistas (F4)."""

import os
import random

import wx
from gui import guiHelper

from ..crucigrama import anunciador, banco, vista
from ..crucigrama.banco import Dificultad, Entrada
from ..crucigrama.generador import Crucigrama, PalabraColocada, Tamano, generar
from ..crucigrama.partida import Partida
from . import traduccion

traduccion.iniciar()

_CARPETA_BANCO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "banco")
_bancos: dict[str, list[Entrada]] = {}


def cargar_banco(nombre: str) -> list[Entrada]:
	"""El banco general o el infantil; se lee del disco la primera vez."""
	if nombre not in _bancos:
		_bancos[nombre] = banco.cargar(os.path.join(_CARPETA_BANCO, f"{nombre}.json"))
	return _bancos[nombre]


def crear(tamano: Tamano, dificultad: Dificultad, tema: str | None) -> Crucigrama:
	"""Un crucigrama nuevo con una semilla al azar."""
	entradas = cargar_banco("infantil" if tema else "general")
	return generar(entradas, tamano, dificultad, random.randrange(1_000_000), tema)


class DialogoNuevoCrucigrama(wx.Dialog):
	"""Elegir un crucigrama general (tamaño y dificultad) o uno infantil (tema), y si va con ayudas.

	Empieza con lo elegido la vez anterior.
	"""

	def __init__(
		self,
		padre: wx.Window | None,
		tema: str | None,
		tamano: Tamano,
		dificultad: Dificultad,
		ayudas: bool,
	) -> None:
		# Translators: title of the dialog to start a new crossword.
		super().__init__(padre, title=_("New crossword"))
		self._tamanos = list(Tamano)
		self._dificultades = list(Dificultad)
		principal = wx.BoxSizer(wx.VERTICAL)
		ayudante = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.tipo: wx.Choice = ayudante.addLabeledControl(
			# Translators: label of the choice between a general crossword and the children's themes.
			_("&Crossword:"),
			wx.Choice,
			choices=[
				# Translators: an option of the Crossword choice: a crossword for everyone.
				_("General"),
				*[
					# Translators: an option of the Crossword choice, for example "Children's: Animals".
					_("Children's: {theme}").format(theme=vista.nombre_tema(tema))
					for tema in vista.TEMAS
				],
			],
		)
		self.tamano: wx.Choice = ayudante.addLabeledControl(
			# Translators: label of the crossword size choice.
			_("&Size:"),
			wx.Choice,
			choices=[vista.nombre_tamano(t) for t in self._tamanos],
		)
		self.dificultad: wx.Choice = ayudante.addLabeledControl(
			# Translators: label of the crossword difficulty choice.
			_("&Difficulty:"),
			wx.Choice,
			choices=[vista.nombre_dificultad(d) for d in self._dificultades],
		)
		self.ayudas: wx.CheckBox = ayudante.addItem(
			wx.CheckBox(
				self,
				# Translators: checkbox of the new crossword dialog.
				label=_("With &help: F7 tells letters and words, and Check says where the mistakes are"),
			),
		)
		ayudante.addDialogDismissButtons(wx.OK | wx.CANCEL, separated=True)
		principal.Add(ayudante.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(principal)
		self.tipo.SetSelection(vista.TEMAS.index(tema) + 1 if tema in vista.TEMAS else 0)
		self.tamano.SetSelection(self._tamanos.index(tamano))
		self.dificultad.SetSelection(self._dificultades.index(dificultad))
		self.ayudas.SetValue(ayudas)
		self._actualizar()
		self.tipo.Bind(wx.EVT_CHOICE, lambda evento: self._actualizar())
		principal.Fit(self)
		self.CentreOnScreen()
		self.tipo.SetFocus()

	def _actualizar(self) -> None:
		"""Los crucigramas infantiles son siempre pequeños y fáciles: no se elige ni tamaño ni dificultad."""
		general = self.tema_elegido() is None
		self.tamano.Enable(general)
		self.dificultad.Enable(general)

	def tema_elegido(self) -> str | None:
		eleccion = self.tipo.GetSelection()
		return vista.TEMAS[eleccion - 1] if eleccion > 0 else None

	def tamano_de_la_lista(self) -> Tamano:
		"""El tamaño marcado en la lista (se recuerda aunque se juegue uno infantil)."""
		return self._tamanos[self.tamano.GetSelection()]

	def dificultad_de_la_lista(self) -> Dificultad:
		return self._dificultades[self.dificultad.GetSelection()]

	def tamano_elegido(self) -> Tamano:
		"""El tamaño del crucigrama que se va a jugar: los infantiles son siempre pequeños."""
		return Tamano.PEQUENO if self.tema_elegido() else self.tamano_de_la_lista()

	def dificultad_elegida(self) -> Dificultad:
		return Dificultad.FACIL if self.tema_elegido() else self.dificultad_de_la_lista()

	def ayudas_elegidas(self) -> bool:
		return self.ayudas.GetValue()


class DialogoPistas(wx.Dialog):
	"""F4: todas las pistas en una lista. Al aceptar, el cursor va a la palabra elegida."""

	def __init__(self, padre: wx.Window | None, partida: Partida) -> None:
		# Translators: title of the list of all the clues of the crossword.
		super().__init__(padre, title=_("Clues"))
		self._palabras = list(partida.orden)
		principal = wx.BoxSizer(wx.VERTICAL)
		ayudante = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		lineas = []
		for palabra in self._palabras:
			linea = anunciador.describir_palabra(palabra)
			if partida.completa(palabra):
				# Translators: added in the list of clues to a word with all its cells filled.
				linea = _("{clue} (complete)").format(clue=linea)
			lineas.append(linea)
		self.lista: wx.ListBox = ayudante.addLabeledControl(
			# Translators: label of the list of clues.
			_("&Clues:"),
			wx.ListBox,
			choices=lineas,
			size=(500, 300),
		)
		ayudante.addDialogDismissButtons(wx.OK | wx.CANCEL, separated=True)
		principal.Add(ayudante.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(principal)
		self.lista.SetSelection(self._palabras.index(partida.palabra_actual))
		self.lista.Bind(wx.EVT_LISTBOX_DCLICK, lambda evento: self.EndModal(wx.ID_OK))
		principal.Fit(self)
		self.CentreOnScreen()
		self.lista.SetFocus()

	def palabra_elegida(self) -> PalabraColocada:
		return self._palabras[self.lista.GetSelection()]

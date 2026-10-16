# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Panel del complemento en las opciones de NVDA (Preferencias, Opciones, MiCrucigramaAccesible)."""

from collections.abc import Callable
from typing import ClassVar

import ui
import wx
from gui import guiHelper
from gui.message import MessageDialog, ReturnCode
from gui.settingsDialogs import SettingsPanel

from . import preferencias, traduccion

traduccion.iniciar()


class PanelMiCrucigrama(SettingsPanel):
	# Translators: title of the add-on panel in NVDA's settings.
	title = _("MiCrucigramaAccesible")
	# Lo pone el complemento: borra el progreso y las estadísticas, y devuelve True si se pudo.
	al_borrar_estadisticas: ClassVar[Callable[[], bool] | None] = None

	def makeSettings(self, settingsSizer: wx.BoxSizer) -> None:
		ayudante = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		datos = preferencias.seccion()
		self.sonidos: wx.CheckBox = ayudante.addItem(
			# Translators: check box in the settings panel.
			wx.CheckBox(self, label=_("Play s&ounds (complete words, solved crosswords)")),
		)
		self.sonidos.SetValue(bool(datos["sonidos"]))
		self.cruces: wx.CheckBox = ayudante.addItem(
			# Translators: check box in the settings panel.
			wx.CheckBox(self, label=_("Say which word &crosses each cell")),
		)
		self.cruces.SetValue(bool(datos["decir_cruces"]))
		self.escrito: wx.CheckBox = ayudante.addItem(
			# Translators: check box in the settings panel.
			wx.CheckBox(self, label=_("Say what is &written when entering a word")),
		)
		self.escrito.SetValue(bool(datos["decir_escrito"]))
		borrar = ayudante.addItem(
			# Translators: button in the settings panel.
			wx.Button(self, label=_("&Delete my progress and statistics...")),
		)
		borrar.Bind(wx.EVT_BUTTON, self._al_borrar)

	def onSave(self) -> None:
		datos = preferencias.seccion()
		datos["sonidos"] = self.sonidos.GetValue()
		datos["decir_cruces"] = self.cruces.GetValue()
		datos["decir_escrito"] = self.escrito.GetValue()
		preferencias.aplicar()

	def _al_borrar(self, evento: wx.CommandEvent) -> None:
		respuesta = MessageDialog.confirm(
			_(
				# Translators: asked before deleting the statistics.
				"This deletes your progress in the course, the crosswords you solved, your best times "
				"and the days in a row. Unfinished crosswords are kept. It cannot be undone. Delete them?",
			),
			# Translators: title of the confirmation to delete the statistics.
			_("Delete my progress and statistics"),
			parent=self,
		)
		if respuesta != ReturnCode.OK:
			return
		borrar = type(self).al_borrar_estadisticas
		if borrar is not None and borrar():
			# Translators: reported after deleting the statistics.
			ui.message(_("Your progress and statistics were deleted."))

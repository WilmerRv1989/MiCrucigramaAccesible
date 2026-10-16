# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""La traducción del complemento: siempre en español.

Los crucigramas, sus pistas y el curso están en español, así que la interfaz también, aunque
NVDA esté en otro idioma. Hace lo mismo que `addonHandler.initTranslation`, pero con el catálogo
español en lugar del del idioma de NVDA. Los textos del código siguen en inglés, como es costumbre
en NVDA, y se traducen con addon/locale/es/LC_MESSAGES/nvda.po.
"""

import gettext
import inspect
import os

IDIOMA = "es"

_CARPETA_LOCALE = os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
	"locale",
)
_traducciones: gettext.NullTranslations | None = None


def catalogo() -> gettext.NullTranslations:
	global _traducciones
	if _traducciones is None:
		_traducciones = gettext.translation(
			"nvda",
			localedir=_CARPETA_LOCALE,
			languages=[IDIOMA],
			fallback=True,
		)
	return _traducciones


def iniciar() -> None:
	"""Pone `_` y `ngettext` en el módulo que la llama, como `addonHandler.initTranslation`."""
	marco = inspect.currentframe()
	try:
		llamador = marco.f_back if marco is not None else None
		if llamador is None:
			return
		traducciones = catalogo()
		llamador.f_globals["_"] = traducciones.gettext
		llamador.f_globals["ngettext"] = traducciones.ngettext
	finally:
		del marco

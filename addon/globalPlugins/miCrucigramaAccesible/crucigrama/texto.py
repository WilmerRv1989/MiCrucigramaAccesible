# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Letras del crucigrama.

Como en los crucigramas impresos, las tildes y la diéresis no cuentan: «canción» se escribe
CANCION y la Á vale lo mismo que la A. La Ñ sí es una letra propia, distinta de la N.
"""

import unicodedata

LETRAS = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"

_SIN_TILDE = str.maketrans("ÁÉÍÓÚÜ", "AEIOUU")


def normalizar_letra(letra: str) -> str:
	"""La letra en mayúsculas y sin tilde, o una cadena vacía si no es una letra del crucigrama."""
	letra = unicodedata.normalize("NFC", letra).upper().translate(_SIN_TILDE)
	return letra if len(letra) == 1 and letra in LETRAS else ""


def normalizar(palabra: str) -> str:
	"""La palabra como se escribe en el tablero: «Canción» da CANCION y «niño» da NIÑO.

	Devuelve una cadena vacía si la palabra tiene algo que no sea una letra del español
	(espacios, guiones, números, ç...), porque esas palabras no caben en un crucigrama.
	"""
	letras = [normalizar_letra(letra) for letra in unicodedata.normalize("NFC", palabra)]
	if not letras or "" in letras:
		return ""
	return "".join(letras)

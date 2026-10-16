# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Lo que se oye en el tablero, en español (con la traducción del archivo .po)."""

import os
import sys
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_RAIZ, "addon", "globalPlugins", "miCrucigramaAccesible"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import po  # noqa: E402
from crucigrama import anunciador, idioma  # noqa: E402
from crucigrama.generador import Direccion  # noqa: E402
from crucigrama.partida import Partida  # noqa: E402
from test_partida import crucigrama_de_animales  # noqa: E402

_PO_ES = os.path.join(_RAIZ, "addon", "locale", "es", "LC_MESSAGES", "nvda.po")


class TestEspanol(unittest.TestCase):
	def setUp(self) -> None:
		idioma.configurar(*po.traducciones(_PO_ES))
		self.partida = Partida(crucigrama_de_animales())

	def tearDown(self) -> None:
		idioma.configurar(idioma._sin_traduccion, idioma._plural_sin_traduccion)

	def test_todo_traducido(self) -> None:
		sin_traducir = [
			e.msgid for e in po.leer(_PO_ES) if e.msgid and not all(e.msgstr.get(i) for i in e.msgstr)
		]
		self.assertEqual(sin_traducir, [])

	def test_al_entrar_en_una_palabra(self) -> None:
		p = self.partida
		self.assertEqual(anunciador.describir_palabra(p.palabra_actual), "1 vertical, 4 letras: Hace mu")

	def test_casilla_con_cruce(self) -> None:
		p = self.partida
		p.mover(Direccion.VERTICAL, 1)
		self.assertEqual(
			anunciador.describir_casilla(p, p.casilla, p.palabra_actual),
			"vacía, letra 2 de 4, cruza con 3 horizontal, letra 2",
		)

	def test_escribir_y_completar(self) -> None:
		p = self.partida
		for letra in "VAC":
			p.escribir(letra)
		resultado = p.escribir("A")
		assert resultado is not None
		self.assertEqual(anunciador.describir_escritura(p, resultado), "A. 1 vertical completa")
		self.assertEqual(anunciador.describir_patron(p, p.palabra_actual), "V, A, C, A")

	def test_estado_y_comprobar(self) -> None:
		p = self.partida
		p.escribir("X")
		self.assertEqual(
			anunciador.describir_comprobacion(p),
			"1 letra incorrecta, en 1 vertical. Faltan 20 casillas.",
		)
		self.assertTrue(anunciador.describir_estado(p).startswith("0 de 6 palabras completas. Faltan: 1 vertical"))


if __name__ == "__main__":
	unittest.main()


class TestTraduccionForzada(unittest.TestCase):
	def test_el_catalogo_es_siempre_el_espanol(self) -> None:
		"""La interfaz carga siempre la traducción española (si el .mo está compilado)."""
		mo = os.path.join(_RAIZ, "addon", "locale", "es", "LC_MESSAGES", "nvda.mo")
		if not os.path.isfile(mo):
			self.skipTest("El .mo solo existe después de compilar con scons")
		sys.path.insert(0, os.path.join(_RAIZ, "addon", "globalPlugins", "miCrucigramaAccesible", "interfaz"))
		import traduccion

		self.assertEqual(traduccion.catalogo().gettext("Board"), "Tablero")

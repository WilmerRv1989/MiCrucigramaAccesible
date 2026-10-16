# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Pruebas del banco que va dentro del complemento (banco/general.json e infantil.json)."""

import os
import sys
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_COMPLEMENTO = os.path.join(_RAIZ, "addon", "globalPlugins", "miCrucigramaAccesible")
sys.path.insert(0, _COMPLEMENTO)

from crucigrama import banco  # noqa: E402
from crucigrama.banco import Dificultad  # noqa: E402
from crucigrama.generador import Tamano, candidatas, generar  # noqa: E402

TEMAS = ("animales", "comida", "colores", "cuerpo", "casa", "escuela")


class TestBancoReal(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.general = banco.cargar(os.path.join(_COMPLEMENTO, "banco", "general.json"))
		cls.infantil = banco.cargar(os.path.join(_COMPLEMENTO, "banco", "infantil.json"))

	def test_unas_mil_palabras_por_nivel(self) -> None:
		for dificultad in Dificultad:
			self.assertGreaterEqual(len(candidatas(self.general, dificultad)), 900, dificultad)

	def test_cada_tema_tiene_palabras_de_sobra(self) -> None:
		temas = {e.tema for e in self.infantil}
		self.assertEqual(temas, set(TEMAS))
		for tema in TEMAS:
			self.assertGreaterEqual(len(candidatas(self.infantil, Dificultad.FACIL, tema)), 15, tema)

	def test_todos_los_crucigramas_salen_completos(self) -> None:
		for tamano in Tamano:
			for dificultad in Dificultad:
				for semilla in range(5):
					c = generar(self.general, tamano, dificultad, semilla)
					self.assertEqual(len(c.palabras), tamano.palabras, (tamano, dificultad, semilla))

	def test_los_infantiles_salen_completos(self) -> None:
		for tema in TEMAS:
			for semilla in range(10):
				c = generar(self.infantil, Tamano.PEQUENO, Dificultad.FACIL, semilla, tema)
				self.assertEqual(len(c.palabras), Tamano.PEQUENO.palabras, (tema, semilla))


if __name__ == "__main__":
	unittest.main()

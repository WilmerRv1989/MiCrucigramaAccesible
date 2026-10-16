# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Pruebas de los textos de la vista previa."""

import os
import sys
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_RAIZ, "addon", "globalPlugins", "miCrucigramaAccesible"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import banco_prueba  # noqa: E402
from crucigrama import vista  # noqa: E402
from crucigrama.banco import Dificultad  # noqa: E402
from crucigrama.generador import Direccion, Tamano, generar  # noqa: E402


class TestVista(unittest.TestCase):
	def setUp(self) -> None:
		self.crucigrama = generar(banco_prueba.banco(), Tamano.PEQUENO, Dificultad.FACIL, 3, "animales")

	def test_secciones(self) -> None:
		titulos = [titulo for titulo, _ in vista.secciones(self.crucigrama)]
		self.assertEqual(titulos, ["Board", "Across", "Down", "Solutions"])

	def test_una_fila_por_fila_del_tablero(self) -> None:
		tablero = vista.secciones(self.crucigrama)[0][1]
		filas = [linea for linea in tablero if linea.startswith("Row ")]
		self.assertEqual(len(filas), self.crucigrama.alto)
		for numero, linea in enumerate(filas):
			casillas = linea.split(": ", 1)[1].split(" ")
			self.assertEqual(len(casillas), self.crucigrama.ancho)
			esperadas = [self.crucigrama.letra(numero, c) or vista.VACIA for c in range(self.crucigrama.ancho)]
			self.assertEqual(casillas, esperadas)

	def test_una_pista_por_palabra(self) -> None:
		secciones = dict(vista.secciones(self.crucigrama))
		for direccion in Direccion:
			palabras = self.crucigrama.de_direccion(direccion)
			lineas = secciones[vista.titulo_direccion(direccion)]
			self.assertEqual(len(lineas), len(palabras))
			for palabra, linea in zip(palabras, lineas):
				self.assertTrue(linea.startswith(f"{palabra.numero}. {palabra.entrada.pista} ("), linea)

	def test_linea_pista(self) -> None:
		self.assertEqual(
			vista.linea_pista(3, "Color del cielo", 4, 2, 5),
			"3. Color del cielo (4 letters; row 2, column 5)",
		)
		self.assertIn("(1 letter;", vista.linea_pista(1, "Pista", 1, 1, 1))

	def test_descripcion(self) -> None:
		self.assertEqual(vista.descripcion(self.crucigrama), "Children's: Animals, 6 words")
		general = generar(banco_prueba.banco(), Tamano.MEDIANO, Dificultad.NORMAL, 1)
		self.assertEqual(vista.descripcion(general), "Medium, Normal, 12 words")

	def test_todos_los_temas_tienen_nombre(self) -> None:
		for tema in vista.TEMAS:
			self.assertTrue(vista.nombre_tema(tema))


if __name__ == "__main__":
	unittest.main()

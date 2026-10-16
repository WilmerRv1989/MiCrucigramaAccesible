# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Pruebas de las letras, del banco y del generador de crucigramas."""

import os
import sys
import tempfile
import time
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_RAIZ, "addon", "globalPlugins", "miCrucigramaAccesible"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import banco_prueba  # noqa: E402
from crucigrama import banco  # noqa: E402
from crucigrama.banco import BancoInvalido, Dificultad, Entrada  # noqa: E402
from crucigrama.generador import (  # noqa: E402
	Crucigrama,
	Direccion,
	SinPalabrasSuficientes,
	Tamano,
	candidatas,
	generar,
	largos,
)
from crucigrama.texto import normalizar  # noqa: E402

SEMILLAS = range(10)


def palabras_del_tablero(crucigrama: Crucigrama) -> set[tuple[int, int, Direccion, str]]:
	"""Todas las tiras de dos o más letras seguidas que se leen en el tablero, en las dos direcciones."""
	tiras: set[tuple[int, int, Direccion, str]] = set()
	for direccion in Direccion:
		df, dc = direccion.paso
		for fila in range(crucigrama.alto):
			for columna in range(crucigrama.ancho):
				antes = crucigrama.letra(fila - df, columna - dc)
				if crucigrama.letra(fila, columna) is None or antes is not None:
					continue
				letras = ""
				f, c = fila, columna
				while (letra := crucigrama.letra(f, c)) is not None:
					letras += letra
					f, c = f + df, c + dc
				if len(letras) >= 2:
					tiras.add((fila, columna, direccion, letras))
	return tiras


class TestTexto(unittest.TestCase):
	def test_quita_tildes_y_mayusculas(self) -> None:
		self.assertEqual(normalizar("Canción"), "CANCION")
		self.assertEqual(normalizar("pingüino"), "PINGUINO")
		self.assertEqual(normalizar("ÁRBOL"), "ARBOL")

	def test_la_enie_es_una_letra_propia(self) -> None:
		self.assertEqual(normalizar("niño"), "NIÑO")
		self.assertEqual(normalizar("AÑO"), "AÑO")
		# La ñ escrita como n más la tilde combinable también vale.
		self.assertEqual(normalizar("año"), "AÑO")

	def test_rechaza_lo_que_no_son_letras(self) -> None:
		for palabra in ("", "arco iris", "auto-bús", "r2d2", "ça"):
			self.assertEqual(normalizar(palabra), "", palabra)


class TestBanco(unittest.TestCase):
	def test_guardar_y_cargar(self) -> None:
		entradas = [
			Entrada("canción", "Música con letra", Dificultad.FACIL),
			Entrada("alféizar", "Parte baja de la ventana", Dificultad.DIFICIL, directa=False, origen="wikcionario"),
			Entrada("jirafa", "Animal de cuello largo", Dificultad.FACIL, tema="animales"),
		]
		with tempfile.TemporaryDirectory() as carpeta:
			ruta = os.path.join(carpeta, "banco.json")
			banco.guardar(ruta, entradas)
			self.assertEqual(banco.cargar(ruta), entradas)

	def test_entrada_sin_pista_o_con_palabra_rara(self) -> None:
		for datos in (
			{"palabra": "casa", "pista": " ", "dificultad": "facil"},
			{"palabra": "arco iris", "pista": "Colores en el cielo", "dificultad": "facil"},
			{"palabra": "casa", "pista": "Hogar", "dificultad": "imposible"},
			{"pista": "Hogar", "dificultad": "facil"},
		):
			with self.assertRaises(BancoInvalido):
				banco.entrada_desde_dict(datos)


class TestCandidatas(unittest.TestCase):
	def setUp(self) -> None:
		self.banco = banco_prueba.banco()

	def test_cada_nivel_usa_solo_sus_palabras_y_largos(self) -> None:
		for dificultad in Dificultad:
			minimo, maximo = largos(dificultad)
			posibles = candidatas(self.banco, dificultad)
			self.assertGreater(len(posibles), 50, dificultad)
			for entrada in posibles:
				self.assertIs(entrada.dificultad, dificultad)
				self.assertIsNone(entrada.tema)
				self.assertTrue(minimo <= len(entrada.clave) <= maximo, entrada)

	def test_facil_solo_pistas_directas(self) -> None:
		self.assertTrue(all(e.directa for e in candidatas(self.banco, Dificultad.FACIL)))
		self.assertFalse(all(e.directa for e in candidatas(self.banco, Dificultad.NORMAL)))

	def test_tema_solo_sus_palabras(self) -> None:
		posibles = candidatas(self.banco, Dificultad.FACIL, "animales")
		self.assertTrue(posibles)
		self.assertTrue(all(e.tema == "animales" for e in posibles))

	def test_sin_repetidas(self) -> None:
		doble = self.banco + self.banco
		claves = [e.clave for e in candidatas(doble, Dificultad.NORMAL)]
		self.assertEqual(len(claves), len(set(claves)))


class TestGenerador(unittest.TestCase):
	banco: list[Entrada]
	generados: list[Crucigrama]

	@classmethod
	def setUpClass(cls) -> None:
		cls.banco = banco_prueba.banco()
		cls.generados = [
			generar(cls.banco, tamano, dificultad, semilla)
			for tamano in Tamano
			for dificultad in Dificultad
			for semilla in SEMILLAS
		] + [generar(cls.banco, Tamano.PEQUENO, Dificultad.FACIL, s, tema="animales") for s in SEMILLAS]

	def test_llega_al_numero_de_palabras(self) -> None:
		for c in self.generados:
			self.assertEqual(len(c.palabras), c.tamano.palabras, (c.tamano, c.dificultad, c.semilla))

	def test_cabe_en_el_lado_del_tamano(self) -> None:
		for c in self.generados:
			self.assertLessEqual(c.alto, c.tamano.lado)
			self.assertLessEqual(c.ancho, c.tamano.lado)
			casillas = [casilla for p in c.palabras for casilla in p.casillas()]
			self.assertEqual(min(f for f, _ in casillas), 0)
			self.assertEqual(min(col for _, col in casillas), 0)

	def test_solo_se_leen_las_palabras_del_crucigrama(self) -> None:
		"""Ninguna letra pegada forma una palabra que no está, y ninguna palabra se alarga."""
		for c in self.generados:
			esperadas = {(p.fila, p.columna, p.direccion, p.clave) for p in c.palabras}
			self.assertEqual(palabras_del_tablero(c), esperadas, (c.tamano, c.dificultad, c.semilla))

	def test_todo_conectado(self) -> None:
		for c in self.generados:
			vistas = {0}
			pendientes = [0]
			while pendientes:
				actual = set(c.palabras[pendientes.pop()].casillas())
				for i, otra in enumerate(c.palabras):
					if i not in vistas and actual & set(otra.casillas()):
						vistas.add(i)
						pendientes.append(i)
			self.assertEqual(len(vistas), len(c.palabras))

	def test_cada_palabra_cruza_al_menos_otra(self) -> None:
		for c in self.generados:
			for p in c.palabras:
				cruces = [casilla for casilla in p.casillas() if len(c.palabras_en(*casilla)) == 2]
				self.assertTrue(cruces, p)

	def test_palabras_sin_repetir_y_del_nivel(self) -> None:
		for c in self.generados:
			claves = [p.clave for p in c.palabras]
			self.assertEqual(len(claves), len(set(claves)))
			for p in c.palabras:
				if c.tema is None:
					self.assertIs(p.entrada.dificultad, c.dificultad)
					self.assertIsNone(p.entrada.tema)
				else:
					self.assertEqual(p.entrada.tema, c.tema)

	def test_numeracion_en_orden_de_lectura(self) -> None:
		for c in self.generados:
			inicios = sorted({(p.fila, p.columna) for p in c.palabras})
			for p in c.palabras:
				self.assertEqual(p.numero, inicios.index((p.fila, p.columna)) + 1)
			numeros = [p.numero for p in c.de_direccion(Direccion.HORIZONTAL)]
			self.assertEqual(numeros, sorted(set(numeros)))

	def test_tema_siempre_facil(self) -> None:
		c = generar(self.banco, Tamano.PEQUENO, Dificultad.DIFICIL, 1, tema="animales")
		self.assertIs(c.dificultad, Dificultad.FACIL)

	def test_misma_semilla_mismo_crucigrama(self) -> None:
		for dificultad in Dificultad:
			a = generar(self.banco, Tamano.MEDIANO, dificultad, 42)
			b = generar(self.banco, Tamano.MEDIANO, dificultad, 42)
			self.assertEqual(a.palabras, b.palabras)
		otra = generar(self.banco, Tamano.MEDIANO, Dificultad.NORMAL, 43)
		self.assertNotEqual(otra.palabras, generar(self.banco, Tamano.MEDIANO, Dificultad.NORMAL, 42).palabras)

	def test_cuanto_mas_facil_mas_letras_compartidas(self) -> None:
		"""Cada cruce regala una letra: en fácil, una buena parte de las letras son cruces."""

		def proporcion(dificultad: Dificultad) -> float:
			cruces = casillas = 0
			for c in self.generados:
				if c.dificultad is dificultad and c.tema is None:
					todas = {casilla for p in c.palabras for casilla in p.casillas()}
					cruces += sum(1 for casilla in todas if len(c.palabras_en(*casilla)) == 2)
					casillas += len(todas)
			return cruces / casillas

		facil = proporcion(Dificultad.FACIL)
		normal = proporcion(Dificultad.NORMAL)
		dificil = proporcion(Dificultad.DIFICIL)
		self.assertGreater(facil, normal + 0.04, (facil, normal))
		self.assertGreater(normal, dificil + 0.04, (normal, dificil))

	def test_rapido(self) -> None:
		inicio = time.perf_counter()
		for semilla in range(5):
			generar(self.banco, Tamano.GRANDE, Dificultad.DIFICIL, 1000 + semilla)
		self.assertLess((time.perf_counter() - inicio) / 5, 1.0)

	def test_sin_palabras_suficientes(self) -> None:
		pocas = self.banco[:3]
		with self.assertRaises(SinPalabrasSuficientes):
			generar(pocas, Tamano.PEQUENO, Dificultad.FACIL, 1)


if __name__ == "__main__":
	unittest.main()

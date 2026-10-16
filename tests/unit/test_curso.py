# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Pruebas del curso: cada ejercicio está bien hecho y se puede superar; sesión y progreso."""

import os
import sys
import tempfile
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_RAIZ, "addon", "globalPlugins", "miCrucigramaAccesible"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crucigrama.curso.modelo import CARPETA_LECCIONES, cargar_curso, carpeta_de_idioma  # noqa: E402
from crucigrama.curso.progreso import Progreso  # noqa: E402
from crucigrama.curso.sesion import SesionEjercicio  # noqa: E402
from crucigrama.texto import normalizar  # noqa: E402
from test_generador import palabras_del_tablero  # noqa: E402

CURSO = cargar_curso(os.path.join(CARPETA_LECCIONES, "es"))
EJERCICIOS = [e for leccion in CURSO.lecciones for e in leccion.ejercicios]


class TestContenido(unittest.TestCase):
	def test_hay_lecciones(self) -> None:
		self.assertGreaterEqual(len(CURSO.lecciones), 5)
		ids = [e.id for e in EJERCICIOS]
		self.assertEqual(len(ids), len(set(ids)))

	def test_cada_tablero_solo_tiene_sus_palabras(self) -> None:
		for e in EJERCICIOS:
			c = e.crucigrama
			esperadas = {(p.fila, p.columna, p.direccion, p.clave) for p in c.palabras}
			self.assertEqual(palabras_del_tablero(c), esperadas, e.id)

	def test_letras_escritas_en_casillas_de_palabras(self) -> None:
		for e in EJERCICIOS:
			casillas = {x for p in e.crucigrama.palabras for x in p.casillas()}
			for casilla, letra in e.letras:
				self.assertIn(casilla, casillas, e.id)
				self.assertTrue(normalizar(letra), e.id)
			for casilla in e.objetivos:
				self.assertIn(casilla, casillas, e.id)

	def test_el_cursor_empieza_en_su_palabra(self) -> None:
		for e in EJERCICIOS:
			sesion = SesionEjercicio(e)
			self.assertIsNotNone(sesion.partida.palabra_en(e.inicio, e.direccion), e.id)

	def test_al_empezar_queda_algo_por_hacer(self) -> None:
		for e in EJERCICIOS:
			sesion = SesionEjercicio(e)
			partida = sesion.partida
			pendientes = [c for c in e.objetivos if partida.letra(c) != partida.solucion(c)]
			self.assertTrue(pendientes, e.id)

	def test_se_supera_escribiendo_las_letras_buenas(self) -> None:
		for e in EJERCICIOS:
			sesion = SesionEjercicio(e)
			partida = sesion.partida
			ultima = None
			for casilla in e.objetivos:
				if partida.letra(casilla) == partida.solucion(casilla):
					continue
				palabra = partida.palabra_en(casilla, partida.direccion) or partida.cruce(casilla)
				assert palabra is not None
				partida.ir_a_palabra(palabra)
				partida.casilla = casilla
				ultima = sesion.escribir(partida.solucion(casilla))
				self.assertTrue(ultima.aceptada, e.id)
			assert ultima is not None
			self.assertTrue(ultima.superado, e.id)
			self.assertEqual(sesion.estrellas, 3)

	def test_cada_leccion_tiene_explicacion_e_instrucciones(self) -> None:
		for leccion in CURSO.lecciones:
			self.assertTrue(leccion.explicacion)
			for e in leccion.ejercicios:
				self.assertGreater(len(e.instruccion), 20, e.id)

	def test_idioma_por_defecto(self) -> None:
		self.assertTrue(carpeta_de_idioma("xx_YY").endswith("es"))


class TestSesion(unittest.TestCase):
	def setUp(self) -> None:
		self.sesion = SesionEjercicio(EJERCICIOS[0])  # 1.1: completar «oso» desde la S de «sol».

	def test_letra_equivocada_no_se_escribe(self) -> None:
		partida = self.sesion.partida
		respuesta = self.sesion.escribir("X")
		self.assertTrue(respuesta.error)
		self.assertIn("Clue:", respuesta.mensaje)
		self.assertEqual(partida.letra(partida.casilla), "S")

	def test_ayudas_quitan_estrellas(self) -> None:
		self.sesion.ayuda(palabra=False)
		self.assertEqual(self.sesion.estrellas, 2)
		self.sesion.ayuda(palabra=True)
		self.sesion.ayuda(palabra=False)
		self.assertEqual(self.sesion.estrellas, 1)

	def test_ya_superado(self) -> None:
		self.sesion.superado = True
		self.assertTrue(self.sesion.escribir("S").error)


class TestProgreso(unittest.TestCase):
	def test_progreso(self) -> None:
		with tempfile.TemporaryDirectory() as carpeta:
			ruta = os.path.join(carpeta, "progreso.json")
			progreso = Progreso(ruta)
			leccion = CURSO.lecciones[0]
			self.assertEqual(progreso.primer_pendiente(leccion), 0)
			progreso.registrar(leccion.ejercicios[0].id, 2)
			progreso.registrar(leccion.ejercicios[0].id, 1)
			progreso.guardar()
			leido = Progreso(ruta)
			self.assertEqual(leido.estrellas_de(leccion), 2)
			self.assertEqual(leido.primer_pendiente(leccion), 1)
			for e in leccion.ejercicios:
				leido.registrar(e.id, 3)
			self.assertTrue(leido.leccion_completada(leccion))
			self.assertEqual(leido.primer_pendiente(leccion), 0)


if __name__ == "__main__":
	unittest.main()


class TestCrucigramaEntero(unittest.TestCase):
	def setUp(self) -> None:
		self.ejercicio = next(e for e in EJERCICIOS if e.entero)

	def test_los_enteros_son_del_bloque_c(self) -> None:
		enteros = [e.id for e in EJERCICIOS if e.entero]
		self.assertEqual(enteros, ["12.1", "12.2", "13.1", "14.1"])
		for e in EJERCICIOS:
			if e.entero:
				casillas = {x for p in e.crucigrama.palabras for x in p.casillas()}
				self.assertEqual(set(e.objetivos), casillas, e.id)

	def test_estrellas_segun_las_ayudas(self) -> None:
		sesion = SesionEjercicio(self.ejercicio)
		esperadas = {0: 3, 1: 3, 2: 2, 4: 2, 5: 1}
		for ayudas, estrellas in esperadas.items():
			sesion.ayudas_pedidas = ayudas
			self.assertEqual(sesion.estrellas, estrellas, ayudas)

	def test_guardar_y_continuar(self) -> None:
		sesion = SesionEjercicio(self.ejercicio)
		partida = sesion.partida
		sesion.escribir(partida.solucion(partida.casilla))
		sesion.ayuda(palabra=False)
		texto = sesion.a_json()
		otra = SesionEjercicio(self.ejercicio)
		self.assertTrue(otra.continuar(texto))
		self.assertTrue(otra.continuada)
		self.assertEqual(otra.partida.letras, partida.letras)
		self.assertEqual(otra.partida.casilla, partida.casilla)
		self.assertEqual(otra.ayudas_pedidas, 1)

	def test_no_continua_otro_ejercicio_ni_un_archivo_danado(self) -> None:
		otro = next(e for e in EJERCICIOS if e.entero and e.id != self.ejercicio.id)
		texto = SesionEjercicio(otro).a_json()
		self.assertFalse(SesionEjercicio(self.ejercicio).continuar(texto))
		self.assertFalse(SesionEjercicio(self.ejercicio).continuar("no es json"))

	def test_los_ejercicios_cortos_no_se_guardan(self) -> None:
		self.assertFalse(SesionEjercicio(EJERCICIOS[0]).se_guarda)
		self.assertTrue(SesionEjercicio(self.ejercicio).se_guarda)


class TestBloqueCAlDia(unittest.TestCase):
	def test_coincide_con_el_generador(self) -> None:
		"""Si falla, hay que volver a ejecutar herramientas/preparar_lecciones.py."""
		import json

		from crucigrama import banco
		from crucigrama.banco import Dificultad
		from crucigrama.generador import Tamano, generar

		complemento = os.path.dirname(CARPETA_LECCIONES)
		bancos = {n: banco.cargar(os.path.join(complemento, "banco", f"{n}.json")) for n in ("general", "infantil")}
		with open(os.path.join(CARPETA_LECCIONES, "es", "bloque_c.json"), encoding="utf-8") as archivo:
			bloque = json.load(archivo)
		for leccion in bloque["lecciones"]:
			for ejercicio in leccion["ejercicios"]:
				datos = ejercicio["generar"]
				tema = datos.get("tema")
				c = generar(
					bancos["infantil" if tema else "general"],
					Tamano(datos["tamano"]),
					Dificultad(datos["dificultad"]),
					int(datos["semilla"]),
					tema,
				)
				esperadas = sorted((p.entrada.palabra, p.fila + 1, p.columna + 1) for p in c.palabras)
				guardadas = sorted((p["palabra"], p["fila"], p["columna"]) for p in ejercicio["palabras"])
				self.assertEqual(guardadas, esperadas, ejercicio["id"])

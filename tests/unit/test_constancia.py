# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Pruebas del crucigrama del día, de las estadísticas y de las opciones de lo que se dice."""

import datetime
import json
import os
import sys
import tempfile
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_COMPLEMENTO = os.path.join(_RAIZ, "addon", "globalPlugins", "miCrucigramaAccesible")
sys.path.insert(0, _COMPLEMENTO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crucigrama import anunciador, banco, diario  # noqa: E402
from crucigrama.banco import Dificultad  # noqa: E402
from crucigrama.estadisticas import Estadisticas, secciones, texto_tiempo  # noqa: E402
from crucigrama.generador import Direccion, Tamano  # noqa: E402
from crucigrama.partida import Partida  # noqa: E402
from test_partida import crucigrama_de_animales  # noqa: E402

LUNES = datetime.date(2026, 10, 5)


class TestDelDia(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.banco = banco.cargar(os.path.join(_COMPLEMENTO, "banco", "general.json"))

	def test_calendario_de_la_semana(self) -> None:
		tipos = [diario.tipo_del_dia(LUNES + datetime.timedelta(days=n)) for n in range(7)]
		self.assertEqual(
			tipos,
			[
				(Tamano.MEDIANO, Dificultad.FACIL),
				(Tamano.MEDIANO, Dificultad.FACIL),
				(Tamano.MEDIANO, Dificultad.NORMAL),
				(Tamano.MEDIANO, Dificultad.NORMAL),
				(Tamano.MEDIANO, Dificultad.DIFICIL),
				(Tamano.GRANDE, Dificultad.NORMAL),
				(Tamano.GRANDE, Dificultad.FACIL),
			],
		)

	def test_el_mismo_para_todos_y_distinto_cada_dia(self) -> None:
		a = diario.crucigrama_del_dia(self.banco, LUNES)
		b = diario.crucigrama_del_dia(self.banco, LUNES)
		martes = diario.crucigrama_del_dia(self.banco, LUNES + datetime.timedelta(days=1))
		self.assertEqual(a.palabras, b.palabras)
		self.assertNotEqual(a.palabras, martes.palabras)

	def test_dos_semanas_completas(self) -> None:
		for n in range(14):
			fecha = LUNES + datetime.timedelta(days=n)
			c = diario.crucigrama_del_dia(self.banco, fecha)
			self.assertEqual(len(c.palabras), c.tamano.palabras, fecha)

	def test_la_partida_recuerda_su_fecha(self) -> None:
		p = Partida(crucigrama_de_animales())
		p.del_dia = "2026-10-05"
		self.assertEqual(Partida.desde_json(p.a_json()).del_dia, "2026-10-05")
		self.assertIsNone(Partida.desde_json(Partida(crucigrama_de_animales()).a_json()).del_dia)


class TestEstadisticas(unittest.TestCase):
	def setUp(self) -> None:
		self.carpeta = tempfile.TemporaryDirectory()
		self.ruta = os.path.join(self.carpeta.name, "sub", "estadisticas.json")

	def tearDown(self) -> None:
		self.carpeta.cleanup()

	def test_mejor_tiempo(self) -> None:
		e = Estadisticas(self.ruta)
		self.assertFalse(e.registrar_resuelto(Tamano.MEDIANO, Dificultad.NORMAL, None, 600, True, 2))
		self.assertFalse(e.registrar_resuelto(Tamano.MEDIANO, Dificultad.NORMAL, None, 700, False, 0))
		self.assertTrue(e.registrar_resuelto(Tamano.MEDIANO, Dificultad.NORMAL, None, 500, False, 1))
		self.assertEqual(e.resueltos["mediano-normal"], {"total": 3, "sin_ayudas": 2, "mejor": 500})
		self.assertEqual(e.ayudas, 3)

	def test_infantiles_juntos(self) -> None:
		e = Estadisticas(self.ruta)
		e.registrar_resuelto(Tamano.PEQUENO, Dificultad.FACIL, "animales", 60, True, 0)
		e.registrar_resuelto(Tamano.PEQUENO, Dificultad.FACIL, "colores", 50, True, 0)
		self.assertEqual(e.resueltos["infantil"]["total"], 2)

	def test_racha(self) -> None:
		e = Estadisticas(self.ruta)
		self.assertEqual(e.registrar_del_dia(LUNES), 1)
		self.assertEqual(e.registrar_del_dia(LUNES), 1)  # El mismo día no cuenta dos veces.
		self.assertEqual(e.registrar_del_dia(LUNES + datetime.timedelta(days=1)), 2)
		self.assertEqual(e.racha_actual(LUNES + datetime.timedelta(days=2)), 2)
		self.assertEqual(e.racha_actual(LUNES + datetime.timedelta(days=3)), 0)
		self.assertEqual(e.registrar_del_dia(LUNES + datetime.timedelta(days=4)), 1)
		self.assertEqual((e.record, e.total_del_dia), (2, 3))

	def test_guardar_leer_y_archivo_danado(self) -> None:
		e = Estadisticas(self.ruta)
		e.registrar_resuelto(Tamano.GRANDE, Dificultad.DIFICIL, None, 1234, False, 0)
		e.registrar_del_dia(LUNES)
		e.guardar()
		leida = Estadisticas(self.ruta)
		self.assertEqual(leida.resueltos, e.resueltos)
		self.assertEqual(leida.ultimo_del_dia, "2026-10-05")
		with open(self.ruta, "w", encoding="utf-8") as archivo:
			json.dump({"version": 1, "resueltos": {"x": {"total": "mucho"}}}, archivo)
		self.assertEqual(Estadisticas(self.ruta).resueltos, {})

	def test_secciones(self) -> None:
		e = Estadisticas(self.ruta)
		vacias = dict(secciones(e, LUNES))
		self.assertEqual(vacias["Crosswords solved"], ["You have not solved any crossword yet."])
		e.registrar_resuelto(Tamano.MEDIANO, Dificultad.NORMAL, None, 754, True, 4)
		e.registrar_del_dia(LUNES)
		datos = dict(secciones(e, LUNES))
		self.assertEqual(
			datos["Crosswords solved"],
			[
				"Medium, Normal: 1 solved, 0 without help. Best time: 12 minutes and 34 seconds.",
				"Help used: 4 times.",
			],
		)
		self.assertIn("Today's crossword is already solved.", datos["Crossword of the day"])

	def test_tiempo(self) -> None:
		self.assertEqual(texto_tiempo(5), "5 seconds")
		self.assertEqual(texto_tiempo(3600 + 61), "1 hour, 1 minute and 1 second")


class TestOpcionesDeAnuncio(unittest.TestCase):
	def tearDown(self) -> None:
		anunciador.configurar(True, True)

	def test_sin_cruces_ni_escrito(self) -> None:
		p = Partida(crucigrama_de_animales())
		p.escribir("V")
		p.mover(Direccion.VERTICAL, -1)
		p.mover(Direccion.VERTICAL, 1)
		anunciador.configurar(False, False)
		self.assertEqual(anunciador.describir_casilla(p, p.casilla, p.palabra_actual), "empty, letter 2 of 4")
		self.assertEqual(anunciador.describir_palabra_al_entrar(p, p.palabra_actual), "1 down, 4 letters: Hace mu")
		# Mayúsculas+F2 sigue diciendo el cruce aunque no se anuncie al moverse.
		self.assertIsNotNone(anunciador.describir_cruce(p))


if __name__ == "__main__":
	unittest.main()


class TestEstadisticasDelCurso(unittest.TestCase):
	def test_seccion_del_curso(self) -> None:
		from crucigrama.curso.modelo import CARPETA_LECCIONES, cargar_curso
		from crucigrama.curso.progreso import Progreso

		with tempfile.TemporaryDirectory() as carpeta:
			curso = cargar_curso(os.path.join(CARPETA_LECCIONES, "es"))
			progreso = Progreso(os.path.join(carpeta, "progreso.json"))
			for e in curso.lecciones[0].ejercicios:
				progreso.registrar(e.id, 3)
			datos = dict(secciones(Estadisticas(os.path.join(carpeta, "e.json")), LUNES, curso, progreso))
			total = len(curso.lecciones)
			self.assertEqual(datos["Learn to play"][0], f"Lessons finished: 1 of {total}.")

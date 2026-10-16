# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Pruebas del crucigrama en juego: caminitos, escribir, borrar, deshacer, comprobar y guardar."""

import os
import sys
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_RAIZ, "addon", "globalPlugins", "miCrucigramaAccesible"))

from crucigrama import anunciador  # noqa: E402
from crucigrama.banco import Dificultad, Entrada  # noqa: E402
from crucigrama.generador import Crucigrama, Direccion, PalabraColocada, Tamano  # noqa: E402
from crucigrama.partida import Partida  # noqa: E402

H = Direccion.HORIZONTAL
V = Direccion.VERTICAL


def crucigrama_de_animales() -> Crucigrama:
	"""Este tablero (filas y columnas desde 0):

	. V . M .
	P A T O .
	. C . N .
	R A T O N
	. . I . .
	. . G . .
	. . R . .
	A B E J A
	"""

	def colocar(palabra: str, pista: str, fila: int, columna: int, direccion: Direccion, numero: int):
		entrada = Entrada(palabra, pista, Dificultad.FACIL, tema="animales")
		return PalabraColocada(entrada, fila, columna, direccion, numero)

	palabras = [
		colocar("vaca", "Hace mu", 0, 1, V, 1),
		colocar("mono", "Come plátanos", 0, 3, V, 2),
		colocar("pato", "Hace cuac", 1, 0, H, 3),
		colocar("ratón", "Le gusta el queso", 3, 0, H, 4),
		colocar("tigre", "Gato con rayas", 3, 2, V, 5),
		colocar("abeja", "Hace miel", 7, 0, H, 6),
	]
	return Crucigrama(8, 5, palabras, Tamano.PEQUENO, Dificultad.FACIL, 1, "animales")


class TestCaminitos(unittest.TestCase):
	def setUp(self) -> None:
		self.partida = Partida(crucigrama_de_animales())

	def test_empieza_en_la_primera_palabra(self) -> None:
		self.assertEqual(self.partida.casilla, (0, 1))
		self.assertEqual(anunciador.nombre_palabra(self.partida.palabra_actual), "1 down")

	def test_solo_se_pisa_donde_hay_letra(self) -> None:
		p = self.partida
		self.assertFalse(p.mover(V, -1))  # Encima de la V no hay nada.
		self.assertFalse(p.mover(H, 1))  # A la derecha de la V tampoco.
		self.assertEqual(p.casilla, (0, 1))
		self.assertEqual(p.direccion, V)
		self.assertTrue(p.mover(V, 1))  # La A de VACA, que cruza con PATO.
		self.assertEqual(p.casilla, (1, 1))
		self.assertTrue(p.mover(H, 1))  # Ahora por PATO.
		self.assertEqual(p.direccion, H)
		self.assertEqual(anunciador.nombre_palabra(p.palabra_actual), "3 across")

	def test_un_paseo_entero(self) -> None:
		p = self.partida
		pasos = [(V, 1), (V, 1), (V, 1), (H, 1), (V, 1), (V, 1), (V, 1), (V, 1)]
		for direccion, paso in pasos:
			self.assertTrue(p.mover(direccion, paso), (direccion, paso, p.casilla))
		self.assertEqual(p.casilla, (7, 2))  # La E de ABEJA, al final de TIGRE.
		self.assertFalse(p.mover(V, 1))

	def test_tab_por_numero_y_da_la_vuelta(self) -> None:
		p = self.partida
		nombres = []
		for _ in range(7):
			palabra = p.siguiente_palabra(1)
			p.ir_a_palabra(palabra)
			nombres.append(anunciador.nombre_palabra(palabra))
		self.assertEqual(nombres, ["2 down", "3 across", "4 across", "5 down", "6 across", "1 down", "2 down"])
		p.ir_a_palabra(p.siguiente_palabra(-1))
		self.assertEqual(anunciador.nombre_palabra(p.palabra_actual), "1 down")

	def test_inicio_y_fin_de_la_palabra(self) -> None:
		p = self.partida
		p.ir_a_palabra(p.orden[3])  # 4 horizontal, RATON.
		p.ir_a_palabra(p.palabra_actual, final=True)
		self.assertEqual(p.casilla, (3, 4))


class TestEscribir(unittest.TestCase):
	def setUp(self) -> None:
		self.partida = Partida(crucigrama_de_animales())

	def test_escribe_y_avanza(self) -> None:
		p = self.partida
		resultado = p.escribir("v")
		self.assertIsNotNone(resultado)
		self.assertEqual(p.letra((0, 1)), "V")
		self.assertEqual(p.casilla, (1, 1))

	def test_tildes_fuera_y_enie_propia(self) -> None:
		p = self.partida
		p.escribir("á")
		self.assertEqual(p.letra((0, 1)), "A")
		p.escribir("ñ")
		self.assertEqual(p.letra((1, 1)), "Ñ")

	def test_lo_que_no_es_letra_no_se_escribe(self) -> None:
		for caracter in ("1", " ", "-", "ç"):
			self.assertIsNone(self.partida.escribir(caracter))
		self.assertFalse(self.partida.empezado)

	def test_en_la_ultima_letra_se_queda_y_avisa_completa(self) -> None:
		p = self.partida
		for letra in "VAC":
			p.escribir(letra)
		resultado = p.escribir("A")
		assert resultado is not None
		self.assertEqual(p.casilla, (3, 1))
		self.assertEqual([anunciador.nombre_palabra(w) for w in resultado.completadas], ["1 down"])
		self.assertEqual(anunciador.describir_escritura(p, resultado), "A. 1 down complete")

	def test_un_cruce_puede_completar_dos_palabras(self) -> None:
		p = self.partida
		p.ir_a_palabra(p.orden[3])  # 4 horizontal, RATON, sin su A (que es la última de VACA).
		p.escribir("R")
		p.mover(H, 1)
		for letra in "TON":
			p.escribir(letra)
		p.ir_a_palabra(p.orden[0])  # 1 vertical, VACA.
		for letra in "VAC":
			p.escribir(letra)
		resultado = p.escribir("A")
		assert resultado is not None
		nombres = sorted(anunciador.nombre_palabra(w) for w in resultado.completadas)
		self.assertEqual(nombres, ["1 down", "4 across"])

	def test_resolver(self) -> None:
		p = self.partida
		for palabra in p.orden:
			p.ir_a_palabra(palabra)
			ultimo = None
			for letra in palabra.clave:
				ultimo = p.escribir(letra)
		assert ultimo is not None
		self.assertTrue(ultimo.resuelto)
		self.assertTrue(p.resuelto)

	def test_lleno_con_errores(self) -> None:
		p = self.partida
		ultimo = None
		for palabra in p.orden:
			p.ir_a_palabra(palabra)
			for _ in palabra.clave:
				ultimo = p.escribir("X")
		assert ultimo is not None
		self.assertFalse(ultimo.resuelto)
		self.assertTrue(ultimo.lleno_con_errores)


class TestBorrarYDeshacer(unittest.TestCase):
	def setUp(self) -> None:
		self.partida = Partida(crucigrama_de_animales())
		for letra in "VAC":
			self.partida.escribir(letra)

	def test_retroceso_en_vacia_va_atras_y_borra(self) -> None:
		p = self.partida
		self.assertEqual(p.casilla, (3, 1))
		self.assertEqual(p.retroceder(), ("C", True))
		self.assertEqual(p.casilla, (2, 1))

	def test_retroceso_en_llena_borra_sin_moverse(self) -> None:
		p = self.partida
		p.escribir("A")  # Última letra: el cursor se queda en ella.
		self.assertEqual(p.retroceder(), ("A", False))
		self.assertEqual(p.casilla, (3, 1))

	def test_retroceso_al_principio(self) -> None:
		p = self.partida
		p.ir_a_palabra(p.orden[1])  # 2 vertical, vacía.
		self.assertEqual(p.retroceder(), (None, False))

	def test_supr_no_se_mueve(self) -> None:
		p = self.partida
		p.mover(V, -1)
		self.assertEqual(p.borrar(), "C")
		self.assertEqual(p.casilla, (2, 1))
		self.assertIsNone(p.borrar())

	def test_deshacer_vuelve_a_la_casilla(self) -> None:
		p = self.partida
		p.ir_a_palabra(p.orden[5])
		self.assertEqual(p.deshacer(), (2, 1))
		self.assertEqual(p.casilla, (2, 1))
		self.assertIsNone(p.letra((2, 1)))
		self.assertEqual(p.direccion, V)
		p.deshacer()
		p.deshacer()
		self.assertIsNone(p.deshacer())
		self.assertFalse(p.empezado)


class TestComprobarYGuardar(unittest.TestCase):
	def test_comprobar(self) -> None:
		p = Partida(crucigrama_de_animales())
		for letra in "VXC":
			p.escribir(letra)
		self.assertEqual(p.errores(), 1)
		self.assertEqual(anunciador.describir_comprobacion(p), "1 wrong letter, in 1 down and 3 across. 18 empty cells left.")

	def test_guardar_y_leer(self) -> None:
		p = Partida(crucigrama_de_animales())
		for letra in "VAC":
			p.escribir(letra)
		p.segundos = 12.5
		leida = Partida.desde_json(p.a_json())
		self.assertEqual(leida.letras, p.letras)
		self.assertEqual(leida.casilla, p.casilla)
		self.assertEqual(leida.direccion, p.direccion)
		self.assertEqual(leida.segundos, 12.5)
		self.assertEqual(leida.crucigrama.palabras, p.crucigrama.palabras)

	def test_archivo_danado(self) -> None:
		for texto in ("{}", '{"version": 1}', "no es json"):
			with self.assertRaises(ValueError):
				Partida.desde_json(texto)


class TestAnunciador(unittest.TestCase):
	def setUp(self) -> None:
		self.partida = Partida(crucigrama_de_animales())

	def test_casilla_con_cruce(self) -> None:
		p = self.partida
		p.mover(V, 1)
		texto = anunciador.describir_casilla(p, p.casilla, p.palabra_actual)
		self.assertEqual(texto, "empty, letter 2 of 4, crosses 3 across, letter 2")

	def test_palabra_y_patron(self) -> None:
		p = self.partida
		self.assertEqual(anunciador.describir_palabra(p.palabra_actual), "1 down, 4 letters: Hace mu")
		p.escribir("V")
		self.assertEqual(anunciador.describir_patron(p, p.palabra_actual), "V, empty, empty, empty")

	def test_cruce_y_estado(self) -> None:
		p = self.partida
		self.assertIsNone(anunciador.describir_cruce(p))
		p.mover(V, 1)
		self.assertEqual(anunciador.describir_cruce(p), "Letter 2 of 3 across, 4 letters: Hace cuac")
		self.assertEqual(
			anunciador.describir_estado(p),
			"0 of 6 words complete. Missing: 1 down, 2 down, 3 across, 4 across, 5 down, 6 across.",
		)

	def test_posicion(self) -> None:
		self.assertEqual(anunciador.describir_posicion((2, 4)), "Row 3, column 5")


if __name__ == "__main__":
	unittest.main()


class TestAyudasYLecturas(unittest.TestCase):
	def setUp(self) -> None:
		self.partida = Partida(crucigrama_de_animales())

	def test_al_entrar_dice_lo_escrito(self) -> None:
		p = self.partida
		palabra = p.palabra_actual
		self.assertEqual(anunciador.describir_palabra_al_entrar(p, palabra), "1 down, 4 letters: Hace mu")
		p.escribir("V")
		p.escribir("A")
		self.assertEqual(
			anunciador.describir_palabra_al_entrar(p, palabra),
			"1 down, 4 letters: Hace mu. Written: V, A, empty, empty",
		)
		p.escribir("C")
		p.escribir("A")
		self.assertTrue(anunciador.describir_palabra_al_entrar(p, palabra).endswith("Written: vaca"))

	def test_palabra_escrita(self) -> None:
		p = self.partida
		palabra = p.palabra_actual
		self.assertEqual(anunciador.describir_palabra_escrita(p, palabra), "nothing written")
		p.escribir("V")
		p.escribir("A")
		p.mover(V, 1)
		p.escribir("A")
		self.assertEqual(anunciador.describir_palabra_escrita(p, palabra), "va, gap, a")

	def test_ayuda_de_letra_y_de_palabra(self) -> None:
		p = self.partida
		self.assertEqual(anunciador.describir_ayuda_letra(p), "Help: here goes V")
		p.escribir("V")
		p.mover(V, -1)
		self.assertEqual(anunciador.describir_ayuda_letra(p), "The V of this cell is already right.")
		p.ir_a_palabra(p.orden[3])
		self.assertEqual(anunciador.describir_ayuda_palabra(p), "Help: 4 across is ratón: R, A, T, O, N")
		self.assertEqual(len(p.letras), 1)  # Las ayudas no escriben nada.

	def test_errores_por_palabra(self) -> None:
		p = self.partida
		p.ir_a_palabra(p.orden[3])  # RATON: la A es también de VACA.
		for letra in "RXTON":
			p.escribir(letra)
		nombres = [anunciador.nombre_palabra(w) for w in p.palabras_con_errores()]
		self.assertEqual(nombres, ["1 down", "4 across"])
		self.assertEqual(
			anunciador.describir_comprobacion(p),
			"1 wrong letter, in 1 down and 4 across. 16 empty cells left.",
		)

	def test_unir(self) -> None:
		self.assertEqual(anunciador.unir(["a"]), "a")
		self.assertEqual(anunciador.unir(["a", "b", "c"]), "a, b and c")

	def test_ayudas_se_guardan(self) -> None:
		p = self.partida
		p.ayudas = 3
		self.assertEqual(Partida.desde_json(p.a_json()).ayudas, 3)


class TestSinAyudas(unittest.TestCase):
	def setUp(self) -> None:
		self.partida = Partida(crucigrama_de_animales(), con_ayudas=False)

	def test_comprobar_no_dice_donde(self) -> None:
		p = self.partida
		for letra in "VXC":
			p.escribir(letra)
		self.assertEqual(anunciador.describir_comprobacion(p), "1 wrong letter. 18 empty cells left.")

	def test_lleno_con_errores_no_dice_donde(self) -> None:
		p = self.partida
		ultimo = None
		for palabra in p.orden:
			p.ir_a_palabra(palabra)
			for _ in palabra.clave:
				ultimo = p.escribir("X")
		assert ultimo is not None
		self.assertTrue(
			anunciador.describir_escritura(p, ultimo).endswith("The crossword is full, but there are wrong letters"),
		)

	def test_se_guarda_y_lo_antiguo_era_con_ayudas(self) -> None:
		self.assertFalse(Partida.desde_json(self.partida.a_json()).con_ayudas)
		antiguo = self.partida.a_json().replace(', "con_ayudas": false', "")
		self.assertNotIn("con_ayudas", antiguo)
		self.assertTrue(Partida.desde_json(antiguo).con_ayudas)

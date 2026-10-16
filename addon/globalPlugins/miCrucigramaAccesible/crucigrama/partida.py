# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""El crucigrama en juego: las letras escritas, el cursor y sus caminitos, deshacer y guardar.

El cursor está siempre en una casilla con letra y lleva una dirección (horizontal o vertical):
la de la palabra que se está siguiendo. En un cruce, la dirección la decide la última flecha
o la palabra a la que se saltó. Como el generador nunca pone dos letras juntas si no son de la
misma palabra, una flecha que se mueve a una casilla vecina sigue siempre dentro de una palabra.
"""

import json
from dataclasses import dataclass, field
from typing import Any

from . import banco
from .banco import Dificultad
from .generador import Casilla, Crucigrama, Direccion, PalabraColocada, Tamano
from .texto import normalizar_letra

VERSION = 1


@dataclass
class Cambio:
	"""Un cambio en una casilla, para poder deshacerlo."""

	casilla: Casilla
	antes: str | None
	despues: str | None


@dataclass
class Escritura:
	"""Lo que pasó al escribir una letra."""

	letra: str
	# Las palabras que se acaban de llenar (sin decir si están bien).
	completadas: list[PalabraColocada] = field(default_factory=list[PalabraColocada])
	resuelto: bool = False
	# El crucigrama está lleno pero alguna letra no es la buena.
	lleno_con_errores: bool = False


class Partida:
	def __init__(
		self,
		crucigrama: Crucigrama,
		letras: dict[Casilla, str] | None = None,
		con_ayudas: bool = True,
	) -> None:
		self.crucigrama = crucigrama
		# Con ayudas, F7 dice letras y palabras y Comprobar dice dónde están los errores.
		# Se decide al empezar y no cambia.
		self.con_ayudas = con_ayudas
		# La fecha (AAAA-MM-DD) si es el crucigrama del día.
		self.del_dia: str | None = None
		self.letras: dict[Casilla, str] = dict(letras or {})
		self.segundos = 0.0
		# Cuántas veces se pidió ayuda (F7 o Mayúsculas+F7).
		self.ayudas = 0
		self._historial: list[Cambio] = []
		# Las palabras en el orden de Tab: por número y, con el mismo número, primero la horizontal.
		self.orden = sorted(crucigrama.palabras, key=lambda p: (p.numero, p.direccion is Direccion.VERTICAL))
		self._palabras_de: dict[Casilla, dict[Direccion, PalabraColocada]] = {}
		for palabra in crucigrama.palabras:
			for casilla in palabra.casillas():
				self._palabras_de.setdefault(casilla, {})[palabra.direccion] = palabra
		primera = self.orden[0]
		self.casilla: Casilla = (primera.fila, primera.columna)
		self.direccion: Direccion = primera.direccion

	# Consultas.

	@property
	def casillas(self) -> list[Casilla]:
		"""Todas las casillas con letra, en orden de lectura."""
		return sorted(self._palabras_de)

	def es_casilla(self, casilla: Casilla) -> bool:
		"""Si la casilla es de alguna palabra (las demás son los huecos negros del tablero)."""
		return casilla in self._palabras_de

	def palabra_en(self, casilla: Casilla, direccion: Direccion) -> PalabraColocada | None:
		return self._palabras_de.get(casilla, {}).get(direccion)

	@property
	def palabra_actual(self) -> PalabraColocada:
		palabra = self.palabra_en(self.casilla, self.direccion)
		assert palabra is not None
		return palabra

	def cruce(
		self,
		casilla: Casilla | None = None,
		direccion: Direccion | None = None,
	) -> PalabraColocada | None:
		"""La otra palabra que pasa por la casilla, si es un cruce."""
		casilla = casilla or self.casilla
		direccion = direccion or self.direccion
		return self.palabra_en(casilla, direccion.otra)

	def posicion_en(self, palabra: PalabraColocada, casilla: Casilla) -> int:
		"""Qué letra de la palabra es la casilla, desde 1."""
		return palabra.casillas().index(casilla) + 1

	def letra(self, casilla: Casilla) -> str | None:
		return self.letras.get(casilla)

	def completa(self, palabra: PalabraColocada) -> bool:
		return all(casilla in self.letras for casilla in palabra.casillas())

	def palabras_completas(self) -> list[PalabraColocada]:
		return [p for p in self.orden if self.completa(p)]

	def vacias(self) -> int:
		return sum(1 for casilla in self._palabras_de if casilla not in self.letras)

	def solucion(self, casilla: Casilla) -> str:
		"""La letra que va en la casilla."""
		letra = self.crucigrama.letra(*casilla)
		assert letra is not None
		return letra

	def es_error(self, casilla: Casilla) -> bool:
		"""Si la casilla tiene escrita una letra que no es la suya."""
		letra = self.letras.get(casilla)
		return letra is not None and letra != self.crucigrama.letra(*casilla)

	def errores(self) -> int:
		"""Cuántas letras escritas no son las de la solución."""
		return sum(1 for casilla in self.letras if self.es_error(casilla))

	def palabras_con_errores(self) -> list[PalabraColocada]:
		"""Las palabras que tienen alguna letra mal, en el orden de Tab."""
		return [p for p in self.orden if any(self.es_error(c) for c in p.casillas())]

	@property
	def resuelto(self) -> bool:
		return self.vacias() == 0 and self.errores() == 0

	@property
	def empezado(self) -> bool:
		return bool(self.letras)

	# Moverse.

	def mover(self, direccion: Direccion, paso: int) -> bool:
		"""Una casilla con una flecha. Si no hay casilla con letra en ese sentido, no se mueve (False).

		Al moverse, la dirección pasa a ser la de la flecha.
		"""
		df, dc = direccion.paso
		destino = (self.casilla[0] + df * paso, self.casilla[1] + dc * paso)
		if destino not in self._palabras_de:
			return False
		self.casilla = destino
		self.direccion = direccion
		return True

	def ir_a_palabra(self, palabra: PalabraColocada, final: bool = False) -> None:
		"""A la primera (o la última) letra de una palabra, en su dirección."""
		casillas = palabra.casillas()
		self.casilla = casillas[-1] if final else casillas[0]
		self.direccion = palabra.direccion

	def siguiente_palabra(self, paso: int) -> PalabraColocada:
		"""La palabra siguiente (paso 1) o anterior (paso -1) en el orden de Tab; da la vuelta al final."""
		indice = self.orden.index(self.palabra_actual)
		return self.orden[(indice + paso) % len(self.orden)]

	def _siguiente_en_palabra(self, paso: int) -> Casilla | None:
		casillas = self.palabra_actual.casillas()
		indice = casillas.index(self.casilla) + paso
		return casillas[indice] if 0 <= indice < len(casillas) else None

	# Cambios.

	def _cambiar(self, casilla: Casilla, letra: str | None) -> None:
		antes = self.letras.get(casilla)
		if antes == letra:
			return
		self._historial.append(Cambio(casilla, antes, letra))
		if letra is None:
			del self.letras[casilla]
		else:
			self.letras[casilla] = letra

	def escribir(self, caracter: str) -> Escritura | None:
		"""Escribe la letra en la casilla y avanza a la siguiente de la palabra, si la hay.

		Devuelve None si el carácter no es una letra del crucigrama.
		"""
		letra = normalizar_letra(caracter)
		if not letra:
			return None
		casilla = self.casilla
		completas_antes = set(self.palabras_completas())
		self._cambiar(casilla, letra)
		resultado = Escritura(letra)
		resultado.completadas = [
			p for p in self._palabras_de[casilla].values() if self.completa(p) and p not in completas_antes
		]
		if self.vacias() == 0:
			resultado.resuelto = self.errores() == 0
			resultado.lleno_con_errores = not resultado.resuelto
		siguiente = self._siguiente_en_palabra(1)
		if siguiente is not None:
			self.casilla = siguiente
		return resultado

	def borrar(self) -> str | None:
		"""Supr: borra la letra de la casilla, sin moverse. Devuelve la letra borrada."""
		letra = self.letras.get(self.casilla)
		self._cambiar(self.casilla, None)
		return letra

	def retroceder(self) -> tuple[str | None, bool]:
		"""Retroceso: si la casilla tiene letra, la borra; si está vacía, va a la anterior y la borra.

		Devuelve la letra borrada y si el cursor se movió.
		"""
		if self.casilla in self.letras:
			return self.borrar(), False
		anterior = self._siguiente_en_palabra(-1)
		if anterior is None:
			return None, False
		self.casilla = anterior
		return self.borrar(), True

	def deshacer(self) -> Casilla | None:
		"""Deshace el último cambio y lleva el cursor a esa casilla. None si no hay nada que deshacer."""
		if not self._historial:
			return None
		cambio = self._historial.pop()
		if cambio.antes is None:
			self.letras.pop(cambio.casilla, None)
		else:
			self.letras[cambio.casilla] = cambio.antes
		self.casilla = cambio.casilla
		if self.palabra_en(cambio.casilla, self.direccion) is None:
			self.direccion = self.direccion.otra
		return cambio.casilla

	def reiniciar(self) -> None:
		self.letras.clear()
		self._historial.clear()
		self.segundos = 0.0
		self.ayudas = 0
		self.ir_a_palabra(self.orden[0])

	# Guardar.

	def a_json(self) -> str:
		c = self.crucigrama
		datos = {
			"version": VERSION,
			"tamano": c.tamano.value,
			"dificultad": c.dificultad.value,
			"semilla": c.semilla,
			"tema": c.tema,
			"alto": c.alto,
			"ancho": c.ancho,
			"palabras": [
				{
					**banco.entrada_a_dict(p.entrada),
					"fila": p.fila,
					"columna": p.columna,
					"direccion": p.direccion.value,
					"numero": p.numero,
				}
				for p in c.palabras
			],
			"letras": [[f, col, letra] for (f, col), letra in sorted(self.letras.items())],
			"cursor": [self.casilla[0], self.casilla[1], self.direccion.value],
			"segundos": round(self.segundos, 1),
			"ayudas": self.ayudas,
			"con_ayudas": self.con_ayudas,
			"del_dia": self.del_dia,
		}
		return json.dumps(datos, ensure_ascii=False)

	@classmethod
	def desde_json(cls, texto: str) -> "Partida":
		"""Lee una partida guardada. Lanza ValueError si el archivo no tiene la forma esperada."""
		try:
			datos: dict[str, Any] = json.loads(texto)
			if datos.get("version") != VERSION:
				raise ValueError("Versión de partida no reconocida")
			palabras = [
				PalabraColocada(
					banco.entrada_desde_dict(p),
					int(p["fila"]),
					int(p["columna"]),
					Direccion(p["direccion"]),
					int(p["numero"]),
				)
				for p in datos["palabras"]
			]
			crucigrama = Crucigrama(
				int(datos["alto"]),
				int(datos["ancho"]),
				palabras,
				Tamano(datos["tamano"]),
				Dificultad(datos["dificultad"]),
				int(datos["semilla"]),
				datos.get("tema"),
			)
			partida = cls(crucigrama)
			for f, col, letra in datos["letras"]:
				casilla = (int(f), int(col))
				if casilla in partida._palabras_de and normalizar_letra(letra):
					partida.letras[casilla] = normalizar_letra(letra)
			f, col, direccion = datos["cursor"]
			casilla = (int(f), int(col))
			if partida.palabra_en(casilla, Direccion(direccion)) is not None:
				partida.casilla = casilla
				partida.direccion = Direccion(direccion)
			partida.segundos = float(datos.get("segundos", 0))
			partida.ayudas = int(datos.get("ayudas", 0))
			partida.con_ayudas = bool(datos.get("con_ayudas", True))
			partida.del_dia = datos.get("del_dia")
		except (KeyError, TypeError, IndexError) as error:
			raise ValueError("Partida guardada no válida") from error
		return partida

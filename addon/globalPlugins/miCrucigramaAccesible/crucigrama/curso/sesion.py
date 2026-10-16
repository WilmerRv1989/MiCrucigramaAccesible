# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Un ejercicio en curso: qué se acepta, qué se dice y cuándo está superado.

A diferencia del juego, en las lecciones una letra equivocada no se escribe: se dice que no va
y se repite la pista, para aprender sin tener que buscar el error después. Las letras buenas se
aceptan en cualquier casilla; el ejercicio termina cuando sus casillas objetivo están bien.
"""

import json
import random
from collections.abc import Callable
from dataclasses import dataclass, field

from .. import anunciador
from ..generador import Direccion, PalabraColocada
from ..idioma import _, ngettext
from ..partida import Partida
from ..texto import normalizar_letra
from .modelo import Ejercicio


@dataclass
class Respuesta:
	mensaje: str
	# Si el tablero cambió (hay que redibujarlo).
	aceptada: bool = False
	# Si suena el tono de error.
	error: bool = False
	# Palabras que se llenaron (suena el sonido de completar).
	completadas: list[PalabraColocada] = field(default_factory=list[PalabraColocada])
	superado: bool = False


def texto_animo(elegir: Callable[[list[str]], str] = random.choice) -> str:
	return elegir(
		[
			# Translators: praise when an exercise of the course is done.
			_("Very good!"),
			# Translators: praise when an exercise of the course is done.
			_("Excellent!"),
			# Translators: praise when an exercise of the course is done.
			_("You did it!"),
			# Translators: praise when an exercise of the course is done.
			_("Well done!"),
		],
	)


def texto_estrellas(estrellas: int) -> str:
	# Translators: stars earned in an exercise of the course.
	return ngettext("You earned {count} star.", "You earned {count} stars.", estrellas).format(
		count=estrellas,
	)


class SesionEjercicio:
	def __init__(self, ejercicio: Ejercicio) -> None:
		self.ejercicio = ejercicio
		self.partida = Partida(ejercicio.crucigrama, dict(ejercicio.letras), con_ayudas=True)
		self.partida.casilla = ejercicio.inicio
		self.partida.direccion = ejercicio.direccion
		# 0: ninguna ayuda; 1: una letra (F7); 2: la palabra entera (Mayúsculas+F7).
		self.ayuda_usada = 0
		# Ayudas pedidas: en un crucigrama entero, las estrellas dependen de cuántas.
		self.ayudas_pedidas = 0
		self.superado = False
		# Si se continúa un crucigrama entero que quedó a medias.
		self.continuada = False

	@property
	def estrellas(self) -> int:
		"""3, 2 o 1. En un crucigrama entero, según cuántas ayudas (0 o 1, de 2 a 4, 5 o más);
		en los demás ejercicios, según la ayuda más completa que se usó."""
		if self.ejercicio.entero:
			if self.ayudas_pedidas <= 1:
				return 3
			return 2 if self.ayudas_pedidas <= 4 else 1
		return 3 - self.ayuda_usada

	# Crucigrama entero a medias.

	@property
	def se_guarda(self) -> bool:
		"""Solo se guarda a medias un crucigrama entero: los demás ejercicios son cortos."""
		return self.ejercicio.entero and not self.superado

	def a_json(self) -> str:
		partida = self.partida
		return json.dumps(
			{
				"id": self.ejercicio.id,
				"letras": [[f, c, letra] for (f, c), letra in sorted(partida.letras.items())],
				"cursor": [partida.casilla[0], partida.casilla[1], partida.direccion.value],
				"ayudas": self.ayudas_pedidas,
			},
			ensure_ascii=False,
		)

	def continuar(self, texto: str) -> bool:
		"""Recupera el crucigrama entero guardado, si es de este ejercicio. Devuelve True si lo recuperó."""
		partida = self.partida
		try:
			datos = json.loads(texto)
			if datos["id"] != self.ejercicio.id:
				return False
			letras = {(int(f), int(c)): normalizar_letra(letra) for f, c, letra in datos["letras"]}
			fila, columna, texto_direccion = datos["cursor"]
			direccion = Direccion(texto_direccion)
			ayudas = int(datos["ayudas"])
		except (KeyError, TypeError, ValueError):
			return False
		if not all(partida.es_casilla(c) and letra for c, letra in letras.items()):
			return False
		partida.letras = letras
		casilla = (int(fila), int(columna))
		if partida.palabra_en(casilla, direccion) is not None:
			partida.casilla = casilla
			partida.direccion = direccion
		self.ayudas_pedidas = ayudas
		self.continuada = True
		return True

	def _hecho(self) -> bool:
		partida = self.partida
		return all(partida.letra(c) == partida.solucion(c) for c in self.ejercicio.objetivos)

	def _ya_superado(self) -> Respuesta:
		# Translators: said when trying to change the board of an exercise that is already done.
		return Respuesta(_("This exercise is already done."), error=True)

	def escribir(self, caracter: str) -> Respuesta:
		partida = self.partida
		letra = normalizar_letra(caracter)
		if not letra:
			# Translators: said when typing something that is not a letter on the board.
			return Respuesta(_("Only letters can be written."), error=True)
		if self.superado:
			return self._ya_superado()
		if letra != partida.solucion(partida.casilla):
			# Translators: said in a lesson when a letter does not go in the cell, followed by the clue, as in "The B does not go here. Clue: Says quack."
			mensaje = _("The {letter} does not go here. Clue: {clue}").format(
				letter=letra,
				clue=partida.palabra_actual.entrada.pista,
			)
			return Respuesta(mensaje, error=True)
		resultado = partida.escribir(letra)
		assert resultado is not None
		respuesta = Respuesta(
			anunciador.describir_escritura(partida, resultado),
			aceptada=True,
			completadas=resultado.completadas,
		)
		if self._hecho():
			self.superado = respuesta.superado = True
		return respuesta

	def borrar(self) -> Respuesta:
		if self.superado:
			return self._ya_superado()
		letra = self.partida.borrar()
		return Respuesta(anunciador.describir_borrado(letra), aceptada=letra is not None)

	def retroceder(self) -> tuple[Respuesta, bool]:
		"""Retroceso, como en el juego. Devuelve la respuesta y si el cursor se movió."""
		if self.superado:
			return self._ya_superado(), False
		letra, movido = self.partida.retroceder()
		return Respuesta(anunciador.describir_borrado(letra), aceptada=letra is not None), movido

	def ayuda(self, palabra: bool) -> str:
		"""F7 (una letra) o Mayúsculas+F7 (la palabra): cuentan para las estrellas."""
		self.ayuda_usada = max(self.ayuda_usada, 2 if palabra else 1)
		self.ayudas_pedidas += 1
		if palabra:
			return anunciador.describir_ayuda_palabra(self.partida)
		return anunciador.describir_ayuda_letra(self.partida)

	def texto_superado(self) -> str:
		return f"{texto_animo()} {texto_estrellas(self.estrellas)}"

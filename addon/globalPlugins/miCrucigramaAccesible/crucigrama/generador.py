# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Generador de crucigramas de palabras cruzadas.

Cómo se genera un crucigrama:
1. Se eligen las palabras posibles del banco según la dificultad (o el tema infantil) y su largo.
2. Se pone una primera palabra en horizontal y se van añadiendo palabras que crucen
   alguna de las ya puestas, sin salirse del lado máximo del tamaño.
   Una palabra solo se pone si no deja letras pegadas a otras palabras (que formarían palabras
   que no están en el crucigrama) y si no alarga otra palabra por sus extremos.
3. En cada paso se prueban unas cuantas palabras al azar y se elige el mejor sitio: en fácil,
   donde cruza más palabras (cada cruce regala una letra); en difícil, donde cruza solo una.
4. Se hacen varios crucigramas completos con otro orden y se elige el que tiene más letras
   compartidas en fácil y menos en difícil. Si alguno no llega al número de palabras del tamaño,
   se descarta. Todo depende de la semilla: la misma semilla da siempre el mismo crucigrama.
5. Al final se numeran las palabras en orden de lectura, como en papel: de arriba abajo
   y de izquierda a derecha; si una horizontal y una vertical empiezan en la misma casilla,
   comparten número.
"""

import enum
import random
from collections.abc import Callable
from dataclasses import dataclass, field

from .banco import Dificultad, Entrada

# Veces que se vuelve a empezar antes de conformarse con el crucigrama más completo.
_INTENTOS = 60
# Crucigramas completos entre los que se elige el que mejor encaja con la dificultad.
_COMPLETOS = 8
# Palabras que se prueban en cada paso antes de elegir el mejor sitio.
_MUESTRA = 40

Casilla = tuple[int, int]


class Tamano(enum.Enum):
	PEQUENO = "pequeno"
	MEDIANO = "mediano"
	GRANDE = "grande"

	@property
	def palabras(self) -> int:
		return {Tamano.PEQUENO: 6, Tamano.MEDIANO: 12, Tamano.GRANDE: 20}[self]

	@property
	def lado(self) -> int:
		"""El máximo de filas y de columnas del tablero."""
		return {Tamano.PEQUENO: 9, Tamano.MEDIANO: 13, Tamano.GRANDE: 17}[self]


class Direccion(enum.Enum):
	HORIZONTAL = "horizontal"
	VERTICAL = "vertical"

	@property
	def paso(self) -> Casilla:
		"""Cuánto cambian la fila y la columna de una letra a la siguiente."""
		return (0, 1) if self is Direccion.HORIZONTAL else (1, 0)

	@property
	def otra(self) -> "Direccion":
		return Direccion.VERTICAL if self is Direccion.HORIZONTAL else Direccion.HORIZONTAL


def largos(dificultad: Dificultad) -> tuple[int, int]:
	"""El largo mínimo y máximo de las palabras de cada dificultad."""
	return {
		Dificultad.FACIL: (3, 7),
		Dificultad.NORMAL: (3, 9),
		Dificultad.DIFICIL: (4, 10),
	}[dificultad]


@dataclass(frozen=True)
class PalabraColocada:
	"""Una palabra en el tablero. La fila y la columna son las de su primera letra, desde 0."""

	entrada: Entrada
	fila: int
	columna: int
	direccion: Direccion
	numero: int

	@property
	def clave(self) -> str:
		return self.entrada.clave

	@property
	def largo(self) -> int:
		return len(self.clave)

	def casillas(self) -> list[Casilla]:
		df, dc = self.direccion.paso
		return [(self.fila + df * i, self.columna + dc * i) for i in range(self.largo)]


@dataclass
class Crucigrama:
	"""Un crucigrama generado: el tamaño del tablero y las palabras puestas, ya numeradas."""

	alto: int
	ancho: int
	palabras: list[PalabraColocada]
	tamano: Tamano
	dificultad: Dificultad
	semilla: int
	tema: str | None = None
	_letras: dict[Casilla, str] = field(default_factory=dict[Casilla, str], init=False, repr=False)

	def __post_init__(self) -> None:
		for palabra in self.palabras:
			for casilla, letra in zip(palabra.casillas(), palabra.clave):
				self._letras[casilla] = letra

	def letra(self, fila: int, columna: int) -> str | None:
		"""La letra de la solución en esa casilla, o None si la casilla no es de ninguna palabra."""
		return self._letras.get((fila, columna))

	def palabras_en(self, fila: int, columna: int) -> list[PalabraColocada]:
		"""Las palabras que pasan por una casilla: dos si es un cruce."""
		return [p for p in self.palabras if (fila, columna) in p.casillas()]

	def de_direccion(self, direccion: Direccion) -> list[PalabraColocada]:
		"""Las horizontales o las verticales, por número."""
		return sorted((p for p in self.palabras if p.direccion is direccion), key=lambda p: p.numero)


class SinPalabrasSuficientes(ValueError):
	"""El banco no tiene bastantes palabras para ese tamaño y dificultad."""


def candidatas(banco: list[Entrada], dificultad: Dificultad, tema: str | None = None) -> list[Entrada]:
	"""Las palabras del banco que pueden salir en un crucigrama de esa dificultad o de ese tema.

	Los crucigramas infantiles usan solo las palabras de su tema. Los demás usan las palabras
	generales de su dificultad y de su largo; en fácil, solo las que tienen una pista directa.
	"""
	vistas: set[str] = set()
	resultado: list[Entrada] = []
	minimo, maximo = largos(Dificultad.FACIL if tema else dificultad)
	for entrada in banco:
		clave = entrada.clave
		if clave in vistas or not minimo <= len(clave) <= maximo:
			continue
		if tema is not None:
			if entrada.tema != tema:
				continue
		elif entrada.tema is not None or entrada.dificultad is not dificultad:
			continue
		elif dificultad is Dificultad.FACIL and not entrada.directa:
			continue
		vistas.add(clave)
		resultado.append(entrada)
	return resultado


def generar(
	banco: list[Entrada],
	tamano: Tamano,
	dificultad: Dificultad,
	semilla: int,
	tema: str | None = None,
) -> Crucigrama:
	"""Un crucigrama nuevo. Los crucigramas infantiles (con tema) son siempre fáciles."""
	if tema is not None:
		dificultad = Dificultad.FACIL
	posibles = candidatas(banco, dificultad, tema)
	if len(posibles) < tamano.palabras:
		raise SinPalabrasSuficientes(
			f"Hay {len(posibles)} palabras para {dificultad.value} y {tema}; hacen falta {tamano.palabras}",
		)
	aleatorio = random.Random(semilla)
	completos: list[_Construccion] = []
	mas_completo: _Construccion | None = None
	for _ in range(_INTENTOS):
		intento = _Construccion(tamano.lado, dificultad, aleatorio)
		intento.construir(posibles, tamano.palabras)
		if len(intento.puestas) == tamano.palabras:
			completos.append(intento)
			if len(completos) == _COMPLETOS:
				break
		elif mas_completo is None or len(intento.puestas) > len(mas_completo.puestas):
			mas_completo = intento
	if completos:
		elegido = max(completos, key=_preferencia(dificultad))
	else:
		assert mas_completo is not None
		elegido = mas_completo
	return numerar(elegido.puestas, tamano, dificultad, semilla, tema)


def _preferencia(dificultad: Dificultad) -> Callable[["_Construccion"], float]:
	"""Cómo se elige entre varios crucigramas completos: más cruces en fácil, menos en difícil.

	Los cruces se cuentan por letra (qué parte de las letras se comparte) para no premiar
	las palabras largas. A igualdad, gana el tablero más compacto.
	"""
	signo = {Dificultad.FACIL: 1.0, Dificultad.NORMAL: 0.0, Dificultad.DIFICIL: -1.0}[dificultad]

	def puntos(intento: _Construccion) -> float:
		fila_min, fila_max, col_min, col_max = intento.limites
		area = (fila_max - fila_min + 1) * (col_max - col_min + 1)
		return signo * intento.proporcion_de_cruces() - 0.001 * area

	return puntos


class _Construccion:
	"""Un intento de poner las palabras, una tras otra."""

	def __init__(self, lado: int, dificultad: Dificultad, aleatorio: random.Random) -> None:
		self.lado = lado
		self.dificultad = dificultad
		self.aleatorio = aleatorio
		self.letras: dict[Casilla, str] = {}
		# Las direcciones de las palabras que pasan por cada casilla.
		self.direcciones: dict[Casilla, set[Direccion]] = {}
		# Las casillas con cada letra que todavía se pueden cruzar (tienen una sola palabra).
		self.cruzables: dict[str, set[Casilla]] = {}
		self.puestas: list[tuple[Entrada, Casilla, Direccion]] = []
		self.limites = (0, 0, 0, 0)  # fila mínima, fila máxima, columna mínima, columna máxima

	def construir(self, posibles: list[Entrada], objetivo: int) -> None:
		restantes = list(posibles)
		self.aleatorio.shuffle(restantes)
		primera = restantes.pop()
		self._poner(primera, (0, 0), Direccion.HORIZONTAL)
		while len(self.puestas) < objetivo and restantes:
			eleccion = self._mejor_sitio(restantes)
			if eleccion is None:
				break
			entrada, inicio, direccion = eleccion
			restantes.remove(entrada)
			self._poner(entrada, inicio, direccion)

	def proporcion_de_cruces(self) -> float:
		"""Qué parte de las casillas son cruces."""
		cruces = sum(1 for direcciones in self.direcciones.values() if len(direcciones) == 2)
		return cruces / len(self.letras)

	def _mejor_sitio(self, restantes: list[Entrada]) -> tuple[Entrada, Casilla, Direccion] | None:
		"""El mejor sitio entre unas cuantas palabras; si ninguna cabe, prueba con las siguientes."""
		for desde in range(0, len(restantes), _MUESTRA):
			mejor: tuple[float, Entrada, Casilla, Direccion] | None = None
			for entrada in restantes[desde : desde + _MUESTRA]:
				for inicio, direccion, cruces, limites in self._sitios(entrada.clave):
					puntos = self._puntuar(cruces, limites)
					if mejor is None or puntos > mejor[0]:
						mejor = (puntos, entrada, inicio, direccion)
			if mejor is not None:
				return mejor[1], mejor[2], mejor[3]
		return None

	def _sitios(self, clave: str) -> list[tuple[Casilla, Direccion, int, tuple[int, int, int, int]]]:
		"""Los sitios donde la palabra cruza alguna puesta, con sus cruces y los nuevos límites."""
		sitios: list[tuple[Casilla, Direccion, int, tuple[int, int, int, int]]] = []
		vistos: set[tuple[Casilla, Direccion]] = set()
		for indice, letra in enumerate(clave):
			for casilla in self.cruzables.get(letra, ()):
				(ocupada,) = self.direcciones[casilla]
				direccion = ocupada.otra
				df, dc = direccion.paso
				inicio = (casilla[0] - df * indice, casilla[1] - dc * indice)
				if (inicio, direccion) in vistos:
					continue
				vistos.add((inicio, direccion))
				resultado = self._comprobar(clave, inicio, direccion)
				if resultado is not None:
					sitios.append((inicio, direccion, *resultado))
		return sitios

	def _comprobar(
		self,
		clave: str,
		inicio: Casilla,
		direccion: Direccion,
	) -> tuple[int, tuple[int, int, int, int]] | None:
		"""Los cruces y los nuevos límites si la palabra cabe ahí; None si no cabe."""
		df, dc = direccion.paso
		fila, columna = inicio
		largo = len(clave)
		# Nada justo antes ni justo después: la palabra no puede alargar otra.
		if (fila - df, columna - dc) in self.letras or (
			fila + df * largo,
			columna + dc * largo,
		) in self.letras:
			return None
		cruces = 0
		for i, letra in enumerate(clave):
			casilla = (fila + df * i, columna + dc * i)
			existente = self.letras.get(casilla)
			if existente is not None:
				if existente != letra or direccion in self.direcciones[casilla]:
					return None
				cruces += 1
				continue
			# Una letra nueva no puede tocar otra por los lados: formaría una palabra que no existe.
			if (casilla[0] + dc, casilla[1] + df) in self.letras or (
				casilla[0] - dc,
				casilla[1] - df,
			) in self.letras:
				return None
		if cruces == 0 or cruces == largo:
			return None
		fila_min, fila_max, col_min, col_max = self.limites
		limites = (
			min(fila_min, fila),
			max(fila_max, fila + df * (largo - 1)),
			min(col_min, columna),
			max(col_max, columna + dc * (largo - 1)),
		)
		if limites[1] - limites[0] >= self.lado or limites[3] - limites[2] >= self.lado:
			return None
		return cruces, limites

	def _puntuar(self, cruces: int, limites: tuple[int, int, int, int]) -> float:
		"""Más puntos al sitio que mejor encaja con la dificultad, y a los tableros compactos."""
		if self.dificultad is Dificultad.FACIL:
			por_cruces = 10.0 * cruces
		elif self.dificultad is Dificultad.NORMAL:
			por_cruces = 4.0 * cruces
		else:
			por_cruces = -6.0 * (cruces - 1)
		alto = limites[1] - limites[0] + 1
		ancho = limites[3] - limites[2] + 1
		compacto = -0.15 * max(alto, ancho) - 0.02 * alto * ancho
		return por_cruces + compacto + self.aleatorio.random() * 2

	def _poner(self, entrada: Entrada, inicio: Casilla, direccion: Direccion) -> None:
		clave = entrada.clave
		df, dc = direccion.paso
		for i, letra in enumerate(clave):
			casilla = (inicio[0] + df * i, inicio[1] + dc * i)
			if casilla in self.letras:
				# Ya es un cruce: no se puede volver a cruzar.
				self.cruzables[letra].discard(casilla)
			else:
				self.letras[casilla] = letra
				self.cruzables.setdefault(letra, set()).add(casilla)
			self.direcciones.setdefault(casilla, set()).add(direccion)
		self.puestas.append((entrada, inicio, direccion))
		fila_min, fila_max, col_min, col_max = self.limites
		self.limites = (
			min(fila_min, inicio[0]),
			max(fila_max, inicio[0] + df * (len(clave) - 1)),
			min(col_min, inicio[1]),
			max(col_max, inicio[1] + dc * (len(clave) - 1)),
		)


def numerar(
	puestas: list[tuple[Entrada, Casilla, Direccion]],
	tamano: Tamano,
	dificultad: Dificultad,
	semilla: int,
	tema: str | None,
) -> Crucigrama:
	"""Lleva el tablero a la fila y la columna 0 y numera las palabras en orden de lectura."""
	fila_min = min(inicio[0] for _, inicio, _ in puestas)
	col_min = min(inicio[1] for _, inicio, _ in puestas)
	movidas = [(entrada, (f - fila_min, c - col_min), d) for entrada, (f, c), d in puestas]
	inicios = sorted({inicio for _, inicio, _ in movidas})
	numeros = {inicio: numero for numero, inicio in enumerate(inicios, start=1)}
	palabras = [
		PalabraColocada(entrada, inicio[0], inicio[1], direccion, numeros[inicio])
		for entrada, inicio, direccion in movidas
	]
	palabras.sort(key=lambda p: (p.numero, p.direccion is Direccion.VERTICAL))
	alto = max(p.casillas()[-1][0] for p in palabras) + 1
	ancho = max(p.casillas()[-1][1] for p in palabras) + 1
	return Crucigrama(alto, ancho, palabras, tamano, dificultad, semilla, tema)

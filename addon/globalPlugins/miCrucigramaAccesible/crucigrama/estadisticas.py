# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Estadísticas: crucigramas resueltos, mejores tiempos, ayudas y los días seguidos del crucigrama del día.

Se guardan en un archivo JSON. Un archivo dañado no impide jugar: se empieza de cero.
Las fechas se reciben como parámetro, para poder probarlo sin depender del día de hoy.
"""

import datetime
import json
import os

from . import vista
from .anunciador import unir
from .curso.modelo import Curso
from .curso.progreso import Progreso
from .banco import Dificultad
from .generador import Tamano
from .idioma import _, ngettext

VERSION = 1

# Los crucigramas infantiles se cuentan juntos, sean del tema que sean.
INFANTIL = "infantil"


def clave(tamano: Tamano, dificultad: Dificultad, tema: str | None) -> str:
	return INFANTIL if tema else f"{tamano.value}-{dificultad.value}"


class Estadisticas:
	def __init__(self, ruta: str) -> None:
		self.ruta = ruta
		# «mediano-normal» o «infantil» → {"total": resueltos, "sin_ayudas": de ellos, "mejor": segundos}.
		self.resueltos: dict[str, dict[str, int]] = {}
		# Ayudas pedidas en los crucigramas resueltos.
		self.ayudas = 0
		# Crucigrama del día: última fecha resuelta, días seguidos, récord y total.
		self.ultimo_del_dia: str | None = None
		self.racha = 0
		self.record = 0
		self.total_del_dia = 0
		self.cargar()

	def cargar(self) -> None:
		try:
			with open(self.ruta, encoding="utf-8") as archivo:
				datos = json.load(archivo)
		except (OSError, ValueError):
			return
		if not isinstance(datos, dict) or datos.get("version") != VERSION:
			return
		try:
			self.resueltos = {
				str(k): {
					"total": int(v["total"]),
					"sin_ayudas": int(v.get("sin_ayudas", 0)),
					"mejor": int(v["mejor"]),
				}
				for k, v in datos.get("resueltos", {}).items()
			}
			self.ayudas = int(datos.get("ayudas", 0))
			diario = datos.get("del_dia", {})
			self.ultimo_del_dia = diario.get("ultimo")
			self.racha = int(diario.get("racha", 0))
			self.record = int(diario.get("record", 0))
			self.total_del_dia = int(diario.get("total", 0))
		except (AttributeError, KeyError, TypeError, ValueError):
			# Archivo dañado: se empieza de cero.
			self.resueltos, self.ayudas = {}, 0
			self.ultimo_del_dia, self.racha, self.record, self.total_del_dia = None, 0, 0, 0

	def guardar(self) -> None:
		os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
		temporal = self.ruta + ".tmp"
		datos = {
			"version": VERSION,
			"resueltos": self.resueltos,
			"ayudas": self.ayudas,
			"del_dia": {
				"ultimo": self.ultimo_del_dia,
				"racha": self.racha,
				"record": self.record,
				"total": self.total_del_dia,
			},
		}
		with open(temporal, "w", encoding="utf-8") as archivo:
			json.dump(datos, archivo, ensure_ascii=False, indent=1)
		os.replace(temporal, self.ruta)

	def registrar_resuelto(
		self,
		tamano: Tamano,
		dificultad: Dificultad,
		tema: str | None,
		segundos: float,
		con_ayudas: bool,
		ayudas_usadas: int,
	) -> bool:
		"""Anota un crucigrama resuelto. Devuelve True si es el mejor tiempo de su tipo (no el primero)."""
		self.ayudas += ayudas_usadas
		segundos = round(segundos)
		sin_ayudas = 1 if not con_ayudas else 0
		datos = self.resueltos.get(clave(tamano, dificultad, tema))
		if datos is None:
			self.resueltos[clave(tamano, dificultad, tema)] = {
				"total": 1,
				"sin_ayudas": sin_ayudas,
				"mejor": segundos,
			}
			return False
		datos["total"] += 1
		datos["sin_ayudas"] += sin_ayudas
		if segundos < datos["mejor"]:
			datos["mejor"] = segundos
			return True
		return False

	def racha_actual(self, hoy: datetime.date) -> int:
		"""Los días seguidos, si siguen vivos: el último resuelto fue hoy o ayer."""
		if self.ultimo_del_dia is None:
			return 0
		ultimo = datetime.date.fromisoformat(self.ultimo_del_dia)
		return self.racha if (hoy - ultimo).days <= 1 else 0

	def resuelto_hoy(self, hoy: datetime.date) -> bool:
		return self.ultimo_del_dia == hoy.isoformat()

	def registrar_del_dia(self, fecha: datetime.date) -> int:
		"""Anota el crucigrama del día resuelto y devuelve los días seguidos."""
		if self.resuelto_hoy(fecha):
			return self.racha
		self.racha = self.racha_actual(fecha) + 1
		self.record = max(self.record, self.racha)
		self.total_del_dia += 1
		self.ultimo_del_dia = fecha.isoformat()
		return self.racha


def texto_tiempo(segundos: float) -> str:
	"""«12 minutos y 5 segundos»."""
	total = int(segundos)
	horas, resto = divmod(total, 3600)
	minutos, segundos_ = divmod(resto, 60)
	partes = []
	if horas:
		# Translators: part of a duration.
		partes.append(ngettext("{count} hour", "{count} hours", horas).format(count=horas))
	if minutos:
		# Translators: part of a duration.
		partes.append(ngettext("{count} minute", "{count} minutes", minutos).format(count=minutos))
	if segundos_ or not partes:
		# Translators: part of a duration.
		partes.append(ngettext("{count} second", "{count} seconds", segundos_).format(count=segundos_))
	return unir(partes)


def texto_racha(racha: int) -> str:
	return ngettext(
		# Translators: days in a row solving the crossword of the day.
		"You have solved it {count} day in a row.",
		"You have solved it {count} days in a row.",
		racha,
	).format(count=racha)


def _nombre_tipo(texto_clave: str) -> str:
	"""«Mediano, Normal» o «Infantiles»."""
	if texto_clave == INFANTIL:
		# Translators: the children's crosswords in the statistics.
		return _("Children's")
	tamano, dificultad = texto_clave.split("-")
	# Translators: a type of crossword in the statistics, as in "Medium, Normal".
	return _("{size}, {difficulty}").format(
		size=vista.nombre_tamano(Tamano(tamano)),
		difficulty=vista.nombre_dificultad(Dificultad(dificultad)),
	)


def secciones(
	estadisticas: Estadisticas,
	hoy: datetime.date,
	curso: Curso | None = None,
	progreso: Progreso | None = None,
) -> list[tuple[str, list[str]]]:
	"""Las secciones de «Mis estadísticas»: título y líneas de cada una."""
	orden = [f"{t.value}-{d.value}" for t in Tamano for d in Dificultad] + [INFANTIL]
	resueltos = []
	for texto_clave in orden:
		datos = estadisticas.resueltos.get(texto_clave)
		if datos is None:
			continue
		resueltos.append(
			ngettext(
				# Translators: a line of the statistics, as in "Medium, Normal: 5 solved, 2 without help. Best time: 20 minutes."
				"{type}: {count} solved, {without} without help. Best time: {time}.",
				"{type}: {count} solved, {without} without help. Best time: {time}.",
				datos["total"],
			).format(
				type=_nombre_tipo(texto_clave),
				count=datos["total"],
				without=datos["sin_ayudas"],
				time=texto_tiempo(datos["mejor"]),
			),
		)
	if resueltos:
		resueltos.append(
			ngettext(
				# Translators: a line of the statistics: help used in the solved crosswords.
				"Help used: {count} time.",
				"Help used: {count} times.",
				estadisticas.ayudas,
			).format(count=estadisticas.ayudas),
		)
	else:
		# Translators: statistics when no crossword has been solved yet.
		resueltos.append(_("You have not solved any crossword yet."))
	del_dia = [
		# Translators: a line of the statistics about the crossword of the day.
		_("Days in a row: {count}.").format(count=estadisticas.racha_actual(hoy)),
		ngettext(
			# Translators: a line of the statistics about the crossword of the day.
			"Record: {count} day in a row.",
			"Record: {count} days in a row.",
			estadisticas.record,
		).format(count=estadisticas.record),
		# Translators: a line of the statistics about the crossword of the day.
		_("Solved in total: {count}.").format(count=estadisticas.total_del_dia),
	]
	if estadisticas.resuelto_hoy(hoy):
		# Translators: a line of the statistics about the crossword of the day.
		del_dia.append(_("Today's crossword is already solved."))
	resultado = [
		# Translators: heading of the statistics.
		(_("Crosswords solved"), resueltos),
		# Translators: heading of the statistics.
		(_("Crossword of the day"), del_dia),
	]
	if curso is not None and progreso is not None:
		lecciones = curso.lecciones
		terminadas = sum(1 for leccion in lecciones if progreso.leccion_completada(leccion))
		estrellas = sum(progreso.estrellas_de(leccion) for leccion in lecciones)
		posibles = sum(leccion.estrellas_posibles for leccion in lecciones)
		aprender = [
			# Translators: a line of the statistics about the course.
			_("Lessons finished: {done} of {total}.").format(done=terminadas, total=len(lecciones)),
			# Translators: a line of the statistics about the course.
			_("Stars: {stars} of {total}.").format(stars=estrellas, total=posibles),
		]
		# Translators: heading of the statistics.
		resultado.append((_("Learn to play"), aprender))
	return resultado

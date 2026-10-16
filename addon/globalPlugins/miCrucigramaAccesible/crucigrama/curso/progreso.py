# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Progreso del curso: qué ejercicios están superados y con cuántas estrellas.

Se guarda en un archivo JSON. Un archivo dañado o de otra versión no impide usar el curso:
simplemente se empieza de cero.
"""

import json
import os

from .modelo import Leccion

VERSION = 1


class Progreso:
	def __init__(self, ruta: str) -> None:
		self.ruta = ruta
		# Ejercicio superado → mejores estrellas.
		self.ejercicios: dict[str, int] = {}
		self.cargar()

	def cargar(self) -> None:
		try:
			with open(self.ruta, encoding="utf-8") as archivo:
				datos = json.load(archivo)
		except (OSError, ValueError):
			return
		if isinstance(datos, dict) and datos.get("version") == VERSION:
			ejercicios = datos.get("ejercicios", {})
			if isinstance(ejercicios, dict):
				self.ejercicios = {str(k): int(v) for k, v in ejercicios.items() if isinstance(v, int)}

	def guardar(self) -> None:
		os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
		temporal = self.ruta + ".tmp"
		with open(temporal, "w", encoding="utf-8") as archivo:
			json.dump(
				{"version": VERSION, "ejercicios": self.ejercicios},
				archivo,
				ensure_ascii=False,
				indent=1,
			)
		os.replace(temporal, self.ruta)

	def registrar(self, id_ejercicio: str, estrellas: int) -> None:
		"""Marca un ejercicio como superado, conservando las mejores estrellas."""
		self.ejercicios[id_ejercicio] = max(estrellas, self.ejercicios.get(id_ejercicio, 0))

	def superado(self, id_ejercicio: str) -> bool:
		return id_ejercicio in self.ejercicios

	def leccion_completada(self, leccion: Leccion) -> bool:
		return all(self.superado(e.id) for e in leccion.ejercicios)

	def estrellas_de(self, leccion: Leccion) -> int:
		return sum(self.ejercicios.get(e.id, 0) for e in leccion.ejercicios)

	def primer_pendiente(self, leccion: Leccion) -> int:
		"""Índice del primer ejercicio sin superar; 0 si la lección ya está completa (se repite)."""
		for indice, ejercicio in enumerate(leccion.ejercicios):
			if not self.superado(ejercicio.id):
				return indice
		return 0

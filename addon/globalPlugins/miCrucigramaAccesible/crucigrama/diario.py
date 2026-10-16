# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""El crucigrama del día: uno por fecha, el mismo para todas las personas con la misma versión.

Sale de la fecha, que se usa como semilla del generador. El tamaño y la dificultad dependen del
día de la semana: la semana va subiendo y el fin de semana trae crucigramas grandes y tranquilos.
"""

import datetime

from .banco import Dificultad, Entrada
from .generador import Crucigrama, Tamano, generar

# De lunes a domingo.
_POR_DIA = [
	(Tamano.MEDIANO, Dificultad.FACIL),
	(Tamano.MEDIANO, Dificultad.FACIL),
	(Tamano.MEDIANO, Dificultad.NORMAL),
	(Tamano.MEDIANO, Dificultad.NORMAL),
	(Tamano.MEDIANO, Dificultad.DIFICIL),
	(Tamano.GRANDE, Dificultad.NORMAL),
	(Tamano.GRANDE, Dificultad.FACIL),
]


def tipo_del_dia(fecha: datetime.date) -> tuple[Tamano, Dificultad]:
	return _POR_DIA[fecha.weekday()]


def semilla_del_dia(fecha: datetime.date) -> int:
	return int(fecha.strftime("%Y%m%d"))


def crucigrama_del_dia(banco: list[Entrada], fecha: datetime.date) -> Crucigrama:
	tamano, dificultad = tipo_del_dia(fecha)
	return generar(banco, tamano, dificultad, semilla_del_dia(fecha))

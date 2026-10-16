# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Escribe en las lecciones los crucigramas enteros, a partir de su campo «generar».

Uso, desde la raíz del repositorio:

	uv run python herramientas/preparar_lecciones.py

En cada ejercicio con «generar» ({"tema": ..., "tamano": ..., "dificultad": ..., "semilla": ...})
se genera el crucigrama con el banco del complemento y se escriben sus «palabras», sus «objetivos»
(todas las palabras) y el «inicio» (la primera palabra en el orden de Tab). Con la misma semilla
y el mismo banco, el resultado es siempre el mismo: así las lecciones cargan al instante y las
pruebas no dependen del azar.
"""

import glob
import json
import os
import sys

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_COMPLEMENTO = os.path.join(_RAIZ, "addon", "globalPlugins", "miCrucigramaAccesible")
sys.path.insert(0, _COMPLEMENTO)

from crucigrama import banco  # noqa: E402
from crucigrama.banco import Dificultad  # noqa: E402
from crucigrama.generador import Direccion, Tamano, generar  # noqa: E402
from crucigrama.partida import Partida  # noqa: E402

_ORDEN_CAMPOS = [
	"id",
	"generar",
	"palabras",
	"escritas",
	"letras",
	"objetivos",
	"casillas",
	"inicio",
	"instruccion",
]


def preparar(ejercicio: dict, bancos: dict[str, list]) -> dict:
	datos = ejercicio["generar"]
	tema = datos.get("tema")
	entradas = bancos["infantil" if tema else "general"]
	crucigrama = generar(
		entradas,
		Tamano(datos["tamano"]),
		Dificultad(datos["dificultad"]),
		int(datos["semilla"]),
		tema,
	)
	primera = Partida(crucigrama).palabra_actual
	ejercicio["palabras"] = [
		{
			"palabra": p.entrada.palabra,
			"pista": p.entrada.pista,
			"fila": p.fila + 1,
			"columna": p.columna + 1,
			"direccion": p.direccion.value,
		}
		for p in sorted(crucigrama.palabras, key=lambda p: (p.numero, p.direccion is Direccion.VERTICAL))
	]
	ejercicio["objetivos"] = [p.entrada.palabra for p in crucigrama.palabras]
	ejercicio["inicio"] = [primera.fila + 1, primera.columna + 1, primera.direccion.value]
	return {campo: ejercicio[campo] for campo in _ORDEN_CAMPOS if campo in ejercicio}


def main() -> None:
	bancos = {
		nombre: banco.cargar(os.path.join(_COMPLEMENTO, "banco", f"{nombre}.json"))
		for nombre in ("general", "infantil")
	}
	for ruta in sorted(glob.glob(os.path.join(_COMPLEMENTO, "lecciones", "*", "bloque_*.json"))):
		with open(ruta, encoding="utf-8") as archivo:
			bloque = json.load(archivo)
		cambiados = 0
		for leccion in bloque["lecciones"]:
			nuevos = []
			for ejercicio in leccion["ejercicios"]:
				if "generar" in ejercicio:
					ejercicio = preparar(ejercicio, bancos)
					cambiados += 1
				nuevos.append(ejercicio)
			leccion["ejercicios"] = nuevos
		if cambiados:
			with open(ruta, "w", encoding="utf-8", newline="\n") as archivo:
				json.dump(bloque, archivo, ensure_ascii=False, indent="\t")
				archivo.write("\n")
			print(f"{os.path.relpath(ruta, _RAIZ)}: {cambiados} crucigramas")


if __name__ == "__main__":
	main()

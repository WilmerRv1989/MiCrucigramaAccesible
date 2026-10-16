# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Muestra en la consola la vista previa de un crucigrama, la misma que se ve en NVDA (en inglés).

Uso, desde la raíz del repositorio:

	uv run python herramientas/mostrar_crucigrama.py [tamaño] [dificultad] [semilla] [tema]

- tamaño: pequeno, mediano o grande (por omisión, mediano).
- dificultad: facil, normal o dificil (por omisión, normal).
- semilla: un número; la misma semilla da el mismo crucigrama (por omisión, 1).
- tema: animales, comida, colores, cuerpo, casa o escuela, para un crucigrama infantil.
"""

import os
import sys

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_COMPLEMENTO = os.path.join(_RAIZ, "addon", "globalPlugins", "miCrucigramaAccesible")
sys.path.insert(0, _COMPLEMENTO)

from crucigrama import banco, vista  # noqa: E402
from crucigrama.banco import Dificultad  # noqa: E402
from crucigrama.generador import Tamano, generar  # noqa: E402


def main() -> None:
	sys.stdout.reconfigure(encoding="utf-8")  # pyright: ignore[reportAttributeAccessIssue]
	argumentos = sys.argv[1:]
	tamano = Tamano(argumentos[0]) if len(argumentos) > 0 else Tamano.MEDIANO
	dificultad = Dificultad(argumentos[1]) if len(argumentos) > 1 else Dificultad.NORMAL
	semilla = int(argumentos[2]) if len(argumentos) > 2 else 1
	tema = argumentos[3] if len(argumentos) > 3 else None
	archivo = "infantil.json" if tema else "general.json"
	entradas = banco.cargar(os.path.join(_COMPLEMENTO, "banco", archivo))
	crucigrama = generar(entradas, tamano, dificultad, semilla, tema)
	print(f"{vista.descripcion(crucigrama)} (semilla {semilla})")
	for titulo, lineas in vista.secciones(crucigrama):
		print(f"\n{titulo}")
		print("\n".join(lineas))


if __name__ == "__main__":
	main()

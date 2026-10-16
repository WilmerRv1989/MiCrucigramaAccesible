# MiCrucigramaAccesible: crucigramas accesibles para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Un banco pequeño para las pruebas: palabras reales con pistas de relleno.

Las palabras se reparten por dificultad a ojo; el banco de verdad se prepara con herramientas/.
"""

from crucigrama.banco import Dificultad, Entrada

FACILES = """
casa perro gato mesa silla agua sol luna mar río pan leche árbol flor libro mano pie ojo boca nariz
pelo cama puerta ventana coche tren avión barco playa nube lluvia nieve fuego tierra cielo verde rojo
azul blanco negro madre padre hijo niño niña abuelo amigo escuela maestro lápiz papel reloj día noche
tarde hora año mes semana lunes martes campo ciudad pueblo calle plaza parque jardín fruta manzana pera
uva limón naranja queso huevo carne pollo pescado arroz sopa sal azúcar miel café vaso plato taza
cuchara tenedor camisa zapato falda gorro bolso mochila juego pelota muñeca globo regalo fiesta música
canción baile risa beso abrazo oso león tigre mono vaca cerdo oveja caballo burro pato ratón conejo
rana pez ballena delfín loro búho águila hormiga abeja mosca araña
"""

NORMALES = """
montaña volcán desierto bosque selva océano isla puerto faro castillo palacio iglesia museo teatro cine
hospital farmacia mercado tienda banco oficina fábrica granja molino puente túnel camino carretera
semáforo bicicleta tractor camión autobús cohete planeta estrella cometa galaxia brújula mapa tesoro
pirata espada escudo corona reina princesa caballero dragón gigante enano bruja hada duende fantasma
vampiro robot máquina motor rueda tornillo martillo serrucho tijeras aguja hilo botón bolsillo bufanda
guante abrigo paraguas espejo peine cepillo jabón toalla almohada sábana manta alfombra cortina lámpara
vela cerilla chimenea escalera ascensor terraza balcón tejado sótano desván ladrillo cemento madera
hierro plata oro cobre diamante perla cristal arena piedra roca barro hielo vapor viento trueno
relámpago tormenta arcoíris
"""

DIFICILES = """
alféizar zaguán buhardilla alacena aljibe azotea celosía dintel jamba umbral cornisa arbotante bóveda
cúpula pináculo claustro ábside crucero rosetón gárgola almena foso rastrillo atalaya alcazaba muralla
mazmorra yelmo coraza adarga alabarda ballesta carcaj aljaba estribo montura alforja zurrón cayado
aldaba picaporte cerrojo gozne bisagra pestillo candil quinqué palmatoria pebetero incensario cáliz
custodia relicario retablo hornacina pórtico peristilo atrio vestíbulo galería zócalo friso capitel
fuste plinto columna pilastra arquitrabe ménsula voluta acanto astrolabio sextante clepsidra cuadrante
gnomon catalejo periscopio alambique retorta crisol matraz probeta pipeta mortero almirez alcuza
aceitera vinagrera salero especiero azafrán comino orégano tomillo romero laurel albahaca perejil
cilantro eneldo estragón
"""

ANIMALES = """
perro gato vaca pato oso león mono rana pez loro búho cerdo oveja burro ratón conejo tigre jirafa cebra
ballena delfín tortuga pollito caballo abeja hormiga
"""


def _entradas(texto: str, dificultad: Dificultad, tema: str | None = None) -> list[Entrada]:
	return [
		# Una de cada cinco palabras tiene una pista indirecta, para probar que el nivel fácil no las usa.
		Entrada(palabra, f"Pista de prueba para {palabra}", dificultad, directa=i % 5 != 4, tema=tema)
		for i, palabra in enumerate(texto.split())
	]


def banco() -> list[Entrada]:
	return (
		_entradas(FACILES, Dificultad.FACIL)
		+ _entradas(NORMALES, Dificultad.NORMAL)
		+ _entradas(DIFICILES, Dificultad.DIFICIL)
		+ _entradas(ANIMALES, Dificultad.FACIL, tema="animales")
	)

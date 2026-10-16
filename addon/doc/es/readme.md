# MiCrucigramaAccesible

Crucigramas en español para el lector de pantalla NVDA, para todas las edades.

MiCrucigramaAccesible está pensado para que personas ciegas o con baja visión resuelvan crucigramas casilla a casilla y palabra a palabra, oyendo cada pista y sabiendo en todo momento cómo se cruzan las palabras. Está pensado también para niñas y niños, con crucigramas pequeños por temas.

Funciona con NVDA 2026.1 o posterior. No necesita Internet y no envía ningún dato: tu progreso se guarda solo en tu equipo.

## Por dónde empezar

* Si nunca has hecho un crucigrama, o nunca con un lector de pantalla, empieza por **Aprender a jugar**, desde la lección 1. En unos minutos sabrás moverte por el tablero.
* Si ya sabes, elige **Nuevo crucigrama** o prueba el **Crucigrama del día**.
* Si te atascas, empieza por otra palabra: sus letras te ayudarán. Y si juegas con ayudas, F7 te dice una letra.

Todo se abre desde el menú de NVDA (NVDA+N), Herramientas, MiCrucigramaAccesible:

* **Nuevo crucigrama...:** elegir un crucigrama y empezar.
* **Continuar el crucigrama:** solo aparece si tienes uno sin terminar.
* **Crucigrama del día:** uno nuevo cada día, el mismo para todo el mundo.
* **Aprender a jugar...:** un curso guiado, con lecciones y ejercicios. Si nunca has hecho un crucigrama, empieza por aquí.
* **Mis estadísticas...:** crucigramas resueltos, mejores tiempos y días seguidos.
* **Atajos de teclado...:** la lista de todas las teclas.

En **Nuevo crucigrama** eliges:

* **Crucigrama:** **General**, o uno de los temas infantiles: animales, comida, colores, el cuerpo, la casa o la escuela. Los infantiles son siempre pequeños y fáciles.
* **Tamaño** (en los generales): pequeño, unas 6 palabras; mediano, unas 12; grande, unas 20.
* **Dificultad** (en los generales): fácil, normal o difícil.
* **Con ayudas:** si la marcas, F7 te dice letras y palabras y Comprobar te dice dónde están los errores (ver «Ayudas»). Viene desmarcada la primera vez.

El diálogo recuerda lo que elegiste la última vez.

El tamaño dice cuánto dura el crucigrama; la dificultad, cuánto cuesta adivinar cada palabra. En fácil las palabras son muy comunes, las pistas directas y muchas letras se comparten con otra palabra, así que cada palabra que aciertas te regala letras de otras. En normal algunas pistas son un sinónimo con una pequeña ayuda («Comenzar; lo contrario de terminar»). En difícil las palabras son menos comunes y más largas, algunas pistas tienen un giro o son un sinónimo solo, como en los crucigramas de papel, y hay menos cruces.

## Cómo es el tablero

El tablero es una cuadrícula, como en papel, pero el cursor solo pisa las casillas que tienen letra: las demás no existen para ti. Te mueves por **caminitos**:

* **Izquierda y derecha** te llevan por una palabra horizontal.
* **Arriba y abajo** te llevan por una palabra vertical.
* Si en esa dirección no hay casilla con letra, suena un **choque** y te quedas donde estás.

Los **cruces** son las casillas que comparten dos palabras: ahí puedes cambiar de camino. Cuando una flecha te mueve, siempre sigues dentro de una palabra: nunca saltas a otra que solo está al lado.

### Lo que se oye

* **Al entrar en una palabra:** su número, si es horizontal o vertical, cuántas letras tiene y su pista. Por ejemplo: «3 horizontal, 4 letras: Hace cuac y nada en el estanque». Si ya tiene algo escrito, se dice después: «Escrito: pato» si está completa, o letra a letra, «Escrito: P, A, vacía, O», si está a medias.
* **En cada casilla:** la letra que escribiste, o «vacía», y en qué letra de la palabra estás: «vacía, letra 2 de 4».
* **En un cruce, además:** con qué palabra se cruza y en qué letra de ella: «cruza con 1 vertical, letra 2».

La fila y la columna no se dicen al moverte, para no cansar; las tienes en F6. Para volver a oír la casilla donde estás, pulsa Espacio.

## Escribir

Escribe las letras con el teclado. Cada letra se pone en la casilla y el cursor avanza a la siguiente de la palabra. En la última letra se queda, y si la palabra ya no tiene casillas vacías oyes, por ejemplo, «3 horizontal completa» (eso no dice si está bien, solo que está llena).

**¿Por qué palabra sigue al escribir?** Por la que llegaste: si llegaste con flecha abajo, al escribir sigues bajando; si llegaste con flecha derecha, con Tab o desde la lista de pistas, sigues esa palabra. Para cambiar de dirección en un cruce, muévete una casilla con la flecha de la otra dirección y vuelve.

Como en los crucigramas impresos, las tildes no cuentan: puedes escribir la A o la Á, es la misma letra. La Ñ sí es una letra propia.

## Teclas del tablero

| Tecla | Acción |
|---|---|
| Flechas | Seguir las palabras casilla a casilla; el choque indica que por ahí no hay letra |
| Inicio / Fin | Primera o última letra de la palabra |
| Tab / Mayúsculas+Tab | Palabra siguiente o anterior, por número |
| F4 | Lista de todas las pistas: eliges una con las flechas y pulsas Intro para ir a su palabra |
| Letras | Escribir la letra y avanzar |
| Retroceso | Borra la letra de la casilla; si está vacía, retrocede y borra la anterior |
| Suprimir | Borra la letra de la casilla, sin moverte |
| Control+Z | Deshacer |
| F2 | Repetir la pista de la palabra |
| Mayúsculas+F2 | En un cruce, la pista de la otra palabra |
| F3 | Las letras de la palabra, con las vacías: «C, vacía, S, A» |
| Mayúsculas+F3 | La palabra tal como está escrita: «casa», o con los huecos, «ca, hueco, a» |
| Espacio | Volver a leer la casilla donde estás |
| F7 | Ayuda: dice qué letra va en la casilla, sin escribirla |
| Mayúsculas+F7 | Ayuda: dice la palabra entera y la deletrea, sin escribirla |
| F5 | Cuántas palabras están completas y cuáles faltan |
| F6 | Fila y columna de la casilla |
| Aplicaciones o Mayúsculas+F10 | Menú del tablero |
| Escape | Cerrar el tablero; el crucigrama se guarda para continuarlo |

Puedes cambiar estas teclas en el menú de NVDA, Preferencias, Gestos de entrada, categoría MiCrucigramaAccesible, con el foco en el tablero.

## Menú del tablero

* **Comprobar:** dice cuántas letras están mal y cuántas casillas faltan; con ayudas, también en qué palabras, sin decir cuáles. Por ejemplo: «2 letras incorrectas, en 3 horizontal y 5 vertical. Faltan 4 casillas».
* **Reiniciar:** borra todas las letras, después de preguntarte.
* **Nuevo crucigrama...**
* **Atajos de teclado:** la lista de teclas, tal como las tengas asignadas.
* **Cerrar el tablero.**

Si llenas todas las casillas y alguna letra está mal, te avisa; con ayudas, también en qué palabras: «El crucigrama está lleno, pero hay letras incorrectas en 3 horizontal». Cuando todas las letras están bien, suena una melodía y oyes «¡Crucigrama resuelto!» y el tiempo que tardaste.

## Guardado automático

Cada letra que escribes se guarda al momento. Puedes cerrar el tablero con Escape, o incluso cerrar NVDA, y seguir otro día con **Continuar el crucigrama**. El crucigrama del día tiene su propio guardado, y también los crucigramas enteros del curso. Un crucigrama resuelto ya no se guarda: no queda nada que continuar.

## Ayudas

Cada crucigrama se juega con ayudas o sin ellas, según la casilla **Con ayudas** del diálogo de nuevo crucigrama. Se decide al empezar y no cambia hasta el final; el título de la ventana dice «sin ayudas» cuando lo es.

Con ayudas:

* **F7** te dice qué letra va en la casilla donde estás. Muchas veces una sola letra basta para adivinar la palabra.
* **Mayúsculas+F7** te dice la palabra entera y te la deletrea.
* **Comprobar** y el aviso de tablero lleno dicen en qué palabras están las letras mal.

Las ayudas no escriben nada: la letra o la palabra las escribes tú. Si te atascas, pídelas sin miedo: también se aprende así.

Sin ayudas, F7 y Mayúsculas+F7 no dicen nada, y Comprobar dice solo cuántas letras están mal, sin decir dónde, como al mirar la solución en el periódico. Las lecturas (Espacio, F3, Mayúsculas+F3 y lo escrito al entrar en una palabra) funcionan siempre: no son ayudas, solo te dejan oír lo que se ve en el tablero.

## Aprender a jugar

Es un curso guiado, pensado también para niñas y niños. Cada lección empieza con una explicación breve y sigue con ejercicios en crucigramas pequeños.

En la lista de lecciones ves cómo vas en cada una. Al elegir una, se lee su explicación; con Empezar pasas a los ejercicios. Si la dejaste a medias, sigue donde lo dejaste.

En los ejercicios usas las mismas teclas que en el juego, y además:

* **F9** repite lo que tienes que hacer en el ejercicio.
* **Mayúsculas+F9** repite la explicación de la lección.

En las lecciones una letra equivocada no se escribe: oyes que no va y te repito la pista. Control+Z no hace nada, porque no hay errores que deshacer.

Cada ejercicio da hasta 3 estrellas: 3 si lo haces sin ayuda, 2 si pediste una letra con F7 y 1 si pediste la palabra con Mayúsculas+F7. Los errores no quitan estrellas. Al terminar una lección, el menú del tablero (tecla Aplicaciones) te lleva a la siguiente.

Bloque A, Conocer el crucigrama:

1. ¿Qué es un crucigrama?
2. Caminitos.
3. Escribir y borrar.
4. Saltar entre palabras.
5. Escuchar el tablero.

Bloque B, Estrategias:

6. Empieza por lo seguro.
7. Los cruces regalan letras.
8. El largo y el patrón.
9. Pistas que dan la forma: verbos, plurales y femeninos.
10. Sinónimos y pistas con truco.
11. Cuando te atascas.

Bloque C, A jugar:

12. Tu primer crucigrama: dos pequeños, de animales y de comida.
13. Un mediano fácil.
14. Un mediano normal.

En los crucigramas enteros del bloque C, las estrellas dependen de cuántas ayudas pidas: con una o ninguna, 3; de 2 a 4, 2; con 5 o más, 1. Si cierras la lección a medias, al volver sigues donde lo dejaste.

## Crucigrama del día

Cada día hay un crucigrama nuevo, el mismo para todas las personas que tengan esta versión. Al abrirlo por primera vez cada día te pregunta si quieres jugarlo con ayudas o sin ellas. La semana va subiendo de dificultad, y el fin de semana trae crucigramas más largos y tranquilos:

| Día | Crucigrama |
|---|---|
| Lunes y martes | Mediano, fácil |
| Miércoles y jueves | Mediano, normal |
| Viernes | Mediano, difícil |
| Sábado | Grande, normal |
| Domingo | Grande, fácil |

Tiene su propio guardado: no pisa el crucigrama normal que tengas a medias. Si lo resuelves varios días seguidos, al terminar oyes cuántos llevas. Si vuelves a abrirlo el mismo día después de resolverlo, te dice que vuelvas mañana.

## Mis estadísticas

Muestra, por tamaño y dificultad (y los infantiles juntos), cuántos crucigramas resolviste, cuántos sin ayudas y tu mejor tiempo; las ayudas que usaste; y del crucigrama del día, los días seguidos, tu récord y el total. Se recorre con las flechas, y con H se salta de una sección a otra.

El tiempo solo cuenta mientras la ventana del tablero está activa. Al resolver un crucigrama oyes el tiempo y, si lo es, que es tu mejor tiempo en ese tamaño y dificultad.

## Opciones

En el menú de NVDA, Preferencias, Opciones, categoría MiCrucigramaAccesible:

* **Reproducir sonidos** (al completar una palabra y al resolver el crucigrama).
* **Decir con qué palabra se cruza cada casilla.** Si ya conoces bien el tablero, desactivarlo hace los anuncios más cortos; Mayúsculas+F2 sigue diciendo el cruce.
* **Decir lo escrito al entrar en una palabra.**
* **Borrar mi progreso y mis estadísticas...:** borra el progreso del curso y las estadísticas; pregunta antes. Los crucigramas a medias se quedan.

Abrir el tablero, el crucigrama del día, Aprender a jugar y Mis estadísticas no tienen tecla, pero puedes asignarles una en Gestos de entrada, categoría MiCrucigramaAccesible.

## Para quien ve la pantalla

La ventana dibuja la cuadrícula con las casillas sin letra en negro, los números de las palabras en la esquina de su primera casilla, la palabra actual en azul claro y un recuadro azul en la casilla del cursor. Si maximizas la ventana, el tablero se agranda y queda centrado.

## Sobre el braille

Todavía no lo he probado con una línea braille. Cada casilla debería mostrarse igual que se oye, pero esa parte necesita revisión. Si usas braille y algo no se lee bien, me ayudarías mucho contándomelo.

## Sobre cómo se hizo este complemento

MiCrucigramaAccesible nació porque quería un juego que ejercitara la memoria y la atención, y porque no encontré ningún crucigrama en español pensado para lectores de pantalla. Leer las pistas en voz alta no basta: lo difícil sin ver el tablero es entender cómo se cruzan las palabras, y alrededor de eso diseñé todo el juego. Es el tercero de mi colección, después de MiAjedrezAccesible y MiSudokuAccesible.

Lo desarrollé con la asistencia de Claude, un modelo de inteligencia artificial de Anthropic. Claude escribió la mayor parte del código y las pistas siguiendo mis indicaciones, consultó la documentación y el código de NVDA y me propuso soluciones técnicas. La dirección y el criterio fueron enteramente míos: el diseño funcional del complemento, la forma de recorrer el tablero, las ayudas, el curso y la forma de enseñar, la experiencia sonora, el comportamiento con el lector de pantalla y el descarte de características que no aportaban.

Cada versión, función, atajo y respuesta de voz fue probada y validada por mí directamente con NVDA. Ninguna función llegó a la versión final sin mi revisión y aprobación.

Lo cuento porque creo que es lo honesto. Si encuentras un error, o una pista que no está bien, la responsabilidad es mía, y me ayudas mucho si me escribes para corregirlo.

## Créditos

Las pistas están escritas para este juego. Para elegir las palabras y su dificultad se usaron el Wikcionario en español y la lista de frecuencias FrequencyWords de Hermit Dave, las dos con licencia CC BY-SA 4.0. El banco de palabras y pistas se distribuye con esa misma licencia. Los crucigramas se generan en el propio complemento y los sonidos son propios.

## Autoría

Desarrollado con amor por Wilmer Rodríguez Vega ([wilmer-rv.com](https://wilmer-rv.com)).

Para reportar un error, una pista equivocada o proponer una mejora, escríbeme a contacto@wilmer-rv.com o abre un reporte en [la página de GitHub del complemento](https://github.com/WilmerRv1989/MiCrucigramaAccesible/issues).

MiCrucigramaAccesible se distribuye con la licencia GPL 2 o posterior; su banco de palabras y pistas, con la licencia CC BY-SA 4.0.

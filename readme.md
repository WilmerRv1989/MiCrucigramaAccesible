# MiCrucigramaAccesible

*Crucigramas en español para NVDA, para todas las edades.*

Hola, soy Wilmer. Quería un juego que ejercitara la memoria y la atención, y pensé en los crucigramas. Busqué uno en español que se pudiera jugar de verdad con un lector de pantalla y no encontré ninguno, así que decidí hacerlo.

Lo más difícil de un crucigrama sin ver el tablero no es leer las pistas: es entender cómo se cruzan las palabras. Por eso el tablero de MiCrucigramaAccesible funciona por caminitos: el cursor solo pisa las casillas con letra, las flechas siguen las palabras, y en cada cruce te digo con qué palabra se cruza y en qué letra.

Es el tercer juego de mi colección para NVDA, después de [MiAjedrezAccesible](https://github.com/WilmerRv1989/MiAjedrezAccesible) y [MiSudokuAccesible](https://github.com/WilmerRv1989/MiSudokuAccesible). Como los otros dos, no solo deja jugar: también enseña, y está pensado para niñas y niños.

* Manual completo: [addon/doc/es/readme.md](addon/doc/es/readme.md).

## Qué vas a encontrar

* **Crucigramas pequeños, medianos y grandes**, en tres dificultades. El tamaño dice cuánto dura; la dificultad, cuánto cuesta adivinar cada palabra: lo común que es, cómo es su pista y cuántas letras te regalan los cruces.
* **Crucigramas infantiles** de animales, comida, colores, el cuerpo, la casa y la escuela, con pistas cariñosas.
* **Unas 3.500 palabras con pistas escritas para el juego.** Las fáciles describen la palabra; las difíciles a veces son un sinónimo o tienen truco, como en los crucigramas de papel.
* **Con o sin ayudas.** Con ayudas, F7 te dice una letra y Comprobar te dice en qué palabras están los errores. Las ayudas nunca escriben por ti: la palabra la escribes tú.
* **Aprender a jugar**, un curso guiado de 14 lecciones: qué es un crucigrama, cómo moverse por el tablero, estrategias para resolverlo y, al final, crucigramas enteros.
* **El crucigrama del día**, el mismo para todas las personas, para crear el hábito y sumar días seguidos.
* **Mis estadísticas**, un panel de opciones y una lista de atajos de teclado.

Todo se guarda solo: cierra el tablero, o incluso NVDA, y sigue después donde lo dejaste. El complemento funciona con NVDA 2026.1 o posterior, no necesita Internet y no envía ningún dato.

> **Sobre el braille:** todavía no lo he probado con una línea braille. Cada casilla debería mostrarse igual que se oye, pero esa parte necesita revisión. Si usas braille y algo no se lee bien, me ayudarías mucho contándomelo.

## Por dónde empezar

Todo se abre desde el menú de NVDA (NVDA+N), Herramientas, MiCrucigramaAccesible:

* Si nunca has hecho un crucigrama, o nunca con un lector de pantalla, empieza por **Aprender a jugar**, desde la lección 1.
* Si ya sabes, elige **Nuevo crucigrama** o prueba el **Crucigrama del día**.
* Si te atascas, ve a otra palabra: sus letras te ayudarán con la que se te resiste.

## Teclas del tablero

| Tecla | Acción |
|---|---|
| Flechas | Seguir las palabras casilla a casilla; el choque indica que por ahí no hay letra |
| Inicio / Fin | Primera o última letra de la palabra |
| Tab / Mayúsculas+Tab | Palabra siguiente o anterior |
| F4 | Lista de todas las pistas, para ir a una palabra |
| Letras | Escribir la letra y avanzar (las tildes no cuentan; la Ñ sí) |
| Retroceso / Suprimir | Borrar |
| Control+Z | Deshacer |
| F2 / Mayúsculas+F2 | Pista de la palabra / de la otra palabra en un cruce |
| F3 / Mayúsculas+F3 | Letras de la palabra, una a una / como palabra, con los huecos |
| Espacio | Volver a leer la casilla |
| F7 / Mayúsculas+F7 | Ayuda: la letra de la casilla / la palabra entera |
| F5 | Palabras completas y pendientes |
| F6 | Fila y columna |
| Aplicaciones o Mayúsculas+F10 | Menú del tablero |
| Escape | Cerrar el tablero (el crucigrama se guarda) |

Puedes cambiar cualquier tecla en los Gestos de entrada de NVDA, categoría MiCrucigramaAccesible.

## Cómo lo hice

Desarrollé MiCrucigramaAccesible con la asistencia de Claude, un modelo de inteligencia artificial de Anthropic. Claude escribió la mayor parte del código y de las pistas siguiendo mis indicaciones, consultó la documentación y el código de NVDA y me propuso soluciones técnicas. La dirección y las decisiones fueron mías: cómo se recorre el tablero, qué se dice en cada casilla, las ayudas, el curso y la forma de enseñar, los sonidos y qué dejar fuera.

Probé y aprobé yo mismo con NVDA cada versión, función, tecla y mensaje de voz. Te lo cuento porque creo que es lo honesto. Si encuentras un error, o una pista que no está bien, la responsabilidad es mía, y me ayudas mucho si me lo haces saber.

Para elegir las palabras y su dificultad usé el Wikcionario en español y la lista de frecuencias FrequencyWords de Hermit Dave, las dos con licencia CC BY-SA 4.0. Gracias a quienes las hacen posibles.

## Escríbeme

Si algo no funciona, si una pista no te convence, si tienes una idea o simplemente quieres contarme qué tal te fue, escríbeme a contacto@wilmer-rv.com o abre un [reporte en GitHub](https://github.com/WilmerRv1989/MiCrucigramaAccesible/issues). Lo leo todo.

Hecho con amor por Wilmer Rodríguez Vega ([wilmer-rv.com](https://wilmer-rv.com)).

El código tiene licencia GPL de GNU, versión 2 o posterior; el banco de palabras y pistas, licencia CC BY-SA 4.0.

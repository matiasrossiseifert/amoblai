# Guion · amoblai

TP 3 · 73.69 Large Language Models · ITBA 2026 · Juan Bautista Albertoni Salini, Matias Juan Rossi Seifert, Junior Rambau

Generado por `build.py` junto con `presentacion.html` (51 láminas + 4 de anexo): los números salen de los mismos archivos de resultados que las láminas. Duración estimada: **30:56** (unas 4.700 palabras. a 150 por minuto).

«▸ paso» marca dónde se aprieta → para mostrar lo siguiente de la lámina. En cada experimento, primero se ve el porqué; después qué hicimos, los resultados y la decisión. Las notas también se ven en la presentación con la tecla N; con `presentacion.html?all` cada lámina aparece con todos sus pasos (para revisar o imprimir).

Si falta tiempo, se pueden pasar rápido las dos láminas de trámite y la del costo.

| # | Lámina | Tiempo | Acumulado |
|---|---|---|---|
| 1 | Portada | 0:25 | 0:25 |
| 2 | El problema | 0:35 | 1:00 |
| 3 | Qué hace amoblai | 0:40 | 1:40 |
| 4 | Por qué RAG | 0:45 | 2:25 |
| 5 | Capítulo 01 · El recorrido | 0:08 | 2:33 |
| 6 | La planta del flujo | 0:35 | 3:08 |
| 7 | 1 · Catálogo | 0:30 | 3:38 |
| 8 | 2 · Descripción | 0:40 | 4:18 |
| 9 | 3 · Índice | 0:45 | 5:03 |
| 10 | 4 · Foto + pedido | 0:15 | 5:18 |
| 11 | 5 · Plan · el prompt | 0:55 | 6:13 |
| 12 | 5 · Plan · lo que devuelve | 0:25 | 6:38 |
| 13 | 6 · Búsqueda | 0:45 | 7:23 |
| 14 | 7 · Elección | 0:40 | 8:03 |
| 15 | 8 · Escena | 0:30 | 8:33 |
| 16 | 9 · Imagen | 0:20 | 8:53 |
| 17 | 10 · Control | 0:40 | 9:33 |
| 18 | 11 · Lista + imagen | 0:20 | 9:53 |
| 19 | Desafíos | 0:50 | 10:43 |
| 20 | Capítulo 02 · Cómo medimos | 0:08 | 10:51 |
| 21 | Dos bancos de prueba | 0:45 | 11:36 |
| 22 | Las métricas del buscador, en un ejemplo | 0:50 | 12:26 |
| 23 | Diferencias pareadas | 0:40 | 13:06 |
| 24 | El generador y los jueces | 0:55 | 14:01 |
| 25 | La imagen: las 11 corridas finales | 0:45 | 14:46 |
| 26 | Las trampas, dichas en voz alta | 0:40 | 15:26 |
| 27 | Capítulo 03 · El buscador | 0:08 | 15:34 |
| 28 | El mapa de experimentos | 0:45 | 16:19 |
| 29 | E1 · ¿Texto del vendedor, o describir cada producto? | 0:50 | 17:09 |
| 30 | E2 · ¿Cuánto suma escribir la consulta como una ficha? | 1:00 | 18:09 |
| 31 | E3 · ¿Suman la búsqueda por palabras y la foto del producto? | 1:00 | 19:09 |
| 32 | El camino, un cambio por paso | 0:50 | 19:59 |
| 33 | E4 · Cuando el primero no es el anotado, ¿se equivocó? | 0:40 | 20:39 |
| 34 | Capítulo 04 · La lista | 0:08 | 20:47 |
| 35 | E5 · Elegir con un VLM, y cuántos candidatos | 0:55 | 21:42 |
| 36 | E6 · ¿Qué catálogo: IKEA, Amazon o los dos? | 0:55 | 22:37 |
| 37 | E7 · Con búsqueda contra sin búsqueda: los dos extremos | 1:00 | 23:37 |
| 38 | Capítulo 05 · De trámite | 0:08 | 23:45 |
| 39 | E8 · ¿Cuánto cambia el número según quién escribe? | 0:35 | 24:20 |
| 40 | De trámite · el índice | 0:45 | 25:05 |
| 41 | De trámite · filtros, rerankers y catálogo | 0:45 | 25:50 |
| 42 | Capítulo 06 · Ejercicio 4 | 0:08 | 25:58 |
| 43 | Ejercicio 4 · versión 1 y su limitación | 0:50 | 26:48 |
| 44 | Ejercicio 4 · el cambio y la configuración | 0:40 | 27:28 |
| 45 | Ejercicio 4 · resultados en las dos versiones | 1:00 | 28:28 |
| 46 | Capítulo 07 · Cierre | 0:08 | 28:36 |
| 47 | El costo | 0:25 | 29:01 |
| 48 | Limitaciones | 0:30 | 29:31 |
| 49 | Trabajo futuro | 0:35 | 30:06 |
| 50 | Conclusiones | 0:40 | 30:46 |
| 51 | Gracias | 0:10 | 30:56 |


## 00 · El producto

### 1. Portada · 0:25 (acumulado 0:25)

Buenas. Somos Juan Bautista, Matías y Junior, y esto es **amoblai**.

Le das una foto de tu ambiente vacío, como este living, y le contás qué querés. Te devuelve una lista de muebles reales de un catálogo y la foto de tu cuarto amoblado con ellos.

Les contamos qué hace, cómo está armado y cómo lo medimos. Y este cuarto se va a ir amoblando mientras avanzamos.

### 2. El problema · 0:35 (acumulado 1:00)

El problema. Te mudás, tenés el ambiente vacío y una idea de lo que querés. Hay dos caminos y ninguno alcanza.

Un generador de imágenes te amobla la foto, pero con muebles inventados: estas cajas punteadas con signos de pregunta. No los podés medir ni comprar.

▸ paso: Un catálogo tiene productos reales, pero no mira tu cuarto: combinar cosas que vayan entre sí y con tu piso lo hacés vos.

▸ paso: Queremos las dos cosas a la vez: que la respuesta salga de lo que se recupera del catálogo, no de la imaginación del modelo.

### 3. Qué hace amoblai · 0:40 (acumulado 1:40)

Así se usa. El usuario sube la foto del ambiente y escribe el pedido como le sale: un living japandi, sereno, con un sofá bajo de tela beige, una mesa ratona redonda, una alfombra de fibra natural, una lámpara de papel y una planta grande.

▸ paso: amoblai devuelve la lista: 5 productos reales, 4 de IKEA y 1 de Amazon, con sus medidas cuando el catálogo las tiene. Cada uno viene con su porqué.

▸ paso: Y la imagen: el mismo cuarto, con esos productos. Esta corrida costó US$0,23. Es la que vamos a seguir en el recorrido.

### 4. Por qué RAG · 0:45 (acumulado 2:25)

¿Por qué un RAG? Por los tres desafíos de la clase. Información actualizada: el catálogo cambia y el modelo no se reentrena; un producto nuevo es una fila más en el índice.

▸ paso: Información personalizada: el LLM no conoce estos 1.502 productos; la búsqueda le trae 5 candidatos reales por pieza.

▸ paso: Y sin alucinaciones: un LLM solo recomienda un sillón que nadie vende, y un modelo de imagen solo inventa los muebles. Acá la lista solo puede tener productos que trajo la búsqueda, y la imagen se genera desde sus fotos.

▸ paso: No es un Q&A: la consulta es una foto y un pedido abierto, y hay dos generaciones aumentadas, la lista y la imagen.


## 01 · El recorrido

### 5. Capítulo 01 · El recorrido · 0:08 (acumulado 2:33)

¿Cómo está armado? Lo recorremos como una casa, ambiente por ambiente. Primera pieza del cuarto: la alfombra.

### 6. La planta del flujo · 0:35 (acumulado 3:08)

Así está armado amoblai, como la planta de una casa: cada fase es un ambiente y se pasa al siguiente por una puerta.

▸ paso: A la izquierda, un pabellón que se construye una vez, offline: catálogo, descripción e índice. El índice llega a la búsqueda por esa pasarela.

▸ paso: Lo demás se recorre en cada pedido. Por pedido se pagan tres llamadas: Opus en el plan y en la elección, y Nano Banana 2 en la imagen; unos US$0,28. Buscar corre local.

▸ paso: Los recorremos uno por uno: qué entra, qué sale y qué decidimos.

### 7. 1 · Catálogo · 0:30 (acumulado 3:38)

El catálogo. El dataset de IKEA de Tautkute y otros, revisado a mano mirando cada foto: de 855 productos quedan 819.

▸ paso: Y un segundo catálogo, Amazon Berkeley Objects, publicaciones reales de Amazon: 683 productos, casi todos con medidas. Cada uno entra con su foto, su tipo, su kind y sus medidas.

▸ paso: El kind es más fino que el tipo: hay 44, y es el filtro duro de la búsqueda. El flujo usa los dos catálogos: lo mide el experimento 6.

### 8. 2 · Descripción · 0:40 (acumulado 4:18)

La descripción. El texto del vendedor es marketing: de esta lámpara dice «da una luz suave», no que es de papel ni que parece un farol. Por eso un modelo de visión mira la foto y la describe. Es el preprocesamiento que más pesa: lo mide el experimento 1.

▸ paso: El prompt pide ocho líneas fijas, en inglés: tipo, uso, estilo de una lista cerrada, materiales, colores, forma, sensación y con qué combina. Solo lo que se ve.

▸ paso: La v3 sumó lámparas y deco; la versión por la API, para Amazon, devuelve además el kind.

▸ paso: Y esto escribió para la lámpara de la lista: papel de arroz, tipo farol, japandi.

### 9. 3 · Índice · 0:45 (acumulado 5:03)

El índice. Se embebe la descripción entera, un documento por producto, con Qwen3-Embedding-0.6B, local: 1.024 dimensiones, a ChromaDB, con la metadata de los filtros. Embedder, splitting, dimensión y base vectorial son las preguntas de trámite, por eso su llamada va punteada: las contestamos juntas más adelante.

▸ paso: Para la búsqueda híbrida se suman dos índices sobre los mismos productos: uno léxico, BM25, sobre las palabras de las descripciones, y uno por foto, con SigLIP 2, que pone la foto y el texto de la consulta en un mismo espacio.

▸ paso: Así queda un registro: el id, el documento, los mil veinticuatro números y la metadata. La lámpara no tiene medidas: se guarda menos uno y pasa cualquier filtro de tamaño.

### 10. 4 · Foto + pedido · 0:15 (acumulado 5:18)

Todo empieza con lo que pone el usuario: una foto del ambiente vacío y el pedido en texto libre.

▸ paso: Vamos a seguir este living hasta el final: un pedido japandi, sobre una foto pública, con la configuración con la que entregamos.

### 11. 5 · Plan · el prompt · 0:55 (acumulado 6:13)

El plan. Opus 5.5 recibe la foto y el pedido y hace de diseñador: lee el ambiente, descompone el pedido en piezas y, para cada una, da el kind, que va a ser el filtro, la medida máxima, y la consulta: el producto ideal escrito en las mismas ocho líneas que el catálogo. En los términos de la clase es query expansion con respuesta hipotética, HyDE: en la base no hay preguntas, hay respuestas, así que la consulta se escribe como una respuesta. Más la descomposición del pedido: una consulta por pieza.

▸ paso: El prompt pide leer el cuarto como un diseñador, respetar la pieza nombrada, porque una silla no es un sillón, y no decir lo que no tiene que ser: los embeddings no leen la negación.

▸ paso: Va por la cuarta versión, cada una por un error que vimos. Cuánto suma escribir la ficha lo mide el experimento 2.

### 12. 5 · Plan · lo que devuelve · 0:25 (acumulado 6:38)

Qué devuelve el plan para el living japandi.

▸ paso: 5 piezas, cada una con su kind y un tamaño máximo: el sofá, hasta 240 por 95.

▸ paso: Y la ficha de cada pieza: «tela beige» pasa a «Colors: warm beige»; «bajo», a «low profile». El plan no ve el catálogo: describe el sofá ideal, en el formato de los documentos.

### 13. 6 · Búsqueda · 0:45 (acumulado 7:23)

La búsqueda. Para cada pieza, primero un filtro duro de metadata: el kind del plan y las medidas máximas, con un 15% de margen porque salen de una foto. Para el sofá quedan 76 de los 1.502 productos.

▸ paso: Sobre esos, tres puntajes con la misma ficha: el coseno de Qwen3 con la descripción; BM25, las palabras de la ficha que están en la descripción; y SigLIP 2, la ficha en una frase contra la foto del producto. Cada puntaje se estandariza y se promedian: es la búsqueda híbrida, la versión 2 del sistema.

▸ paso: Quedan los 5 mejores: estos sofás, de los dos catálogos. El que termina en la lista es el 4.º.

### 14. 7 · Elección · 0:40 (acumulado 8:03)

La elección: es la generación de la lista, la G del RAG. Opus 5.5 ve la foto del ambiente y los 5 candidatos de cada pieza, acá 26 imágenes. Solo puede elegir productos que trajo la búsqueda: si no, el código rechaza la respuesta.

▸ paso: El prompt le pide elegir las piezas juntas, como un solo look, juzgando por las fotos, y decir cuántas unidades.

▸ paso: La v2 agregó las cantidades: cero deja una pieza afuera.

▸ paso: No es un reranker: arma un conjunto para este cuarto. Tomó el primero de la búsqueda en 1 de las 5 piezas. Para el sofá eligió el 4.º: era el único realmente beige.

### 15. 8 · Escena · 0:30 (acumulado 8:33)

La escena: el prompt para el modelo de imagen. Probamos dos caminos: que Opus escriba dónde va cada producto, o una plantilla sin LLM, que se completa con la lista.

▸ paso: La última plantilla es estricta: es una edición de la foto del cliente, con la misma cámara, las mismas paredes y ventanas, y exactamente estos productos.

▸ paso: Las comparamos en los 11 ambientes, con las mismas listas: empate, en productos reconocidos y en cuartos conservados. Queda la plantilla, que ahorra una llamada.

### 16. 9 · Imagen · 0:20 (acumulado 8:53)

La imagen: Nano Banana 2, de Gemini, por fal, edita la foto con las fotos de los 5 productos y el prompt. US$0,08 por intento.

▸ paso: Acepta 14 imágenes, así que muestra hasta 13 productos; el resto queda en la lista. El modelo no lo elegimos con un experimento: esa comparación quedó sin correr.

### 17. 10 · Control · 0:40 (acumulado 9:33)

El control. Buscamos puntos característicos de la foto original en la generada, con SIFT, y una homografía con RANSAC. Si se reencuentran al menos 50 y la cámara casi no se movió, es el mismo cuarto; si no, se genera otra, hasta 3 veces. Los umbrales están puestos a mano.

▸ paso: El living del recorrido pasó al primer intento, con 168 puntos.

▸ paso: Este otro pedido, un living clásico, no: el modelo reencuadró hacia la chimenea en los tres intentos, y se entrega el mejor, marcado. En las 11 corridas finales pasan 7, todas al primer intento; en las otras 4 fallaron los tres. El control detecta; reintentar pocas veces arregla.

### 18. 11 · Lista + imagen · 0:20 (acumulado 9:53)

Y la salida: la lista de compra, 5 productos con su id, su medida cuando la hay y la cantidad, cada uno con su porqué. Esta corrida costó US$0,23.

▸ paso: Y la foto de tu cuarto con esos productos. Ese es el recorrido completo.

### 19. Desafíos · 0:50 (acumulado 10:43)

Los desafíos. El más grande fue cambiar la arquitectura que nos aprobaron. La propuesta era generar primero una imagen amoblada, recortar cada mueble y buscar en el catálogo el más parecido, por imagen.

▸ paso: Construimos y medimos su buscador sobre el mismo ground truth: encontraba primero el 43% de los productos anotados, contra 55% buscando por texto. Con eso, y con una generación de imagen menos por pedido, cambiamos a RAG por texto. Ojo: esa versión nunca corrió de punta a punta; comparamos buscadores, no sistemas.

▸ paso: Los otros tres: el catálogo traía fotos de otro producto y hubo que revisarlo a mano; no hay ground truth de la tarea real; y el modelo de imagen rehace el cuarto.


## 02 · Cómo medimos

### 20. Capítulo 02 · Cómo medimos · 0:08 (acumulado 10:51)

Antes de los experimentos, cómo medimos: qué mide cada número y cuánto creerle. Segunda pieza: el sofá.

### 21. Dos bancos de prueba · 0:45 (acumulado 11:36)

Usamos dos bancos de prueba, que miden cosas distintas. Para el buscador, 65 ambientes de IKEA con sus productos anotados. Por cada mueble que se ve, un subagente escribió la consulta como la escribiría el plan, sin ver el catálogo: 864 consultas, 549 con su producto en el catálogo. Es un banco de producto conocido: quien escribe está viendo el mueble, así que mide el índice, no la recomendación.

▸ paso: Para el flujo entero, 11 ambientes vacíos reales, cada uno con su pedido. Ahí no hay ground truth: un juez compara a ciegas las listas de dos configuraciones, en los dos órdenes, y una gana solo si gana en los dos.

▸ paso: Con ground truth medimos el índice; con el juez, la lista.

### 22. Las métricas del buscador, en un ejemplo · 0:50 (acumulado 12:26)

Las métricas del buscador, sobre una sola búsqueda: la alfombra crema de pelo largo de la foto anterior. La búsqueda del flujo ordena las 89 alfombras y la anotada queda 3.ª.

▸ paso: **hit@k**: si el anotado está entre los primeros k. Acá hit@1 da 0, y hit@3 y hit@5 dan 1. El titular es hit@5, porque son los cinco candidatos que ve el que elige: hoy, 0,825. **MRR** es uno sobre el puesto del primer relevante: un tercio.

▸ paso: Las de la clase: **NDCG** y **context precision**, que con uno o dos relevantes por consulta repiten al MRR, con una correlación mayor a 0,99; y **context recall**, que acá es por ambiente: de los productos anotados de la foto, cuántos aparecen en algún top-3.

### 23. Diferencias pareadas · 0:40 (acumulado 13:06)

¿Cuándo una diferencia es una diferencia? Las consultas de un mismo ambiente no son independientes. Y mirar el intervalo de cada método por separado nos había hecho leer mejoras que eran ruido, y al revés.

▸ paso: Por eso comparamos dos métodos sobre las mismas consultas: la diferencia media y su intervalo de 95 por ciento, remuestreando ambientes.

▸ paso: Cuatro ejemplos. Describir cada producto y la búsqueda híbrida: el intervalo no toca el cero, es señal. Qwen3 contra contar palabras: 0,530 contra 0,515 parecía ganar, pero el intervalo cruza el cero. Y el filtro por kind parecía no cambiar nada, y resta en hit@5. Esa es la regla de toda la charla.

### 24. El generador y los jueces · 0:55 (acumulado 14:01)

El generador es el paso que elige y explica. **Faithfulness**: partimos el porqué en afirmaciones, y un juez dice cuáles se infieren de lo que el generador vio. Da 0,88: 313 de 356. Lo que no se sostiene es casi siempre la especie de la madera, que afirma sin verla escrita.

▸ paso: **Answer relevance**: un juez que no ve el pedido escribe los pedidos que esa lista contesta. Da 0,70, contra 0,56 con pedidos escritos para otras listas.

▸ paso: Estas métricas las rehicimos, y es una historia de data leakage: el prompt del juez traía de ejemplo «un living nórdico y cálido», que era justo como empezaba el pedido evaluado, y lo copiaba. Y sobre los jueces: validado contra el ground truth hay uno solo; el de listas se controla con los dos órdenes.

### 25. La imagen: las 11 corridas finales · 0:45 (acumulado 14:46)

La imagen la medimos sobre las 11 corridas de la configuración final, no sobre la mejor. Primero: ¿son esos productos? Detectamos cada mueble, lo recortamos y lo comparamos con las fotos del catálogo de su tipo: reconocido, si el más parecido es el de la lista. En el living del recorrido salen primeros el sofá, la lámpara y la planta; la alfombra y la mesa, no. En total se reconocen 31 de 75, el 41%, aunque aparecen 71.

▸ paso: Segundo: ¿es ese cuarto? El control pasa en 7 de 11, todas al primer intento. O sea: la lista es confiable; la imagen es una visualización.

### 26. Las trampas, dichas en voz alta · 0:40 (acumulado 15:26)

Y las trampas, dichas en voz alta. Uno: el banco de la búsqueda es de producto conocido; en el flujo real el plan imagina el producto, no lo ve. Dos: el mismo modelo escribe las consultas y las descripciones, con el mismo molde; por eso contar palabras rinde casi como el embedder.

▸ paso: Tres: no hay conjunto apartado. Y cuatro: de punta a punta son 11 ambientes, el juez es el mismo modelo que elige, y el ruido solo ya mueve ambientes: la misma configuración corrida dos veces reparte 3 a 3. Por eso leemos las asimetrías grandes, y las diferencias de dos puntos, no.


## 03 · El buscador

### 27. Capítulo 03 · El buscador · 0:08 (acumulado 15:34)

Ahora los experimentos, por cuánto importan. Los que sostienen una decisión tienen su lámina; los de trámite van juntos. Llega el mueble de la tele.

### 28. El mapa de experimentos · 0:45 (acumulado 16:19)

La misma planta, con los experimentos encima: cada llamada es una pregunta que le hicimos a una parte del sistema; arriba el experimento, abajo su lámina. Las llenas, del 1 al 8, tienen lámina propia; las punteadas, del 9 al 15, son las de trámite.

▸ paso: En el indexing: qué catálogo, qué se indexa, y las cuatro de trámite del índice.

▸ paso: En cada pedido: cómo se escribe la consulta, la búsqueda híbrida, con búsqueda o sin búsqueda, y elegir con un modelo que ve.

▸ paso: Dos, el 4 y el 8, no miden una fase: miden al banco de prueba. Y dos cosas no las decidió ningún experimento: el modelo de imagen y los umbrales del control.

### 29. E1 · ¿Texto del vendedor, o describir cada producto? · 0:50 (acumulado 17:09)

Experimento 1: qué se indexa. El texto de IKEA es una frase de marketing, y la gente pide estilo, color y materiales, que están en la foto. ¿Vale la pena describir cada producto?

▸ paso: Indexamos dos textos, con todo lo demás fijo: el texto del vendedor y la descripción de ocho líneas. La consulta, una frase corta sin reescribir, para medir un solo cambio.

▸ paso: Con el texto del vendedor, hit@1 da 0,11; con la descripción, 0,30: casi el triple, y hit@5 pasa de 0,30 a 0,60. La diferencia es pareada y su intervalo no toca el cero. Con la consulta escrita como ficha, la diferencia supera 0,4.

▸ paso: Se indexa la descripción hecha desde la foto. Es el preprocesamiento que más pesa de todo el trabajo.

### 30. E2 · ¿Cuánto suma escribir la consulta como una ficha? · 1:00 (acumulado 18:09)

Experimento 2: cómo se escribe la consulta. El plan no busca con el pedido: escribe el producto ideal en las ocho líneas del catálogo. Es la técnica de Advanced RAG del flujo, y no la habíamos medido contra no hacerla: la comparábamos con buscar solo con el nombre del kind, que es azar por construcción.

▸ paso: La ficha contra la frase natural, sin reescribir: las pocas palabras con que el redactor nombró la pieza. Con la búsqueda del flujo, y también contra la foto del producto.

▸ paso: La ficha da 0,530 y la frase natural 0,324: suma +0,21, con un intervalo lejos del cero. Y lo que no esperábamos: contra la foto, la frase sin reescribir da 0,479, casi lo mismo que la ficha. El texto necesita que la consulta hable como el catálogo; la foto, casi no.

▸ paso: El plan sigue escribiendo la ficha. Y queda un argumento para la búsqueda híbrida: las dos rutas fallan distinto.

### 31. E3 · ¿Suman la búsqueda por palabras y la foto del producto? · 1:00 (acumulado 19:09)

Experimento 3: búsqueda léxica, por foto e híbrida. Dos dudas de fondo sobre el índice. ¿El embedder neuronal hace falta, o alcanza con contar palabras? Y el catálogo tiene fotos: la clase dio dos rutas, pasar la imagen a texto, que es lo que hacíamos, o embeberla directamente. Esa nunca la habíamos medido.

▸ paso: Tres buscadores sobre las mismas consultas: el denso, Qwen3 sobre las descripciones; el léxico, BM25; y por foto, SigLIP 2, con la consulta en una frase contra la foto del producto. Y sus fusiones.

▸ paso: Solos, los tres rinden parecido: 0,530, 0,517 y 0,508. Ni el embedder le gana a contar palabras, ni describir le gana a embeber la foto. Pero se equivocan en cosas distintas: fusionados dan 0,605, +0,075 de hit@1, con un intervalo que no toca el cero.

▸ paso: La búsqueda híbrida pasa a ser la del flujo: es la versión 2, el Ejercicio 4. Usa las dos rutas de la clase a la vez.

### 32. El camino, un cambio por paso · 0:50 (acumulado 19:59)

La ablación incremental: un cambio por paso, con su diferencia pareada. Arrancamos del RAG naive, el texto del vendedor y la consulta sin reescribir: 0,11. Describir cada producto desde su foto lo lleva a 0,30; escribir la consulta como una ficha, a 0,54. Esos dos pasos son los que más pesan. El filtro por kind no suma en este banco: lo usamos por otra razón, que vemos en los de trámite. Con el filtro, esa es la versión 1 del flujo. Con la búsqueda léxica, 0,58; con la foto, 0,60: la versión 2.

Aparte queda el 0,69 que mostrábamos antes: es un VLM reordenando el top-10, una técnica aislada, no un escalón del flujo.

### 33. E4 · Cuando el primero no es el anotado, ¿se equivocó? · 0:40 (acumulado 20:39)

Experimento 4. hit@1 exige el producto anotado exacto, y el catálogo está lleno de variantes del mismo modelo. ¿Cuánto de lo que cuenta como error es el mismo mueble en otro color?

▸ paso: Tres niveles de correcto para el primer candidato: el producto exacto, el mismo modelo, y uno que sirve según un juez.

▸ paso: El exacto, 0,53; el mismo modelo, 0,62; uno que sirve, 0,78. Una de cada 5 veces que el primero falla es otra variante: las mismas mesas en otro color, la misma alfombra en otra medida.

▸ paso: El banco subestima el nivel, no el orden: la comparación entre buscadores no cambia.


## 04 · La lista

### 34. Capítulo 04 · La lista · 0:08 (acumulado 20:47)

Segundo grupo: quién elige, y el flujo entero en cuartos reales, con el juez. Llega la mesa ratona.

### 35. E5 · Elegir con un VLM, y cuántos candidatos · 0:55 (acumulado 21:42)

Experimento 5. hit@10 es 0,89 pero hit@1 0,54: el correcto casi siempre está entre los diez primeros, pero no primero. ¿Mirar las fotos ordena mejor que el coseno? ¿Y cuántos candidatos conviene pasar?

▸ paso: Opus recibe la consulta y las fotos de los diez primeros, y los ordena. De ahí sale gratis la curva: si eligiera entre los primeros k, ¿acertaría? La punteada es el techo.

▸ paso: Reordenando el top-10, hit@1 pasa de 0,535 a 0,687. De 3 a 5 candidatos la elección sube 3 puntos, también significativo; a partir de 8 se aplana.

▸ paso: Cinco candidatos por pieza. Pero ojo: es una técnica aislada, no un paso del flujo. Ese reranker ordena contra la consulta, sin ver el ambiente; el que elige en el flujo arma un conjunto para el cuarto, y no tiene ground truth. Por eso este número no es el del sistema.

### 36. E6 · ¿Qué catálogo: IKEA, Amazon o los dos? · 0:55 (acumulado 22:37)

Experimento 6: qué catálogo. IKEA es de 2013, con una sola estética, la nórdica. Amazon Berkeley Objects tiene publicaciones reales, con medidas, pero no tiene ambientes anotados: hay que medirlo de punta a punta. Los mismos ambientes, pedidos y plan; cambia solo el catálogo, y el juez compara las dos listas a ciegas, en los dos órdenes.

▸ paso: En nuestros cinco departamentos, con pedidos nórdicos, los dos juntos empatan con IKEA. En los seis ambientes públicos, con otros estilos, IKEA más Amazon gana 6 a 0. En total, 8 a 2.

▸ paso: Usamos los dos catálogos. Con dos salvedades: 8 a 2 en once ambientes da p igual a 0,11, no es concluyente; y los pedidos de otros estilos los escribimos nosotros, sabiendo qué le falta a IKEA. Muestra que Amazon cubre ese hueco, no cuán frecuente es.

### 37. E7 · Con búsqueda contra sin búsqueda: los dos extremos · 1:00 (acumulado 23:37)

Experimento 7: con búsqueda contra sin búsqueda. Es el con y sin retrieval del flujo, con dos extremos. Uno: darle al que elige cinco productos al azar del kind pedido. Dos, la pregunta incómoda: si el catálogo entra en el contexto, ¿hacía falta RAG?

▸ paso: Mismo plan, mismo modelo que elige, mismo juez. Contra el azar, en 7 ambientes. Y contra el catálogo entero en el prompt, las 1.502 fichas en texto, en los 11.

▸ paso: Contra el azar, 7 a 0, con los 14 votos. Contra el catálogo entero, 5 a 5, con los mismos productos útiles: empatan.

▸ paso: La búsqueda hace falta cuando el que elige ve cinco productos, y empata cuando puede leerlos todos. Con el catálogo en la caché de prompt cuesta lo mismo; sin caché, diez veces más. Con mil quinientos productos, RAG no hace mejor la lista: lo elegimos porque escala, y porque no depende del tráfico ni de un modelo de contexto largo.


## 05 · De trámite

### 38. Capítulo 05 · De trámite · 0:08 (acumulado 23:45)

Lo que la cátedra dijo que iba a preguntar, con la respuesta corta. Se prende la lámpara.

### 39. E8 · ¿Cuánto cambia el número según quién escribe? · 0:35 (acumulado 24:20)

Experimento 8: tres redactores. Las consultas de evaluación las escribió un modelo. La clase pidió promedio y desvío: ¿cuánto cambia el número sin cambiar el sistema?

▸ paso: Las mismas consultas, escritas otras dos veces por subagentes independientes.

▸ paso: La versión 1 da 0,539 ± 0,025; la versión 2, 0,604 ± 0,009. La mejora de la híbrida se repite con los tres.

▸ paso: El número se mueve unos dos puntos y medio según quién escribe: por eso no leemos diferencias de dos puntos.

### 40. De trámite · el índice · 0:45 (acumulado 25:05)

Los de trámite: lo que la cátedra dijo que iba a preguntar, con la respuesta corta. Embedder: Qwen3 solo se sostiene sobre BGE; contra contar palabras no se distingue, porque consultas y descripciones comparten el molde. Dimensión: con 512 da lo mismo que con 1.024, y con 1.502 productos la memoria no pesa. Splitting: no partimos, un producto es un documento; lo que importa es qué líneas lo componen, y son las de lo que se ve: colores y forma. Base vectorial: ChromaDB da el mismo ranking que la búsqueda exacta en las 864 consultas; la usamos por la persistencia y los filtros.

### 41. De trámite · filtros, rerankers y catálogo · 0:45 (acumulado 25:50)

Filtros de metadata: en este banco no suman, y el de kind cuesta dos puntos de hit@5. Lo usamos igual, por algo que el banco no mide: en los pedidos reales, sin él, el 11% de los candidatos sería de otro kind; pedís un sillón y aparece una silla de comedor. El de medidas cambia pocos candidatos y queda como resguardo. Rerankers de texto: probamos el MiniLM de la clase y Qwen3-Reranker, y los dos empeoran, porque releen el texto que ya usó la búsqueda. La escena: la plantilla y la escrita por el LLM empatan en los once ambientes; queda la plantilla, que ahorra una llamada. Y el catálogo: sumar Amazon le cuesta al buscador 3,5 puntos de hit@5.


## 06 · Ejercicio 4

### 42. Capítulo 06 · Ejercicio 4 · 0:08 (acumulado 25:58)

El Ejercicio 4: versión 1 y versión 2 de la arquitectura. Cortinas y planta.

### 43. Ejercicio 4 · versión 1 y su limitación · 0:50 (acumulado 26:48)

El Ejercicio 4. La versión 1 es el sistema hasta el 11 de noviembre: la búsqueda era el coseno del embedder sobre las descripciones, con el filtro por kind.

▸ paso: Su limitación, medida: entre productos casi iguales, el primero es el anotado el 53% de las veces, y en una de cada 5 piezas el correcto no llega a los cinco candidatos. Falla donde hay muchos parecidos: alfombras y deco.

▸ paso: Un caso: se busca un almohadón blanco con hojas negras, y la versión 1 trae almohadones blancos y negros; el anotado quedó 6.º. El índice lee una descripción, pero no ve el producto ni aprovecha las palabras exactas. Y BM25 y la foto sola rendían como el embedder, fallando en cosas distintas.

### 44. Ejercicio 4 · el cambio y la configuración · 0:40 (acumulado 27:28)

El cambio es una línea de configuración: rag.hybrid pasa de una lista vacía a BM25 y SigLIP 2. La búsqueda ahora calcula tres puntajes para cada producto que pasa el filtro: el coseno con la descripción, que ya estaba; BM25, las palabras; y SigLIP 2, la ficha en una frase contra la foto. Se estandarizan y se promedian.

▸ paso: ¿Por qué este cambio? Sale de una limitación medida; es una técnica de Advanced RAG, búsqueda híbrida y multimodal; y no cuesta nada por pedido, porque corre local.

▸ paso: En el caso del almohadón, ahora el anotado sale primero.

### 45. Ejercicio 4 · resultados en las dos versiones · 1:00 (acumulado 28:28)

Los resultados en las dos versiones. Sobre el ground truth: hit@1 pasa de 0,530 a 0,605, y hit@5, lo que ve el que elige, de 0,790 a 0,825. Las diferencias son pareadas y sus intervalos no tocan el cero; con los otros dos redactores, la mejora se repite. De punta a punta, en los 11 ambientes, con el mismo plan y el juez en los dos órdenes: la versión 2 gana 5, empata 6 y no pierde ninguno. Los productos útiles pasan de 0,68 a 0,74, y el costo es el mismo.

▸ paso: Con honestidad: lo del ground truth es claro; de punta a punta son once ambientes, cinco a cero da p igual a 0,06, y en seis el juez no se decide; y la misma configuración corrida dos veces reparte 3 a 3. Clara en el banco; no peor, probablemente mejor, en la tarea real.


## 07 · Cierre

### 46. Capítulo 07 · Cierre · 0:08 (acumulado 28:36)

Cerramos. El cuarto ya está completo: le faltaban los almohadones.

### 47. El costo · 0:25 (acumulado 29:01)

Costos, del registro de gastos. Un pedido cuesta unos 28 centavos de dólar: 6 el plan, 14 la elección y 8 la imagen. Buscar no cuesta nada: todo corre local.

▸ paso: El trabajo entero costó 45 dólares; lo más caro fue evaluar el reranking con el VLM. Cada llamada paga queda registrada, con topes por cuenta, y lo ya pagado queda en caché.

### 48. Limitaciones · 0:30 (acumulado 29:31)

Limitaciones. Del sistema: no dice «no hay», pone lo más parecido sin avisar; el tamaño no se puede verificar; la imagen es una visualización; y el generador afirma cosas que no ve.

▸ paso: De la evaluación: el banco de la búsqueda es de producto conocido y no hay conjunto apartado; de punta a punta son 11 ambientes, con un juez sin validar contra personas; y el ruido solo ya mueve ambientes.

### 49. Trabajo futuro · 0:35 (acumulado 30:06)

Trabajo futuro. Lo próximo es del RAG y de cómo lo medimos: que el sistema diga «no hay»; un banco de consultas escrito por personas, con un conjunto apartado; validar al juez con nuestro voto a ciegas; más ambientes y más repeticiones. Más lejos: medidas reales del ambiente.

▸ paso: Y fuera del RAG hicimos una prueba: vaciamos un living real y lo volvimos a amoblar con sus muebles. Es un solo cuarto; lo único que se sostiene es que indicarle al modelo dónde va cada mueble ayuda.

### 50. Conclusiones · 0:40 (acumulado 30:46)

Para cerrar. Uno: lo que más pesa es la base de conocimiento y cómo se escribe la consulta; el embedder casi no importa.

▸ paso: Dos: la versión 2 es la búsqueda híbrida: suma en el ground truth, sin costo, y de punta a punta gana 5, empata 6 y no pierde.

▸ paso: Tres: la búsqueda aporta en la tarea real, 7 a 0 contra candidatos al azar; y contra el catálogo entero en el prompt, empata: RAG es lo que escala.

▸ paso: Cuatro: medir bien fue medio trabajo; nos hizo cambiar el número de cabecera y rehacer las métricas del generador.

▸ paso: Y cinco: la lista es confiable; la imagen es una visualización.

### 51. Gracias · 0:10 (acumulado 30:56)

Les dejamos el living del recorrido, amoblado por amoblai. Gracias; ¿preguntas?


## Anexo

### Anexo A · IA responsable

Lámina de respaldo para la discusión del ejercicio 3: riesgos de IA responsable y estrategia de producción. Lo marcado «ya» está implementado en el prototipo.

### Anexo B · La grilla completa

Lámina de respaldo: todas las configuraciones de la grilla (embedder, texto, filtro, dimensión, chunks), por si preguntan por alguna combinación. Las diferencias entre filas vecinas hay que leerlas con la diferencia pareada, no con estos números sueltos.

### Anexo C · Línea de tiempo

Lámina de respaldo: la cronología. El 06/10 arrancamos con la propuesta aprobada, que buscaba por imagen; medimos su buscador y el 21/10 pasamos a RAG por texto.

▸ paso: Después vinieron la elección con un VLM, un catálogo más grande y las métricas de la clase.

▸ paso: En noviembre revisamos el catálogo a mano, sumamos un segundo catálogo y, el 12/11, la revisión crítica: de ahí sale la versión 2.

### Anexo D · La planilla de alternativas

Lámina de respaldo: las alternativas de cada decisión, la que quedó y el experimento que la midió. Del E9 al E15 son los de trámite: el experimento no siempre sostiene la elección (el embedder y el filtro quedan por otra razón). En la charla, esto lo cuenta el mapa de experimentos.

# Guion · amoblai

TP 3 · 73.69 Large Language Models · ITBA 2026 · Juan Bautista Albertoni Salini, Matias Juan Rossi Seifert, Junior Rambau

Presentación: `presentacion.html` (47 láminas + 2 de anexo). Duración estimada: **30:00**. «▸ paso» marca dónde se aprieta → para mostrar lo siguiente de la lámina. Las notas también se ven en la presentación con la tecla N.

| # | Lámina | Tiempo | Acumulado |
|---|---|---|---|
| 1 | Portada | 0:25 | 0:25 |
| 2 | El problema | 0:45 | 1:10 |
| 3 | Qué hace amoblai | 1:00 | 2:10 |
| 4 | Lo que tiene que cumplir | 0:30 | 2:40 |
| 5 | Capítulo 01 · Arquitectura | 0:10 | 2:50 |
| 6 | Indexing | 0:40 | 3:30 |
| 7 | Por pedido | 1:10 | 4:40 |
| 8 | Documento y consulta | 0:45 | 5:25 |
| 9 | Variantes | 0:30 | 5:55 |
| 10 | Línea de tiempo | 0:30 | 6:25 |
| 11 | Capítulo 02 · Cómo medimos | 0:10 | 6:35 |
| 12 | Ground truth | 0:45 | 7:20 |
| 13 | Las métricas, en un ejemplo | 1:10 | 8:30 |
| 14 | Intervalos de confianza | 0:40 | 9:10 |
| 15 | Capítulo 03 · Qué guardamos | 0:10 | 9:20 |
| 16 | E1 · ¿Buscamos los muebles por imagen o por texto? | 1:00 | 10:20 |
| 17 | E2 · ¿Qué texto indexamos, con qué embedder y qué filtro? | 1:05 | 11:25 |
| 18 | E3 · ¿Partimos cada descripción en chunks? | 0:35 | 12:00 |
| 19 | E4 · ¿Cuántas dimensiones necesita el embedding? | 0:40 | 12:40 |
| 20 | E5 · ¿La base vectorial se pierde resultados? | 0:30 | 13:10 |
| 21 | Capítulo 04 · Cómo buscamos | 0:10 | 13:20 |
| 22 | E6 · ¿Hace falta que el LLM reescriba la consulta? | 0:45 | 14:05 |
| 23 | E7 · ¿Conviene reordenar los candidatos mirando las fotos? | 0:55 | 15:00 |
| 24 | E7 · Dónde ayuda | 0:45 | 15:45 |
| 25 | E8 · ¿Cuántos candidatos le mostramos a choose? | 0:45 | 16:30 |
| 26 | Capítulo 05 · Cuánto creerle | 0:10 | 16:40 |
| 27 | E9 · Si otro escribe las consultas, ¿cambia el resultado? | 0:45 | 17:25 |
| 28 | E10 · ¿Sirve lo que trae, aunque no sea el producto exacto? | 0:45 | 18:10 |
| 29 | E11 · ¿La respuesta inventa, o responde lo que se pidió? | 0:50 | 19:00 |
| 30 | Capítulo 06 · De punta a punta | 0:10 | 19:10 |
| 31 | E12 · Qué catálogo (diseño) | 0:50 | 20:00 |
| 32 | E12 · Resultados | 0:55 | 20:55 |
| 33 | E12 · Un caso | 0:20 | 21:15 |
| 34 | E13 · Métricas de imagen | 0:40 | 21:55 |
| 35 | E13 · ¿Cómo pedimos la imagen para que no cambie el cuarto? | 1:00 | 22:55 |
| 36 | E13 · El control en acción | 0:30 | 23:25 |
| 37 | E14 · ¿Reproduce un living real si le damos sus muebles? | 1:10 | 24:35 |
| 38 | T4 · Lo que sigue | 0:20 | 24:55 |
| 39 | Capítulo 07 · Cierre | 0:10 | 25:05 |
| 40 | Lo que decidimos | 0:25 | 25:30 |
| 41 | El camino | 0:25 | 25:55 |
| 42 | Costos | 0:25 | 26:20 |
| 43 | Aprendizajes y límites | 0:55 | 27:15 |
| 44 | Futuro · cajas en la foto | 0:45 | 28:00 |
| 45 | Futuro · cuánto ayudan las cajas | 0:45 | 28:45 |
| 46 | Futuro · con medidas reales | 1:00 | 29:45 |
| 47 | Gracias | 0:15 | 30:00 |


## 00 · El producto

### 1. Portada · 0:25 (acumulado 0:25)

Buenas. Somos Juan Bautista, Matías y Junior, y esto es **amoblai**.

La idea es simple de decir: le das una foto de tu ambiente vacío, como este living dibujado, y le contás qué querés. amoblai te devuelve una lista de muebles reales de un catálogo y la foto de tu cuarto amoblado con ellos.

En la próxima media hora les contamos qué hace, cómo está armado y, sobre todo, cómo lo medimos: cada decisión salió de un experimento. Y este cuarto vacío se va a ir amoblando a medida que avanzamos.

### 2. El problema · 0:45 (acumulado 1:10)

Arranquemos por el problema. Te mudás, tenés el ambiente vacío y una idea de lo que querés. Hoy hay dos caminos y ninguno alcanza.

Un generador de imágenes te amobla la foto, pero con muebles inventados: son estas cajas punteadas con signos de pregunta. No los podés medir ni comprar.

▸ paso: Un catálogo tiene productos reales, pero no mira tu cuarto: filtrás por tipo, color, precio, y combinar ocho cosas que vayan entre sí y con tu piso lo hacés vos.

▸ paso: Nosotros queremos las dos cosas a la vez. Y eso, en el fondo, es un problema de RAG: la respuesta tiene que salir de lo que recuperamos del catálogo, no de la imaginación del modelo.

### 3. Qué hace amoblai · 1:00 (acumulado 2:10)

Así se usa. El usuario sube la foto del ambiente y escribe el pedido como le sale: «un living moderno y luminoso para recibir amigos, un sofá de tres cuerpos gris claro contra la pared de la izquierda, una mesa ratona de madera clara, una alfombra grande…».

▸ paso: amoblai devuelve la lista: 8 productos reales del catálogo, con cantidades (los almohadones van por dos) y medidas cuando el catálogo las tiene. Cada uno viene con su porqué. Un detalle que vamos a retomar: en 5 de las 8 piezas eligió un producto que no era el más parecido por coseno.

▸ paso: Y la imagen: el mismo cuarto, con esos productos. Esta corrida costó US$0,41, con 3 intentos de imagen. Por qué hubo 3 lo vemos al final.

### 4. Lo que tiene que cumplir · 0:30 (acumulado 2:40)

Antes de entrar en la arquitectura, lo que amoblai promete, porque de acá salen las métricas. Es el programa, como en un proyecto de arquitectura.

Que los productos sean los que van: eso es retrieval y se mide contra un ground truth, con las métricas de ranking de la materia. Que si el exacto no está, traiga algo que sirva. Que cada número se pueda creer. Que el porqué no invente y que la respuesta conteste lo que se pidió: ahí entran RAGAS y un juez. Y que la imagen sea tu cuarto y no otro. La columna de la derecha dice qué experimento mide cada cosa.


## 01 · Arquitectura

### 5. Capítulo 01 · Arquitectura · 0:10 (acumulado 2:50)

Entonces: ¿cómo está armado? Primera pieza del cuarto: la alfombra, la base sobre la que se apoya todo.

### 6. Indexing · 0:40 (acumulado 3:30)

La arquitectura tiene dos tiempos. El primero pasa una sola vez, offline: el indexing. El catálogo son 819 productos de IKEA más 683 de Amazon Berkeley Objects, cada uno con su foto, su tipo, su kind y sus medidas cuando las tiene.

▸ paso: Un modelo de visión mira la foto de cada producto y escribe una descripción en ocho líneas fijas: tipo, uso, estilo, materiales, colores, forma, sensación y con qué combina. Un producto, un documento.

▸ paso: Esa descripción se embebe con Qwen3-Embedding-0.6B, que corre local: 1024 números por producto.

▸ paso: Y va a ChromaDB junto con la metadata. Lo importante: lo que después buscamos no son fotos, son descripciones.

### 7. Por pedido · 1:10 (acumulado 4:40)

El segundo tiempo pasa en cada pedido, y lo vamos a ver como capas sobre el cuarto. Primero, **plan**, con Claude Opus 5.5: mira la foto y el pedido y decide qué piezas hacen falta, el kind de cada una y su tamaño máximo; son estas cajas punteadas. Y escribe el producto ideal de cada pieza en las mismas ocho líneas del catálogo. Es query rewriting.

▸ paso: **retrieve** aplica esos filtros como where de Chroma y trae los k más cercanos por coseno: acá, los cinco candidatos de algunas piezas.

▸ paso: **choose**, otra vez Opus, mira las fotos de los candidatos de cada pieza y elige la combinación y las cantidades. Es un reranking después del retrieval, hecho por un modelo que ve. Las cajas se vuelven muebles.

▸ paso: Y la imagen: un prompt de edición estricta, Nano Banana 2 edita la foto, y un control con SIFT verifica que siga siendo el mismo cuarto; si no, se reintenta, hasta 3 veces.

### 8. Documento y consulta · 0:45 (acumulado 5:25)

Esto es el corazón del retrieval. A la izquierda, el documento de un sofá del catálogo: lo escribió un modelo mirando su foto, en las ocho líneas.

▸ paso: A la derecha, la consulta que escribió plan para el living de recién, sin ver el catálogo. Mismo formato, mismo vocabulario: «light grey», «Scandinavian», «white walls». La idea es que documento y consulta se parezcan como dos fichas del mismo catálogo, y se comparan por coseno.

▸ paso: Abajo, los cinco más cercanos. El sofá que terminó en la lista salió 2.º, con 0,852, muy cerca del primero. Choose lo eligió igual, porque mirando las fotos es el gris claro de brazos anchos que pidió el usuario.

### 9. Variantes · 0:30 (acumulado 5:55)

Cada caja del diagrama tuvo alternativas. Esta planilla es el mapa de la charla: cada fila es una decisión, y a la derecha está el experimento que la resolvió.

La mayoría son hiperparámetros del retrieval, que es lo que se puede medir contra un ground truth. Lo de borde gris es de la v0, que buscaba por imagen. Y la última fila, el modelo de imagen, quedó diseñada pero sin correr. Al final volvemos a esta planilla con lo que elegimos.

### 10. Línea de tiempo · 0:30 (acumulado 6:25)

Y así se fue transformando. El 06/10 arrancamos con una v0 que buscaba por imagen. El 21/10 pasamos a texto, que es la arquitectura que acaban de ver; el primer experimento explica por qué.

▸ paso: Después vinieron el reranking con Opus y un catálogo más grande, las métricas de RAGAS y la reproducibilidad, y el control de la imagen.

▸ paso: En noviembre revisamos el catálogo a mano y sumamos un segundo catálogo, el 10/11. Lo que sigue son los experimentos de imagen, que están diseñados.


## 02 · Cómo medimos

### 11. Capítulo 02 · Cómo medimos · 0:10 (acumulado 6:35)

Antes de los experimentos, cómo medimos. Esto vale para todo lo que sigue. Segunda pieza: el sofá.

### 12. Ground truth · 0:45 (acumulado 7:20)

Para medir el retrieval hacen falta respuestas correctas. El dataset de IKEA de Tautkute y otros trae fotos de ambientes armados y, para cada foto, qué productos del catálogo aparecen. Esta es una, con sus 14 productos anotados.

▸ paso: Usamos los 65 livings y comedores. Para cada foto, subagentes de Claude escribieron una consulta por pieza que se ve, en las ocho líneas, como lo haría plan y sin ver el catálogo ni las anotaciones. Son 864 búsquedas; 549 tienen su producto en el catálogo, y sobre esas se mide. Una búsqueda acierta si trae el producto anotado de esa pieza. De referencia: elegir al azar entre lo que deja pasar el filtro acierta el primero en el 1,7% de los casos.

### 13. Las métricas, en un ejemplo · 1:10 (acumulado 8:30)

Las métricas, sobre una sola búsqueda: la alfombra crema de pelo largo de la foto anterior. El retrieval ordena las 89 alfombras del catálogo y el producto anotado queda 4.º.

▸ paso: **hit@k** pregunta si el anotado está entre los primeros k: acá hit@1 y hit@3 dan 0 y hit@5 da 1. Promediado sobre todas las búsquedas es una proporción de aciertos, y es la métrica que más vamos a usar. **MRR** es uno sobre el puesto del primer relevante: 1/4, 0,25. Premia que esté arriba aunque no sea primero.

▸ paso: **NDCG** descuenta la ganancia por el logaritmo del puesto y la normaliza por el orden ideal: 0,431. **Context precision** de RAGAS promedia la precisión en cada puesto donde hay un relevante; con un solo relevante coincide con MRR. En las 32 configuraciones que corrimos, MRR y context precision correlacionan 0,9999: miden casi lo mismo.

▸ paso: **Context recall**, también de RAGAS, se mira por ambiente: de los productos anotados de la foto, cuántos aparecen en el top-3 de alguna de sus búsquedas. Acá, 9 de 12.

### 14. Intervalos de confianza · 0:40 (acumulado 9:10)

Cada número de la charla va con un intervalo de confianza del 95%, por bootstrap. Pero ojo: las búsquedas de un mismo ambiente no son independientes, comparten la foto y el estilo.

▸ paso: Entonces remuestreamos ambientes, no búsquedas: sorteamos 64 ambientes con reposición, recalculamos el hit@1, y lo repetimos 1000 veces. El histograma son esas medias; el intervalo va de 0,491 a 0,577.

▸ paso: Y la regla que usamos en toda la charla: si dos intervalos se pisan, no decimos que una variante le gana a la otra.


## 03 · Qué guardamos

### 15. Capítulo 03 · Qué guardamos · 0:10 (acumulado 9:20)

Primer capítulo de experimentos: qué guardamos en el índice. Cinco decisiones del indexing. Y al cuarto se le suma el mueble de la tele.

### 16. E1 · ¿Buscamos los muebles por imagen o por texto? · 1:00 (acumulado 10:20)

Primer experimento, y el que cambió todo: ¿buscamos por imagen o por texto?

La v0 buscaba por imagen: detectaba cada mueble en la foto, lo recortaba y lo comparaba con las fotos del catálogo. Es lo natural si la pregunta es «encontrá este mueble». Pero en amoblai el ambiente está vacío: no hay nada que recortar, hay un pedido.

▸ paso: Para comparar en serio usamos el mismo ground truth y el mismo catálogo que vio la v0, 275 productos. Por imagen, seis pasos acumulados, de CLIP a DINOv3, sobre 325 recortes. Por texto, las descripciones con Qwen3, sobre 207 búsquedas.

▸ paso: La imagen mejoró mucho con cada paso: de 0,126 a 0,508. Pero el texto llega a 0,618, con intervalos que apenas se tocan.

▸ paso: Decidimos texto. Gana, y además es lo único que funciona con el caso real: un cuarto vacío y un pedido escrito.

### 17. E2 · ¿Qué texto indexamos, con qué embedder y qué filtro? · 1:05 (acumulado 11:25)

Ya en texto: ¿qué texto ponemos de cada producto, con qué embedder y con qué filtro?

El catálogo trae el texto del vendedor: el nombre y una frase de marketing. Nuestra hipótesis era que describir cada producto en las mismas ocho líneas que la consulta iba a hacer que se encuentren. Y queríamos saber cuánto aporta un embedder neuronal frente a contar palabras, y si filtrar por metadata ayuda.

▸ paso: Corrimos la grilla completa: dos textos, tres embedders (desde contar palabras hasta Qwen3) y tres filtros: ninguno, el tipo grueso (sofá, mesa) o el kind fino (mesa ratona, mesa auxiliar).

▸ paso: La lectura es por filas. Con el texto del vendedor, nada pasa de 0,189. Con nuestras descripciones, todo salta a más de 0,47. El embedder suma menos: Qwen3 es el mejor, pero el hashing queda cerca. Y poner el nombre comercial adelante empeora: agrega palabras que la consulta no tiene.

▸ paso: Decidimos descripciones con Qwen3. Los filtros, con descripciones, casi no cambian nada, porque la línea Type ya dice qué es cada cosa. El flujo filtra por el kind que decide el plan; type, kind o ninguno quedan dentro del intervalo.

### 18. E3 · ¿Partimos cada descripción en chunks? · 0:35 (acumulado 12:00)

Splitting. La receta de RAG dice partir los documentos en chunks, pero nuestra descripción ya es corta. ¿Conviene igual comparar por partes?

▸ paso: Probamos tres formas: el documento entero, cada línea como chunk, y línea contra línea del mismo rótulo, colores con colores.

▸ paso: Partir en líneas sueltas se cae a 0,273: una línea sola no dice de qué producto habla. Alinear por rótulo casi empata.

▸ paso: Nos quedamos con un documento por producto: igual de bueno y ocho veces más simple.

### 19. E4 · ¿Cuántas dimensiones necesita el embedding? · 0:40 (acumulado 12:40)

Dimensión del embedding. Qwen3 se entrenó con Matryoshka: las primeras componentes del vector ya son un embedding válido, y uno más chico es más barato de guardar y de buscar.

▸ paso: Truncamos a 32, 64, hasta 1024, y renormalizamos. Sin reentrenar.

▸ paso: Con 32 componentes ya da 0,428; desde 512 la curva se aplana (0,532 contra 0,535).

▸ paso: Nos quedamos con las 1024: todo el catálogo ocupa 6,2 megas. Con un catálogo de millones, elegiríamos 256 o 512.

### 20. E5 · ¿La base vectorial se pierde resultados? · 0:30 (acumulado 13:10)

La base vectorial. ChromaDB usa HNSW, una búsqueda aproximada sobre un grafo de vecinos. ¿Se le escapa el correcto?

▸ paso: Corrimos todas las búsquedas con HNSW y con búsqueda exacta, y comparamos el ranking entero.

▸ paso: Idénticos en las 864. Con este tamaño de catálogo, aproximado es exacto.

▸ paso: Nos quedamos con Chroma por todo lo demás que trae: filtros, persistencia, el texto al lado del vector.


## 04 · Cómo buscamos

### 21. Capítulo 04 · Cómo buscamos · 0:10 (acumulado 13:20)

Segundo capítulo: lo que pasa en cada pedido, antes y después de buscar. Llega la mesa ratona.

### 22. E6 · ¿Hace falta que el LLM reescriba la consulta? · 0:45 (acumulado 14:05)

Query rewriting. Plan podría buscar la palabra «alfombra» y listo. En cambio escribe el producto ideal en las ocho líneas, como un documento hipotético del catálogo, que es la idea de HyDE. Cuesta una llamada a Opus por pedido: ¿vale la pena?

▸ paso: Misma búsqueda con tres consultas: las ocho líneas, solo la línea Type, o solo el nombre del kind.

▸ paso: Con el nombre solo, 0,064, apenas arriba del azar. Con la línea Type, 0,293. Con las ocho líneas, 0,535.

▸ paso: Es la decisión que más pesa de todo el retrieval. Los colores, la forma y el estilo son lo que distingue una alfombra de otras ochenta.

### 23. E7 · ¿Conviene reordenar los candidatos mirando las fotos? · 0:55 (acumulado 15:00)

Reranking. El embedding compara textos, pero dos alfombras crema de pelo largo se describen casi igual y se distinguen mirando. La idea es que un modelo que ve reordene los primeros diez.

▸ paso: Probamos dos: un cross-encoder de texto, gratis, que lee consulta y descripción juntas; y Opus mirando las fotos, a unos US$0,02 por búsqueda.

▸ paso: El cross-encoder empeora: 0,419. Está entrenado en búsqueda web y no aporta nada que el embedding no tenga. Opus sube de 0,535 a 0,687, con intervalos que no se tocan: es la mejora más grande después del query rewriting.

### 24. E7 · Dónde ayuda · 0:45 (acumulado 15:45)

Dónde ayuda. Por categoría, el salto es mayor donde los productos se parecen entre sí: alfombras, de 0,31 a 0,60, estantes, deco, lámparas. Donde el texto ya alcanzaba, como sillas, sube menos.

A la derecha, la búsqueda de la alfombra que usamos para explicar las métricas: Qwen3 la dejó 4.ª; Opus, mirando, la sube a la 1.ª.

▸ paso: Decisión: reordenar con un modelo que ve. En el flujo, ese reranker es el paso choose: el mismo Opus, que además elige la combinación entera.

### 25. E8 · ¿Cuántos candidatos le mostramos a choose? · 0:45 (acumulado 16:30)

¿Cuántos candidatos le mostramos a choose? Más candidatos, más chance de que esté el correcto, pero más fotos por llamada: más costo, más latencia y más con qué confundirse.

▸ paso: No hizo falta gastar de nuevo: del reranking de Opus sobre el top-10 sale qué elegiría entre los primeros k. Lo comparamos con el techo, que el correcto esté entre los k.

▸ paso: El techo sube rápido, pero el acierto real se aplana: de 3 a 5 candidatos suma 0,029; de 5 a 8, 0,022.

▸ paso: Pasamos de 3 a 5. Más allá, el costo crece más que el acierto.


## 05 · Cuánto creerle

### 26. Capítulo 05 · Cuánto creerle · 0:10 (acumulado 16:40)

Tercer capítulo: cuánto creerle a todo esto. Se prende la lámpara.

### 27. E9 · Si otro escribe las consultas, ¿cambia el resultado? · 0:45 (acumulado 17:25)

Reproducibilidad. Las consultas las escribieron subagentes de Claude; otro redactor escribiría otras. Si el ranking de métodos depende de una redacción, no vale.

▸ paso: Hicimos escribir todas las consultas tres veces, de forma independiente, y corrimos cinco métodos en cada escritura.

▸ paso: El mejor método da 0,544 más menos 0,026. El orden se mantiene en las tres: Qwen3 con filtro por tipo arriba, el texto del vendedor abajo de todo.

▸ paso: Conclusión: el orden es firme, pero diferencias de dos o tres centésimas entre métodos son ruido de redacción. Por eso varias «mejoras» las tratamos como empate.

### 28. E10 · ¿Sirve lo que trae, aunque no sea el producto exacto? · 0:45 (acumulado 18:10)

Relevancia graduada. hit@k solo cuenta el producto exacto; si el sofá anotado no está, uno muy parecido le sirve igual al usuario. Y más de un tercio de las búsquedas no tiene su producto en el catálogo.

▸ paso: Un juez LLM mira la foto del ambiente y los tres primeros, sin saber cuál es el anotado, y les pone 2, 1 o 0. Son 150 búsquedas al azar: 75 con el producto en el catálogo y 75 sin. Esto es el context precision de RAGAS en su versión sin ground truth, y el NDCG graduado de la clase.

▸ paso: El primero sirve en el 75% de los casos, contra un hit@1 exacto de 0,53. Y sin el producto en el catálogo, igual en el 63%. Validamos al juez: le pone 2 al anotado en el 81% y a los demás en el 5%.

▸ paso: hit@1 es una cota inferior de lo útil. Usamos el juez como complemento, validado contra las anotaciones.

### 29. E11 · ¿La respuesta inventa, o responde lo que se pidió? · 0:50 (acumulado 19:00)

RAGAS sobre la respuesta. Choose explica cada elección; si afirma una medida o un material falso, es una alucinación que el usuario se va a creer. Y la lista entera tiene que contestar el pedido, no solo cada pieza.

▸ paso: Medimos dos cosas con un juez. Faithfulness: se parte la explicación en afirmaciones y se cuenta qué fracción se sostiene con lo que vio el sistema. Answer relevance: el juez, sin ver el pedido, escribe tres pedidos que esa respuesta contestaría, y medimos el coseno con el original. La vara es el mismo coseno contra pedidos que no tienen nada que ver.

▸ paso: Faithfulness entre 0,89 y 0,97; answer relevance muy por encima de la vara. Lo interesante es qué no se sostiene: que el piso es de roble, que la alfombra llega abajo del sofá. Son medidas y cosas que el catálogo no dice.

▸ paso: El modelo no inventa productos; lo que le falta es información. Los asientos de IKEA no tienen medidas en el dataset, y eso nos llevó al último capítulo: otro catálogo.


## 06 · De punta a punta

### 30. Capítulo 06 · De punta a punta · 0:10 (acumulado 19:10)

Último capítulo de experimentos: de punta a punta, en ambientes vacíos reales. Cortinas y planta.

### 31. E12 · Qué catálogo (diseño) · 0:50 (acumulado 20:00)

¿Alcanza con IKEA? El catálogo del dataset es de un solo estilo, y sus asientos no tienen medidas: ninguno. E11 nos mostró que lo que falla son justamente medidas. Amazon Berkeley Objects son publicaciones reales de Amazon, de muchos estilos y casi todas con medidas. Describimos 683 productos con las mismas ocho líneas.

▸ paso: Acá no hay ground truth, así que lo medimos de punta a punta: 11 ambientes vacíos reales, cinco nuestros con pedidos nórdicos y seis fotos públicas con pedidos de otros estilos. Corremos el flujo con cada catálogo y un juez compara las dos listas. Como los LLM tienden a preferir la primera opción, se pregunta en los dos órdenes, y una lista gana solo si gana en los dos. Medimos también el sesgo de posición y el acuerdo entre órdenes.

### 32. E12 · Resultados · 0:55 (acumulado 20:55)

Los resultados. Cada columna es un ambiente: los cinco primeros son departamentos propios, los seis siguientes fotos públicas.

▸ paso: Con los dos votos del juez: en los propios, con pedidos nórdicos, IKEA solo e IKEA más ABO empatan: 2 a 2 con un empate. En las seis fotos públicas, con pedidos industrial, clásico, bohemio, gana IKEA más ABO 6 a 0, y la fracción de productos que cumplen sube de 0,46 a 0,71. Además, ABO solo pierde contra IKEA en los cuartos nórdicos, y sumar ABO como distractor casi no cambia el retrieval sobre el ground truth de IKEA. El juez coincide consigo mismo en los dos órdenes en el 91% de los casos.

▸ paso: Decisión: el flujo usa los dos catálogos. Lo que no cambia: las métricas con ground truth se siguen calculando solo sobre IKEA.

### 33. E12 · Un caso · 0:20 (acumulado 21:15)

Un caso para ver qué está mirando el juez: un loft con vigas y un pedido industrial, sofá de cuero envejecido, mesa de madera con patas de metal negro, biblioteca de metal y madera.

IKEA solo no tiene esos productos y propone lo más cercano: un sofá de cuero liso, una mesa toda de madera, un estante de vidrio. Con ABO aparecen el sofá de cuero coñac, la mesa industrial y la biblioteca. Las barritas son la nota del juez a cada producto, en cada orden.

### 34. E13 · Métricas de imagen · 0:40 (acumulado 21:55)

Para la imagen no hay ground truth, así que armamos métricas que comparan contra lo que sí tenemos: la foto original y las fotos del catálogo.

**SSIM** fuera de los muebles: la similitud estructural, luz, contraste y textura por ventanas, entre la foto original y la generada, solo donde no hay muebles. Si da cerca de uno, el cuarto se preservó.

▸ paso: **SIFT con RANSAC**: buscamos puntos característicos de la foto original en la generada. Si la cámara se movió o el cuarto cambió, se reencuentran pocos y se desplazan. Con esto armamos el control automático: al menos 50 inliers y un desplazamiento de a lo sumo el 1% del ancho.

▸ paso: **Fidelidad de producto**: detectamos cada mueble, recortamos y vemos si el más parecido del catálogo es el de la lista. Como vara, con fotos reales de IKEA esto da 0,444: es difícil incluso con fotos de verdad.

▸ paso: Y SigLIP 2 para ver si la imagen se alinea con el pedido. Todas corren local y gratis.

### 35. E13 · ¿Cómo pedimos la imagen para que no cambie el cuarto? · 1:00 (acumulado 22:55)

La imagen. El modelo tiende a «mejorar» la foto: mueve la cámara, agranda ventanas, repinta. Para el usuario es grave, porque compraría para un cuarto que no es el suyo.

▸ paso: Probamos distintas formas de pedir la edición, siempre con la misma foto y la misma lista: que Claude escriba la escena, un template de edición libre, y uno de edición estricta. Ojo: una imagen por variante.

▸ paso: Con el pedido corto, las dos primeras preservan el cuarto parecido. Con el pedido detallado y 9 productos, la edición libre lo cambió: el SSIM fuera de los muebles cae a 0,29 y SIFT ve la cámara movida. La estricta lo preserva.

▸ paso: Elegimos edición estricta, sin LLM: más barata y más fiel. Pero una imagen por variante es una anécdota, así que además pusimos un control automático en cada corrida.

### 36. E13 · El control en acción · 0:30 (acumulado 23:25)

Y acá el control en una corrida real: el living de la portada. Los dos primeros intentos cambiaron el cuarto, la cámara se movió, y SIFT reencontró menos del 5% de los puntos con desplazamientos de más del 15%. Se rechazaron solos. El tercero preservó el cuarto y se aceptó. Por eso esa corrida tuvo tres intentos.

▸ paso: El control queda en el flujo, con hasta 3 intentos. Dónde poner el umbral exacto es lo que sigue.

### 37. E14 · ¿Reproduce un living real si le damos sus muebles? · 1:10 (acumulado 24:35)

Un experimento más sobre la imagen, que se nos ocurrió mirando el ground truth. En los ambientes vacíos no tenemos con qué comparar la imagen: nadie sabe cómo debería quedar. Pero un living del ground truth sí lo tiene: la foto real, y la lista de sus productos. Queríamos medir el generador solo, con la lista ya decidida, sin el retrieval en el medio.

▸ paso: Tomamos la foto real y la vaciamos con el mismo modelo de imagen. Hicieron falta 2 intentos: el primero abrió el encuadre y dejó una lámpara; el segundo conserva la puerta, las cortinas, la ventana y el piso. Después la volvimos a amoblar con sus 6 muebles anotados, con el paso de imagen del flujo tal cual, 3 veces. Y comparamos con la foto real: dónde quedó cada mueble, como IoU entre su caja y la de la foto real, y si es el producto, con el coseno de DINOv3. Es una sola habitación: es una prueba, no una medición.

▸ paso: Los 6 productos aparecen en todas, y se reconocen: coseno 0,63. Pero cada vez arma su propio living: el sofá a la izquierda, la estantería a la derecha. El IoU medio con las cajas reales es 0,20: en promedio, 1,0 de 6 muebles quedan en su lugar.

▸ paso: La conclusión: el generador respeta los productos, no la distribución. Y no es un error: el pedido no dice dónde va cada cosa. Si queremos controlar dónde, hay que decírselo. Eso es lo que probamos al final, como paso a futuro.

### 38. T4 · Lo que sigue · 0:20 (acumulado 24:55)

Lo que sigue, y lo decimos claro: esto está diseñado y no corrido, no hay resultados.

La imagen la medimos con una imagen por variante. El plan es repetirlo bien, en todos los ambientes: escena escrita por el LLM contra edición estricta, qué modelo de imagen, qué resolución, si las fotos del catálogo cambian la fidelidad, y calibrar el umbral del control SIFT con todos esos intentos. Con las métricas de E13 y un juez de a pares en los dos órdenes, como en E12. Cuesta unos US$10 de fal más unos US$5 de Claude.


## 07 · Cierre

### 39. Capítulo 07 · Cierre · 0:10 (acumulado 25:05)

Cerramos. El cuarto ya está completo: le faltaban los almohadones.

### 40. Lo que decidimos · 0:25 (acumulado 25:30)

Volvemos a la planilla del principio, ahora con lo que elegimos en cada fila y el experimento que lo decidió.

Descripciones de ocho líneas, Qwen3 entero, Chroma, un documento por producto; la consulta reescrita en ocho líneas; un modelo que ve para elegir entre cinco; los dos catálogos; y edición estricta con control SIFT. El modelo de imagen es el único que quedó sin medir.

### 41. El camino · 0:25 (acumulado 25:55)

El camino de los números. El punto de partida ingenuo, texto del vendedor y contar palabras, da 0,076. Escribir nuestras descripciones lo lleva a 0,495: el salto más grande lo dio qué texto guardamos, no el modelo. Qwen3, filtro y Chroma suman poco más, hasta 0,535. Y un modelo que mira las fotos al final lo lleva a 0,687.

### 42. Costos · 0:25 (acumulado 26:20)

Lo que cuesta. Una corrida del flujo, unos US$0,29: plan, choose, que es lo más caro porque mira fotos, y la imagen, más US$0,08 por cada reintento.

▸ paso: En todo el trabajo gastamos US$25,60 registrados, y lo que más se llevó fue evaluar: el reranking con Opus sobre todas las búsquedas. Todo lo demás, el retrieval, los embeddings y las métricas de imagen, corre local y gratis.

### 43. Aprendizajes y límites · 0:55 (acumulado 27:15)

Cuatro cosas que aprendimos. Uno: lo que más pesó fue qué texto guardamos y cómo escribimos la consulta, más que el modelo de embeddings. Dos: un modelo que ve, al final, vale más que cualquier ajuste fino del retrieval. Tres: medir con intervalos y repetir nos salvó de declarar ganadoras a varias cosas que eran ruido. Cuatro: las métricas sin ground truth encontraron problemas que hit@k no veía, como las medidas que faltan.

▸ paso: Y los límites, con honestidad: la imagen se midió con muy pocas imágenes; ABO solo tiene evaluación con juez; los jueces son Claude evaluando a Claude, validados contra las anotaciones pero no contra personas; y los asientos de IKEA siguen sin medidas.


## Pasos a futuro

### 44. Futuro · cajas en la foto · 0:45 (acumulado 28:00)

Para terminar, hacia dónde iría el producto. E14 mostró que el generador pone los productos pero decide él dónde. La idea: dibujar en la foto vacía una caja por mueble, donde tiene que ir y cuánto ocupa, y pedirle que cada mueble llene su caja. A la izquierda, las tres réplicas sin cajas de recién.

▸ paso: Primero con cajas planas, rectángulos, en el lugar exacto de cada mueble en la foto real: 3 imágenes.

▸ paso: Y con cajas 3D: un prisma por mueble, apoyado en el piso, que además dice para dónde está girado y cuánto ocupa hacia el fondo.

### 45. Futuro · cuánto ayudan las cajas · 0:45 (acumulado 28:45)

Los números. Con cajas planas, el IoU medio sube de 0,20 a 0,40, y los muebles en su lugar de 1,0 a 2,7. El producto se sigue reconociendo igual. Y un problema: en 2 de las 3 imágenes el modelo dejó las cajas dibujadas, y hasta las movió.

▸ paso: Por mueble se ve dónde funciona: la estantería, el sofá y la alfombra van a su caja; el puf, la mesa ratona y la lámpara, que se superponen con otros, no.

▸ paso: Lo que vimos: las cajas sirven para los muebles grandes, pero hay que pasarlas de otra forma, por ejemplo como una máscara aparte, o borrarlas en un segundo paso. Son tres imágenes por variante: es una pista, no un resultado.

### 46. Futuro · con medidas reales · 1:00 (acumulado 29:45)

Y cómo se vería en el producto, sobre nuestro cuarto dibujado. Uno: medir el ambiente, con una app móvil que use el LiDAR del teléfono para escanear el cuarto: paredes, aberturas y medidas reales. Hoy las cotas del dibujo dicen «?».

▸ paso: Dos: las medidas de cada producto en la metadata del catálogo, para tener su caja 3D a escala. Acá están las del living de la portada: la alfombra y la mesa ratona tienen ancho y fondo, el mueble de la tele solo el ancho; el sofá, la lámpara y la planta no tienen ninguna.

▸ paso: Tres: ubicar las cajas, de dos maneras: que la IA decida en el plano dónde va cada una, o que un primer paso de generación ponga los muebles así nomás, y tomar dónde quedó cada uno para poner ahí su caja a escala.

▸ paso: Cuatro: generar, con cada mueble llenando su caja, en su tamaño y lugar reales. Más adelante, si el negocio tiene modelos 3D de los productos, se usan en lugar de las cajas: se ubica el modelo en el cuarto escaneado y el generador solo tiene que hacerlo verse real.


## 07 · Cierre

### 47. Gracias · 0:15 (acumulado 30:00)

Les dejamos el comedor del mismo departamento, amoblado por amoblai. Gracias; ¿preguntas?


## Anexo

### Anexo A · IA responsable

Lámina de respaldo para la discusión del ejercicio 3: riesgos de IA responsable y estrategia de producción. Lo marcado «ya» está implementado en el prototipo.

### Anexo B · Ablación completa

Lámina de respaldo: todas las configuraciones de la ablación final, por si preguntan por alguna combinación.

# Guion · amoblai

TP 3 · 73.69 Large Language Models · ITBA 2026 · Juan Bautista Albertoni Salini, Matias Juan Rossi Seifert, Junior Rambau

Presentación: `presentacion.html` (56 láminas + 6 de anexo). Duración estimada: **30:50**. «▸ paso» marca dónde se aprieta → para mostrar lo siguiente de la lámina. Las notas también se ven en la presentación con la tecla N.

| # | Lámina | Tiempo | Acumulado |
|---|---|---|---|
| 1 | Portada | 0:25 | 0:25 |
| 2 | El problema | 0:40 | 1:05 |
| 3 | Qué hace amoblai | 0:50 | 1:55 |
| 4 | Lo que tiene que cumplir | 0:25 | 2:20 |
| 5 | Capítulo 01 · El recorrido | 0:10 | 2:30 |
| 6 | La planta del flujo | 0:35 | 3:05 |
| 7 | 1 · Catálogo | 0:30 | 3:35 |
| 8 | 2 · Descripción | 0:45 | 4:20 |
| 9 | 3 · Índice | 0:45 | 5:05 |
| 10 | 4 · Foto + pedido | 0:15 | 5:20 |
| 11 | 5 · Plan · el prompt | 0:50 | 6:10 |
| 12 | 5 · Plan · lo que devuelve | 0:30 | 6:40 |
| 13 | 6 · Búsqueda | 0:40 | 7:20 |
| 14 | 7 · Elección | 0:40 | 8:00 |
| 15 | 8 · Escena | 0:40 | 8:40 |
| 16 | 9 · Imagen | 0:20 | 9:00 |
| 17 | 10 · Control | 0:30 | 9:30 |
| 18 | 11 · Lista + imagen | 0:20 | 9:50 |
| 19 | El mapa de experimentos | 0:40 | 10:30 |
| 20 | Capítulo 02 · Cómo medimos | 0:10 | 10:40 |
| 21 | Ground truth | 0:45 | 11:25 |
| 22 | Las métricas, en un ejemplo | 1:10 | 12:35 |
| 23 | Intervalos de confianza | 0:40 | 13:15 |
| 24 | Capítulo 03 · Qué guardamos | 0:10 | 13:25 |
| 25 | E1 · ¿Buscamos los muebles por imagen o por texto? | 0:50 | 14:15 |
| 26 | E2 · ¿Qué texto indexamos, con qué embedder y qué filtro? | 0:55 | 15:10 |
| 27 | E3 · ¿Partimos cada descripción en chunks? | 0:30 | 15:40 |
| 28 | E4 · ¿Cuántas dimensiones necesita el embedding? | 0:35 | 16:15 |
| 29 | E5 · ¿La base vectorial se pierde resultados? | 0:25 | 16:40 |
| 30 | Capítulo 04 · Cómo buscamos | 0:10 | 16:50 |
| 31 | E6 · ¿Hace falta que el LLM reescriba la consulta? | 0:35 | 17:25 |
| 32 | E7 · ¿Conviene reordenar los candidatos mirando las fotos? | 0:45 | 18:10 |
| 33 | E7 · Dónde ayuda | 0:35 | 18:45 |
| 34 | E8 · ¿Cuántos candidatos le mostramos a choose? | 0:35 | 19:20 |
| 35 | Capítulo 05 · Cuánto creerle | 0:10 | 19:30 |
| 36 | E9 · Si otro escribe las consultas, ¿cambia el resultado? | 0:40 | 20:10 |
| 37 | E10 · ¿Sirve lo que trae, aunque no sea el producto exacto? | 0:40 | 20:50 |
| 38 | E11 · ¿La respuesta inventa, o responde lo que se pidió? | 0:45 | 21:35 |
| 39 | Capítulo 06 · De punta a punta | 0:10 | 21:45 |
| 40 | E12 · Qué catálogo (diseño) | 0:40 | 22:25 |
| 41 | E12 · Resultados | 0:50 | 23:15 |
| 42 | E12 · Un caso | 0:20 | 23:35 |
| 43 | E13 · Métricas de imagen | 0:35 | 24:10 |
| 44 | E13 · ¿Cómo pedimos la imagen para que no cambie el cuarto? | 0:45 | 24:55 |
| 45 | E14 · ¿Reproduce un living real si le damos sus muebles? | 0:40 | 25:35 |
| 46 | T4 · Lo que sigue | 0:15 | 25:50 |
| 47 | Capítulo 07 · Cierre | 0:10 | 26:00 |
| 48 | El camino | 0:25 | 26:25 |
| 49 | Costos | 0:20 | 26:45 |
| 50 | Aprendizajes y límites | 0:45 | 27:30 |
| 51 | Futuro · cajas en la foto | 0:25 | 27:55 |
| 52 | Futuro · ronda 2, el prompt | 0:45 | 28:40 |
| 53 | Futuro · el lugar en palabras | 0:30 | 29:10 |
| 54 | Futuro · ronda 2, resultados | 0:55 | 30:05 |
| 55 | Futuro · con medidas reales | 0:30 | 30:35 |
| 56 | Gracias | 0:15 | 30:50 |


## 00 · El producto

### 1. Portada · 0:25 (acumulado 0:25)

Buenas. Somos Juan Bautista, Matías y Junior, y esto es **amoblai**.

La idea es simple de decir: le das una foto de tu ambiente vacío, como este living dibujado, y le contás qué querés. amoblai te devuelve una lista de muebles reales de un catálogo y la foto de tu cuarto amoblado con ellos.

En la próxima media hora les contamos qué hace, cómo está armado y, sobre todo, cómo lo medimos: cada decisión salió de un experimento. Y este cuarto vacío se va a ir amoblando a medida que avanzamos.

### 2. El problema · 0:40 (acumulado 1:05)

El problema. Te mudás, tenés el ambiente vacío y una idea de lo que querés. Hay dos caminos y ninguno alcanza.

Un generador de imágenes te amobla la foto, pero con muebles inventados: son estas cajas punteadas con signos de pregunta. No los podés medir ni comprar.

▸ paso: Un catálogo tiene productos reales, pero no mira tu cuarto: filtrás por tipo, color, precio, y combinar ocho cosas que vayan entre sí y con tu piso lo hacés vos.

▸ paso: Nosotros queremos las dos cosas a la vez. Y eso, en el fondo, es un problema de RAG: la respuesta tiene que salir de lo que recuperamos del catálogo, no de la imaginación del modelo.

### 3. Qué hace amoblai · 0:50 (acumulado 1:55)

Así se usa. El usuario sube la foto del ambiente y escribe el pedido como le sale: «un living moderno y luminoso para recibir amigos, un sofá de tres cuerpos gris claro contra la pared de la izquierda, una mesa ratona de madera clara, una alfombra grande…».

▸ paso: amoblai devuelve la lista: 8 productos reales del catálogo, con cantidades (los almohadones van por dos) y medidas cuando el catálogo las tiene. Cada uno viene con su porqué.

▸ paso: Y la imagen: el mismo cuarto, con esos productos. Esta corrida costó US$0,41, con 3 intentos de imagen. Por qué hubo 3, lo vemos en el recorrido.

### 4. Lo que tiene que cumplir · 0:25 (acumulado 2:20)

Lo que amoblai promete, porque de acá salen las métricas: es el programa, como en un proyecto de arquitectura.

Que los productos sean los que van, contra un ground truth; si el exacto no está, algo que sirva; números creíbles; un porqué que no invente; y que la imagen sea tu cuarto. A la derecha, qué experimento mide cada cosa.


## 01 · El recorrido

### 5. Capítulo 01 · El recorrido · 0:10 (acumulado 2:30)

¿Cómo está armado? Lo vamos a recorrer como una casa, ambiente por ambiente. Primera pieza del cuarto: la alfombra, la base sobre la que se apoya todo.

### 6. La planta del flujo · 0:35 (acumulado 3:05)

Así está armado amoblai, dibujado como la planta de una casa: cada fase es un ambiente y se pasa al siguiente por una puerta.

▸ paso: A la izquierda, un pabellón que se construye una vez, offline: catálogo, descripción e índice. El índice llega a la búsqueda por esa pasarela.

▸ paso: Lo demás se recorre en cada pedido, de la foto a la lista. Tres ambientes llaman a un LLM, y una corrida cuesta unos US$0,29.

▸ paso: Los recorremos uno por uno: qué hace, qué decidimos y con qué experimento.

### 7. 1 · Catálogo · 0:30 (acumulado 3:35)

El catálogo. El dataset de IKEA de Tautkute y otros, revisado a mano: de 855 productos quedan 819.

▸ paso: Y un segundo catálogo, Amazon Berkeley Objects: 683 productos, casi todos con medidas. Cada uno entra con su foto, su tipo, su kind y sus medidas.

▸ paso: El kind es más fino que el tipo: hay 44, y es el filtro duro de la búsqueda. Usar los dos catálogos lo decidió el experimento 12.

### 8. 2 · Descripción · 0:45 (acumulado 4:20)

La descripción. El texto del vendedor es marketing: del sofá no dice que es gris claro ni de tres cuerpos. Por eso un modelo de visión mira la foto y lo describe. Texto y no imagen, y nuestras ocho líneas y no las del vendedor: experimentos 1 y 2.

▸ paso: El prompt pide ocho líneas fijas, en inglés: tipo, uso, estilo de una lista cerrada, materiales, colores, forma, sensación y con qué combina. Solo lo que se ve.

▸ paso: La v3 sumó lámparas y deco; la versión por la API, para ABO, devuelve además el kind.

▸ paso: Y esto escribió para el sofá de la lista.

### 9. 3 · Índice · 0:45 (acumulado 5:05)

El índice. Se embebe la descripción entera, un documento por producto; partirla en líneas empeora, experimento 3.

▸ paso: Con Qwen3-Embedding-0.6B, local, que le ganó a contar palabras y a BGE. Sin la instrucción de consulta del modelo: nuestra consulta ya está escrita como un documento. Y las 1024 dimensiones: el índice entero pesa 6,2 MB.

▸ paso: Va a ChromaDB, con un índice HNSW en coseno: da exactamente el mismo ranking que la búsqueda exacta, y guarda la metadata para filtrar.

▸ paso: Así queda un registro: el id, el documento, los mil veinticuatro números y la metadata. El sofá no tiene medidas: el catálogo guarda menos uno y pasa cualquier filtro.

### 10. 4 · Foto + pedido · 0:15 (acumulado 5:20)

Cada pedido empieza con lo que pone el usuario: una foto del ambiente vacío y el pedido en texto libre.

▸ paso: Puede sumar otra vista del cuarto: la ven plan y elección, pero se amobla la primera.

### 11. 5 · Plan · el prompt · 0:50 (acumulado 6:10)

Plan, el ambiente que más pesa. Opus 5.5 mira la foto y el pedido y, por pieza, decide el kind, hasta qué tamaño entra y una consulta en las mismas ocho líneas que los documentos. Es query rewriting, como HyDE: el experimento 6 muestra que es lo que más pesa del retrieval.

▸ paso: El prompt pide leer el cuarto como un diseñador, respetar la pieza nombrada, porque una silla no es un sillón, y no decir lo que no tiene que ser: los embeddings no leen la negación.

▸ paso: Cuarta versión, cada una por un error: la v1 pidió un sillón por una silla; la v3, por un living largo con cuatro muebles; la v4 sacó el tope de seis piezas.

### 12. 5 · Plan · lo que devuelve · 0:30 (acumulado 6:40)

Qué devuelve plan para el living de la portada. El pedido es largo y bastante preciso.

▸ paso: Plan lo convierte en 8 piezas, cada una con su kind y, cuando el cuarto lo limita, un tamaño máximo: el sofá hasta 240 por 95, la mesa ratona hasta 45 de alto.

▸ paso: Y la consulta de cada pieza: «gris claro» pasa a «Colors: light grey», «tres cuerpos» a «three-seat». Plan no ve el catálogo: describe el sofá ideal, en el formato de los documentos.

### 13. 6 · Búsqueda · 0:40 (acumulado 7:20)

La búsqueda. Primero un filtro duro: el kind de plan y el tamaño máximo, con un 15% de margen porque sale de una foto. Kind, tipo o ningún filtro dan casi lo mismo, experimento 2.

▸ paso: Este es el where del sofá. Después, el coseno entre la consulta y la descripción: 0,852.

▸ paso: Salen los 5 más cercanos; el de la lista salió segundo. Los sofás de IKEA no tienen medidas: el tamaño no los filtra.

▸ paso: Reordenarlos con un cross-encoder empeora; con Opus mirando las fotos mejora mucho. Eso lo hace el ambiente siguiente.

### 14. 7 · Elección · 0:40 (acumulado 8:00)

La elección. Opus 5.5 ve el cuarto y las 5 fotos de cada pieza y elige la combinación: uno por pieza, cuántos y por qué. Es el reranking del flujo; el experimento 7 mide cuánto suma y el 8, por qué 5.

▸ paso: El prompt pide elegir las piezas juntas, como un solo look, juzgando por las fotos.

▸ paso: La v2 agregó cantidades: cero saca la pieza.

▸ paso: Para la alfombra eligió la quinta por coseno, la de 170 por 240 que arma la zona. En 5 de las 8 piezas no eligió la primera.

### 15. 8 · Escena · 0:40 (acumulado 8:40)

La escena, el prompt del modelo de imagen. Al principio lo escribía Claude; hoy es una plantilla que se completa con la lista, sin LLM. Lo decidió el experimento 13.

▸ paso: El que se mandó para el living: es la foto del cliente y tiene que quedar el mismo cuarto, exactamente. Una línea por producto, con su medida o «size unknown». Y solo esos productos.

▸ paso: Con LLM, la v2 anclaba cada lugar a algo visible. Sin LLM, la v4 se volvió estricta cuando, con nueve productos, apareció una ventana que no existía.

### 16. 9 · Imagen · 0:20 (acumulado 9:00)

La imagen: Nano Banana 2, de Gemini, por fal, edita la foto con las de los 8 productos y el prompt. US$0,08 por imagen. Qué modelo usar está diseñado, sin correr.

▸ paso: Devuelve esto. Los productos son los de la lista… pero miren el cuarto.

### 17. 10 · Control · 0:30 (acumulado 9:30)

Por eso existe el control. Buscamos puntos característicos de la foto original en la generada, con SIFT, y una homografía con RANSAC. Si se reencuentran al menos 50 y la cámara casi no se movió, es el mismo cuarto.

▸ paso: Los dos primeros intentos de este living fallaron: 18 y 11 inliers, con la cámara corrida más del 15%. Se rechazaron solos.

▸ paso: El tercero reencontró 70 y se aceptó. Hasta 3 intentos; el umbral exacto queda para el experimento pendiente.

### 18. 11 · Lista + imagen · 0:20 (acumulado 9:50)

Y la salida: la lista de compra, 8 productos con su id, su medida cuando la hay y la cantidad, cada uno con su porqué. Esta corrida costó US$0,41, por los tres intentos de imagen.

▸ paso: Y la foto de tu cuarto con esos productos. Ese es el recorrido completo.

### 19. El mapa de experimentos · 0:40 (acumulado 10:30)

El mapa de lo que sigue: la misma planta, con una llamada de detalle por experimento; arriba el experimento, abajo su lámina.

▸ paso: En el indexing: qué catálogo, texto o imagen, qué texto, y cuatro decisiones del índice.

▸ paso: En cada pedido: reescribir la consulta, el filtro, el reranking y cuántos candidatos. Las punteadas son pruebas que no cambiaron el flujo.

▸ paso: Y la imagen: el prompt estricto y el control; la réplica, una prueba; el modelo de imagen, sin correr. Vamos a los detalles.


## 02 · Cómo medimos

### 20. Capítulo 02 · Cómo medimos · 0:10 (acumulado 10:40)

Antes de los experimentos, cómo medimos. Esto vale para todo lo que sigue. Segunda pieza: el sofá.

### 21. Ground truth · 0:45 (acumulado 11:25)

Para medir el retrieval hacen falta respuestas correctas. El dataset de IKEA de Tautkute y otros trae fotos de ambientes armados y, para cada foto, qué productos del catálogo aparecen. Esta es una, con sus 14 productos anotados.

▸ paso: Usamos los 65 livings y comedores. Para cada foto, subagentes de Claude escribieron una consulta por pieza que se ve, en las ocho líneas, como lo haría plan y sin ver el catálogo ni las anotaciones. Son 864 búsquedas; 549 tienen su producto en el catálogo, y sobre esas se mide. Una búsqueda acierta si trae el producto anotado de esa pieza. De referencia: elegir al azar entre lo que deja pasar el filtro acierta el primero en el 1,7% de los casos.

### 22. Las métricas, en un ejemplo · 1:10 (acumulado 12:35)

Las métricas, sobre una sola búsqueda: la alfombra crema de pelo largo de la foto anterior. El retrieval ordena las 89 alfombras del catálogo y el producto anotado queda 4.º.

▸ paso: **hit@k** pregunta si el anotado está entre los primeros k: acá hit@1 y hit@3 dan 0 y hit@5 da 1. Promediado sobre todas las búsquedas es una proporción de aciertos, y es la métrica que más vamos a usar. **MRR** es uno sobre el puesto del primer relevante: 1/4, 0,25. Premia que esté arriba aunque no sea primero.

▸ paso: **NDCG** descuenta la ganancia por el logaritmo del puesto y la normaliza por el orden ideal: 0,431. **Context precision** de RAGAS promedia la precisión en cada puesto donde hay un relevante; con un solo relevante coincide con MRR. En las 32 configuraciones que corrimos, MRR y context precision correlacionan 0,9999: miden casi lo mismo.

▸ paso: **Context recall**, también de RAGAS, se mira por ambiente: de los productos anotados de la foto, cuántos aparecen en el top-3 de alguna de sus búsquedas. Acá, 9 de 12.

### 23. Intervalos de confianza · 0:40 (acumulado 13:15)

Cada número de la charla va con un intervalo de confianza del 95%, por bootstrap. Pero ojo: las búsquedas de un mismo ambiente no son independientes, comparten la foto y el estilo.

▸ paso: Entonces remuestreamos ambientes, no búsquedas: sorteamos 64 ambientes con reposición, recalculamos el hit@1, y lo repetimos 1000 veces. El histograma son esas medias; el intervalo va de 0,491 a 0,577.

▸ paso: Y la regla que usamos en toda la charla: si dos intervalos se pisan, no decimos que una variante le gana a la otra.


## 03 · Qué guardamos

### 24. Capítulo 03 · Qué guardamos · 0:10 (acumulado 13:25)

Primer capítulo de experimentos: qué guardamos en el índice. Cinco decisiones del indexing. Y al cuarto se le suma el mueble de la tele.

### 25. E1 · ¿Buscamos los muebles por imagen o por texto? · 0:50 (acumulado 14:15)

Primer experimento, y el que cambió todo: ¿buscamos por imagen o por texto?

La v0 buscaba por imagen: detectaba cada mueble en la foto, lo recortaba y lo comparaba con las fotos del catálogo. Pero en amoblai el ambiente está vacío: no hay nada que recortar, hay un pedido.

▸ paso: Mismo ground truth y mismo catálogo que vio la v0, 275 productos. Por imagen, seis pasos acumulados, de CLIP a DINOv3. Por texto, las descripciones con Qwen3.

▸ paso: La imagen mejoró mucho con cada paso: de 0,126 a 0,508. Pero el texto llega a 0,618, con intervalos que apenas se tocan.

▸ paso: Decidimos texto. Gana, y además es lo único que funciona con el caso real: un cuarto vacío y un pedido escrito.

### 26. E2 · ¿Qué texto indexamos, con qué embedder y qué filtro? · 0:55 (acumulado 15:10)

Ya en texto: ¿qué texto ponemos de cada producto, con qué embedder y con qué filtro? La hipótesis: describir cada producto en las mismas ocho líneas que la consulta hace que se encuentren.

▸ paso: Corrimos la grilla completa: dos textos, tres embedders, desde contar palabras hasta Qwen3, y tres filtros: ninguno, el tipo grueso o el kind fino.

▸ paso: La lectura es por filas. Con el texto del vendedor, nada pasa de 0,189. Con nuestras descripciones, todo salta a más de 0,47. El embedder suma menos: Qwen3 es el mejor, pero el hashing queda cerca. Y poner el nombre comercial adelante empeora: agrega palabras que la consulta no tiene.

▸ paso: Decidimos descripciones con Qwen3. Los filtros casi no cambian nada, porque la línea Type ya dice qué es cada cosa; el flujo filtra por el kind que decide plan.

### 27. E3 · ¿Partimos cada descripción en chunks? · 0:30 (acumulado 15:40)

Splitting. La receta dice partir los documentos en chunks, pero la descripción ya es corta. ¿Conviene igual comparar por partes?

▸ paso: Probamos tres formas: el documento entero, cada línea como chunk, y línea contra línea del mismo rótulo, colores con colores.

▸ paso: Partir en líneas sueltas se cae a 0,273: una línea sola no dice de qué producto habla. Alinear por rótulo casi empata.

▸ paso: Nos quedamos con un documento por producto: igual de bueno y ocho veces más simple.

### 28. E4 · ¿Cuántas dimensiones necesita el embedding? · 0:35 (acumulado 16:15)

Dimensión del embedding. Qwen3 se entrenó con Matryoshka: las primeras componentes del vector ya son un embedding válido, más barato de guardar y de buscar.

▸ paso: Truncamos a 32, 64, hasta 1024, y renormalizamos. Sin reentrenar.

▸ paso: Con 32 componentes ya da 0,428; desde 512 la curva se aplana (0,532 contra 0,535).

▸ paso: Nos quedamos con las 1024: todo el catálogo ocupa 6,2 megas. Con un catálogo de millones, elegiríamos 256 o 512.

### 29. E5 · ¿La base vectorial se pierde resultados? · 0:25 (acumulado 16:40)

ChromaDB usa HNSW, una búsqueda aproximada sobre un grafo de vecinos. ¿Se le escapa el correcto?

▸ paso: Corrimos todas las búsquedas con HNSW y con búsqueda exacta, y comparamos el ranking entero.

▸ paso: Idénticos en las 864. Con este tamaño de catálogo, aproximado es exacto.

▸ paso: Nos quedamos con Chroma: filtros, persistencia y el texto al lado del vector.


## 04 · Cómo buscamos

### 30. Capítulo 04 · Cómo buscamos · 0:10 (acumulado 16:50)

Segundo capítulo: lo que pasa en cada pedido, antes y después de buscar. Llega la mesa ratona.

### 31. E6 · ¿Hace falta que el LLM reescriba la consulta? · 0:35 (acumulado 17:25)

Query rewriting. Vimos que plan escribe el producto ideal en las ocho líneas, como HyDE. Cuesta una llamada a Opus por pedido: ¿vale la pena, o alcanza con buscar «alfombra»?

▸ paso: Misma búsqueda con tres consultas: las ocho líneas, solo la línea Type, o solo el kind.

▸ paso: Con el nombre solo, 0,064, apenas arriba del azar. Con la línea Type, 0,293. Con las ocho líneas, 0,535.

▸ paso: Es la decisión que más pesa del retrieval: los colores, la forma y el estilo distinguen una alfombra de otras ochenta.

### 32. E7 · ¿Conviene reordenar los candidatos mirando las fotos? · 0:45 (acumulado 18:10)

Reranking. El embedding compara textos, pero dos alfombras crema de pelo largo se describen casi igual y se distinguen mirando. ¿Y si un modelo que ve reordena los primeros diez?

▸ paso: Probamos dos: un cross-encoder de texto, gratis; y Opus con la consulta y las fotos de los candidatos, a unos US$0,02 por búsqueda.

▸ paso: El cross-encoder empeora: 0,419; está entrenado en búsqueda web. Opus sube de 0,535 a 0,687, con intervalos que no se tocan: la mejora más grande después del query rewriting.

### 33. E7 · Dónde ayuda · 0:35 (acumulado 18:45)

Dónde ayuda: donde los productos se parecen entre sí. Alfombras, de 0,31 a 0,60; estantes, deco, lámparas. Sillas, donde el texto ya alcanzaba, sube menos.

A la derecha, la alfombra de las métricas: Qwen3 la dejó 4.ª; Opus la sube a la 1.ª.

▸ paso: Decisión: reordenar con un modelo que ve. En el flujo, eso lo hace la elección, que además arma la combinación entera.

### 34. E8 · ¿Cuántos candidatos le mostramos a choose? · 0:35 (acumulado 19:20)

¿Cuántos candidatos le mostramos a choose? Más candidatos, más chance de que esté el correcto, pero más fotos por llamada: más costo y más con qué confundirse.

▸ paso: Sin gastar de nuevo: del reranking de Opus sobre el top-10 sale qué elegiría entre los primeros k. Contra el techo: que el correcto esté entre los k.

▸ paso: El techo sube rápido, pero el acierto real se aplana: de 3 a 5 candidatos suma 0,029; de 5 a 8, 0,022.

▸ paso: Pasamos de 3 a 5. Más allá, el costo crece más que el acierto.


## 05 · Cuánto creerle

### 35. Capítulo 05 · Cuánto creerle · 0:10 (acumulado 19:30)

Tercer capítulo: cuánto creerle a todo esto. Se prende la lámpara.

### 36. E9 · Si otro escribe las consultas, ¿cambia el resultado? · 0:40 (acumulado 20:10)

Reproducibilidad. Las consultas las escribieron subagentes de Claude; otro redactor escribiría otras. Si el ranking de métodos depende de una redacción, no vale.

▸ paso: Hicimos escribir todas las consultas tres veces, de forma independiente, y corrimos cinco métodos en cada escritura.

▸ paso: El mejor método da 0,544 más menos 0,026. El orden se mantiene en las tres: Qwen3 con filtro por tipo arriba, el texto del vendedor abajo de todo.

▸ paso: El orden es firme, pero dos o tres centésimas entre métodos son ruido de redacción: empate.

### 37. E10 · ¿Sirve lo que trae, aunque no sea el producto exacto? · 0:40 (acumulado 20:50)

Relevancia graduada. hit@k solo cuenta el producto exacto, pero uno muy parecido sirve igual. Y más de un tercio de las búsquedas no tiene su producto en el catálogo.

▸ paso: Un juez LLM mira la foto y los tres primeros, sin saber cuál es el anotado, y les pone 2, 1 o 0: el context precision de RAGAS sin ground truth.

▸ paso: El primero sirve en el 75%, contra un hit@1 exacto de 0,53; sin el producto en el catálogo, en el 63%. El juez le pone 2 al anotado en el 81%.

▸ paso: hit@1 es una cota inferior de lo útil; el juez lo complementa.

### 38. E11 · ¿La respuesta inventa, o responde lo que se pidió? · 0:45 (acumulado 21:35)

RAGAS sobre la respuesta. Choose explica cada elección; si afirma una medida o un material falso, es una alucinación que el usuario se va a creer.

▸ paso: Faithfulness: qué fracción de las afirmaciones se sostiene con lo que vio el sistema. Answer relevance: el juez, sin ver el pedido, escribe tres que la respuesta contestaría, y medimos el coseno con el original, contra una vara de pedidos sin relación.

▸ paso: Faithfulness entre 0,89 y 0,97; relevance muy por encima de la vara. Lo que no se sostiene son medidas y cosas que el catálogo no dice.

▸ paso: No inventa productos; le falta información: los asientos de IKEA no tienen medidas. Eso nos llevó a otro catálogo.


## 06 · De punta a punta

### 39. Capítulo 06 · De punta a punta · 0:10 (acumulado 21:45)

Último capítulo de experimentos: de punta a punta, en ambientes vacíos reales. Cortinas y planta.

### 40. E12 · Qué catálogo (diseño) · 0:40 (acumulado 22:25)

¿Alcanza con IKEA? Es de un solo estilo y sus asientos no tienen medidas, justo lo que E11 vio fallar. ABO, el catálogo del primer ambiente del recorrido, trae muchos estilos y casi siempre medidas.

▸ paso: Sin ground truth, lo medimos de punta a punta: 11 ambientes vacíos reales, cinco nuestros con pedidos nórdicos y seis fotos públicas de otros estilos. El flujo con cada catálogo, y un juez compara las dos listas en los dos órdenes, porque los LLM prefieren la primera: una lista gana solo si gana en los dos.

### 41. E12 · Resultados · 0:50 (acumulado 23:15)

Los resultados. Cada columna es un ambiente: los cinco primeros son departamentos propios, los seis siguientes fotos públicas.

▸ paso: Con los dos votos del juez: en los propios, con pedidos nórdicos, IKEA solo e IKEA más ABO empatan: 2 a 2 con un empate. En las seis fotos públicas, con pedidos industrial, clásico, bohemio, gana IKEA más ABO 6 a 0, y la fracción de productos que cumplen sube de 0,46 a 0,71. Y sumar ABO como distractor casi no cambia el retrieval sobre el ground truth de IKEA. El juez coincide consigo mismo en los dos órdenes en el 91% de los casos.

▸ paso: Decisión: el flujo usa los dos catálogos. Lo que no cambia: las métricas con ground truth se siguen calculando solo sobre IKEA.

### 42. E12 · Un caso · 0:20 (acumulado 23:35)

Un caso: un loft con vigas y un pedido industrial, sofá de cuero envejecido, mesa con patas de metal negro, biblioteca de metal y madera.

IKEA propone lo más cercano: cuero liso, una mesa toda de madera. Con ABO aparecen el cuero coñac y la mesa industrial. Las barritas son la nota del juez.

### 43. E13 · Métricas de imagen · 0:35 (acumulado 24:10)

La imagen no tiene ground truth: la comparamos con la foto original y con el catálogo.

**SSIM** fuera de los muebles: similitud estructural solo donde no hay muebles; cerca de uno, el cuarto se preservó.

▸ paso: **SIFT con RANSAC**, la del control: si la cámara se movió, se reencuentran pocos puntos.

▸ paso: **Fidelidad de producto**: recortamos cada mueble y vemos si el más parecido del catálogo es el de la lista. Con fotos reales de IKEA da 0,444: es difícil.

▸ paso: Y SigLIP 2, imagen contra pedido. Todas locales y gratis.

### 44. E13 · ¿Cómo pedimos la imagen para que no cambie el cuarto? · 0:45 (acumulado 24:55)

El modelo de imagen tiende a «mejorar» la foto: mueve la cámara, agranda ventanas. El usuario compraría para un cuarto que no es el suyo.

▸ paso: Misma foto y misma lista; cambia el pedido de edición: Claude escribe la escena, edición libre o estricta. Una imagen por variante.

▸ paso: Con el pedido corto, las dos primeras preservan el cuarto parecido. Con el pedido detallado y 9 productos, la edición libre lo cambió: el SSIM fuera de los muebles cae a 0,29 y SIFT ve la cámara movida. La estricta lo preserva.

▸ paso: Edición estricta, sin LLM: más barata y más fiel. Y como una imagen por variante es una anécdota, el control automático en cada corrida.

### 45. E14 · ¿Reproduce un living real si le damos sus muebles? · 0:40 (acumulado 25:35)

Un experimento más sobre la imagen. En un ambiente vacío nadie sabe cómo debería quedar; en un living del ground truth sí: tenemos la foto real y sus productos.

▸ paso: La vaciamos con el mismo modelo y la volvimos a amoblar con sus 6 muebles, con el paso de imagen del flujo, 3 veces. Medimos dónde quedó cada uno: el IoU contra su caja en la foto real.

▸ paso: Los 6 aparecen y se reconocen, pero arma su propio living: IoU 0,20, 1 de 6 en su lugar.

▸ paso: Respeta los productos, no la distribución: el pedido no dice dónde va cada cosa. Al final probamos decírselo.

### 46. T4 · Lo que sigue · 0:15 (acumulado 25:50)

Lo que sigue, diseñado y sin correr: repetir la imagen en todos los ambientes, con LLM o estricta, qué modelo, qué resolución, y calibrar el control SIFT. Cuesta unos US$10 de fal más unos US$5 de Claude.


## 07 · Cierre

### 47. Capítulo 07 · Cierre · 0:10 (acumulado 26:00)

Cerramos. El cuarto ya está completo: le faltaban los almohadones.

### 48. El camino · 0:25 (acumulado 26:25)

El camino de los números. El punto de partida ingenuo, texto del vendedor y contar palabras, da 0,076. Escribir nuestras descripciones lo lleva a 0,495: el salto más grande lo dio qué texto guardamos, no el modelo. Qwen3, filtro y Chroma suman poco más, hasta 0,535. Y un modelo que mira las fotos al final lo lleva a 0,687.

### 49. Costos · 0:20 (acumulado 26:45)

Lo que cuesta: una corrida, unos US$0,29, más US$0,08 por cada reintento de imagen.

▸ paso: En todo el trabajo gastamos US$27,15 registrados, y lo que más se llevó fue evaluar: el reranking con Opus sobre todas las búsquedas. El retrieval, los embeddings y las métricas de imagen corren local y gratis.

### 50. Aprendizajes y límites · 0:45 (acumulado 27:30)

Cuatro cosas que aprendimos. Lo que más pesó fue qué texto guardamos y cómo escribimos la consulta, más que el embedder. Un modelo que ve, al final, vale más que cualquier ajuste fino del retrieval. Medir con intervalos y repetir nos salvó de declarar ganadoras cosas que eran ruido. Y las métricas sin ground truth encontraron lo que hit@k no ve, como las medidas que faltan.

▸ paso: Los límites: la imagen se midió con muy pocas imágenes; ABO solo tiene juez; los jueces son Claude evaluando a Claude, validados contra las anotaciones y no contra personas; y los asientos de IKEA siguen sin medidas.


## Pasos a futuro

### 51. Futuro · cajas en la foto · 0:25 (acumulado 27:55)

Para decirle dónde, dibujamos en la foto vacía una caja por mueble, donde está en la foto real: primero rectángulos, después cajas 3D, que además dicen hacia dónde mira y cuánto ocupa.

▸ paso: Ayudan, pero hubo dos problemas: el modelo dejaba las cajas dibujadas, en 3 de 6 imágenes, y el prompt era largo, una lista de prohibiciones. Por eso hicimos una ronda 2.

### 52. Futuro · ronda 2, el prompt · 0:45 (acumulado 28:40)

La ronda 2: seis variantes, 3 imágenes cada una, con el mismo cuarto vaciado y los mismos 6 productos. Todas usan este prompt corto: qué hacer, el pedido, una línea por producto y que el cuarto quede igual. Son 128 palabras; el de la ronda 1 llegaba a 375.

▸ paso: Cambia una sola línea: cómo dice dónde va cada mueble. Sin cajas, donde lo pondría un diseñador; en palabras, donde dice cada producto. Las tres de la ronda 1 las rehicimos con este prompt, para que solo cambie eso.

▸ paso: Y cuatro con cajas, 2D o 3D: dibujadas en la foto, y que las borre; o la foto limpia y las cajas en una guía aparte, la imagen 8, que no tiene que copiar.

### 53. Futuro · el lugar en palabras · 0:30 (acumulado 29:10)

En palabras: cada producto termina en «Where» y una o dos frases: contra qué pared y al lado de qué.

▸ paso: Las escribió Opus 5.5, en una llamada, mirando la foto real y la vaciada. Ojo: eso mide si alcanza con decirlo en palabras, no si un LLM sabe dónde van.

▸ paso: Las tres salieron iguales: la estantería y la lámpara donde dice el texto, y el sofá mirando a la cámara.

### 54. Futuro · ronda 2, resultados · 0:55 (acumulado 30:05)

Los resultados. Arriba, la ronda 1 de referencia: sin cajas, 0,20 de IoU; con rectángulos, 0,40; con cajas 3D, 0,48.

▸ paso: La ronda 2. El prompt corto no empeora nada: con rectángulos da 0,43 y con cajas 3D 0,52, y con tres imágenes eso es ruido; lo que cambia es que con cajas 3D ninguna quedó dibujada. En palabras casi duplica a no decir nada, 0,37 contra 0,20, pero pone pocos muebles en su lugar. Y la guía aparte ubica peor que dibujar las cajas, y tampoco evita que aparezcan.

▸ paso: Acá se ven: la de texto, la mejor con cajas 3D, y una con guía que copió los rectángulos.

▸ paso: La decisión: el flujo no cambia, porque sin medidas no hay cajas; a futuro, cajas 3D en la foto y prompt corto. Es un cuarto y tres imágenes: una prueba, no una medición.

### 55. Futuro · con medidas reales · 0:30 (acumulado 30:35)

Y cómo sería en el producto. Uno: medir el ambiente con el LiDAR del teléfono; hoy las cotas dicen «?».

▸ paso: Dos: la caja 3D de cada producto, con las medidas del catálogo; en rojo, los que no las tienen.

▸ paso: Tres: ubicar las cajas, que lo decida la IA o una primera generación. Sin medir nada, se puede probar ya que el plan lo diga en palabras.

▸ paso: Cuatro: generar con las cajas 3D dibujadas en la foto y el prompt corto.


## 07 · Cierre

### 56. Gracias · 0:15 (acumulado 30:50)

Les dejamos el comedor del mismo departamento, amoblado por amoblai. Gracias; ¿preguntas?


## Anexo

### Anexo A · IA responsable

Lámina de respaldo para la discusión del ejercicio 3: riesgos de IA responsable y estrategia de producción. Lo marcado «ya» está implementado en el prototipo.

### Anexo B · Ablación completa

Lámina de respaldo: todas las configuraciones de la ablación final, por si preguntan por alguna combinación.

### Anexo C · Línea de tiempo

Y así se fue transformando. El 06/10 arrancamos con una v0 que buscaba por imagen. El 21/10 pasamos a texto, que es la arquitectura que acaban de ver; el primer experimento explica por qué.

▸ paso: Después vinieron el reranking con Opus y un catálogo más grande, las métricas de RAGAS y la reproducibilidad, y el control de la imagen.

▸ paso: En noviembre revisamos el catálogo a mano y sumamos un segundo catálogo, el 10/11. Lo que sigue son los experimentos de imagen, que están diseñados.

### Anexo D · La planilla de alternativas

Lámina de respaldo: las alternativas de cada decisión, la que quedó y el experimento que la decidió. En la charla, esto lo cuenta el mapa de experimentos.

### Anexo E · Réplica, ronda 2: las imágenes

Lámina de respaldo: las 18 imágenes de la ronda 2, con su IoU, cuántos muebles quedaron en su lugar y lo que se ve a ojo (las observaciones de replica.yaml).

### Anexo F · Réplica: el IoU de cada mueble

Lámina de respaldo: el IoU de cada mueble en las nueve variantes. Las cajas ubican sobre todo los muebles grandes (estantería, sofá, alfombra); sin decir dónde, la estantería va siempre a la derecha.

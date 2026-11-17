# Guion de la presentación (amoblai, versión simple)

Generado por `build.py` junto con `presentacion_simple.html`: los números salen de los mismos archivos de resultados que las láminas, y los extractos de los prompts, de `src/amoblai/prompts/`. 56 láminas, unos 33 minutos (32:53); son unas 4.300 palabras, contadas a 135 por minuto.

**Cómo se pasa.** Flecha derecha, espacio o clic: avanza un paso; flecha izquierda: vuelve. F: pantalla completa; O: índice con miniaturas; N: estas notas abajo de la lámina; P: ventana del presentador (lámina actual, la siguiente, notas y reloj, sincronizadas); B: pantalla negra; A: en la lámina del prompt de la descripción, abre el anexo con el prompt completo, y en el anexo vuelve. `presentacion.html?all#/12` muestra la lámina 12 con todos sus pasos; `#/12.2` va al paso 2.

**El recorrido** (láminas 5 a 15) sigue un pedido real con la configuración final, un loft de estilo industrial sobre una foto pública, por las once fases del flujo, con el mapa arriba a la derecha: la fase actual encendida, las vistas con ✓ y el pin de los experimentos que le hicieron una pregunta a esa fase (lleno: con lámina propia; hueco: de trámite). En cada fase: qué entra y qué sale, y el prompt tal cual se manda (extracto, en inglés, con lo importante resaltado) con sus versiones. Ahí no se dan resultados: los números van en cada experimento.

**Los experimentos** van por su ranking (el mapa, en la lámina 26), una lámina cada uno: el título y los gráficos, con barras de error (IC 95% por bootstrap de ambientes) y, en azul, lo que queda en el flujo. Cuando el experimento se repitió de punta a punta en los 11 ambientes vacíos (el 1, el 2, el 5, el 6, el 13 y el 5b), ese panel va a la derecha: los productos útiles de cada lado y el marcador del juez. El camino incremental (lámina 30) resume los tres primeros; los siete de trámite van del 36 al 42; al final, el 5b, elegir con texto o con fotos, que se nos ocurrió después de decidir todo lo demás (43), y el coseno sin juez (44). Las láminas no tienen pasos: se cuenta la pregunta, se señala cada panel y se dice la decisión.

**El Ejercicio 4** son las láminas 45 a 47: la versión 1 y su limitación, el cambio con la configuración antes y después, y los resultados en las dos versiones.

En el texto, **→** marca dónde se avanza un paso. Si falta tiempo, se pueden pasar rápido las láminas de trámite (las marcadas con *). Los costos están en el anexo, después de «Gracias».

**Reparto sugerido** (a definir entre los tres):
- Parte 1: láminas 1 a 18 (Portada → Ambientes vacíos), unos 11:00.
- Parte 2: láminas 19 a 34 (El juez de listas, en un caso → Exp. 7: Tres redactores), unos 10:55.
- Parte 3: láminas 35 a 56 (Exp. 8: Buscar por imagen → Gracias), unos 11:00.

## 1. Portada
*Portada · ~0:25 · desde el minuto 0:00*

Somos Juan Bautista, Matías y Junior. amoblai responde una pregunta concreta: tengo este ambiente vacío, ¿qué compro y cómo queda? Sacás una foto, escribís qué querés, y te devuelve una lista de productos reales de un catálogo y la imagen del mismo ambiente con esos productos.

## 2. El problema
*El problema · ~0:25 · desde el minuto 0:25*

Cuando te mudás a un lugar vacío tenés que decidir qué comprar sin poder verlo puesto. Los catálogos muestran cada mueble suelto, y las fotos de ambientes muestran la casa de otro. **→** Queremos responder, para este ambiente y este pedido: qué productos reales van, y cómo queda el ambiente con ellos.

## 3. El producto
*El producto · ~0:30 · desde el minuto 0:50*

Así se usa. La entrada es una foto del ambiente y un pedido en texto libre, como este: un loft donde piden un living de estilo industrial, con un sofá de cuero envejecido. **→** La salida son dos cosas: la lista de compra, con productos reales del catálogo, acá 7, entre IKEA y Amazon, y la foto del mismo ambiente con esos productos puestos.

## 4. Por qué RAG
*El producto · ~0:35 · desde el minuto 1:20*

¿Por qué un RAG? Por tres cosas. Información actualizada: para que un LLM solo conozca productos nuevos habría que reentrenarlo; acá un producto nuevo es una fila más en el índice. **→** Información personalizada: el modelo no conoce estos 1.502 productos; la búsqueda le trae, por cada pieza, 5 candidatos reales con su foto. **→** Y sin alucinaciones: un LLM solo puede recomendar un sillón que nadie vende; acá solo puede elegir productos que trajo la búsqueda, y la imagen se arma con sus fotos.

## 5. El recorrido
*Recorrido · ~0:40 · desde el minuto 1:55*

El sistema, fase por fase, sobre este mapa: once fases en dos pipelines. **→** Las tres primeras corren una vez, offline: el catálogo, la descripción de cada producto y el índice. **→** Las otras ocho corren en cada pedido: el plan decide las piezas, la búsqueda trae candidatos, la elección arma la lista, y después la escena, la imagen y el control. Solo tres llaman a un modelo: Opus en el plan y en la elección, y Nano Banana 2 en la imagen. **→** En cada fase vamos a ver qué entra, qué sale y el prompt.

## 6. Fase 1: Catálogo
*Recorrido · 1 · ~0:40 · desde el minuto 2:35*

Fase uno, el catálogo: la base de conocimiento. Son dos fuentes. El dataset de IKEA: lo ampliamos a 855 productos de living y comedor y, revisado mirando cada foto, quedaron 819. Y Amazon Berkeley Objects, listados reales de Amazon: de casi 150 mil quedaron 683. En total, 1.502 productos. **→** Cada producto es un mismo registro: id, foto, tipo, kind y medidas. Tipo, kind y medidas sirven para filtrar; la foto, para describirlo. Así viene una lámpara de IKEA, sin medidas, y así un sofá de Amazon, con medidas.

## 7. Fase 2: Descripción
*Recorrido · 2 · ~0:40 · desde el minuto 3:15*

Fase dos: la descripción. Un VLM, Opus 5.5, mira la foto de cada producto y lo escribe en ocho líneas fijas: tipo, uso, estilo, materiales, colores, forma, sensación y con qué combina. El prompt pide exactamente esas ocho líneas, sin marca, precio ni medidas, y nada de lo que el producto no es, porque el embedding no entiende la negación. **→** Este es el sofá de Amazon que vamos a seguir: Amazon pasó por la API, con las mismas reglas. Es el preprocesamiento que más pesa: lo mide el experimento 1.

## 8. Fase 3: Índice
*Recorrido · 3 · ~0:40 · desde el minuto 3:55*

Fase tres: el índice. Se embebe la descripción entera, un documento por producto, con Qwen3-Embedding, local, en CPU: 1.024 dimensiones, a ChromaDB, con la metadata de los filtros al lado. Así queda el sofá. Embedder, splitting, dimensión y base vectorial son preguntas de trámite: las contestamos juntas más adelante. **→** Para la búsqueda híbrida se suman dos índices sobre los mismos productos: uno léxico, BM25 sobre las palabras de las descripciones, y uno por foto, con SigLIP 2, que pone la foto y el texto en un mismo espacio.

## 9. Fase 4: Foto, pedido y plan
*Recorrido · 4 · ~0:50 · desde el minuto 4:35*

Fases cuatro y cinco. Entra una foto del ambiente vacío y un pedido en texto libre. Vamos a seguir este loft hasta el final: un pedido de estilo industrial, sobre una foto pública. **→** El plan es la primera llamada a Opus, que hace de diseñador: lee el ambiente, descompone el pedido en piezas, acá 7, y para cada una da el kind, que va a ser el filtro, la medida máxima, y la consulta: el producto ideal escrito en las mismas ocho líneas que el catálogo. Es query expansion con respuesta hipotética, HyDE: en la base no hay preguntas, hay respuestas. Más la descomposición del pedido: una consulta por pieza.

## 10. Fase 5: Plan
*Recorrido · 5 · ~0:40 · desde el minuto 5:25*

Es el prompt que más reescribimos, y cada versión salió de una corrida. La primera le dio un sillón a alguien que pidió una silla para su escritorio. La v2 pide la pieza como la nombró el usuario, el kind de una lista cerrada, las medidas máximas y la consulta en ocho líneas. La v3 pide terminar el ambiente, y la v4 saca el tope de piezas. La consulta en las ocho líneas no cambió desde la v2: es lo que mide el experimento 2.

## 11. Fase 6: Búsqueda
*Recorrido · 6 · ~0:45 · desde el minuto 6:00*

Fase seis, la búsqueda. Para cada pieza, primero un filtro duro de metadata: el kind del plan y las medidas máximas, con 15% de margen porque salen de una foto. Acá quedan 76 de los 1.502 productos. **→** Sobre esos, tres puntajes con la misma ficha: el coseno de Qwen3 entre la ficha y la descripción; BM25, las palabras de la ficha que están en la descripción; y SigLIP 2, la ficha en una frase contra la foto del producto. Cada puntaje se estandariza y se promedian: es la búsqueda híbrida, la versión 2. Quedan los cinco mejores: 4 de Amazon y 1 de IKEA.

## 12. Fase 7: Elección
*Recorrido · 7 · ~0:45 · desde el minuto 6:45*

Fase siete, la elección: es la generación de la lista, la G del RAG. Opus ve la foto del ambiente y los cinco candidatos de cada pieza, acá 36 imágenes, cada uno con su id, su tipo y su medida. El prompt le pide elegir las piezas juntas, como un solo look, y decir cuántas unidades; cero deja una pieza afuera. Solo puede elegir productos que trajo la búsqueda: si no, el código rechaza la respuesta. **→** No es un reranker: arma un conjunto para este cuarto. Acá tomó el primero de la búsqueda en 3 de las 7 piezas; la biblioteca era el quinto candidato.

## 13. Fase 8: Escena
*Recorrido · 8 · ~0:35 · desde el minuto 7:35*

Fase ocho, la escena: el prompt para el modelo de imagen. Hay dos caminos: que Opus escriba dónde va cada producto, con una llamada más, o una plantilla sin LLM, que se completa con la lista y el pedido. Esta es la plantilla: una edición de la foto del cliente, con la misma cámara, sin tocar paredes ni ventanas, y exactamente estos productos. En la configuración final va la plantilla; por qué, lo vemos en los experimentos.

## 14. Fase 9: Imagen y control
*Recorrido · 9 · ~0:45 · desde el minuto 8:10*

La imagen la hace Nano Banana 2, en modo edición: recibe la foto del ambiente, las fotos de los productos y el prompt. Acepta 14 imágenes, así que muestra hasta 13 productos; el resto queda en la lista. **→** Después, el control: si la imagen no conserva el cuarto, se genera otra, hasta 3 veces. El loft pasó al primer intento. Este otro pedido, un living clásico, no: el modelo reencuadró hacia la chimenea en los tres intentos, y se entrega el que mejor conserva el cuarto. En las 11 corridas finales pasan 7, todas al primer intento.

## 15. Fase 11: Lista + imagen
*Recorrido · 11 · ~0:30 · desde el minuto 8:50*

Y fase once, lo que sale: la lista de compra, con productos reales y cuántos de cada uno, y la foto del mismo ambiente con ellos. Cada línea tiene su recorrido: el kind lo puso el plan, la búsqueda trajo los candidatos y la elección tomó uno, a veces no el primero: acá se ve el puesto de cada uno en la búsqueda.

## 16. Desafíos
*Desafíos · ~0:45 · desde el minuto 9:20*

Los desafíos. Uno: el texto del catálogo es marketing, y la gente pide estilo, color y materiales; hubo que describir cada producto mirando su foto. Dos: el catálogo; algunos productos traían la foto de otro, o de otra medida. Revisamos los dos, IKEA a mano, y en Amazon el modelo que describe descarta las fotos que no muestran el producto. Tres: no hay ground truth de la tarea real; la búsqueda la medimos con fotos de IKEA anotadas, y la lista, con un juez que compara dos listas. Y cuatro: el modelo de imagen rehace el cuarto; por eso, el control.

## 17. Cómo medimos la búsqueda
*Datos · ~0:35 · desde el minuto 10:05*

Usamos dos sets de evaluación, que miden cosas distintas. Para la búsqueda, 65 ambientes de IKEA con sus productos anotados. Por cada mueble visible, un subagente escribió la consulta como la escribiría el plan, sin ver el catálogo. **→** Una consulta acierta si el anotado sale primero, o entre los k primeros. **→** Son 864 consultas, 549 con su producto en el catálogo de 819. Es de producto conocido: quien escribe está viendo el mueble, así que mide el índice, no la recomendación.

## 18. Ambientes vacíos
*Datos · ~0:20 · desde el minuto 10:40*

Para el flujo entero, 11 ambientes vacíos reales, cada uno con su pedido: 5 nuestros y 6 públicos, de estilos distintos del nórdico. Ahí no hay ground truth: compara un juez, que vemos en un caso.

## 19. El juez de listas, en un caso
*Datos · ~0:25 · desde el minuto 11:00*

Un caso. El juez ve la foto, el pedido y dos listas, sin saber de dónde viene cada una. **→** A cada producto le pone 2, 1 o 0; los que sacan 2 son los productos útiles. **→** Elige B, por el sofá beige. **→** Y al revés: si vuelve a elegir la misma, gana el ambiente; si no, empate.

## 20. Métricas del buscador
*Métricas · ~0:45 · desde el minuto 11:25*

Las métricas del buscador. Arriba, una consulta real: el anotado sale en el puesto 3, así que hit@1 da cero y hit@3 da uno. **→** El titular es hit@5, porque son los cinco candidatos que ve el que elige. Para comparar dos métodos usamos la diferencia pareada: las mismas consultas, la diferencia media y su intervalo de 95 por ciento, por bootstrap de ambientes. Si no toca el cero, no es ruido. Mirar el intervalo de cada método por separado nos había hecho leer mejoras que eran ruido. Context precision y NDCG, con uno o dos relevantes por consulta, repiten al MRR.

## 21. El generador
*Métricas · ~0:25 · desde el minuto 12:10*

El generador es Opus eligiendo, con un porqué por producto. Faithfulness: un juez parte el porqué en afirmaciones y marca cuáles se infieren de lo que vio. Answer relevance: un juez que no ve el pedido escribe el que la lista contesta, y medimos el coseno con el original; la vara, con pedidos de otras listas.

## 22. Faithfulness, en un caso
*Métricas · ~0:25 · desde el minuto 12:35*

El loft. Al juez le entra lo que vio Opus: las fotos, la línea de cada producto, el pedido y el porqué. **→** Lo parte en afirmaciones y marca cada una. **→** Sostiene 26 de 29. Fallan «madera maciza», que la línea no dice; «como pediste», con una maceta que nadie pidió; y «nada de blanco», con flecos blancos.

## 23. La imagen
*Métricas · ~0:25 · desde el minuto 13:00*

La imagen, con dos preguntas. ¿Son esos productos? Recortamos cada mueble y, con DINOv3, lo comparamos con los de su tipo: reconocido, si el más parecido es el de la lista. En el loft, la alfombra no. **→** ¿Es ese cuarto? SIFT busca en la imagen los puntos de la foto; si encuentra pocos, se genera otra.

## 24. Advertencias
*Métricas · ~1:35 · desde el minuto 13:25*

Cuatro advertencias, y por qué medimos igual. Uno: el set de la búsqueda es de producto conocido. Quien escribe la consulta ve el mueble; en el flujo, el plan lo imagina, y el coseno del primer candidato baja de 0,875 a 0,80–0,82: esos números son optimistas. Lo usamos porque es la única forma de tener respuesta correcta para cientos de consultas, y todas las variantes reciben las mismas: sirve para comparar. **→** Dos: el mismo modelo escribe las descripciones y las consultas, con el mismo molde; por eso contar palabras rinde casi como el embedder. Pero así funciona el sistema: el plan también escribe una ficha. **→** Tres: no hay conjunto apartado; todo se eligió sobre los mismos 64 ambientes. Partirlos dejaba muy pocos. En cambio, comparamos siempre de a pares, con su intervalo, y medimos el ruido con tres redactores: dos puntos no son señal. **→** Y cuatro: de punta a punta son 11 ambientes, y el juez es el mismo modelo que elige. La misma configuración, corrida dos veces, cambió 9 de 75 productos, y el juez repartió los ambientes 3 a 3. Por eso el juez corre en los dos órdenes y solo leemos resultados desparejos, como un cinco a cero. Más ambientes, y validar al juez con personas, quedan para el trabajo futuro.

## 25. Configuración inicial
*Experimentos · ~0:20 · desde el minuto 15:00*

Arrancamos de un RAG naive; al lado de cada fase, el experimento que la pone a prueba. Lo que gana se suma, y cada experimento cambia una sola cosa.

## 26. El mapa de los experimentos
*Experimentos · ~0:30 · desde el minuto 15:20*

Ahora los experimentos, por cuánto importan. El mismo mapa: cada pin es una pregunta que le hicimos a una parte del sistema. Del 1 al 8, los que más pesan; el 4 y el 7 miden al set de evaluación. Del 9 al 15, los de trámite, una lámina rápida cada uno. Y dos cosas no las decidió ningún experimento: el modelo de imagen y los umbrales del control.

## 27. Exp. 1: Qué se indexa
*Experimentos · 1 · ~0:55 · desde el minuto 15:50*

El texto de IKEA es marketing, y la gente pide estilo, color y materiales, que están en la foto. Comparamos indexar el texto del vendedor contra la descripción de ocho líneas hecha mirando la foto, con todo lo demás fijo. En el set de IKEA, hit@1 pasa de 0,11 a 0,30, casi el triple, y hit@5 de 0,30 a 0,60; la diferencia pareada, +0,19, está lejos del cero. De punta a punta, en los once ambientes, el juez elige la descripción 9 a 1, con 1 empate, p igual a 0,02, y los productos útiles caen de 0,77 a 0,60 con el texto del vendedor. Decisión: se indexa la descripción. Es lo que más pesa de todo el trabajo.

## 28. Exp. 2: Cómo se escribe la consulta
*Experimentos · 2 · ~0:50 · desde el minuto 16:45*

El plan no busca con el pedido: escribe el producto ideal en las ocho líneas del catálogo, una ficha. Es la técnica de Advanced RAG del flujo, query expansion, y la medimos contra no reescribir: la frase con que el redactor nombró la pieza. La ficha da 0,530 y la frase 0,324: +0,21, lejos del cero; solo la línea Type o solo el kind quedan muy abajo. De punta a punta, 7 a 3 para la ficha, con 1 empate: no alcanza la significancia, p igual a 0,34, pero va para el mismo lado. Texto y foto fallan distinto, y eso es un argumento para la híbrida. Decisión: el plan sigue escribiendo la ficha.

## 29. Exp. 3: Búsqueda léxica, por foto e híbrida
*Experimentos · 3 · ~0:45 · desde el minuto 17:35*

¿Hace falta el embedder, o alcanza con contar palabras? ¿Y embeber la foto del producto, en vez de describirla? Tres buscadores con el filtro por kind: el denso, Qwen3 sobre las descripciones; el léxico, BM25; y por foto, SigLIP 2, y sus fusiones. Solos rinden parecido: 0,530, 0,517 y 0,508; CLIP, un modelo por foto más viejo, queda muy abajo. Pero se equivocan en cosas distintas: a la derecha, la diferencia pareada contra la densa. Las tres juntas dan 0,605, +0,075, con un intervalo que no toca el cero. Decisión: la búsqueda pasa a ser híbrida. Es la versión 2, el Ejercicio 4.

## 30. El camino incremental
*Experimentos · ~0:35 · desde el minuto 18:20*

La ablación incremental: un cambio por paso, con su intervalo, sobre las 549 consultas. Del RAG naive, 0,11, la descripción lo lleva a 0,30 y la consulta como ficha a 0,54: esos dos pasos son los que más pesan. El filtro por kind no suma acá; con él, es la versión 1. La léxica y la foto llegan a 0,60: la versión 2. A la derecha, rayados, un VLM eligiendo o reordenando, 0,687: técnicas aisladas, no escalones del flujo.

## 31. Exp. 4: ¿Error, o una variante?
*Experimentos · 4 · ~0:40 · desde el minuto 18:55*

hit@1 exige el producto anotado exacto, y el catálogo está lleno de variantes del mismo modelo. Tres niveles de correcto para el primer candidato: el exacto, 0,53; el mismo modelo, 0,62; y uno que sirve según un juez, 0,78. Una de cada 5 veces que el primero falla es otra variante del mismo mueble. Al juez lo probamos con las anotaciones: al producto anotado le dice que sirve el 81 por ciento de las veces; a los otros candidatos, el 5. Conclusión: el exacto subestima el nivel, no el orden; sirve para comparar.

## 32. Exp. 5: Elegir con un VLM, y cuántos candidatos
*Experimentos · 5 · ~0:50 · desde el minuto 19:35*

hit@10 es 0,89 pero hit@1 0,54: el correcto suele estar, pero no primero. Opus mirando las fotos del top-10 lleva hit@1 de 0,535 a 0,687. De ahí sale la curva del medio: si eligiera entre los primeros k, ¿acertaría? La punteada es el techo. De 3 a 5 sube 3 puntos, con un intervalo que no toca el cero, y a partir de 8 se aplana. De punta a punta, cinco contra tres: 7 a 1, con 3 empates, p igual a 0,07. Decisión: cinco candidatos por pieza. Ojo: el reranker es una técnica aislada; el que elige arma un conjunto para el cuarto y no tiene ground truth.

## 33. Exp. 6: Con búsqueda, al azar, o con el catálogo entero
*Experimentos · 6 · ~0:55 · desde el minuto 20:25*

¿La búsqueda aporta en la tarea real? ¿Y hacía falta, si el catálogo entra en el contexto? Mismo plan, mismo modelo que elige, mismo juez, en los dos órdenes. Contra cinco al azar del mismo kind, 7 a 0: los productos útiles pasan de 0,26 a 0,82, y el juez distingue. Contra el catálogo entero en el prompt, 5 a 5: empatan. ¿Por qué RAG, entonces? Con búsqueda, el que elige recibe unos 24 mil tokens; con el catálogo, 346 mil, un tercio del contexto: con el triple de productos no entra. Y elegir cuesta US$0,14 contra US$1,42 sin caché; la caché lo baja a US$0,12, pero dura cinco minutos. Con poco tráfico o un catálogo más grande conviene RAG, y por eso lo elegimos.

## 34. Exp. 7: Tres redactores
*Experimentos · 7 · ~0:30 · desde el minuto 21:20*

Las consultas de evaluación las escribió un modelo: ¿medimos al redactor o al sistema? Las mismas consultas, escritas otras dos veces por subagentes independientes. La versión 1 da 0,539 ± 0,025; la versión 2, 0,604 ± 0,009, y la mejora de la híbrida se repite en los tres, con intervalos que no tocan el cero. El número se mueve unos dos puntos y medio según quién escribe: dos puntos no son señal.

## 35. Exp. 8: Buscar por imagen
*Experimentos · 8 · ~0:35 · desde el minuto 21:55*

Otra arquitectura: que un generador de imágenes amueble primero, recortar cada mueble y buscarlo en el catálogo por su foto. Con el mismo ground truth, los 232 productos anotados: por imagen encuentra primero el 43 por ciento; por texto, el 55. Y es el mejor caso para la imagen: los recortes salen de fotos reales. Nos quedamos con el texto. Ojo: el flujo entero por imagen no lo corrimos; lo que el generador elegiría y dónde lo ubicaría no lo medimos.

## 36. Exp. 9: Embedder *
*Experimentos · 9 · ~0:15 · desde el minuto 22:30*

¿Importa el embedder? Cuatro, de contar palabras a Qwen3. Qwen3 solo se distingue de BGE; contra contar palabras no, por el molde compartido. Queda Qwen3.

## 37. Exp. 10: Dimensión del embedding *
*Experimentos · 10 · ~0:15 · desde el minuto 22:45*

Qwen3 deja recortar el vector: probamos de 32 a 1024 dimensiones. Con 512 da lo mismo; con este catálogo la memoria no pesa, y queda 1024.

## 38. Exp. 11: Chunk size *
*Experimentos · 11 · ~0:15 · desde el minuto 23:00*

¿Partir la descripción en pedazos? No: las líneas solas pierden el contexto del producto. Un documento por producto.

## 39. Exp. 12: Base vectorial *
*Experimentos · 12 · ~0:15 · desde el minuto 23:15*

ChromaDB busca con un índice aproximado. Contra comparar con todos no pierde nada: el mismo top-10 en las 864 consultas. La usamos porque persiste y escala.

## 40. Exp. 13: Filtros por metadata *
*Experimentos · 13 · ~0:25 · desde el minuto 23:30*

¿Suman los filtros? En el set de IKEA, no. De punta a punta, sin el filtro por kind: 4 a 3, con 4 empates; empatan. Lo usamos igual: no cuesta nada y asegura cinco candidatos del tipo pedido. Sin él, el 11 por ciento de los candidatos de los pedidos reales sería de otra categoría.

## 41. Exp. 14: Rerankers de texto *
*Experimentos · 14 · ~0:15 · desde el minuto 23:55*

¿Un reranker de texto ordena mejor? No: los dos empeoran, porque releen el texto que ya usó la búsqueda. El que suma mira las fotos: el experimento 5.

## 42. Exp. 15: La escena *
*Experimentos · 15 · ~0:15 · desde el minuto 24:10*

El prompt de la imagen: ¿una plantilla, o que lo escriba el LLM? Empatan, y la plantilla ahorra una llamada: queda la plantilla.

## 43. Exp. 5b: Elegir con texto o con fotos
*Experimentos · 5b · ~0:50 · desde el minuto 24:25*

El último, y por eso va al final: se nos ocurrió después de decidir todo lo demás. Elegir es, en el fondo, reordenar; el 5 lo midió mirando las fotos, nunca sin ellas. En el set de IKEA, reordenando el top-10: con fotos 0,687, solo con texto 0,681; la diferencia pareada es casi cero. De punta a punta, 6 a 4, con 1 empate: dentro del ruido, que es 3 a 3. Y con texto, elegir cuesta la mitad: US$0,07 en vez de US$0,14, porque entran 9 mil tokens en vez de 24 mil. Decisión: el flujo sigue con fotos, como se midió todo lo demás; si con más ambientes sigue empatando, conviene el texto, por costo.

## 44. ¿Sirve el coseno sin juez?
*Experimentos · ~0:35 · desde el minuto 25:15*

Una métrica sin juez: el coseno entre la ficha que escribe el plan y el producto elegido, con el mismo embedder para todas las variantes. Es gratis. Separa lo malo: al azar da 0,710, y la frase natural y el texto del vendedor, 0,759. Pero no ordena lo bueno: la versión 1 saca más que la 2, 0,798 contra 0,791, y pierde 0–5 con el juez; y tres candidatos queda segundo, y pierde 1–7. Sirve de alarma barata; no reemplaza al juez.

## 45. Ejercicio 4: la versión 1
*Ejercicio 4 · 1 de 3 · ~0:45 · desde el minuto 25:50*

El Ejercicio 4. La versión 1, la densa: el coseno del embedder sobre las descripciones, con el filtro por kind. Su limitación, medida: entre productos casi iguales, el primero es el anotado el 53 por ciento de las veces, y en una de cada cinco piezas el correcto no llega a los cinco candidatos. **→** Un caso: se busca un almohadón blanco con hojas negras, y la versión 1 trae almohadones blancos y negros; el anotado quedó sexto. Y había información sin usar: BM25, contando palabras (0,517), y la foto sola (0,508) rendían como el embedder, fallando en cosas distintas.

## 46. Ejercicio 4: la versión 2
*Ejercicio 4 · 2 de 3 · ~0:35 · desde el minuto 26:35*

El cambio es una línea de configuración: rag.hybrid pasa de una lista vacía a BM25 y SigLIP 2. ¿Por qué este cambio? Sale de una limitación medida; es una técnica de Advanced RAG, búsqueda híbrida y multimodal; y corre local, sin llamadas nuevas. **→** La búsqueda ahora promedia tres puntajes estandarizados: el coseno con la descripción, que ya estaba; BM25, las palabras; y SigLIP 2, la foto. En el caso del almohadón, ahora el anotado sale primero.

## 47. Ejercicio 4: resultados
*Ejercicio 4 · 3 de 3 · ~0:50 · desde el minuto 27:10*

Sobre el ground truth: hit@1 pasa de 0,530 a 0,605, y hit@5, lo que ve el que elige, de 0,790 a 0,825. Los intervalos de la diferencia no tocan el cero, y con los otros dos redactores la mejora se repite. De punta a punta, en los 11 ambientes: la versión 2 gana 5, empata 6 y no pierde ninguno. Los productos útiles pasan de 0,68 a 0,74. **→** Con once ambientes, cinco a cero da p igual a 0,06. La versión 2 es hoy la búsqueda del flujo: clara en el set de evaluación; no peor, probablemente mejor, en la tarea real. **→** El generador da casi lo mismo; la imagen reconoce 31 de 75: es una visualización.

## 48. Exp. 16: Qué modelo elige
*Experimentos · 16 · ~0:40 · desde el minuto 28:00*

Hasta acá elige Opus. ¿Cuánto se pierde con uno más chico? Mismo paso y mismo prompt, con Sonnet y con Haiku. En el set de IKEA se pierde poco: Opus 0,687, Sonnet 0,668 y Haiku 0,647. De punta a punta, más: el juez prefiere a Opus 9 a 0 contra Sonnet y 8 a 1 contra Haiku. Ese juez es Opus; lo revisamos en la que sigue. Una lista cuesta 14 centavos con Opus, 6 con Sonnet y menos de uno con Haiku. Sigue Opus: el camino no cambia.

## 49. Exp. 17: Qué modelo juzga
*Experimentos · 17 · ~0:35 · desde el minuto 28:40*

¿Y un juez más chico? Sonnet y Haiku juzgaron los mismos 44 pares de listas que Opus. Casi nunca lo contradicen, 2 y 2 veces: el resto de las diferencias son empates. Pero son menos coherentes: si se invierte el orden de las listas, Opus mantiene el veredicto en el 82% de los ambientes; Sonnet, en el 61, y Haiku, en el 64. Sigue juzgando Opus. Lo que falta es un juez de otro proveedor.

## 50. Exp. 18: Qué modelo dibuja
*Experimentos · 18 · ~0:35 · desde el minuto 29:15*

El modelo de imagen nunca lo habíamos puesto a prueba. Misma lista, mismo prompt, un intento cada uno: Nano Banana 2 contra tres de OpenAI. gpt-image-2 empata: reconoce el producto exacto en 42 de cada 100, contra 44, y conserva el cuarto en 7 de 11, contra 7. Pero cuesta 11 centavos, contra 8. gpt-image-1.5 y el mini quedan abajo: reconocen 38 y 23 de cada 100. Sigue Nano Banana 2: con gpt-image-2 la decisión no cambiaría.

## 51. Exp. 18: lo que se ve
*Experimentos · 18 · ~0:20 · desde el minuto 29:50*

Así se ve, en dos ambientes; a la izquierda, la foto vacía. Nano Banana 2 y gpt-image-2 amoblan esa misma foto. gpt-image-1.5 cambia el encuadre, y el mini vuelve a dibujar el cuarto entero, con otra cámara y otra luz. Para mostrarle a alguien su propio ambiente, eso no sirve.

## 52. Exp. 19: El embedding de OpenAI
*Experimentos · 19 · ~0:40 · desde el minuto 30:10*

Faltaba un embedding pago: cambiamos Qwen3, local, por el más grande de OpenAI, solo en la parte densa. Sola, la densa sube 0,05 de hit@1. Dentro de la híbrida, 0,02, y con los otros dos redactores, casi cero: la léxica y la foto ya cubren mucho. De punta a punta, el juez elige la de OpenAI 6 a 0, con 5 empates; el piso de ruido era 3 a 3. Embeber todo costó 5 centavos. Es la versión 3, y va al final para que todo lo anterior quede medido con Qwen3.

## 53. Limitaciones
*Cierre · ~0:30 · desde el minuto 30:50*

Del sistema: no dice «no hay», pone lo más parecido sin avisar; el tamaño no se puede verificar, porque pocas fichas tienen medidas; la imagen es una visualización; y el generador afirma maderas que no ve. **→** De la evaluación, las advertencias que ya vimos, más dos: el pedido abierto no está evaluado, y el que elige no es determinístico. Ninguna invalida la lista, pero acotan cuánto podemos afirmar.

## 54. Trabajo futuro
*Cierre · ~0:40 · desde el minuto 31:20*

Lo próximo es del RAG y de cómo lo medimos: que el sistema diga «no hay»; consultas de prueba escritas por personas, con un conjunto apartado, y nuestro voto a ciegas para validar al juez; un juez de otro proveedor; y pasarle los materiales al que elige. Más lejos: medidas reales del ambiente y un catálogo actual. **→** Y fuera del RAG hicimos una prueba: vaciamos un living real y lo volvimos a amoblar con sus muebles. Es un solo cuarto: solo se sostiene que indicarle dónde va cada mueble ayuda.

## 55. Conclusiones
*Cierre · ~0:45 · desde el minuto 32:00*

Uno: lo que más pesa es la base de conocimiento y cómo se escribe la consulta; el embedder casi no importa. **→** Dos: la versión 2 es la búsqueda híbrida: suma en el ground truth y de punta a punta gana 5, empata 6 y no pierde. **→** Tres: la búsqueda gana 7 a 0 contra el azar, y empata contra el catálogo entero en el contexto: RAG no hace mejor la lista, es la arquitectura que escala. **→** Cuatro: medir bien fue la mitad del trabajo; nos hizo cambiar el número de cabecera. **→** Y cinco: la lista es confiable; la imagen es una visualización.

## 56. Gracias
*Portada · ~0:05 · desde el minuto 32:50*

Gracias. ¿Preguntas?

## Anexo A: el prompt de la descripción
*Anexo · no se pasa: se abre con la A desde su lámina*

Si preguntan qué recibe el modelo que describe: las fotos del producto, y en el texto su tipo, su nombre y sus medidas, que son los marcadores en color. Las medidas le dan la escala, pero no las puede escribir. Con la A se vuelve al recorrido.

## Anexo B: cuánto cuesta
*Anexo · no se pasa: se abre con la A desde su lámina*

Costos, del registro de gastos. Un pedido cuesta unos 29 centavos de dólar: 6 el plan, 14 la elección y 8 la imagen. Buscar no cuesta nada: todo corre local. **→** El trabajo entero costó 64 dólares; lo que más costó fue evaluar el reranking con un VLM. Cada llamada paga queda registrada con su costo, tokens y latencia, con topes por cuenta, y lo ya pagado queda en caché.

## Anexo C: lo que cuesta cada opción
*Anexo · no se pasa: se abre con la A desde su lámina*

Lo que cuesta cada opción. Describir un producto por la API, US$0,007, una vez. La escena escrita por el LLM suma US$0,056 por pedido; la plantilla, nada. Reordenar con un VLM, US$0,02 por búsqueda. Y elegir: entre 5 con foto, US$0,145; con el catálogo entero, US$0,12 con la caché caliente y US$1,42 sin caché.

## Anexo D: las fotos de los ambientes
*Anexo · no se pasa: se abre con la A desde su lámina*

Las 6 fotos públicas de los ambientes vacíos, con su autor y su licencia. Las otras son de departamentos reales, de uso privado.

## Anexo E: el prompt del juez de faithfulness
*Anexo · no se pasa: se abre con la A desde su lámina*

Si preguntan cómo juzga: le damos la foto del ambiente, la de cada producto elegido con su línea, el pedido y el porqué. Parte el porqué en afirmaciones y marca cada una. Con la A se vuelve al caso.

## Anexo F: el prompt del juez de listas
*Anexo · no se pasa: se abre con la A desde su lámina*

Si preguntan cómo compara: ve la foto, el pedido y las dos listas con la foto de cada producto; califica cada producto, puntúa cada lista en tres criterios y elige. Con la A se vuelve al caso.

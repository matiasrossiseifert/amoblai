# Guion de la presentación (amoblai)

Generado por `docs/presentacion/build.py` junto con `amoblai.html`: los números salen de los mismos resultados que las slides y los extractos de los prompts, de los archivos de `src/amoblai/prompts/`. 44 slides, unos 31 minutos (30:51); son unas 4.200 palabras, a 135 por minuto.

**El recorrido** (slides 5 a 17). Arriba de cada lámina va el mapa de las once fases: la fase de la que se habla, encendida; las ya vistas, marcadas. Se sigue un mismo pedido real, con la configuración final (un loft de estilo industrial, sobre una foto pública), de la foto a la lista. El mismo mapa vuelve en la slide 26 con un pin por experimento sobre la fase a la que le hizo la pregunta (lleno: con lámina propia; hueco: de trámite), y cada lámina de experimento repite ese pin en un minimapa.

**Cómo se pasa.** En cada experimento, primero se ve solo el porqué, la pregunta y qué se comparó. **Se cuentan esas dos cosas antes de avanzar.** La flecha (o espacio) muestra los resultados; otra flecha, la decisión. Flecha atrás vuelve un paso. Con `amoblai.html?todo` se ve todo de entrada (para revisar o imprimir).

**Reparto sugerido** (a definir entre los tres):
- Parte 1: slides 1 a 17 (Portada → Sale la lista de compra y el ambiente amoblado), unos 10 min.
- Parte 2: slides 18 a 30 (De buscar por imagen a RAG por texto, y otros tres desafíos → El camino: de 0,11 a 0,60 de hit@1, un cambio por paso), unos 10 min.
- Parte 3: slides 31 a 44 (¿Error, o el mismo mueble en otro color? → Conclusiones), unos 11 min.

Si falta tiempo, se pueden pasar rápido las dos láminas de trámite y la de costos (las marcadas con *).

## 1. Portada
*~0:21 min · desde el minuto 0:00*

Somos Juan Bautista, Matías y Junior. amoblai responde una pregunta concreta: tengo este ambiente vacío, ¿qué compro y cómo queda? Sacás una foto, escribís qué querés, y te devuelve una lista de productos reales de un catálogo y la imagen del mismo ambiente con esos productos.

## 2. ¿Qué compro para este ambiente, y cómo queda?
*El problema · ~0:24 min · desde el minuto 0:21*

Cuando te mudás a un lugar vacío tenés que decidir qué comprar sin poder verlo puesto. Los catálogos muestran cada mueble suelto, sobre fondo blanco, y las fotos de ambientes muestran la casa de otro. Queremos responder, para este ambiente y este pedido: qué productos reales van, cuántos, y cómo queda el ambiente con ellos.

## 3. Foto + pedido → lista de compra + imagen
*El producto · ~0:30 min · desde el minuto 0:45*

Así se usa. La entrada es una foto del ambiente y un pedido en texto libre, como este: un rincón de lectura con una biblioteca alta de madera oscura. La salida son dos cosas: la lista de compra, con productos reales del catálogo, acá 7, entre IKEA y Amazon, y la foto del mismo ambiente con esos productos puestos.

## 4. Recomendaciones atadas a productos que existen
*Por qué RAG · ~0:48 min · desde el minuto 1:15*

¿Por qué un RAG? Por los tres desafíos de la clase. Información actualizada: el catálogo cambia y el modelo no se reentrena; un producto nuevo es una fila más en el índice. Información personalizada: el LLM no conoce estos 1.502 productos; la búsqueda le trae cinco candidatos reales por pieza. Y sin alucinaciones: un LLM solo recomienda un sillón que nadie vende, y un modelo de imagen solo inventa los muebles; acá la lista solo puede tener productos que trajo la búsqueda, y la imagen se genera desde sus fotos. No es un Q&A: la consulta es una foto y un pedido abierto, y hay dos generaciones aumentadas, la lista y la imagen.

## 5. El recorrido
*Parte 1 · ~0:06 min · desde el minuto 2:03*

Primero, el recorrido: todo el pipeline, fase por fase, con un mapa que se va encendiendo.

## 6. Once fases: una vez offline, y por cada pedido
*El recorrido · el mapa · ~0:39 min · desde el minuto 2:09*

Este es el mapa completo, con dos pipelines. Arriba, lo que se hace una vez, offline: el catálogo, la descripción de cada producto y el índice. Abajo, lo que pasa en cada pedido: entran la foto y el pedido, el plan decide las piezas, la búsqueda trae candidatos, la elección arma la lista, y después la escena, la imagen y el control. Por pedido se pagan solo tres llamadas: Opus en el plan y en la elección, y Nano Banana 2 en la imagen. Lo demás corre local.

## 7. Dos catálogos de productos reales, con foto
*El recorrido · fase 1 de 11 · Catálogo · ~0:36 min · desde el minuto 2:48*

Fase uno, el catálogo. Son dos. El dataset de IKEA: de sus 2.191 productos empezamos con 268 muebles, lo ampliamos a 855 de living y comedor y, revisado mirando cada foto, quedaron 819. Y Amazon Berkeley Objects, listados reales de Amazon: de casi 150 mil quedaron 683. El flujo usa los dos, 1.502 productos. De cada uno guardamos las fotos, el tipo, el kind y las medidas cuando hay. Así viene un sofá de IKEA: el texto es marketing y no tiene medidas.

## 8. Un VLM mira cada foto y escribe el producto en 8 líneas
*El recorrido · fase 2 de 11 · Descripción · ~0:42 min · desde el minuto 3:24*

Fase dos: la descripción. Un VLM mira la foto de cada producto y lo escribe en ocho líneas fijas: tipo, uso, estilo, materiales, colores, forma, sensación y con qué combina. Es el mismo sofá: a la izquierda, lo que dice IKEA; en el medio, lo que escribió el modelo. El prompt pide exactamente esas ocho líneas, sin marca, precio ni medidas, y nada de lo que el producto no es, porque el embedding no entiende la negación. Para Amazon usamos la misma receta, por la API. Es el preprocesamiento que más pesa: lo mide el experimento 1.

## 9. Un vector por producto: Qwen3, local, en ChromaDB
*El recorrido · fase 3 de 11 · Índice · ~0:39 min · desde el minuto 4:06*

Fase tres: el índice. Se embebe la descripción entera, un documento por producto, con Qwen3-Embedding, local, en CPU: 1.024 dimensiones, a ChromaDB, con la metadata de los filtros. Embedder, splitting, dimensión y base vectorial son las preguntas de trámite, por eso su pin va hueco: las contestamos juntas más adelante. Para la búsqueda híbrida se suman dos índices sobre los mismos productos: uno léxico, BM25 sobre las palabras de las descripciones, y uno por foto, con SigLIP 2, que pone la foto y el texto de la consulta en un mismo espacio.

## 10. Entra una foto del ambiente vacío y un pedido libre
*El recorrido · fase 4 de 11 · Foto + pedido · ~0:18 min · desde el minuto 4:45*

Fase cuatro, lo que entra: una foto del ambiente vacío y un pedido en texto libre. Vamos a seguir este loft hasta el final: un pedido de estilo industrial, sobre una foto pública, con la configuración con la que entregamos.

## 11. El plan descompone el pedido y escribe una ficha por pieza
*El recorrido · fase 5 de 11 · Plan · ~0:54 min · desde el minuto 5:03*

Fase cinco, el plan. Opus recibe la foto y el pedido y hace de diseñador: lee el ambiente, descompone el pedido en piezas y, para cada una, da el kind, que va a ser el filtro, la medida máxima, y la consulta: el producto ideal escrito en las mismas ocho líneas que el catálogo. En los términos de la clase es query expansion con respuesta hipotética, HyDE: en la base no hay preguntas, hay respuestas, así que la consulta se escribe como una respuesta. Más la descomposición del pedido: una consulta por pieza. Del “sofá de cuero marrón envejecido” sale esta pieza: kind sofá, hasta 240 centímetros, y su ficha. Propuso 7 piezas. Cuánto suma escribir la ficha lo mide el experimento 2.

## 12. Filtro por kind, después búsqueda híbrida: 5 candidatos
*El recorrido · fase 6 de 11 · Búsqueda · ~0:51 min · desde el minuto 5:57*

Fase seis, la búsqueda. Para cada pieza, primero un filtro duro de metadata: el kind del plan y las medidas máximas, con margen porque salen de una foto. Acá quedan 76 de los 1.502 productos. Sobre esos, tres puntajes: el coseno de Qwen3 entre la ficha y la descripción; BM25, las palabras de la ficha que están en la descripción; y SigLIP 2, la ficha en una frase contra la foto del producto. Cada puntaje se estandariza y se promedian: es la búsqueda híbrida, la versión 2 del sistema. Quedan los cinco mejores: estos sofás, 4 de Amazon y 1 de IKEA.

## 13. Opus ve el cuarto y los 5 de cada pieza, y arma la lista
*El recorrido · fase 7 de 11 · Elección · ~0:48 min · desde el minuto 6:48*

Fase siete, la elección: es la generación de la lista, la G del RAG. Opus ve la foto del ambiente y los cinco candidatos de cada pieza, acá 36 imágenes, cada uno con su id, su tipo y su medida. El prompt le pide elegir las piezas juntas, como un solo look, y decir cuántas unidades; cero deja una pieza afuera. Solo puede elegir productos que trajo la búsqueda: si no, el código rechaza la respuesta. No es un reranker: arma un conjunto para este cuarto. Acá tomó el primero de la búsqueda en 3 de las 7 piezas; la biblioteca era el quinto candidato.

## 14. El prompt de la imagen: una plantilla, sin LLM
*El recorrido · fase 8 de 11 · Escena · ~0:39 min · desde el minuto 7:36*

Fase ocho, la escena: el prompt para el modelo de imagen. Probamos dos caminos: que Opus escriba dónde va cada producto, o una plantilla sin LLM, que se completa con la lista. La última versión de la plantilla es estricta: es una edición de la foto del cliente, con la misma cámara, las mismas paredes y ventanas, y exactamente estos productos. Las comparamos en los once ambientes, con las mismas listas: empatan en productos reconocidos y en cuartos conservados. Nos quedamos con la plantilla, que ahorra una llamada.

## 15. Nano Banana 2 edita la foto con las fotos de los productos
*El recorrido · fase 9 de 11 · Imagen · ~0:24 min · desde el minuto 8:15*

Fase nueve, la imagen. Nano Banana 2, en modo edición: recibe la foto del ambiente, las fotos de los productos y el prompt. Cuesta 8 centavos por intento. Acepta 14 imágenes, así que muestra hasta 13 productos; el resto queda en la lista. El modelo no lo elegimos con un experimento: esa comparación quedó sin correr.

## 16. ¿Es el mismo cuarto? SIFT lo controla, y si no, reintenta
*El recorrido · fase 10 de 11 · Control · ~0:45 min · desde el minuto 8:39*

Fase diez, el control. Comparamos la foto original con la generada con SIFT y RANSAC: si reencuentra al menos 50 puntos del cuarto y la cámara casi no se movió, se acepta; si no, se genera otra, hasta 3 veces. Los umbrales están puestos a mano. El loft pasó al primer intento. Este otro pedido, un living clásico, no: el modelo reencuadró hacia la chimenea en los tres intentos, y se entrega el mejor, marcado. En las 11 corridas finales pasan 7, todas al primer intento; en las otras 4 fallaron los tres. El control detecta; reintentar pocas veces arregla.

## 17. Sale la lista de compra y el ambiente amoblado
*El recorrido · fase 11 de 11 · Lista + imagen · ~0:24 min · desde el minuto 9:24*

Y fase once, lo que sale: la lista de compra, con productos reales y cuántos de cada uno, acá 5 de Amazon y 2 de IKEA, y la foto del mismo ambiente con ellos. Este pedido costó unos 26 centavos de Claude y 8 de la imagen. Cada fase deja su archivo en la carpeta de la corrida.

## 18. De buscar por imagen a RAG por texto, y otros tres desafíos
*Desafíos · ~0:54 min · desde el minuto 9:48*

Los desafíos. El más grande fue cambiar la arquitectura que nos aprobaron. La propuesta era generar primero una imagen amoblada, recortar cada mueble y buscar en el catálogo el más parecido, por imagen. Construimos y medimos su buscador sobre el mismo ground truth: encontraba primero el 43 por ciento de los productos anotados, contra 55 buscando por texto. Con eso, y con una generación de imagen menos por pedido, cambiamos a RAG por texto. Ojo: esa versión nunca corrió de punta a punta; comparamos buscadores, no sistemas. Los otros tres: el catálogo traía fotos de otro producto y hubo que revisarlo a mano; no hay ground truth de la tarea real; y el modelo de imagen rehace el cuarto.

## 19. Cómo evaluamos
*Parte 2 · ~0:06 min · desde el minuto 10:42*

Antes de los experimentos, cómo evaluamos: qué mide cada número y cuánto creerle.

## 20. Ambientes IKEA anotados y ambientes vacíos reales
*Cómo evaluamos · los datos · ~0:45 min · desde el minuto 10:48*

Usamos dos bancos de prueba, que miden cosas distintas. Para la búsqueda, 65 ambientes de IKEA con sus productos anotados. Por cada mueble visible, un subagente escribió la consulta como la escribiría el plan, sin ver el catálogo: 864 consultas, 549 con su producto en el catálogo. Es un banco de producto conocido: quien escribe está viendo el mueble, así que mide el índice, no la recomendación. Para el flujo entero, 11 ambientes vacíos reales, cada uno con su pedido: ahí no hay ground truth, y un juez compara a ciegas las listas de dos configuraciones, en los dos órdenes.

## 21. El buscador: ¿trae el producto anotado, y arriba?
*Cómo evaluamos · el retriever · ~0:45 min · desde el minuto 11:33*

Las métricas del buscador, con el valor de hoy. hit@k: si el producto anotado está entre los k primeros. El titular es hit@5, porque son los cinco candidatos que ve el que elige: 0,825. Para comparar dos métodos usamos la diferencia pareada: las mismas consultas, la diferencia media y su intervalo de 95 por ciento, por bootstrap de ambientes. Si no toca el cero, no es ruido. Mirar el intervalo de cada método por separado nos había hecho leer mejoras que eran ruido. Las de la clase, context precision y NDCG, acá repiten al MRR; context recall es por ambiente.

## 22. El generador: faithfulness 0,88 y answer relevance 0,70
*Cómo evaluamos · el generador y los jueces · ~0:57 min · desde el minuto 12:18*

El generador es el paso que elige y explica. Faithfulness: partimos el porqué en afirmaciones, y un juez dice cuáles se infieren de lo que el generador vio. Da 0,88: 313 de 356. Lo que no se sostiene es casi siempre la especie de la madera, que afirma sin verla escrita. Answer relevance: un juez que no ve el pedido escribe los pedidos que esa lista contesta. Da 0,70, contra 0,56 con pedidos escritos para otras listas. Estas métricas las rehicimos, y es una historia de data leakage: el prompt del juez traía de ejemplo “un living nórdico y cálido”, que era justo como empezaba el pedido evaluado, y lo copiaba. Y sobre los jueces: validado contra el ground truth hay uno solo; el de listas se controla con los dos órdenes.

## 23. La imagen: 31 de 75 productos reconocidos, 7 de 11 cuartos
*Cómo evaluamos · la imagen · ~0:48 min · desde el minuto 13:15*

La imagen la medimos sobre las 11 corridas finales, no sobre la mejor. Primero: ¿son esos productos? Detectamos cada mueble, lo recortamos y lo comparamos con las fotos del catálogo de su tipo: reconocido, si el más parecido es el de la lista. En el loft, el sofá, la biblioteca y la lámpara salen primeros; la alfombra, no. En total se reconocen 31 de 75, el 41 por ciento, aunque aparecen 71. Segundo: ¿es ese cuarto? El control pasa en 7 de 11. O sea: la lista es confiable; la imagen es una visualización, que acierta el producto exacto cuatro de cada diez veces.

## 24. Las trampas, dichas en voz alta
*Cómo evaluamos · cuánto creerle · ~0:39 min · desde el minuto 14:03*

Y las trampas, dichas en voz alta. Uno: el banco de la búsqueda es de producto conocido; en el flujo real el plan imagina el producto, no lo ve. Dos: el mismo modelo escribe las consultas y las descripciones, con el mismo molde; por eso contar palabras rinde casi como el embedder. Tres: no hay conjunto apartado. Y cuatro: de punta a punta son 11 ambientes y el juez es el mismo modelo que elige; con la misma configuración corrida dos veces reparte tres a tres, así que lo que cuenta es la asimetría. Por eso leemos las diferencias grandes, y las de dos puntos, no.

## 25. Experimentos
*Parte 3 · ~0:09 min · desde el minuto 14:42*

Ahora los experimentos, por cuánto importan. Los que sostienen una decisión tienen su lámina; los de trámite van juntos al final.

## 26. Quince experimentos: ocho con lámina propia, siete de trámite
*Experimentos · el mapa · ~0:39 min · desde el minuto 14:51*

El mismo mapa, con los experimentos encima: cada pin es una pregunta que le hicimos a una parte del sistema. Los llenos, del 1 al 8, tienen lámina propia. Dos de ellos, el 4 y el 8, no miden una fase: miden al banco de prueba. Los huecos, del 9 al 15, son los de trámite: embedder, dimensión, splitting, base vectorial, filtros, rerankers de texto y la escena. Y dos cosas no las decidió ningún experimento: el modelo de imagen y los umbrales del control.

## 27. Qué se indexa
*Experimento 1 · ~0:54 min · desde el minuto 15:30*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): El texto de IKEA es una frase de marketing, y la gente pide estilo, color y materiales, que están en la foto. ¿Vale la pena describir cada producto?
2. **Qué se comparó:** Indexamos dos textos, con todo lo demás fijo: el texto del vendedor y la descripción de ocho líneas. La consulta, una frase corta sin reescribir, para medir un solo cambio.
3. **→ Resultados** (flecha): Con el texto del vendedor, hit@1 da 0,11; con la descripción, 0,30: casi el triple, y hit@5 pasa de 0,30 a 0,60. La diferencia es pareada y su intervalo no toca el cero. Con la consulta escrita como ficha, la diferencia supera 0,4.
4. **→ Decisión** (flecha): Se indexa la descripción hecha desde la foto. Es el preprocesamiento que más pesa de todo el trabajo.

## 28. Cómo se escribe la consulta
*Experimento 2 · ~1:06 min · desde el minuto 16:24*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): El plan no busca con el pedido: escribe el producto ideal en las ocho líneas del catálogo. Es la técnica de Advanced RAG del flujo, y no la habíamos medido contra no hacerla: la comparábamos con buscar solo con el nombre del kind, que es azar por construcción.
2. **Qué se comparó:** La ficha contra la frase natural, sin reescribir: las pocas palabras con que el redactor nombró la pieza. Con la búsqueda del flujo, y también contra la foto del producto.
3. **→ Resultados** (flecha): La ficha da 0,530 y la frase natural 0,324: suma +0,21, con un intervalo lejos del cero. Y lo que no esperábamos: contra la foto, la frase sin reescribir da 0,479, casi lo mismo que la ficha. El texto necesita que la consulta hable como el catálogo; la foto, casi no.
4. **→ Decisión** (flecha): El plan sigue escribiendo la ficha. Y queda un argumento para la búsqueda híbrida: las dos rutas fallan distinto.

## 29. Búsqueda léxica, por foto e híbrida
*Experimento 3 · ~1:06 min · desde el minuto 17:30*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): Dos dudas de fondo sobre el índice. ¿El embedder neuronal hace falta, o alcanza con contar palabras? Y el catálogo tiene fotos: la clase dio dos rutas, pasar la imagen a texto, que es lo que hacíamos, o embeberla directamente. Esa nunca la habíamos medido.
2. **Qué se comparó:** Tres buscadores sobre las mismas consultas: el denso, Qwen3 sobre las descripciones; el léxico, BM25; y por foto, SigLIP 2, con la consulta en una frase contra la foto del producto. Y sus fusiones.
3. **→ Resultados** (flecha): Solos, los tres rinden parecido: 0,530, 0,517 y 0,508. Ni el embedder le gana a contar palabras, ni describir le gana a embeber la foto. Pero se equivocan en cosas distintas: fusionados dan 0,605, +0,075 de hit@1, con un intervalo que no toca el cero.
4. **→ Decisión** (flecha): La búsqueda híbrida pasa a ser la del flujo: es la versión 2, el Ejercicio 4. Usa las dos rutas de la clase a la vez.

## 30. El camino: de 0,11 a 0,60 de hit@1, un cambio por paso
*Experimentos · la ablación incremental · ~0:51 min · desde el minuto 18:36*

La ablación incremental: un cambio por paso, con su diferencia pareada. Arrancamos del RAG naive, el texto del vendedor y la consulta sin reescribir: 0,11. Describir cada producto desde su foto lo lleva a 0,30; escribir la consulta como una ficha, a 0,54. Esos dos pasos son los que más pesan. El filtro por kind no suma en este banco: lo usamos por otra razón, que vemos en los de trámite. Con el filtro, esa es la versión 1 del flujo. Con la búsqueda léxica, 0,58; con la foto, 0,60: la versión 2. Aparte queda el 0,69 que mostrábamos antes: es un VLM reordenando el top-10, una técnica aislada, no un escalón del flujo.

## 31. ¿Error, o el mismo mueble en otro color?
*Experimento 4 · ~0:42 min · desde el minuto 19:27*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): hit@1 exige el producto anotado exacto, y el catálogo está lleno de variantes del mismo modelo. ¿Cuánto de lo que cuenta como error es el mismo mueble en otro color?
2. **Qué se comparó:** Tres niveles de correcto para el primer candidato: el producto exacto, el mismo modelo, y uno que sirve según un juez.
3. **→ Resultados** (flecha): El exacto, 0,53; el mismo modelo, 0,62; uno que sirve, 0,78. Una de cada 5 veces que el primero falla es otra variante del mismo mueble.
4. **→ Decisión** (flecha): El banco subestima el nivel, no el orden: la comparación entre buscadores no cambia. Usamos el exacto para comparar, y los tres juntos para decir cuánto sirve.

## 32. Elegir con un VLM, y cuántos candidatos
*Experimento 5 · ~1:03 min · desde el minuto 20:09*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): hit@10 es 0,89 pero hit@1 0,54: el correcto casi siempre está entre los diez primeros, pero no primero. ¿Mirar las fotos ordena mejor que el coseno? ¿Y cuántos candidatos conviene pasar?
2. **Qué se comparó:** Opus recibe la consulta y las fotos de los diez primeros, y los ordena. De ahí sale gratis la curva: si eligiera entre los primeros k, ¿acertaría? La punteada es el techo.
3. **→ Resultados** (flecha): Reordenando el top-10, hit@1 pasa de 0,535 a 0,687. De 3 a 5 candidatos la elección sube 3 puntos, también significativo; a partir de 8 se aplana.
4. **→ Decisión** (flecha): Cinco candidatos por pieza. Pero ojo: es una técnica aislada, no un paso del flujo. Ese reranker ordena contra la consulta, sin ver el ambiente; el que elige en el flujo arma un conjunto para el cuarto, y no tiene ground truth. Por eso este número no es el del sistema.

## 33. Qué catálogo
*Experimento 6 · ~1:06 min · desde el minuto 21:12*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): IKEA es de 2013, con una sola estética, la nórdica. Amazon Berkeley Objects tiene listados reales, con medidas, pero no tiene ambientes anotados: hay que medirlo de punta a punta.
2. **Qué se comparó:** Los mismos ambientes, pedidos y plan; cambia solo el catálogo. El juez compara las dos listas a ciegas, en los dos órdenes.
3. **→ Resultados** (flecha): En nuestros cinco departamentos, con pedidos nórdicos, IKEA le gana a Amazon solo, y los dos juntos empatan con IKEA. Sumamos seis ambientes públicos con otros estilos: ahí, IKEA más Amazon gana 6 a 0. En total, 8 a 2.
4. **→ Decisión** (flecha): Usamos los dos catálogos. Con dos salvedades: 8 a 2 en once ambientes da p igual a 0,11, no es concluyente; y los pedidos de otros estilos los escribimos nosotros, sabiendo qué le falta a IKEA. Muestra que Amazon cubre ese hueco, no cuán frecuente es.

## 34. Con búsqueda, sin búsqueda, o con el catálogo entero
*Experimento 7 · ~1:15 min · desde el minuto 22:18*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): Es el con y sin retrieval del flujo, con dos extremos. Uno: darle al que elige cinco productos al azar del kind pedido. Dos, la pregunta incómoda: si el catálogo entra en el contexto, ¿hacía falta RAG?
2. **Qué se comparó:** Mismo plan, mismo modelo que elige, mismo juez. Contra el azar, en 7 ambientes. Y contra el catálogo entero en el prompt, las 1.502 fichas en texto, en los 11.
3. **→ Resultados** (flecha): Contra el azar, 7 a 0, con los 14 votos. Contra el catálogo entero, 5 a 5, con los mismos productos útiles: empatan. Y con el catálogo en la caché de prompt cuesta lo mismo; sin caché, diez veces más.
4. **→ Decisión** (flecha): La búsqueda hace falta cuando el que elige ve cinco productos, y empata cuando puede leerlos todos. Con mil quinientos productos, RAG no hace mejor la lista: lo elegimos porque escala, y porque no depende del tráfico ni de un modelo de contexto largo.

## 35. Tres redactores
*Experimento 8 · ~0:33 min · desde el minuto 23:33*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): Las consultas de evaluación las escribió un modelo. La clase pidió promedio y desvío: ¿cuánto cambia el número sin cambiar el sistema?
2. **Qué se comparó:** Las mismas consultas, escritas otras dos veces por subagentes independientes.
3. **→ Resultados** (flecha): La versión 1 da 0,539 ± 0,025; la versión 2, 0,604 ± 0,009. La mejora de la híbrida se repite con los tres.
4. **→ Decisión** (flecha): El número se mueve unos dos puntos y medio según quién escribe: por eso no leemos diferencias de dos puntos.

## 36. De trámite: las cuatro preguntas sobre el índice *
*Experimentos · de trámite (1 de 2) · ~0:48 min · desde el minuto 24:06*

Los de trámite: lo que la cátedra dijo que iba a preguntar, con la respuesta corta. Embedder: Qwen3 solo se sostiene sobre BGE; contra contar palabras no se distingue, porque consultas y descripciones comparten el molde. Dimensión: con 512 da lo mismo que con 1.024, y con 1.500 productos la memoria no pesa. Splitting: no partimos, un producto es un documento; lo que importa es qué líneas lo componen, y son las de lo que se ve: colores y forma. Base vectorial: ChromaDB da el mismo top-10 que la búsqueda exacta en las 864 consultas; la usamos por la persistencia y los filtros.

## 37. De trámite: filtros, rerankers de texto, el catálogo y la escena *
*Experimentos · de trámite (2 de 2) · ~0:48 min · desde el minuto 24:54*

Filtros de metadata: en este banco no suman, y el de kind cuesta dos puntos de hit@5. Lo usamos igual, por algo que el banco no mide: en los pedidos reales, sin él, el 11 por ciento de los candidatos sería de otro kind; pedís un sillón y aparece una silla de comedor. El de medidas cambia uno de cada once candidatos, sin evidencia de que mejore la lista. Rerankers de texto: probamos el MiniLM de la clase y Qwen3-Reranker, y los dos empeoran, porque releen el texto que ya usó la búsqueda. Y el catálogo: ampliarlo y revisarlo fueron decisiones de datos, y sumar Amazon le cuesta al buscador 3,5 puntos de hit@5. Y la escena: escrita por un LLM empata con la plantilla en los once ambientes; queda la plantilla.

## 38. Versión 1: el índice lee la descripción, no ve el producto
*Ejercicio 4 · 1 de 3 · la versión anterior y su limitación · ~0:54 min · desde el minuto 25:42*

El Ejercicio 4. La versión 1 es el sistema hasta el 11 de noviembre: la búsqueda era el coseno del embedder sobre las descripciones, con el filtro por kind. Su limitación, medida: entre productos casi iguales, el primero es el anotado el 53 por ciento de las veces, y en una de cada cinco piezas el correcto no llega a los cinco candidatos. Falla donde hay muchos parecidos: alfombras y deco. Un caso: se busca un almohadón blanco con hojas negras, y la versión 1 trae almohadones blancos y negros; el anotado quedó sexto. El índice lee una descripción, pero no ve el producto ni aprovecha las palabras exactas. Y BM25 y la foto sola rendían como el embedder, fallando en cosas distintas.

## 39. Versión 2: búsqueda híbrida, una línea de configuración
*Ejercicio 4 · 2 de 3 · el cambio y la configuración · ~0:48 min · desde el minuto 26:36*

El cambio es una línea de configuración: rag.hybrid pasa de una lista vacía a BM25 y SigLIP 2. La búsqueda ahora calcula tres puntajes para cada producto que pasa el filtro: el coseno con la descripción, que ya estaba; BM25, las palabras; y SigLIP 2, la ficha en una frase contra la foto. Se estandarizan y se promedian. ¿Por qué este cambio? Sale de una limitación medida; es una técnica de Advanced RAG, búsqueda híbrida y multimodal; y no cuesta nada por pedido, porque corre local. En el caso del almohadón, ahora el anotado sale primero.

## 40. Resultados: gana en el ground truth y no pierde con el juez
*Ejercicio 4 · 3 de 3 · resultados en las dos versiones · ~1:03 min · desde el minuto 27:24*

Los resultados en las dos versiones. Sobre el ground truth: hit@1 pasa de 0,530 a 0,605, y hit@5, lo que ve el que elige, de 0,790 a 0,825. Las diferencias son pareadas y sus intervalos no tocan el cero; con los otros dos redactores, la mejora se repite. De punta a punta, en los 11 ambientes, con el mismo plan y el juez en los dos órdenes: la versión 2 gana 5, empata 6 y no pierde ninguno. Los productos útiles pasan de 0,68 a 0,74, y el costo es el mismo. Con honestidad: lo del ground truth es claro; de punta a punta son once ambientes, cinco a cero da p igual a 0,06, y en seis el juez no se decide; la misma configuración contra sí misma reparte tres a tres. Clara en el banco; no peor, probablemente mejor, en la tarea real.

## 41. Cuánto cuesta un pedido, y cuánto costó el trabajo *
*Costo · ~0:30 min · desde el minuto 28:27*

Costos, del registro de gastos. Un pedido cuesta unos 28 centavos de dólar: 6 el plan, 14 la elección y 8 la imagen. Buscar no cuesta nada: todo corre local. El trabajo entero costó 45 dólares; lo más caro fue evaluar el reranking con el VLM. Cada llamada paga queda registrada, con topes por cuenta, y lo ya pagado queda en caché.

## 42. Limitaciones
*Cierre · ~0:33 min · desde el minuto 28:57*

Limitaciones. Del sistema: no dice “no hay”, pone lo más parecido sin avisar; el tamaño no se puede verificar; la imagen es una visualización; y el generador afirma maderas que no ve. De la evaluación: el banco de la búsqueda es de producto conocido y no hay conjunto apartado; de punta a punta son 11 ambientes, con un juez sin validar contra personas; y ninguna corrida se repitió.

## 43. Trabajo futuro
*Cierre · ~0:39 min · desde el minuto 29:30*

Trabajo futuro. Lo próximo es del RAG y de cómo lo medimos: que el sistema diga “no hay”; un banco de consultas escrito por personas, con un conjunto apartado; y validar al juez con nuestro voto a ciegas. Más lejos: medidas reales del ambiente y un catálogo actual. Y fuera del RAG hicimos una prueba: vaciamos un living real y lo volvimos a amoblar con sus muebles. Es un solo cuarto; lo único que se sostiene es que indicarle al modelo dónde va cada mueble ayuda.

## 44. Conclusiones
*Cierre · ~0:42 min · desde el minuto 30:09*

Para cerrar. Uno: lo que más pesa es la base de conocimiento y cómo se escribe la consulta; el embedder casi no importa. Dos: la versión 2 es la búsqueda híbrida: suma en el ground truth, sin costo, y de punta a punta gana 5, empata 6 y no pierde. Tres: la búsqueda aporta en la tarea real, 7 a 0 contra candidatos al azar; contra el catálogo entero en el prompt empata: RAG es lo que escala. Cuatro: medir bien fue la mitad del trabajo; nos hizo cambiar el número de cabecera y rehacer las métricas del generador. Y cinco: la lista es confiable; la imagen es una visualización. Gracias.

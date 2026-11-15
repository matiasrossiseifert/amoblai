# Guion de la presentación (amoblai, versión b2)

Generado por `build.py` junto con `presentacion.html`: los números salen de los mismos archivos de resultados que las láminas, y los extractos de los prompts, de `src/amoblai/prompts/`. 46 láminas, unos 30 minutos (29:37); son unas 4.000 palabras, contadas a 135 por minuto.

**Cómo se pasa.** Flecha derecha, espacio o clic: avanza un paso; flecha izquierda: vuelve. F: pantalla completa; O: índice con miniaturas; N: estas notas abajo de la lámina; P: ventana del presentador (lámina actual, la siguiente, notas y reloj, sincronizadas); B: pantalla negra. `presentacion.html?all#/12` muestra la lámina 12 con todos sus pasos; `#/12.2` va al paso 2.

**El recorrido** (láminas 5 a 15) sigue un pedido real con la configuración final, un loft de estilo industrial sobre una foto pública, por las once fases del flujo, con el mapa arriba a la derecha: la fase actual encendida, las vistas con ✓ y el pin de los experimentos que le hicieron una pregunta a esa fase (lleno: con lámina propia; hueco: de trámite). En cada fase: qué entra y qué sale, y el prompt tal cual se manda (extracto, en inglés, con lo importante resaltado) con sus versiones. Ahí no se dan resultados: los números van en cada experimento.

**Los experimentos** van por su ranking (el mapa, en la lámina 23). Los seis principales tienen dos láminas: la oscura es la pregunta, con el porqué y el esquema del flujo con la etapa encendida; con la flecha aparece qué se comparó. **Se cuentan esas dos cosas antes de pasar.** La clara es el resultado: una flecha muestra los resultados, con la diferencia pareada, y otra la decisión, que se imprime como un talón abajo. Los experimentos 4 y 8, que miden al banco de prueba, van en una sola lámina; el camino incremental (lámina 30) resume los tres primeros; y los siete de trámite van juntos en las láminas 37 y 38.

**El Ejercicio 4** son las láminas 39 a 41: la versión 1 y su limitación, el cambio con la configuración antes y después, y los resultados en las dos versiones.

En el texto, **→** marca dónde se avanza un paso. Si falta tiempo, se pueden pasar rápido las dos láminas de trámite y la de costos (las marcadas con *).

**Reparto sugerido** (a definir entre los tres):
- Parte 1: láminas 1 a 15 (Portada → Fase 11: Lista + imagen), unos 9:45.
- Parte 2: láminas 16 a 31 (Desafíos → Exp. 4: ¿Error, o una variante?), unos 10:15.
- Parte 3: láminas 32 a 46 (Exp. 5: Elegir con un VLM, y cuántos → Gracias), unos 9:35.

## 1. Portada
*Portada · ~0:25 · desde el minuto 0:00*

Somos Juan Bautista, Matías y Junior. amoblai responde una pregunta concreta: tengo este ambiente vacío, ¿qué compro y cómo queda? Sacás una foto, escribís qué querés, y te devuelve una lista de productos reales de un catálogo y la imagen del mismo ambiente con esos productos.

## 2. El problema
*El problema · ~0:25 · desde el minuto 0:25*

Cuando te mudás a un lugar vacío tenés que decidir qué comprar sin poder verlo puesto. Los catálogos muestran cada mueble suelto, sobre fondo blanco, y las fotos de ambientes muestran la casa de otro. **→** Queremos responder, para este ambiente y este pedido: qué productos reales van, cuántos, y cómo queda el ambiente con ellos.

## 3. El producto
*El producto · ~0:30 · desde el minuto 0:50*

Así se usa. La entrada es una foto del ambiente y un pedido en texto libre, como este: un loft donde piden un living de estilo industrial, con un sofá de cuero envejecido. **→** La salida son dos cosas: la lista de compra, con productos reales del catálogo, acá 7, entre IKEA y Amazon, y la foto del mismo ambiente con esos productos puestos.

## 4. Por qué RAG
*El producto · ~0:50 · desde el minuto 1:20*

¿Por qué un RAG? Por los tres desafíos de la clase. Información actualizada: el catálogo cambia y el modelo no se reentrena; un producto nuevo es una fila más en el índice. **→** Información personalizada: el LLM no conoce estos 1.502 productos; la búsqueda le trae cinco candidatos reales por pieza, y elige mirando sus fotos y la del cuarto. **→** Y sin alucinaciones: un LLM solo recomienda un sillón que nadie vende, y un modelo de imagen solo inventa los muebles; acá la lista solo puede tener productos que trajo la búsqueda, y la imagen se genera desde sus fotos. No es un Q&A: hay dos generaciones aumentadas, la lista y la imagen.

## 5. El recorrido
*Recorrido · ~0:45 · desde el minuto 2:10*

El sistema, fase por fase, sobre este mapa: once fases en dos pipelines. **→** Las tres primeras corren una vez, offline: el catálogo, la descripción de cada producto y el índice. **→** Las otras ocho corren en cada pedido: el plan decide las piezas, la búsqueda trae candidatos, la elección arma la lista, y después la escena, la imagen y el control. Se pagan solo tres llamadas: Opus en el plan y en la elección, y Nano Banana 2 en la imagen. **→** En cada fase, qué entra, qué sale y el prompt. Y una idea: la respuesta queda atada al catálogo.

## 6. Fase 1: Catálogo
*Recorrido · 1 · ~0:30 · desde el minuto 2:55*

Fase uno, el catálogo: la base de conocimiento. Son dos. El dataset de IKEA: lo ampliamos a 855 productos de living y comedor y, revisado mirando cada foto, quedaron 819. Y Amazon Berkeley Objects, listados reales de Amazon: de casi 150 mil quedaron 683. El flujo usa los dos, 1.502 productos. Así viene una lámpara de IKEA: el texto es marketing y no tiene medidas. Y así un sofá de Amazon, con medidas.

## 7. Fase 2: Descripción
*Recorrido · 2 · ~0:35 · desde el minuto 3:25*

Fase dos: la descripción. Un VLM, Opus 5.5, mira la foto de cada producto y lo escribe en ocho líneas fijas: tipo, uso, estilo, materiales, colores, forma, sensación y con qué combina. El prompt pide exactamente esas ocho líneas, sin marca, precio ni medidas, y nada de lo que el producto no es, porque el embedding no entiende la negación. Este es el sofá de Amazon que vamos a seguir. Es el preprocesamiento que más pesa: lo mide el experimento 1.

## 8. Fase 3: Índice
*Recorrido · 3 · ~0:35 · desde el minuto 4:00*

Fase tres: el índice. Se embebe la descripción entera, un documento por producto, con Qwen3-Embedding, local, en CPU: 1.024 dimensiones, a ChromaDB, con la metadata de los filtros. Embedder, splitting, dimensión y base vectorial son preguntas de trámite: las contestamos juntas más adelante. Para la búsqueda híbrida se suman dos índices sobre los mismos productos: uno léxico, BM25 sobre las palabras de las descripciones, y uno por foto, con SigLIP 2, que pone la foto y el texto en un mismo espacio.

## 9. Fase 4: Foto, pedido y plan
*Recorrido · 4 · ~0:55 · desde el minuto 4:40*

Fases cuatro y cinco. Entra una foto del ambiente vacío y un pedido en texto libre. Vamos a seguir este loft hasta el final: un pedido de estilo industrial, sobre una foto pública. **→** El plan es la primera llamada a Opus, que hace de diseñador: lee el ambiente, descompone el pedido en piezas, acá 7, y para cada una da el kind, que va a ser el filtro, la medida máxima, y la consulta: el producto ideal escrito en las mismas ocho líneas que el catálogo. En los términos de la clase es query expansion con respuesta hipotética, HyDE: en la base no hay preguntas, hay respuestas. Más la descomposición del pedido: una consulta por pieza. Cuánto suma escribir la ficha lo mide el experimento 2.

## 10. Fase 5: Plan
*Recorrido · 5 · ~0:25 · desde el minuto 5:35*

Es el prompt que más reescribimos. La primera versión le dio un sillón a alguien que pidió una silla para su escritorio. La v2 pide la pieza como la nombró el usuario, el kind de una lista cerrada, las medidas máximas y la consulta en ocho líneas. La v3 pide terminar el ambiente, y la v4 saca el tope de piezas.

## 11. Fase 6: Búsqueda
*Recorrido · 6 · ~0:45 · desde el minuto 6:00*

Fase seis, la búsqueda. Para cada pieza, primero un filtro duro de metadata: el kind del plan y las medidas máximas, con margen porque salen de una foto. Acá quedan 76 de los 1.502 productos. Sobre esos, tres puntajes: el coseno de Qwen3 entre la ficha y la descripción; BM25, las palabras de la ficha que están en la descripción; y SigLIP 2, la ficha en una frase contra la foto del producto. Cada puntaje se estandariza y se promedian: es la búsqueda híbrida, la versión 2. Quedan los cinco mejores: 4 de Amazon y 1 de IKEA.

## 12. Fase 7: Elección
*Recorrido · 7 · ~0:45 · desde el minuto 6:45*

Fase siete, la elección: es la generación de la lista, la G del RAG. Opus ve la foto del ambiente y los cinco candidatos de cada pieza, acá 36 imágenes, cada uno con su id, su tipo y su medida. El prompt le pide elegir las piezas juntas, como un solo look, y decir cuántas unidades; cero deja una pieza afuera. Solo puede elegir productos que trajo la búsqueda: si no, el código rechaza la respuesta. No es un reranker: arma un conjunto para este cuarto. Acá tomó el primero de la búsqueda en 3 de las 7 piezas; la biblioteca era el quinto candidato.

## 13. Fase 8: Escena
*Recorrido · 8 · ~0:45 · desde el minuto 7:30*

Fase ocho, la escena: el prompt para el modelo de imagen. Probamos dos caminos: que Opus escriba dónde va cada producto, o una plantilla sin LLM, que se completa con la lista. La plantilla es estricta: una edición de la foto del cliente, con la misma cámara y exactamente estos productos. Las comparamos en los 11 ambientes y empatan: se reconocen 31 productos de 75 con la plantilla y 32 con la escena del LLM, y el ambiente se conserva en 7 y en 8. Nos quedamos con la plantilla: da lo mismo y cuesta una llamada menos.

## 14. Fase 9: Imagen y control
*Recorrido · 9 · ~0:55 · desde el minuto 8:15*

La imagen la hace Nano Banana 2, en modo edición: recibe la foto del ambiente, las fotos de los productos y el prompt. Acepta 14 imágenes, así que muestra hasta 13 productos; el resto queda en la lista. **→** Después, el control: comparamos la foto original con la generada con SIFT y RANSAC. Si reencuentra al menos 50 puntos del cuarto y la cámara casi no se movió, se acepta; si no, se genera otra, hasta 3 veces. El loft pasó al primer intento. Este otro pedido, un living clásico, no: el modelo reencuadró hacia la chimenea en los tres intentos, y se entrega el mejor, marcado. El control detecta; reintentar lo arregla pocas veces: contando otra tanda, rescató 2 de las 9 que fallaron al primer intento.

## 15. Fase 11: Lista + imagen
*Recorrido · 11 · ~0:30 · desde el minuto 9:10*

Y fase once, lo que sale: la lista de compra, con productos reales y cuántos de cada uno, acá 5 de Amazon y 2 de IKEA, y la foto del mismo ambiente con ellos. Cada línea tiene su recorrido: el kind lo puso el plan, la búsqueda trajo los candidatos y la elección tomó uno, a veces no el primero. Este pedido costó unos 26 centavos de Claude y 8 de la imagen.

## 16. Desafíos
*Desafíos · ~0:55 · desde el minuto 9:45*

Los desafíos. El más grande fue cambiar la arquitectura que nos aprobaron. La propuesta era generar primero una imagen amoblada, recortar cada mueble y buscar en el catálogo el más parecido, por imagen. **→** Construimos y medimos su buscador sobre el mismo ground truth: encontraba primero el 43 por ciento de los productos anotados, contra 55 buscando por texto. Con eso, y con una generación de imagen menos por pedido, cambiamos a RAG por texto. Ojo: esa versión nunca corrió de punta a punta; comparamos buscadores, no sistemas. **→** Los otros tres: el catálogo traía fotos de otro producto y hubo que revisarlo a mano; no hay ground truth de la tarea real; y el modelo de imagen rehace el cuarto.

## 17. El banco de la búsqueda
*Datos · ~0:35 · desde el minuto 10:35*

Usamos dos bancos de prueba, que miden cosas distintas. Para la búsqueda, 65 ambientes de IKEA con sus productos anotados. Por cada mueble visible, un subagente escribió la consulta como la escribiría el plan, sin ver el catálogo. **→** Una consulta acierta si el anotado sale primero, o entre los k primeros. **→** Son 864 consultas, 549 con su producto en el catálogo. Es un banco de producto conocido: quien escribe está viendo el mueble, así que mide el índice, no la recomendación.

## 18. Ambientes vacíos
*Datos · ~0:30 · desde el minuto 11:15*

Para el flujo entero, 11 ambientes vacíos reales, cada uno con su pedido: 5 de departamentos nuestros y 6 públicos, con licencia Creative Commons y estilos distintos del nórdico. Ahí no hay ground truth: un juez compara a ciegas las listas de dos configuraciones, en los dos órdenes, y una gana un ambiente solo si gana en los dos. La imagen se mide aparte.

## 19. Métricas del buscador
*Métricas · ~0:45 · desde el minuto 11:40*

Las métricas del buscador. Arriba, una consulta real: el anotado sale en el puesto 3, así que hit@1 da cero y hit@3 da uno. **→** El titular es hit@5, porque son los cinco candidatos que ve el que elige: hoy, 0,825. Para comparar dos métodos usamos la diferencia pareada: las mismas consultas, la diferencia media y su intervalo de 95 por ciento, por bootstrap de ambientes. Si no toca el cero, no es ruido. Mirar el intervalo de cada método por separado nos había hecho leer mejoras que eran ruido. Las de la clase, context precision y NDCG, acá repiten al MRR; context recall es por ambiente.

## 20. El generador y los jueces
*Métricas · ~0:45 · desde el minuto 12:30*

Faithfulness: partimos el porqué en afirmaciones, y un juez dice cuáles se infieren de lo que el generador vio. Da 0,88: 313 de 356. Lo que no se sostiene es casi siempre la especie de la madera. Answer relevance: un juez que no ve el pedido escribe los pedidos que esa lista contesta. Da 0,70, contra 0,56 con pedidos escritos para otras listas. Con otras once listas, las de la versión 1, dieron 0,82 y 0,69: los números se repiten. **→** Y sobre los jueces: validado contra el ground truth hay uno solo; el de listas se controla con los dos órdenes.

## 21. La imagen
*Métricas · ~0:45 · desde el minuto 13:15*

La imagen la medimos sobre las 11 corridas finales, no sobre la mejor. Primero: ¿son esos productos? Detectamos cada mueble, lo recortamos y lo comparamos con las fotos del catálogo de su tipo: reconocido, si el más parecido es el de la lista. En el loft, el sofá, la biblioteca y la lámpara salen primeros; la alfombra, no. En total se reconocen 31 de 75, el 41 por ciento, aunque aparecen 71. **→** Segundo: ¿es ese cuarto? El control pasa en 7 de 11. O sea: la lista es confiable; la imagen es una visualización, que acierta el producto exacto cuatro de cada diez veces.

## 22. Las trampas
*Métricas · ~0:55 · desde el minuto 14:00*

Las trampas, en voz alta. Uno: el banco de la búsqueda es de producto conocido; en el flujo real el plan imagina el producto, no lo ve. **→** Dos: el mismo modelo escribe las consultas y las descripciones, con el mismo molde; por eso contar palabras rinde casi como el embedder. **→** Tres: no hay conjunto apartado. **→** Y cuatro: de punta a punta son 11 ambientes, y el juez es el mismo modelo que elige. Corrimos la misma configuración dos veces: el que elige cambió 9 de 75 productos, y el juez repartió los ambientes 3 a 3. Ganar un ambiente no es evidencia: lo que cuenta es la asimetría. Por eso leemos las diferencias grandes, y las de dos puntos, no.

## 23. El mapa de los experimentos
*Experimentos · ~0:35 · desde el minuto 14:55*

Ahora los experimentos, por cuánto importan. El mismo mapa: cada pin es una pregunta que le hicimos a una parte del sistema. Los llenos, del 1 al 7, tienen lámina propia. Dos de ellos, el 4 y el 7, no miden una fase: miden al banco de prueba. Los huecos, del 8 al 14, son los de trámite. Y dos cosas no las decidió ningún experimento: el modelo de imagen y los umbrales del control.

## 24. Exp. 1: Qué se indexa
*Experimentos · 1 · ~0:25 · desde el minuto 15:25*

El texto de IKEA es una frase de marketing, y la gente pide estilo, color y materiales, que están en la foto. ¿Vale la pena describir cada producto? **→** Indexamos dos textos, con todo lo demás fijo: el texto del vendedor y la descripción de ocho líneas. La consulta, una frase corta sin reescribir, para medir un solo cambio.

## 25. Exp. 1: resultados
*Experimentos · 1 · ~0:25 · desde el minuto 15:50*

Con el texto del vendedor, hit@1 da 0,11; con la descripción, 0,30: casi el triple, y hit@5 pasa de 0,30 a 0,60. La diferencia es pareada y su intervalo no toca el cero. **→** Decisión: se indexa la descripción hecha desde la foto. Es el preprocesamiento que más pesa de todo el trabajo.

## 26. Exp. 2: Cómo se escribe la consulta
*Experimentos · 2 · ~0:35 · desde el minuto 16:15*

El plan no busca con el pedido: escribe el producto ideal en las ocho líneas del catálogo. Es la técnica de Advanced RAG del flujo, y no la habíamos medido contra no hacerla: la comparábamos con buscar solo con el nombre del kind, que es azar por construcción. **→** La ficha contra la frase natural: las pocas palabras con que el redactor nombró la pieza. Con la búsqueda del flujo, y también contra la foto.

## 27. Exp. 2: resultados
*Experimentos · 2 · ~0:30 · desde el minuto 16:50*

La ficha da 0,530 y la frase natural 0,324: suma +0,21, con un intervalo lejos del cero. Y lo que no esperábamos: contra la foto, la frase sin reescribir da 0,479, casi lo mismo que la ficha. El texto necesita que la consulta hable como el catálogo; la foto, casi no. **→** Decisión: el plan sigue escribiendo la ficha. Y queda un argumento para la búsqueda híbrida: las dos rutas fallan distinto.

## 28. Exp. 3: Léxica, por foto e híbrida
*Experimentos · 3 · ~0:35 · desde el minuto 17:20*

Dos dudas sobre el índice. ¿El embedder neuronal hace falta, o alcanza con contar palabras? Y el catálogo tiene fotos: la clase dio dos rutas, pasar la imagen a texto, que es lo que hacíamos, o embeberla directamente. Esa nunca la habíamos medido. **→** Tres buscadores sobre las mismas consultas: el denso, Qwen3 sobre las descripciones; el léxico, BM25; y por foto, SigLIP 2, la consulta en una frase contra la foto. Y sus fusiones.

## 29. Exp. 3: resultados
*Experimentos · 3 · ~0:30 · desde el minuto 17:50*

Solos, los tres rinden parecido: 0,530, 0,517 y 0,508. Ni el embedder le gana a contar palabras, ni describir le gana a embeber la foto. Pero se equivocan en cosas distintas: fusionados dan 0,605, +0,075 de hit@1, con un intervalo que no toca el cero. **→** Decisión: la búsqueda híbrida pasa a ser la del flujo: es la versión 2, el Ejercicio 4.

## 30. El camino incremental
*Experimentos · ~0:50 · desde el minuto 18:20*

La ablación incremental: un cambio por paso, con su diferencia pareada, sobre las 549 consultas. Arrancamos del RAG naive, el texto del vendedor y la consulta sin reescribir: 0,11. **→** Describir cada producto desde su foto lo lleva a 0,30; escribir la consulta como una ficha, a 0,54. Esos dos pasos son los que más pesan. **→** El filtro por kind no suma en este banco: lo usamos por otra razón, que vemos en los de trámite. Con el filtro, esa es la versión 1 del flujo. **→** Con la búsqueda léxica, 0,58; con la foto, 0,60: la versión 2. **→** Aparte queda el 0,69 que mostrábamos antes: es un VLM reordenando el top-10, una técnica aislada, no un escalón del flujo.

## 31. Exp. 4: ¿Error, o una variante?
*Experimentos · 4 · ~0:50 · desde el minuto 19:10*

hit@1 exige el producto anotado exacto, y el catálogo está lleno de variantes del mismo modelo. ¿Cuánto de lo que cuenta como error es el mismo mueble en otro color? **→** Tres niveles de correcto para el primer candidato: el producto exacto, el mismo modelo, y uno que sirve según un juez. **→** El exacto, 0,53; el mismo modelo, 0,62; uno que sirve, 0,78. Una de cada 5 veces que el primero falla es otra variante del mismo mueble, como esta alfombra. **→** El banco subestima el nivel, no el orden: la comparación entre buscadores no cambia. Usamos el exacto para comparar, y los tres juntos para decir cuánto sirve.

## 32. Exp. 5: Elegir con un VLM, y cuántos
*Experimentos · 5 · ~0:30 · desde el minuto 20:00*

hit@10 es 0,89 pero hit@1 0,54: el correcto casi siempre está entre los diez primeros, pero no primero. ¿Mirar las fotos ordena mejor que el coseno? ¿Y cuántos candidatos conviene pasar? **→** Opus recibe la consulta y las fotos de los diez primeros, y los ordena. De ahí sale gratis la curva: si eligiera entre los primeros k, ¿acertaría? La punteada es el techo.

## 33. Exp. 5: resultados
*Experimentos · 5 · ~0:30 · desde el minuto 20:30*

Reordenando el top-10, hit@1 pasa de 0,535 a 0,687. De 3 a 5 candidatos la elección sube 3 puntos, también significativo; a partir de 8 se aplana. **→** Decisión: cinco candidatos por pieza. Ojo: es una técnica aislada, no un paso del flujo. Ese reranker ordena contra la consulta, sin ver el ambiente; el que elige arma un conjunto para el cuarto, y no tiene ground truth.

## 34. Exp. 6: Con búsqueda o sin búsqueda
*Experimentos · 6 · ~0:40 · desde el minuto 20:55*

Es el con y sin retrieval del flujo, con sus dos extremos. Uno: darle al que elige cinco productos al azar del kind pedido; es el control del juez, porque si no distinguiera esas dos listas, ninguna comparación de punta a punta diría nada. Dos, la pregunta incómoda: si el catálogo entra en el contexto, ¿hacía falta RAG? **→** Mismo plan, mismo modelo que elige, mismo juez. Contra el azar, en 7 ambientes. Contra el catálogo entero en el prompt, las 1.502 fichas en texto, en los 11.

## 35. Exp. 6: resultados
*Experimentos · 6 · ~0:50 · desde el minuto 21:35*

Contra el azar, 7 a 0, con los 14 votos: los productos útiles pasan de 0,26 a 0,82. Y el juez distingue cuando la diferencia es grande. Contra el catálogo entero, 5 a 5, con los mismos productos útiles: empatan. Con el catálogo en la caché de prompt cuesta lo mismo; sin caché, diez veces más. **→** O sea: por calidad, no hacía falta. Con mil quinientos productos, un modelo de contexto largo hace el trabajo de la búsqueda leyendo todo. La búsqueda hace falta cuando el que elige ve cinco productos, y empata cuando puede leerlos todos. RAG lo elegimos porque escala, y porque no depende del tráfico, de la caché ni de un modelo de contexto largo.

## 36. Exp. 7: Tres redactores
*Experimentos · 7 · ~0:35 · desde el minuto 22:30*

Las consultas de evaluación las escribió un modelo. La clase pidió promedio y desvío: ¿cuánto cambia el número sin cambiar el sistema? **→** Las mismas consultas, escritas otras dos veces por subagentes independientes. **→** La versión 1 da 0,539 ± 0,025; la versión 2, 0,604 ± 0,009. La mejora de la híbrida se repite con los tres. **→** El número se mueve unos dos puntos y medio según quién escribe: por eso no leemos diferencias de dos puntos.

## 37. De trámite (1 de 2) *
*Experimentos · de trámite · ~0:40 · desde el minuto 23:00*

Los de trámite, con la respuesta corta. Embedder: Qwen3 solo se sostiene sobre BGE; contra contar palabras no se distingue, porque consultas y descripciones comparten el molde. Dimensión: con 512 da lo mismo que con 1.024, y con 1.502 productos la memoria no pesa. Splitting: no partimos; lo que importa son las líneas de lo que se ve, colores y forma. Base vectorial: ChromaDB da el mismo top-10 que la búsqueda exacta en las 864 consultas; la usamos porque persiste y escala; la híbrida no lo consulta, puntúa a todos los que pasan el filtro.

## 38. De trámite (2 de 2) *
*Experimentos · de trámite · ~0:50 · desde el minuto 23:45*

Filtros de metadata: en este banco no suman, y el de kind cuesta dos puntos de hit@5. Lo usamos igual, por algo que el banco no mide: en los pedidos reales, sin él, el 11 por ciento de los candidatos sería de otro kind. El de medidas cambia uno de cada once candidatos, sin evidencia de que mejore la lista. Rerankers de texto: probamos el MiniLM de la clase y Qwen3-Reranker, y los dos empeoran, porque releen el texto que ya usó la búsqueda. La escena: la plantilla y la escrita por el LLM empatan, como vimos. Y el catálogo: ampliarlo y revisarlo fueron decisiones de datos, y sumar Amazon le cuesta al buscador 3,5 puntos de hit@5.

## 39. Ejercicio 4: la versión 1
*Ejercicio 4 · 1 de 3 · ~0:50 · desde el minuto 24:35*

El Ejercicio 4. La versión 1 es el sistema hasta el 11 de noviembre: la búsqueda era el coseno del embedder sobre las descripciones, con el filtro por kind. Su limitación, medida: entre productos casi iguales, el primero es el anotado el 53 por ciento de las veces, y en una de cada cinco piezas el correcto no llega a los cinco candidatos. **→** Un caso: se busca un almohadón blanco con hojas negras, y la versión 1 trae almohadones blancos y negros; el anotado quedó sexto. El índice lee una descripción, pero no ve el producto ni aprovecha las palabras exactas. **→** Y BM25 y la foto sola rendían como el embedder, fallando en cosas distintas.

## 40. Ejercicio 4: la versión 2
*Ejercicio 4 · 2 de 3 · ~0:35 · desde el minuto 25:25*

El cambio es una línea de configuración: rag.hybrid pasa de una lista vacía a BM25 y SigLIP 2. ¿Por qué este cambio? Sale de una limitación medida; es una técnica de Advanced RAG, búsqueda híbrida y multimodal; y no cuesta nada por pedido, porque corre local. **→** La búsqueda ahora promedia tres puntajes estandarizados: el coseno con la descripción, que ya estaba; BM25, las palabras; y SigLIP 2, la foto. En el caso del almohadón, ahora el anotado sale primero.

## 41. Ejercicio 4: resultados
*Ejercicio 4 · 3 de 3 · ~1:00 · desde el minuto 26:05*

Sobre el ground truth: hit@1 pasa de 0,530 a 0,605, y hit@5, lo que ve el que elige, de 0,790 a 0,825. Los intervalos de la diferencia no tocan el cero, y con los otros dos redactores la mejora se repite. De punta a punta, en los 11 ambientes: la versión 2 gana 5, empata 6 y no pierde ninguno. Los productos útiles pasan de 0,68 a 0,74, y el costo es el mismo. **→** Lo del ground truth es claro; de punta a punta son once ambientes, cinco a cero da p igual a 0,06, y en seis el juez no se decide. Corrimos la misma versión dos veces y el juez repartió los ambientes 3 a 3: ganar un ambiente no alcanza, cuenta la asimetría. Clara en el banco; no peor, probablemente mejor, en la tarea real.

## 42. Cuánto cuesta *
*Cierre · ~0:30 · desde el minuto 27:05*

Costos, del registro de gastos. Un pedido cuesta unos 28 centavos de dólar: 6 el plan, 14 la elección y 8 la imagen. Buscar no cuesta nada: todo corre local. **→** El trabajo entero costó 45 dólares; lo que más costó fue evaluar el reranking con un VLM. Cada llamada paga queda registrada, con topes por cuenta, y lo ya pagado queda en caché.

## 43. Limitaciones
*Cierre · ~0:35 · desde el minuto 27:30*

Del sistema: no dice «no hay», pone lo más parecido sin avisar; el tamaño no se puede verificar; la imagen es una visualización; y el generador afirma maderas que no ve. **→** De la evaluación: el banco de la búsqueda es de producto conocido, sin conjunto apartado; de punta a punta son 11 ambientes, con un juez sin validar contra personas; y el que elige no es determinístico: entre dos corridas iguales cambia 9 de 75 productos.

## 44. Trabajo futuro
*Cierre · ~0:40 · desde el minuto 28:05*

Lo próximo es del RAG y de cómo lo medimos: que el sistema diga «no hay»; un banco de consultas escrito por personas, con un conjunto apartado; validar al juez con nuestro voto a ciegas; y probar un modelo más barato para elegir. Más lejos: medidas reales del ambiente y un catálogo actual. **→** Y fuera del RAG hicimos una prueba: vaciamos un living real y lo volvimos a amoblar con sus muebles. Es un solo cuarto; lo único que se sostiene es que indicarle al modelo dónde va cada mueble ayuda.

## 45. Conclusiones
*Cierre · ~0:45 · desde el minuto 28:45*

Uno: lo que más pesa es la base de conocimiento y cómo se escribe la consulta; el embedder casi no importa. **→** Dos: la versión 2 es la búsqueda híbrida: suma en el ground truth, sin costo, y de punta a punta gana 5, empata 6 y no pierde. **→** Tres: la búsqueda gana 7 a 0 contra el azar, y empata contra el catálogo entero en el contexto: RAG no hace mejor la lista, es la arquitectura que escala. **→** Cuatro: medir bien fue la mitad del trabajo; nos hizo cambiar el número de cabecera. **→** Y cinco: la lista es confiable; la imagen es una visualización.

## 46. Gracias
*Portada · ~0:05 · desde el minuto 29:30*

Gracias. ¿Preguntas?

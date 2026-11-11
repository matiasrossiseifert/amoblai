# Guion de la presentación (amoblai, versión b2)

Generado por `build.py` junto con `presentacion.html`: los números salen de los mismos archivos de resultados que las láminas. 55 láminas, unos 31 minutos (30:45).

**Cómo se pasa.** Flecha derecha, espacio o clic: avanza un paso; flecha izquierda: vuelve. F: pantalla completa; O: índice con miniaturas; N: estas notas abajo de la lámina; P: ventana del presentador (lámina actual, la siguiente, notas y reloj, sincronizadas); B: pantalla negra. `presentacion.html?all#/12` muestra la lámina 12 con todos sus pasos; `#/12.2` va al paso 2.

**Los experimentos** tienen dos láminas. La oscura es la pregunta: se ve el porqué y el esquema del flujo con la etapa que se prueba encendida; con la flecha aparece el experimento (las variantes). **Se cuentan esas dos cosas antes de pasar.** La clara es el resultado: arranca con las variantes y las barras vacías; una flecha muestra los resultados y otra la decisión, que se imprime como un talón abajo (la línea de configuración que deja el experimento). Los experimentos 4 y 5 van en una sola lámina, y el 13 tiene una lámina más en el medio, con sus prompts.

**El recorrido** (láminas 6 a 16) sigue un pedido real, el rincón de lectura, por las once fases del flujo, con el mapa arriba a la derecha: la fase actual encendida, las vistas con ✓ y los números de los experimentos que la decidieron. En cada fase: qué entra y qué sale, el prompt tal cual se manda (extracto, en inglés, con lo importante resaltado) y sus versiones. Ahí no se dan resultados: los números van en cada experimento.

En el texto, **→** marca dónde se avanza un paso.

**Reparto sugerido** (a definir entre los tres):
- Parte 1: láminas 1 a 18 (Portada → Ground truth), unos 10:20.
- Parte 2: láminas 19 a 38 (Ambientes vacíos → Exp. 9: resultados), unos 10:10.
- Parte 3: láminas 39 a 55 (Exp. 10: Qué catálogo → Gracias), unos 10:15.

## 1. Portada
*Portada · ~0:25 · desde el minuto 0:00*

Somos Juan Bautista, Matías y Junior. amoblai responde una pregunta concreta: tengo este ambiente vacío, ¿qué compro y cómo queda? Sacás una foto, escribís qué querés, y te devuelve una lista de productos reales de un catálogo y la imagen del mismo ambiente con esos productos.

## 2. El problema
*El problema · ~0:25 · desde el minuto 0:25*

Cuando te mudás a un lugar vacío tenés que decidir qué comprar sin poder verlo puesto. Los catálogos muestran cada mueble suelto, sobre fondo blanco, y las fotos de ambientes muestran la casa de otro. **→** Nosotros queremos responder, para este ambiente y este pedido: qué productos reales, que se puedan comprar, van; cuántos y de qué medida; y cómo queda el ambiente con ellos.

## 3. El producto
*El producto · ~0:40 · desde el minuto 0:50*

Así se usa. La entrada es una foto del ambiente y un pedido en texto libre, como este: un rincón de lectura con una biblioteca alta de madera oscura. **→** La salida son dos cosas: la lista de compra, con productos reales del catálogo y cuántas unidades de cada uno (acá, 2 bibliotecas iguales), y la foto del mismo ambiente con esos productos puestos.

## 4. Por qué RAG
*El producto · ~0:35 · desde el minuto 1:30*

¿Por qué un RAG y no un LLM o un modelo de imagen solos? Un LLM sabe de decoración, pero no sabe qué hay en un catálogo: te recomienda un sillón de cuero coñac que nadie vende. Un modelo de imagen amobla lindo, pero inventa los muebles. **→** Con RAG, el catálogo es la base de conocimiento: el LLM decide qué hace falta, el retrieval trae candidatos reales, el VLM elige mirando sus fotos, y la imagen sale de esas fotos. No es un Q&A: la respuesta es una combinación de productos que tiene que funcionar junta.

## 5. v0 → v1
*Arquitectura · ~0:40 · desde el minuto 2:05*

La primera versión buscaba por imagen: detectaba cada mueble en la foto con Grounding DINO, lo recortaba con SAM y buscaba la foto del catálogo más parecida con DINOv3. Eso sirve para encontrar este sofá, pero nuestro caso es un ambiente vacío: no hay nada que recortar. La v1 busca por texto: un LLM escribe el producto ideal en el mismo formato que el catálogo. **→** Con el mismo ground truth, la v1 da 0,62 de hit@1 contra 0,51 de la v0, y además funciona con el ambiente vacío.

## 6. El recorrido
*Recorrido · ~0:35 · desde el minuto 2:45*

El sistema, fase por fase, sobre este mapa: once fases en dos pipelines. **→** Las tres primeras corren una vez, offline: el catálogo, una descripción de cada producto escrita por un VLM, y el índice vectorial. **→** Las otras ocho corren en cada pedido: dos llamadas a Claude, el plan y la elección, y una al modelo de imagen. Lo demás es local. **→** En cada fase, qué entra, qué sale, el prompt y el experimento que la decidió. Y una idea: la elección solo toma productos que trajo la búsqueda, así que la respuesta queda atada al catálogo.

## 7. Fase 1: Catálogo
*Recorrido · 1 · ~0:35 · desde el minuto 3:20*

La primera fase es el catálogo, la base de conocimiento del RAG. Dos fuentes: IKEA, el dataset de Tautkute y otros, con 855 productos de living y comedor, 819 después de revisarlos, fotos chicas y casi sin medidas en los asientos; y Amazon Berkeley Objects, listados reales, 683 productos con medidas en el 90%. Juntos, 1502. Cada registro tiene tipo, kind y medidas, que filtran la búsqueda. Y el texto del vendedor de la HEMNES, «la madera maciza se siente natural», no sirve para buscar. Qué entra lo decidieron los experimentos 9 y 10.

## 8. Fase 2: Descripción
*Recorrido · 2 · ~0:35 · desde el minuto 3:55*

Segunda fase: la descripción. Claude Opus 5.5 mira la foto de cada producto y lo escribe en ocho líneas fijas: tipo, uso, estilo, materiales, colores, forma, sensación y con qué combina. El estilo sale de una lista cerrada, y no van marca, precio ni medidas. A IKEA lo describieron subagentes de Claude Code; a Amazon, la API. El prompt tuvo tres versiones: la v2 para los muebles, la v3 para lámparas y deco, y la de la API, que además da el kind. Por qué describir: el experimento 1.

## 9. Fase 3: Índice
*Recorrido · 3 · ~0:35 · desde el minuto 4:30*

El índice. Embebemos la descripción entera, un documento por producto, de unas 84 palabras. El modelo es Qwen3-Embedding, de 600 millones de parámetros, local y en CPU: toma el último token y da 1024 componentes. La consulta entra igual, sin instrucción, porque ya está escrita como una descripción. Los vectores van a ChromaDB, con HNSW en coseno, y al lado la metadata que leen los filtros; la que falta va como menos uno y pasa cualquier tope. Cada decisión tiene su experimento: el 1, el 2, el 4, el 5 y el 6.

## 10. Fase 4: Foto, pedido y plan
*Recorrido · 4 · ~0:40 · desde el minuto 5:05*

Fases 4 y 5. Entra una foto del ambiente vacío y el pedido en texto libre, como este rincón de lectura. Puede entrar otra foto del mismo ambiente, que ve Claude pero no el modelo de imagen. **→** El plan es la primera llamada a Claude. Lee el ambiente como un diseñador y decide las piezas: acá, 9. Para cada una elige el kind de una lista cerrada, que después es un filtro, estima la medida máxima que entra, y escribe el producto ideal en las mismas ocho líneas que las descripciones. Ese es nuestro query rewriting: la consulta habla como los documentos.

## 11. Fase 5: Plan
*Recorrido · 5 · ~0:35 · desde el minuto 5:45*

Es el prompt que más reescribimos. La primera versión le dio un sillón a alguien que pidió una silla para su escritorio. La v2 pide la pieza como la nombró el usuario, el kind de una lista cerrada, las medidas máximas y la consulta en ocho líneas. Con la primera imagen, un living largo con cuatro muebles y nada más, la v3 pide terminar el ambiente, hasta seis piezas. Como un rincón de lectura ya llegaba a seis, la v4 saca el tope. Si conviene reescribir la consulta entera, lo responde el experimento 6.

## 12. Fase 6: Búsqueda
*Recorrido · 6 · ~0:35 · desde el minuto 6:20*

La búsqueda tiene dos pasos. Primero un filtro duro, que en ChromaDB va como where: el kind del plan y las medidas máximas, con 15% de margen porque salen de una foto. Después, el coseno entre la consulta y cada descripción que pasó. Acá se ve por qué funciona: la consulta del plan y el documento del VLM hablan igual, línea por línea, y la HEMNES sale primera. Quedan los 5 más cercanos; esta corrida es de antes del experimento 8 y traía 3. El filtro lo decidió el experimento 3.

## 13. Fase 7: Elección
*Recorrido · 7 · ~0:35 · desde el minuto 6:55*

La elección es la segunda llamada a Claude. Ve la foto del cuarto y las fotos de los candidatos de todas las piezas juntas, y elige la combinación, no el mejor de cada una por separado; la v2 del prompt agregó cuántas unidades. Acá eligió dos HEMNES para llenar la pared; para la lámpara, la tercera por coseno, porque el brazo articulado sirve para leer; y avisó que no hay alfombras redondas. Es un reranker que mira fotos: lo mostraron los experimentos 7 y 8.

## 14. Fase 8: Escena
*Recorrido · 8 · ~0:35 · desde el minuto 7:30*

La escena es el prompt del modelo de imagen. Primero lo escribía Claude, diciendo dónde va cada producto. En paralelo probamos una plantilla sin LLM, donde el modelo de imagen decide dónde va cada cosa. La v3 le pasó las cantidades, y la v4, después de que el modelo inventara una ventana, es una edición estricta: la foto del cliente, el mismo cuarto, y solo estos productos. A la derecha, el prompt lleno de este pedido, con su tipo, su medida y sus unidades. La plantilla la decidió el experimento 12.

## 15. Fase 9: Imagen y control
*Recorrido · 9 · ~0:40 · desde el minuto 8:05*

La imagen la hace Nano Banana 2, el modelo de imagen de Gemini, por fal, en modo edición: recibe la foto del cuarto, una foto por producto y el prompt de la escena. Cuesta 8 centavos de dólar. **→** Como a veces redecora, hay un control automático: SIFT busca puntos de la foto original en la generada, y RANSAC verifica que encajen con el mismo encuadre. Si reencuentra al menos 50 y la cámara no se movió, queda; si no, se pide otra, hasta 3 veces. Acá pasó al primer intento, con 116 puntos. En otro departamento descartó dos y se quedó con la tercera.

## 16. Fase 11: Lista + imagen
*Recorrido · 11 · ~0:30 · desde el minuto 8:45*

Y la última fase es lo que sale: la lista y la imagen. Cada línea tiene su recorrido: el kind lo puso el plan, la búsqueda trajo los candidatos y la elección tomó uno, a veces no el primero por coseno, y cuántas unidades. La imagen sale de las fotos de esos mismos productos. Cada decisión que fuimos nombrando salió de un experimento: son trece.

## 17. Los hiperparámetros
*Arquitectura · ~0:30 · desde el minuto 9:15*

Estas son las decisiones que fuimos nombrando en el recorrido, sobre el mismo mapa: cada número marca en qué fase pega su experimento. Todavía no decimos qué ganó. Primero, con qué datos y qué métricas medimos; después, cada experimento en dos láminas, la pregunta y el resultado con su decisión, en el orden en que los hicimos: cada uno deja su decisión en la configuración del siguiente.

## 18. Ground truth
*Datos · ~0:35 · desde el minuto 9:45*

Para medir el retrieval necesitamos saber cuál es el producto correcto. El dataset trae 65 fotos de livings y comedores reales de IKEA con sus productos anotados. Por cada mueble visible, un subagente escribe la búsqueda como la escribiría nuestro plan, mirando el ambiente. **→** Una búsqueda acierta si el anotado sale primero (hit@1) o entre los k primeros. **→** En total, 864 búsquedas, 549 con su producto en el catálogo. Los intervalos de confianza son por bootstrap por ambiente, porque las búsquedas de un mismo ambiente no son independientes.

## 19. Ambientes vacíos
*Datos · ~0:30 · desde el minuto 10:20*

Para probar el sistema completo hacen falta ambientes vacíos reales. Tenemos 11: 5 de departamentos nuestros y 6 públicos de Wikimedia Commons y Flickr, con licencia Creative Commons, elegidos entre 22 que revisamos uno por uno para descartar renders y fotos generadas con IA. Cada uno tiene un pedido escrito como lo escribiría un usuario que sabe pedir; los públicos, con estilos distintos del nórdico. Acá no hay ground truth: medimos con un juez y con métricas de imagen.

## 20. Métricas de retrieval
*Métricas · ~0:35 · desde el minuto 10:50*

Las métricas de retrieval, donde sí hay ground truth. Arriba, una búsqueda real: el anotado sale segundo. hit@k: si el anotado está entre los k primeros; acá hit@1 da 0 y hit@3 da 1. MRR: el promedio de uno sobre la posición del correcto; esta búsqueda suma un medio. **→** hit@k con k igual a los candidatos que ve el VLM es el techo de lo que puede elegir. Context recall y precision son las de RAGAS. NDCG admite relevancia graduada. Y si los intervalos de confianza de dos métodos se pisan, no los podemos distinguir.

## 21. Jueces y pares
*Métricas · ~0:25 · desde el minuto 11:25*

Cuando no hay un único correcto usamos jueces, pero validados. Relevancia graduada: un LLM califica el top-3 con 2, 1 o 0, y antes chequeamos que le dé 2 al anotado. RAGAS sobre la explicación de cada elección: faithfulness y answer relevance. Para comparar variantes sin ground truth, un juez de a pares en los dos órdenes. Y el costo de cada llamada.

## 22. Métricas de imagen
*Métricas · ~0:35 · desde el minuto 11:50*

Para la imagen medimos tres cosas. Que sea el mismo cuarto: SIFT reencuentra puntos de la foto original y mide cuánto se movió la cámara, y SSIM compara lo que no es mueble. Que sean los mismos productos: detectamos cada mueble, lo recortamos y vemos si el más parecido del catálogo es el de la lista. Y que sea lo que se pidió: SigLIP 2 entre el pedido y la imagen, y contamos lo que falta, lo repetido y lo inventado. Además, reproducibilidad, con tres redactores, y el espacio de embeddings.

## 23. Exp. 1: Qué texto se indexa
*Experimentos · 1 · ~0:35 · desde el minuto 12:25*

La primera pregunta fue qué texto indexar. IKEA trae nombre, tipo, colores y una frase de marketing del estilo «The armchair is lightweight and easy to move». Pero nadie pide así: se pide un sillón nórdico, de madera clara, con tapizado crema, y eso está en la foto. **→** Indexamos tres textos y corrimos las mismas 549 búsquedas del ground truth, con todo lo demás fijo: el texto del vendedor; la descripción del VLM que vimos en el recorrido; y esa descripción con el nombre comercial adelante.

## 24. Exp. 1: resultados
*Experimentos · 1 · ~0:30 · desde el minuto 13:00*

Con el texto del vendedor, hit@1 da 0,13; con la descripción del VLM, 0,54: más de 4 veces. Es el cambio más grande de todo el trabajo. El nombre comercial adelante empeora: con el mismo filtro, de 0,53 a 0,42. NOLMYRA no le dice nada al embedding. **→** Decisión: indexamos solo la descripción del VLM. Y queda una idea que vuelve en todo el trabajo: la consulta y el documento escritos en el mismo formato.

## 25. Exp. 2: Embedder
*Experimentos · 2 · ~0:30 · desde el minuto 13:30*

Con el texto resuelto, la pregunta natural es cuánto aporta el modelo de embeddings. Un modelo más grande cuesta memoria y tiempo, y nos pusimos la restricción de que el retrieval corra local, en CPU, sin pagar una API. Queríamos ver cuánto gana un modelo entrenado contra una línea de base sin modelo. **→** Tres embedders sobre el mismo texto y las mismas búsquedas: hashing, una bolsa de palabras hasheada, sin ningún modelo; BGE-base, de 110 millones de parámetros; y Qwen3-Embedding, de 600 millones.

## 26. Exp. 2: resultados
*Experimentos · 2 · ~0:25 · desde el minuto 14:00*

Gana Qwen3, con 0,54. Pero el hashing queda cerca (0,51) y BGE último (0,48). La explicación: las descripciones usan vocabulario controlado, los estilos y los kinds salen de listas cerradas, así que hasta contar palabras funciona bastante. Qwen3 gana más claro en MRR (0,65 contra 0,63). **→** Decisión: Qwen3-Embedding-0.6B, Apache 2.0, corre en CPU. La lección: el formato del texto vale más que el modelo.

## 27. Exp. 3: Filtros duros
*Experimentos · 3 · ~0:30 · desde el minuto 14:25*

El filtro duro que vimos en la búsqueda: por similitud sola, una mesa nórdica de madera clara se puede parecer más a la consulta que un sofá. Filtrar es gratis, pero si el plan y el catálogo no coinciden en la categoría, el correcto queda afuera. **→** Tres opciones: sin filtro; por tipo, 14 categorías gruesas como sofá, mesa o lámpara; y por kind, 41 categorías finas como mesa ratona o mesa de comedor. Miramos hit@1 y sobre todo hit@10.

## 28. Exp. 3: resultados
*Experimentos · 3 · ~0:35 · desde el minuto 14:55*

Con descripciones buenas, hit@1 casi no cambia. Pero el filtro por kind resta: en hit@10 da 0,86 contra 0,89 del filtro por tipo. Si el plan pide una mesa auxiliar y el catálogo la tiene como mesa ratona, el filtro fino la deja afuera. **→** Decisión: filtrar siempre, más las medidas máximas del plan. El flujo filtra por los kinds que elige el plan, que puede dar más de uno; contra el tipo, la diferencia en hit@1 está dentro del intervalo, y pasarlo a tipo es lo próximo que probaríamos.

## 29. Exp. 4: Splitting
*Experimentos · 4 · ~0:40 · desde el minuto 15:30*

El chunking es central en un RAG. Nuestros documentos son cortos, de 70 a 100 palabras, pero tienen 8 líneas con roles distintos. ¿Comparar colores contra colores sería más preciso que un solo vector? **→** Tres formas: un documento por producto; un chunk por línea, donde el producto vale lo que su línea más parecida; y línea contra línea, cada una contra la del mismo rótulo. **→** Gana un documento (0,54). Línea contra línea queda cerca (0,51) y el chunk por línea se desploma (0,27): «Colors: light wood» se parece a cualquier cosa de madera clara. **→** Decisión: un documento por producto. Con documentos tan cortos no hay nada que partir.

## 30. Exp. 5: Dimensión del embedding
*Experimentos · 5 · ~0:30 · desde el minuto 16:10*

Qwen3 se entrenó con Matryoshka: se puede truncar el vector sin reentrenar. Con 819 productos no importa; en un catálogo de millones, la memoria y la latencia crecen con la dimensión. **→** Truncamos de 32 a 1024 componentes, renormalizamos y repetimos las búsquedas. **→** Con 512 da casi lo mismo que con 1024 (0,53 contra 0,54), con la mitad de memoria. Con 32 cae a 0,43. **→** Decisión: para este catálogo dejamos 1024 porque no cuesta nada; si creciera, indexaríamos con 512.

## 31. Exp. 6: Base vectorial y consulta
*Experimentos · 6 · ~0:25 · desde el minuto 16:40*

Dos dudas. ChromaDB usa HNSW, un índice aproximado: había que verificar que no perdiera resultados contra la búsqueda exacta con numpy. Y el query rewriting que vimos en el plan cuesta tokens y latencia en cada pedido: ¿alcanzaba una consulta más corta? **→** ChromaDB contra la búsqueda exacta, con la misma consulta. Y la consulta completa contra solo la línea Type, y contra solo el kind, que sería no reescribir.

## 32. Exp. 6: resultados
*Experimentos · 6 · ~0:25 · desde el minuto 17:05*

HNSW da exactamente lo mismo que la búsqueda exacta (0,535 y 0,535). Con solo la línea Type, hit@1 cae a 0,29; con solo el kind, a 0,06. El estilo, los colores y la forma son lo que distingue un sofá de otro. **→** Decisión: ChromaDB con la consulta completa que escribe el plan. El query rewriting cuesta, pero vale la pena.

## 33. Exp. 7: Reranking
*Experimentos · 7 · ~0:30 · desde el minuto 17:30*

Mirando los resultados, hit@10 era 0,89 pero hit@1 0,54: el correcto casi siempre está entre los 10 primeros, pero no primero. El cuello de botella era el orden. Advanced RAG propone un reranker: un segundo modelo que mira la consulta y cada candidato juntos. **→** Dos rerankers sobre el top-10: un cross-encoder MiniLM entrenado en MS MARCO, local y gratis, que lee consulta y descripción juntas; y Claude Opus como VLM, que ve las fotos de los 10 y los ordena.

## 34. Exp. 7: resultados
*Experimentos · 7 · ~0:30 · desde el minuto 18:00*

MiniLM empeora (0,42): está entrenado con preguntas y pasajes web, no con descripciones de muebles. El VLM sube hit@1 de 0,54 a 0,69 y MRR de 0,65 a 0,76: mira la foto, que tiene lo que la descripción no dijo. Cuesta unos dos centavos de dólar por búsqueda. **→** Decisión: el reranking con VLM funciona, y nuestro paso de elección ya es eso. No agregamos un paso: la pregunta pasó a ser cuántos candidatos mostrarle, que es el experimento siguiente.

## 35. Exp. 8: Candidatos por pieza
*Experimentos · 8 · ~0:30 · desde el minuto 18:30*

La elección ya es un reranker que mira fotos, pero le pasábamos 3 candidatos por pieza, y con 3 el correcto faltaba en una de cada cuatro piezas. Más candidatos suben ese techo, pero son más fotos: más caro, y más difícil elegir entre parecidos. **→** Sale gratis del experimento anterior: si el VLM ordenó el top-10, lo que elegiría entre los primeros k es el mejor ordenado de esos k. Es un proxy: la elección real además ve el ambiente y el pedido.

## 36. Exp. 8: resultados
*Experimentos · 8 · ~0:30 · desde el minuto 19:00*

La línea punteada es el techo: que el correcto esté entre los k. La sólida es lo que elegiría el VLM. De 3 a 5 candidatos, la elección sube de 0,637 a 0,667; a partir de 8 se aplana. Y la distancia al techo crece: entre muchos parecidos, el VLM no siempre reconoce al correcto. **→** Decisión: 5 candidatos por pieza: casi toda la mejora, y la llamada queda en 45 fotos para 9 piezas.

## 37. Exp. 9: Ampliación y revisión
*Experimentos · 9 · ~0:30 · desde el minuto 19:30*

El primer alcance eran sofás, sillones, mesas y alfombras: 268 productos. Con pedidos reales, la gente pide una biblioteca, una lámpara de pie, cortinas, y no había nada. Y al describir, los subagentes marcaron productos con la foto de otro o mal clasificados: la lista diría una cosa y la imagen otra. **→** Las mismas métricas sobre tres catálogos: el de 268, el ampliado a 855 y el revisado, con 36 productos afuera y 7 kinds corregidos.

## 38. Exp. 9: resultados
*Experimentos · 9 · ~0:30 · desde el minuto 20:00*

Ampliar baja hit@1 de 0,636 a 0,533: hay más productos parecidos y las búsquedas nuevas son de deco, que es más difícil. La revisión casi no lo cambia (0,533 a 0,535), pero hace que el producto de la lista sea el de la foto. Ojo: no son números directamente comparables, porque cambia el universo. **→** Decisión: catálogo ampliado y revisado. Perder unos puntos de hit@1 es el precio de poder amoblar un living completo.

## 39. Exp. 10: Qué catálogo
*Experimentos · 10 · ~0:40 · desde el minuto 20:30*

IKEA es de 2013, con fotos de 500 píxeles, asientos sin medidas y una sola estética, la nórdica. Queríamos ver si con Amazon, o con los dos juntos, salen mejores listas para ambientes reales. **→** Acá no hay ground truth: comparamos de punta a punta, con los mismos ambientes, pedidos y plan; cambia solo el catálogo. Un juez, Claude Opus, ve la foto, el pedido y las dos listas sin saber de qué catálogo es cada una, y elige, en los dos órdenes: una variante gana un ambiente solo si gana en los dos. Primero, en nuestros 5 departamentos.

## 40. Exp. 10: resultados (1 de 2)
*Experimentos · 10 · ~0:25 · desde el minuto 21:10*

IKEA le gana a Amazon 4 a 0; según el juez, Amazon pierde por estilo (maderas oscuras, patas doradas para pedidos nórdicos). Y IKEA + Amazon empataba con IKEA, 2 a 2. **→** Con esto solo, la decisión habría sido quedarse con IKEA. Pero miramos los pedidos.

## 41. Exp. 10: resultados (2 de 2)
*Experimentos · 10 · ~0:40 · desde el minuto 21:35*

Los 5 pedidos eran nórdicos, justo la estética de IKEA, así que sumamos 6 ambientes públicos reales con pedidos de otros estilos: industrial, clásico, bohemio. **→** En los nórdicos siguen empatados, 2 a 2; en los otros estilos, IKEA + Amazon gana 6 a 0, y los productos útiles pasan de 0,46 a 0,71. Los dos órdenes del juez coinciden en el 91% de los ambientes. Y sumar Amazon casi no cambia el retrieval sobre el ground truth de IKEA: hit@1 de 0,535 a 0,525. **→** Decisión: usamos los dos catálogos. Y la lección: con ambientes y pedidos poco variados habríamos tomado la decisión contraria.

## 42. Exp. 11: Cuánto mide el ground truth
*Experimentos · 11 · ~0:30 · desde el minuto 22:15*

Todos los números hasta acá son contra un ground truth con un solo producto correcto por pieza. Pero si el sistema trae un sillón casi igual al anotado, ¿se equivocó? Y si las búsquedas de evaluación las escribiera otro, ¿cambiaría el número? **→** Un juez califica el top-3 de 150 búsquedas con la escala de 2, 1 y 0 que vimos; antes, lo validamos contra el ground truth. Y tres redactores independientes escribieron las mismas búsquedas.

## 43. Exp. 11: resultados
*Experimentos · 11 · ~0:30 · desde el minuto 22:45*

El juez le da 2 al producto anotado el 81% de las veces y a los demás el 5%: es confiable. Con él, el primer candidato sirve en el 75% de los casos, aunque hit@1 sea 0,53: el ground truth subestima. Con tres redactores, hit@1 varía unos 2,6 puntos: diferencias más chicas que eso entre métodos no son señal. **→** Decisión: reportamos hit@1 para comparar métodos, porque es objetivo y barato, y la relevancia graduada para saber cuán útil es de verdad.

## 44. Exp. 12: La imagen
*Experimentos · 12 · ~0:35 · desde el minuto 23:15*

Cuando empezamos a generar imágenes, el modelo no solo agregaba los muebles: redecoraba. En este ejemplo inventó una ventana y movió la biblioteca. El usuario quiere ver su cuarto con esos productos: había que pedirle al modelo que respete el ambiente, y detectar cuándo no lo hace. **→** El mismo ambiente, cuatro versiones del paso de la imagen: la escena guiada que escribe el LLM, la escena libre, libre y sin tope de piezas, y la edición estricta. Medimos con SIFT cuántos puntos de la foto original se reencuentran, y SSIM fuera de los muebles.

## 45. Exp. 12: resultados
*Experimentos · 12 · ~0:30 · desde el minuto 23:50*

Las dos primeras conservan el cuarto (203 y 154 puntos) pero la biblioteca queda chica. La tercera, libre y sin tope: linda, pero inventó una ventana; SIFT lo detecta, reencuentra solo 10 puntos. La edición estricta conserva el cuarto, con 116 puntos, y la biblioteca es la que se pidió. **→** Decisión: edición estricta y un control automático: si SIFT no reencuentra el cuarto, la imagen se descarta y se reintenta, hasta 3 veces. Es el control que vimos en el recorrido.

## 46. Exp. 13: Réplica de un living real
*Experimentos · 13 · ~0:45 · desde el minuto 24:20*

Un living del ground truth, a diferencia de un ambiente vacío, tiene con qué comparar: la foto real. La vaciamos y la volvimos a amoblar con sus 6 muebles. En una primera ronda los ponía todos, pero armaba su propio living. Con cajas dibujadas en la foto los ubicaba mejor, pero las dejaba dibujadas: 2 de 3 imágenes con rectángulos. Y los prompts eran largos. **→** En la segunda ronda, seis formas de decirle dónde va cada mueble: no decirlo, decirlo en palabras, o cajas, rectángulos o 3D, dibujadas en la foto o en una copia aparte, como guía, con 3 imágenes por variante; un mueble está en su lugar si el IoU de su caja con la real es 0,5 o más.

## 47. Exp. 13: los prompts
*Experimentos · 13 · ~0:50 · desde el minuto 25:05*

Los seis prompts son cortos y dicen qué hacer: agregar estos productos al cuarto de la imagen 1, el pedido, la lista, y que el cuarto quede igual. Cambia una sola línea, la de dónde va cada mueble. Sin decirlo: donde lo pondría un diseñador. Con cajas en la foto: cada producto llena su caja, y después hay que borrarlas. Con la guía: la imagen 8 es solo una guía, no dibujes sus cajas. Rehicimos también las de la primera ronda, para no mezclar el largo del prompt con la forma de decir dónde. **→** En palabras, cada producto lleva una o dos frases de dónde va. Las escribió Opus mirando la foto real: mide si alcanza con decirlo en palabras, no si un LLM sabe decidir dónde van los muebles.

## 48. Exp. 13: resultados
*Experimentos · 13 · ~1:10 · desde el minuto 25:55*

Arriba, la primera ronda, de referencia; abajo, las seis nuevas. **→** El prompt corto no empeora nada: con rectángulos da 0,43 y con cajas 3D 0,52, contra 0,40 y 0,48; con tres imágenes, eso es ruido. En palabras casi duplica el IoU de no decir nada, de 0,20 a 0,37, y no deja nada que borrar, pero pocos muebles quedan justo en su lugar: 1,7 de 6. La guía aparte no sirvió: ubica peor que las cajas en la foto, y una de cada tres igual quedó con cajas dibujadas, como esta. La mejor, cajas 3D en la foto: 0,52, 4 de 6 en su lugar, y ninguna quedó dibujada. **→** Decisión: el flujo no cambia, porque sin medidas del cuarto no hay cajas. A futuro, con el cuarto medido, cajas 3D dibujadas en la foto y el prompt corto; la guía aparte se descarta. Hoy, sin medir nada, se podría probar que el plan diga en palabras dónde va cada mueble; ahí lo decidiría el LLM, sin foto que copiar. Es una habitación y tres imágenes por variante: una prueba, no una medición.

## 49. La iteración
*Cierre · ~0:30 · desde el minuto 27:05*

Esto es el ejercicio 4 en un ticket: cada línea es un problema que encontramos usando el sistema, el cambio que hicimos y cuánto mejoró. Todos salen de los experimentos que acabamos de ver.

## 50. El camino
*Cierre · ~0:30 · desde el minuto 27:35*

El resumen en un gráfico: cada barra suma un cambio a la anterior. Arrancamos con el texto del vendedor y una bolsa de palabras: 0,08. **→** La descripción del VLM: 0,50. **→** Qwen3: 0,54. **→** El filtro por tipo no mueve hit@1: lo que protege es hit@10. **→** Y el VLM reordenando el top-10: 0,69. Lo que más movió el número fue qué texto se indexa; lo segundo, que un VLM mire las fotos.

## 51. Cuánto cuesta
*Cierre · ~0:25 · desde el minuto 28:05*

Un pedido cuesta unos 21 centavos de dólar de Claude y 8 por intento de imagen. Describir el catálogo es un costo único, de menos de un centavo por producto. Embeddings y base vectorial corren locales. Todo gasto queda registrado, con topes por cuenta, y las respuestas de los jueces quedan en caché: repetir un experimento no se vuelve a pagar.

## 52. Limitaciones
*Cierre · ~0:30 · desde el minuto 28:30*

Limitaciones: los catálogos son viejos y de uso no comercial; las medidas del ambiente se estiman a ojo; el ground truth es uno solo y con consultas escritas por modelos; la imagen es una visualización, con escala y luz aproximadas; y tenemos pocos ambientes vacíos. **→** A futuro: el catálogo de un vendedor actual, con precio y stock; más ambientes y evaluación humana; que el usuario cambie una pieza y regenere solo eso. Y lo más importante, las medidas reales, que mostramos ahora.

## 53. Futuro: medidas reales
*Pasos a futuro · ~1:00 · desde el minuto 29:00*

Cómo se vería en el producto, sobre el mismo flujo. **→** Uno: medir el ambiente, con una app móvil que use el LiDAR del teléfono para escanear el cuarto: paredes, aberturas y medidas reales. **→** Dos: las medidas de cada producto en la metadata del catálogo, para tener su caja 3D a escala. **→** Tres: ubicar las cajas, de dos maneras: que la IA decida en el plano dónde va cada una, o que una primera generación ponga los muebles, y tomar dónde quedó cada uno para poner ahí su caja a escala. **→** Cuatro: generar, con cada mueble en su caja 3D dibujada en la foto, como en la réplica. **→** Más adelante, con modelos 3D de los productos, si el negocio los tiene, en lugar de cajas: el generador solo tiene que hacerlos verse reales. Lo que falta: las medidas, del ambiente y de los productos; probarlo en muchos cuartos; y elegir cómo se ubican las cajas.

## 54. Conclusiones
*Cierre · ~0:40 · desde el minuto 30:00*

Para cerrar, cinco cosas. Lo que más importó fue el texto que se indexa, no el modelo. **→** El mejor reranker es un VLM mirando las fotos, y nuestro paso de elegir ya lo es. **→** Las métricas con ground truth subestiman, así que hace falta un juez, validado y preguntado en los dos órdenes. **→** El catálogo decide qué se puede recomendar, y evaluar con ambientes variados cambió la decisión. **→** Y la imagen necesita un control automático para que el cuarto sea el del cliente.

## 55. Gracias
*Portada · ~0:05 · desde el minuto 30:40*

Gracias. ¿Preguntas?

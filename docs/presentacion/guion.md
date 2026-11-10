# Guion de la presentación (amoblai)

Generado por `docs/presentacion/build.py` junto con `amoblai.html`: los números salen de los mismos resultados que las slides. 35 slides, unos 31 minutos.

**Cómo se pasa.** En cada experimento, primero se ve solo el porqué, la pregunta y el experimento. **Se cuentan esas dos cosas antes de avanzar.** La flecha (o espacio) muestra los resultados; otra flecha, la decisión. Flecha atrás vuelve un paso. Con `amoblai.html?todo` se ve todo de entrada (para revisar o imprimir).

**Reparto sugerido** (a definir entre los tres):
- Parte 1: slides 1 a 12 (Portada → Los hiperparámetros que decidimos con experimentos), unos 9 min.
- Parte 2: slides 13 a 23 (Métricas → Base vectorial y query rewriting), unos 9 min.
- Parte 3: slides 24 a 35 (Reranking (Advanced RAG) → Conclusiones), unos 13 min.

Si falta tiempo, se pueden pasar rápido los experimentos 4 y 5 y la slide de costos (los marcados con *).

## 1. Portada
*~0:30 min · desde el minuto 0:00*

Somos Juan Bautista, Matías y Junior. amoblai responde una pregunta concreta: tengo este ambiente vacío, ¿qué compro y cómo queda? Sacás una foto, escribís qué querés, y te devuelve una lista de productos reales de un catálogo y la imagen del mismo ambiente con esos productos.

## 2. ¿Qué compro para este ambiente, y cómo queda?
*El problema · ~0:48 min · desde el minuto 0:30*

Cuando te mudás a un lugar vacío tenés que decidir qué comprar sin poder verlo puesto. Los catálogos muestran cada mueble suelto, sobre fondo blanco, y las fotos de ambientes muestran la casa de otro. Nosotros queremos responder, para este ambiente y este pedido: qué productos reales, que se puedan comprar, van; cuántos y de qué medida; y cómo queda el ambiente con ellos.

## 3. Foto + pedido → lista de compra + imagen
*El producto · ~1:00 min · desde el minuto 1:18*

Así se usa. La entrada es una foto del ambiente y un pedido en texto libre, como este: un rincón de lectura con una biblioteca alta de madera oscura. La salida son dos cosas: la lista de compra, con productos reales del catálogo y cuántas unidades de cada uno (acá, dos bibliotecas iguales), y la foto del mismo ambiente con esos productos puestos.

## 4. Recomendaciones atadas a productos que existen
*Por qué RAG · ~0:48 min · desde el minuto 2:18*

¿Por qué un RAG y no un LLM o un modelo de imagen solos? Un LLM sabe de decoración, pero no sabe qué hay en un catálogo: te recomienda un sillón de cuero coñac que nadie vende. Un modelo de imagen amobla lindo, pero inventa los muebles: no hay nada que comprar. Con RAG, el catálogo es la base de conocimiento: el LLM decide qué hace falta, el retrieval trae candidatos reales y el VLM elige mirando sus fotos. Y la imagen se genera desde las fotos de los productos elegidos. No es un Q&A: la consulta es una foto y un pedido abierto, y la respuesta es una combinación de productos que tiene que funcionar junta.

## 5. Datos
*Parte 1 · ~0:12 min · desde el minuto 3:06*

Primero, los datos: con qué catálogo trabajamos, cómo medimos el retrieval y con qué ambientes probamos.

## 6. El catálogo: productos IKEA descritos por un VLM
*Datos · el catálogo · ~0:54 min · desde el minuto 3:18*

El catálogo base es el dataset IKEA de Tautkute y otros, de uso no comercial. Nos quedamos con lo de living y comedor: muebles, iluminación, textiles y deco, 855 productos, 819 después de la revisión. El texto de IKEA es pobre, así que un VLM describe cada producto mirando su foto en 8 líneas fijas (esta es una). Eso es lo que se indexa, y el experimento 1 muestra por qué. Los problemas del catálogo: fotos de 500 píxeles, asientos sin medidas y productos que comparten la foto de otra medida.

## 7. Ambientes reales con sus muebles: el ground truth del retrieval
*Datos · ground truth · ~0:54 min · desde el minuto 4:12*

Para medir el retrieval necesitamos saber cuál es el producto correcto. El dataset trae 65 fotos de livings y comedores reales de IKEA con sus productos anotados. Por cada mueble visible, un subagente escribe la búsqueda como la escribiría nuestro plan, mirando el ambiente: 864 búsquedas, 549 con su producto en el catálogo. Una búsqueda acierta si el anotado sale primero (hit@1) o entre los k primeros. Los intervalos de confianza son por bootstrap por ambiente, porque las búsquedas de un mismo ambiente no son independientes.

## 8. Ambientes vacíos reales para probar de punta a punta
*Datos · ambientes vacíos · ~0:48 min · desde el minuto 5:06*

Para probar el sistema completo hacen falta ambientes vacíos reales. Tenemos 11: 5 de departamentos nuestros y 6 públicos de Wikimedia Commons y Flickr, con licencia Creative Commons, elegidos entre 22 que revisamos uno por uno para descartar renders y fotos generadas con IA. Cada uno tiene un pedido escrito como lo escribiría un usuario que sabe pedir; los públicos, con estilos distintos del nórdico. Acá no hay ground truth: medimos con un juez y con métricas de imagen.

## 9. Arquitectura
*Parte 2 · ~0:12 min · desde el minuto 5:54*

Después, la arquitectura: de dónde venimos y qué variantes probamos.

## 10. Por qué dejamos la búsqueda por imagen
*Arquitectura · v0 → v1 · ~1:00 min · desde el minuto 6:06*

La primera versión buscaba por imagen: detectaba cada mueble en la foto con Grounding DINO, lo recortaba con SAM y buscaba la foto del catálogo más parecida con DINOv3. Eso sirve para encontrar este sofá, pero nuestro caso es un ambiente vacío: no hay nada que recortar. La v1 busca por texto: un LLM escribe el producto ideal en el mismo formato que el catálogo. Con el mismo ground truth, la v1 da 0,62 de hit@1 contra 0,51 de la v0, y además funciona con el ambiente vacío.

## 11. Dos pipelines: indexing offline y consulta por pedido
*Arquitectura · v1 · ~1:18 min · desde el minuto 7:06*

La arquitectura tiene dos pipelines. El de indexing corre una vez: catálogo, descripciones del VLM, embeddings con Qwen3 y ChromaDB. El de consulta corre por pedido. Plan: Claude Opus lee la foto y el pedido, decide las piezas, su tipo, la medida máxima y escribe la consulta ideal. Retrieve: Qwen3 y ChromaDB con filtros duros, k candidatos por pieza. Choose: Claude mira las fotos de los candidatos, elige uno por pieza pensando la combinación, y cuántas unidades; solo puede elegir productos recuperados. Y la imagen: Nano Banana 2 recibe la foto del ambiente y las de los productos, y un control automático descarta la imagen si cambió el cuarto.

## 12. Los hiperparámetros que decidimos con experimentos
*Arquitectura · variantes · ~0:30 min · desde el minuto 8:24*

Cada fila de esta tabla es una decisión de la arquitectura que tomamos con un experimento, con todo lo demás fijo. Los vamos a ver en este orden, que es más o menos el orden en que los hicimos: cada uno deja su decisión en la configuración del siguiente.

## 13. Métricas
*Parte 3 · ~0:12 min · desde el minuto 8:54*

Antes de los experimentos, las métricas, para que cada número que mostremos se entienda.

## 14. Con ground truth: ¿trae el producto correcto, y arriba?
*Métricas · retrieval · ~0:54 min · desde el minuto 9:06*

Las métricas de retrieval, donde sí hay ground truth. hit@k: si el anotado está entre los k primeros; hit@1 es encontrarlo primero, y hit@k con k igual a los candidatos que ve el VLM es el techo de lo que puede elegir. MRR: el promedio de uno sobre la posición del correcto, premia que esté arriba. Context recall y context precision son las de RAGAS: cuántos de los productos de un ambiente aparecen entre los candidatos, y cuán arriba quedan. NDCG admite relevancia graduada. Y los intervalos de confianza: si dos métodos tienen intervalos que se pisan, con estos datos no los podemos distinguir.

## 15. Sin un único correcto: jueces validados y comparaciones de a pares
*Métricas · la respuesta · ~0:54 min · desde el minuto 10:00*

Cuando no hay un único correcto usamos jueces, pero validados. Relevancia graduada: un LLM califica el top-3 con 2, 1 o 0, y antes chequeamos que le dé 2 al producto anotado. RAGAS sobre la explicación de cada elección: faithfulness, si lo que dice se sostiene con lo que vio, y answer relevance, si responde al pedido. Para comparar variantes sin ground truth, un juez de a pares en los dos órdenes, y reportamos cuánto coinciden los dos órdenes. Y el costo de cada llamada.

## 16. La imagen: mismo cuarto, mismos productos, lo que se pidió
*Métricas · la imagen y el resto · ~0:54 min · desde el minuto 10:54*

Para la imagen medimos tres cosas. Que sea el mismo cuarto: SIFT reencuentra puntos de la foto original y mide cuánto se movió la cámara, y SSIM compara lo que no es mueble. Que sean los mismos productos: detectamos cada mueble, lo recortamos y vemos si el más parecido del catálogo es el de la lista. Y que sea lo que se pidió: SigLIP 2 entre el pedido y la imagen, y contamos lo que falta, lo repetido y lo inventado. Además, reproducibilidad, con tres redactores, y el espacio de embeddings.

## 17. Experimentos
*Parte 4 · ~0:18 min · desde el minuto 11:48*

Ahora los experimentos. Todos siguen el mismo orden: primero por qué lo hicimos y qué queríamos ver, que está arriba en cada slide; después cómo es el experimento, a la izquierda; y recién ahí mostramos los resultados y la decisión, que aparecen con la flecha.

## 18. Qué texto se indexa
*Experimento 1 · ~1:12 min · desde el minuto 12:06*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): Lo primero que miramos fue qué texto trae el catálogo. IKEA tiene nombre, tipo, colores y una frase de marketing del estilo “The armchair is lightweight and easy to move”. Pero nadie pide así: se pide un sillón nórdico, de madera clara, con tapizado crema, y todo eso está en la foto. La pregunta era si alcanzaba con el texto del vendedor o si valía la pena describir cada producto mirando su foto, un costo que se paga una sola vez.
2. **El experimento:** Indexamos tres textos y corrimos las mismas 549 búsquedas del ground truth, con todo lo demás fijo (Qwen3, filtro por tipo): el texto del vendedor; la descripción de 8 líneas que escribe un VLM mirando la foto, en el mismo formato en que el plan escribe la consulta; y esa descripción con el nombre comercial adelante.
3. **→ Resultados** (flecha): Con el texto del vendedor, hit@1 da 0,13; con la descripción del VLM, 0,54: más de cuatro veces. Es el cambio más grande de todo el trabajo. El nombre comercial adelante empeora: con el mismo filtro, de 0,53 a 0,42. NOLMYRA no le dice nada al embedding.
4. **→ Decisión** (flecha): Indexamos solo la descripción del VLM. Y queda una idea que vuelve en todo el trabajo: la consulta y el documento escritos en el mismo formato.

## 19. Embedder
*Experimento 2 · ~1:12 min · desde el minuto 13:18*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): Con el texto resuelto, la pregunta natural es cuánto aporta el modelo de embeddings. Un modelo más grande cuesta memoria y tiempo, y nos pusimos la restricción de que el retrieval corra local, en CPU, sin pagar una API. Queríamos ver cuánto gana un modelo entrenado contra una línea de base sin modelo.
2. **El experimento:** Tres embedders sobre el mismo texto y las mismas búsquedas: hashing, una bolsa de palabras hasheada, sin ningún modelo; BGE-base, de 110 millones de parámetros; y Qwen3-Embedding, de 600 millones.
3. **→ Resultados** (flecha): Gana Qwen3, con 0,54. Pero el hashing queda cerca (0,51) y BGE último (0,48). La explicación: las descripciones usan vocabulario controlado, los estilos y los kinds salen de listas cerradas, así que hasta contar palabras funciona bastante. Qwen3 gana más claro en MRR y en las búsquedas difíciles.
4. **→ Decisión** (flecha): Qwen3-Embedding-0.6B (Apache 2.0, corre en CPU). La lección: el formato del texto vale más que el modelo.

## 20. Filtros duros
*Experimento 3 · ~1:12 min · desde el minuto 14:30*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): El plan sabe qué pieza está buscando: un sofá, una lámpara. Por similitud sola, una mesa nórdica de madera clara se puede parecer más a la consulta que un sofá. Un filtro por metadata lo evita y es gratis, pero tiene un riesgo: si el plan y el catálogo no coinciden en la categoría, el producto correcto queda afuera. Queríamos ver si conviene filtrar, y con qué granularidad.
2. **El experimento:** Tres opciones: sin filtro; filtro por tipo, 14 categorías gruesas como sofá, mesa o lámpara; y filtro por kind, 41 categorías finas como mesa ratona o mesa de comedor. En ChromaDB el filtro va como where. Miramos hit@1 y sobre todo hit@10.
3. **→ Resultados** (flecha): Con descripciones buenas, hit@1 casi no cambia. Pero el filtro por kind resta: en hit@10 da 0,86 contra 0,89 del filtro por tipo. Si el plan pide una mesa auxiliar y el catálogo la tiene como mesa ratona, el filtro fino la deja afuera. El de tipo protege de los errores gruesos sin ese costo.
4. **→ Decisión** (flecha): Filtrar siempre, más las medidas máximas que estima el plan. Con qué granularidad quedó abierto: el flujo filtra por los kinds que elige el plan, que puede dar más de uno (mesa ratona o auxiliar) para no dejar afuera al correcto. La diferencia con el filtro por tipo es de un punto en hit@1, dentro del intervalo, y tres en hit@10; pasar el flujo a tipo es lo próximo que probaríamos.

## 21. Splitting *
*Experimento 4 · ~0:36 min · desde el minuto 15:42*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): En la materia vimos que el chunking es una de las decisiones centrales de un RAG. Nuestros documentos son cortos, de 60 a 90 palabras, pero tienen 8 líneas con roles distintos: tipo, estilo, colores, materiales. La hipótesis era que comparar línea por línea, colores contra colores, podía ser más preciso que un solo vector por producto.
2. **El experimento:** Tres formas: un documento por producto, con las 8 líneas juntas; un chunk por línea, donde el producto vale lo que su línea más parecida a la consulta; y línea contra línea, cada una contra la del mismo rótulo en la consulta, promediado.
3. **→ Resultados** (flecha): Gana un documento por producto (0,54). Línea contra línea queda cerca (0,51) y el chunk por línea se desploma (0,27): una línea suelta como “Colors: light wood” se parece a cualquier cosa de madera clara. Partir pierde el contexto.
4. **→ Decisión** (flecha): Un documento por producto. Con documentos tan cortos no hay nada que partir.

## 22. Dimensión del embedding *
*Experimento 5 · ~0:36 min · desde el minuto 16:18*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): Qwen3 se entrenó con Matryoshka: las primeras componentes del vector concentran la información, así que se puede truncar sin reentrenar. Con 819 productos no importa, pero en un catálogo de millones la memoria y la latencia crecen con la dimensión. Queríamos saber cuánto se puede achicar sin perder.
2. **El experimento:** Truncamos los vectores a 32, 64, 128, 256, 512 y 1024 componentes, los renormalizamos y corrimos las mismas búsquedas.
3. **→ Resultados** (flecha): Con 512 da prácticamente lo mismo que con 1024 (0,53 contra 0,54), con la mitad de memoria. Por debajo de 128 cae rápido: con 32, 0,43.
4. **→ Decisión** (flecha): Para este catálogo dejamos 1024 porque no cuesta nada; si creciera, indexaríamos con 512.

## 23. Base vectorial y query rewriting
*Experimento 6 · ~1:12 min · desde el minuto 16:54*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): Dos dudas. Primero, pasamos de una búsqueda exacta con numpy a ChromaDB, que usa HNSW, un índice aproximado: había que verificar que no perdiera resultados. Segundo, el query rewriting: el plan escribe para cada pieza el producto ideal en 8 líneas, y eso cuesta tokens y latencia en cada pedido. Queríamos ver si una consulta más corta alcanzaba.
2. **El experimento:** ChromaDB contra la búsqueda exacta, con la misma consulta. Y la consulta completa contra solo la línea Type, y contra solo el nombre del kind, que sería no reescribir.
3. **→ Resultados** (flecha): HNSW da exactamente lo mismo que la búsqueda exacta (0,535 y 0,535). Con solo la línea Type, hit@1 cae a 0,29; con solo el kind, a 0,06. El estilo, los colores y la forma son lo que distingue un sofá de otro.
4. **→ Decisión** (flecha): ChromaDB con la consulta completa que escribe el plan. El query rewriting cuesta, pero vale la pena.

## 24. Reranking (Advanced RAG)
*Experimento 7 · ~1:12 min · desde el minuto 18:06*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): Mirando los resultados vimos que hit@10 era 0,89 pero hit@1 0,54: el producto correcto casi siempre está entre los 10 primeros, pero no primero. El cuello de botella era el orden. Advanced RAG propone un reranker, un segundo modelo que mira la consulta y cada candidato juntos. Queríamos ver si eso ordena mejor, y con qué tipo de modelo.
2. **El experimento:** Dos rerankers sobre el top-10: un cross-encoder MiniLM entrenado en MS MARCO, local y gratis, que lee la consulta y la descripción juntas; y Claude Opus como VLM, que ve la consulta y las fotos de los 10 candidatos y los ordena.
3. **→ Resultados** (flecha): MiniLM empeora (0,42): está entrenado con preguntas y pasajes web, no con descripciones de muebles. El VLM sube hit@1 de 0,54 a 0,69 y MRR de 0,65 a 0,76: mira la foto, que tiene lo que la descripción no dijo. Cuesta unos dos centavos de dólar por búsqueda.
4. **→ Decisión** (flecha): El reranking con VLM funciona, y nuestro paso choose ya es eso: Claude elige mirando las fotos de los candidatos. No agregamos un paso: la pregunta pasó a ser cuántos candidatos mostrarle, que es el experimento siguiente.

## 25. Candidatos por pieza
*Experimento 8 · ~1:12 min · desde el minuto 19:18*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): El paso choose ya es un reranker que mira fotos, pero le pasábamos 3 candidatos por pieza, y con 3 el correcto faltaba en una de cada cuatro piezas. Más candidatos suben ese techo, pero son más fotos en la llamada: más caro, y más difícil elegir entre muchos parecidos. Queríamos encontrar el k que maximiza la chance de que el VLM elija bien.
2. **El experimento:** Lo sacamos gratis del experimento anterior: si el VLM ordenó el top-10, lo que elegiría entre los primeros k es el mejor ordenado de esos k. Así sale la curva para k de 1 a 10 sin pagar nada más. Es un proxy: el choose real además ve el ambiente y el pedido.
3. **→ Resultados** (flecha): La línea punteada es el techo: que el correcto esté entre los k. La sólida es lo que elegiría el VLM. De 3 a 5 candidatos, la elección sube de 0,637 a 0,667; a partir de 8 se aplana. Y la distancia al techo crece: entre muchos parecidos, el VLM no siempre reconoce al correcto.
4. **→ Decisión** (flecha): 5 candidatos por pieza: casi toda la mejora, y la llamada queda en 45 fotos para 9 piezas.

## 26. Catálogo: ampliación y revisión
*Experimento 9 · ~1:12 min · desde el minuto 20:30*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): El primer alcance eran sofás, sillones, mesas y alfombras: 268 productos. Con pedidos reales, la gente pide una biblioteca, una lámpara de pie, cortinas, y no había nada. Así que ampliamos. Y mientras los subagentes describían los productos, marcaron varios con la foto de otro producto o mal clasificados: la lista diría una cosa y la imagen mostraría otra. Queríamos saber cuánto cuesta ampliar en retrieval y qué cambia la limpieza.
2. **El experimento:** Las mismas métricas sobre tres catálogos: el de 268, el ampliado a 855 (guardado, iluminación, textiles y deco) y el revisado, con 36 productos afuera y 7 kinds corregidos.
3. **→ Resultados** (flecha): Ampliar baja hit@1 de 0,636 a 0,533: hay más productos parecidos y las búsquedas nuevas son de deco, que es más difícil. La revisión casi no lo cambia (0,533 a 0,535), pero hace que el producto de la lista sea el de la foto. Ojo: no son números directamente comparables, porque cambia el universo.
4. **→ Decisión** (flecha): Catálogo ampliado y revisado. Perder unos puntos de hit@1 es el precio de poder amoblar un living completo.

## 27. Qué catálogo
*Experimento 10 · ~2:00 min · desde el minuto 21:42*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): El catálogo de IKEA tiene límites: es de 2013, las fotos son de 500 píxeles, los asientos no tienen medidas y tiene una sola estética, la nórdica. Encontramos Amazon Berkeley Objects, un dataset académico con listados reales de Amazon, con medidas y fotos grandes. Queríamos ver si con otro catálogo, o con los dos juntos, salen mejores listas para ambientes reales.
2. **El experimento:** Acá no hay ground truth: nadie anotó qué sofá de Amazon va en un living vacío. Comparamos de punta a punta: mismos ambientes, mismos pedidos y el mismo plan; cambia solo el catálogo. Un juez, Claude Opus, ve la foto, el pedido y las dos listas sin saber de qué catálogo es cada una, y elige. Se le pregunta en los dos órdenes, y una variante gana un ambiente solo si gana en los dos. Primero lo corrimos en nuestros 5 departamentos.
3. **→ Resultados** (flecha): Primera tabla: IKEA le gana a Amazon 4 a 0; según el juez, Amazon pierde por estilo (maderas oscuras, patas doradas para pedidos nórdicos). Y IKEA + Amazon empataba con IKEA. Ahí vimos que los 5 pedidos eran nórdicos, justo la estética de IKEA, así que sumamos 6 ambientes públicos reales con pedidos de otros estilos: industrial, clásico, bohemio. Segunda tabla: en los nórdicos siguen empatados; en los otros estilos, IKEA + Amazon gana 6 a 0, y los productos útiles pasan de 0,46 a 0,71. Los dos órdenes del juez coinciden en el 91% de los ambientes. Y sumar Amazon casi no cambia el retrieval sobre el ground truth de IKEA: hit@1 de 0,535 a 0,525.
4. **→ Decisión** (flecha): Usamos los dos catálogos. Y la lección: con ambientes y pedidos poco variados habríamos tomado la decisión contraria.

## 28. ¿Cuánto mide el ground truth?
*Experimento 11 · ~1:12 min · desde el minuto 23:42*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): Todos los números hasta acá son contra un ground truth con un solo producto correcto por pieza. Pero si el sistema trae un sillón casi igual al anotado, ¿se equivocó? Y las búsquedas de evaluación las escribieron subagentes: si las escribiera otro, ¿cambiaría el número? Queríamos saber cuánto mide realmente el ground truth.
2. **El experimento:** Dos cosas. Un juez califica el top-3 de 150 búsquedas: 2 si es el mismo o indistinguible, 1 si es una alternativa aceptable, 0 si no sirve; antes de creerle, lo validamos contra el ground truth. Y tres redactores independientes escribieron las mismas búsquedas.
3. **→ Resultados** (flecha): El juez le da 2 al producto anotado el 81% de las veces y a los demás el 5%: es confiable. Con él, el primer candidato sirve en el 75% de los casos, aunque hit@1 sea 0,53: el ground truth subestima. Con tres redactores, hit@1 varía unos 2,6 puntos: diferencias más chicas que eso entre métodos no son señal.
4. **→ Decisión** (flecha): Reportamos hit@1 para comparar métodos, porque es objetivo y barato, y la relevancia graduada para saber cuán útil es de verdad.

## 29. La imagen: del cuarto reimaginado al cuarto del cliente
*Experimento 12 · ~1:30 min · desde el minuto 24:54*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): Cuando empezamos a generar imágenes vimos que el modelo no solo agregaba los muebles: redecoraba. En este ejemplo inventó una ventana y movió la biblioteca. Para el usuario eso no sirve: quiere ver su cuarto con esos productos. Queríamos encontrar cómo pedirle al modelo que respete el ambiente, y cómo detectar automáticamente cuando no lo hace.
2. **El experimento:** El mismo ambiente, cuatro versiones del paso de la imagen. Las dos de arriba son con el pedido corto, de 6 piezas: una escena que escribe el LLM describiendo dónde va cada cosa, y una escena libre. Las dos de abajo, con el pedido completo, de 9 piezas: libre, y una edición estricta, que exige el mismo encuadre, las mismas paredes y aberturas y exactamente los productos de las fotos. Medimos con SIFT cuántos puntos de la foto original se reencuentran, y SSIM fuera de los muebles.
3. **→ Resultados** (flecha): Arriba, las dos primeras conservan el cuarto pero la biblioteca queda chica. Abajo a la izquierda, libre y sin tope: linda, pero inventó una ventana; SIFT lo detecta, reencuentra solo 10 puntos. La edición estricta conserva el cuarto, con 116 puntos, y la biblioteca es la que se pidió.
4. **→ Decisión** (flecha): Edición estricta y un control automático: si SIFT no reencuentra el cuarto, la imagen se descarta y se reintenta, hasta 3 veces. En la slide siguiente se ve funcionando.

## 30. De punta a punta, en un departamento real
*Resultado · ~0:48 min · desde el minuto 26:24*

Y así queda todo junto, con la configuración final, en un departamento real. En el living, los dos primeros intentos de la imagen salieron lindos pero con la cámara corrida, y el control los descartó solo; el tercero quedó. El comedor pasó al primer intento.

## 31. La iteración: qué falló, qué cambiamos y cuánto mejoró
*Ejercicio 4 · ~0:42 min · desde el minuto 27:12*

Esto es el ejercicio 4 en una tabla: cada fila es un problema que encontramos usando el sistema, el cambio que hicimos y cuánto mejoró. Todos salen de los experimentos que acabamos de ver.

## 32. El camino: de 0,08 a 0,69 de hit@1
*Resumen de los experimentos · ~0:42 min · desde el minuto 27:54*

El resumen en un gráfico: cada barra suma un cambio a la anterior. Del texto del vendedor con una bolsa de palabras (0,08) al VLM reordenando el top-10 (0,69). Lo que más movió el número fue qué texto se indexa; lo segundo, que un VLM mire las fotos.

## 33. Cuánto cuesta un pedido *
*Costo · ~0:30 min · desde el minuto 28:36*

Un pedido cuesta unos 20 centavos de dólar de Claude y 8 por intento de imagen. Describir el catálogo es un costo único, de menos de un centavo por producto. Embeddings y base vectorial corren locales. Todo gasto queda registrado, con topes por cuenta, y las respuestas de los jueces quedan en caché: repetir un experimento no se vuelve a pagar.

## 34. Limitaciones y trabajo futuro
*Cierre · ~0:48 min · desde el minuto 29:06*

Limitaciones: los catálogos son viejos y de uso no comercial; las medidas del ambiente se estiman a ojo; el ground truth es uno solo y con consultas escritas por modelos; la imagen es una visualización, con escala y luz aproximadas; y tenemos pocos ambientes vacíos. Como trabajo futuro: medidas reales, con un metro en la foto o un modelo de profundidad; el catálogo de un vendedor actual, con precio y stock; más ambientes y evaluación humana; y que el usuario pueda cambiar una pieza y regenerar solo eso.

## 35. Conclusiones
*Cierre · ~1:00 min · desde el minuto 29:54*

Para cerrar, cinco cosas. Lo que más importó fue el texto que se indexa, no el modelo. El mejor reranker es un VLM mirando las fotos, y nuestro paso de elegir ya lo es. Las métricas con ground truth subestiman, así que hace falta un juez, validado y preguntado en los dos órdenes. El catálogo decide qué se puede recomendar, y evaluar con ambientes variados cambió la decisión. Y la imagen necesita un control automático para que el cuarto sea el del cliente. Gracias.

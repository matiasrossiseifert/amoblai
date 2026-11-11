# Guion de la presentación (amoblai)

Generado por `docs/presentacion/build.py` junto con `amoblai.html`: los números salen de los mismos resultados que las slides y los extractos de los prompts, de los archivos de `src/amoblai/prompts/`. 41 slides, unos 31 minutos (31:00).

**El recorrido** (slides 5 a 18). Arriba de cada lámina va el mapa de las once fases: la fase de la que se habla, encendida; las ya vistas, marcadas. Se sigue un mismo pedido real (el living de Caballito) de la foto a la lista. La última lámina del recorrido es el mismo mapa con un pin por experimento, sobre la fase que decidió; cada lámina de experimento repite ese pin en un minimapa.

**Cómo se pasa.** En cada experimento, primero se ve solo el porqué, la pregunta y el experimento. **Se cuentan esas dos cosas antes de avanzar.** La flecha (o espacio) muestra los resultados; otra flecha, la decisión. Flecha atrás vuelve un paso. Con `amoblai.html?todo` se ve todo de entrada (para revisar o imprimir).

**Reparto sugerido** (a definir entre los tres):
- Parte 1: slides 1 a 12 (Portada → Filtro duro por kind, después coseno: 5 candidatos), unos 9 min.
- Parte 2: slides 13 a 28 (Opus ve el cuarto y los 5 de cada pieza, y elige el conjunto → Splitting), unos 11 min.
- Parte 3: slides 29 a 41 (Dimensión del embedding → Conclusiones), unos 11 min.

Si falta tiempo, se pueden pasar rápido los experimentos 4 y 5 y la slide de costos (los marcados con *).

## 1. Portada
*~0:30 min · desde el minuto 0:00*

Somos Juan Bautista, Matías y Junior. amoblai responde una pregunta concreta: tengo este ambiente vacío, ¿qué compro y cómo queda? Sacás una foto, escribís qué querés, y te devuelve una lista de productos reales de un catálogo y la imagen del mismo ambiente con esos productos.

## 2. ¿Qué compro para este ambiente, y cómo queda?
*El problema · ~0:42 min · desde el minuto 0:30*

Cuando te mudás a un lugar vacío tenés que decidir qué comprar sin poder verlo puesto. Los catálogos muestran cada mueble suelto, sobre fondo blanco, y las fotos de ambientes muestran la casa de otro. Nosotros queremos responder, para este ambiente y este pedido: qué productos reales, que se puedan comprar, van; cuántos y de qué medida; y cómo queda el ambiente con ellos.

## 3. Foto + pedido → lista de compra + imagen
*El producto · ~0:48 min · desde el minuto 1:12*

Así se usa. La entrada es una foto del ambiente y un pedido en texto libre, como este: un rincón de lectura con una biblioteca alta de madera oscura. La salida son dos cosas: la lista de compra, con productos reales del catálogo y cuántas unidades de cada uno (acá, dos bibliotecas iguales), y la foto del mismo ambiente con esos productos puestos.

## 4. Recomendaciones atadas a productos que existen
*Por qué RAG · ~0:42 min · desde el minuto 2:00*

¿Por qué un RAG? Un LLM solo sabe de decoración, pero no qué hay en un catálogo: te recomienda un sillón de cuero coñac que nadie vende. Un modelo de imagen solo amobla lindo, pero inventa los muebles. Con RAG, el catálogo es la base de conocimiento: el LLM decide qué hace falta, el retrieval trae candidatos reales y el VLM elige mirando sus fotos; y la imagen se genera desde las fotos de los productos elegidos. Y no es un Q&A: la consulta es una foto y un pedido abierto, y la respuesta, una combinación que tiene que funcionar junta.

## 5. El recorrido
*Parte 1 · ~0:12 min · desde el minuto 2:42*

Primero, el recorrido: vamos a pasar por todo el pipeline, fase por fase, con un mapa arriba que se va encendiendo.

## 6. Once fases: una vez offline, y por cada pedido
*El recorrido · el mapa · ~0:42 min · desde el minuto 2:54*

Este es el mapa completo, y lo vamos a recorrer fase por fase. Hay dos pipelines. Arriba, lo que se hace una vez, offline: el catálogo, la descripción de cada producto y el índice. Abajo, lo que pasa en cada pedido: entran la foto y el pedido, el plan decide las piezas, la búsqueda trae candidatos del índice, la elección arma el conjunto, y después la escena, la imagen y el control, hasta la lista y la foto amoblada. Por pedido trabajan solo tres modelos: Opus en el plan y la elección, y Nano Banana 2 en la imagen.

## 7. Dos catálogos de productos reales, con foto
*El recorrido · fase 1 de 11 · Catálogo · ~0:42 min · desde el minuto 3:36*

Fase uno, el catálogo. Son dos. El dataset de IKEA de Tautkute y otros: de sus 2.191 productos empezamos con 268 muebles, lo ampliamos a 855 de living y comedor y, revisado, quedaron 819; eso lo decide el experimento 9. Y Amazon Berkeley Objects, un dataset académico con listados reales de Amazon: de casi 150 mil listados quedaron 683. El flujo usa los dos, 1.502 productos, por el experimento 10. De cada uno guardamos las fotos, el tipo, el kind y las medidas cuando hay. Así viene el sofá que va a elegir el flujo: el texto es marketing y no tiene medidas.

## 8. Un VLM mira cada foto y escribe el producto en 8 líneas
*El recorrido · fase 2 de 11 · Descripción · ~1:00 min · desde el minuto 4:18*

Fase dos: la descripción. Un VLM mira la foto de cada producto y lo escribe en ocho líneas fijas: tipo, uso, estilo, materiales, colores, forma, sensación y con qué combina. Es el mismo sofá: a la izquierda, lo que dice IKEA; en el medio, lo que escribió el modelo. El prompt pide exactamente esas ocho líneas, el estilo de una lista cerrada, sin marca, precio ni medidas, y nada de lo que el producto no es, porque el embedding no entiende la negación. La v2 fue para los muebles; la v3, cuando sumamos lámparas, textiles y deco; y una versión por la API para Amazon, que además da el kind y descarta lo que no es de un living. El experimento 1 decidió indexar esto y no el texto del vendedor.

## 9. Un vector por producto: Qwen3, local, en ChromaDB
*El recorrido · fase 3 de 11 · Índice · ~1:00 min · desde el minuto 5:18*

Fase tres: el índice. Se embebe la descripción entera, un documento por producto: es corta, y partirla en líneas pierde contexto, como muestra el experimento 4. El modelo es Qwen3-Embedding de 600 millones de parámetros, local, en CPU, con el último token como vector y sin instrucción de consulta, porque la consulta se escribe igual que el documento. Da 1.024 dimensiones; por Matryoshka se pueden truncar, y con 512 alcanza. Van a ChromaDB, con un índice HNSW en espacio coseno y la metadata que usan los filtros. Antes hubo una v0 que buscaba por imagen, recortando muebles de una foto amoblada: no sirve con un ambiente vacío, y con el mismo ground truth daba 0,51 contra 0,62.

## 10. Entra una foto del ambiente vacío y un pedido libre
*El recorrido · fase 4 de 11 · Foto + pedido · ~0:24 min · desde el minuto 6:18*

Fase cuatro, lo que entra: una foto del ambiente vacío, que es la que se amobla, y un pedido en texto libre, en castellano, como lo escribiría el usuario. Se pueden sumar otras fotos del mismo ambiente: van solo al LLM, para entender el lugar; el modelo de imagen recibe solo la primera. Vamos a seguir este living hasta el final.

## 11. El plan reescribe el pedido: una consulta por pieza
*El recorrido · fase 5 de 11 · Plan · ~1:06 min · desde el minuto 6:42*

Fase cinco, el plan, que es nuestro query rewriting. Opus 5.5 recibe la foto y el pedido y hace de diseñador: primero lee el ambiente, después decide qué piezas hacen falta y, para cada una, da el kind, que va a ser el filtro, la medida máxima que entra, y la consulta: el producto ideal escrito en las mismas ocho líneas que el catálogo. Del pedido “un sofá de tres cuerpos gris claro” sale esta pieza: kind sofá, hasta 240 centímetros de ancho, y su consulta. Para este living propuso ocho piezas. El prompt tuvo cuatro versiones: la primera confundía silla con sillón; la v2 agregó leer el ambiente y la lista de kinds; la v3 pidió terminar el ambiente con lámparas y deco; y la v4 sacó el tope de piezas. El experimento 6 mostró que escribir la consulta completa es lo que más pesa antes de buscar. Cuesta unos siete centavos.

## 12. Filtro duro por kind, después coseno: 5 candidatos
*El recorrido · fase 6 de 11 · Búsqueda · ~0:48 min · desde el minuto 7:48*

Fase seis, la búsqueda. Para cada pieza, primero un filtro duro en ChromaDB: el kind que eligió el plan y las medidas máximas, con un 15 por ciento de margen porque salen de una foto; un producto sin medidas pasa. Después, el coseno de Qwen3 entre la consulta y las descripciones, y quedan los 5 más cercanos. Estos son los cinco sofás para este pedido. El filtro lo decidió el experimento 3, y los 5 candidatos, el 8. También probamos un reranker después de la búsqueda: un cross-encoder de texto empeoró, y Opus mirando las fotos mejoró. No lo agregamos como paso: la fase siguiente ya mira las fotos.

## 13. Opus ve el cuarto y los 5 de cada pieza, y elige el conjunto
*El recorrido · fase 7 de 11 · Elección · ~0:54 min · desde el minuto 8:36*

Fase siete, la elección. Opus recibe la foto del ambiente y los cinco candidatos de cada pieza: acá son 41 imágenes, cada candidato con su id, su línea Type y su medida, sin el nombre comercial. El prompt le pide elegir las piezas juntas, como un solo look, mirando las fotos, y decir cuántas unidades: cero deja una pieza afuera. Solo puede elegir productos que trajo la búsqueda; si no, el código rechaza la respuesta. Acá eligió el segundo sofá de la búsqueda, porque el primero era blanco y el pedido decía gris claro, y puso dos almohadones. La v2 agregó las cantidades. Es el reranker con VLM del experimento 7.

## 14. El prompt de la imagen: una plantilla estricta, sin LLM
*El recorrido · fase 8 de 11 · Escena · ~0:54 min · desde el minuto 9:30*

Fase ocho, la escena: el prompt para el modelo de imagen. Probamos dos caminos. En uno, Opus escribe la escena: dónde va cada producto, anclado a lo que se ve. En el otro, una plantilla sin LLM: se completa con la lista y el modelo de imagen acomoda. La plantilla tuvo cuatro versiones: la libre, una que repetía los muebles modulares, otra con las cantidades, y la v4, estricta, que salió de un error: con nueve productos, el modelo inventó una ventana y movió la biblioteca. La v4 dice que es una edición de la foto del cliente: la misma cámara, las mismas paredes y ventanas, nada agregado, y exactamente estos productos. El experimento 12 eligió esta, que además no cuesta nada.

## 15. Nano Banana 2 edita la foto con las fotos de los productos
*El recorrido · fase 9 de 11 · Imagen · ~0:30 min · desde el minuto 10:24*

Fase nueve, la imagen. Nano Banana 2, por fal, en modo edición: recibe la foto del ambiente, las fotos de los productos en el orden de la lista y el prompt. Cuesta 8 centavos por imagen a 1K. El modelo no lo elegimos con un experimento: la comparación quedó diseñada, sin correr. Y el primer intento salió así: lindo, pero con la cámara corrida.

## 16. ¿Es el mismo cuarto? SIFT lo decide, y si no, reintenta
*El recorrido · fase 10 de 11 · Control · ~0:36 min · desde el minuto 10:54*

Fase diez, el control. Comparamos la foto original con la generada con SIFT y RANSAC: si reencuentra al menos 50 puntos del cuarto y la cámara se movió menos del 1 por ciento del ancho, se acepta. Si no, se guarda aparte y se genera otra, hasta 3 veces. En este living, los dos primeros intentos eran lindos pero con la cámara corrida: 18 y 11 puntos. El tercero reencontró 70 y quedó. Este control salió del experimento 12.

## 17. Sale la lista de compra y el ambiente amoblado
*El recorrido · fase 11 de 11 · Lista + imagen · ~0:36 min · desde el minuto 11:30*

Y fase once, lo que sale: la lista de compra, con productos reales del catálogo y cuántos de cada uno, y la foto del mismo ambiente con esos productos. Este pedido costó unos 17 centavos de Claude y 24 de imágenes, por los tres intentos. Cada fase deja su archivo en la carpeta de la corrida, y la webapp muestra cada paso mientras se hace. El comedor del mismo departamento pasó el control al primer intento.

## 18. Doce experimentos, cada uno con su pin donde decidió
*El recorrido · los experimentos · ~0:48 min · desde el minuto 12:06*

Y este es el mismo mapa con los experimentos encima: cada pin es un experimento, puesto sobre la parte que decidió, con todo lo demás fijo. El catálogo lo decidieron el 9 y el 10; qué se describe, el 1; el índice, cuatro: el embedder, el splitting, la dimensión y la base vectorial; la consulta del plan, el 6; el filtro y los candidatos de la búsqueda, el 3 y el 8; que la elección mire las fotos, el 7; y la escena y el control, el 12. El 11 mide cuánto vale el ground truth de la búsqueda. Ocho de las once fases las decidió un experimento. Antes de verlos, cómo medimos.

## 19. Cómo medimos
*Parte 2 · ~0:12 min · desde el minuto 12:54*

Antes de los experimentos, cómo medimos, para que cada número se entienda.

## 20. Ambientes IKEA anotados y ambientes vacíos reales
*Cómo medimos · los datos · ~0:54 min · desde el minuto 13:06*

Usamos dos bancos de prueba. Para el retrieval, 65 fotos de livings y comedores de IKEA con sus productos anotados: ahí sabemos cuál es el correcto. Por cada mueble visible, un subagente escribió la búsqueda como la escribiría el plan, sin ver el catálogo: 864 búsquedas, 549 con su producto en el catálogo. Acierta si el anotado sale primero, o entre los k primeros, y los intervalos son por bootstrap por ambiente. Para el sistema completo, 11 ambientes vacíos reales: 5 nuestros y 6 públicos, elegidos entre 22, cada uno con un pedido escrito como lo escribiría un usuario. Ahí no hay ground truth: un juez compara listas, y la imagen se mide aparte.

## 21. Con ground truth: ¿trae el producto correcto, y arriba?
*Métricas · retrieval · ~0:48 min · desde el minuto 14:00*

Las métricas de retrieval, donde sí hay ground truth. hit@k: si el anotado está entre los k primeros; hit@1 es encontrarlo primero, y hit@k con k igual a los candidatos que ve el VLM es el techo de lo que puede elegir. MRR: el promedio de uno sobre la posición del correcto, premia que esté arriba. Context recall y context precision son las de RAGAS: cuántos de los productos de un ambiente aparecen entre los candidatos, y cuán arriba quedan. NDCG admite relevancia graduada. Y los intervalos: si dos métodos tienen intervalos que se pisan, con estos datos no los podemos distinguir.

## 22. Sin un único correcto: jueces validados y comparaciones de a pares
*Métricas · la respuesta · ~0:48 min · desde el minuto 14:48*

Cuando no hay un único correcto usamos jueces, pero validados. Relevancia graduada: un LLM califica el top-3 con 2, 1 o 0, y antes chequeamos que le dé 2 al producto anotado. RAGAS sobre la explicación de cada elección: faithfulness, si lo que dice se sostiene con lo que vio, y answer relevance, si responde al pedido. Para comparar variantes sin ground truth, un juez de a pares en los dos órdenes, y reportamos cuánto coinciden los dos órdenes. Y el costo de cada llamada.

## 23. La imagen: mismo cuarto, mismos productos, lo que se pidió
*Métricas · la imagen y el resto · ~0:48 min · desde el minuto 15:36*

Para la imagen medimos tres cosas. Que sea el mismo cuarto: SIFT reencuentra puntos de la foto original y mide cuánto se movió la cámara, y SSIM compara lo que no es mueble. Que sean los mismos productos: detectamos cada mueble, lo recortamos y vemos si el más parecido del catálogo es el de la lista. Y que sea lo que se pidió: SigLIP 2 entre el pedido y la imagen, y contamos lo que falta, lo repetido y lo inventado. Además, reproducibilidad con tres redactores, y el espacio de embeddings.

## 24. Experimentos
*Parte 3 · ~0:12 min · desde el minuto 16:24*

Ahora los experimentos. Todos siguen el mismo orden: arriba, el minimapa con la fase que decide; después, por qué lo hicimos y cómo es el experimento; y recién ahí, con la flecha, los resultados y la decisión.

## 25. Qué texto se indexa
*Experimento 1 · ~1:00 min · desde el minuto 16:36*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): El texto que trae IKEA es una frase de marketing, y la gente pide estilo, color y materiales, que están en la foto. Queríamos saber si valía la pena describir cada producto, un costo que se paga una sola vez.
2. **El experimento:** Indexamos tres textos y corrimos las mismas 549 búsquedas, con todo lo demás fijo: el texto del vendedor, la descripción de ocho líneas, y la descripción con el nombre comercial adelante.
3. **→ Resultados** (flecha): Con el texto del vendedor, hit@1 da 0,13; con la descripción, 0,54: más de cuatro veces, el cambio más grande del trabajo. El nombre adelante empeora (de 0,53 a 0,42): NOLMYRA no le dice nada al embedding.
4. **→ Decisión** (flecha): Se indexa solo la descripción. Y queda una idea que vuelve en todo el trabajo: consulta y documento en el mismo formato.

## 26. Embedder
*Experimento 2 · ~0:54 min · desde el minuto 17:36*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): Con el texto resuelto, ¿cuánto aporta el modelo? Uno más grande cuesta memoria y tiempo, y queríamos que el retrieval corra local, en CPU.
2. **El experimento:** Tres embedders sobre el mismo texto y las mismas búsquedas: hashing, una bolsa de palabras sin modelo; BGE-base, de 110 millones de parámetros; y Qwen3-Embedding, de 600 millones.
3. **→ Resultados** (flecha): Gana Qwen3, con 0,54, pero el hashing queda cerca (0,51) y BGE último (0,48). Las descripciones usan vocabulario controlado, así que hasta contar palabras funciona. Qwen3 gana más claro en MRR y en las búsquedas difíciles.
4. **→ Decisión** (flecha): Qwen3-Embedding-0.6B, Apache 2.0, en CPU. El formato del texto vale más que el modelo.

## 27. Filtros duros
*Experimento 3 · ~1:00 min · desde el minuto 18:30*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): Por similitud sola, una mesa nórdica de madera clara se puede parecer más a la consulta que un sofá. Un filtro por metadata lo evita, pero puede dejar afuera al correcto.
2. **El experimento:** Tres opciones: sin filtro; por tipo, 14 categorías gruesas como sofá o mesa; y por kind, 41 finas como mesa ratona o de comedor. Miramos sobre todo hit@10.
3. **→ Resultados** (flecha): Con descripciones buenas, hit@1 casi no cambia, pero el de kind resta: en hit@10, 0,86 contra 0,89 del de tipo. Si el plan pide una mesa auxiliar y el catálogo la tiene como ratona, el filtro fino la deja afuera.
4. **→ Decisión** (flecha): Filtrar siempre, más las medidas. El flujo filtra por los kinds del plan, que puede dar dos; la diferencia con el tipo está dentro del intervalo, y pasarlo a tipo es lo próximo que probaríamos.

## 28. Splitting *
*Experimento 4 · ~0:30 min · desde el minuto 19:30*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): El splitting es una decisión clásica de un RAG. Nuestras ocho líneas tienen roles distintos: quizás convenía compararlas por separado.
2. **El experimento:** Un documento por producto; un chunk por línea, donde el producto vale su mejor línea; y línea contra línea, con el mismo rótulo de la consulta.
3. **→ Resultados** (flecha): Gana un documento (0,54); el chunk por línea se desploma (0,27): “Colors: light wood” se parece a cualquier cosa de madera clara.
4. **→ Decisión** (flecha): Un documento por producto: con unas 80 palabras no hay nada que partir.

## 29. Dimensión del embedding *
*Experimento 5 · ~0:30 min · desde el minuto 20:00*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): Qwen3 se entrenó con Matryoshka: el vector se puede truncar sin reentrenar. En un catálogo de millones, la memoria y la latencia crecen con la dimensión.
2. **El experimento:** Truncamos a 32, 64, 128, 256, 512 y 1024 componentes y renormalizamos.
3. **→ Resultados** (flecha): Con 512 da lo mismo que con 1024 (0,53 contra 0,54); por debajo de 128 cae rápido: con 32, 0,43.
4. **→ Decisión** (flecha): Con este catálogo dejamos 1024 porque no cuesta nada; si creciera, 512.

## 30. Base vectorial y query rewriting
*Experimento 6 · ~0:54 min · desde el minuto 20:30*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): Dos dudas. ChromaDB aproxima con HNSW: ¿pierde algo contra la búsqueda exacta? Y escribir la consulta completa cuesta tokens en cada pedido: ¿alcanza con algo más corto?
2. **El experimento:** ChromaDB contra recorrer todos los vectores con numpy, con la misma consulta. Y la consulta completa contra solo la línea Type, y contra solo el kind, que sería no reescribir.
3. **→ Resultados** (flecha): HNSW da exactamente lo mismo que la exacta (0,535 y 0,535). Con solo la línea Type, hit@1 cae a 0,29; con solo el kind, a 0,06. El estilo, los colores y la forma son lo que distingue un sofá de otro.
4. **→ Decisión** (flecha): ChromaDB con la consulta completa que escribe el plan: el query rewriting cuesta, pero vale.

## 31. Reranking (Advanced RAG)
*Experimento 7 · ~1:06 min · desde el minuto 21:24*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): hit@10 daba 0,89 pero hit@1 0,54: el correcto casi siempre está entre los 10 primeros, pero no primero. Advanced RAG propone un reranker, un segundo modelo que mira la consulta y cada candidato juntos.
2. **El experimento:** Dos rerankers sobre el top-10: un cross-encoder MiniLM de MS MARCO, local y gratis, que lee consulta y descripción; y Opus, que ve la consulta y las fotos de los 10 candidatos y los ordena.
3. **→ Resultados** (flecha): MiniLM empeora (0,42): está entrenado con preguntas web, no con muebles. Opus sube hit@1 de 0,54 a 0,69 y MRR de 0,65 a 0,76: la foto tiene lo que la descripción no dijo. Cuesta unos dos centavos por búsqueda.
4. **→ Decisión** (flecha): El reranking con VLM funciona, y la elección ya es eso. No agregamos un paso: la pregunta pasó a ser cuántos candidatos mostrarle.

## 32. Candidatos por pieza
*Experimento 8 · ~1:00 min · desde el minuto 22:30*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): La elección es un reranker con fotos, pero con 3 candidatos el correcto faltaba en una de cada cuatro piezas. Más candidatos suben ese techo, pero son más fotos en la llamada: más caro y más difícil elegir.
2. **El experimento:** Sale gratis del experimento anterior: si Opus ordenó el top-10, lo que elegiría entre los primeros k es el mejor ordenado de esos k. Es un proxy: la elección real además ve el ambiente y el pedido.
3. **→ Resultados** (flecha): La punteada es el techo; la sólida, lo que elegiría el VLM. De 3 a 5 candidatos sube de 0,637 a 0,667; a partir de 8 se aplana, y la distancia al techo crece.
4. **→ Decisión** (flecha): 5 candidatos por pieza: casi toda la mejora, y la llamada queda en 45 fotos para 9 piezas.

## 33. Catálogo: ampliación y revisión
*Experimento 9 · ~0:54 min · desde el minuto 23:30*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): El primer catálogo eran 268 sofás, sillones, mesas y alfombras: no había biblioteca, lámpara ni cortinas. Y al describirlo aparecieron productos con la foto de otro: la lista diría una cosa y la imagen mostraría otra.
2. **El experimento:** Las mismas métricas sobre el de 268, el ampliado a 855 y el revisado: 36 productos afuera y 7 kinds corregidos.
3. **→ Resultados** (flecha): Ampliar baja hit@1 de 0,636 a 0,533: hay más productos parecidos y lo nuevo es deco, más difícil. La revisión casi no lo cambia (0,535), pero hace que la lista y la imagen muestren el mismo producto. Ojo: cambia el universo, no son números comparables.
4. **→ Decisión** (flecha): Ampliado y revisado: unos puntos de hit@1 son el precio de poder amoblar un living completo.

## 34. Qué catálogo
*Experimento 10 · ~1:30 min · desde el minuto 24:24*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): IKEA es de 2013, con fotos chicas, asientos sin medidas y una sola estética, la nórdica. Amazon Berkeley Objects tiene listados reales, con medidas y fotos grandes.
2. **El experimento:** Sin ground truth: de punta a punta, con los mismos ambientes, pedidos y plan; cambia solo el catálogo. El juez de a pares compara las dos listas, en los dos órdenes.
3. **→ Resultados** (flecha): Primero, en nuestros 5 departamentos: IKEA le gana a Amazon 4 a 0, por estilo, e IKEA más Amazon empataba con IKEA. Pero los 5 pedidos eran nórdicos, así que sumamos 6 ambientes públicos con otros estilos. En los nórdicos siguen empatados; en los otros, IKEA más Amazon gana 6 a 0, y los productos útiles pasan de 0,46 a 0,71. Los dos órdenes del juez coinciden en el 91% de los ambientes. 
4. **→ Decisión** (flecha): Usamos los dos catálogos. Con ambientes y pedidos poco variados habríamos decidido lo contrario.

## 35. ¿Cuánto mide el ground truth?
*Experimento 11 · ~1:00 min · desde el minuto 25:54*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): El ground truth tiene un solo producto correcto por pieza, pero uno casi igual también sirve. Y las búsquedas las escribieron subagentes: con otros, ¿cambiaría el número?
2. **El experimento:** Un juez califica el top-3 de 150 búsquedas con 2, 1 o 0, y antes lo validamos contra el ground truth. Y tres redactores independientes escribieron las mismas búsquedas.
3. **→ Resultados** (flecha): El juez le da 2 al anotado el 81% de las veces y a los demás el 5%: es confiable. Con él, el primero sirve en el 75% de los casos, aunque hit@1 sea 0,53: el ground truth subestima. Con tres redactores, hit@1 varía unos 2,6 puntos: diferencias más chicas entre métodos no son señal.
4. **→ Decisión** (flecha): hit@1 para comparar métodos, porque es objetivo y barato; la relevancia graduada para saber cuán útil es de verdad.

## 36. La imagen: del cuarto reimaginado al cuarto del cliente
*Experimento 12 · ~1:12 min · desde el minuto 26:54*

1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): En las primeras imágenes el modelo redecoraba: acá inventó una ventana y movió la biblioteca. El usuario quiere ver su cuarto con esos productos.
2. **El experimento:** El mismo ambiente, cuatro versiones de la escena. Arriba, con el pedido corto de 6 piezas: la escena escrita por Opus y la plantilla libre. Abajo, con el pedido completo de 9 piezas: libre, y la edición estricta. Medimos con SIFT los puntos de la foto original que se reencuentran, y SSIM fuera de los muebles.
3. **→ Resultados** (flecha): Arriba, las dos conservan el cuarto pero la biblioteca queda chica. Abajo a la izquierda, linda pero con una ventana inventada: SIFT reencuentra solo 10 puntos. La estricta conserva el cuarto, con 116, y la biblioteca es la que se pidió.
4. **→ Decisión** (flecha): Edición estricta y el control automático con reintento, que ya vimos funcionando en la fase 10.

## 37. La iteración: qué falló, qué cambiamos y cuánto mejoró
*Ejercicio 4 · ~0:30 min · desde el minuto 28:06*

Esto es el ejercicio 4 en una tabla: cada fila es un problema que encontramos usando el sistema, el cambio que hicimos y cuánto mejoró. Todos salen de lo que acabamos de ver.

## 38. El camino: de 0,08 a 0,69 de hit@1
*Resumen de los experimentos · ~0:30 min · desde el minuto 28:36*

El resumen en un gráfico: cada barra suma un cambio a la anterior. Del texto del vendedor con una bolsa de palabras (0,08) al VLM reordenando el top-10 (0,69). Lo que más movió el número fue qué texto se indexa; lo segundo, que un VLM mire las fotos.

## 39. Cuánto cuesta un pedido *
*Costo · ~0:24 min · desde el minuto 29:06*

Un pedido cuesta unos 20 centavos de dólar de Claude y 8 por intento de imagen. Describir el catálogo es un costo único, de menos de un centavo por producto, y embeddings y base vectorial corren locales. Todo gasto queda registrado, con topes por cuenta, y lo que ya se pagó queda en caché.

## 40. Limitaciones y trabajo futuro
*Cierre · ~0:42 min · desde el minuto 29:30*

Limitaciones: los catálogos son viejos y de uso no comercial; las medidas del ambiente se estiman a ojo; el ground truth es uno solo, con consultas escritas por modelos; la imagen es una visualización; y tenemos pocos ambientes vacíos. Como trabajo futuro: medidas reales, con un metro en la foto o un modelo de profundidad; el catálogo de un vendedor actual, con precio y stock; más ambientes y evaluación humana; y que el usuario pueda cambiar una pieza y regenerar solo eso.

## 41. Conclusiones
*Cierre · ~0:48 min · desde el minuto 30:12*

Para cerrar, cinco cosas. Lo que más importó fue el texto que se indexa, no el modelo. El mejor reranker es un VLM mirando las fotos, y nuestro paso de elegir ya lo es. Las métricas con ground truth subestiman, así que hace falta un juez, validado y preguntado en los dos órdenes. El catálogo decide qué se puede recomendar, y evaluar con ambientes variados cambió la decisión. Y la imagen necesita un control automático para que el cuarto sea el del cliente. Gracias.

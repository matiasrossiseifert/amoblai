# Guion de la presentación (amoblai, versión b2)

Generado por `build.py` junto con `presentacion.html`: los números salen de los mismos archivos de resultados que las láminas. 48 láminas, unos 31 minutos (30:40).

**Cómo se pasa.** Flecha derecha, espacio o clic: avanza un paso; flecha izquierda: vuelve. F: pantalla completa; O: índice con miniaturas; N: estas notas abajo de la lámina; P: ventana del presentador (lámina actual, la siguiente, notas y reloj, sincronizadas); B: pantalla negra. `presentacion.html?all#/12` muestra la lámina 12 con todos sus pasos; `#/12.2` va al paso 2.

**Los experimentos** tienen dos láminas. La oscura es la pregunta: se ve el porqué y el esquema del flujo con la etapa que se prueba encendida; con la flecha aparece el experimento (las variantes). **Se cuentan esas dos cosas antes de pasar.** La clara es el resultado: arranca con las variantes y las barras vacías; una flecha muestra los resultados y otra la decisión, que se imprime como un talón abajo (la línea de configuración que deja el experimento). Los experimentos 4 y 5 van en una sola lámina.

En el texto, **→** marca dónde se avanza un paso.

**Reparto sugerido** (a definir entre los tres):
- Parte 1: láminas 1 a 17 (Portada → Exp. 2: Embedder), unos 10:20.
- Parte 2: láminas 18 a 33 (Exp. 2: resultados → Exp. 10: resultados (2 de 2)), unos 10:15.
- Parte 3: láminas 34 a 48 (Exp. 11: Cuánto mide el ground truth → Gracias), unos 10:05.

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
*El producto · ~0:45 · desde el minuto 1:30*

¿Por qué un RAG y no un LLM o un modelo de imagen solos? Un LLM sabe de decoración, pero no sabe qué hay en un catálogo: te recomienda un sillón de cuero coñac que nadie vende. Un modelo de imagen amobla lindo, pero inventa los muebles: no hay nada que comprar. **→** Con RAG, el catálogo es la base de conocimiento: el LLM decide qué hace falta, el retrieval trae candidatos reales y el VLM elige mirando sus fotos. Y la imagen se genera desde las fotos de los productos elegidos. No es un Q&A: la consulta es una foto y un pedido abierto, y la respuesta es una combinación de productos que tiene que funcionar junta.

## 5. El catálogo
*Datos · ~0:35 · desde el minuto 2:15*

El catálogo base es el dataset IKEA de Tautkute y otros, de uso no comercial. Nos quedamos con lo de living y comedor: muebles, iluminación, textiles y deco, 855 productos, 819 después de la revisión. El texto de IKEA es pobre, así que un VLM describe cada producto mirando su foto en 8 líneas fijas (esta es una). Eso es lo que se indexa, y el experimento 1 muestra por qué. **→** Los problemas del catálogo: fotos de 500 píxeles, asientos sin medidas (144 de 152) y productos que comparten la foto de otra medida.

## 6. Ground truth
*Datos · ~0:35 · desde el minuto 2:50*

Para medir el retrieval necesitamos saber cuál es el producto correcto. El dataset trae 65 fotos de livings y comedores reales de IKEA con sus productos anotados. Por cada mueble visible, un subagente escribe la búsqueda como la escribiría nuestro plan, mirando el ambiente. **→** Una búsqueda acierta si el anotado sale primero (hit@1) o entre los k primeros. **→** En total, 864 búsquedas, 549 con su producto en el catálogo. Los intervalos de confianza son por bootstrap por ambiente, porque las búsquedas de un mismo ambiente no son independientes.

## 7. Ambientes vacíos
*Datos · ~0:30 · desde el minuto 3:25*

Para probar el sistema completo hacen falta ambientes vacíos reales. Tenemos 11: 5 de departamentos nuestros y 6 públicos de Wikimedia Commons y Flickr, con licencia Creative Commons, elegidos entre 22 que revisamos uno por uno para descartar renders y fotos generadas con IA. Cada uno tiene un pedido escrito como lo escribiría un usuario que sabe pedir; los públicos, con estilos distintos del nórdico. Acá no hay ground truth: medimos con un juez y con métricas de imagen.

## 8. v0 → v1
*Arquitectura · ~0:45 · desde el minuto 3:55*

La primera versión buscaba por imagen: detectaba cada mueble en la foto con Grounding DINO, lo recortaba con SAM y buscaba la foto del catálogo más parecida con DINOv3. Eso sirve para encontrar este sofá, pero nuestro caso es un ambiente vacío: no hay nada que recortar. La v1 busca por texto: un LLM escribe el producto ideal en el mismo formato que el catálogo. **→** Con el mismo ground truth, la v1 da 0,62 de hit@1 contra 0,51 de la v0, y además funciona con el ambiente vacío.

## 9. El flujo
*Arquitectura · ~1:00 · desde el minuto 4:40*

La arquitectura tiene dos pipelines. **→** El de indexing corre una vez: el catálogo, las descripciones que escribe un VLM, los embeddings con Qwen3 y ChromaDB. **→** El de consulta corre por pedido. Plan: Claude Opus lee la foto y el pedido, decide las piezas, su tipo, la medida máxima y escribe la consulta ideal. **→** Búsqueda: Qwen3 y ChromaDB con filtros duros, 5 candidatos por pieza. **→** Elección: Claude mira las fotos de los candidatos, elige uno por pieza pensando la combinación, y cuántas unidades. **→** Escena e imagen: Nano Banana 2 recibe la foto del ambiente y las de los productos, y un control automático descarta la imagen si cambió el cuarto. **→** Y lo importante: la elección solo puede tomar productos recuperados, así que la respuesta queda atada al catálogo.

## 10. Los hiperparámetros
*Arquitectura · ~0:30 · desde el minuto 5:40*

Cada una de estas filas es una decisión de la arquitectura que tomamos con un experimento, con todo lo demás fijo, y el número marca en qué etapa del flujo está. Todavía no decimos qué ganó: eso lo vemos en cada experimento. Van en este orden, que es más o menos el orden en que los hicimos: cada uno deja su decisión en la configuración del siguiente.

## 11. Métricas de retrieval
*Métricas · ~0:50 · desde el minuto 6:10*

Las métricas de retrieval, donde sí hay ground truth. Arriba, una búsqueda real: el anotado sale segundo. hit@k: si el anotado está entre los k primeros; acá hit@1 da 0 y hit@3 da 1. MRR: el promedio de uno sobre la posición del correcto, premia que esté arriba; esta búsqueda suma un medio. **→** hit@1 es encontrarlo primero, y hit@k con k igual a los candidatos que ve el VLM es el techo de lo que puede elegir. Context recall y context precision son las de RAGAS: cuántos de los productos de un ambiente aparecen entre los candidatos, y cuán arriba quedan. NDCG admite relevancia graduada. Y los intervalos de confianza: si dos métodos tienen intervalos que se pisan, con estos datos no los podemos distinguir.

## 12. Jueces y pares
*Métricas · ~0:35 · desde el minuto 7:00*

Cuando no hay un único correcto usamos jueces, pero validados. Relevancia graduada: un LLM califica el top-3 con 2, 1 o 0, y antes chequeamos que le dé 2 al producto anotado. RAGAS sobre la explicación de cada elección: faithfulness, si lo que dice se sostiene con lo que vio, y answer relevance, si responde al pedido. Para comparar variantes sin ground truth, un juez de a pares en los dos órdenes, y reportamos cuánto coinciden los dos órdenes. Y el costo de cada llamada.

## 13. Métricas de imagen
*Métricas · ~0:35 · desde el minuto 7:35*

Para la imagen medimos tres cosas. Que sea el mismo cuarto: SIFT reencuentra puntos de la foto original y mide cuánto se movió la cámara, y SSIM compara lo que no es mueble. Que sean los mismos productos: detectamos cada mueble, lo recortamos y vemos si el más parecido del catálogo es el de la lista. Y que sea lo que se pidió: SigLIP 2 entre el pedido y la imagen, y contamos lo que falta, lo repetido y lo inventado. Además, reproducibilidad, con tres redactores, y el espacio de embeddings.

## 14. Cómo leemos cada experimento
*Experimentos · ~0:20 · desde el minuto 8:10*

Ahora los experimentos. Todos siguen el mismo orden: primero por qué lo hicimos y qué queríamos ver, con el flujo marcando la etapa que se toca; después cómo es el experimento; y recién ahí mostramos los resultados y, al final, la decisión, que queda en la configuración del siguiente.

## 15. Exp. 1: Qué texto se indexa
*Experimentos · 1 · ~0:50 · desde el minuto 8:30*

Lo primero que miramos fue qué texto trae el catálogo. IKEA tiene nombre, tipo, colores y una frase de marketing del estilo «The armchair is lightweight and easy to move». Pero nadie pide así: se pide un sillón nórdico, de madera clara, con tapizado crema, y todo eso está en la foto. La pregunta era si alcanzaba con el texto del vendedor o si valía la pena describir cada producto mirando su foto, un costo que se paga una sola vez. **→** Indexamos tres textos y corrimos las mismas 549 búsquedas del ground truth, con todo lo demás fijo (Qwen3, filtro): el texto del vendedor; la descripción de 8 líneas que escribe un VLM mirando la foto, en el mismo formato en que el plan escribe la consulta; y esa descripción con el nombre comercial adelante.

## 16. Exp. 1: resultados
*Experimentos · 1 · ~0:30 · desde el minuto 9:20*

Con el texto del vendedor, hit@1 da 0,13; con la descripción del VLM, 0,54: más de 4 veces. Es el cambio más grande de todo el trabajo. El nombre comercial adelante empeora: con el mismo filtro, de 0,53 a 0,42. NOLMYRA no le dice nada al embedding. **→** Decisión: indexamos solo la descripción del VLM. Y queda una idea que vuelve en todo el trabajo: la consulta y el documento escritos en el mismo formato.

## 17. Exp. 2: Embedder
*Experimentos · 2 · ~0:30 · desde el minuto 9:50*

Con el texto resuelto, la pregunta natural es cuánto aporta el modelo de embeddings. Un modelo más grande cuesta memoria y tiempo, y nos pusimos la restricción de que el retrieval corra local, en CPU, sin pagar una API. Queríamos ver cuánto gana un modelo entrenado contra una línea de base sin modelo. **→** Tres embedders sobre el mismo texto y las mismas búsquedas: hashing, una bolsa de palabras hasheada, sin ningún modelo; BGE-base, de 110 millones de parámetros; y Qwen3-Embedding, de 600 millones.

## 18. Exp. 2: resultados
*Experimentos · 2 · ~0:25 · desde el minuto 10:20*

Gana Qwen3, con 0,54. Pero el hashing queda cerca (0,51) y BGE último (0,48). La explicación: las descripciones usan vocabulario controlado, los estilos y los kinds salen de listas cerradas, así que hasta contar palabras funciona bastante. Qwen3 gana más claro en MRR (0,65 contra 0,63). **→** Decisión: Qwen3-Embedding-0.6B, Apache 2.0, corre en CPU. La lección: el formato del texto vale más que el modelo.

## 19. Exp. 3: Filtros duros
*Experimentos · 3 · ~0:45 · desde el minuto 10:45*

El plan sabe qué pieza está buscando: un sofá, una lámpara. Por similitud sola, una mesa nórdica de madera clara se puede parecer más a la consulta que un sofá. Un filtro por metadata lo evita y es gratis, pero tiene un riesgo: si el plan y el catálogo no coinciden en la categoría, el producto correcto queda afuera. Queríamos ver si conviene filtrar, y con qué granularidad. **→** Tres opciones: sin filtro; filtro por tipo, 14 categorías gruesas como sofá, mesa o lámpara; y filtro por kind, 41 categorías finas como mesa ratona o mesa de comedor. En ChromaDB el filtro va como where. Miramos hit@1 y sobre todo hit@10.

## 20. Exp. 3: resultados
*Experimentos · 3 · ~0:45 · desde el minuto 11:30*

Con descripciones buenas, hit@1 casi no cambia. Pero el filtro por kind resta: en hit@10 da 0,86 contra 0,89 del filtro por tipo. Si el plan pide una mesa auxiliar y el catálogo la tiene como mesa ratona, el filtro fino la deja afuera. El de tipo protege de los errores gruesos sin ese costo. **→** Decisión: filtrar siempre, más las medidas máximas que estima el plan. El flujo filtra por los kinds que elige el plan, que puede dar más de uno para no dejar afuera al correcto; contra el filtro por tipo la diferencia en hit@1 está dentro del intervalo, y pasarlo a tipo es lo próximo que probaríamos.

## 21. Exp. 4: Splitting
*Experimentos · 4 · ~1:00 · desde el minuto 12:15*

En la materia vimos que el chunking es una de las decisiones centrales de un RAG. Nuestros documentos son cortos, de 70 a 100 palabras, pero tienen 8 líneas con roles distintos: tipo, estilo, colores, materiales. La hipótesis era que comparar línea por línea, colores contra colores, podía ser más preciso que un solo vector por producto. **→** Tres formas: un documento por producto, con las 8 líneas juntas; un chunk por línea, donde el producto vale lo que su línea más parecida a la consulta; y línea contra línea, cada una contra la del mismo rótulo en la consulta, promediado. **→** Gana un documento por producto (0,54). Línea contra línea queda cerca (0,51) y el chunk por línea se desploma (0,27): una línea suelta como «Colors: light wood» se parece a cualquier cosa de madera clara. Partir pierde el contexto. **→** Decisión: un documento por producto. Con documentos tan cortos no hay nada que partir.

## 22. Exp. 5: Dimensión del embedding
*Experimentos · 5 · ~0:40 · desde el minuto 13:15*

Qwen3 se entrenó con Matryoshka: las primeras componentes del vector concentran la información, así que se puede truncar sin reentrenar. Con 819 productos no importa, pero en un catálogo de millones la memoria y la latencia crecen con la dimensión. Queríamos saber cuánto se puede achicar sin perder. **→** Truncamos los vectores a 32, 64, 128, 256, 512 y 1024 componentes, los renormalizamos y corrimos las mismas búsquedas. **→** Con 512 da prácticamente lo mismo que con 1024 (0,53 contra 0,54), con la mitad de memoria. Por debajo de 128 cae rápido: con 32, 0,43. **→** Decisión: para este catálogo dejamos 1024 porque no cuesta nada; si creciera, indexaríamos con 512.

## 23. Exp. 6: Base vectorial y consulta
*Experimentos · 6 · ~0:35 · desde el minuto 13:55*

Dos dudas. Primero, pasamos de una búsqueda exacta con numpy a ChromaDB, que usa HNSW, un índice aproximado: había que verificar que no perdiera resultados. Segundo, el query rewriting: el plan escribe para cada pieza el producto ideal en 8 líneas, y eso cuesta tokens y latencia en cada pedido. Queríamos ver si una consulta más corta alcanzaba. **→** ChromaDB contra la búsqueda exacta, con la misma consulta. Y la consulta completa contra solo la línea Type, y contra solo el nombre del kind, que sería no reescribir.

## 24. Exp. 6: resultados
*Experimentos · 6 · ~0:25 · desde el minuto 14:30*

HNSW da exactamente lo mismo que la búsqueda exacta (0,535 y 0,535). Con solo la línea Type, hit@1 cae a 0,29; con solo el kind, a 0,06. El estilo, los colores y la forma son lo que distingue un sofá de otro. **→** Decisión: ChromaDB con la consulta completa que escribe el plan. El query rewriting cuesta, pero vale la pena.

## 25. Exp. 7: Reranking
*Experimentos · 7 · ~0:40 · desde el minuto 14:55*

Mirando los resultados vimos que hit@10 era 0,89 pero hit@1 0,54: el producto correcto casi siempre está entre los 10 primeros, pero no primero. El cuello de botella era el orden. Advanced RAG propone un reranker, un segundo modelo que mira la consulta y cada candidato juntos. Queríamos ver si eso ordena mejor, y con qué tipo de modelo. **→** Dos rerankers sobre el top-10: un cross-encoder MiniLM entrenado en MS MARCO, local y gratis, que lee la consulta y la descripción juntas; y Claude Opus como VLM, que ve la consulta y las fotos de los 10 candidatos y los ordena.

## 26. Exp. 7: resultados
*Experimentos · 7 · ~0:35 · desde el minuto 15:35*

MiniLM empeora (0,42): está entrenado con preguntas y pasajes web, no con descripciones de muebles. El VLM sube hit@1 de 0,54 a 0,69 y MRR de 0,65 a 0,76: mira la foto, que tiene lo que la descripción no dijo. Cuesta unos dos centavos de dólar por búsqueda. **→** Decisión: el reranking con VLM funciona, y nuestro paso de elección ya es eso: Claude elige mirando las fotos de los candidatos. No agregamos un paso: la pregunta pasó a ser cuántos candidatos mostrarle, que es el experimento siguiente.

## 27. Exp. 8: Candidatos por pieza
*Experimentos · 8 · ~0:45 · desde el minuto 16:10*

La elección ya es un reranker que mira fotos, pero le pasábamos 3 candidatos por pieza, y con 3 el correcto faltaba en una de cada cuatro piezas. Más candidatos suben ese techo, pero son más fotos en la llamada: más caro, y más difícil elegir entre muchos parecidos. Queríamos encontrar el k que maximiza la chance de que el VLM elija bien. **→** Lo sacamos gratis del experimento anterior: si el VLM ordenó el top-10, lo que elegiría entre los primeros k es el mejor ordenado de esos k. Así sale la curva para k de 1 a 10 sin pagar nada más. Es un proxy: la elección real además ve el ambiente y el pedido.

## 28. Exp. 8: resultados
*Experimentos · 8 · ~0:30 · desde el minuto 16:55*

La línea punteada es el techo: que el correcto esté entre los k. La sólida es lo que elegiría el VLM. De 3 a 5 candidatos, la elección sube de 0,637 a 0,667; a partir de 8 se aplana. Y la distancia al techo crece: entre muchos parecidos, el VLM no siempre reconoce al correcto. **→** Decisión: 5 candidatos por pieza: casi toda la mejora, y la llamada queda en 45 fotos para 9 piezas.

## 29. Exp. 9: Ampliación y revisión
*Experimentos · 9 · ~0:40 · desde el minuto 17:25*

El primer alcance eran sofás, sillones, mesas y alfombras: 268 productos. Con pedidos reales, la gente pide una biblioteca, una lámpara de pie, cortinas, y no había nada. Así que ampliamos. Y mientras los subagentes describían los productos, marcaron varios con la foto de otro producto o mal clasificados: la lista diría una cosa y la imagen mostraría otra. Queríamos saber cuánto cuesta ampliar en retrieval y qué cambia la limpieza. **→** Las mismas métricas sobre tres catálogos: el de 268, el ampliado a 855 (guardado, iluminación, textiles y deco) y el revisado, con 36 productos afuera y 7 kinds corregidos.

## 30. Exp. 9: resultados
*Experimentos · 9 · ~0:30 · desde el minuto 18:05*

Ampliar baja hit@1 de 0,636 a 0,533: hay más productos parecidos y las búsquedas nuevas son de deco, que es más difícil. La revisión casi no lo cambia (0,533 a 0,535), pero hace que el producto de la lista sea el de la foto. Ojo: no son números directamente comparables, porque cambia el universo. **→** Decisión: catálogo ampliado y revisado. Perder unos puntos de hit@1 es el precio de poder amoblar un living completo.

## 31. Exp. 10: Qué catálogo
*Experimentos · 10 · ~0:55 · desde el minuto 18:35*

El catálogo de IKEA tiene límites: es de 2013, las fotos son de 500 píxeles, los asientos no tienen medidas y tiene una sola estética, la nórdica. Encontramos Amazon Berkeley Objects, un dataset académico con listados reales de Amazon, con medidas y fotos grandes. Queríamos ver si con otro catálogo, o con los dos juntos, salen mejores listas para ambientes reales. **→** Acá no hay ground truth: nadie anotó qué sofá de Amazon va en un living vacío. Comparamos de punta a punta: mismos ambientes, mismos pedidos y el mismo plan; cambia solo el catálogo. Un juez, Claude Opus, ve la foto, el pedido y las dos listas sin saber de qué catálogo es cada una, y elige. Se le pregunta en los dos órdenes, y una variante gana un ambiente solo si gana en los dos. Primero, en nuestros 5 departamentos.

## 32. Exp. 10: resultados (1 de 2)
*Experimentos · 10 · ~0:25 · desde el minuto 19:30*

IKEA le gana a Amazon 4 a 0; según el juez, Amazon pierde por estilo (maderas oscuras, patas doradas para pedidos nórdicos). Y IKEA + Amazon empataba con IKEA, 2 a 2. **→** Con esto solo, la decisión habría sido quedarse con IKEA. Pero miramos los pedidos.

## 33. Exp. 10: resultados (2 de 2)
*Experimentos · 10 · ~0:40 · desde el minuto 19:55*

Los 5 pedidos eran nórdicos, justo la estética de IKEA, así que sumamos 6 ambientes públicos reales con pedidos de otros estilos: industrial, clásico, bohemio. **→** En los nórdicos siguen empatados, 2 a 2; en los otros estilos, IKEA + Amazon gana 6 a 0, y los productos útiles pasan de 0,46 a 0,71. Los dos órdenes del juez coinciden en el 91% de los ambientes. Y sumar Amazon casi no cambia el retrieval sobre el ground truth de IKEA: hit@1 de 0,535 a 0,525. **→** Decisión: usamos los dos catálogos. Y la lección: con ambientes y pedidos poco variados habríamos tomado la decisión contraria.

## 34. Exp. 11: Cuánto mide el ground truth
*Experimentos · 11 · ~0:40 · desde el minuto 20:35*

Todos los números hasta acá son contra un ground truth con un solo producto correcto por pieza. Pero si el sistema trae un sillón casi igual al anotado, ¿se equivocó? Y las búsquedas de evaluación las escribieron subagentes: si las escribiera otro, ¿cambiaría el número? Queríamos saber cuánto mide realmente el ground truth. **→** Dos cosas. Un juez califica el top-3 de 150 búsquedas: 2 si es el mismo o indistinguible, 1 si es una alternativa aceptable, 0 si no sirve; antes de creerle, lo validamos contra el ground truth. Y tres redactores independientes escribieron las mismas búsquedas.

## 35. Exp. 11: resultados
*Experimentos · 11 · ~0:35 · desde el minuto 21:15*

El juez le da 2 al producto anotado el 81% de las veces y a los demás el 5%: es confiable. Con él, el primer candidato sirve en el 75% de los casos, aunque hit@1 en esas mismas búsquedas sea 0,53: el ground truth subestima. Con tres redactores, hit@1 varía unos 2,6 puntos: diferencias más chicas que eso entre métodos no son señal. **→** Decisión: reportamos hit@1 para comparar métodos, porque es objetivo y barato, y la relevancia graduada para saber cuán útil es de verdad.

## 36. Exp. 12: La imagen
*Experimentos · 12 · ~0:50 · desde el minuto 21:50*

Cuando empezamos a generar imágenes vimos que el modelo no solo agregaba los muebles: redecoraba. En este ejemplo inventó una ventana y movió la biblioteca. Para el usuario eso no sirve: quiere ver su cuarto con esos productos. Queríamos encontrar cómo pedirle al modelo que respete el ambiente, y cómo detectar automáticamente cuando no lo hace. **→** El mismo ambiente, cuatro versiones del paso de la imagen: una escena que escribe el LLM diciendo dónde va cada cosa; una escena libre; libre y sin tope de piezas; y una edición estricta, que exige el mismo encuadre, las mismas paredes y aberturas y solo los productos de las fotos. Medimos con SIFT cuántos puntos de la foto original se reencuentran, y SSIM fuera de los muebles.

## 37. Exp. 12: resultados
*Experimentos · 12 · ~0:30 · desde el minuto 22:40*

Las dos primeras conservan el cuarto (203 y 154 puntos) pero la biblioteca queda chica. La tercera, libre y sin tope: linda, pero inventó una ventana; SIFT lo detecta, reencuentra solo 10 puntos. La edición estricta conserva el cuarto, con 116 puntos, y la biblioteca es la que se pidió. **→** Decisión: edición estricta y un control automático: si SIFT no reencuentra el cuarto, la imagen se descarta y se reintenta, hasta 3 veces. En el cierre se ve funcionando.

## 38. Exp. 13: Réplica de un living real
*Experimentos · 13 · ~0:50 · desde el minuto 23:10*

En los ambientes vacíos no tenemos con qué comparar la imagen: nadie sabe cómo debería quedar. Pero un living del ground truth sí lo tiene: la foto real, y la lista de sus productos. Queríamos medir el generador solo, con la lista ya decidida, sin el retrieval en el medio. **→** Vaciamos la foto real con el mismo modelo de imagen: el primer intento abrió el encuadre y dejó una lámpara; el segundo conserva la puerta, las cortinas y el piso. La volvimos a amoblar con sus 6 muebles anotados, con el paso de imagen del flujo, 3 veces. Y comparamos con la real: dónde quedó cada mueble, como IoU entre su caja y la real, y si es el producto, con el coseno de DINOv3. Es una sola habitación: una prueba, no una medición.

## 39. Exp. 13: resultados
*Experimentos · 13 · ~0:35 · desde el minuto 24:00*

Los 6 productos aparecen en todas, y se reconocen: coseno 0,63. Pero cada vez arma su propio living: el sofá a la izquierda, la estantería a la derecha. El IoU medio con las cajas reales es 0,20: en promedio, 1,0 de 6 muebles quedan en su lugar. **→** La conclusión: el generador respeta los productos, no la distribución. Y no es un error: el pedido no dice dónde va cada cosa. Si queremos controlar dónde, hay que decírselo. Eso es lo que dejamos como paso a futuro, al final.

## 40. De punta a punta
*Cierre · ~0:40 · desde el minuto 24:35*

Y así queda todo junto, con la configuración final, en un departamento real. **→** En el living, el primer intento de la imagen salió lindo pero con la cámara corrida: SIFT reencontró 18 puntos, y el control lo descartó solo. **→** El segundo, lo mismo: 11 puntos, descartado. **→** El tercero quedó, con 70 puntos. **→** El comedor pasó al primer intento.

## 41. La iteración
*Cierre · ~0:40 · desde el minuto 25:15*

Esto es el ejercicio 4 en un ticket: cada línea es un problema que encontramos usando el sistema, el cambio que hicimos y cuánto mejoró. Todos salen de los experimentos que acabamos de ver.

## 42. El camino
*Cierre · ~0:35 · desde el minuto 25:55*

El resumen en un gráfico: cada barra suma un cambio a la anterior. Arrancamos con el texto del vendedor y una bolsa de palabras: 0,08. **→** La descripción del VLM: 0,50. **→** Qwen3: 0,54. **→** El filtro por tipo no mueve hit@1: lo que protege es hit@10. **→** Y el VLM reordenando el top-10: 0,69. Lo que más movió el número fue qué texto se indexa; lo segundo, que un VLM mire las fotos.

## 43. Cuánto cuesta
*Cierre · ~0:25 · desde el minuto 26:30*

Un pedido cuesta unos 21 centavos de dólar de Claude y 8 por intento de imagen. Describir el catálogo es un costo único, de menos de un centavo por producto. Embeddings y base vectorial corren locales. Todo gasto queda registrado, con topes por cuenta, y las respuestas de los jueces quedan en caché: repetir un experimento no se vuelve a pagar.

## 44. Limitaciones
*Cierre · ~0:35 · desde el minuto 26:55*

Limitaciones: los catálogos son viejos y de uso no comercial; las medidas del ambiente se estiman a ojo; el ground truth es uno solo y con consultas escritas por modelos; la imagen es una visualización, con escala y luz aproximadas; y tenemos pocos ambientes vacíos. **→** A futuro: el catálogo de un vendedor actual, con precio y stock; más ambientes y evaluación humana; y que el usuario pueda cambiar una pieza y regenerar solo eso. Y lo más importante, las medidas reales, que es lo que mostramos ahora.

## 45. Futuro: cajas en la foto
*Pasos a futuro · ~1:20 · desde el minuto 27:30*

La réplica mostró que el generador pone los productos pero decide él dónde. La idea: dibujar en la foto vacía una caja por mueble, donde tiene que ir y cuánto ocupa, y pedirle que cada mueble llene su caja. Lo probamos en la misma habitación con los mismos 6 muebles, con las cajas donde está cada mueble en la foto real: primero un rectángulo plano, y después un prisma en perspectiva, apoyado en el piso, que además dice para dónde mira y cuánto ocupa hacia el fondo. **→** Con cajas 2D, el IoU medio sube de 0,20 a 0,40, y los muebles en su lugar de 1,0 a 2,7. Por mueble se ve dónde funciona: la estantería, el sofá y la alfombra van a su caja; el puf, la mesa ratona y la lámpara, que se superponen con otros, no. Y un problema: en 2 de las 3 imágenes el modelo dejó las cajas dibujadas. Con cajas 3D, el IoU medio da 0,48 y quedan 3,3 de 6 muebles en su lugar. **→** Lo que vimos: las cajas sirven para los muebles grandes, pero hay que pasarlas de otra forma, como una máscara aparte o borrándolas en un segundo paso. Son tres imágenes por variante: una pista, no un resultado.

## 46. Futuro: medidas reales
*Pasos a futuro · ~1:00 · desde el minuto 28:50*

Y cómo se vería en el producto, sobre el mismo flujo. **→** Uno: medir el ambiente, con una app móvil que use el LiDAR del teléfono para escanear el cuarto: paredes, aberturas y medidas reales. **→** Dos: las medidas de cada producto en la metadata del catálogo, para tener su caja 3D a escala. **→** Tres: ubicar las cajas, de dos maneras: que la IA decida en el plano dónde va cada una, o que una primera generación ponga los muebles, y tomar dónde quedó cada uno para poner ahí su caja a escala. **→** Cuatro: generar, con cada mueble llenando su caja, en su tamaño y lugar reales. **→** Más adelante, con modelos 3D de los productos, si el negocio los tiene, en lugar de cajas: el generador solo tiene que hacerlos verse reales. Lo que falta: las medidas, del ambiente y de los productos; pasar las cajas sin que queden dibujadas; y elegir cómo se ubican y medirlo en muchos ambientes.

## 47. Conclusiones
*Cierre · ~0:45 · desde el minuto 29:50*

Para cerrar, cinco cosas. Lo que más importó fue el texto que se indexa, no el modelo. **→** El mejor reranker es un VLM mirando las fotos, y nuestro paso de elegir ya lo es. **→** Las métricas con ground truth subestiman, así que hace falta un juez, validado y preguntado en los dos órdenes. **→** El catálogo decide qué se puede recomendar, y evaluar con ambientes variados cambió la decisión. **→** Y la imagen necesita un control automático para que el cuarto sea el del cliente.

## 48. Gracias
*Portada · ~0:05 · desde el minuto 30:35*

Gracias. ¿Preguntas?

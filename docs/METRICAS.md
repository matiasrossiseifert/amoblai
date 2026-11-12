# Métricas de amoblai: qué mide cada una y cuáles valen más

Pensadas de cero para nuestro caso, después de leer las clases 7 a 11 (PDFs y transcripciones,
resumen en `docs/clases/notas_clases.md`). Las de la propuesta original no se mantienen por
obligación: cambió el enfoque (de retrieval por imagen a RAG por texto) y cambió el producto
(foto + pedido → lista de compra + imagen del ambiente amoblado).

Todo lo de esta página es gratis: corre local o con subagentes de Claude Code como jueces. Lo
pago (el reranking con Opus sobre el catálogo ampliado, más imágenes generadas) está al final,
con su costo. Los números son del catálogo de 855 productos y de las 552 consultas con producto
anotado de los 65 ambientes IKEA, salvo que se diga otra cosa. Las tablas completas están en
`datos/resultados/reporte/reporte.md`.

## Qué tiene que salir bien (de ahí salen las métricas)

El usuario manda una foto de su ambiente y un pedido ("un living nórdico y cálido"). Le sirve el
resultado si:

1. **los productos son buenos para el pedido y para el ambiente** (estilo, tipo, tamaño);
2. **existen** (son del catálogo, con su medida y su precio);
3. **la imagen muestra esos productos** y no otros parecidos inventados;
4. **la imagen es su ambiente** (las mismas paredes, la misma cámara);
5. sale **barato y rápido**.

En el esquema de la clase 11 (pregunta, contexto, respuesta, ground truth): la pregunta es la
foto con el pedido; el contexto son los candidatos que trae la búsqueda para cada pieza (el top-3
que ve el LLM que elige); la respuesta es la lista elegida con su porqué y la imagen. El ground
truth existe en dos lugares: los productos anotados en las fotos de IKEA (para el retriever) y
la foto del catálogo de cada producto (para la imagen).

## Cómo las ordené

Cada métrica se juzga por seis cosas:
- **validez**: si mide algo que le importa al usuario;
- **ground truth**: si es real (anotaciones, foto del catálogo, foto original) o lo pone un juez
  LLM;
- **poder estadístico**: cuántos casos tiene y qué intervalo de confianza;
- **sensibilidad**: si separa las configuraciones de la ablación;
- **accionable**: si, cuando baja, dice qué tocar (la matriz de la clase 11);
- **costo y reproducibilidad**.

"Mejor" es la que combina mejor las seis para este trabajo, no la más importante en abstracto.
La fidelidad de la imagen importa muchísimo, pero hoy se mide sobre una sola imagen.

## El ranking

| # | Métrica | Evalúa | Ground truth | Valor hoy (mejor método) |
|---|---|---|---|---|
| 1 | MRR@10 | retrieval (orden del contexto) | anotaciones IKEA | 0,651 [0,62–0,69] |
| 2 | hit@1 | retrieval, y después del reranking | anotaciones IKEA | 0,533 [0,49–0,57] |
| 3 | Context recall@K y curva de hit@k | retrieval → generación (¿el contexto tiene la respuesta?) | anotaciones IKEA | @3: 0,782, @10: 0,928 |
| 4 | Relevancia graduada del top-3 (útil@1, útil@3, NDCG@3) | retrieval, con juez | juez LLM, validado contra las anotaciones | útil@1 0,747, útil@3 0,840 |
| 5 | Fidelidad de producto en la imagen | generación (faithfulness visual) | foto del catálogo | 7 de 10 identificados en 2 imágenes, coseno 0,53–0,68 (vara real: hit@1 0,444, coseno 0,41) |
| 6 | Ambiente preservado (SSIM fuera de los muebles, SIFT) | generación (restricción del caso) | foto original | SSIM 0,975 y 0,829; cámara quieta en las dos (SIFT) |
| 7 | Faithfulness del porqué (RAGAS) | generación (texto) | juez LLM | 0,89 a 0,97 |
| 8 | Context precision@10 (RAGAS) | retrieval | anotaciones IKEA | 0,630 [0,60–0,66] |
| 9 | NDCG@10 | retrieval | anotaciones IKEA | 0,652 [0,62–0,68] |
| 10 | Answer relevance (RAGAS, ingeniería inversa del pedido) | de punta a punta | juez LLM + embeddings | 0,60 a 0,73 (vara 0,37–0,40) |
| 11 | Pedido ↔ imagen (SigLIP 2) | generación (imagen) | ninguno (alineación) | +0,077 y +0,061 sobre la foto vacía; 1.º de 7 pedidos en las dos |
| 12 | Presencia y piezas inventadas | generación (imagen) | la lista | 10/10 presentes; 1 falsa inventada (la 2.ª mesita del juego, vista como banqueta) |
| 13 | Calibración del score (AUROC "el primero está bien") | retrieval (negative rejection) | anotaciones IKEA | AUROC 0,655 |
| 14 | Separabilidad del espacio (vecino del mismo kind, silhouette, UMAP) | indexing | kinds del catálogo | Qwen3 0,894, BGE 0,918 |
| 15 | Costo y latencia | operación | ledger de gastos | US$0,21–0,22 y 64–74 s por corrida |

Además hay cuatro **metamétricas**, que no miden al sistema sino cuánto se puede creer en las de
arriba: el IC 95% bootstrap por ambiente, la reproducibilidad entre escritores de consultas, el
acuerdo del juez con el ground truth y la varianza entre jueces. Están más abajo.

### 1. MRR@10: la mejor métrica que tenemos

- **Qué evalúa:** el retriever, es decir, el orden del contexto. Es el recíproco del puesto del
  primer producto relevante en el top-10, promediado (la métrica de sistemas de recomendación que
  nombró la clase).
- **Cómo:** cada consulta la escribió un subagente mirando una foto de IKEA, sin ver el catálogo
  ni las anotaciones. Es lo mismo que hace el paso plan del flujo: el producto en las mismas ocho
  líneas del catálogo. Relevantes: los SKUs anotados en ese ambiente del mismo grupo. Para los
  muebles el grupo es la categoría (sofá, silla, mesa...); para lámparas y decoración, el kind.
- **Por qué es la primera:**
  - el ground truth es real y lo armó IKEA, no nosotros;
  - tiene 552 consultas y un IC por bootstrap de ambientes;
  - es gratis y determinística;
  - es la más sensible de las que miramos: va de 0,143 (naive) a 0,651, y separa a Qwen3 de BGE
    (0,599) con IC que no se pisan;
  - usa todo el top-10, que es justamente lo que ve el reranker, y castiga más el puesto 2 que el
    1. Eso importa porque el LLM que elige mira los candidatos en orden ("lost in the middle").
- **Debilidades:**
  - mide "encontrar el producto que se ve", no "el mejor producto para el pedido" (eso lo cubre
    la 4);
  - el ground truth es permisivo con el grupo: cualquier sofá anotado en el ambiente vale para una
    consulta de sofá, porque las anotaciones de IKEA no dicen dónde está cada producto;
  - la consulta la escribe un subagente, no el plan con el pedido del usuario.
- **Si baja (matriz de la clase):** es un problema del retriever. Revisar el indexing: las
  descripciones, el embedder, los filtros por metadata, el reranker.

### 2. hit@1: la más fácil de explicar

- **Qué evalúa:** el retriever (con el filtro por tipo, 0,533), y el reranking después. Con Opus
  mirando el top-10 llegó a 0,803 sobre el catálogo de 268.
- **Por qué la segunda:** es la que se entiende en una frase ("la primera opción es el producto
  exacto el 53% de las veces") y es la que mueve un reranker. Pero es binaria: tira la diferencia
  entre el puesto 2 y el 10, y tiene más ruido (IC de ±0,04 contra ±0,03 del MRR).
- **Por categoría** dice dónde está el problema: sillas 0,84, guardado 0,73, mesas 0,69,
  lámparas 0,59, deco 0,35 y alfombras 0,31. Lo difícil son los productos muy parecidos entre sí:
  hay 53 almohadones y 89 alfombras.

### 3. Context recall@K y la curva de hit@k: ¿llega lo correcto al LLM que elige?

- **Qué evalúa:** la frontera entre retriever y generador. Es el context recall de la clase,
  bajado a productos: por ambiente, de los productos anotados que buscan sus consultas, cuántos
  están en el contexto (la unión de los top-K). Las "frases del ground truth atribuibles al
  contexto" son acá productos.
- **Valores:** con K=3, lo que el flujo le pasa hoy al LLM por pieza, da **0,782** [0,75–0,82].
  Con K=10, lo que mira el reranker, da **0,928** [0,91–0,95]. La curva de hit@k
  (`reporte/curva_k.png`) muestra cuánto se gana con cada candidato extra: hit@1 0,533, hit@3
  0,728, hit@5 0,813, hit@10 0,895, hit@20 0,958, hit@50 0,995.
- **Por qué importa:** si el producto no está en el contexto, el LLM no lo puede elegir. Es el
  techo del choose y del reranking. Y responde la pregunta de la clase ("¿por qué k=5 y no
  k=10?"): cada candidato más por pieza son unos 375 tokens de imagen (unos US$0,0015 con Opus,
  medido en el choose). Pasar de 3 a 10 candidatos en un ambiente de 6 piezas suma unos US$0,06
  por corrida, más el riesgo de que el LLM se distraiga con más fotos parecidas. Con k=3, una de
  cada cuatro piezas no tiene el producto correcto entre las opciones. **Recomendación** para el
  flujo: subir `furnish.candidates` a 5, que suma 8 puntos de hit@k por unos US$0,02 por corrida.
  O pasarle 10 al reranker y quedarse con sus 3 primeros, que es lo que mostró el reranking con
  Opus (0,64 → 0,80 de hit@1).
- **Por qué no está más arriba:** satura (hit@10 ya es 0,9), así que separa mal entre
  configuraciones buenas.

### 4. Relevancia graduada del top-3: ¿sirve lo que se trae, aunque no sea el SKU anotado?

- **Qué evalúa:** el retriever, medido por lo que le sirve al usuario. Un juez (subagente de
  Claude Code) mira la foto del ambiente y la de cada uno de los 3 primeros candidatos, y le pone
  2 (el mismo o indistinguible), 1 (una alternativa aceptable) o 0 (no sirve). No sabe cuál es el
  anotado. Fueron 150 consultas al azar: 75 con producto anotado en el catálogo y 75 sin.
- **Es** el context precision de RAGAS tal como se calcula cuando no hay ground truth (un LLM
  etiqueta cada v_k), y el NDCG graduado de la clase.
- **Valores:**
  - el primer candidato sirve (nota 1 o 2) en el **74,7%** [68–82] de las consultas, contra un
    hit@1 exacto de 0,53;
  - alguno del top-3 sirve en el **84%**;
  - con producto anotado, 87% y 95%;
  - **sin producto anotado** (el catálogo no tiene el que se ve), igual hay una alternativa
    aceptable primero en el 63% de las consultas;
  - NDCG@3 graduado: 0,78.
- **Validación del juez:** al producto anotado le dio 2 en el 81% de las veces que apareció en
  el top-3, y a los demás candidatos solo en el 5%. Coincide con el ground truth donde lo hay, así
  que se le puede creer donde no lo hay.
- **Por qué cuarta y no primera:** la nota la pone un LLM (hay un loop LLM-juzga-LLM, como avisó
  la clase), y son 150 consultas, no 552. Pero es la que mejor responde "¿le sirve al usuario?", y
  corrige la debilidad principal de las tres primeras: un sofá casi idéntico al anotado deja de
  contar como error.

### 5. Fidelidad de producto en la imagen: ¿lo que se ve es lo que se compra?

Es la idea del recorte contra la foto del catálogo, y es la faithfulness de la clase llevada a la
imagen: ¿la imagen usa el contexto recuperado o dibuja otra cosa?

- **Cómo:**
  - Grounding DINO busca cada producto de la lista en la imagen final, con las frases del
    detector de su categoría;
  - el recorte se embebe con DINOv3 (el mejor embedder de imagen de la v0), igual que la foto del
    catálogo;
  - por producto sale el coseno con su foto y su puesto entre todos los productos del catálogo de
    su tipo, ordenados por parecido al recorte. Puesto 1 quiere decir "se reconoce como ese
    producto y no como otro parecido".
- **La vara**, que es la otra idea (el recorte del mueble real en su lugar): la misma
  identificación con las fotos reales de IKEA, donde cada producto está fotografiado de verdad en
  un ambiente. Sobre 545 recortes de 64 ambientes da hit@1 0,444 [0,39–0,50] y coseno medio 0,41.
  Así se sabe qué es un número "bueno".
- **Hoy, dos imágenes generadas** con Nano Banana 2:
  - **prueba-alvear2** (living): se detectan los 4 productos y 3 se identifican (el sillón, la
    mesa y la alfombra). El sofá queda 7.º de 37, porque hay muchos sofás blancos. Coseno medio
    0,68.
  - **experimento** (rincón de lectura, foto de un compañero): se detectan los 6 productos y 4
    se identifican (la estantería, el sillón, la lámpara de pie y las mesitas nido). La alfombra
    redonda queda 9.ª de 89 y la cortina 10.ª de 255. Coseno medio 0,53.
  - Los cosenos son más altos que en las fotos reales (0,41): el generador copia la foto de
    referencia.
  - Lo difícil coincide con la vara: alfombras (perspectiva oblicua contra la foto cenital del
    catálogo; 0,30 en fotos reales) y textiles.
  - `6_recortes.jpg` muestra cada foto al lado de su recorte.
- **Una corrección que salió de usarla:** al principio cada producto se quedaba con la detección
  de más score de su categoría. En experimento, el sillón agarró unas mesitas nido que el detector
  vio como banqueta (puesto 77 de 78). Ahora, entre las detecciones candidatas, gana la que más se
  parece a la foto del producto. Esto favorece un poco la identificación: en prueba-alvear2, la
  alfombra pasó de un recorte de la alfombra entera (10.ª) a uno de una franja (1.ª).
- **Por qué quinta:** es la métrica de generación más importante para el producto, tiene
  referencia real y es gratis. Pero hay dos imágenes, y depende del detector (cajas parciales,
  la segunda mesita del juego nido detectada como banqueta) y de la perspectiva.

### 6. Ambiente preservado: ¿es mi living?

- **Qué evalúa:** una restricción propia del caso. El generador no puede cambiar paredes,
  aberturas ni la cámara (las primeras pruebas de la v0 recortaban o rehacían el ambiente).
- **Cómo** (las técnicas de imagen de la clase):
  - SSIM entre la foto original y la final, fuera de las cajas de los muebles;
  - SIFT con RANSAC: qué fracción de los puntos de la foto original se reencuentra en la final
    con una homografía, y cuánto se movieron.
- **Hoy:**
  - **prueba-alvear2:** SSIM fuera de los muebles 0,975 (en toda la imagen 0,845, por los muebles
    nuevos). El 55% de los puntos SIFT se reencuentra, con desplazamiento mediano de 0: la cámara
    no se movió.
  - **experimento:** SSIM fuera de los muebles 0,829, y se reencuentra solo el 13% de los puntos
    SIFT. Muchos puntos estaban en la vista de la calle por el ventanal, que las cortinas nuevas
    tapan en parte. Los que se reencuentran se movieron un 0,1% del ancho: la cámara tampoco se
    movió.
- **Debilidad:** SSIM y SIFT también bajan con cambios legítimos (sombras, cortinas que tapan una
  ventana). El desplazamiento mediano es la señal más limpia de "es la misma foto". Son dos
  imágenes.

### 7. Faithfulness del porqué (RAGAS)

- **Qué evalúa:** el generador en texto. El paso choose explica cada elección ("el sofá blanco de
  brazos rectos y patas de abedul..."). Un juez parte la explicación en afirmaciones de hecho y
  marca cuáles se infieren de lo que vio el sistema: el pedido, la foto del ambiente, y la foto,
  la descripción y la medida de cada producto. Es la fórmula de la clase: afirmaciones sostenidas
  sobre afirmaciones.
- **Hoy:** 0,889 (27 afirmaciones), 0,96 (25), 0,923 (26) y, en experimento, 0,971 (34). Lo que
  no se sostiene ahí: "es la única alfombra redonda", porque el juez no ve los otros
  candidatos.
- **Lo útil es lo que no se sostiene:**
  - "piso de roble" (se ve madera, no la especie);
  - "la alfombra entra bajo el frente del sofá y del sillón": el sofá y el sillón no tienen medida
    en el catálogo, así que el LLM supone. Es un hallazgo accionable: faltan las medidas de los
    asientos (ver `FUTURO.md`).
- **Por qué séptima:** detecta alucinaciones concretas, pero el juez es un LLM, son 3 respuestas
  y el juez varía (ver metamétricas).

### 8. Context precision@10 (RAGAS)

- **Qué evalúa:** el retriever. Es la fórmula exacta de la clase: Σ Precision@k · v_k sobre los
  relevantes del top-K, con v_k de las anotaciones. Valor: **0,630** [0,60–0,66].
- **Por qué octava:** con 1 o 2 relevantes por consulta es casi lo mismo que el MRR (en el
  ejemplo de Francia da 0,5, igual que 1/2). Sobre las 32 configuraciones de la ablación,
  correlaciona 0,9999 con el MRR. Está para que se pueda comparar con la clase; no agrega
  información.

### 9. NDCG@10

- **Qué evalúa:** el retriever (la otra métrica de ranking que nombró la clase). Valor:
  **0,652** [0,62–0,68].
- Con relevancia binaria es redundante: correlaciona 0,998 con el MRR sobre las 32
  configuraciones. La versión graduada, que sí agrega, es la de la 4.

### 10. Answer relevance (RAGAS): ¿el resultado responde al pedido?

- **Qué evalúa:** de punta a punta. Es la fórmula de la clase: un juez que no vio el pedido mira
  la respuesta (la lista y, si hay, la imagen final) y escribe tres pedidos que esa respuesta
  contesta. Después se toma el coseno medio entre cada uno y el pedido original, con Qwen3, que es
  multilingüe.
- **Hoy:** 0,69 a 0,73 en los livings de alvear, contra 0,37 de la vara (el mismo coseno con
  pedidos que no tienen nada que ver). El juez reconstruyó "un living nórdico y cálido con sofá,
  sillón para leer, mesa ratona y alfombra" casi literal. En experimento da 0,60, contra una vara
  de 0,40. Reconstruyó "un rincón de lectura cálido con sillón, biblioteca, alfombra redonda y
  lámpara", pero llamó al ambiente "living" y no nombró el "tono amaderado del suelo". El pedido
  original es más largo y específico, y eso baja el coseno.
- **Por qué décima:** separa lo relacionado de lo que no lo es, pero es poco sensible a matices y
  depende del largo del pedido. Además depende del juez y hay 4 corridas.

### 11. Pedido ↔ imagen (SigLIP 2)

- **Qué evalúa:** la imagen contra el texto del pedido, en el espacio de embeddings imagen-texto
  (la clase: "por lo general se usan embeddings para comparar imágenes").
- **Hoy:** la imagen final se parece al pedido 0,077 (alvear) y 0,061 (experimento) más que la
  foto vacía, y en las dos el pedido real queda 1.º entre 7, contra seis pedidos de contraste. El de "un ambiente vacío, sin muebles" baja
  con la imagen final, como debe.
- **Por qué abajo:** los modelos tipo CLIP entienden "un living con sofá", no "nórdico y cálido".
  La escala de cosenos es chica.

### 12. Presencia y piezas inventadas

- **Qué evalúa:** la imagen contra la lista: qué productos se detectan y qué muebles aparecen que
  no son de la lista ni estaban en la foto original. Las partes de un producto (los almohadones
  del sofá) no cuentan como inventadas.
- **Hoy:**
  - prueba-alvear2: 4/4 presentes, 0 inventadas; una franja de la alfombra sale como "repetida".
  - experimento: 6/6 presentes, 1 inventada falsa (la segunda mesita del juego nido, que el
    detector ve como banqueta) y 1 repetida (el segundo paño de las cortinas). Las que caen en una
    categoría de la lista se separan como "repetidas": pueden ser el par de un producto.
- **Por qué abajo:** es un conteo que depende de los errores del detector. Sirve como alarma, no
  como medida fina.

### 13. Calibración del score: ¿la búsqueda sabe cuándo no sabe?

- **Qué evalúa:** el negative rejection de la clase. Es el AUROC del coseno del primer candidato
  para separar las consultas donde ese primero es el anotado de las que no, y el umbral que
  maximiza F1. Valor: **AUROC 0,655**. El umbral de F1 (coseno 0,77) acepta casi todo (recall
  0,98, precisión 0,55). El coseno solo no alcanza para decir "estoy seguro": separa lo que está
  fuera del dominio, no el producto exacto entre parecidos.
- **Para qué:** avisar "no encontré algo así" o mandar al reranker solo lo dudoso. En la UMAP, la
  consulta fuera del dominio tiene coseno máximo 0,32, contra 0,83 de una del dominio.
- **Por qué abajo:** es indirecta; no mide calidad sino si el score sirve para decidir.

### 14. Separabilidad del espacio de embeddings

- **Qué evalúa:** el indexing, antes de cualquier consulta. Para cada producto, si su vecino más
  cercano es de su mismo kind; también el silhouette por kind, y la UMAP de la clase
  (`reporte/umap.png`, con una consulta del dominio y una de afuera).
- **Hoy:**
  - vecino del mismo kind: hashing 0,834, BGE 0,918, Qwen3 0,894;
  - silhouette: 0,08, 0,22 y 0,18.
- **Por qué casi última:** BGE separa mejor los kinds que Qwen3, pero Qwen3 recupera mejor (hit@1
  0,533 contra 0,476). Esta métrica no predice la tarea. Sirve para diagnosticar, no para decidir
  el embedder.

### 15. Costo y latencia

- **Qué evalúa:** la operación. La clase pidió costo (tokens, llamadas, infra) y el enunciado lo
  pone entre los extras.
- **Hoy, por corrida** (prueba-alvear2: 4 piezas; experimento: 6 piezas):

| Paso | prueba-alvear2 | experimento |
|---|---|---|
| plan | US$0,048, 19 s (3.362 tokens de entrada, 1.743 de salida) | US$0,057, 22 s |
| choose | US$0,046, 12 s (6.755 tokens de entrada, 14 imágenes) | US$0,053, 12 s (8.070 tokens de entrada) |
| scene | US$0,032, 9 s | US$0,032, 10 s |
| imagen (Nano Banana 2) | US$0,08, 24 s | US$0,08, 29 s |
| retrieve | gratis, menos de 1 s (local) | gratis |
| **total** | **US$0,21, unos 64 s** | **US$0,22, unos 74 s** |

- **Evaluar sale:**
  - US$0,020 por consulta con reranking por VLM;
  - US$0 todo lo demás (embeddings locales, ChromaDB en memoria, jueces subagentes).
- **Por qué última:** no mide calidad. Igual es imprescindible para decidir, por ejemplo, cuántos
  candidatos pasarle al LLM (la 3).

## Metamétricas: cuánto creerle a cada número

- **IC 95% bootstrap por ambiente.** Las consultas de un mismo ambiente no son independientes
  (mismo estilo, misma luz), así que se remuestrean ambientes enteros. Va en todas las métricas
  del retriever.
- **Reproducibilidad.** La clase pidió "promedio de ejecuciones y desvío estándar". La búsqueda
  es determinística: correrla dos veces da lo mismo. Lo que varía es quién escribe la consulta,
  que en el flujo es el paso plan. Las consultas se escribieron tres veces, por subagentes
  distintos, con los mismos prompts y las mismas fotos (864, 865 y 855 consultas):

| Método | hit@1 (media ± desvío, rango) | MRR@10 |
|---|---|---|
| Qwen3, filtro por tipo | 0,544 ± 0,026 (0,525–0,575) | 0,655 ± 0,017 |
| Qwen3, filtro por kind | 0,536 ± 0,024 | 0,640 ± 0,015 |
| hashing, descripciones, filtro por tipo | 0,513 ± 0,027 | 0,635 ± 0,021 |
| BGE, filtro por tipo | 0,488 ± 0,015 | 0,609 ± 0,009 |
| naive (texto del vendedor) | 0,074 ± 0,002 | 0,139 ± 0,003 |

  Dos lecturas:
  - **Los valores absolutos se mueven unos ±2,5 puntos** de hit@1 según quién escribió las
    consultas. Es del orden del IC bootstrap (±4). Un número suelto, como "0,533", hay que leerlo
    como "0,54 ± 0,03". El MRR varía menos (±1,7), otra razón para ponerlo primero.
  - **Las comparaciones sí son reproducibles:** Qwen3 le gana a BGE (+0,02 a +0,09), a hashing
    (+0,02 a +0,04) y al filtro por kind (+0,01) en las tres escrituras, siempre con el mismo
    signo. Las conclusiones de la ablación no dependen del escritor. La ventaja de Qwen3 sobre
    hashing es chica: lo que hace el trabajo son las descripciones de ocho líneas, no el
    embedder.

- **Acuerdo del juez con el ground truth** (relevancia graduada): 81% de 2 para el anotado,
  contra 5% para el resto.
- **Varianza entre jueces.** Dos jueces independientes sobre la misma respuesta (prueba-alvear2 y
  prueba-alvear2-scene-v2 tienen el mismo choose) dieron faithfulness 0,96 y 0,92: una afirmación
  de diferencia, sobre unas 25. Para comparar dos versiones del choose hace falta más de un juez
  por respuesta.
- **Data leakage** (la clase): no se entrenó nada, así que no hay train y test que se mezclen. El
  riesgo es que el mismo modelo escriba los dos lados. Las descripciones las escribieron
  subagentes de Claude mirando la foto del producto (con su nombre); las consultas, otros
  subagentes mirando la foto del ambiente, sin el catálogo ni las anotaciones. Un vocabulario
  compartido ("warm", "Scandinavian") puede ayudar, pero en el flujo real el plan también es
  Claude, así que es representativo. Los nombres de IKEA no están en las consultas. La ablación
  con el nombre adelante de la descripción dice cuánto aporta el nombre. Ningún número da 100%,
  que según la clase sería sospechoso.

## Accionables (la matriz de la clase con nuestros números)

| | Generador alto | Generador bajo |
|---|---|---|
| **Retriever alto** | lámparas, guardado, sillas: hit@10 alto y la imagen las reproduce | — |
| **Retriever bajo** | — | deco y alfombras: hit@1 0,35 y 0,31, y la alfombra es la peor identificada en la imagen |

- **Retriever, deco y alfombras:** el ranking falla entre productos casi iguales. Lo que
  corresponde es el reranking con el VLM mirando las fotos, que en el catálogo de 268 subió hit@1
  de 0,64 a 0,80, y quizás el kind como filtro solo ahí.
- **Generador:** la faithfulness del texto falla siempre por lo mismo, las medidas que el catálogo
  no tiene. Eso es la knowledge base, no el prompt.
- **Imagen:** la fidelidad baja en alfombras y sofás blancos. Para el Ejercicio 4: scene v2 y
  la imagen en 2K, medidos con estas mismas métricas.

## Lo que no usamos, y por qué

- **WER:** no hay audio.
- **BLEU, ROUGE, BERTScore:** no hay un texto de referencia que la respuesta tenga que reproducir.
- **FID, IS, KID:** miden realismo sobre cientos de imágenes, no fidelidad a un producto. Además
  generar imágenes cuesta.
- **SSIM contra un ambiente real amoblado:** no tenemos el mismo ambiente vacío y amoblado. El
  plan para tenerlo es el benchmark de reconstrucción de abajo.
- **Precision@K plana:** con 1 o 2 relevantes por consulta queda clavada abajo de 0,2 con K=10,
  sin información.
- **El context recall de RAGAS por frases:** nuestro ground truth son productos, no frases, así
  que se usa por producto (la 3).
- **Answer correctness, noise robustness, information integration:** no hay una respuesta
  correcta en texto, y el choose no sintetiza documentos largos.
- **LangSmith:** quedó afuera por decisión del equipo.

## Lo pendiente (pago, o esperando imágenes)

- **Reranking con Opus sobre el catálogo ampliado:** 367 llamadas sin caché, unos US$7,5. Hay que
  subir el tope de Anthropic.
- **Más imágenes generadas**, para que las métricas 5, 6, 11 y 12 tengan n. Gratis por la ruta
  manual (pegar la carpeta `manual/` en ChatGPT o Gemini) o unos US$0,21 por corrida.
- **Benchmark de reconstrucción:** vaciar fotos de IKEA con inpainting, amoblarlas con el flujo y
  compararlas con la real, el mismo mueble en el mismo lugar. Unos US$0,30 por ambiente.
- **Qwen3-Reranker** sobre las 552 consultas: gratis pero unas 15 h en esta CPU, minutos en una
  GPU.

## Cómo se corre

```bash
uv run amoblai evaluar                     # retrieval: MRR, hit@k, context precision/recall, NDCG, curva k
uv run amoblai evaluar --ablacion datos/configs/ablaciones/reproducibilidad.yaml --replica r2
uv run amoblai evaluar-graduada --armar 150   # lotes para los jueces; después, sin --armar, puntuar
uv run amoblai evaluar-imagen --referencia    # la imagen generada y la vara con fotos reales
uv run amoblai evaluar-respuesta              # RAGAS del porqué (jueces: subagentes o --juez opus --pagar)
uv run amoblai evaluar-espacio                # separabilidad y UMAP
uv run amoblai reporte                        # todo en datos/resultados/reporte/reporte.md
```

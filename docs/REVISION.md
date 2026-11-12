# Revisión crítica de amoblai (2026-11-12)

Qué pide el enunciado, qué haría alguien que piensa el problema desde cero, qué tenemos, qué
estaba mal y qué cambió. Está escrita para discutirla entre los tres antes de cerrar la entrega.

**Cómo se hizo.** Cinco lecturas independientes, sin ver unas las conclusiones de las otras:
una pensó el trabajo desde cero leyendo solo el enunciado y las clases (sin abrir el repo), y
cuatro auditaron lo hecho tratándolo como obra de alguien de quien no se sabe si es capaz:
arquitectura y código, métricas, experimentos, y una corrección contra el enunciado como la haría
la cátedra. Después se verificó cada hallazgo grave contra el código y los resultados guardados
antes de darlo por cierto. Todo lo que dice "verificado" se recalculó.

**En una página.**

1. **El núcleo está bien.** El diseño pensado desde cero coincide con el nuestro en lo que
   importa: descomponer el pedido en piezas, escribir cada consulta como una ficha del catálogo,
   indexar descripciones hechas desde la foto, filtrar por metadata, elegir el conjunto con un
   VLM, validar los ids. Los números del registro se reproducen al cuarto decimal desde los
   resultados guardados (12 corridas recalculadas, 0 diferencias). Los tests pasan (109).
2. **Lo que estaba mal no eran los números: era qué se comparaba y cómo se contaba.** El número
   de cabecera (0,69) no es del sistema que corre; el "query rewriting" se medía contra un rival
   que no es "no reescribir"; varias decisiones se presentaban como salidas de un experimento
   que no las sostiene (el embedder, el filtro, la escena sin LLM); las métricas del generador
   tenían una fuga de datos; el README mostraba la mejor de 8 imágenes.
3. **Había cuatro errores de código que importan para probar el sistema y para la demo**, ya
   arreglados (sección 3).
4. **Faltaban tres experimentos gratis que valen más que varios de los que hay**, ya corridos
   (sección 4): la consulta contra no reescribirla, la búsqueda léxica y la búsqueda con la foto
   del producto (multimodal), y qué líneas de la descripción hacen el trabajo.
5. **De ahí salió la versión 2, centrada en el RAG**: búsqueda híbrida (densa + léxica + foto).
   Medida gratis sobre el ground truth (hit@1 0,530 → 0,605) y confirmada de punta a punta en los
   11 ambientes reales (gana 5, empata 6, no pierde ninguno). Ya es la búsqueda del flujo; la
   versión 1 queda a una línea de configuración (sección 6).
6. **La búsqueda aporta en la tarea real**: contra 5 candidatos al azar del mismo kind, el flujo
   con búsqueda gana 7 a 0 (sección 4).
7. **Queda por decidir** (sección 8): el filtro de medidas, las presentaciones, y cosas chicas.

---

## 1. Qué pide el enunciado y cómo estamos

| Qué se evalúa | Dónde está | Estado | Qué falta |
|---|---|---|---|
| Problema que no sea un Q&A, definido desde los tres desafíos (actualizada, personalizada, alucinaciones) | README, presentaciones | bien | decir las tres palabras de la clase |
| Data loading y base de conocimiento curada | `dataset/`, `catalog/`, `correcciones.yaml` | bien | — |
| Splitting, justificado | un documento por producto; ablación | bien | contarlo como lo que es: no partir, y qué compone el documento (líneas, sección 4) |
| Embedding: algoritmo, si se varió, dimensión | T1, dimensión Matryoshka | bien el experimento, mal la conclusión | "gana Qwen3" no se sostiene contra una bolsa de palabras: decirlo |
| Base vectorial, justificada | ChromaDB = búsqueda exacta en 864 de 864 | bien | — |
| Retrieval: k y filtros | curva de candidatos; filtros | k bien; filtros flojo | el filtro del flujo (kind) no es el del número publicado; el de medidas nunca se midió |
| Pre y posprocesamiento | descripciones, validación de ids, control del ambiente | bien | — |
| Dataset | catálogo descripto, 864 consultas × 3 redactores, 11 ambientes vacíos | bien | los 11 pedidos enumeran las piezas: el pedido abierto no se evalúa |
| Métricas: al menos una del retriever y una del generador | METRICAS.md | retriever bien; generador flojo | arreglado esta noche (sección 5) |
| Ablación con cambios incrementales | README, T1 | bien con reparos | rehecha: un cambio por paso (sección 4) |
| Advanced RAG (al menos una técnica) | plan, filtros, elección | bien, mal nombrado | el plan es query expansion con respuesta hipotética (HyDE), no "query rewriting" |
| Extras | webapp, registro de gastos y tokens, investigación | bien | LangSmith no (decir por qué) |
| Ejercicio 3 (2 hojas) | `docs/entregas/ej3_informe.pdf` | bien | corregidas tres afirmaciones y el costo |
| Ejercicio 4: versión 1, versión 2, configuración antes y después | una lámina de 30 s | **flojo** | decidir (sección 6) |
| Oral: desafíos encontrados | disperso | flojo | una lámina: el cambio desde la propuesta aprobada |
| Oral: resultados en ambas versiones | no está | **falta** | sale de la sección 6 |

## 2. El problema pensado desde cero, contra lo que tenemos

Lo que dijo quien lo pensó sin ver el repo, y cómo estamos en cada punto:

| Pensado desde cero | Lo que tenemos |
|---|---|
| Buscar no es lo difícil (son 1.500 documentos cortos). Lo difícil es que **el pedido habla de un ambiente y los documentos de objetos**: hace falta descomponer el pedido en piezas y buscar cada una. Es la única técnica de Advanced RAG que el problema exige por estructura. | Igual: el paso `plan`. |
| Cada consulta se escribe **como la ficha del producto ideal**, en el formato del catálogo ("en mi base no tengo preguntas, tengo respuestas": la respuesta hipotética de la clase de Advanced RAG). | Igual. Lo llamábamos "query rewriting"; el nombre de la clase es query expansion con respuesta hipotética (HyDE). |
| La decisión con más sustancia es **qué representa a un producto en el índice**: el texto del vendedor, una descripción de lo que se ve, o la foto misma (embedding multimodal). | Teníamos las dos primeras. La tercera faltaba y es la otra ruta que nombró la profesora ("si no lo paso a texto, hay formas de pasarlo a embedding directamente"). Medida esta noche. |
| Splitting, dimensión, distancia y marca de la base vectorial son **trámite**: hay que tener la respuesta, no un gran experimento. | Los tenemos, y está bien que ocupen poco. |
| Tres controles sin los que ningún número significa nada: **azar dentro de la categoría**, **mismo presupuesto de candidatos** y **piso de ruido**. | Azar: sí. Piso de ruido: sí para quien escribe la consulta (tres redactores); no para el plan, la elección ni el juez. |
| El ground truth de IKEA es un **proxy** chico: sirve para comparar cambios grandes, no para elegir entre embedders. | Lo usábamos también para lo segundo. Corregido en cómo se cuenta. |
| Elegir entre los candidatos es **selección conjunta** (un conjunto que combina), con derecho a decir "no hay". | Igual (`choose`, cantidad 0). En 187 piezas nunca dijo "no hay": sustituye. |
| El prompt de la imagen lo arma **una plantilla** desde la lista validada, no un LLM. | Igual. |
| No haría: generar primero y buscar después por imagen; un agente con herramientas; fine-tuning; layout 3D; comparar modelos de imagen. | La primera era nuestra propuesta original (la "v0"): se abandonó. El resto no lo hicimos. |
| La pregunta más incómoda: **"¿hacía falta RAG si el catálogo entra en el contexto?"** | Sin respuesta escrita hasta hoy. Sección 7. |

**Complicaciones que tenemos y su justificación:**

| Complicación | ¿Justificada? |
|---|---|
| Describir cada producto con un VLM (8 líneas) | Sí: +0,42 de hit@1 sobre el texto del vendedor. Es el mayor efecto del trabajo. |
| Filtro duro por kind | Sí en el flujo, con costo: con filtro por tipo, el 11% de los candidatos de los 11 ambientes sería de otro kind (un sillón pedido y una silla de comedor ofrecida). Cuesta 2 a 3 puntos de hit@5 y hit@10 en el ground truth, porque a veces la consulta y el catálogo no coinciden en el kind fino (ratona / auxiliar). Hay que contarlo así. |
| Filtro duro por medidas | **No tiene evidencia.** El límite lo estima el plan a ojo desde una foto; solo el 34% de IKEA tiene alguna medida (ningún sofá ni sillón), así que lo que más recorta es el catálogo con mejores datos (ABO); en el catálogo combinado cambia el top-5 de 23 de las 52 piezas que traen límite, y nunca se evaluó. Además tenía un error de orientación (sección 3). Ahora se puede apagar (`furnish.size_filter`). Propuesta: apagarlo y dejar las medidas como dato para el que elige, o validarlo de punta a punta (US$2). |
| Dos catálogos (IKEA + ABO) | Sí por cobertura de estilos (T3b), con la salvedad de cómo se escribieron esos pedidos (sección 4). |
| Control del ambiente (SIFT) con reintento | El control, sí: en las 11 imágenes finales marcó los 4 ambientes donde el modelo movió la cámara o rehízo el cuarto. El reintento, dudoso: en esos 4 fallaron los 3 intentos (rescató 1 de 5 contando una corrida anterior) y cuesta dos imágenes más. Los umbrales (50 puntos, 1%) están puestos a mano. |
| Segunda foto del ambiente (`--vista`) | Sin evidencia: nunca se midió si cambia algo. Es opcional; decirlo o sacarlo. |
| Embedder neuronal (Qwen3) | Solo, no se distingue de contar palabras en este banco de prueba. Fusionado con la búsqueda léxica y con la foto, sí suma: es la versión 2. |
| Búsqueda híbrida (BM25 + foto con SigLIP 2) | Sí: +0,075 de hit@1 en el ground truth, con los tres redactores, y de punta a punta gana 5, empata 6 y no pierde. Corre local, sin costo por pedido. |

## 3. Errores encontrados y arreglados

| Qué pasaba | Arreglo |
|---|---|
| **Repetir la misma foto con otro pedido devolvía, sin avisar, la lista y la imagen del pedido anterior** (la carpeta de la corrida es el nombre de la foto y los pasos guardados se reutilizaban). | La carpeta de otro pedido se rechaza con un mensaje claro. Con test. |
| **Instalando como dice el README faltaba scikit-image**: la imagen se pagaba, el control del ambiente fallaba al importar y al reintentar se pagaba de nuevo. La CI no lo veía porque instala otro extra. | scikit-image y scipy pasan a las dependencias base. |
| **El filtro de medidas comparaba ancho con ancho y fondo con fondo**, pero IKEA guarda las alfombras como ancho × largo y ABO pone el lado mayor primero: quedaban afuera las alfombras de 200 × 300 justo cuando se pedía una grande. | Con los dos límites, la pieza puede ir girada. Con test. |
| La webapp mostraba la lista de compra en blanco para los productos de ABO. | Los datos salen de los candidatos de la corrida. |
| Cada evaluación reconstruía el índice versionado y dejaba carpetas huérfanas en git; y el índice no se enteraba si cambiaban las descripciones. | El índice se reconstruye solo si cambió el catálogo, las descripciones o el embedder. |
| El retrieve abría el índice y cargaba el modelo de embeddings de nuevo por cada pieza. | Una vez por corrida. |
| La curva que decidió "5 candidatos" no tenía código en el repo. | `amoblai evaluar-candidatos` la rehace (mismos números). |
| Las métricas del generador (sección 5). | Jueces nuevos. |

Sin tocar (para decidir): no hay tope de piezas (una corrida llegó a 76 fotos en la elección);
las respuestas del LLM no tienen esquema ni reintento; el lugar que decide el plan no llega al
modelo de imagen; el reparto de candidatos entre dos kinds; código que nunca se usó (los tres
clientes de OpenAI, `whole_catalog`, el describer por visión). Detalle en el informe de
arquitectura (al final).

## 4. Experimentos: ranking y qué cambia

Sin borrar ninguno. "Va" quiere decir que merece lugar en el oral.

### Sí o sí van

| Experimento | La pregunta | Qué corregir al contarlo |
|---|---|---|
| **Qué se indexa** (texto del vendedor contra nuestras descripciones) | ¿Hace falta describir cada producto? | Es el mayor efecto (+0,42 [0,37–0,47], pareado). La línea de base estaba debilitada: no incluía el tipo que le pone el vendedor. Rehecha. |
| **Cómo se escribe la consulta** (nuevo) | ¿Sirve escribir la consulta como una ficha, contra no reescribirla? | Es la técnica de Advanced RAG del flujo y no estaba medida contra no hacerla. Ver abajo. |
| **Elección con el VLM** (rerank del top-10) | ¿Un VLM que mira las fotos ordena mejor que el coseno? | +0,151 [0,115–0,190]. Es el techo de una técnica aislada, **no un paso del flujo**: el reranker ordena contra la consulta sin ver el ambiente; `choose` elige con la foto del ambiente y el pedido, y nunca se midió contra ground truth. |
| **Cuántos candidatos** | ¿Por qué 5 y no 3 o 10? | De 3 a 5: +0,029 [0,015–0,043], significativo. Sumar que en los 11 ambientes el 24% de lo elegido salió de los puestos 4 y 5. |
| **Texto contra imagen** (la propuesta original contra la actual) | ¿Buscar por descripción o por recorte? | Reportarlo con la misma unidad: por producto anotado, 0,43 contra 0,55 (+0,12 [0,04–0,20]). Y decir qué fue la v0: solo se construyó y evaluó su buscador; nunca corrió de punta a punta. |
| **Qué catálogo, de punta a punta** | ¿IKEA, ABO o los dos? | Lo único que evalúa el flujo entero. 8 a 2 da p = 0,11; el 6 a 0 es sobre pedidos escritos sabiendo qué le falta a IKEA. La decisión es razonable; el titular, no. |
| **Tres redactores** | ¿Cuánto cambia el número según quién escribe la consulta? | ±2,5 puntos. Usarlo: no leer diferencias de 2 puntos. |
| **Híbrida y multimodal** (nuevo) | ¿Suman la búsqueda por palabras y la foto del producto? | Ver abajo. Es la versión 2. |
| **Versión 1 contra versión 2, y con búsqueda contra sin búsqueda, de punta a punta** (nuevo) | ¿La mejora del buscador llega a la lista? ¿La búsqueda aporta en la tarea real? | Ver abajo. Decir n y p. |

### Normalitos (correctos, de trámite o de respuesta previsible)

Embedder (hashing, BGE, Qwen3): solo se sostiene Qwen3 sobre BGE. Filtros: va como resultado
honesto (no suma en el banco de prueba; se usa por otra razón). Dimensión (512 = 1024).
Splitting por línea. ChromaDB contra búsqueda exacta. Cross-encoder MiniLM (empeora). Catálogo
ampliado y revisado (son decisiones de datos, no experimentos). ABO como distractores (contarlo
con hit@5: baja 3,5 puntos). Relevancia graduada (buena medición, no compara nada). La grilla de
la v0 (el mejor diseño del repo, pero de la versión abandonada). La prueba del flujo (sirve para
contar desafíos). Una lámina para todos los de trámite juntos.

### No sirven tal como están

| Experimento | Por qué | Qué hacer |
|---|---|---|
| "Query rewriting" contra solo Type o solo el kind | Buscar "rug" entre 89 alfombras es azar por construcción: mide sacarle información a la consulta, no reescribirla. | Reemplazado por el de arriba. |
| La escena sin LLM ("experimento 12") | Una imagen contra una, con otro pedido y otras piezas; y la escena escrita por el LLM tiene mejor número en las cuatro métricas. No estaba en el registro. | Contarla como decisión de costo y simplicidad (ahorra una llamada), no como resultado. |
| La réplica con cajas (T5) | Un cuarto, 3 imágenes por variante, no decide nada del flujo ni tiene que ver con el RAG. Solo se sostiene "indicar el lugar ayuda" (0,20 → 0,40–0,52); "ninguna quedó dibujada" es ruido (p = 0,40) y la explicación de la lámpara se da vuelta en la ronda 2. | Una lámina de trabajo futuro, sin esas dos frases. |
| Los experimentos de imagen diseñados (T4) | No se corrieron. | No son experimentos: son pendientes. |
| La imagen de un caso y RAGAS como "resultados" | El README mostraba la mejor de 8 imágenes (3 de 4 productos); sobre las 8 son 26 de 52. RAGAS: 3 respuestas, con fuga. | Tabla completa; jueces nuevos (sección 5). |

### Lo que se corrió esta noche (gratis, local; 549 consultas, catálogo IKEA de 819)

Cada método contra la base y contra el paso anterior, con la diferencia pareada (las mismas
consultas) y su IC 95% por bootstrap de ambientes.

**El camino incremental, un cambio por paso** (`ablaciones/camino.yaml`). Reemplaza a "de 0,08 a
0,69", que fundía tres cambios en un escalón, partía de una línea de base debilitada y terminaba
en un número que no es del sistema.

| Paso | hit@1 [IC 95%] | hit@5 | hit@10 | MRR@10 | Cambio en hit@1 contra el paso anterior |
|---|---|---|---|---|---|
| 1. RAG naive: el texto del vendedor embebido, la consulta sin reescribir | 0,109 [0,08–0,14] | 0,299 | 0,439 | 0,194 | |
| 2. + la base que armamos: cada producto descripto desde su foto, en 8 líneas | 0,297 [0,25–0,35] | 0,601 | 0,736 | 0,430 | +0,188 [0,137; 0,237] |
| 3. + la consulta escrita como una ficha del catálogo (respuesta hipotética, HyDE) | 0,535 [0,49–0,58] | 0,811 | 0,885 | 0,652 | +0,239 [0,189; 0,287] |
| 4. + filtro de metadata por kind: **la búsqueda del flujo (versión 1)** | 0,530 [0,49–0,57] | 0,790 | 0,863 | 0,641 | −0,005 [−0,015; +0,006]; en hit@5, −0,020 [−0,037; −0,004] |
| 5. + búsqueda léxica (BM25) fusionada | 0,581 [0,54–0,63] | 0,807 | 0,876 | 0,674 | +0,051 [0,013; 0,088] |
| 6. + la foto del producto (SigLIP 2) fusionada: híbrida multimodal | 0,605 [0,56–0,65] | 0,825 | 0,883 | 0,701 | +0,024 [0,002; 0,045] |

Lecturas: (a) las dos decisiones que más pesan son la base de conocimiento (+0,19) y cómo se
escribe la consulta (+0,24), y se miden por separado; (b) el filtro por kind no suma en este
banco de prueba y cuesta 2 puntos de hit@5: se usa por otra razón (sección 2); (c) la búsqueda
híbrida suma 7,5 puntos de hit@1 y 3,5 de hit@5 sobre la versión 1, con intervalos que no tocan
el cero. Aparte, y no como un paso del flujo: si un VLM elige entre los 5 primeros mirando las
fotos, el acierto sube a 0,667 (medido sobre el paso 3 con filtro por tipo).

**Cómo se escribe la consulta, contra no reescribirla** (`ablaciones/consulta.yaml`). Las
consultas guardadas ya traían la versión sin reescribir: la frase corta con que el redactor
nombró la pieza ("square pine coffee table, front center"; 8 palabras de mediana).

| Consulta | Densa (el flujo) hit@1 / hit@5 | Léxica (BM25) hit@1 | Por foto (SigLIP 2) hit@1 / hit@5 |
|---|---|---|---|
| La ficha de ocho líneas (lo que escribe el plan) | 0,530 / 0,790 | 0,517 | 0,508 / 0,807 |
| La frase natural, sin reescribir | 0,324 / 0,648 | 0,332 | **0,479 / 0,781** |
| Solo la línea Type | 0,299 / 0,641 | | |
| Solo el nombre del kind (el piso) | 0,066 / 0,264 | | |

Lecturas: (a) escribir la consulta como una ficha suma +0,206 [0,157; 0,254] de hit@1 sobre no
reescribirla (antes se informaba "de 0,06 a 0,54", contra un rival que era azar por construcción);
(b) cuando la consulta es pobre, el filtro por kind sí ayuda (0,297 sin filtro → 0,324), y cuando
es rica, no; (c) **la búsqueda por foto casi no necesita la reescritura**: con la frase natural
da 0,479, mucho más que el texto (0,324). La descripción en texto necesita que la consulta hable
como el catálogo; la foto no. Es evidencia de que el banco de prueba no mide solo vocabulario
compartido, y un argumento más a favor de fusionar las dos rutas.

**Búsqueda léxica, por foto e híbrida** (`ablaciones/hibrido.yaml`). La base es la búsqueda del
flujo (densa sobre las descripciones, filtro por kind).

| Buscador | hit@1 | hit@5 | hit@10 | MRR@10 | hit@1 contra la base (pareado) |
|---|---|---|---|---|---|
| Densa: Qwen3 sobre las descripciones (**el flujo**) | 0,530 | 0,790 | 0,863 | 0,641 | |
| Léxica: BM25 sobre las descripciones | 0,517 | 0,801 | 0,869 | 0,631 | −0,013 [−0,063; +0,032] |
| Por foto: SigLIP 2, la consulta en una frase contra la foto del producto (sin descripciones) | 0,508 | 0,807 | 0,889 | 0,632 | −0,022 [−0,077; +0,032] |
| Por foto: CLIP ViT-B/32 | 0,357 | 0,710 | 0,849 | 0,512 | −0,173 [−0,221; −0,130] |
| Densa + léxica | 0,581 | 0,807 | 0,876 | 0,674 | +0,051 [0,013; 0,088] |
| Densa + foto | 0,585 | 0,829 | 0,889 | 0,689 | +0,055 [0,022; 0,090] |
| Léxica + foto (sin embedder de texto) | 0,597 | 0,832 | 0,882 | 0,693 | +0,067 [0,024; 0,114] |
| **Densa + léxica + foto** | **0,605** | **0,825** | **0,883** | **0,701** | **+0,075 [0,041; 0,111]** |
| Lo mismo, fusión por puestos (RRF) | 0,590 | 0,829 | 0,887 | 0,693 | +0,060 [0,027; 0,098] |
| Densa + léxica + foto, con filtro por tipo en vez de kind | 0,616 | 0,847 | 0,920 | 0,715 | +0,086 [0,050; 0,123] |

Lecturas: (a) los tres buscadores solos rinden parecido: ni el embedder neuronal le gana a contar
palabras, ni describir cada producto con un VLM le gana a embeber su foto con SigLIP 2 (así es con
dos de los tres redactores de consultas; con el tercero la densa sola queda arriba, 0,567 contra
0,501 y 0,477); (b) pero se equivocan en cosas distintas, y juntos suman 7,5 puntos de hit@1 y
3,5 de hit@5, con intervalos que no tocan el cero, y la mejora se repite con los tres redactores
(+0,075, +0,075 y +0,046 de hit@1); (c) es la respuesta con datos a "¿por qué no CLIP?": con CLIP
no alcanza, con SigLIP 2 sí, y lo mejor es usar las dos rutas de la clase a la vez (la imagen
pasada a texto y la imagen embebida).

**Qué líneas de la descripción hacen el trabajo** (`ablaciones/lineas.yaml`; la pregunta de
splitting que este problema sí tiene). Sacando líneas de documentos y consultas: sin Colors, hit@1
baja de 0,530 a 0,474 (−0,057 [−0,082; −0,030]); sin Shape, a 0,499 (−0,031 [−0,057; −0,006]); sin
Feel ni Goes with no cambia (0,534); y con solo las cuatro líneas de lo que se ve (Type,
Materials, Colors, Shape), tampoco (0,537). Lo que encuentra el producto es lo que se ve. Las
otras cuatro (Use, Style, Feel, Goes with) están para el pedido abierto, que este banco no mide:
no es evidencia para sacarlas, es una hipótesis para probar de punta a punta.

**Un reranker de texto local** (`ablaciones/reranking-local.yaml`; quedaba configurado y sin
correr). Qwen3-Reranker-0.6B, un cross-encoder de la familia del embedder, reordena el top-10
leyendo la consulta y cada descripción juntas: hit@1 baja de 0,535 a 0,474 (−0,062 [−0,111;
−0,013]). Igual que el MiniLM de la demo de la clase (0,419). Un reranker de texto relee lo mismo
que ya usó la búsqueda y empeora; el que suma (+0,151) es el VLM que mira las fotos. Tardó 7,6
horas en esta CPU (50 s por consulta): tampoco sirve por latencia.

**¿Error, o el mismo mueble en otro color?** (`ablaciones/embedders.yaml`). El 69% de las
consultas busca un producto que tiene variantes del mismo modelo en el catálogo. Contando como
acierto el producto anotado o cualquier variante de su modelo, hit@1 sube de 0,530 a 0,623: una
de cada cinco veces que el primero "falla" es el mismo mueble en otra medida u otro color. Hay
tres niveles de correcto: el producto exacto primero, 0,53; el mismo modelo, 0,62; uno que un
juez considera que sirve, 0,78. La comparación entre embedders no cambia (por familia tampoco se
distinguen Qwen3, BM25 y SigLIP 2; BGE sigue peor): el banco subestima el nivel, no el orden.

**De punta a punta, pago** (los 11 ambientes vacíos, el juez de listas en los dos órdenes;
`docs/EXPERIMENTOS.md`, T8):

| Comparación | Resultado | Costo |
|---|---|---|
| Versión 1 (densa) contra versión 2 (híbrida), 11 ambientes | La híbrida gana 5, empata 6, no pierde ninguno (15 votos a 5; p = 0,06); productos útiles 0,74 contra 0,68 | US$3,0 |
| Con búsqueda contra sin búsqueda (5 candidatos al azar del mismo kind), 7 ambientes | 7 a 0, los 14 votos (p = 0,016); productos útiles 0,82 contra 0,26 | US$1,4 |

El segundo es además el control del instrumento: cuando la diferencia es grande, el juez la ve
siempre, y eso le da sentido a los empates del primero.

### Experimentos que faltan (para decidir)

| Qué | Para qué | Costo |
|---|---|---|
| La misma configuración dos veces (A/A) | Cuántos ambientes da vuelta el ruido solo | US$2,5 de Anthropic (el tope de US$30 está agotado: 29,41) |
| Las métricas del generador sobre las listas de la versión 2 | Hoy están medidas sobre las de la versión 1 | US$1,1 de Anthropic |
| El mejor embedding de OpenAI contra Qwen3 | Si un embedder por API cambia algo | centavos; listo (`ablaciones/embedder-openai.yaml`), pero la clave de OpenAI del `.env` está vencida |
| Escena escrita por el LLM contra plantilla, 8–10 ambientes | El experimento de imagen que sí vale | ~US$1,5 de fal y US$0,4 de Anthropic |
| Voto a ciegas del equipo sobre los pares de listas | Validar al juez contra personas | gratis, 15 minutos |

## 5. Métricas: ranking y qué cambia

### Imprescindibles

1. **hit@k con IC por ambiente y el azar al lado**, con **hit@5 de titular** (es lo que ve el
   que elige) y las **diferencias pareadas** entre métodos (faltaban: los IC de cada método por
   separado llevaban a leer como mejora lo que era ruido, y al revés).
2. **El juez de a pares sobre ambientes vacíos**: lo único medido sobre la tarea real.
3. **La elección con el VLM y la curva de candidatos**, dichas como técnica aislada.
4. **Fidelidad de producto y ambiente preservado, sobre todas las imágenes** (en las 11
   imágenes de la configuración final: 31 de 75 productos reconocidos, coseno 0,50; el ambiente
   se conserva en 7 de 11).
5. **Los tres redactores y el IC**: lo que pidió la clase ("promedio de ejecuciones, desvío").
6. **Costo por pedido, con rango**: US$0,06 el plan y US$0,14 la elección (de 0,05 a 0,43), más
   US$0,08 por intento de imagen.
7. **Las cuatro de la clase, bien rotuladas** (context precision, context recall, faithfulness,
   answer relevance).

### Útiles

Relevancia graduada (reponderada: sirve el primero 0,78, alguno del top-3 0,87); hit@1 por
categoría con su n; recall por producto anotado (texto contra imagen); MRR@10 como resumen.

### Prescindibles o engañosas (no se borran: se rotulan)

| Métrica | Problema |
|---|---|
| Answer relevance, como estaba | El prompt del juez traía de ejemplo "un living nórdico y cálido", que era el pedido evaluado: el juez lo copiaba. Y la vara (0,37, pedidos sin relación) era de paja: contra los pedidos generados para *otras* respuestas daba 0,66 contra 0,69–0,73. |
| Faithfulness, como estaba | El juez leía la descripción completa del producto, que el generador nunca ve. Medía si el porqué coincide con la ficha, no si se infiere del contexto. Tres respuestas, de la configuración vieja. |
| "NDCG@3 graduado" | No es el NDCG de la clase (usa como ideal las mismas notas ordenadas). |
| NDCG@10 y context precision@10 | Correctas, pero con uno o dos relevantes por consulta repiten al MRR (correlación > 0,99). Se muestran por la clase, en una línea. |
| Context recall@3 | Bien calculada, pero es por ambiente y comparte tabla con métricas por consulta. Aclararlo. |
| Pedido ↔ imagen (SigLIP) | Sus contrastes son de paja ("una cocina blanca"). |
| "Aceptable" del juez de listas | Satura (0,97–1,00). |
| AUROC del coseno llamado "negative rejection" | Se calcula solo entre consultas con respuesta. El real (con respuesta contra sin) da 0,72. |
| Separabilidad del espacio (UMAP) | No predice la tarea. Sirve como figura, no como métrica. |

### Las métricas del generador, rehechas

Jueces nuevos (`juez_fidelidad_v2`, `juez_pedidos_v2`): sin el ejemplo que filtraba el pedido,
y el juez de faithfulness recibe exactamente lo que vio el generador (la foto del ambiente y, de
cada producto elegido, su foto y la línea con su kind, su tipo y su medida). Corridos sobre las
**11 listas de la configuración final** (IKEA + ABO), con Opus por la API: US$1,10.

| Métrica | Valor | Cómo leerlo |
|---|---|---|
| Faithfulness del porqué | **0,82** (289 de 351 afirmaciones; por lista, de 0,70 a 0,93) | Antes decía 0,89–0,96, con el juez leyendo una ficha que el generador no ve. Lo que no se sostiene es casi siempre lo mismo: **la especie de la madera** ("fresno", "abedul", "haya"), que el generador afirma sin que su contexto lo diga, y medidas que el catálogo no tiene. |
| Answer relevance | **0,69** | Vara cruzada (el mismo pedido contra los pedidos que el juez reconstruyó para *otras* listas): 0,55. La lista propia supera a las ajenas en 11 de 11. Piso (pedidos sin relación): 0,40. |

Accionable: pasarle al que elige la línea de materiales de cada candidato (hoy solo ve el tipo y
la medida, y adivina la madera por la foto), o pedirle que no afirme lo que no ve.

### Trampas que hay que decir en voz alta

- **El banco de retrieval es "encontrar un producto conocido"**: quien escribió la consulta
  estaba viendo el producto, y consultas y descripciones las escribió el mismo modelo con el
  mismo molde. Por eso contar palabras rinde casi como un embedder. En el flujo real el plan
  imagina un producto ideal: sus consultas quedan más lejos del catálogo (coseno del primero
  0,80–0,82 contra 0,875) y el que elige toma el primero del coseno solo el 45% de las veces.
- **No hay conjunto apartado**: todo se eligió y se reporta sobre los mismos 64 ambientes.
- **El ground truth es permisivo e incompleto**: con asignación uno a uno hit@1 baja de 0,536 a
  0,519; y el juez encuentra productos que sirven y no están anotados.
- **Lo que no se midió**: cuánto cambia la lista si se corre dos veces el mismo pedido.

## 6. Ejercicio 4: versión 1 y versión 2

El enunciado pide el problema de la versión anterior, el cambio, su justificación, la
configuración antes y después y la comparación; la profesora lo llamó "una versión 2 de su
arquitectura", y puso de ejemplo "agregar más técnicas de Advanced RAG y ver cómo soluciona
algún problema que tienen". La versión 1 es el sistema como estaba hasta el 11/11.

**Decidido (2026-11-12): la versión 2 es la búsqueda híbrida.** Sale de una limitación medida
de la versión 1, es una técnica de Advanced RAG, es una línea de configuración y está medida con
las mismas consultas y los mismos ambientes.

| | Versión 1 | Versión 2 |
|---|---|---|
| Configuración | `rag.hybrid: []` | `rag.hybrid: [bm25, siglip2]` |
| Qué busca | el coseno del embedder (Qwen3) sobre las descripciones | lo mismo, fusionado con la búsqueda léxica (BM25) y con la foto del producto (SigLIP 2) |
| La limitación de la versión 1 | El índice lee una descripción pero no ve el producto, y no aprovecha las palabras exactas. Entre productos casi iguales el primero acierta el 53% y en 1 de cada 5 piezas el correcto no llega a los 5 candidatos | |
| hit@1 / hit@5 / MRR@10 (ground truth, 549 consultas) | 0,530 / 0,790 / 0,641 | 0,605 / 0,825 / 0,701 |
| Diferencia pareada de hit@1 | | +0,075 [0,041; 0,111]; con los otros dos redactores, +0,075 y +0,046 |
| hit@1 con tres redactores (media ± desvío) | 0,539 ± 0,025 | 0,604 ± 0,009 |
| De punta a punta, 11 ambientes (juez en los dos órdenes) | gana 0 | gana 5, empata 6 (15 votos a 5) |
| Productos útiles según el juez | 0,68 | 0,74 |
| Costo por pedido | US$0,28 | igual (BM25 y SigLIP 2 corren locales) |

Lo que hay que decir con honestidad: de punta a punta son 11 ambientes y 5 a 0 da p = 0,06; en
6 el juez no se decide. La mejora es clara en el ground truth y "no peor, probablemente mejor"
en la tarea real.

Las otras maneras de contarlo, descartadas como Ejercicio 4:

| Opción | Por qué no |
|---|---|
| Por calendario: de 3 a 5 candidatos y de IKEA a IKEA + ABO | Son dos cambios juntos, y quedan mejor donde están: como experimentos del Ejercicio 2 |
| Con y sin el que elige (0,535 → 0,687) | `choose` existió desde el primer día: es una ablación, no una iteración |
| El cambio de arquitectura (de buscar por imagen a RAG por texto) | La primera nunca corrió de punta a punta. Va en la lámina de desafíos |

## 7. Las preguntas difíciles del oral

1. **¿Hacía falta RAG si el catálogo entra en el contexto?** En texto entra: las 1.502 fichas
   son unos 200 mil tokens (814 mil caracteres). Mandarlas enteras costaría unos US$0,80 de
   entrada por pedido con Opus, contra US$0,14 de la elección de hoy, que además mira las fotos
   de los candidatos; con las fotos de todo el catálogo ya no entra. RAG se justifica por costo,
   por escala (ABO completo son 147 mil productos), por actualización (un alta es un insert) y
   porque el modelo de imagen necesita igual las fotos de los elegidos. No lo medimos de punta
   a punta.
2. **¿Dónde está la G?** `choose` es el generador: elige y explica, con el contexto recuperado.
   La imagen es una segunda generación aumentada con las fotos recuperadas.
3. **El 0,69, ¿es del sistema que corre?** No: es el techo de una técnica aislada. El flujo
   tiene 0,667 en el sustituto (elegir entre 5) y el juez sobre ambientes reales.
4. **Consultas y documentos los escribió el mismo modelo: ¿miden vocabulario?** En parte sí
   (BM25 rinde casi igual que el embedder). Es la limitación principal del banco de prueba.
5. **Su experimento dice que el filtro por kind resta. ¿Por qué lo usan?** Porque garantiza el
   tipo de pieza (evita 11% de candidatos de otro kind) y cuesta 2 a 3 puntos de recall.
6. **¿El filtro de medidas hace algo?** Sin evidencia. Solo el 34% de IKEA tiene medidas.
7. **¿Qué es lo que hace el plan: query rewriting?** Query expansion con respuesta hipotética
   (HyDE) más descomposición del pedido en sub-consultas más filtros de metadata.
8. **¿Qué pasa si el catálogo no tiene lo pedido?** Hoy sustituye por lo más parecido sin
   avisar (0 piezas rechazadas en 187). Es una limitación.
9. **¿Cuántas imágenes evaluaron y cuántos productos se reconocen?** Las 11 de la configuración
   final: 31 de 75 productos reconocidos como el exacto (41%) y el ambiente conservado en 7 de 11.
10. **¿Por qué cambiaron la arquitectura aprobada?** La propuesta era generar una imagen,
    recortar los muebles y buscarlos por parecido visual. Construimos y medimos su buscador
    (0,43 de recall por producto) y el de texto dio 0,55 con una generación menos por pedido.
    Nunca corrió de punta a punta.
11. **¿Por qué una base vectorial para 1.500 vectores?** Por los filtros de metadata en la misma
    consulta y la persistencia; a este tamaño da el mismo resultado que la búsqueda exacta
    (verificado en 864 de 864), y es la pieza que escala.
12. **¿Por qué Opus y no un modelo más barato?** No está medido en la versión actual. Hay un
    dato histórico (un rerank con un modelo chico dio 0,768 contra 0,803 a 1/26 del costo) que
    se sacó del registro; rehacerlo con Sonnet cuesta unos US$5.

## 8. Lo que queda por decidir

| Decisión | Opciones | Costo |
|---|---|---|
| El filtro de medidas | Apagarlo (`furnish.size_filter: false`), o dejarlo y validarlo | Validarlo: US$2 |
| Rehacer el experimento de la escena (LLM contra plantilla) | 8–10 ambientes, o contarlo como decisión de costo | ~US$1,5 de fal y US$0,4 de Anthropic |
| El tope de Anthropic | Está agotado (US$29,41 de 30). Cualquier corrida paga nueva pide subirlo | — |
| La clave de OpenAI | La del `.env` está vencida: con una nueva, la comparación de embeddings son centavos | — |
| Validar al juez contra personas | Los tres votan a ciegas los 11 pares de listas | Gratis, 15 minutos |
| El dato del reranker con un modelo chico | Citarlo como histórico, rehacerlo con Sonnet, o dejarlo afuera | Sonnet: ~US$5 |
| Las presentaciones | No se tocaron esta noche: tienen las frases que esta revisión corrige. La lista de cambios está en la sección 9; se aplican a la que quede elegida | — |
| El historial de git | 150 de los 152 commits ya pusheados llevan una línea de co-autoría de Claude. Los de esta revisión no. Sacarla de los viejos pide reescribir el historial y un push forzado | — |
| Las menciones a "YouSeeYouBuy" | `docs/EXPERIMENTOS.md` (ya en el repo desde ayer) nombra dos veces ese otro proyecto sin explicarlo. Explicarlo en una línea (de dónde viene el núcleo de búsqueda) o sacarlas | — |
| El índice de ChromaDB en git | `chroma.sqlite3` cambia con solo abrir el índice, así que cada corrida ensucia el repo. Se regenera en segundos desde los vectores en caché: se puede sacar de git | — |

Los gastos, por uso y por día, están en `datos/resultados/gastos.md` (se genera con `uv run
amoblai gastos --md`).

## 9. Cambios para las presentaciones

Las cinco presentaciones no se tocaron (falta elegir cuál queda). Lo que hay que cambiar en la
que quede, con los números de lámina de `docs/presentacion/` como referencia:

| Dónde | Qué dice | Qué tiene que decir |
|---|---|---|
| Fase 5 del recorrido, y la lámina "Base vectorial y query rewriting" (30) | "el plan es nuestro query rewriting"; la consulta completa contra solo Type y solo el kind, "que sería no reescribir" | El plan hace query expansion con respuesta hipotética (HyDE) y descompone el pedido. La comparación es la ficha contra la frase natural: 0,530 contra 0,324 (+0,21). |
| Embedder (26) | "Gana Qwen3... gana más claro en las búsquedas difíciles" | Qwen3 y contar palabras no se distinguen (+0,026 [−0,025; +0,077]); solo le gana a BGE. Se queda por robustez a la paráfrasis. |
| Filtros duros (27) | "Filtrar siempre... la diferencia con el tipo está dentro del intervalo" | El filtro no suma en el banco de prueba y el de kind cuesta 2 puntos de hit@5. Se usa porque evita 11% de candidatos de otro kind en los pedidos reales. El de medidas no tiene evidencia. |
| "Jueces validados" (22) | Los tres jueces, validados | Validado contra el ground truth, uno (el de relevancia, para la nota 2). El de listas, solo por acuerdo entre órdenes. |
| La imagen: del cuarto reimaginado al cuarto del cliente (36) | La edición estricta ganó | Es una decisión de costo y simplicidad; una imagen por variante no decide. |
| Qué catálogo (34) y conclusiones (41) | "8 a 2", "6 a 0" | Sumar p = 0,11 y que los pedidos de otros estilos se escribieron sabiendo qué le falta a IKEA. |
| "El camino: de 0,08 a 0,69" (38) | Seis barras que terminan en el rerank | El camino de la sección 4: de 0,11 a 0,53 (el flujo), y 0,60 con la híbrida. El 0,69 va aparte, como techo de una técnica aislada. |
| La v0 (fase 3 y desafíos) | "no sirve con un ambiente vacío: no hay nada que recortar" | Fue la propuesta aprobada; su diseño generaba primero una imagen. Construimos y medimos su buscador (0,43 de recall por producto contra 0,55 por texto) y cambiamos. Nunca corrió entera. |
| Ejercicio 4 (37) | Una tabla de 8 filas en 30 segundos | Versión 1, versión 2, configuración antes y después y los resultados de las dos: 3 láminas. |
| Métricas del generador (22) | Faithfulness 0,89–0,96; answer relevance 0,69–0,73 contra 0,37 | 0,82 (289 de 351) y 0,69 contra 0,55 de la vara cruzada, sobre las 11 listas finales. |
| La imagen (23) | 3 de 4 productos reconocidos | 31 de 75 (41%) en las 11 imágenes de la configuración final; el ambiente se conserva en 7 de 11. |
| "Ocho de las once fases las decidió un experimento" | — | Sacarla: suena a volumen, y tres de esos experimentos no sostienen su decisión. |
| Falta | — | Una lámina de desafíos (el cambio de arquitectura) y la respuesta a "¿hacía falta RAG?". |

## Informes completos

Los cinco informes, con la evidencia (archivo y línea) y los scripts de recálculo, están en
`docs/revision/` (carpeta local, no va a git): `desde_cero.md`, `arquitectura.md`,
`metricas.md`, `experimentos.md` y `evaluador.md`.

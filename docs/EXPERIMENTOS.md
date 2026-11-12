# Registro de experimentos

Registro continuo: cada experimento con su configuración, los resultados y lo que se aprendió.

- **v1 (actual): RAG por texto** (`src/amoblai/`). Evaluaciones en `datos/resultados/evaluacion/`, corridas
  del flujo en `datos/resultados/amoblar/`, reporte en `datos/resultados/reporte/` (`uv run amoblai reporte`).
- **v0 (deprecada): retrieval por imagen.** Sus corridas están en `datos/resultados/v0_imagen/` y su
  código en `deprecated/`. Se conserva abajo porque es la línea de base de la v1 (mismo ground
  truth) y la historia de cómo se llegó al diseño actual.

## Ranking de los experimentos (revisión del 2026-11-12)

De la revisión crítica (`docs/REVISION.md`, sección 4), sin borrar ninguno. Las lecturas que esa
revisión corrigió están anotadas en cada sección como *Corrección (2026-11-12)*.

| Grupo | Experimentos | Por qué |
|---|---|---|
| **Sí o sí van** | Qué se indexa (T1, T6a) · cómo se escribe la consulta (T6b) · búsqueda léxica, por foto e híbrida (T6c) · versión 1 contra versión 2 y con búsqueda contra sin búsqueda, de punta a punta (T8) · las imágenes de la configuración final (T9) · elegir con un VLM y cuántos candidatos (T1b, T1e) · texto contra imagen (T1 contra la v0) · qué catálogo, de punta a punta (T3b) · tres redactores (T1d) · las métricas del generador (T7) | Responden una duda real del pipeline, cambian (o sostienen) una decisión y están medidos con diferencias pareadas |
| **Normalitos** | Embedder (T1: solo se sostiene Qwen3 sobre BGE) · filtros (T1: no suman en este banco; se usan por otra razón) · dimensión, splitting y cross-encoder MiniLM (T1d) · ChromaDB contra exacta (T1b) · reranker de texto local (T6e) · qué líneas pesan (T6d) · el acierto por familia (T6g) · catálogo ampliado y revisado (T1c, T1e) · ABO como distractores (T3b) · IKEA contra ABO en 5 ambientes (T3) · relevancia graduada (T1d) · el flujo sin juez (T6f) · la prueba del flujo (T2) · la grilla de la v0 (R1–R3) | Correctos, pero de trámite (los pregunta la cátedra y la respuesta era previsible), controles, o mediciones que no comparan nada |
| **No sirven tal como están** | "Query rewriting" contra solo Type o solo el kind (T1b: reemplazado por T6b) · la escena sin LLM (una imagen por variante; no está en este registro) · la réplica con cajas (T5, T5b: un cuarto, 3 imágenes por variante, fuera del RAG) · los experimentos de imagen diseñados y sin correr (T4) · la imagen de un caso y las métricas del generador versión 1 como resultados (T1d) | Rival de paja, n = 1 con variables confundidas, sin poder para lo que concluyen, o el mejor caso de pocos |

# v1: RAG por texto

## Metodología del retrieval

- **Datos**: los mismos 65 ambientes de IKEA (livings y comedores con productos anotados del
  catálogo) que la v0. El catálogo son los 268 productos del alcance (275 menos 7 cuya foto no
  los muestra, ver T1), cada uno con su descripción de ocho líneas (`datos/catalogo/descripciones.jsonl`).
- **Consultas** (`datos/evaluacion_ikea/consultas.json`, prompt `consultas_ambiente_v1`): subagentes
  de Claude Code miraron cada foto, sin ver el catálogo ni las anotaciones, y escribieron una
  consulta por mueble del alcance que se ve (228 en total), en las mismas ocho líneas y con su
  kind, como lo hace el paso `plan`. Es el equivalente en texto del recorte de la v0: mide el
  retrieval aislado, con consultas fijas para todos los métodos.
- **Relevantes de una consulta**: los SKUs anotados en ese ambiente de la misma categoría del TP
  (sofá, sillón, silla, mesa, alfombra) que su kind; 198 consultas tienen al menos uno en el
  catálogo. Es la misma definición permisiva que en la v0 (las anotaciones no dicen dónde está
  cada producto).
- **Métricas**: hit@k (1, 3, 5, 10), MRR@10, recall por ítem anotado, baseline aleatorio sobre
  lo que deja pasar el filtro, IC 95% por bootstrap de ambientes (1000 remuestreos).
- **Métodos**: embedder (hashing de palabras, BGE-base, Qwen3-Embedding-0.6B; locales) × texto
  del producto (nuestras ocho líneas, el texto del vendedor, el nombre comercial adelante) ×
  filtro (kind, tipo grueso, ninguno).
- Comando: `uv run amoblai evaluar --ablacion datos/configs/ablaciones/<ablación>.yaml` (la de
  retrieval es local y gratis; los vectores quedan en caché). Cada YAML declara sus métodos.
- Base vectorial: ChromaDB (HNSW, coseno, los filtros como `where`) salvo donde se compara con
  la búsqueda exacta.

## T1: ablación del retrieval por texto

Corrida `datos/resultados/evaluacion/20261021-161057_ablacion-retrieval` (ChromaDB, CPU), 198
consultas (`ablaciones/retrieval.yaml`). Con búsqueda exacta (`20261021-141030_ablacion-texto-268`)
dio los mismos números.
*Corrección (2026-11-12):* eso vale para las filas con nuestras descripciones. Las tres filas de texto del
vendedor con filtro por kind de la tabla (0,434; 0,667; 0,677 de hit@10) son de la corrida exacta,
y con ChromaDB cambian hasta 63 de 228 top-10: son textos repetidos entre variantes del mismo
modelo, que empatan.

| Embedder | Texto | Filtro | hit@1 [IC 95%] | hit@3 | hit@10 | MRR@10 | recall ítem@10 |
|---|---|---|---|---|---|---|---|
| hashing | vendedor | ninguno | 0,146 [0,10–0,21] | 0,222 | 0,434 | 0,213 | 0,417 |
| hashing | vendedor | kind | 0,202 [0,14–0,27] | 0,343 | 0,687 | 0,324 | 0,655 |
| hashing | descripción | ninguno | 0,586 [0,51–0,66] | 0,813 | 0,929 | 0,712 | 0,883 |
| hashing | descripción | tipo | 0,586 [0,51–0,66] | 0,828 | 0,934 | 0,716 | 0,883 |
| hashing | descripción | kind | 0,571 [0,50–0,65] | 0,778 | 0,894 | 0,688 | 0,845 |
| BGE | vendedor | kind | 0,242 [0,17–0,31] | 0,424 | 0,667 | 0,359 | 0,636 |
| BGE | descripción | tipo | 0,520 [0,45–0,59] | 0,748 | 0,919 | 0,649 | 0,898 |
| BGE | descripción | kind | 0,515 [0,45–0,59] | 0,722 | 0,894 | 0,634 | 0,854 |
| BGE | nombre + descripción | kind | 0,485 [0,42–0,55] | 0,692 | 0,849 | 0,600 | 0,816 |
| Qwen3 | vendedor | kind | 0,212 [0,16–0,27] | 0,409 | 0,677 | 0,340 | 0,646 |
| **Qwen3** | **descripción** | **tipo** | **0,636 [0,58–0,70]** | **0,813** | 0,914 | **0,737** | 0,893 |
| Qwen3 | descripción | kind | 0,616 [0,55–0,68] | 0,773 | 0,879 | 0,709 | 0,835 |
| Qwen3 | nombre + descripción | kind | 0,505 [0,44–0,58] | 0,742 | 0,838 | 0,623 | 0,801 |

(Tabla completa con todas las combinaciones en `datos/resultados/reporte/README.md`.)
Azar con filtro por tipo: hit@1 0,020, hit@10 0,194, MRR@10 0,058.

**Camino incremental** (para la presentación, `datos/resultados/reporte/camino_texto.png`):
T0 naive (hashing, texto del vendedor, sin filtro) 0,146 → T1 + nuestras descripciones 0,586 →
T2 + filtro por tipo 0,586 → T3 Qwen3-Embedding **0,636** (hit@1).

**Lecturas**:
- **Lo que más pesa son las descripciones propias**: con cualquier embedder, hit@1 pasa de
  0,15-0,24 (texto del vendedor) a 0,52-0,64. La frase de marketing de IKEA no describe el
  mueble; las ocho líneas sí, y en el mismo formato que la consulta.
- **El nombre comercial adelante empeora** (0,62 → 0,51 con Qwen3): agrega tokens que la consulta
  no tiene. Coincide con lo que midió YouSeeYouBuy.
- **Los filtros ayudan mucho con el texto del vendedor y casi nada con nuestras descripciones**,
  que ya dicen qué es cada cosa en la línea Type. El filtro por **kind** resta un poco frente al
  filtro por **tipo** (0,616 vs. 0,636 con Qwen3; los IC se solapan): cuando la consulta y el
  producto discrepan en el kind fino ("side table" vs. "coffee table"), el filtro deja afuera al
  producto correcto. El flujo usa el kind (lo decide el plan); es un candidato para iterar.
  *Corrección (2026-11-12):* con la diferencia pareada (mismas consultas, catálogo final), kind contra tipo da
  −0,005 de hit@1 (no se distingue), pero −0,020 [−0,037; −0,004] de hit@5 y −0,022 [−0,041;
  −0,002] de hit@10: resta donde importa, que es entre los 5 candidatos. Y tipo contra ningún
  filtro da 0,000. El filtro por kind se queda en el flujo por otra razón, que este banco de
  prueba no mide: en los 11 ambientes vacíos, con filtro por tipo el 11% de los candidatos sería
  de otro kind que el pedido (un sillón pedido, una silla de comedor ofrecida).
- **Qwen3-Embedding es el mejor embedder**; BGE queda por debajo del hashing de palabras en hit@1.
  *Corrección (2026-11-12):* "el mejor" solo se sostiene contra BGE (+0,057 [0,017; 0,095], pareado, catálogo
  final). Contra el hashing de palabras la diferencia es +0,026 [−0,025; +0,077] en hit@1, 0,812
  contra 0,809 en hit@5 e idéntico hit@10: no se distinguen. Contra BM25, igual (T6). El embedder
  casi no importa en este banco de prueba; Qwen3 queda por robustez a la paráfrasis, sin
  evidencia medida.
  Ojo con el hashing: consultas y descripciones las escribió la misma familia de modelos con el
  mismo formato y vocabulario, lo que favorece el solapamiento de palabras. En el flujo real
  pasa lo mismo (el plan también es Claude), así que no es un sesgo de la evaluación sola.
- **Por categoría** (Qwen3, filtro por tipo, hit@1): silla 0,86 (44 consultas), sillón 0,72 (18),
  mesa 0,69 (67), sofá 0,63 (24), alfombra 0,31 (45). Las alfombras son lo más difícil: hay 89
  en el catálogo, muchas parecidas, y en las fotos quedan tapadas por los muebles.

**El catálogo de 275 a 268.** La primera corrida
(`20261021-133226_ablacion-texto`) usó los 275 productos: el mejor método dio 0,618 [0,56–0,68]
sobre 207 consultas, con las mismas conclusiones. Después, la prueba del flujo (T2) mostró que
varios SKUs comparten la foto con otra medida del mismo modelo, y en 7 la forma no coincide (una
mesa de 118 x 50 cm con la foto de la cuadrada de 70 x 70; una alfombra de 170 x 240 con la foto
del pasillo): el modelo de imagen dibujaría otro producto que el de la lista de compra. Se
dejaron afuera (`datos/catalogo/correcciones.yaml`, `excluir`), mirando la forma de cada foto; 9
consultas se quedaron sin su único relevante.

## T1b: base vectorial, query rewriting y reranking (Advanced RAG)

Sobre el mejor método (Qwen3, nuestras descripciones, filtro por tipo), cambiando una sola cosa
por fila. Corridas `20261021-161057_ablacion-retrieval` (gratis) y
`20261022-175001_ablacion-reranking` (`ablaciones/reranking.yaml`, paga). Gráfico:
`datos/resultados/reporte/avanzado.png`.

| | hit@1 [IC 95%] | hit@3 | hit@10 | MRR@10 [IC 95%] |
|---|---|---|---|---|
| ChromaDB (HNSW, coseno) | 0,636 [0,58–0,70] | 0,813 | 0,914 | 0,737 [0,69–0,79] |
| búsqueda exacta (numpy) | 0,636 [0,58–0,70] | 0,813 | 0,914 | 0,737 [0,69–0,79] |
| consulta: solo la línea Type | 0,353 [0,28–0,43] | 0,636 | 0,843 | 0,510 [0,45–0,57] |
| consulta: solo el kind (sin reescribir) | 0,040 [0,01–0,07] | 0,091 | 0,237 | 0,082 [0,05–0,12] |
| **+ reranking con VLM (Claude Opus 5.5, top-10)** | **0,803 [0,75–0,87]** | **0,889** | 0,914 | **0,847 [0,80–0,90]** |

**Lecturas**:
- **ChromaDB y la búsqueda exacta dan el mismo ranking en las 228 consultas** (con 268
  productos, HNSW con `ef_search` 100 no pierde vecinos). La base vectorial no cambia la calidad;
  da los filtros por metadata en la misma consulta y escala.
- **El query rewriting es lo que más pesa del pre-retrieval**: con la consulta en las ocho líneas
  del catálogo (lo que escribe el plan) hit@1 es 0,64; con solo la línea Type (una frase corta:
  "Type: armchair, lounge reading chair") cae a 0,35; con solo el nombre del mueble (sin
  reescribir) a 0,04, casi el azar (0,02). La consulta tiene que hablar como los documentos.
  *Corrección (2026-11-12):* esta comparación no mide reescribir contra no reescribir: buscar "rug" entre 89
  alfombras es azar por construcción. La comparación justa (la ficha contra la frase natural con
  que el redactor nombró la pieza) está en T6: +0,24 de hit@1. Y el nombre de la técnica, en los
  términos de la clase, es query expansion con respuesta hipotética (HyDE), no query rewriting.
- **El reranking con un VLM suma +0,17 de hit@1** (0,64 → 0,80; los IC no se solapan) y +0,11 de
  MRR: mirando las fotos, Opus ordena el top-10 mejor que el coseno. hit@10 no cambia (reordena
  dentro del top-10). Por categoría (hit@1): alfombra 0,31 → 0,60, mesa 0,69 → 0,87, silla
  0,86 → 0,95, sofá 0,63 → 0,75, sillón 0,72 → 0,78. El reranker ve la consulta y las fotos de
  los candidatos, no la foto del ambiente (ahí el producto está y la tarea sería encontrarlo).
  En el flujo, el reranking lo hace choose (el mismo Opus 5.5, con la foto del ambiente vacío,
  eligiendo la combinación): esta ablación mide la técnica aislada.
- **Costo del reranking**: 198 llamadas a Opus 5.5 (10 fotos + la consulta cada una; solo las
  consultas con relevantes, las otras no entran en las métricas), US$0,020 por llamada, US$4,02
  en total, 106 s con 8 en paralelo. Las respuestas quedan en caché (`datos/cache/rerank/`):
  volver a correr la ablación no cuesta nada.

## T1c: el catálogo ampliado (855 productos)

**Qué cambió.** El catálogo pasó de 268 a 855 productos: 587 de estanterías, muebles de
guardado, cómodas, escritorios, sillas de escritorio, pufs, banquetas, bancos, lámparas y
decoración (docs/catalogo.md), descritos por 15 subagentes con `describe_product_v3`. Para
evaluarlos, otros 6 subagentes escribieron con `consultas_ambiente_v2` 636 consultas de esas
categorías en los 64 ambientes que las tienen anotadas, sin ver el catálogo; se sumaron detrás de
las 228 de la v1, que no se tocaron. En lámparas y deco la relevancia va por kind (un almohadón
no responde a una búsqueda de florero; macetas con plantas y marcos con cuadros van juntos); en
muebles sigue siendo la categoría del TP.

**Corrida:** `20261022-213008_ablacion-retrieval` (la misma grilla, gratis). 864 consultas, 552
con respuesta (199 de la v1 y 353 de la v2).

| Método | hit@1 [IC 95%] | hit@10 | MRR@10 | v1 hit@1 | v2 hit@1 |
|---|---|---|---|---|---|
| hashing + texto del vendedor, sin filtro | 0,076 | 0,319 | 0,143 | 0,111 | 0,057 |
| hashing + descripciones, sin filtro | 0,493 | 0,870 | 0,616 | 0,578 | 0,445 |
| hashing + descripciones + filtro por tipo | 0,509 | 0,893 | 0,633 | 0,583 | 0,467 |
| **Qwen3 + descripciones + filtro por tipo** | **0,533** [0,49–0,57] | 0,895 | 0,651 | 0,633 | 0,476 |
| Qwen3 + descripciones + filtro por kind | 0,525 | 0,864 | 0,637 | 0,613 | 0,476 |
| BGE + descripciones + filtro por tipo | 0,476 | 0,871 | 0,599 | 0,518 | 0,453 |

- **Lo viejo casi no se mueve.** En las consultas de la v1, el mejor método da 0,633 (0,636 con
  268 productos): sumar 587 productos de otras categorías apenas toca los muebles, porque el
  filtro por tipo los deja afuera y, sin filtro, las descripciones ya los separan (0,633 también
  sin filtro). Hay una consulta más con respuesta (199): una silla de escritorio del ambiente
  ahora está en el catálogo.
- **Lo nuevo es más difícil:** 0,476. Por categoría (Qwen3, filtro por tipo): muebles de
  guardado 0,73, lámparas 0,59, estanterías 0,43, deco 0,35 (208 consultas). Deco y alfombras
  (0,31) comparten el problema: muchos productos parecidos y una anotación que no dice cuál de
  los del ambiente es cada uno.
- **Query rewriting** sigue siendo lo que más pesa: solo la línea Type 0,292, solo el kind 0,063.
- **ChromaDB = exacta**: mismo ranking en las 864 consultas con filtro por tipo (863 con kind).
- **Reranking:** sin correr sobre el catálogo ampliado. `evaluar --estimar`: 367 consultas sin
  caché (las 353 nuevas y las de la v1 cuyo top-10 cambió); al costo medido (US$0,020 cada una),
  unos US$7,5.

## T1d: las métricas de la clase 11 y lo que preguntan las profesoras (2026-10-23)

**Qué cambió.** Se sumaron las métricas de la clase de métricas y tres ablaciones que responden
las preguntas de la presentación del enunciado: "¿por qué esa dimensión de embedding?", "¿por qué
k=5 y no k=10?" y "¿cómo hiciste el splitting y por qué?". El ranking razonado de las métricas
está en `docs/METRICAS.md`.

**Corrida:** `20261023-173217_ablacion-retrieval` (la grilla de siempre más las variantes nuevas;
gratis, unas 2 h en CPU por los embeddings de las líneas sueltas).

- **Métricas nuevas sobre el mejor método** (Qwen3, filtro por tipo):
  - context precision@10 (la fórmula de RAGAS) 0,630 [0,60–0,66];
  - NDCG@10 0,652;
  - context recall por ambiente: @3 0,782, @10 0,928;
  - AUROC del coseno para "el primero está bien": 0,655.
  - Context precision y NDCG correlacionan 0,9999 y 0,998 con el MRR sobre las 32
    configuraciones: con 1 o 2 relevantes por consulta no agregan información.
- **K (cuántos candidatos):** hit@1 0,533, hit@3 0,728, hit@5 0,813, hit@10 0,895, hit@20 0,958,
  hit@50 0,995. El flujo le pasa 3 por pieza al LLM: una de cada cuatro piezas no tiene el
  correcto entre las opciones. Pasar a 5 suma 8 puntos por unos US$0,02 por corrida (cada foto de
  candidato son unos 375 tokens en el choose). Recomendado, no aplicado: cambia el costo y la
  comparación con las corridas que ya hay.
- **Dimensión (Matryoshka, Qwen3 truncado):** 32 → 0,427, 64 → 0,464, 128 → 0,507,
  256 → 0,516, 512 → 0,533, 1024 → 0,533. Con 512 alcanza (la mitad de memoria, igual hit@1);
  con 855 productos la memoria no pesa (3,4 MB a 1024), así que queda 1024.
- **Splitting:** un documento por producto 0,533; cada línea un chunk (el producto vale su mejor
  línea) 0,268; línea contra línea del mismo rótulo 0,511 [0,46–0,56]. Partir la descripción no
  ayuda: cada línea sola ("Colors: white") matchea con cualquier producto blanco, y la consulta
  necesita todas las líneas a la vez. La descripción entera (unas 70 palabras) entra de sobra en
  la ventana del embedder.
- **Reranking con un cross-encoder de texto gratis** (BERT de MS MARCO, como en la demo de la
  clase): empeora, de 0,533 a 0,417 de hit@1. Está entrenado para relevancia de pasajes en
  preguntas web, no para comparar atributos de muebles, y lee el mismo texto que ya usó el
  embedder. El reranker que sirve mira las fotos (Opus: 0,64 → 0,80 sobre el catálogo de 268).
  Qwen3-Reranker queda en `ablaciones/reranking-local.yaml`: es gratis, pero en esta CPU tarda
  unas 15 h.

- **Reproducibilidad:** las mismas consultas, escritas otras dos veces por subagentes
  independientes (`reproducibilidad-r2`, `reproducibilidad-r3`). Qwen3 con filtro por tipo da
  hit@1 0,533, 0,526 y 0,575 (0,544 ± 0,026) y MRR 0,655 ± 0,017. En las tres escrituras, Qwen3
  le gana a BGE (+0,02 a +0,09), a hashing (+0,02 a +0,04) y al filtro por kind (+0,01): el
  orden de la ablación se mantiene y los valores absolutos se mueven unos ±2,5 puntos.
  *Corrección (2026-11-12):* esos números son del catálogo de 855. Rehechas sobre el catálogo
  final (819; corridas `20261112-095138_reproducibilidad-r2` y `-r3`): Qwen3 con filtro por tipo
  0,547 ± 0,027 (MRR 0,657 ± 0,017); con filtro por kind, la búsqueda del flujo, 0,539 ± 0,025;
  hashing 0,516 ± 0,030; BGE 0,492 ± 0,016. Y la lectura "Qwen3 le gana a hashing en las tres"
  vale para el signo, no para la significancia: juntando las tres escrituras la diferencia es
  +0,03 con un intervalo que toca el cero.

**Métricas de otras etapas, sumadas el mismo día:**
- **Relevancia graduada del top-3** (juez): sobre 150 consultas el primer candidato sirve en el
  74,7%, y alguno del top-3 en el 84%. En las que no tienen producto anotado en el catálogo, el
  primero sirve en el 63%. El juez le da 2 al anotado en el 81% de los casos y a los demás en el
  5%.
- **Imagen** (prueba-alvear2): 4/4 productos detectados; el sillón y la mesa identificados como el
  producto exacto, el sofá 7.º de 37 y la alfombra 10.ª de 89; coseno medio 0,65. La vara de
  fotos reales IKEA da hit@1 0,444 y coseno 0,41 (545 recortes). SSIM fuera de los muebles 0,975;
  55% de los puntos SIFT reencontrados, sin desplazamiento.
  *Corrección (2026-11-12):* con la asignación actual de recortes esa imagen da 3 de 4 y coseno 0,68, y es la
  mejor de las 8 imágenes con métricas. Sobre las 8: 26 de 52 productos identificados y coseno
  medio 0,48. La vara de fotos reales usa otro procedimiento (valen todos los recortes), así que
  no es una comparación pareja.
- **RAGAS sobre el porqué:** faithfulness 0,89 a 0,96 (lo que no se sostiene son medidas que el
  catálogo no tiene); answer relevance 0,69 a 0,73, contra 0,37 de la vara.
- **Espacio:** el vecino más cercano es del mismo kind en el 89% de los productos con Qwen3 y en
  el 92% con BGE. BGE separa mejor los kinds y recupera peor: esta métrica no decide el embedder.

## T1e: el catálogo revisado, el reranking sobre el catálogo final y cuántos candidatos (2026-11-09/10)

**Revisión del catálogo.** 36 productos más afuera: la foto es de otro producto o de otra medida,
o no son de living ni comedor (botiquines, estantes sueltos, accesorios de cocina). Y 7 kinds
corregidos mirando la foto (`datos/catalogo/correcciones.yaml`). Quedan 819 productos, contra 855.
Corrida `20261109-235406_ablacion-catalogo-revisado`: Qwen3 con filtro por tipo, hit@1 de 0,533 a
0,535. No cambia el retrieval: cambia que la lista y la imagen muestren el producto que dicen.
Se pierden 3 búsquedas con respuesta (549 contra 552), las de productos excluidos.
**Decisión:** el catálogo revisado.

**Reranking con el VLM sobre el catálogo final** (`20261109-235522_ablacion-reranking`, US$7,3
por 364 llamadas nuevas). Opus ordena el top-10 mirando las fotos:

| | hit@1 | hit@10 | MRR@10 |
|---|---|---|---|
| Qwen3, filtro por tipo | 0,535 | 0,892 | 0,654 |
| + rerank con Opus | **0,687** | 0,892 | **0,760** |

Sube menos que sobre el catálogo original (de 0,636 a 0,803), porque el catálogo final tiene
más productos parecidos y las consultas nuevas son de deco.

**Cuántos candidatos ve el VLM** (`datos/resultados/evaluacion_candidatos/curva_k.json`, gratis:
sale del mismo reranking). Si el VLM ordena el top-10, la pieza que elegiría entre los primeros k
es la mejor ordenada de esas k. Se supone que el orden del VLM no depende de qué otros candidatos
ve.

| k | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 |
|---|---|---|---|---|---|---|---|---|
| acierto de la elección | 0,536 | 0,618 | 0,637 | 0,656 | **0,667** | 0,679 | 0,689 | 0,687 |
| techo (hit@k) | 0,536 | 0,674 | 0,732 | 0,774 | 0,812 | 0,842 | 0,876 | 0,893 |

De 3 a 5 candidatos la elección sube 3 puntos (de 0,637 a 0,667). A partir de 8 se aplana. La distancia al techo crece,
porque entre muchos parecidos el VLM no siempre reconoce al correcto. **Decisión:** `furnish.candidates: 5`
(antes 3). Con 9 piezas son 45 fotos en la llamada de choose, debajo del límite de 100.

Ojo: es un proxy. El rerank no ve el ambiente ni el pedido completo, el choose sí.

## T1f: un catálogo alternativo, Amazon Berkeley Objects (2026-11-10)

**Por qué.** El catálogo IKEA tiene fotos de 500 px y los asientos sin medidas, y es de 2013. ABO
(Collins et al., CVPR 2022; CC BY-NC 4.0) tiene listados reales de Amazon de 2019-2020, con el
texto del vendedor, medidas en el 90% (de los 683 descriptos) y fotos de hasta 2000 px.

**Cómo** (`amoblai catalogo-abo`, `src/amoblai/catalog/abo.py`):
- De los 147.702 listados, los de EE. UU. en inglés de los tipos que tiene el catálogo IKEA.
- Un producto por modelo (las variantes de color o medida cuentan como el mismo), con foto de al
  menos 800 px.
- Un tope por kind, para tener un tamaño parecido al de IKEA. Quedan 781.
- Fuera las fotos compartidas por 3 o más productos: son "Image Coming Soon" o muestras de tela.
  Quedan 759.

Descripciones: Claude Opus 5.5 por la API (`describe_api.py`), con el mismo formato de 8 líneas, las
mismas reglas y la misma validación que las de IKEA. Van 10 productos por llamada, a 512 px (como
las fotos de IKEA) y con effort low. Costaron US$5,38, unos US$0,007 por producto. Además, el
describer da el kind de cada producto y si está en el alcance. Resultado:
- 683 con descripción.
- 58 fuera del alcance: foto que no muestra el producto, o producto de exterior, baño o infantil.
- 18 inválidas.

En 81 casos el modelo contestó el grupo ("table") en vez del kind ("coffee table"). Se resolvió
gratis, desde la caché, con el kind del listado cuando cae en ese grupo.

**Cómo se comparan.** ABO no tiene ambientes con sus productos anotados: no hay ground truth de
retrieval. La comparación es de punta a punta, sobre ambientes reales vacíos, con un juez que
compara las listas de a pares en los dos órdenes (`evaluation/endtoend.py`, `prompts/juez_listas_v1.md`).
Se usa el mismo plan para los dos catálogos, porque el plan no depende del catálogo. Configuración:
`datos/configs/punta_a_punta/catalogos.yaml`. Resultados en T3.

## T1 contra la v0 (mismo ground truth)

| | unidad | hit@1 | hit@10 | MRR@10 |
|---|---|---|---|---|
| v0 imagen: DINOv3, recorte con fondo, filtro por categoría | 325 recortes | 0,508 [0,44–0,57] | 0,819 | 0,603 |
| v1 texto: Qwen3, descripción, filtro por tipo (mismo catálogo de 275) | 207 consultas | **0,618 [0,56–0,68]** | **0,908** | **0,717** |
| v1 texto, catálogo actual de 268 | 198 consultas | 0,636 [0,58–0,70] | 0,914 | 0,737 |

Las unidades no son idénticas (un recorte por detección contra una consulta por producto visto),
pero el ground truth y la definición de relevante sí. Además la v1 no necesita generar una
primera imagen: el costo por corrida baja a la de una sola generación.

## T2: prueba del flujo completo

Pedido: "un living nórdico y cálido: un sofá, un sillón para leer, una mesa ratona y una
alfombra". Ambiente: `datos/ambientes_vacios/ambiente2-alvear/`, un living largo con ventanal al
balcón, con dos fotos: `alvear1.jpg` (la esquina del ventanal) y `alvear2.jpg` (el ambiente
entero, desde la abertura del otro extremo). Se corrió el RAG con cada una como foto que se
amobla y la otra como vista extra (va a Claude en plan, choose y scene, no al modelo de imagen),
y se generó la imagen sobre `alvear2`, que muestra todo el piso libre.

| | `prueba-alvear` (amobla alvear1) | `prueba-alvear2` (amobla alvear2) |
|---|---|---|
| Cómo leyó el ambiente | "an empty, bright living room with a full-width black-framed sliding glass door to a balcony..." | "an empty, long, bright living room [...] a black-framed sliding door to a balcony at the far end" |
| Sofá | 691.249.46: blanco, 3 cuerpos, brazos rectos, patas de abedul; contra la pared larga de la derecha | el mismo; contra la pared larga de la izquierda, a mitad del ambiente |
| Sillón para leer | 391.505.88: cuero coñac, estructura curvada oscura; junto al ventanal | el mismo |
| Mesa ratona | 902.976.57: cuadrada de fresno, 70 x 70 cm | 302.397.12: redonda, baja, de nogal |
| Alfombra | 302.837.81: crema de pelo largo, 170 x 240 cm | 002.852.58: tejida a rayas beige y gris, 180 x 224 cm |
| Claude (plan + choose + scene) | US$0,13 | US$0,13 |

El sofá y el sillón salieron primeros del ranking en las dos; la mesa y la alfombra cambian con
el lugar que se ve (con el living entero eligió una mesa más grande). En los dos, el prompt de
scene ubica cada producto por lo que se ve, da las medidas del catálogo y no menciona la otra
foto.

**La imagen** (`datos/resultados/amoblar/prueba-alvear2/final.png`, comparación en
`antes_despues.jpg`): Nano Banana 2 en fal, 1K, 24 s, US$0,08 (precio configurado: fal no
devuelve el costo). Lo que se ve:

- **El ambiente queda igual**: el encuadre, la abertura, el ventanal, la puerta de la derecha, el
  piso y la luz.
- **Los cuatro productos se reconocen**: el sofá de brazos rectos con patas claras, el sillón de
  cuero acolchado en rombos con su estructura oscura, la mesa redonda de nogal y la alfombra de
  tres franjas. Se pierde algún detalle chico (el ribete verde de la alfombra).
- **La ubicación respeta el prompt a medias**: el sofá va contra la pared izquierda mirando a la
  derecha, la mesa sobre la alfombra y el sillón a la derecha, orientado hacia el sofá. Pero el
  grupo queda en el primer tercio del ambiente, no "a mitad", y el sillón no está "cerca del
  balcón".
- Las sombras de contacto son suaves y creíbles; la escala relativa entre los muebles y el
  ambiente es razonable a ojo (sin medidas no se puede verificar).

**Cómo la vimos nosotros**: los productos se ven pegados ("falsos") y la disposición no tiene
sentido en un living tan largo: cuatro muebles juntos adelante y todo el fondo vacío; iban más
atrás, y el ambiente pide más muebles (una biblioteca, por ejemplo). Lo primero es del modelo de
imagen y del prompt, no del plan: el plan y el prompt pedían el sofá a mitad del living. Lo
segundo es del pedido (cuatro piezas) y del alcance del catálogo. El prompt de scene v2
(`src/amoblai/prompts/scene_prompt_v2.md`, corrida `prueba-alvear2-scene-v2`, US$0,04) ataca la
ubicación y la luz; su imagen está pendiente. Ver FUTURO.md.

**Lo que mostró la prueba** (y se arregló antes de generar):
1. **Medidas que no llegaban al LLM.** El paso choose solo pasaba la medida de un candidato si tenía
   ancho, profundidad y alto; las alfombras y las mesas del dataset tienen ancho y profundidad.
   Claude recibía "size unknown", eligió una alfombra de 140 x 200 cm y escribió en el prompt
   "unos 2 x 3 m". Ahora pasan las medidas que haya; con ellas eligió la de 170 x 240.
2. **Fotos que no son del producto.** Con las medidas, eligió la LISABO de 118 x 50 cm, cuya foto
   es la de 70 x 70: se excluyeron los 7 casos así (ver T1).
3. **Los asientos no tienen medidas en el dataset** (sofás, sillones y sillas: ninguno), así que
   el límite del plan no los filtra y el prompt da su tamaño a ojo. Ver FUTURO.md.

Los intermedios descartados están en `datos/resultados/amoblar/prueba-alvear/` (`descartado_sin_medidas/`,
`descartado_lisabo_118/`). Una primera prueba sobre una foto de Wikimedia Commons se descartó
porque la foto era poco realista (posterizada y oscura).

**Costo de una corrida completa**: US$0,13 de Claude + US$0,08 de la imagen = **US$0,21**. En
total, con las pruebas y repeticiones: Claude US$0,53, fal US$0,08 (`datos/resultados/gastos.jsonl`).

## T3: qué catálogo, de punta a punta en ambientes reales (2026-11-10)

**Pregunta.** ¿Con qué catálogo salen mejores listas para un ambiente vacío real: IKEA, ABO o los
dos juntos? T1f explica por qué no se puede medir con ground truth.

**Cómo.** Se usaron los 5 ambientes propios de `datos/ambientes_vacios/pedidos.yaml`, cada uno con un
pedido escrito como lo escribiría un usuario que sabe pedir. Cada variante corre plan, retrieve
y choose; el plan es el mismo para todas (el de IKEA). Después, el juez (Opus 5.5,
`juez_listas_v1`) ve la foto, el pedido y las dos listas: la foto de cada producto, su línea Type,
la medida y las unidades. No sabe de qué catálogo es cada una, y se le pregunta en los dos órdenes.

Métricas:
- **Gana:** la variante gana un ambiente solo si la elige en los dos órdenes; si cada orden elige
  otra, es empate.
- **Útil y aceptable:** el porcentaje de productos con nota 2 (cumple), y con nota 1 o más.
- **Pedido, ambiente y conjunto:** de 1 a 5, si la lista cumple lo que se pidió, si queda bien en
  ese cuarto y si los productos combinan entre sí.
- **Acuerdo entre órdenes:** cuántas veces los dos órdenes eligen lo mismo. Es la confiabilidad
  del juez.

Configuración: `datos/configs/punta_a_punta/catalogos.yaml`. Resultados:
`datos/resultados/punta_a_punta/catalogos/juez_*.json`. Costó unos US$3,7 en total: US$2,7 de plan y
choose (incluido un intento que se cortó a la mitad) y US$1,0 de juez.

| | gana | empates | útil | aceptable | pedido | ambiente | conjunto |
|---|---|---|---|---|---|---|---|
| **IKEA** | **4** | 1 | 0,71 | 0,97 | 4,2 | 4,3 | 4,1 |
| ABO | 0 | | 0,58 | 1,00 | 3,1 | 3,6 | 3,1 |
| IKEA | 2 | 1 | 0,78 | 1,00 | 4,2 | 4,0 | 4,1 |
| IKEA + ABO | 2 | | 0,76 | 1,00 | 4,2 | 4,3 | 3,9 |

Los dos órdenes coincidieron en 4 de 5 ambientes en las dos comparaciones. El 60% de los votos
fue para la posición A: hay algo de sesgo de posición, y preguntar en los dos órdenes lo cancela.

**Qué dice el juez.**
- ABO pierde por estilo. Para un pedido nórdico de maderas claras elige maderas medias u oscuras,
  patas doradas o una silla de plástico. En el rincón de lectura eligió una biblioteca escalera de
  76 × 160 cm cuando se pidió "grande y alta".
- Donde ABO empata es en la escala: en el living comedor largo, su mesa para seis de 180 cm y su
  alfombra de 292 cm le ganan a la mesa de 140 cm de IKEA. Eso sale de que ABO tiene medidas de
  casi todo.
- IKEA + ABO juntos no se distinguen de IKEA solo (2 a 2). En un ambiente la lista combinada no
  tenía ningún producto de ABO y ganó igual. Esa es la variación propia del choose y del juez
  cuando las listas son casi iguales: con 5 ambientes, una diferencia de un ambiente no es una
  señal.

**Decisión provisoria: el catálogo de IKEA** (con 5 ambientes). Pero todos los pedidos eran de
estilo nórdico o cálido, que es la estética de IKEA. Faltaba ver qué pasa con otros estilos.

### T3b: once ambientes, con pedidos de otros estilos

**Por qué.** IKEA + ABO empataba con IKEA en los 5 ambientes propios, y en ese caso el catálogo
combinado debería aportar variedad. Se sumaron 6 ambientes públicos reales (Wikimedia Commons y
Flickr, CC BY / BY-SA; `publicas.yaml` tiene el autor y la licencia, y 22 revisados) con pedidos
en otros estilos: loft industrial, living clásico con chimenea, comedor clásico moderno, japandi,
bohemio con color y estudio sobrio.

Configuración: `datos/configs/punta_a_punta/catalogos_estilos.yaml`. Los 5 propios salen de la
caché. Costo: US$2,2 (US$1,7 de plan y choose de los 6 nuevos, US$0,55 de juez).

| | ambientes | IKEA gana | IKEA + ABO gana | empates | útil IKEA | útil IKEA + ABO | ABO en la lista combinada |
|---|---|---|---|---|---|---|---|
| propios (nórdicos) | 5 | 2 | 2 | 1 | 0,78 | 0,76 | 26% |
| públicos (otros estilos) | 6 | 0 | **6** | 0 | 0,46 | **0,71** | 75% |
| **total** | 11 | 2 | **8** | 1 | 0,63 | **0,73** | |

Los dos órdenes coinciden en 10 de 11 ambientes (0,91). En los públicos, IKEA + ABO saca 4,1 de
pedido y 4,0 de ambiente, contra 3,0 y 3,1 de IKEA solo.

Lo que dice el juez en los públicos:
- La lista combinada trae lo que se pidió: el sofá de cuero envejecido y la biblioteca de metal
  negro del loft, la mesa para 6 a 8 de 198 cm, la silla ergonómica negra del estudio.
- IKEA 2013 no tiene esos productos. Cambia el sofá de cuero envejecido por uno liso, la biblioteca
  baja negra por una Billy marrón, y la mesa ratona clásica por una de vidrio.
- En ninguna de las dos listas apareció el sofá de terciopelo mostaza ni el verde: ningún catálogo
  lo tiene.

**Retrieval con ABO como distractores** (`20261110-010145_ablacion-catalogo-todos`, gratis). Las
mismas 549 búsquedas del ground truth de IKEA, sobre el catálogo combinado:

| | hit@1 | hit@10 | MRR@10 |
|---|---|---|---|
| IKEA | 0,535 | 0,893 | 0,654 |
| IKEA + ABO | 0,525 | 0,873 | 0,637 |

hit@1 baja un punto, dentro del intervalo de 95% (0,49 a 0,58). Es una cota pesimista: un producto
de ABO arriba del anotado puede servir igual, y el ground truth lo cuenta como error.
*Corrección (2026-11-12):* agregar productos solo puede bajar el número (0 consultas mejoran). Pareado: hit@1
−0,011 [−0,021; −0,002] y, lo que importa con 5 candidatos, hit@5 −0,035 [−0,052; −0,019] (0,812 →
0,778). El efecto es chico y es una cota pesimista, pero no está "dentro del intervalo".

**Decisión: el flujo usa IKEA + ABO** (`rag.catalog: datos/catalogo/todos.yaml`). En los pedidos
nórdicos no pierde nada, y en los de otros estilos es lo que hace que la lista tenga lo pedido. Las
evaluaciones con ground truth de IKEA se siguen corriendo sobre el catálogo de IKEA (`cli.IKEA_GT`),
para que los números sigan comparables.

**Límites.** Son 11 ambientes, y los pedidos los escribimos nosotros. Para los públicos los
escribimos sabiendo qué estilos faltan en IKEA: el experimento muestra que ABO cubre ese hueco, no
cuán frecuente es ese hueco entre los usuarios reales.

## T4 (diseño, pendiente de saldo en fal): experimentos de la imagen

Todo corre sobre los ambientes de `datos/ambientes_vacios/pedidos.yaml`, con la lista que eligió
el flujo para cada uno (los mismos `3_choice.json`: la imagen es lo único que cambia). Las
métricas son las de `evaluar-imagen` (gratis, locales):
- preservación: SIFT reencontrados y desplazamiento de la cámara, SSIM fuera de los muebles;
- fidelidad: puesto del producto de la lista entre los de su tipo, comparando el recorte con DINOv3;
- productos que faltan, repetidos e inventados;
- SigLIP 2 entre el pedido y la imagen.

Además, un juez (Opus, de a pares y en los dos órdenes, como T3) ve la foto original, las fotos
de los productos y las dos imágenes. Juzga si es el mismo cuarto, si son esos productos y si se ve
real. Se reportan también los reintentos del control SIFT.

| Exp. | Pregunta | Variantes | Imágenes (se pensó para 15 ambientes; hay 11) | Costo estimado |
|---|---|---|---|---|
| I1 | ¿Escena escrita por el LLM o edición estricta libre? | `scene_prompt_v2` (Claude escribe dónde va cada cosa) vs. `scene_prompt_libre_v4` | 30 + ~20% de reintentos | US$2,9 fal + US$0,5 Claude |
| I2 | ¿Qué modelo de imagen? | Nano Banana 2 vs. Nano Banana Pro (fal, ~US$0,15) vs. gpt-image (OpenAI, US$0,12, queda poco saldo) | 45 | US$4 |
| I3 | ¿Resolución 1K o 2K? | 1K (US$0,08) vs. 2K (US$0,12) | 15 extra | US$1,8 |
| I4 | ¿Las fotos del catálogo cambian la fidelidad? | IKEA (500 px) vs. ABO (1024 px), con la lista de cada catálogo | 15 extra | US$1,2 |
| I5 | ¿Dónde poner el umbral del control SIFT? | se calibra con los intentos de I1–I4 | 0 | gratis |
| | Jueces de imagen (Opus, dos órdenes) | | ~60 comparaciones | ~US$4 de Claude |

**Total estimado: unos US$10 de fal más unos US$5 de Claude.** Con US$15 de fal sobra margen para
repetir lo que haga falta. Se corre en ese orden: I1 decide la escena para I2–I4.

## T5: réplica de un ambiente real, sin cajas, con cajas 2D y con cajas 3D (2026-11-10; ronda 2, 2026-11-11)

**Pregunta.** En los ambientes vacíos no hay con qué comparar la imagen. ¿El generador reproduce un
ambiente real si sabe exactamente qué muebles van? (se prueba el generador, no el retrieval). Y, como
paso a futuro: ¿lo hace mejor si además le marcamos dónde va cada mueble?

**Configuración.** `amoblai evaluar-replica datos/configs/imagen/replica.yaml --pagar`
(evaluation/replica.py). El living `ikea-a-leather-look-made-for-lounging__1364309444239-s4.jpg`
del ground truth y sus 6 muebles anotados con caja confiable: sofá con chaise longue 802.991.95,
puf 702.991.91, mesa ratona 802.133.09, alfombra 302.837.81, estantería 599.026.58, lámpara de pie
302.865.67. Los adornos (floreros, portavelas, cuadros) quedan afuera porque el detector no los separa.
1. Las cajas de la foto real: Grounding DINO más la asignación por DINOv3 (evaluation/image.py).
2. Vaciado con Nano Banana 2 (`vaciar_ambiente_v1.md`), hasta 2 intentos. El control SIFT del flujo
   no sirve acá: casi todos los puntos de la foto real están en los muebles y cuadros que se sacan
   (6 y 7 inliers). Vale el intento que no deja muebles y tiene SSIM fuera de las cajas ≥ 0,4.
   - Intento 1: abrió el encuadre y dejó una lámpara (SSIM 0,33).
   - Intento 2: puerta, cortinas, ventana y línea del piso en su lugar (SSIM 0,45). Es el elegido.
3. sin_cajas: el paso de imagen del flujo tal cual (`scene_prompt_libre_v4`, pedido «Un living
   moderno con estos productos.»), 3 imágenes.
4. con_cajas: la foto vaciada con un rectángulo numerado por mueble, en su lugar en la foto real
   (`scene_prompt_cajas_v1`: cada producto llena su caja, después no queda ninguna línea), 3 imágenes.
5. con_cajas_3d (agregado después, porque las cajas de un mueble son volúmenes, no rectángulos): la
   foto vaciada con un prisma en perspectiva por mueble, apoyado en el piso, con su lugar, orientación
   y tamaño en la foto real (`scene_prompt_cajas3d_v1`), 3 imágenes. Las cajas salen de
   `evaluation/cajas3d.py`, gratis: Depth Pro (profundidad métrica y focal: 1179 px, campo de 47°),
   una máscara SAM por mueble (para el sofá hicieron falta puntos de ayuda: con la caja sola se
   quedaba con el respaldo), piso por RANSAC sobre la alfombra (cámara a 0,92 m) y pared por RANSAC
   (89,9° con el piso; la de los cuadros, a unos 48° de la cámara). Por mueble, percentiles 5-95 de sus
   puntos en los ejes del cuarto. Control con la metadata: estantería 140 × 166 cm estimada contra
   151 × 175 del catálogo; mesa ratona 63 × 62 contra Ø75.
6. Métricas, gratis: por producto, IoU de su caja en la imagen con la real (no detectado = 0),
   distancia entre centros y coseno DINOv3 del recorte con su foto. Por imagen, SSIM y coseno DINOv3
   con la foto real, y SIFT contra la vaciada.

**Resultados** (media de 3 imágenes; US$0,88 de fal; `datos/resultados/replica/living-dagarna/`):

| variante | IoU medio | en su lugar (IoU ≥ 0,5) | detectados | centro | coseno producto | SSIM real | DINO real |
|---|---|---|---|---|---|---|---|
| sin cajas | 0,20 (0,18 / 0,19 / 0,24) | 1,0 de 6 | 6 | 0,18 | 0,63 | 0,29 | 0,69 |
| con cajas | 0,40 (0,42 / 0,39 / 0,40) | 2,7 de 6 | 5,7 | 0,09 | 0,63 | 0,30 | 0,67 |
| con cajas 3D | 0,48 (0,44 / 0,55 / 0,46) | 3,3 de 6 | 5,7 | 0,06 | 0,60 | 0,32 | 0,67 |

IoU medio por mueble, sin → cajas 2D → cajas 3D: estantería 0,00 → 0,76 → 0,71; sofá 0,11 → 0,52 →
0,44; alfombra 0,54 → 0,69 → 0,75; puf 0,08 → 0,22 → 0,30; lámpara 0,23 → 0,16 → 0,57; mesa ratona
0,26 → 0,08 → 0,12.

**Lectura.**
- Sin cajas, el generador respeta los productos (los 6 aparecen y se reconocen) pero arma su
  propio living en cada imagen: sofá a la izquierda o al centro, estantería a la derecha. No es un
  error: el pedido no dice dónde va cada cosa.
- Con cajas, los muebles grandes van a su caja (estantería, sofá, alfombra). Los chicos que se
  superponen con otros no (puf, mesa ratona, lámpara).
- En 2 de 3 imágenes con cajas el modelo dejó las cajas dibujadas, y hasta las movió (una «6b»).
  Solo la tercera salió limpia, con un IoU igual que las otras (0,40).
- Con cajas 3D mejora un poco más (IoU 0,48, 3,3 de 6). La que más gana es la lámpara (0,16 →
  0,57): su rectángulo marcaba solo lo que se veía, detrás del sofá; el prisma llega al piso y dice
  dónde está parada. Puf y alfombra también suben; sofá y estantería quedan parecidos.
  *Corrección (2026-11-12):* esa explicación no se repitió: en la ronda 2 la lámpara empeora con cajas 3D
  (0,43 → 0,24). Con 3 imágenes por variante, las diferencias por mueble son ruido.
- Con cajas 3D, 1 de 3 imágenes dejó las cajas dibujadas (con rectángulos, 2 de 3). Otra repitió el
  puf (puso dos) y la tercera dio vuelta el sofá (la chaise a la izquierda).
- SSIM y DINO contra la foto real casi no cambian: los dominan lo que no está en la lista (el
  sillón, los cuadros, los adornos) y la ventana que el vaciado cambió.
- Es una sola habitación y 3 imágenes por variante: es una prueba, no una medición.

**Decisión.** El flujo no cambia. Si se sigue por acá, con cajas 3D. Queda como paso a futuro: medir el ambiente (una app con
LiDAR), tener las medidas de cada producto en la metadata, ubicar las cajas (que la IA decida en el
plano, o tomar dónde puso cada mueble una primera generación libre) y generar con cada mueble
llenando su caja. Más adelante, modelos 3D de los productos en lugar de cajas. Antes hay que pasar
las cajas de una forma que no quede dibujada (una máscara aparte o un segundo paso que las borre).

### T5b: ronda 2, prompts cortos, lugar en palabras y cajas en una imagen guía (2026-11-11)

**Por qué.** En la ronda 1 el modelo dejaba las cajas dibujadas (2 de 3 con rectángulos, 1 de 3 con
cajas 3D) y los prompts eran largos (una lista de prohibiciones). Pedido del usuario: una variante
sin cajas que diga en palabras dónde va cada mueble; las cajas en una imagen aparte, con la foto del
cuarto limpia; y prompts sencillos que digan qué hacer. Se rehicieron también sin cajas, cajas 2D y
cajas 3D con el prompt corto, para que la comparación no mezcle el prompt con la forma de indicar
el lugar.

**Configuración.** Mismo vaciado, mismos 6 productos, 3 imágenes por variante (variantes `simple_*`
de replica.yaml). Los seis prompts son iguales salvo una línea: `scene_prompt_simple_v1`,
`scene_prompt_texto_v1`, `scene_prompt_cajas_v2`, `scene_prompt_cajas_guia_v1`,
`scene_prompt_cajas3d_v2`, `scene_prompt_cajas3d_guia_v1`. Variante texto: cada línea de producto
termina en «Where: …», una o dos frases que escribió Opus 5.5 en una llamada (US$0,03) mirando la
foto real y la vaciada (`describir_lugares_v1`; quedan en lugares.json). Variante guía: la imagen 1
es la foto vacía limpia y la imagen 8 la misma foto con las cajas (`vacio_con_cajas.png` o
`vacio_con_cajas_3d.png`).

**Resultados** (media de 3; entre paréntesis, cada imagen):

| variante | IoU medio | en su lugar (de 6) | cajas que quedaron dibujadas |
|---|---|---|---|
| ronda 1 · sin cajas | 0,20 | 1,0 | — |
| ronda 1 · cajas 2D | 0,40 | 2,7 | 2 de 3 |
| ronda 1 · cajas 3D | 0,48 | 3,3 | 1 de 3 |
| sin cajas | 0,20 (0,19 / 0,27 / 0,16) | 0,7 | — |
| texto | 0,37 (0,38 / 0,41 / 0,34) | 1,7 | — |
| cajas 2D | 0,43 (0,42 / 0,40 / 0,46) | 3,3 | 2 de 3 |
| cajas 2D guía | 0,36 (0,25 / 0,37 / 0,47) | 2,3 | 1 de 3 (copió los rectángulos) |
| cajas 3D | 0,52 (0,59 / 0,52 / 0,46) | 4,0 | 0 de 3 |
| cajas 3D guía | 0,38 (0,39 / 0,36 / 0,39) | 2,3 | 1 de 3 (el borde de la alfombra) |

IoU por mueble, sofá / puf / mesa ratona / alfombra / estantería / lámpara: sin cajas 0,31 / 0,11 /
0,10 / 0,58 / 0,00 / 0,12; texto 0,51 / 0,11 / 0,22 / 0,61 / 0,51 / 0,30; cajas 2D 0,57 / 0,09 /
0,19 / 0,74 / 0,55 / 0,43; guía 2D 0,41 / 0,31 / 0,08 / 0,70 / 0,50 / 0,16; cajas 3D 0,55 / 0,46 /
0,27 / 0,73 / 0,89 / 0,24; guía 3D 0,62 / 0,11 / 0,23 / 0,67 / 0,62 / 0,03.

Costo: US$1,52 de fal (18 imágenes y una que se pagó y se perdió al llenarse el disco) y US$0,03 de
Opus. La réplica entera, US$2,40 de fal.

**Lectura.**
- El prompt corto no empeora nada: con la misma forma de indicar el lugar da lo mismo o un poco más
  (2D 0,40 → 0,43; 3D 0,48 → 0,52); con 3 imágenes, es ruido. Con cajas 3D, ninguna quedó dibujada.
- En palabras casi duplica el IoU de no decir nada (0,20 → 0,37) y no hay nada que borrar: las tres
  imágenes salen limpias y con el mismo arreglo (estantería y lámpara del lado correcto; el sofá
  mira a la cámara en vez de a la izquierda). Pero pocos muebles quedan exactamente en su lugar
  (1,7 de 6). El texto lo escribió Opus mirando la foto real: mide el canal, no si un LLM sabe
  decidir dónde va cada mueble.
- La imagen guía aparte no sirvió: ubica peor que las cajas dibujadas en la foto (2D 0,43 → 0,36; 3D
  0,52 → 0,38), una de las 2D no la siguió y tampoco evita que las dibuje (1 de 3 en las dos).
- La mejor: cajas 3D dibujadas sobre la foto con el prompt corto (IoU 0,52, 4 de 6, estantería 0,89).

**Decisión.** El flujo no cambia (sin medidas del ambiente no hay cajas). El paso a futuro va con
cajas 3D dibujadas sobre la foto y prompt corto; la guía aparte se descarta. Sin medir nada, se
podría probar que el plan escriba en palabras dónde va cada mueble.

## T6: lo que se midió en la revisión del 2026-11-12 (gratis, local)

**Por qué.** Una revisión crítica del trabajo (`docs/REVISION.md`) encontró que los números del
registro son correctos pero varias comparaciones no medían lo que decían: la tabla incremental
fundía tres cambios en un paso y partía de una línea de base debilitada; el "query rewriting" se
comparaba con un rival que no es "no reescribir"; faltaba la otra ruta de la clase para un
catálogo con fotos (embeber la imagen en vez de describirla); y los métodos se comparaban mirando
el intervalo de cada uno por separado. Todo lo de esta sección corre sobre las 549 consultas con
respuesta del catálogo IKEA final (819 productos), y cada método trae su **diferencia pareada**
contra la base y contra el paso anterior (las mismas consultas, IC 95% por bootstrap de
ambientes: `vs_base` y `vs_anterior` en `metricas.json`).

### T6a: el camino incremental, un cambio por paso

`ablaciones/camino.yaml`, corrida `20261112-090439_ablacion-camino`.

| Paso | hit@1 [IC 95%] | hit@5 | hit@10 | MRR@10 | Cambio en hit@1 contra el paso anterior |
|---|---|---|---|---|---|
| 1. RAG naive: el texto del vendedor (con su tipo) embebido con Qwen3, sin filtro; la consulta, la frase corta sin reescribir | 0,109 [0,08–0,14] | 0,299 | 0,439 | 0,194 | |
| 2. + nuestras descripciones de ocho líneas | 0,297 [0,25–0,35] | 0,601 | 0,736 | 0,430 | +0,188 [0,137; 0,237] |
| 3. + la consulta escrita como una ficha del catálogo (respuesta hipotética, HyDE) | 0,535 [0,49–0,58] | 0,811 | 0,885 | 0,652 | +0,239 [0,189; 0,287] |
| 4. + filtro por kind: la búsqueda del flujo | 0,530 [0,49–0,57] | 0,790 | 0,863 | 0,641 | −0,005 [−0,015; +0,006]; hit@5 −0,020 [−0,037; −0,004] |
| 5. + búsqueda léxica (BM25) fusionada | 0,581 [0,54–0,63] | 0,807 | 0,876 | 0,674 | +0,051 [0,013; 0,088] |
| 6. + la foto del producto (SigLIP 2) fusionada | 0,605 [0,56–0,65] | 0,825 | 0,883 | 0,701 | +0,024 [0,002; 0,045] |

- La línea de base es ahora honesta: el texto del vendedor **con el tipo que él le pone** ("Easy
  chair"; antes iba nuestra categoría gruesa), un embedder de verdad y la consulta como la
  escribiría alguien sin el paso plan. Antes el punto de partida era 0,077 (bolsa de palabras).
- Las dos decisiones que más pesan se miden por separado: la base de conocimiento (+0,19) y cómo
  se escribe la consulta (+0,24).
- El paso 4 no suma en este banco de prueba; se usa por otra razón (ver la corrección en T1).
- Los pasos 5 y 6 no están en el flujo: son la búsqueda híbrida de T6c.

### T6b: cómo se escribe la consulta, contra no reescribirla

**Pregunta.** El paso plan no busca con el pedido del usuario: escribe, para cada pieza, el
producto ideal en las mismas ocho líneas que el catálogo, y esa ficha es la consulta (query
expansion con respuesta hipotética, HyDE: "en mi base no tengo preguntas, tengo respuestas").
¿Cuánto suma, contra buscar con una frase corta sin reescribir? T1b lo comparaba con "solo la
línea Type" y "solo el kind", que no son no reescribir: buscar "rug" entre 89 alfombras es azar.

**Cómo.** `ablaciones/consulta.yaml`, corrida `20261112-093413_ablacion-consulta`. Las consultas
guardadas ya traen la versión sin reescribir: el campo `piece`, la frase con que el redactor
nombró la pieza antes de escribir la ficha ("square pine coffee table, front center"; 8 palabras
de mediana).

| Consulta | Densa, filtro kind (el flujo): hit@1 / hit@5 / hit@10 | Densa, sin filtro: hit@1 | BM25, filtro kind: hit@1 | SigLIP 2 (foto), filtro kind: hit@1 / hit@5 / hit@10 |
|---|---|---|---|---|
| La ficha de ocho líneas | 0,530 / 0,790 / 0,863 | 0,535 | 0,517 | 0,508 / 0,807 / 0,889 |
| La frase natural, sin reescribir | 0,324 / 0,648 / 0,778 | 0,297 | 0,332 | 0,479 / 0,781 / 0,880 |
| Solo la línea Type | 0,299 / 0,641 / 0,800 | | | |
| Solo el nombre del kind | 0,066 / 0,264 / 0,465 | | | |

- **La ficha suma +0,206 [0,157; 0,254] de hit@1** sobre la frase natural con la búsqueda del
  flujo (+0,142 de hit@5), y +0,239 [0,189; 0,287] sin filtro. Con BM25, +0,186.
- **El filtro por kind ayuda cuando la consulta es pobre** (0,297 → 0,324 con la frase natural) y
  no cuando es rica (0,535 → 0,530): la ficha ya dice qué es la pieza.
- **La búsqueda por foto casi no necesita la reescritura**: SigLIP 2 con la frase natural da
  0,479, contra 0,508 con la ficha (−0,029 [−0,065; +0,006]) y contra 0,324 de la densa con esa
  misma frase. Un modelo de imagen y texto está entrenado con frases cortas; el embedder de
  texto sobre descripciones necesita que la consulta hable como el catálogo. Con la frase
  natural, la híbrida (0,468) no mejora a la foto sola.
- **Límite.** La frase natural la escribió el mismo redactor que después escribió la ficha,
  mirando el mueble: es más informativa que un pedido de usuario. Lo que no está medido es el
  plan contra el pedido crudo, de punta a punta (US$2–3).

### T6c: búsqueda léxica, por foto e híbrida

**Pregunta.** Dos dudas de fondo sobre el índice. (1) ¿El embedder neuronal hace falta, o con
contar palabras alcanza? (2) El catálogo tiene fotos: la clase dio dos rutas, pasar la imagen a
texto (lo que hacemos: un VLM describe cada producto) o embeber la imagen directamente. La
segunda nunca se había medido para la consulta en texto (la primera aproximación buscaba imagen
contra imagen).

**Cómo.** `ablaciones/hibrido.yaml`, corrida `20261112-092807_ablacion-hibrido`. La base es la
búsqueda del flujo. `bm25`: Okapi BM25 sobre las mismas descripciones (`rag/hybrid.py`).
`siglip2` y `clip`: la torre de texto del modelo embebe la consulta en una frase corta (lo que
dicen las líneas Type, Materials, Colors y Shape; el modelo lee 64 tokens) y la de imagen, la
foto de cada producto; coseno entre las dos. Fusión: cada puntaje estandarizado (z-score) sobre
los productos que pasan el filtro, y el promedio; o por puestos (RRF).

| Buscador | hit@1 [IC 95%] | hit@5 | hit@10 | MRR@10 | hit@1 contra la base (pareado) |
|---|---|---|---|---|---|
| Densa: Qwen3 sobre las descripciones (el flujo) | 0,530 [0,49–0,57] | 0,790 | 0,863 | 0,641 | |
| Léxica: BM25 | 0,517 [0,48–0,56] | 0,801 | 0,869 | 0,631 | −0,013 [−0,063; +0,032] |
| Por foto: SigLIP 2 | 0,508 [0,45–0,56] | 0,807 | 0,889 | 0,632 | −0,022 [−0,077; +0,032] |
| Por foto: CLIP ViT-B/32 | 0,357 [0,31–0,40] | 0,710 | 0,849 | 0,512 | −0,173 [−0,221; −0,130] |
| Densa + léxica | 0,581 [0,54–0,63] | 0,807 | 0,876 | 0,674 | +0,051 [0,013; 0,088] |
| Densa + léxica, RRF | 0,545 [0,50–0,58] | 0,800 | 0,876 | 0,655 | +0,015 [−0,023; +0,050] |
| Densa + foto | 0,585 [0,54–0,64] | 0,829 | 0,889 | 0,689 | +0,055 [0,022; 0,090] |
| Léxica + foto (sin embedder de texto) | 0,597 [0,55–0,65] | 0,832 | 0,882 | 0,693 | +0,067 [0,024; 0,114] |
| **Densa + léxica + foto** | **0,605 [0,56–0,65]** | 0,825 | 0,883 | **0,701** | **+0,075 [0,041; 0,111]** |
| Densa + léxica + foto, RRF | 0,590 [0,54–0,64] | 0,829 | 0,887 | 0,693 | +0,060 [0,027; 0,098] |
| Densa, filtro por tipo | 0,535 [0,49–0,58] | 0,812 | 0,892 | 0,654 | +0,005 [−0,006; +0,015] |
| Densa + léxica + foto, filtro por tipo | 0,616 [0,57–0,66] | **0,847** | **0,920** | 0,715 | +0,086 [0,050; 0,123] |
| Densa, sin filtro | 0,535 [0,49–0,58] | 0,811 | 0,885 | 0,652 | +0,005 [−0,006; +0,015] |
| Densa + léxica + foto, sin filtro | 0,603 [0,56–0,65] | 0,842 | 0,913 | 0,707 | +0,073 [0,037; 0,109] |

**Lecturas.**
- **Los tres buscadores solos no se distinguen** (los intervalos de la diferencia cruzan el
  cero): el embedder neuronal no le gana a BM25, y describir cada producto con un VLM no le gana
  a embeber su foto con SigLIP 2, que además trae mejor hit@10 (+0,025 [0,005; 0,046]). Con CLIP
  ViT-B/32 la ruta de la imagen no alcanza.
- **Juntos sí suman**: se equivocan en cosas distintas. Las tres fusionadas dan +0,075 de hit@1,
  +0,035 [0,013; 0,056] de hit@5 y +0,060 [0,038; 0,083] de MRR sobre la búsqueda del flujo.
  Cada agregado solo ya es significativo (léxica +0,051, foto +0,055).
- La fusión por z-score rinde igual o mejor que RRF (los pesos son iguales: no se ajustó nada
  sobre estas consultas).
- La mejora es independiente del filtro.

**Con los otros dos redactores de consultas** (`--replica r2` y `r3`, corridas
`20261112-093737_ablacion-hibrido-r2` y `20261112-094441_ablacion-hibrido-r3`):

| Consultas | Densa (el flujo): hit@1 / hit@5 | Léxica: hit@1 | Por foto: hit@1 | Densa + léxica + foto: hit@1 / hit@5 | Diferencia de hit@1 (pareada) |
|---|---|---|---|---|---|
| originales | 0,530 / 0,790 | 0,517 | 0,508 | 0,605 / 0,825 | +0,075 [0,041; 0,111] |
| r2 | 0,519 / 0,788 | 0,486 | 0,495 | 0,594 / 0,823 | +0,075 [0,043; 0,111] |
| r3 | 0,567 / 0,797 | 0,501 | 0,477 | 0,612 / 0,845 | +0,046 [0,016; 0,076] |
| media ± desvío | 0,539 ± 0,025 / 0,792 | 0,501 | 0,493 | 0,604 ± 0,009 / 0,831 | |

La mejora de la fusión se repite en las tres escrituras, en hit@1 y en hit@5 (+0,035, +0,035 y
+0,048, todos con intervalo que no toca el cero). Lo que no se repite del todo es el empate entre
los buscadores solos: con el tercer redactor la densa queda arriba de la léxica (−0,066 [−0,114;
−0,021]) y de la foto (−0,090 [−0,131; −0,050]). La híbrida además varía menos entre redactores
(±0,009 contra ±0,025).

**En los pedidos reales** (los 11 ambientes vacíos, 75 piezas; gratis: solo el retrieve). Con la
híbrida cambian en promedio 1,6 de los 5 candidatos de cada pieza (3,4 en común), el primero es
el mismo en el 55% de las piezas, y el producto que eligió la versión 1 sigue entre los 5 en el
87%. Qué lista resulta mejor solo lo puede decir el cara a cara con el juez
(`datos/configs/punta_a_punta/hibrida.yaml`: unos US$2, sin correr).

**Decisión.** La búsqueda híbrida es la **versión 2** del flujo (`rag.hybrid: [bm25, siglip2]`
en `amoblai.yaml`; la versión 1 es `rag.hybrid: []`): sale de una limitación medida de la
versión 1, es una técnica de Advanced RAG, es una línea de configuración, y se confirmó de punta
a punta (T8).

### T6d: qué líneas de la descripción hacen el trabajo

**Pregunta.** La pregunta de splitting que este problema sí tiene no es cómo partir el documento
(T1d: no conviene) sino qué lo compone: ¿qué líneas de las ocho hacen el trabajo?

**Cómo.** `ablaciones/lineas.yaml`, corrida `20261112-095742_ablacion-lineas`: se sacan líneas de
los documentos y de las consultas, y se vuelve a embeber y a buscar (el documento entero, con la
búsqueda densa y el filtro por kind).

| Descripción y consulta | hit@1 | hit@5 | hit@10 | MRR@10 | hit@1 contra las ocho líneas (pareado) |
|---|---|---|---|---|---|
| Las ocho líneas | 0,530 | 0,790 | 0,863 | 0,641 | |
| Sin Colors | 0,474 | 0,760 | 0,854 | 0,595 | −0,057 [−0,082; −0,030] |
| Sin Shape | 0,499 | 0,772 | 0,869 | 0,620 | −0,031 [−0,057; −0,006] |
| Sin Feel ni Goes with | 0,534 | 0,778 | 0,863 | 0,639 | +0,004 [−0,017; +0,025] |
| Solo lo que se ve: Type, Materials, Colors, Shape | 0,537 | 0,776 | 0,849 | 0,634 | +0,007 [−0,033; +0,045] |

**Lectura.** Lo que encuentra el producto es lo que se ve: sacar los colores cuesta 6 puntos y
sacar la forma, 3. Las cuatro líneas subjetivas o de contexto (Use, Style, Feel, Goes with) no
aportan nada medible en este banco: con cuatro líneas se encuentra igual que con ocho (en el
modo línea contra línea, que sale de la caché, da lo mismo: Colors −0,055, Shape −0,038, el
resto dentro del ruido). **Salvedad, y por qué no se sacan:** el banco es de producto conocido.
Use, Style y Goes with existen para el pedido abierto ("un living nórdico y cálido"), donde el
plan pide un estilo y un uso y no un objeto que está viendo: eso este banco no lo mide. Es una
hipótesis a probar de punta a punta, no una decisión.

### T6e: un reranker de texto local (Qwen3-Reranker)

Quedaba configurado desde octubre y sin correr (unos 50 s por consulta en esta CPU: 7,6 horas
para las 549). `ablaciones/reranking-local.yaml`, corrida `20261112-093720_ablacion-reranking-local`
(los puntajes quedan en caché: volver a correrla tarda segundos). Qwen3-Reranker-0.6B, un
cross-encoder de la familia del embedder, reordena el top-10 leyendo la consulta y cada
descripción juntas.

| | hit@1 | hit@5 | hit@10 | MRR@10 |
|---|---|---|---|---|
| Qwen3, filtro por tipo | 0,535 | 0,812 | 0,892 | 0,654 |
| + rerank con MiniLM de MS MARCO (T1d) | 0,419 | 0,774 | 0,892 | 0,565 |
| + rerank con Qwen3-Reranker-0.6B | 0,474 | 0,796 | 0,892 | 0,611 |
| + rerank con Opus mirando las fotos (T1e) | 0,687 | 0,858 | 0,892 | 0,760 |

Qwen3-Reranker empeora: −0,062 [−0,111; −0,013] de hit@1 y −0,042 [−0,073; −0,012] de MRR. Antes
solo estaba el MiniLM, un modelo chico entrenado para otra tarea, y contra un VLM que además ve
fotos: no separaba modelo de modalidad. Con un reranker de texto bueno y hecho para esto el
resultado es el mismo: **releer el texto que ya usó la búsqueda no suma; mirar las fotos sí.**
Y a 50 s por consulta en CPU, tampoco serviría por latencia.

### T6f: el flujo real, sin juez

`amoblai diagnostico-flujo` lee las corridas guardadas de punta a punta (11 ambientes vacíos, 75
piezas por variante) y escribe `datos/resultados/punta_a_punta/catalogos/diagnostico.json`.

| | IKEA | IKEA + ABO (las listas de la versión 1) |
|---|---|---|
| El producto elegido es el primero del coseno | 47% | 45% |
| El elegido sale de los puestos 4 y 5 | 16% | 24% |
| Piezas que el que elige dejó afuera | 0 de 75 | 0 de 75 |
| Coseno del primer candidato (mediana) | 0,80 | 0,82 |
| Elegidos sin ninguna medida en el catálogo | 72% | 37% |
| Piezas con dos o más candidatos del mismo modelo | 40 de 75 | 18 de 75 |
| El elegido tiene el primer estilo que pidió el plan | 60% | 61% |
| Elegidos que son de ABO | — | 52% |

- **El que elige hace trabajo de verdad**: en más de la mitad de las piezas no se queda con el
  primero de la búsqueda. Y los candidatos 4 y 5 se usan (24% de lo elegido): apoya haber pasado
  de 3 a 5.
- **Nunca dice "no hay"**: 0 piezas dejadas afuera (y 0 de 187 contando todas las corridas),
  aunque ningún catálogo tenía, por ejemplo, el sofá de terciopelo mostaza pedido. Sustituye por
  lo más parecido sin avisar. Es una limitación.
- **Las consultas del plan quedan más lejos del catálogo** que las del banco de prueba (coseno
  del primero 0,80–0,82 contra 0,875): en el flujo real el plan imagina el producto, no lo ve.
- **El tamaño casi nunca se puede verificar** con IKEA (72% de lo elegido sin medidas).
- **Variantes repetidas**: con IKEA, en más de la mitad de las piezas hay candidatos que son el
  mismo modelo en otro color o medida. No se deduplica ni se usa MMR.

### T6g: ¿error, o el mismo mueble en otro color? El acierto por familia

**Pregunta.** hit@1 exige el producto anotado exacto, y el catálogo está lleno de variantes del
mismo modelo (482 de los 819 productos comparten nombre y grupo con otro; el 69% de las consultas
busca un producto que tiene variantes). ¿Cuánto de lo que cuenta como error es "el mismo mueble
en otra medida u otro color"? ¿Y eso cambia qué embedder conviene?

**Cómo.** Una métrica más en todas las ablaciones: `familia_hit@k` cuenta como acierto el
producto anotado **o** cualquier variante de su modelo (mismo nombre comercial y mismo grupo de
relevancia). `ablaciones/embedders.yaml`, corrida `20261112-102437_ablacion-embedders`.

| Buscador (filtro por kind) | hit@1 exacto | hit@1 por familia [IC 95%] | hit@5 exacto / por familia | hit@1 por familia contra Qwen3 (pareado) |
|---|---|---|---|---|
| Qwen3-Embedding (densa) | 0,530 | 0,623 [0,58–0,67] | 0,790 / 0,827 | |
| Bolsa de palabras (hashing) | 0,515 | 0,596 [0,55–0,65] | 0,796 / 0,843 | −0,027 [−0,070; +0,017] |
| BM25 | 0,517 | 0,637 [0,60–0,68] | 0,801 / 0,854 | +0,015 [−0,024; +0,055] |
| BGE-base | 0,475 | 0,557 [0,51–0,60] | 0,740 / 0,805 | −0,066 [−0,106; −0,027] |
| SigLIP 2 (por foto) | 0,508 | 0,585 [0,53–0,64] | 0,807 / 0,843 | −0,038 [−0,089; +0,017] |
| Densa + léxica + foto (versión 2) | 0,605 | 0,689 [0,64–0,74] | 0,825 / 0,862 | |

- **Sí: una parte de los "errores" no lo son.** De las veces que el primero no es el producto
  anotado, una de cada cinco es otra variante del mismo modelo (20% con Qwen3, 25% con BM25).
  Contando la familia, el acierto sube unos 9 puntos (0,530 → 0,623).
- **Hay tres niveles de "correcto"**, y conviene decirlos juntos: el producto exacto primero,
  0,53; el mismo modelo primero, 0,62; un producto que un juez considera que sirve primero, 0,78
  (relevancia graduada, T1d).
- **No cambia la comparación entre embedders**: por familia tampoco se distinguen Qwen3, BM25,
  hashing y SigLIP 2, y BGE sigue siendo peor. El experimento subestima el nivel absoluto, no
  el orden.
- **El mejor embedding de OpenAI** (text-embedding-3-large) quedó listo para comparar
  (`ablaciones/embedder-openai.yaml`, unos centavos) y sin correr: la clave de OpenAI del `.env`
  está vencida.

## T7: las métricas del generador, rehechas (2026-11-12)

**Por qué.** La revisión encontró dos problemas en las métricas RAGAS del generador (T1d): el
prompt del juez de answer relevance traía de ejemplo "un living nórdico y cálido", que era el
pedido evaluado en 3 de las 4 corridas (el juez lo copiaba: fuga de datos); y el juez de
faithfulness leía la descripción completa de cada producto, que el paso choose nunca recibe.
Además eran 3 respuestas distintas, de una configuración anterior.

**Cómo.** `juez_pedidos_v2` (sin ejemplos de pedido) y `juez_fidelidad_v2` (el juez recibe lo
que vio el generador: el pedido, la foto del ambiente y, de cada producto elegido, su foto y la
línea con su kind, su tipo y su medida). Opus por la API sobre las **11 listas de la
configuración final** (`punta_a_punta/catalogos/todos/`): `amoblai evaluar-respuesta <corridas>
--juez opus --pagar`. Costó US$1,10 (22 llamadas). Resultados:
`datos/resultados/evaluacion_respuesta/resumen.json`.

| Métrica | Valor | Referencia |
|---|---|---|
| Faithfulness | 0,82 (289 de 351 afirmaciones; por lista, de 0,70 a 0,93) | la versión 1 daba 0,89–0,96, con otro contexto |
| Answer relevance | 0,69 | vara cruzada (los pedidos escritos para *otras* listas): 0,55; la propia supera a las ajenas en 11 de 11; piso (pedidos sin relación): 0,40 |

- **Lo que no se sostiene** (62 afirmaciones) es casi siempre lo mismo: la especie de la madera
  ("la mesa es de fresno", "las patas son de abedul", "las sillas son de haya"), que el
  generador afirma sin que nada de su contexto lo diga, y medidas que el catálogo no tiene.
  Accionable: pasarle al que elige la línea de materiales de cada candidato, o pedirle que no
  afirme lo que no ve.
- Con la fuga afuera, la answer relevance sigue distinguiendo la lista propia de las ajenas
  (0,69 contra 0,55), que es lo que la versión 1 no mostraba.

## T8: de punta a punta: versión 1 contra versión 2, y con búsqueda contra sin búsqueda (2026-11-12)

Los 11 ambientes vacíos reales de `pedidos.yaml`, el mismo plan para todas las variantes, y el
juez de listas de T3 (Opus, de a pares, a ciegas, en los dos órdenes; una variante gana un
ambiente solo si gana en los dos órdenes). Resultados en
`datos/resultados/punta_a_punta/hibrida/`.

### T8a: la búsqueda densa (versión 1) contra la híbrida (versión 2)

`punta_a_punta/hibrida.yaml`. El único cambio es `rag.hybrid`. Las listas de la versión 1 son
las del 10/11, salvo dos ambientes donde el arreglo del filtro de medidas cambia los candidatos
de la alfombra: esos se eligieron de nuevo, para que las dos variantes usen el mismo filtro.
Costó unos US$3,0 (US$2,0 de elección y US$1,0 de juez).

| | gana | empates | votos (de 22) | útil | pedido | ambiente | conjunto |
|---|---|---|---|---|---|---|---|
| Versión 1: densa | 0 | 6 | 5 | 0,68 | 3,68 | 3,96 | 3,59 |
| **Versión 2: híbrida** | **5** | | **15** | **0,74** | **3,96** | **4,04** | **3,96** |

- **La híbrida gana 5 ambientes, no pierde ninguno y empata 6** (test de signos sobre los 5
  decididos: p = 0,06 a dos colas). En 5 de los 6 empates cada orden eligió una lista distinta (el
  juez no se decide); en el otro las dos listas son idénticas y el juez dijo empate las dos veces.
- Los dos órdenes coinciden en 6 de 11 (0,55), menos que en T3b (0,91): acá las listas se
  parecen mucho (comparten 50 de 75 productos) y la diferencia es más fina. El sesgo a la
  posición A es 0,59; preguntar en los dos órdenes lo cancela.
- Sin juez (`diagnostico-flujo`): el que elige se queda con el primero de la búsqueda el 41% de
  las veces con la híbrida y el 44% con la densa; el primer estilo pedido, 60% y 63%. No hay
  diferencia ahí: lo que cambia es qué productos llegan.

**Decisión: el flujo usa la búsqueda híbrida** (versión 2). Para el Ejercicio 4:

| | Versión 1 | Versión 2 |
|---|---|---|
| Configuración | `rag.hybrid: []` | `rag.hybrid: [bm25, siglip2]` |
| Qué busca | coseno del embedder sobre las descripciones | lo mismo, fusionado con BM25 y con la foto del producto (SigLIP 2) |
| Limitación de la versión 1 | el índice lee una descripción pero no ve el producto ni aprovecha las palabras exactas: entre productos casi iguales el primero acierta el 53% y en 1 de cada 5 piezas el correcto no llega a los 5 candidatos | |
| hit@1 / hit@5 / MRR@10 (ground truth, 549 consultas) | 0,530 / 0,790 / 0,641 | 0,605 / 0,825 / 0,701 (+0,075 [0,041; 0,111] de hit@1) |
| hit@1 con tres redactores | 0,539 ± 0,025 | 0,604 ± 0,009 |
| De punta a punta (11 ambientes) | gana 0 | gana 5, empata 6 |
| Productos útiles según el juez | 0,68 | 0,74 |
| Costo por pedido | igual | igual (BM25 y SigLIP 2 corren locales) |

### T8b: con búsqueda contra sin búsqueda

**Pregunta.** ¿La búsqueda aporta en la tarea real, o el LLM que elige arma una buena lista con
cualquier cosa del kind pedido? Es el "con y sin retrieval" del flujo, y a la vez el control del
instrumento: si el juez no distinguiera estas dos listas, ninguna comparación de punta a punta
sobre la búsqueda diría nada.

**Cómo.** `punta_a_punta/sin_busqueda.yaml`: el flujo con los 5 candidatos más cercanos de cada
pieza contra el mismo flujo con 5 productos **al azar** entre los que pasan los mismos filtros
(kind y medidas; `rag.mode: random`). Mismo plan, mismo paso de elección, mismo juez. 7 ambientes
(los de menos piezas, por costo). Costó US$1,41.

| | gana | votos (de 14) | útil | pedido | ambiente | conjunto |
|---|---|---|---|---|---|---|
| **Con búsqueda** | **7** | **14** | **0,82** | 4,14 | 4,29 | 4,21 |
| Sin búsqueda (al azar dentro del kind) | 0 | 0 | 0,26 | 2,71 | 2,93 | 2,29 |

- **7 a 0, con los dos órdenes de acuerdo en los 7** (test de signos, p = 0,016). Productos
  útiles: 0,82 contra 0,26. El filtro por kind solo no alcanza: sin el ranking, la lista tiene
  el tipo de pieza correcto y poco más.
- Sin juez va en el mismo sentido: el producto elegido tiene el primer estilo que pidió el plan
  en el 33% de las piezas sin búsqueda, contra el 63% con búsqueda.
- **El juez distingue**: cuando la diferencia es grande, los dos órdenes coinciden siempre. Eso
  le da sentido a los empates de T8a (ahí las listas son parecidas de verdad).

## T9: las imágenes de la configuración final (2026-11-12)

**Por qué.** Hasta acá ninguna imagen se había generado con el catálogo combinado ni con la
búsqueda de la versión 2: las 8 imágenes con métricas eran de 4 ambientes, con listas solo de
IKEA y con varias configuraciones mezcladas.

**Cómo.** Las 11 listas de la versión 2 (`punta_a_punta/hibrida/hibrida/`; 37 de sus 75
productos son de ABO) pasaron por el resto del flujo: la plantilla del prompt
(`scene_prompt_libre_v4`), Nano Banana 2 y el control del ambiente con hasta 3 intentos. Las
corridas completas están en `datos/resultados/amoblar/final-<ambiente>/`. Después,
`amoblai evaluar-imagen` (gratis). Costó US$1,52 de fal (19 intentos).

| Ambiente | Productos | Detectados | Reconocidos como el producto exacto | Coseno | Control del ambiente (puntos SIFT de cada intento) |
|---|---|---|---|---|---|
| alvear-escritorio | 5 | 5 | 3 | 0,54 | pasa al 1.º (416) |
| alvear-living-comedor | 15 (13 en la imagen) | 14 | 2 | 0,35 | no pasa (3 intentos; el mejor, 39) |
| caballito-comedor | 4 | 4 | 1 | 0,49 | no pasa (50, 68, 56: la cámara se movió) |
| caballito-living | 8 | 8 | 4 | 0,50 | no pasa (20, 12, 17) |
| experimento-lectura | 7 | 7 | 3 | 0,44 | pasa al 1.º (158) |
| publica-comedor-clasico-moderno | 4 | 4 | 1 | 0,59 | pasa al 1.º (398) |
| publica-estudio-sobrio | 5 | 5 | 4 | 0,70 | pasa al 1.º (145) |
| publica-living-bohemio | 9 | 9 | 4 | 0,54 | pasa al 1.º (222) |
| publica-living-clasico | 6 | 5 | 3 | 0,58 | no pasa (8, 9, 7: reencuadró hacia la chimenea) |
| publica-living-japandi | 5 | 5 | 3 | 0,51 | pasa al 1.º (168) |
| publica-loft-industrial | 7 | 5 | 3 | 0,59 | pasa al 1.º (360) |
| **Total** | **75** | **71** | **31 (41%)** | **0,50** | **7 de 11 pasan, todas al primer intento** |

- **Los productos aparecen (71 de 75 detectados), pero el reconocimiento exacto es del 41%**:
  al comparar el recorte de cada mueble con las fotos del catálogo, el más parecido de su tipo es
  el de la lista en 31 de 75. Es del orden de lo que da el mismo reconocimiento sobre fotos
  reales de IKEA (0,44, con otro procedimiento), y menos que el 50% de las 8 imágenes anteriores:
  son listas más largas y con productos de ABO.
- **El control del ambiente hace su trabajo, el reintento no**: 7 de 11 ambientes pasan al primer
  intento. En los otros 4 fallaron los 3 intentos: el modelo vuelve a mover la cámara o a rehacer
  el cuarto con el mismo prompt. Reintentar igual gasta dos imágenes más y casi nunca lo arregla
  (contando la corrida anterior de caballito-living, rescató 1 de 5). Lo que se entrega en esos
  casos es el mejor intento, marcado como no preservado.
- **El modelo de imagen acepta 14 imágenes**: la foto y 13 productos. El ambiente de 15 piezas
  no se podía dibujar (fal rechazó el pedido, sin cobrarlo). Desde hoy la imagen muestra las 13
  primeras piezas (el plan las ordena por importancia) y las otras quedan en la lista de compra
  (`furnish.max_image_products`).
- **Decisión.** El flujo no cambia. Queda como limitación de la mitad "imagen" del producto: la
  lista es confiable (productos reales, elegidos entre candidatos recuperados); la imagen es una
  visualización que acierta el producto exacto 4 de cada 10 veces y conserva el cuarto 2 de cada 3.

## Pendientes de la v1

Actualizado el 2026-11-12. Lo que falta decidir y lo que cuesta está en `docs/REVISION.md`
(secciones 4, 6 y 8): el cara a cara de punta a punta entre la versión 1 y la versión 2, RAG
contra no RAG, la misma configuración dos veces (el piso de ruido del juez), una imagen con la
configuración final, el experimento de la escena con más de un ambiente, y el voto a ciegas del
equipo para validar al juez.

# v0: retrieval por imagen (deprecada)

## Metodología

### Retriever (ambientes de IKEA)

- **Datos**: fotos de ambientes de IKEA de tipo *Living Room* y *Dining* que
  están en disco y tienen al menos un SKU anotado del alcance: **65 ambientes**,
  232 pares (ambiente, SKU anotado) dentro de las 5 categorías.
- **Consulta**: detección de los muebles del alcance → recorte → (sin fondo) →
  embedding → ANN con o sin filtro por la categoría detectada → top-10.
- **Relevantes de un recorte**: los SKUs anotados en ese ambiente de la misma
  categoría que la detección. Las anotaciones no traen posiciones, así que la
  métrica es **permisiva**: un recorte de la silla A que recupera la silla B del
  mismo ambiente cuenta como acierto. Los recortes cuya categoría no tiene
  ningún SKU anotado en el ambiente (falsos positivos del detector o muebles no
  anotados) no tienen respuesta posible y se cuentan aparte.
- **Métricas**: hit rate@k (k = 1, 5, 10) y MRR@10 por recorte; recall@k por
  ítem anotado (¿algún recorte del ambiente recuperó ese SKU?, castiga también
  lo que el detector no ve); baseline aleatorio analítico (ranking al azar
  dentro del mismo universo de búsqueda); IC 95% por bootstrap de ambientes
  (1000 remuestreos), porque los recortes de un ambiente no son independientes.
- **Versión estricta**: recortes etiquetados a mano con su SKU exacto
  (`deprecated/anotaciones/estricto.jsonl`, herramienta `deprecated/apps/etiquetado.py`). *Pendiente
  de etiquetar.*
- **Umbral**: se calibra por colección maximizando F1 de "aceptar ⇔ el top-1 es
  correcto" (los recortes sin respuesta posible cuentan como negativos).

### De punta a punta (ambientes vacíos)

Re-identificación (top-1 y top-5), SSIM y error absoluto medio fuera de las
cajas dilatadas (original vs. final, y original vs. imagen 1 como referencia),
cobertura, costo en USD y latencia por ambiente. *Pendiente: requiere las fotos
de ambientes vacíos y las imágenes generadas.*

### Entorno de las corridas de este registro

CPU (Intel, sin GPU NVIDIA), torch 2.14.1, transformers 5.19.0, chromadb 1.5.9.
Detector Grounding DINO tiny, SAM ViT-B, embedders en su variante base.

---

## R1 — Línea de base: DINOv2 + SAM + filtro por categoría (detector v1)

- **Corrida**: `20261006-203639_retriever_base-dinov2`
- **Config**: `deprecated/configs/base.yaml` (DINOv2 base, fondo quitado con SAM, filtro por
  categoría, Grounding DINO con el post-procesamiento estándar de transformers).

| | hit@1 | hit@5 | hit@10 | MRR@10 |
|---|---|---|---|---|
| Retriever (227 recortes con respuesta) | 0,286 [0,227–0,347] | 0,560 | 0,643 | 0,400 [0,343–0,458] |
| Azar | 0,024 | 0,116 | 0,226 | 0,068 |

Recall por ítem@10: 0,539. **Recall de sillas: 0,00.**

**Problema detectado**: de 403 detecciones, 187 eran "armchair" y 1 era "chair".
Grounding DINO arma la etiqueta con todos los tokens que superan el umbral y
devuelve frases fusionadas como `"armchair chair chair"`; el mapeo elegía la
frase más larga contenida ("armchair"). Resultado: casi todas las sillas se
buscaban entre los sillones (con filtro por categoría, nunca podían acertar).

## R2 — Detector v2: clasificación por frase

- **Corrida**: `20261006-222011_retriever_base-dinov2-detector-v2`
- **Cambio**: cada caja se asigna a la frase del prompt con mayor probabilidad
  (máximo de sus tokens), en lugar de reconstruir la etiqueta con todos los
  tokens que superan un umbral (`vision/detection.py`, commit `ccdd97b`).
- **Config**: igual que R1.

| | hit@1 | hit@5 | hit@10 | MRR@10 |
|---|---|---|---|---|
| Retriever (325 recortes con respuesta) | **0,345** [0,293–0,397] | 0,597 | 0,686 | **0,453** [0,413–0,494] |
| Azar | 0,023 | 0,115 | 0,225 | 0,067 |

Recall por ítem@10: **0,651** [0,595–0,703].

| Categoría | recortes | hit@1 | hit@10 | MRR@10 | recall ítem@10 |
|---|---|---|---|---|---|
| silla | 127 | 0,504 | 0,811 | 0,604 | 0,976 |
| sillón | 8 | 0,500 | 1,000 | 0,750 | 0,381 |
| mesa | 94 | 0,319 | 0,670 | 0,435 | 0,792 |
| sofá | 30 | 0,133 | 0,567 | 0,241 | 0,552 |
| alfombra | 66 | 0,152 | 0,485 | 0,247 | 0,406 |

Umbral calibrado: **0,563** (F1 0,573; precisión 0,471; recall 0,732). Similitud
media del top-1: 0,638 cuando es correcto, 0,481 cuando no.

**Lecturas**:
- El arreglo del detector sube todas las métricas y lleva el recall de sillas de 0 a 0,98.
- Ahora el error va para el otro lado: varios sillones se detectan como sillas
  (recall de sillones 0,95 → 0,38). Con filtro duro, un error de categoría del
  detector es un error de retrieval: motiva el "filtro por grupo" (FUTURO.md).
- Alfombras y sofás son lo más difícil: las alfombras quedan tapadas por otros
  muebles (SAM las segmenta mal) y los sofás aparecen muy ocluidos y en
  perspectiva, contra fotos de catálogo frontales.

## R3 — Ablación del retriever

- **Plan**: `deprecated/configs/ablaciones/retriever.yaml` — grilla completa embedder (CLIP,
  SigLIP 2, DINOv2, DINOv3) × quitar fondo (SAM / no) × filtro por categoría
  (sí / no), más el camino incremental E0 → E4. Mismo detector (v2) y mismos 65
  ambientes en todas las corridas; 325 recortes con respuesta posible en cada una.
- **Corridas**: `datos/resultados/v0_imagen/corridas/*_retriever_abl-retriever-*`; tablas y
  gráficos en `datos/resultados/v0_imagen/reporte/`. DINOv3 se sumó cuando llegó el acceso
  (mismo día, mismas detecciones y máscaras en caché).

### Camino incremental (para la presentación)

| Paso | Cambio respecto del anterior | hit@1 [IC 95%] | hit@5 | hit@10 | MRR@10 | recall ítem@10 |
|---|---|---|---|---|---|---|
| E0 | naive: CLIP, recorte con fondo, sin filtro | 0,126 [0,08–0,18] | 0,255 | 0,345 | 0,179 | 0,323 |
| E1 | + quitar fondo (SAM) | 0,139 [0,09–0,19] | 0,249 | 0,320 | 0,186 | 0,341 |
| E2 | + filtro por categoría (metadata filtering) | 0,209 [0,16–0,26] | 0,459 | 0,588 | 0,317 | 0,599 |
| E3 | CLIP → DINOv2 | 0,345 [0,29–0,40] | 0,597 | 0,686 | 0,452 | 0,651 |
| E3' | CLIP → SigLIP 2 | 0,323 [0,27–0,38] | 0,615 | 0,711 | 0,445 | 0,698 |
| E3'' | CLIP → DINOv3 | 0,468 [0,42–0,52] | 0,689 | 0,757 | 0,562 | 0,720 |
| **E4** | DINOv3 **sin** quitar fondo (**default**) | **0,508 [0,44–0,57]** | 0,714 | **0,819** | **0,603** | 0,741 |
| E4' | SigLIP 2 **sin** quitar fondo | 0,465 [0,40–0,53] | **0,754** | 0,809 | 0,587 | **0,763** |

Baseline aleatorio (con filtro): hit@1 0,023, hit@10 0,225, MRR@10 0,067.
Sin filtro el universo es todo el catálogo indexado (2187 SKUs): hit@1 0,0006.

### Grilla completa (hit@1 / MRR@10)

| Embedder | fondo quitado, sin filtro | fondo quitado, con filtro | con fondo, sin filtro | con fondo, con filtro |
|---|---|---|---|---|
| CLIP | 0,139 / 0,186 | 0,209 / 0,317 | 0,126 / 0,179 | 0,237 / 0,342 |
| DINOv2 | 0,262 / 0,350 | 0,345 / 0,452 | 0,099 / 0,195 | 0,252 / 0,381 |
| SigLIP 2 | 0,252 / 0,331 | 0,323 / 0,445 | 0,400 / 0,507 | 0,465 / 0,587 |
| DINOv3 | 0,385 / 0,455 | 0,468 / 0,562 | 0,375 / 0,456 | **0,508 / 0,603** |

**Lecturas**:
- **El filtro por categoría ayuda siempre**, con cualquier embedder y
  preprocesamiento (entre +0,06 y +0,15 de hit@1). Es la técnica de Advanced
  RAG con mayor efecto: sin filtro, los muebles se confunden con productos de
  otras categorías del catálogo completo (lámparas, estantes…).
- **Quitar el fondo interactúa con el embedder.** Con DINOv2 ayuda mucho
  (0,25 → 0,34 con filtro): sus features se distraen con el fondo del
  ambiente. Con DINOv3 (0,51 → 0,47) y SigLIP 2 (0,46 → 0,32) perjudica, y con
  CLIP es neutro o negativo. Hipótesis: las máscaras de SAM recortan partes del
  mueble (patas, brazos, alfombras tapadas) y los embeddings más fuertes
  aprovechan el contexto o son robustos al fondo. La hipótesis de la propuesta
  ("quitar el fondo achica la brecha de dominio") solo se cumple para DINOv2.
- **DINOv3 es el mejor embedder** en todas las combinaciones con filtro.
  **Default: DINOv3, recorte con fondo, filtro por categoría** — hit@1 0,508,
  MRR@10 0,603, hit@10 0,819. Por categoría (hit@1): silla 0,73, sillón 0,63,
  mesa 0,43, sofá 0,40, alfombra 0,23. Los intervalos de DINOv3 y SigLIP 2 (sin
  quitar fondo) se solapan: con 65 ambientes no se pueden separar con
  confianza. SigLIP 2 tiene mejor hit@5 y recall por ítem.
- Lo más difícil sigue siendo alfombras y sofás (oclusión y perspectiva).
- **Umbral**: SigLIP 2 comprime las similitudes (top-1 correcto 0,82 vs.
  incorrecto 0,77), así que su umbral (0,81) separa peor. Los umbrales
  calibrados están en `deprecated/configs/umbrales.yaml`, por colección, método de fondo y
  filtro.

## Pendientes que quedaron de la v0

- Repetir la grilla en la RTX 3070 (debería dar lo mismo salvo diferencias
  numéricas de fp16).
- Filtro por grupo de asientos (sofá + sillón + silla): el detector confunde
  silla ↔ sillón y con filtro duro eso es un error de retrieval.
- Set estricto etiquetado a mano y su evaluación.
- Evaluación de punta a punta (`datos/configs/ablaciones/e2e.yaml`): entrada del
  generador n.º 2 (imagen 1 vs. original) × modo (una llamada vs. un mueble por
  llamada), con costo y latencia.
- Ejercicio 4: reranking con VLM (antes/después sobre la mejor config de R3).

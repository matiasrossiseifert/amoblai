# Registro de experimentos

Registro continuo: cada experimento con su configuración, los resultados y lo que se aprendió.

- **v1 (actual): RAG por texto** con roomrag. Evaluaciones en `resultados/evaluacion/`, corridas
  del flujo en `resultados/amoblar/`, reporte en `resultados/reporte/` (`uv run amoblai reporte`).
- **v0 (deprecada): retrieval por imagen.** Sus corridas están en `resultados/v0_imagen/` y su
  código en `deprecated/`. Se conserva abajo porque es la línea de base de la v1 (mismo ground
  truth) y la historia de cómo se llegó al diseño actual.

# v1: RAG por texto

## Metodología del retrieval

- **Datos**: los mismos 65 ambientes de IKEA (livings y comedores con productos anotados del
  catálogo) que la v0. El catálogo son los 268 productos del alcance (275 menos 7 cuya foto no
  los muestra, ver T1), cada uno con su descripción de ocho líneas (`catalogo/descripciones.jsonl`).
- **Consultas** (`evaluacion/ikea/consultas.json`, prompt `consultas_ambiente_v1`): subagentes
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
- Comando: `uv run amoblai evaluar` (todo local y gratis; los vectores quedan en caché).

## T1: ablación del retrieval por texto

Corrida `resultados/evaluacion/20261021-141030_ablacion-texto-268` (CPU), 198 consultas.

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

(Tabla completa con todas las combinaciones en `resultados/reporte/README.md`.)
Azar con filtro por tipo: hit@1 0,020, hit@10 0,194, MRR@10 0,058.

**Camino incremental** (para la presentación, `resultados/reporte/camino_texto.png`):
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
- **Qwen3-Embedding es el mejor embedder**; BGE queda por debajo del hashing de palabras en hit@1.
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
dejaron afuera (`catalogo/correcciones.yaml`, `excluir`), mirando la forma de cada foto; 9
consultas se quedaron sin su único relevante.

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

Corrida `resultados/amoblar/prueba-alvear`. Foto que se amobla:
`ambientes_vacios/ambiente2-alvear/alvear1.jpg` (la esquina del ventanal de un living largo);
vista extra: `alvear2.jpg` (el mismo ambiente entero, desde la abertura del otro extremo), que
va a Claude en plan, choose y scene pero no al modelo de imagen. Pedido: "un living nórdico y
cálido: un sofá, un sillón para leer, una mesa ratona y una alfombra".

- **plan** (Claude Opus 5.5): "an empty, bright living room with a full-width black-framed sliding
  glass door to a balcony, white walls, white baseboards and a warm mid-tone oak plank floor".
  Pidió 4 piezas: el sofá contra "la pared larga de la derecha" (lo largo lo ve en la segunda
  foto) hasta 260 cm, el sillón de lectura junto al ventanal, la mesa ratona hasta 110 x 70 cm y la
  alfombra hasta 300 x 230 cm.
- **retrieve**: 3 candidatos por pieza, todos del kind pedido.
- **choose**: sofá blanco de brazos rectos con patas de abedul (691.249.46), sillón de cuero
  coñac con estructura curvada (391.505.88), mesa ratona cuadrada de fresno de 70 x 70 cm
  (902.976.57) y alfombra crema de pelo largo de 170 x 240 cm (302.837.81): "white, cream and
  pale wood keep the bright room calm and Scandinavian; the cognac leather and the plush rug add
  warmth, and the chair's dark bentwood frame picks up the black window frames".
- **scene**: un prompt de 219 palabras que ubica cada producto por lo que se ve (el sofá centrado
  bajo la fila de enchufes de la pared derecha, el sillón delante de la parte izquierda del
  ventanal), con las medidas del catálogo y sin mencionar la segunda foto.
- **generate**: *pendiente* (una imagen por fal, US$0,08, espera aprobación).

**Lo que mostró la prueba** (y se arregló antes de seguir):
1. **Medidas que no llegaban al LLM.** roomrag solo pasaba la medida de un candidato si tenía
   ancho, profundidad y alto; las alfombras y las mesas del dataset tienen ancho y profundidad.
   Claude recibía "size unknown", eligió una alfombra de 140 x 200 cm y escribió en el prompt
   "unos 2 x 3 m". Ahora pasan las medidas que haya; con ellas eligió la de 170 x 240.
2. **Fotos que no son del producto.** Con las medidas, eligió la LISABO de 118 x 50 cm, cuya foto
   es la de 70 x 70: se excluyeron los 7 casos así (ver T1).
3. **Los asientos no tienen medidas en el dataset** (sofás, sillones y sillas: ninguno), así que
   el límite del plan no los filtra y el prompt da su tamaño a ojo. Ver FUTURO.md.

Los intermedios descartados están en la carpeta de la corrida (`descartado_sin_medidas/`,
`descartado_lisabo_118/`). Una primera prueba sobre una foto de Wikimedia Commons se descartó
porque la foto era poco realista (posterizada y oscura).

**Costo** (Claude, `resultados/gastos.jsonl`): plan US$0,041 + choose US$0,044 + scene
US$0,042 = **US$0,13** la corrida final; con las dos repeticiones de choose y scene y la prueba
descartada, US$0,40 en total.

## Pendientes de la v1

- Evaluación de punta a punta sobre ambientes vacíos: re-identificación del producto en la imagen
  final, preservación del ambiente, cobertura (piezas con producto), costo y latencia.
- Evaluación con calificaciones (2/1/0) del top-3 para pedidos reales, como en YouSeeYouBuy
  (`roomrag/evaluate.py`): mide la relevancia para el pedido, no solo encontrar el SKU anotado.
- Ejercicio 4 (iteración): candidatos en `FUTURO.md` (una vista contra dos, filtro por tipo en
  vez de kind, consultas de estilo sin kind, medidas del ambiente).

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
- **Corridas**: `resultados/v0_imagen/corridas/*_retriever_abl-retriever-*`; tablas y
  gráficos en `resultados/v0_imagen/reporte/`. DINOv3 se sumó cuando llegó el acceso
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
- Evaluación de punta a punta (`configs/ablaciones/e2e.yaml`): entrada del
  generador n.º 2 (imagen 1 vs. original) × modo (una llamada vs. un mueble por
  llamada), con costo y latencia.
- Ejercicio 4: reranking con VLM (antes/después sobre la mejor config de R3).

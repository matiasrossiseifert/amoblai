# Registro de experimentos

Registro continuo: cada experimento con su configuración, los resultados y lo
que se aprendió. Las corridas completas (config resuelta, commit, métricas,
artefactos) están en `resultados/corridas/`; las tablas comparativas se generan
con `uv run amoblai report` en `resultados/reporte/`.

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
  (`anotaciones/estricto.jsonl`, herramienta `apps/etiquetado.py`). *Pendiente
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
- **Config**: `configs/base.yaml` (DINOv2 base, fondo quitado con SAM, filtro por
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

- **Plan**: `configs/ablaciones/retriever.yaml` — grilla completa embedder (CLIP,
  SigLIP 2, DINOv2) × quitar fondo (SAM / no) × filtro por categoría (sí / no),
  más el camino incremental E0 → E4. Mismo detector (v2) y mismos 65 ambientes
  en todas las corridas; 325 recortes con respuesta posible en cada una.
- **Corridas**: `resultados/corridas/*_retriever_abl-retriever-*`; tablas y
  gráficos en `resultados/reporte/`.

### Camino incremental (para la presentación)

| Paso | Cambio respecto del anterior | hit@1 [IC 95%] | hit@5 | hit@10 | MRR@10 | recall ítem@10 |
|---|---|---|---|---|---|---|
| E0 | naive: CLIP, recorte con fondo, sin filtro | 0,126 [0,08–0,18] | 0,255 | 0,345 | 0,179 | 0,323 |
| E1 | + quitar fondo (SAM) | 0,139 [0,09–0,19] | 0,249 | 0,320 | 0,186 | 0,341 |
| E2 | + filtro por categoría (metadata filtering) | 0,209 [0,16–0,26] | 0,459 | 0,588 | 0,317 | 0,599 |
| E3 | CLIP → DINOv2 | 0,345 [0,29–0,40] | 0,597 | 0,686 | 0,452 | 0,651 |
| E3' | CLIP → SigLIP 2 | 0,323 [0,27–0,38] | 0,615 | 0,711 | 0,445 | 0,698 |
| **E4** | SigLIP 2 **sin** quitar fondo | **0,465 [0,40–0,53]** | **0,754** | **0,809** | **0,587** | **0,763** |

Baseline aleatorio (con filtro): hit@1 0,023, hit@10 0,225, MRR@10 0,067.
Sin filtro el universo es todo el catálogo indexado (2187 SKUs): hit@1 0,0006.

### Grilla completa (hit@1 / MRR@10)

| Embedder | fondo quitado, sin filtro | fondo quitado, con filtro | con fondo, sin filtro | con fondo, con filtro |
|---|---|---|---|---|
| CLIP | 0,139 / 0,186 | 0,209 / 0,317 | 0,126 / 0,179 | 0,237 / 0,342 |
| DINOv2 | 0,262 / 0,350 | 0,345 / 0,452 | 0,099 / 0,195 | 0,252 / 0,381 |
| SigLIP 2 | 0,252 / 0,331 | 0,323 / 0,445 | 0,400 / 0,507 | **0,465 / 0,587** |

**Lecturas**:
- **El filtro por categoría ayuda siempre**, con cualquier embedder y
  preprocesamiento (entre +0,06 y +0,15 de hit@1). Es la técnica de Advanced
  RAG con mayor efecto: sin filtro, los muebles se confunden con productos de
  otras categorías del catálogo completo (lámparas, estantes…).
- **Quitar el fondo interactúa con el embedder.** Con DINOv2 ayuda mucho
  (0,25 → 0,34 con filtro): sus features autosupervisadas se distraen con el
  fondo del ambiente. Con SigLIP 2 perjudica (0,46 → 0,32) y con CLIP es
  neutro o negativo. Hipótesis: las máscaras de SAM recortan partes del mueble
  (patas, brazos, alfombras tapadas) y los embeddings alineados con texto
  aprovechan el contexto. SigLIP 2 sin fondo es mejor que SigLIP 2 con SAM en
  las cinco categorías.
- **Mejor configuración: SigLIP 2, recorte con fondo, filtro por categoría**:
  hit@1 0,465, MRR@10 0,587, recall por ítem@10 0,763. Por categoría (hit@1):
  sillón 0,88, silla 0,63, mesa 0,41, sofá 0,37, alfombra 0,21.
- **Umbral**: SigLIP 2 comprime las similitudes (top-1 correcto 0,82 vs.
  incorrecto 0,77), así que su umbral (0,81) separa peor que el de DINOv2
  (0,64 vs. 0,48). Los umbrales calibrados están en `configs/umbrales.yaml`,
  por colección y método de fondo.
- La default de `configs/base.yaml` sigue siendo DINOv2 + SAM (a la espera de
  DINOv3). Para usar la mejor: `embedding.name: siglip2` y
  `background.method: none`.

## Pendientes

- Repetir la grilla en la RTX 3070 (debería dar lo mismo salvo diferencias
  numéricas de fp16) y sumar DINOv3 cuando haya acceso.
- Probar `background.skip_categories: [rug]` con DINOv2 (las alfombras se
  segmentan mal) y el filtro por grupo de asientos.
- Set estricto etiquetado a mano y su evaluación.
- Evaluación de punta a punta (`configs/ablaciones/e2e.yaml`): entrada del
  generador n.º 2 (imagen 1 vs. original) × modo (una llamada vs. un mueble por
  llamada), con costo y latencia.
- Ejercicio 4: reranking con VLM (antes/después sobre la mejor config de R3).

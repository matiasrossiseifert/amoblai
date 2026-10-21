# Arquitectura (v1)

La v1 implementa el diagrama de la propuesta aprobada. Cada caja corresponde a
un módulo de `src/amoblai/`; las decisiones de diseño están justificadas al final.

![Diagrama de arquitectura](arquitectura.png)

(Fuente editable: `docs/arquitectura.excalidraw`.)

## Mapa diagrama → código

### Indexing pipeline (offline, una única vez): `amoblai index`

| Caja del diagrama | Módulo | Qué hace |
|---|---|---|
| Catálogo IKEA (data loading) | `data/download.py`, `data/ikea.py`, `data/safe_pickle.py` | Descarga el dataset fijado a un commit; carga los pickles con un unpickler restringido; une todo por SKU; deduplica imágenes; arma el ground truth por ambiente. |
| Ficha por SKU | `data/catalog.py` | `Product` con nombre, tipo, categoría, color, medidas (texto y cm), descripción limpia e imágenes. Se guarda una vez por SKU en `data/processed/catalog.json`. |
| Preprocesamiento | `indexing/preprocess.py` | RGB, fondo blanco y padding a cuadrado (el mismo proceso que siguen los recortes). |
| Splitting | `indexing/splitter.py` | Una entrada por imagen de producto (`id = SKU#i`) con metadata: `sku`, `category`, `raw_type`, `name`, `dimN_cm`, `size_raw`, `color`. |
| Embedding | `embeddings/hf.py`, `embeddings/registry.py` | DINOv3 (default), DINOv2, CLIP o SigLIP 2, locales con Hugging Face; fp16 en GPU, fp32 en CPU, por lotes; vectores L2-normalizados. |
| Vector DB | `vectorstore/chroma.py` | ChromaDB persistente, HNSW con espacio **coseno explícito**, una colección por modelo + preprocesamiento. |

### Consulta: `amoblai run` / `pipeline/query.py`

| Caja del diagrama | Módulo | Qué hace |
|---|---|---|
| Pre-retrieval: Generador 1 | `generation/` + `prompts.GENERATOR1` | Amobla el ambiente vacío con muebles genéricos de las 5 categorías → **imagen 1**. Transforma foto + texto en consultas del mismo dominio que el catálogo (idea tipo HyDE: generar un "documento hipotético" y buscar con él). |
| Detección y recorte | `vision/detection.py`, `vision/background.py`, `vision/crops.py` | Grounding DINO u OWLv2 con etiquetas en inglés, clasificación por frase y NMS; opcionalmente fondo quitado con SAM guiado por la caja; padding a cuadrado sobre blanco. |
| Retrieval: embedding + búsqueda ANN + filtro | `retrieval/retriever.py` | Mismo embedder que el índice; ANN coseno; **metadata filtering** por la categoría detectada; umbral calibrado por colección. |
| Post-retrieval: reranking | `retrieval/reranker.py` | Interfaz `Reranker`. En la v1, `NoopReranker` (top-1). El VLM es la iteración del Ejercicio 4. |
| Generación: Generador 2 | `generation/` + `prompts.GENERATOR2_*` | Recibe la imagen 1 **o** la foto original, las fotos de los productos elegidos y un prompt; reemplaza cada mueble genérico por el real. Dos modos: todo en una llamada, o un mueble por llamada con máscara. |
| Lista de compra | `pipeline/output.py` | JSON SKU → ficha (nombre, categoría, tipo, medidas, cantidad, similitud); precio y link solo si existen. |

### Generadores intercambiables (`generation/`)

```
ImageEditor (Protocol)            EditorService
├── OpenAIImageEditor   ─┐        ├── caché por hash(proveedor, modelo, prompt, imágenes, máscara)
├── GeminiImageEditor    ├──────▶ ├── BudgetGuard: dry-run, tope de llamadas y de USD
├── ManualImageEditor    │        └── SpendLedger: resultados/gastos.jsonl
└── DryRunEditor        ─┘
```

Contrato: la imagen devuelta tiene el tamaño de la base. Cada proveedor adapta
el tamaño a su API (`generation/geometry.py`: tamaño libre múltiplo de 16 para
gpt-image-2, tamaños fijos con letterbox, relación de aspecto para Gemini) y
vuelve a la geometría original, así las cajas de la imagen 1 siguen valiendo
sobre la foto original.

El **editor manual** prepara `resultados/generaciones/manual/<hash>/` con las
imágenes de entrada, `prompt.txt`, `INSTRUCCIONES.md` y `meta.yaml`, y espera a
que alguien deje `resultado.png` generado a mano en ChatGPT o Gemini. Registra
la app usada. Nunca automatiza las webs de chat.

### Evaluación (`eval/`) y reporte (`report/`)

- `retriever_eval.py`: hit rate@k, MRR, recall por ítem, baseline aleatorio, IC bootstrap, calibración del umbral.
- `strict_eval.py`: set etiquetado a mano (`anotaciones/estricto.jsonl`).
- `e2e_eval.py`: re-identificación, SSIM fuera de las cajas, cobertura, costo y latencia.
- `ablation.py`: planes de ablación (`configs/ablaciones/*.yaml`).
- `report/report.py`: tablas y gráficos de todas las corridas.

### Infraestructura (`infra/`)

`cache.py` (caché direccionada por contenido), `budget.py`, `usage.py` (tokens →
USD con `configs/pricing.yaml`), `runs.py` (carpeta por corrida con config,
manifest con commit de git, métricas y artefactos), `device.py`, `tracing.py`
(LangSmith opcional).

## Decisiones de diseño

**Qué se indexa: todo el catálogo.** Son 2189 imágenes (unos minutos por modelo
en CPU). Cada vector lleva `category` = una de las 5 del alcance u `other`. Si
solo se indexara el alcance, la ablación "sin filtro por categoría" no tendría
distractores y no mediría nada. Indexando todo, mide cuánto aporta el metadata
filtering, y sumar categorías no obliga a reindexar. El alcance se aplica en el
prompt del generador n.º 1, en las etiquetas del detector y en el filtro.

**Mapeo de categorías explícito** (`configs/categories.yaml`): los 677 valores de
`type` del dataset se reducen a 5 categorías con una lista revisable; los
dudosos excluidos están documentados con su motivo. `amoblai categories` genera
`resultados/mapeo_categorias.md` con los conteos.

**Splitting = una imagen.** La unidad recuperable es una foto de producto, no el
producto: hoy hay 2 SKUs con dos fotos distintas (dos vectores), y el esquema
soporta más vistas por scraping. La ficha completa vive aparte, una vez por SKU
(patrón multi-vector / parent document).

**Preprocesamiento simétrico.** Catálogo y recortes pasan por el mismo proceso
(fondo blanco, padding a cuadrado, sin center-crop). Sin el padding, el
center-crop de los procesadores corta los extremos de un sofá.

**Quitar el fondo: opcional y decidido por la ablación.** La hipótesis de la
propuesta era que quitarlo achica la brecha de dominio con el catálogo. La
ablación (docs/EXPERIMENTOS.md) muestra que depende del embedder: ayuda a
DINOv2 pero perjudica a DINOv3 y SigLIP 2, así que el default es no quitarlo.
Cuando se quita, se usa SAM guiado por la caja: un recorte de un living tiene varios
objetos destacados; un modelo de objeto saliente puede elegir el equivocado. Con
la caja del detector como prompt, la máscara apunta al mueble detectado. Se
limpia (componente mayor dentro de la caja, huecos rellenos). Las alfombras,
tapadas por otros muebles, salen mal segmentadas: `background.skip_categories`
permite no quitarles el fondo (experimento pendiente).

**Coseno explícito + vectores normalizados.** El default de Chroma es L2; se
configura `cosine` y además se normalizan los vectores, así ambos criterios
ordenan igual.

**Umbral calibrado por colección.** Las escalas de coseno de DINO, CLIP y SigLIP
no son comparables. `amoblai eval retriever --calibrate` elige el umbral que
maximiza F1 de "aceptar ⇔ el top-1 es correcto" sobre los ambientes de IKEA (los
recortes sin respuesta posible cuentan como negativos) y lo guarda en
`configs/umbrales.yaml`.

**Advanced RAG en la v1.** (1) Transformación de la consulta en el
pre-retrieval: el generador n.º 1 convierte foto + texto en recortes del mismo
dominio que los documentos. (2) Metadata filtering por categoría. El reranking
con un VLM es la iteración del Ejercicio 4.

**LangChain: no; LangSmith: sí.** El retrieval es imagen → imagen con embeddings
propios de Hugging Face; los wrappers de LangChain para Chroma y multimodal
agregan una capa sin aportar (habría que envolver el embedder y perder el
control de lotes, fp16 y metadata). Las etapas se instrumentan con `@traceable`
de LangSmith, que no requiere LangChain: trazas con entradas resumidas (sin subir
imágenes), tiempos y salidas. Se activa con `LANGSMITH_TRACING=true` en `.env`.

**Caché y costos.** Toda generación pasa por `EditorService`: si la misma
entrada ya se generó (por API o a mano), se reusa sin pagar. Las imágenes
generadas viven en `resultados/generaciones/` y se commitean, así el equipo
comparte un mismo set de imágenes 1 entre experimentos y máquinas. Las cachés
recomputables (detecciones, máscaras) quedan en `data/cache/`.

**Reproducibilidad.** Dataset fijado a un commit, `uv.lock`, config resuelta y
commit de git en cada corrida, semillas fijas para el bootstrap.

## Limitaciones conocidas de la v1

- El ground truth de IKEA no tiene posiciones: la métrica del retriever es permisiva (ver `docs/EXPERIMENTOS.md`).
- Las alfombras se segmentan mal (quedan tapadas por otros muebles).
- El detector confunde silla ↔ sillón ↔ sofá; con filtro duro, un error del detector es un error del retrieval (ver FUTURO.md: filtro por grupo).
- Después del generador n.º 1 el texto del usuario no influye en la elección del producto: lo resolvería el reranking con VLM (Ejercicio 4).
- Las máscaras de gpt-image son orientativas y Gemini no recibe máscara: sin compositing, el generador puede retocar fuera de las cajas (se mide con el SSIM).

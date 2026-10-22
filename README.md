# amoblai

Amoblado virtual con RAG sobre un catálogo real de muebles. Trabajo práctico de 73.69 Large
Language Models (ITBA, 2026).

**Entrada:** una foto del ambiente (y, opcional, otra foto del mismo ambiente desde otro ángulo) y
el pedido en texto libre ("un living nórdico y cálido"). **Salida:** los productos del catálogo
IKEA que hacen falta (lista de compra) y la foto del ambiente con ellos.

## Cómo funciona

```mermaid
flowchart LR
  subgraph IDX["Indexing pipeline (una vez)"]
    A["Catálogo IKEA<br/>268 productos"] --> B["Descripciones<br/>en 8 líneas"]
    B --> E["Embedding<br/>Qwen3"]
    E --> V[("ChromaDB<br/>HNSW + metadata")]
  end
  U["Foto + pedido"] --> P["plan<br/>query rewriting"]
  P --> R["retrieve<br/>filtros + coseno"]
  V --> R
  R --> C["choose<br/>reranking con VLM"]
  C --> S["scene<br/>prompt de imagen"]
  S --> G["generate<br/>Nano Banana 2"]
  C --> L["Lista de compra"]
  G --> F["Ambiente amoblado"]
```

| Etapa | Código (`src/amoblai/`) | Qué hace |
|---|---|---|
| Data loading | `dataset/` | Descarga el dataset IKEA fijado a un commit, lo carga con un unpickler restringido y une todo por SKU. |
| Preprocesamiento | `catalog/` | Los productos del alcance (sofá, sillón, silla, mesa, alfombra) con su tipo, kind y medidas; correcciones y exclusiones a mano. |
| Splitting | `datos/catalogo/descripciones.jsonl` | Un documento por producto (la descripción es corta): ocho líneas fijas (Type, Use, Style, Materials, Colors, Shape, Feel, Goes with), escritas por subagentes mirando la foto. |
| Embedding y base vectorial | `rag/embed.py`, `rag/store.py`, `rag/index.py` | Qwen3-Embedding (local) → ChromaDB: vector, descripción y metadata por producto, índice HNSW en espacio coseno. |
| Pre-retrieval: query rewriting | `furnish/steps.py` (`plan`) | Claude lee la foto y el pedido, decide las piezas, su kind y su tamaño máximo, y escribe el producto ideal en las mismas ocho líneas que el catálogo. |
| Retrieval | `rag/search.py`, `rag/filters.py` | Filtros duros de metadata (kind, medidas) como `where` de ChromaDB, después los k más cercanos por coseno. |
| Post-retrieval: reranking | `furnish/steps.py` (`choose`) | Claude mira la foto y los candidatos de cada pieza y elige la mejor combinación. |
| Generación | `furnish/steps.py` (`scene`), `furnish/image_models.py` | Claude escribe el prompt; el modelo de imagen (Nano Banana 2 por fal, gpt-image o a mano) pone los productos en la foto. |
| Evaluación | `evaluation/` | Métricas sobre 65 ambientes IKEA anotados y las ablaciones de `datos/configs/ablaciones/`. |

## Resultados

Retrieval sobre los 65 livings y comedores de IKEA con productos anotados (198 consultas con
respuesta; IC 95% bootstrap por ambiente). Tablas completas en
`datos/resultados/reporte/reporte.md`.

| Configuración | hit@1 | hit@10 | MRR@10 |
|---|---|---|---|
| Naive: texto del vendedor, hashing de palabras, sin filtro | 0,146 | 0,429 | 0,212 |
| + nuestras descripciones de ocho líneas | 0,586 | 0,929 | 0,712 |
| + Qwen3-Embedding, filtro por tipo, ChromaDB | 0,636 | 0,914 | 0,737 |
| **+ reranking con VLM (Claude Opus 5.5, top-10)** | **0,803** | 0,914 | **0,847** |
| Azar | 0,020 | 0,194 | 0,058 |

- **Query rewriting:** con la consulta en las ocho líneas del catálogo, hit@1 da 0,636. Con solo
  la línea Type cae a 0,353, y con solo el nombre del mueble (sin reescribir) a 0,040.
- **Base vectorial:** ChromaDB (HNSW) y la búsqueda exacta dan el mismo ranking en las 228
  consultas.
- **Reranking:** Opus mira las fotos del top-10 y sube hit@1 de 0,636 a 0,803 (US$0,020 por
  consulta).
- **Texto contra imagen:** con el mismo ground truth y el catálogo completo, el retrieval por
  texto da 0,618 de hit@1 y el mejor retrieval por imagen de la v0 (DINOv3) da 0,508.

![Camino incremental](datos/resultados/reporte/camino_texto.png)
![Base vectorial, query rewriting y reranking](datos/resultados/reporte/avanzado.png)

Una corrida completa del flujo cuesta unos US$0,21: plan, choose y scene con Claude Opus 5.5
(US$0,13) y la imagen con Nano Banana 2 (US$0,08). Ejemplo:
`datos/resultados/amoblar/prueba-alvear2/antes_despues.jpg`.

## Instalación

Requisitos: Python 3.11+ y [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra cpu --group dev --group apps     # sin GPU NVIDIA
uv sync --extra gpu --group dev --group apps     # con GPU NVIDIA (CUDA 12.6)
cp .env.example .env                             # ANTHROPIC_API_KEY, FAL_KEY, OPENAI_API_KEY
```

## Uso

```bash
uv run amoblai data download     # dataset IKEA (Tautkute et al., 2017) en datos/dataset/
uv run amoblai catalogo          # el catálogo: productos, descripciones, kinds, correcciones
uv run amoblai indice            # descripciones → embeddings → ChromaDB (en caché, gratis)
uv run amoblai buscar "Type: armchair, lounge reading chair
Materials: bentwood, leather" --kind armchair

# El flujo completo (se retoma donde quedó; nada se paga dos veces)
uv run amoblai amoblar datos/ambientes_vacios/ambiente2-alvear/alvear2.jpg "un living nórdico y cálido" \
    --vista datos/ambientes_vacios/ambiente2-alvear/alvear1.jpg \
    --set 'budget.allow_paid_steps=[furnish.plan, furnish.choose, furnish.scene]'   # imagen a mano
uv run amoblai amoblar foto.jpg "un comedor para seis" --generador nano_banana_2 --pagar

# Evaluación: cada ablación es un YAML de datos/configs/ablaciones/
uv run amoblai evaluar                                                        # gratis, local
uv run amoblai evaluar --ablacion datos/configs/ablaciones/reranking.yaml --pagar
uv run amoblai reporte           # tablas y gráficos en datos/resultados/reporte/
uv run amoblai gastos            # lo gastado por cuenta contra sus topes
```

La webapp muestra cada paso del flujo, a medida que se hace:

```bash
uv run --group apps python apps/amoblar.py      # http://127.0.0.1:7860
```

**Costos y topes.** Las llamadas pagas se rechazan salvo que se habiliten (`--pagar`,
`budget.allow_paid` o `budget.allow_paid_steps`) y nunca superan el tope de su cuenta
(`budget.accounts` en `datos/configs/amoblai.yaml`). Cada una queda en
`datos/resultados/gastos.jsonl`. El generador `manual` (default) deja una carpeta con las
imágenes y el prompt para generar a mano en ChatGPT o Gemini.

## Estructura

```
src/amoblai/          el código, un subpaquete por etapa (ver la tabla de arriba)
  paths.py            dónde está cada cosa de datos/
apps/                 la webapp (Gradio)
tests/                pytest sin red: dataset sintético; Claude y fal simulados
datos/
  configs/            amoblai.yaml, categories.yaml, ablaciones/*.yaml
  catalogo/           descripciones (por lote), kinds, correcciones, ikea.yaml
  evaluacion_ikea/    consultas de evaluación sobre los ambientes IKEA
  ambientes_vacios/   fotos de ambientes (dos vistas de cada uno)
  resultados/         corridas del flujo, evaluaciones, reporte, gastos; v0_imagen/
  dataset/ procesados/ cache/    (no se commitean: se regeneran con la CLI)
deprecated/           la v0 (retrieval por imagen), completa
```

## Desarrollo

```bash
uv run pytest
uv run ruff check src tests apps && uv run ruff format --check src tests apps
```

La v0 (retrieval por imagen: Grounding DINO, SAM, DINOv3) sigue en `deprecated/`, con sus
propios tests:

```bash
uv sync --extra cpu --extra imagen --group dev
PYTHONPATH=deprecated uv run pytest -c deprecated/pytest.ini deprecated/tests
PYTHONPATH=deprecated uv run python -m amoblai_imagen.cli --help
```

## Créditos

- **Dataset:** I. Tautkute et al., *What Looks Good with my Sofa: Multimodal Search Engine for
  Interior Design*, FedCSIS 2017 (imágenes de IKEA, uso no comercial).
- **Fotos de ambientes** (`datos/ambientes_vacios/`): avisos inmobiliarios que aportó el equipo.
  Se usan solo para probar el sistema en este repositorio privado; ni ellas ni las imágenes
  generadas a partir de ellas se publican.

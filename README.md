# amoblai

Amoblado virtual con RAG sobre un catálogo real de muebles. Trabajo práctico de 73.69 Large
Language Models (ITBA, 2026).

**Entrada:** una foto del ambiente y el pedido en texto libre ("un living nórdico y cálido").
**Salida:** los productos del catálogo IKEA que hacen falta (lista de compra) y la foto del
ambiente con ellos.

El catálogo es la memoria no paramétrica. Un LLM con visión lee la foto y el pedido y escribe,
para cada mueble que hace falta, el producto ideal en el mismo formato que las descripciones
del catálogo (pre-retrieval); la búsqueda aplica filtros duros (tipo, medidas) y trae los más
cercanos por embeddings (retrieval); el LLM elige la mejor combinación mirando las fotos
(post-retrieval) y escribe el prompt con el que un modelo de imagen pone esos productos en la
foto. Detalle en [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

El núcleo RAG es `roomrag` (`desde_youseeyoubuy/`), compartido con el proyecto YouSeeYouBuy. La
primera versión del TP, que recuperaba por imagen, está en [deprecated/](deprecated/).

## Resultados

Retrieval sobre 65 livings y comedores de IKEA con productos anotados (198 consultas con
respuesta; IC 95% bootstrap por ambiente). Detalle y lecturas en
[docs/EXPERIMENTOS.md](docs/EXPERIMENTOS.md):

| Configuración | hit@1 | hit@10 | MRR@10 |
|---|---|---|---|
| Naive: texto del vendedor, hashing de palabras, sin filtro | 0,146 | 0,434 | 0,213 |
| + nuestras descripciones de ocho líneas | 0,586 | 0,929 | 0,712 |
| **+ Qwen3-Embedding, filtro por tipo** | **0,636** | 0,914 | **0,737** |
| Azar | 0,020 | 0,194 | 0,058 |

Con el catálogo completo de 275 productos (el mismo que la v0), el texto da 0,618 de hit@1
contra 0,508 del mejor retrieval por imagen (DINOv3), con el mismo ground truth.

![Camino incremental](resultados/reporte/camino_texto.png)

Una corrida completa del flujo cuesta unos US$0,21: plan, choose y scene con Claude Opus 5.5
(US$0,13) y la imagen con Nano Banana 2 (US$0,08). Ejemplo en
`resultados/amoblar/prueba-alvear2/antes_despues.jpg` (detalle en docs/EXPERIMENTOS.md, T2).

## Instalación

Requisitos: Python 3.11+ y [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra cpu --group dev --group apps     # sin GPU NVIDIA
uv sync --extra gpu --group dev --group apps     # con GPU NVIDIA (CUDA 12.6)
cp .env.example .env                             # ANTHROPIC_API_KEY, FAL_KEY, OPENAI_API_KEY
```

Para la v0 (deprecated/) se suma `--extra imagen`.

## Uso

```bash
uv run amoblai data download     # dataset IKEA (Tautkute et al., 2017) en data/raw/ikea
uv run amoblai catalogo          # catálogo de roomrag: productos, descripciones, kinds
uv run amoblai indice            # descripciones → embeddings (en caché, gratis)
uv run amoblai buscar "Type: coffee table, round
Materials: light oak" --kind "coffee table"

# El flujo completo (se retoma donde quedó; nada se paga dos veces)
uv run amoblai amoblar ambientes_vacios/ambiente2-alvear/alvear1.jpg "un living nórdico y cálido" \
    --vista ambientes_vacios/ambiente2-alvear/alvear2.jpg \
    --set 'budget.allow_paid_steps=[furnish.plan, furnish.choose, furnish.scene]'   # Claude sí, imagen a mano
uv run amoblai amoblar foto.jpg "un comedor para seis" --generador nano_banana_2 --pagar

uv run amoblai evaluar           # ablación del retrieval (local, gratis)
uv run amoblai reporte           # tablas y gráficos en resultados/reporte/
uv run amoblai gastos            # lo gastado por cuenta contra sus topes
```

La webapp de prueba muestra cada paso (ver [apps/README.md](apps/README.md)):

```bash
uv run --group apps python apps/amoblar.py      # http://127.0.0.1:7860
```

### Costos y topes

Las llamadas pagas se rechazan salvo que se habiliten (`--pagar`, `budget.allow_paid` o
`budget.allow_paid_steps`) y nunca superan el tope de su cuenta en `configs/amoblai.yaml`
(`budget.accounts`). Cada una queda en `resultados/gastos.jsonl`. El generador `manual` (default)
deja una carpeta con las imágenes y el prompt para generar a mano en ChatGPT o Gemini.

## Estructura

```
configs/            amoblai.yaml (roomrag: catálogo, embedders, LLM, generadores, topes),
                    categories.yaml (type de IKEA → alcance)
catalogo/           ikea.yaml, descripciones (escritas por subagentes), kinds, correcciones
evaluacion/ikea/    consultas de evaluación por ambiente (escritas por subagentes)
src/amoblai/        lo propio del TP: data loading del dataset, catálogo, validadores,
                    generadores (fal, OpenAI), evaluación, reporte, CLI
desde_youseeyoubuy/ roomrag (el núcleo RAG compartido), su LEEME y CAMBIOS.md
apps/               la webapp de prueba
ambientes_vacios/   fotos de ambientes vacíos, dos vistas de cada uno (ver CREDITOS.md)
resultados/         corridas, evaluaciones, reporte y gastos (se commitea); v0_imagen/
deprecated/         la v0 (retrieval por imagen), completa
docs/               ARQUITECTURA.md, EXPERIMENTOS.md, propuesta y diagrama original
tests/              pytest sin red (dataset sintético; Claude y fal simulados)
```

## Desarrollo

```bash
uv run pytest                                   # tests del TP y de roomrag
PYTHONPATH=deprecated uv run pytest -c deprecated/pytest.ini deprecated/tests   # los de la v0
uv run ruff check src tests apps && uv run ruff format --check src tests apps
```

Mejoras fuera del alcance: [FUTURO.md](FUTURO.md).

## Créditos

Dataset: I. Tautkute et al., *What Looks Good with my Sofa: Multimodal Search Engine for
Interior Design*, FedCSIS 2017 (imágenes de IKEA, uso no comercial). Núcleo RAG: roomrag, de
YouSeeYouBuy. Fotos de terceros: `ambientes_vacios/CREDITOS.md`.

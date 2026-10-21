# El núcleo RAG de YouSeeYouBuy, para el TP de LLM

Esta carpeta la armó el Claude que trabaja en YouSeeYouBuy (`/home/fer/youseeyoubuy`), a pedido
de los fundadores, para el Claude que trabaja en este TP. Leela entera antes de tocar código.

## Contexto

- **YouSeeYouBuy** es el proyecto de los fundadores: pone muebles reales, a su tamaño real, en
  la foto de un ambiente. Usa 3D (el modelo del mueble a escala), el escaneo del cuarto con
  LiDAR, un render y un pase de realismo con un modelo de imagen. Todo eso no llega a estar
  listo para esta materia, y no es lo que la materia evalúa.
- Lo que importa para la materia es el **RAG**: un catálogo de muebles descripto en texto,
  embeddings sobre esas descripciones, filtros duros y LLMs que planifican y eligen. Eso es
  `roomrag/`, un paquete sin nada de 3D.
- **Es el mismo código que usa YouSeeYouBuy** (allá vive en `pipeline/roomrag/`). YouSeeYouBuy
  corre los mismos pasos y, en vez de los dos últimos de abajo (`scene` y `generate`), le suma el
  suyo, que ubica el 3D. Ese cambio es una línea de su config (`furnish.steps`). La idea es que el
  núcleo sea intercambiable: YouSeeYouBuy contiene a este TP, más el 3D.
- Te lo pasan para que armes, siguiendo la consigna de la materia (`docs/consigna.pdf`), el flujo
  de abajo. Los experimentos, las métricas, las presentaciones, las claves de API de las
  profesoras y todo lo propio de la materia los decidís vos con el grupo.
- Ojo: este TP hoy recupera por imagen (recortes de un ambiente amoblado + DINOv3). Este flujo
  recupera por texto: un LLM escribe qué hace falta y se busca sobre las descripciones. Cómo
  convive con lo que ya está (reemplazarlo, compararlo, combinarlo) lo hablás con el grupo.

## El flujo a armar

Entrada: una foto del ambiente y el pedido del usuario en texto libre ("un living nórdico",
"agregame una silla que combine con el escritorio").

1. **plan** (LLM con visión): lee la foto y el pedido como un decorador de interiores. Decide qué
   muebles hacen falta (uno a cuatro, el más importante primero; los que el usuario nombró, tal
   cual: una silla no es un sillón). Para cada uno escribe:
   - para qué es (`kinds`: un tipo fino de una lista fija, `roomrag/kinds.py`; es un filtro duro);
   - lo máximo que puede medir, si el lugar lo limita;
   - la **consulta**: el producto ideal escrito en las mismas ocho líneas que las descripciones
     del catálogo, para que la búsqueda compare cosas comparables.

   No se elige dónde va cada mueble con precisión: eso es lo del 3D.
2. **retrieve** (el RAG): por cada mueble, primero los filtros duros (tipo, que entre) y después
   las descripciones más cercanas a la consulta (coseno entre embeddings). Trae 3 candidatos por
   mueble. Si el catálogo no tiene nada para un mueble, ese queda anotado (`empty`) y se sigue
   con los demás.
3. **choose** (LLM con visión): ve la foto del ambiente y las fotos de los candidatos (3 por cada
   cosa pedida) y elige la mejor combinación: uno por mueble, que queden bien juntos y con lo que
   ya hay. No elige el mejor de cada uno por separado.
4. **scene** (LLM con visión): arma el prompt para el modelo de imagen. Dice que la imagen 1 es el
   ambiente y cada imagen siguiente es un producto, dónde va cada uno (junto a qué, contra qué
   pared), hacia dónde mira, qué tamaño tiene al lado de lo que ya hay, y que todo lo demás quede
   igual.
5. **generate** (modelo de imagen): recibe la foto del ambiente, las fotos de los productos
   elegidos y ese prompt, y devuelve el ambiente amoblado.

Para pensar o probar después (no es indispensable ahora): consultas **genéricas o de estilo**,
donde el LLM no decide el tipo de mueble y el RAG trae lo pertinente. Puede traer cosas que el
LLM no pensaría, como una funda de silla o un objeto de decoración poco típico. El código ya lo
permite: una pieza sin `kinds` busca en todo el catálogo solo por la consulta. Falta un prompt de
plan que las escriba así y ver si sirve.

## Qué hay acá

```
roomrag/                 el paquete (solo imports relativos: se puede mover adentro de src/)
  __init__.py            resumen del flujo y de cada módulo
  config.py              la config YAML (extends, --set), cada campo comentado
  catalog.py             qué productos hay: carpetas con product.json o archivos JSON-lines
  kinds.py               los tipos finos ("desk chair", "coffee table"...): editalo para IKEA
  filters.py             filtros duros: tipo, kind, medidas máximas
  describe.py            las descripciones: escritas de antemano, del vendedor, o por un LLM
  embed.py               texto -> vector: hashing (gratis), modelo local (HF), OpenAI
  index.py               arma y cachea el índice (descripciones + vectores)
  search.py              filtros, después los k más cercanos (o todo el catálogo, para comparar)
  llm.py                 el LLM: anthropic (Claude) u openai_chat (cualquier API compatible)
  steps.py               plan, retrieve, choose, scene, generate
  generate.py            el modelo de imagen: manual incluido; los de API se enchufan por config
  flow.py                la corrida: un archivo por paso, se retoma donde quedó
  evaluate.py            el test de búsqueda: ok@k, good@k, first_ok, nDCG@k
  http.py, budget.py, prompts.py   reintentos, el tope de gasto, las plantillas
  __main__.py            python -m roomrag build | search | run
  prompts/               search_query_v2 (plan), choose_combination_v1, scene_prompt_v1,
                         describe_product_v2 (las descripciones)
tests/                   pytest sin red: test_roomrag.py, test_roomrag_eval.py
ejemplo/config.yaml      una config para el TP, comentada
ejemplo/descripciones_muestra.jsonl   3 descripciones nuestras, para ver el formato
```

Los tests pasan en el entorno de este repo (`.venv`), sin instalar nada (mientras `roomrag` no
esté en `src/`, el isort de ruff pide agrupar sus imports con los de terceros en los tests):

```bash
PYTHONPATH=desde_youseeyoubuy uv run --no-sync python -m pytest -q desde_youseeyoubuy/tests
```

## Cómo se usa

Dependencias: numpy, pydantic 2, pyyaml, httpx y pillow, que ya están en este repo. Para los
embeddings locales hacen falta además torch y transformers.

Para integrarlo, lo más simple es mover `roomrag/` a `src/roomrag/` y sumarlo al build
(`[tool.hatch.build.targets.wheel] packages = ["src/amoblai", "src/roomrag"]`). Como solo usa
imports relativos, también funciona como `src/amoblai/roomrag/`, pero entonces hay que cambiar
los imports de los tests.

```bash
# desde tp-llm/, con roomrag importable (ver arriba)
python -m roomrag build --config desde_youseeyoubuy/ejemplo/config.yaml   # lee las descripciones y vectoriza
python -m roomrag search "three-seat sofa, green velvet" --config ...       # probar el índice
python -m roomrag run foto.jpg "un living nórdico" --config ... --set budget.allow_paid=true
```

Desde Python:

```python
from pathlib import Path

from roomrag.config import load_config
from roomrag.flow import run_flow

cfg = load_config("desde_youseeyoubuy/ejemplo/config.yaml")
run = run_flow("foto.jpg", "un living nórdico", cfg, out=Path("resultados/roomrag/prueba"))
run.data["plan"], run.data["choose"], run.chosen()  # lo que salió de cada paso
```

Cada paso escribe su archivo en la carpeta de la corrida: `1_searches.json`,
`2_candidates.json` (y `2_candidates*.jpg`, los candidatos numerados), `3_choice.json`,
`4_scene.json`, `5_image.json` y `final.png`. Si el archivo de un paso existe, ese paso no se
vuelve a hacer, así que una corrida se retoma donde quedó y nada se paga dos veces.

El generador `manual` deja en `manual/` las imágenes en orden y el prompt, para pegarlos en
ChatGPT o Gemini. La imagen que devuelvan se guarda ahí como `result.png` y se vuelve a correr.

Para agregar un paso propio, se pone en `furnish.steps` como `"paquete.modulo:funcion"` (recibe
el `Run`, devuelve un dict). Así es como YouSeeYouBuy agrega su 3D.

## El catálogo

Los muebles pueden ser los de este TP (IKEA) o los nuestros. Lo natural es IKEA, que ya está
bajado y procesado acá (`data/processed/catalog.json`).

Un catálogo es un YAML (`roomrag/catalog.py` explica todas las formas). Para IKEA conviene un
JSON-lines con un producto por línea:

```json
{"id": "<sku>", "name": "...", "category": "chair", "kind": "dining chair",
 "dimensions_cm": {"width": 45, "depth": 52, "height": 81},
 "photos": ["data/raw/ikea/images/chair/<archivo>.jpg"], "color": "...", "type_ikea": "Chair"}
```

```yaml
name: ikea
items: [data/processed/items_roomrag.jsonl]
```

- `category` es el tipo grueso que usamos nosotros: chair, sofa, table, desk, bed, shelf,
  cabinet, dresser, ottoman, stool, bench.
- `kind` es el tipo fino de `roomrag/kinds.py`. IKEA trae cosas que no están en la lista
  (alfombras, lámparas, macetas, decoración): sumalas a `KINDS`. El prompt del plan las lista
  solo, con `kinds_text()`.
- `dimensions_cm` va solo cuando no es ambiguo (en muebles, IKEA da ancho x profundidad x alto).
  Sin medidas, los filtros de tamaño lo dejan pasar.
- Las fotos son relativas a `root`.
- Cualquier otro campo (color, link, precio) queda como metadata.

Los nuestros son 708 productos: 700 de Amazon Berkeley Objects (licencia CC BY-NC 4.0) y 8 de
Artek y HAY. Sus descripciones están en
`/home/fer/youseeyoubuy/configs/catalogs/descriptions/{abo,brands}.jsonl` y las fotos en
`/home/fer/youseeyoubuy/data/catalog/` (no las copié). El catálogo es
`configs/catalogs/main.yaml` de ese repo.

## Las descripciones: las escribís vos, sin API

Los embeddings son sobre las descripciones, no sobre el texto del vendedor. Las nuestras, 700, no
las escribió ninguna API: las escribió Claude en Claude Code mirando las fotos de cada producto.
Hacé lo mismo con el catálogo que usen:

1. El formato está en `roomrag/prompts/describe_product_v2.md`. Leelo entero, con sus dos
   ejemplos:
   - ocho líneas en este orden: Type, Use, Style, Materials, Colors, Shape, Feel, Goes with;
   - en inglés, frases cortas, de 60 a 90 palabras en total;
   - Style sale de una lista fija;
   - sin marca, precio ni medidas (el tamaño va por filtro), y sin decir lo que no es: los
     embeddings no leen el "no".
2. Por cada producto, mirá sus fotos (hasta 4; la principal primero) y escribí la descripción
   con ese prompt, completado con su nombre, tipo y medidas. Si el nombre y las fotos no
   coinciden, mandan las fotos. Nosotros lo hicimos con subagentes, de a unos 25 productos cada
   uno. Dos se escribieron a mano como ejemplos del prompt.
3. Una línea JSON por producto en `data/processed/descripciones.jsonl`, con el formato de
   `ejemplo/descripciones_muestra.jsonl`:

   ```json
   {"id": "<sku>", "text": "Type: ...\nUse: ...\n...", "by": "claude-code <modelo>", "prompt": "describe_product_v2"}
   ```

4. En la misma pasada, asigná el `kind` de cada producto mirando la foto. Va en el JSON-lines del
   catálogo, o en un `kinds_file` `{id: kind}`. Conviene revisar a mano las sillas y los sillones:
   es donde más se equivoca un tipo automático.
5. Si un producto tiene mal el tipo, se corrige en el YAML del catálogo (`categories:`), porque
   el tipo es un filtro.
6. Revisá que cada descripción tenga las ocho líneas, en orden y en el largo pedido. Después
   corré `python -m roomrag build` con `describer: written`. Un producto sin descripción queda
   afuera del índice y se avisa.

## El LLM y el modelo de imagen

- **LLM** (`furnish.llm`, `roomrag/llm.py`):
  - `anthropic` es Claude, el que usamos nosotros (Opus 5.5 para planificar y elegir).
  - `openai_chat` sirve para OpenAI o cualquier API compatible con Chat Completions. Se cambian
    `base_url` y `api_key_env`; Gemini, por ejemplo, tiene un endpoint compatible.
  - Se usa para los tres pasos con LLM: plan, choose y scene.
  - El costo sale de los tokens que devuelve la API y de los precios de la tabla `models`, así
    que hay que ponerle los reales.
  - Si las claves de las profesoras son de otro tipo de API, se agrega una clase en `llm.py`
    (unas 40 líneas, como `OpenAIChat`) y se registra en `KINDS`.
- **Modelo de imagen** (`furnish.generators`, `roomrag/generate.py`):
  - Viene `manual`.
  - Para uno por API se escribe una clase con `estimate_cost(images)` y
    `generate(prompt, images, out)` y se nombra en la config como `kind: "paquete.modulo:Clase"`.
    Este TP ya tiene generadores de OpenAI y Gemini en `src/amoblai/generation/`: alcanza con
    envolver uno.
  - YouSeeYouBuy hace lo mismo con los suyos (`ysyb/furnish/generate.py`).
- **Lo que aprendimos con modelos de imagen**, que puede servirte:
  - Lo primero que pierden es la forma del mueble. El prompt de `scene` ya pide cada producto
    "exactamente como en su foto".
  - En nuestra prueba, Gemini (Nano Banana, también en la app gratis) conservó la forma mejor
    que gpt-image de OpenAI.
  - Nano Banana 2 y 2.1 con `aspect_ratio: auto` devuelven la proporción de la foto. Pro con
    `auto` reencuadró todo a un cuadrado; hay que pasarle la foto rellenada hasta una proporción
    que acepte.
  - Una sola imagen por modelo no mide la variación entre corridas.

## Gasto y caché

- Toda llamada paga pasa por un tope antes de salir y queda registrada en un ledger JSON-lines
  (`budget.*`, `roomrag/budget.py`).
- Con `budget.allow_paid: false`, que es el valor por defecto, las llamadas pagas se rechazan.
  Se habilitan a propósito con `--set budget.allow_paid=true`.
- Las descripciones y los vectores se cachean en `cache_dir/rag/` y los pasos en la carpeta de
  cada corrida. Repetir no vuelve a pagar.

## Lo que medimos en YouSeeYouBuy (puntos de partida)

Test de búsqueda (`roomrag/evaluate.py`), sobre nuestro catálogo de 700:

- 24 pedidos escritos como los escribe la gente, la mayoría sin nombrar un mueble.
- De ahí salen 40 búsquedas.
- Se calificó cada top-3 mirando la foto del producto, no nuestro texto: 2 bueno, 1 aceptable,
  0 mal. Fueron 350 calificaciones.

| Método | ok@3 | good@3 | first ok | nDCG@3 |
|---|---|---|---|---|
| OpenAI text-embedding-3-large, nuestra descripción, filtros | 0,92 | 0,64 | 0,95 | 0,82 |
| Qwen3-Embedding-0.6B (local), igual | 0,85 | 0,57 | 0,93 | 0,75 |
| BGE-base (local), igual | 0,84 | 0,53 | 0,88 | 0,69 |
| BGE, sin filtros | 0,73 | 0,52 | 0,78 | 0,62 |
| BGE, texto del vendedor en vez del nuestro | 0,78 | 0,41 | 0,80 | 0,60 |
| hashing de palabras (sin modelo) | 0,83 | 0,55 | 0,88 | 0,71 |

Qué sacamos de ahí:

- El tipo y el tamaño van como filtros, no como palabras en el vector.
- Nuestras ocho líneas le ganan al texto del vendedor, y el nombre de la tienda no suma.
- Lo que más falla no es el vector: son tipos demasiado gruesos (por eso existen los `kinds`),
  un "tiene que ser verde" que el usuario dice, y un plan que pide algo que el catálogo no tiene.
- Antes de que `kinds` fuera filtro, "agregame una silla" en un estudio con escritorio traía
  sillones. Con el filtro y el prompt de diseñador, trae sillas de escritorio.

Ablaciones que salen solas de la config:

- con y sin filtros;
- con distintos embedders;
- `mode: whole_catalog` (todo el catálogo al LLM) contra `rag` (los k más cercanos);
- nuestra descripción contra la del vendedor (`describer: fields`);
- cuántos candidatos ve el LLM.

## Para que siga siendo intercambiable

- `roomrag/` no importa nada de `amoblai` (ni de YouSeeYouBuy). Un test lo verifica. Lo propio
  del TP va afuera, en `src/amoblai/`: los generadores, la conversión del catálogo, los
  experimentos, las apps.
- Si mejorás `roomrag/` (un bug, un paso nuevo, un prompt mejor), mantenelo genérico y anotalo en
  `CAMBIOS.md` en esta carpeta, así vuelve a YouSeeYouBuy.
- YouSeeYouBuy actualiza esta carpeta con `scripts/export_roomrag.sh`, que pisa `roomrag/` y
  `tests/` (no este LEEME ni `ejemplo/`). Por eso los cambios hechos acá tienen que estar
  anotados antes de una actualización.

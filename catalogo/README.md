# Catálogo (IKEA, alcance de la v1)

Lo que lee roomrag para el índice. Se regenera con `uv run amoblai catalogo` (necesita el
dataset bajado: `uv run amoblai data download`).

| Archivo | Qué es | Quién lo escribe |
|---|---|---|
| `ikea.yaml` | El catálogo de roomrag: los productos (`data/processed/items_roomrag.jsonl`), sus kinds y los tipos corregidos | `amoblai catalogo` |
| `descripciones/lote_NN.jsonl` | Las descripciones de ocho líneas y el kind de cada producto, por lote | Subagentes de Claude Code (Opus 5.5), mirando la foto, con `describe_product_v2` de roomrag |
| `descripciones.jsonl` | Los lotes juntos (lo que lee el describer `written`) | `amoblai catalogo` |
| `kinds.yaml` | El kind de cada producto (filtro duro) | `amoblai catalogo` (lotes + correcciones) |
| `correcciones.yaml` | Correcciones a mano de tipo y kind | Nosotros |

**Productos**: 268 de IKEA del alcance (mapeo `configs/categories.yaml`): 89 alfombras, 71
mesas, 64 sillas y sillones, 37 sofás y 7 escritorios (que IKEA tipifica como "Table"). Se
describieron 275; 7 quedan afuera porque su foto es la de otra medida del mismo modelo (ver
abajo). **Medidas**: los asientos no tienen ninguna en el dataset; las mesas y alfombras, ancho y
profundidad (cuando las tienen).

**Cómo se escribieron las descripciones**: 8 subagentes, ~35 productos cada uno. Cada uno leyó
el prompt de roomrag, miró cada foto, escribió las ocho líneas (Type, Use, Style, Materials,
Colors, Shape, Feel, Goes with; 60 a 90 palabras; sin marca, nombre comercial, precio ni
medidas), eligió el kind mirando la foto y validó su lote con
`uv run python -m amoblai.descripciones <lote.jsonl> <lote.json>`. Ninguna API paga.

## Para revisar (lo que marcaron los subagentes)

- **Kinds cambiados respecto del tipo de IKEA** (5): 202.959.25 TINGBY 64x64 (side → coffee
  table, discutible), 302.620.95 y 702.828.31 GUNNERN (dining → side table: son pedestales
  chicos), 500.583.76 AGEN (dining chair → armchair: es un sillón de ratán), 502.345.82 HOLMSEL
  (armchair → dining chair, discutible).
- **Escritorios tipificados como mesa** (7, corregidos en `correcciones.yaml`): KLIMPEN/NIPEN,
  HISSMON/KRILLE, LINNMON/LERBERG, LINNMON/ADILS (x2), LINNMON/NIPEN, TORNLIDEN/ADILS.
- **Fotos repetidas entre SKUs** (el mismo modelo en otra medida): 16 grupos, casi todos
  alfombras de proporción parecida (MORUM, OSTED, PERSISK HAMADAN...), que quedan: la foto sirve
  para las dos medidas, y el retrieval no puede separarlas. En 7 la forma no coincide y se
  **excluyó** el SKU que no es el de la foto (`excluir` en `correcciones.yaml`, decidido mirando
  la foto): LISABO 702.976.58 (118x50, la foto es la de 70x70), MELLTORP 190.117.77 (125x75, la
  foto es la de 75x75), LOHALS 002.773.95, OSTED 202.703.12 y GÅSER 802.307.90 (la foto es un
  pasillo), LAPPLJUNG RUTA 402.279.02 y HAMPEN 703.130.07. Sin eso, el modelo de imagen dibuja
  un producto y la lista de compra recomienda otro.
- **Muebles infantiles dentro del alcance**: sillones SUNDVIK, IKEA PS LÖMSK, POPPTORP; varias
  alfombras de cuarto de chicos. Quedan, con "kids room" en Use.
- **Fotos con varios productos**: SIGNE 002.973.60 (ocho variantes de color), TÅNUM 302.126.75
  (dos), juegos de mesas nido (SVALSTA, KRAGSTA, RISSNA, STOCKHOLM). Descritos como se ven.
- **Nombres con letras perdidas en el dataset** (FLNG, GSER, RNDER, NORRKER, LMSTA...): no
  afecta, las descripciones no usan el nombre.

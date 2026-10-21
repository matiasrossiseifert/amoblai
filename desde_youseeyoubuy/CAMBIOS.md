# Cambios hechos en roomrag/ desde el TP (para llevar a YouSeeYouBuy)

YouSeeYouBuy pisa `roomrag/` y `tests/` al exportar: estos cambios tienen que volver allá antes
de la próxima actualización.

## 2026-10-21

- `kinds.py`: nuevo kind `"rug": "rug"` (tipo `rug`). El catálogo de IKEA del TP tiene alfombras
  y el alcance aprobado de la materia las incluye; sin el kind, `load_catalog` rechaza el
  catálogo y el plan no puede pedir una alfombra. Es genérico: sirve igual para YouSeeYouBuy.

## Cómo lo usa el TP (no es un cambio a roomrag)

- Se instala desde esta carpeta: `pyproject.toml` del TP empaqueta
  `desde_youseeyoubuy/roomrag` como `roomrag` (hatch `packages`). Una exportación nueva desde
  YouSeeYouBuy lo actualiza en el lugar, sin copias.
- Los tests de `tests/` de esta carpeta corren con los del TP (`testpaths`).
- Lo propio del TP vive en `src/amoblai/`: el catálogo IKEA (`catalogo_ikea.py`), los
  generadores de fal y OpenAI (`generacion.py`, con la interfaz de `generate.py`), la
  evaluación con el ground truth de IKEA y las apps.

## Otras vistas del ambiente (`views`) — steps.py, flow.py, __main__.py

- `run_flow(..., views=[...])` (y `python -m roomrag run ... --view <foto>`): otras fotos del
  mismo ambiente desde otros ángulos. Se guardan en la corrida como `room_2.jpg`, `room_3.jpg`...
  (`Run.views`) y van a `plan`, `choose` y `scene` **después** de las imágenes propias del paso,
  con una nota (`view_blocks`): sirven solo para entender el tamaño y la forma del cuarto; la
  imagen 1 sigue siendo la que se amobla. En `scene`, la nota pide no mencionarlas en el prompt,
  porque `generate` sigue mandando solo la foto principal y los productos.
- Sin vistas, el contenido de cada llamada es el mismo de antes (los prompts no cambian de
  versión). El registro de cada paso suma `"views": n` cuando hubo.

## Medidas parciales en los prompts — steps.py `_size`

- Antes, un candidato sin las tres medidas era "size unknown". Ahora van las que tenga (una
  alfombra o una mesa del dataset IKEA: "170 cm wide, 240 cm deep"). Con las tres, el texto es
  el mismo. Lo mostró la prueba del flujo: Claude eligió una alfombra de 140 x 200 cm y escribió
  "about 2 x 3 m" en el prompt de la imagen.

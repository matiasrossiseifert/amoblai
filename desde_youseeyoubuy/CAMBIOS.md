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

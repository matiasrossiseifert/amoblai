# Evaluación

## `ikea/`: retrieval por texto con el ground truth del dataset

- `consultas/lote_NN.json`: por cada uno de los 65 ambientes de IKEA (livings y comedores con
  productos anotados del catálogo), una consulta por mueble del alcance que se ve en la foto, en
  las ocho líneas del catálogo y con su kind. Las escribieron 5 subagentes de Claude Code con
  `src/amoblai/prompts/consultas_ambiente_v1.md`, mirando solo la foto (sin el catálogo ni las
  anotaciones), y las validaron con `uv run python -m amoblai.consultas <lote> <entrada>`.
- `consultas.json`: los lotes juntos (228 consultas), con el prompt y quién las escribió en `_meta`.

Nota: el prompt mostraba los kinds agrupados por tipo ("- chair: desk chair, dining chair,
armchair"); varios subagentes pusieron primero el tipo ("chair") y el validador los obligó a
usar el kind. Para una v2 del prompt conviene decirlo explícito.

Se corre con `uv run amoblai evaluar` (métricas y metodología en `docs/EXPERIMENTOS.md`); las
corridas quedan en `resultados/evaluacion/`.

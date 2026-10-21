# Resultados

Todo lo que producen las corridas. El repo es privado: se commitea para compartirlo.

| Carpeta / archivo | Contenido |
|---|---|
| `amoblar/<nombre>/` | Una corrida del flujo: `room.jpg` (y `room_2.jpg`, la vista extra), `request.json`, `1_searches.json` (plan), `2_candidates.json` y `2_candidates*.jpg` (retrieve), `3_choice.json` (choose), `4_scene.json` (scene), `5_image.json` y `final.png` (generate), y `manual/` si la imagen se hace a mano. Cada archivo trae el modelo, el prompt y el costo de su paso. |
| `evaluacion/<fecha>_<nombre>/` | Una evaluación del retrieval por texto: `corrida.json` (índice, embedders, commit), `metricas.json` (por método) y `rankings.jsonl` (el top-10 de cada consulta). |
| `reporte/` | Tablas y gráficos de las evaluaciones: `uv run amoblai reporte`. |
| `gastos.jsonl` | Una línea por llamada paga (cuenta, modelo, US$). Lo usan los topes de `configs/amoblai.yaml`; `uv run amoblai gastos` lo resume. |
| `mapeo_categorias.md` | El mapeo `type` de IKEA → categorías del alcance, con conteos. |
| `v0_imagen/` | Todo lo de la v0 (retrieval por imagen): corridas, recortes y reporte. |

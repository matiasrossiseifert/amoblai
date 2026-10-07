# Resultados

Todo lo que producen las corridas. El repo es privado, así que se commitea para
compartirlo en el equipo y entre máquinas.

| Carpeta / archivo | Contenido |
|---|---|
| `corridas/<fecha>_<tipo>_<nombre>/` | Una carpeta por corrida: `config.yaml` (config resuelta), `manifest.json` (commit de git, versiones, máquina), `metrics.json`, `usage.jsonl` y los artefactos. |
| `generaciones/<proveedor>/<hash>/` | Caché de imágenes generadas (API o a mano): `image.png` + `meta.json` con prompt, modelo, tokens y USD. El hash depende de las entradas y la config: repetir una corrida no vuelve a pagar. Las del editor manual incluyen además las entradas, `prompt.txt`, `INSTRUCCIONES.md` y `meta.yaml` (app usada). |
| `gastos.jsonl` | Una línea por llamada paga (tokens y USD). Lo usa `budget.max_usd_total`. |
| `reporte/` | Tablas (`.md`, `.csv`) y gráficos comparativos: `uv run amoblai report`. |
| `mapeo_categorias.md` | Mapeo `type` del dataset → categorías del alcance, con conteos. |

Tipos de corrida: `retriever` (evaluación sobre IKEA), `strict` (set
etiquetado), `e2e` (ambientes vacíos, con una subcarpeta por ambiente), `run`
(CLI) y `app` (webapps).

Artefactos de una corrida del pipeline: `00_original.jpg`, `01_imagen1.jpg`,
`02_detecciones.jpg`, `03_recortes/` (crudo y consulta), `05_mascara.png`,
`05_pasos/` (modo un mueble por llamada), `06_final.jpg`, `lista_compra.json`,
`resultado.json` (candidatos y similitudes de cada mueble) y los prompts usados.

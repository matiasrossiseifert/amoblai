"""Dónde está cada cosa del repositorio. Todo lo que el código lee y escribe vive en `datos/`;
las rutas son relativas a la raíz del repo (desde donde se corre `uv run amoblai`).

    datos/configs/          la config (amoblai.yaml), el mapeo de categorías y las ablaciones
    datos/catalogo/         el catálogo que se indexa: descripciones, kinds, correcciones
    datos/evaluacion_ikea/  las consultas de evaluación sobre los ambientes IKEA
    datos/ambientes_vacios/ fotos de ambientes para amoblar (dos vistas de cada uno)
    datos/resultados/       corridas, evaluaciones, reporte y el ledger de gastos (se commitea)
    datos/dataset/          el dataset IKEA descargado (no se commitea)
    datos/procesados/       lo que se genera desde el dataset: items, lotes (no se commitea)
    datos/cache/            descripciones, vectores, índices de ChromaDB (no se commitea)
"""

from __future__ import annotations

from pathlib import Path

DATOS = Path("datos")

CONFIGS = DATOS / "configs"
CONFIG = CONFIGS / "amoblai.yaml"
CATEGORIES = CONFIGS / "categories.yaml"
ABLATIONS = CONFIGS / "ablaciones"

CATALOG = DATOS / "catalogo"
DESCRIPTION_BATCHES = CATALOG / "descripciones"
DESCRIPTIONS = CATALOG / "descripciones.jsonl"
KINDS_FILE = CATALOG / "kinds.yaml"
CORRECTIONS = CATALOG / "correcciones.yaml"
CATALOG_YAML = CATALOG / "ikea.yaml"

EVAL_QUERIES = DATOS / "evaluacion_ikea" / "consultas.json"
REPLICAS = DATOS / "evaluacion_ikea" / "replicas"  # las mismas consultas, otros escritores
EMPTY_ROOMS = DATOS / "ambientes_vacios"

RESULTS = DATOS / "resultados"
RUNS = RESULTS / "amoblar"
EVAL_RUNS = RESULTS / "evaluacion"
IMAGE_REFERENCE = RESULTS / "evaluacion_imagen" / "referencia_ikea.json"
REPORT = RESULTS / "reporte"
LEDGER = RESULTS / "gastos.jsonl"

RAW = DATOS / "dataset" / "ikea"
PROCESSED = DATOS / "procesados"
ITEMS = PROCESSED / "items.jsonl"
CACHE = DATOS / "cache"

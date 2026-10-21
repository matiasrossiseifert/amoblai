# v0 deprecada: retrieval por imagen

Primera versión del TP (octubre de 2026). Se reemplazó por el RAG por texto (roomrag): ver
`docs/ARQUITECTURA.md` y, para la comparación con el mismo ground truth, `docs/EXPERIMENTOS.md`.
Queda acá completa y funcionando por si se quiere volver a probar o comparar.

Flujo: generador n.º 1 (ambiente con muebles genéricos) → detección (Grounding DINO / OWLv2) →
recorte con o sin fondo (SAM) → embeddings de imagen (DINOv3, DINOv2, CLIP, SigLIP 2) →
ChromaDB con filtro por categoría → generador n.º 2 (reemplaza cada mueble por el real).
Arquitectura: `docs/ARQUITECTURA_v0.md`. Resultados: `resultados/v0_imagen/`.

## Qué hay

```
amoblai_imagen/   el paquete de la v0 (antes src/amoblai): config, CLI, visión, embeddings, ...
apps/             sus webapps (usuario, flujo, etiquetado, paso a paso)
configs/          base.yaml, ablaciones/, umbrales.yaml, pricing.yaml, categories.yaml (copia)
tests/            sus tests (sin red; -m models para los que bajan modelos)
anotaciones/      el set estricto (vacío)
docs/             ARQUITECTURA_v0.md
```

## Cómo correrlo

Desde la raíz del repo, con las dependencias de la v0:

```bash
uv sync --extra cpu --extra imagen --group dev --group apps
PYTHONPATH=deprecated uv run pytest -c deprecated/pytest.ini deprecated/tests   # tests
PYTHONPATH=deprecated uv run python -m amoblai_imagen.cli --help        # CLI
PYTHONPATH=deprecated uv run python -m amoblai_imagen.cli eval retriever --calibrate
uv run --group apps python deprecated/apps/flujo.py                     # app de flujo
```

Las rutas por defecto apuntan a `deprecated/configs/` y `resultados/v0_imagen/`; el dataset y
los índices de Chroma siguen en `data/`.

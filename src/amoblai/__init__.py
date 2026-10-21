"""amoblai: amoblado virtual con RAG sobre el catálogo IKEA.

De una foto del ambiente y un pedido en texto libre, los productos del catálogo que hacen falta
(la lista de compra) y el ambiente amoblado con ellos.

    dataset/     data loading del dataset IKEA
    catalog/     preprocesamiento: el catálogo que se indexa, kinds, correcciones
    rag/         indexing pipeline (describe, embed, ChromaDB) y retrieval (filtros + coseno)
    furnish/     el flujo: plan → retrieve → choose → scene → generate
    prompts/     los prompts versionados
    evaluation/  métricas, ablaciones y reporte
    infra/       HTTP con reintentos y topes de gasto
    config.py    la config (datos/configs/amoblai.yaml)    paths.py  dónde está cada cosa
    cli.py       `uv run amoblai --help`
"""

"""Salida para el usuario: lista de compra en JSON (SKU → ficha del catálogo)."""

from __future__ import annotations

from typing import Any

from amoblai.categories import CategoryMap
from amoblai.data.catalog import Catalog
from amoblai.retrieval.retriever import RetrievalResult


def build_shopping_list(
    results: list[RetrievalResult], catalog: Catalog, categories: CategoryMap
) -> dict[str, Any]:
    productos: dict[str, dict[str, Any]] = {}
    no_encontrados: list[dict[str, Any]] = []
    for res in results:
        if res.chosen_sku is None:
            no_encontrados.append(
                {
                    "categoria": categories.name_es(res.category),
                    "mejor_similitud": res.best_score,
                    "umbral": res.threshold,
                }
            )
            continue
        score = next((c.score for c in res.candidates if c.sku == res.chosen_sku), None)
        entry = productos.get(res.chosen_sku)
        if entry is None:
            card = catalog.get(res.chosen_sku).card()
            card["categoria"] = categories.name_es(str(card["categoria"]))
            entry = productos[res.chosen_sku] = {**card, "cantidad": 0, "similitud": score}
        entry["cantidad"] += 1
        if score is not None and (entry["similitud"] is None or score > entry["similitud"]):
            entry["similitud"] = score
    return {
        "productos": productos,
        "total_unidades": sum(p["cantidad"] for p in productos.values()),
        "no_encontrados": no_encontrados,
        "nota": "El dataset no incluye precios ni links; se agregan solo cuando están disponibles.",
    }

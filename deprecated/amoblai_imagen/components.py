"""Construcción de los componentes del pipeline a partir de la config.

Los modelos se memorizan por proceso: una ablación que corre varias
configuraciones con el mismo detector o el mismo embedder no los vuelve a cargar.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from amoblai_imagen.categories import CategoryMap
from amoblai_imagen.config import AppConfig, stable_hash
from amoblai_imagen.data.catalog import Catalog
from amoblai_imagen.embeddings.base import Embedder
from amoblai_imagen.embeddings.registry import build_embedder
from amoblai_imagen.indexing.indexer import (
    index_catalog,
    load_or_build_catalog,
    open_store,
    sync_categories,
    threshold_key,
)
from amoblai_imagen.infra.cache import ArtifactCache
from amoblai_imagen.retrieval.reranker import NoopReranker, Reranker
from amoblai_imagen.retrieval.retriever import Retriever, resolve_threshold
from amoblai_imagen.vectorstore.chroma import ChromaVectorStore
from amoblai_imagen.vision.background import BackgroundRemover, build_background_remover
from amoblai_imagen.vision.detection import Detector, build_detector

log = logging.getLogger(__name__)

_MEMO: dict[tuple[str, str], Any] = {}


def _memo(kind: str, key: Any, factory):
    k = (kind, stable_hash(key))
    if k not in _MEMO:
        _MEMO[k] = factory()
    return _MEMO[k]


@dataclass
class RetrievalComponents:
    config: AppConfig
    categories: CategoryMap
    catalog: Catalog
    detector: Detector
    remover: BackgroundRemover
    embedder: Embedder
    store: ChromaVectorStore
    retriever: Retriever
    reranker: Reranker


def get_embedder(cfg: AppConfig) -> Embedder:
    return _memo(
        "embedder", [cfg.embedding, cfg.device], lambda: build_embedder(cfg.embedding, cfg.device)
    )


def ensure_index(cfg: AppConfig, embedder: Embedder) -> ChromaVectorStore:
    """Abre la colección del embedder y la construye si está vacía."""
    store = open_store(cfg)
    if store.count() == 0:
        log.info("La colección %s está vacía: se indexa el catálogo", store.collection_name)
        index_catalog(cfg, embedder)
    return store


def build_retrieval_components(cfg: AppConfig, use_threshold: bool = True) -> RetrievalComponents:
    categories = CategoryMap.load(cfg.paths.categories_file)
    catalog = load_or_build_catalog(cfg)
    cache_root = cfg.paths.cache_dir
    detector = _memo(
        "detector",
        [cfg.detection, cfg.device, categories.detector_labels],
        lambda: build_detector(
            cfg.detection,
            categories.label_to_category,
            cfg.device,
            cache=ArtifactCache(cache_root, "detecciones"),
        ),
    )
    remover = _memo(
        "remover",
        [
            cfg.background.method,
            cfg.background.sam_model_id,
            cfg.background.rembg_model,
            cfg.device,
        ],
        lambda: build_background_remover(
            cfg.background, cfg.device, cache=ArtifactCache(cache_root, "mascaras")
        ),
    )
    embedder = get_embedder(cfg)
    store = ensure_index(cfg, embedder)
    sync_categories(store, catalog, categories)
    threshold = (
        resolve_threshold(cfg.retrieval, cfg.paths.thresholds_file, threshold_key(cfg))
        if use_threshold
        else None
    )
    retriever = Retriever(
        embedder,
        store,
        top_k=cfg.retrieval.top_k,
        category_filter=cfg.retrieval.category_filter,
        threshold=threshold,
        scope=categories.scope,
    )
    return RetrievalComponents(
        cfg, categories, catalog, detector, remover, embedder, store, retriever, NoopReranker()
    )

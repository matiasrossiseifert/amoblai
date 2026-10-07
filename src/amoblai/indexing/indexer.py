"""Indexing pipeline: catálogo → preprocesamiento → splitting → embedding → vector store."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from rich.progress import Progress

from amoblai.categories import CategoryMap
from amoblai.config import AppConfig, stable_hash
from amoblai.data.catalog import Catalog
from amoblai.data.ikea import IkeaDataset
from amoblai.embeddings.base import Embedder
from amoblai.embeddings.registry import model_id_for
from amoblai.indexing.preprocess import prepare_for_embedding
from amoblai.indexing.splitter import IndexEntry, split_catalog
from amoblai.infra.images import load_image
from amoblai.vectorstore.chroma import ChromaVectorStore, collection_name_for

log = logging.getLogger(__name__)


@dataclass
class IndexStats:
    collection: str
    entries: int
    added: int
    skipped_existing: int
    seconds: float


def collection_name(cfg: AppConfig) -> str:
    """Nombre de la colección para el embedder y el preprocesamiento de `cfg`."""
    return collection_name_for(
        cfg.embedding.name, model_id_for(cfg.embedding), stable_hash(cfg.preprocess, length=8)
    )


def open_store(cfg: AppConfig) -> ChromaVectorStore:
    return ChromaVectorStore(cfg.paths.chroma_dir, collection_name(cfg))


def load_or_build_catalog(cfg: AppConfig, rebuild: bool = False) -> Catalog:
    """Carga la ficha de productos; la regenera desde el dataset si falta o se pide."""
    path = Path(cfg.paths.catalog_file)
    categories = CategoryMap.load(cfg.paths.categories_file)
    if path.exists() and not rebuild:
        return Catalog.load(path, cfg.paths.raw_dir, categories)
    dataset = IkeaDataset.load(cfg.paths.raw_dir)
    catalog = Catalog.from_dataset(dataset, categories)
    catalog.save(path)
    log.info("Catálogo guardado en %s (%d productos)", path, len(catalog))
    return catalog


def build_index(
    entries: list[IndexEntry],
    embedder: Embedder,
    store: ChromaVectorStore,
    cfg: AppConfig,
    batch_size: int = 64,
) -> IndexStats:
    """Embebe e inserta las entradas que todavía no están en la colección (incremental)."""
    start = time.perf_counter()
    existing = store.existing_ids([e.id for e in entries])
    todo = [e for e in entries if e.id not in existing]
    log.info(
        "Colección %s: %d entradas, %d ya indexadas, %d por indexar",
        store.collection_name,
        len(entries),
        len(existing),
        len(todo),
    )
    with Progress() as progress:
        task = progress.add_task("Indexando", total=len(todo))
        for i in range(0, len(todo), batch_size):
            batch = todo[i : i + batch_size]
            images = [
                prepare_for_embedding(load_image(cfg.paths.raw_dir / e.image_path), cfg.preprocess)
                for e in batch
            ]
            vectors = embedder.embed_images(images)
            store.upsert([e.id for e in batch], vectors, [e.metadata for e in batch])
            progress.advance(task, len(batch))
    return IndexStats(
        collection=store.collection_name,
        entries=len(entries),
        added=len(todo),
        skipped_existing=len(existing),
        seconds=round(time.perf_counter() - start, 1),
    )


def sync_categories(store: ChromaVectorStore, catalog: Catalog, categories: CategoryMap) -> int:
    """Si cambió el mapeo de categorías, actualiza la metadata del índice (sin re-embeber).

    Devuelve cuántos vectores se actualizaron.
    """
    fingerprint = categories.fingerprint()
    if store.metadata.get("categories_hash") == fingerprint:
        return 0
    entries = split_catalog(catalog)
    present = store.existing_ids([e.id for e in entries])
    todo = [e for e in entries if e.id in present]
    store.update_metadatas([e.id for e in todo], [e.metadata for e in todo])
    store.set_metadata({"categories_hash": fingerprint})
    log.info(
        "Mapeo de categorías %s aplicado a %d vectores de %s",
        fingerprint,
        len(todo),
        store.collection_name,
    )
    return len(todo)


def index_catalog(cfg: AppConfig, embedder: Embedder, rebuild_catalog: bool = False) -> IndexStats:
    catalog = load_or_build_catalog(cfg, rebuild=rebuild_catalog)
    entries = split_catalog(catalog, scope_only=cfg.index.scope_only)
    store = open_store(cfg)
    stats = build_index(entries, embedder, store, cfg)
    sync_categories(store, catalog, CategoryMap.load(cfg.paths.categories_file))
    return stats

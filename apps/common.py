"""Helpers compartidos por las webapps de prueba.

Las apps solo orquestan y muestran: toda la lógica está en el paquete `amoblai`.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
if str(ROOT / "src") not in sys.path:  # permite correr las apps sin instalar el paquete
    sys.path.insert(0, str(ROOT / "src"))

from amoblai.config import AppConfig, load_config, load_env, stable_hash  # noqa: E402
from amoblai.infra.images import load_image  # noqa: E402
from amoblai.infra.runs import list_runs  # noqa: E402
from amoblai.pipeline.query import FurnishPipeline  # noqa: E402

PROVIDERS = ["manual", "openai", "gemini", "dry_run"]
_PIPELINES: dict[str, FurnishPipeline] = {}


def setup() -> None:
    """Carga .env y fija el directorio de trabajo en la raíz del repo (rutas relativas)."""
    import logging

    os.chdir(ROOT)
    load_env(ROOT / ".env")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def make_config(overrides: list[str] | None = None) -> AppConfig:
    """Config base + overrides; en las apps los pasos manuales nunca bloquean."""
    extra = [
        "generation.generator1.manual_wait=false",
        "generation.generator2.manual_wait=false",
        *(overrides or []),
    ]
    return load_config(ROOT / "configs" / "base.yaml", extra)


def get_pipeline(cfg: AppConfig) -> FurnishPipeline:
    """Un pipeline por config (los modelos además se comparten entre pipelines)."""
    key = stable_hash(cfg.model_dump(mode="json", exclude={"name"}))
    if key not in _PIPELINES:
        _PIPELINES[key] = FurnishPipeline.from_config(cfg)
    return _PIPELINES[key]


def allowed_paths(cfg: AppConfig) -> list[str]:
    return [
        str(Path(p).resolve())
        for p in (cfg.paths.results_dir, cfg.paths.raw_dir, cfg.paths.empty_rooms_dir)
    ]


def empty_rooms(cfg: AppConfig) -> list[str]:
    folder = Path(cfg.paths.empty_rooms_dir)
    if not folder.exists():
        return []
    return sorted(
        str(p) for p in folder.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    )


def ikea_rooms(
    cfg: AppConfig, room_types: tuple[str, ...] = ("Living Room", "Dining")
) -> list[str]:
    """Fotos de ambientes de IKEA amoblados: sirven como "imagen 1" para probar sin generar."""
    from amoblai.data.ikea import IkeaDataset

    raw = Path(cfg.paths.raw_dir)
    if not (raw / "text_data").exists():
        return []
    ds = IkeaDataset.load(raw)
    return [str(raw / r.path) for r in ds.rooms.values() if r.room_type in room_types]


def runs(cfg: AppConfig, kind: str | None = None) -> list[str]:
    return [str(p) for p in list_runs(cfg.paths.runs_dir, kind)]


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text()) if Path(path).exists() else None


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def image_or_none(path: Path) -> Image.Image | None:
    return load_image(path) if Path(path).exists() else None


def manual_inputs(workdir: Path) -> tuple[list[tuple[str, str]], str, str]:
    """Imágenes de entrada, prompt e instrucciones de una carpeta de trabajo manual."""
    workdir = Path(workdir)
    images = [(str(p), p.name) for p in sorted(workdir.glob("entrada_*.png"))]
    zone = workdir / "zona_a_editar.png"
    if zone.exists():
        images.append((str(zone), zone.name))
    prompt = (workdir / "prompt.txt").read_text() if (workdir / "prompt.txt").exists() else ""
    instructions = (
        (workdir / "INSTRUCCIONES.md").read_text()
        if (workdir / "INSTRUCCIONES.md").exists()
        else ""
    )
    return images, prompt, instructions


def save_manual_result(workdir: Path, image: Image.Image, app: str, notes: str = "") -> None:
    """Guarda el resultado generado a mano y la app usada (lo registra la corrida)."""
    workdir = Path(workdir)
    image.convert("RGB").save(workdir / "resultado.png")
    meta_path = workdir / "meta.yaml"
    meta = (yaml.safe_load(meta_path.read_text()) or {}) if meta_path.exists() else {}
    meta.update({"app": app, "notas": notes or meta.get("notas", ""), "cargado_desde": "webapp"})
    meta_path.write_text(yaml.safe_dump(meta, allow_unicode=True, sort_keys=False))


def shopping_rows(shopping: dict[str, Any]) -> list[list[Any]]:
    rows = []
    for sku, p in (shopping or {}).get("productos", {}).items():
        rows.append(
            [
                sku,
                p.get("nombre"),
                p.get("categoria"),
                p.get("tipo"),
                p.get("medidas"),
                p.get("cantidad"),
                p.get("similitud"),
            ]
        )
    return rows


SHOPPING_HEADERS = ["SKU", "Nombre", "Categoría", "Tipo", "Medidas", "Cantidad", "Similitud"]

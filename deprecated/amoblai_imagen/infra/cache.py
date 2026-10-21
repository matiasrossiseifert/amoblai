"""Caché direccionada por contenido: hash(entradas + configuración) → artefactos.

Sirve para no pagar dos veces la misma llamada a una API y para no recomputar
pasos locales caros (detecciones, máscaras). Cada entrada es una carpeta con
archivos simples (JSON e imágenes), fácil de inspeccionar y de commitear.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from amoblai_imagen.config import stable_hash


class ArtifactCache:
    def __init__(self, root: Path, namespace: str):
        self.root = Path(root) / namespace

    def key(self, payload: Any) -> str:
        return stable_hash(payload, length=24)

    def dir_for(self, key: str) -> Path:
        return self.root / key

    def has(self, key: str, name: str) -> bool:
        return (self.dir_for(key) / name).exists()

    def get_json(self, key: str, name: str = "meta.json") -> Any | None:
        path = self.dir_for(key) / name
        return json.loads(path.read_text()) if path.exists() else None

    def put_json(self, key: str, data: Any, name: str = "meta.json") -> Path:
        path = self.dir_for(key) / name
        _atomic_write(path, json.dumps(data, ensure_ascii=False, indent=1, default=str).encode())
        return path

    def get_image(self, key: str, name: str = "image.png") -> Image.Image | None:
        path = self.dir_for(key) / name
        if not path.exists():
            return None
        with Image.open(path) as img:
            img.load()
            return img.copy()

    def put_image(self, key: str, img: Image.Image, name: str = "image.png") -> Path:
        path = self.dir_for(key) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        img.save(tmp, format="PNG")
        os.replace(tmp, path)
        return path

    def get_array(self, key: str, name: str = "array.npz") -> dict[str, np.ndarray] | None:
        path = self.dir_for(key) / name
        if not path.exists():
            return None
        with np.load(path) as data:
            return {k: data[k] for k in data.files}

    def put_array(self, key: str, arrays: dict[str, np.ndarray], name: str = "array.npz") -> Path:
        path = self.dir_for(key) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".npz", delete=False) as tmp:
            np.savez_compressed(tmp, **arrays)
        os.replace(tmp.name, path)
        return path


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)

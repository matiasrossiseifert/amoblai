"""Descarga del dataset IKEA (Tautkute et al., 2017) fijado a un commit.

Las imágenes nunca se commitean: este módulo las baja de GitHub y las extrae en
`data/raw/ikea/`. El zip se trata como dato no confiable: se valida cada ruta
antes de extraerla (zip slip) y solo se extraen `images/` y `text_data/`.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

import httpx

log = logging.getLogger(__name__)

DEFAULT_REPO = "IvonaTau/ikea"
# Último commit del repo (2018-07-13, "additional ground truth data").
DEFAULT_COMMIT = "6f316e3fecf8ce95069eaef5f2021405c536168a"
_KEEP_PREFIXES = ("images/", "text_data/")
_MARKER = ".amoblai_download_ok"


def archive_url(repo: str = DEFAULT_REPO, commit: str = DEFAULT_COMMIT) -> str:
    return f"https://codeload.github.com/{repo}/zip/{commit}"


def is_downloaded(dest: Path) -> bool:
    return (dest / _MARKER).exists()


def download_dataset(
    dest: Path,
    repo: str = DEFAULT_REPO,
    commit: str = DEFAULT_COMMIT,
    force: bool = False,
) -> Path:
    """Descarga y extrae el dataset en `dest`. Es idempotente salvo `force=True`."""
    dest = Path(dest)
    if is_downloaded(dest) and not force:
        log.info("Dataset ya descargado en %s", dest)
        return dest
    if dest.exists() and force:
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    url = archive_url(repo, commit)
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "ikea.zip"
        log.info("Descargando %s", url)
        with httpx.stream("GET", url, follow_redirects=True, timeout=120.0) as resp:
            resp.raise_for_status()
            with zip_path.open("wb") as fh:
                for chunk in resp.iter_bytes(chunk_size=1 << 20):
                    fh.write(chunk)
        n = extract_safely(zip_path, dest)
    (dest / _MARKER).write_text(f"{repo}@{commit}\n")
    log.info("Extraídos %d archivos en %s", n, dest)
    return dest


def extract_safely(zip_path: Path, dest: Path) -> int:
    """Extrae solo `images/` y `text_data/`, quitando la carpeta raíz del zip.

    Rechaza rutas absolutas o con `..` para evitar escribir fuera de `dest`.
    """
    dest = dest.resolve()
    count = 0
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            parts = PurePosixPath(info.filename).parts
            if len(parts) < 2:
                continue
            rel = PurePosixPath(*parts[1:])  # quita "ikea-<commit>/"
            if rel.is_absolute() or ".." in rel.parts:
                raise ValueError(f"Ruta sospechosa en el zip: {info.filename!r}")
            if not str(rel).startswith(_KEEP_PREFIXES):
                continue
            target = (dest / rel).resolve()
            if not target.is_relative_to(dest):
                raise ValueError(f"Ruta fuera del destino: {info.filename!r}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target.open("wb") as out:
                shutil.copyfileobj(src, out)
            count += 1
    return count

"""Corridas reproducibles: cada una guarda su config, métricas, artefactos y costo.

Estructura de `resultados/corridas/<fecha>_<tipo>_<nombre>/`:
    config.yaml      configuración resuelta (después de `extends` y `--set`)
    manifest.json    commit de git, versiones, dispositivo, tiempos, comando
    metrics.json     métricas de la corrida
    usage.jsonl      uso por llamada (tokens, latencia, USD)
    ...              artefactos propios del tipo de corrida
"""

from __future__ import annotations

import json
import platform
import socket
import subprocess
import sys
from datetime import datetime
from importlib import metadata
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from amoblai.config import AppConfig
from amoblai.infra.images import save_image
from amoblai.infra.usage import UsageRecord, summarize_usage

_PACKAGES = ("torch", "transformers", "chromadb", "openai", "google-genai", "pillow", "numpy")


def git_info() -> dict[str, Any]:
    def run(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], capture_output=True, text=True, check=True, timeout=10
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""

    return {"commit": run("rev-parse", "HEAD") or None, "dirty": bool(run("status", "--porcelain"))}


def package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for pkg in _PACKAGES:
        try:
            versions[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            versions[pkg] = None
    return versions


class RunContext:
    def __init__(
        self, config: AppConfig, kind: str, name: str | None = None, root: Path | None = None
    ):
        self.config = config
        self.kind = kind
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        label = _slug(name or config.name)
        base = Path(root or config.paths.runs_dir)
        self.run_id = f"{stamp}_{kind}_{label}"
        suffix = 1
        while (base / self.run_id).exists():
            suffix += 1
            self.run_id = f"{stamp}_{kind}_{label}-{suffix}"
        self.dir = base / self.run_id
        self.dir.mkdir(parents=True)
        self.usage: list[UsageRecord] = []
        self.started = datetime.now()
        self.write_yaml("config.yaml", config.model_dump(mode="json"))
        self._write_manifest(finished=False)

    @classmethod
    def reopen(cls, run_dir: Path, config: AppConfig) -> RunContext:
        """Retoma una corrida existente (p. ej. una que quedó esperando un paso manual)."""
        run = cls.__new__(cls)
        run.config = config
        run.dir = Path(run_dir)
        manifest = json.loads((run.dir / "manifest.json").read_text())
        run.kind = manifest["kind"]
        run.run_id = manifest["run_id"]
        run.started = datetime.fromisoformat(manifest["started_at"])
        usage_path = run.dir / "usage.jsonl"
        run.usage = (
            [UsageRecord.model_validate_json(x) for x in usage_path.read_text().splitlines() if x]
            if usage_path.exists()
            else []
        )
        return run

    def path(self, rel: str) -> Path:
        p = self.dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def write_json(self, rel: str, data: Any) -> Path:
        p = self.path(rel)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        return p

    def write_yaml(self, rel: str, data: Any) -> Path:
        p = self.path(rel)
        p.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
        return p

    def append_jsonl(self, rel: str, row: dict[str, Any]) -> None:
        with self.path(rel).open("a") as fh:
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    def save_image(self, rel: str, img: Image.Image) -> Path:
        return save_image(img, self.path(rel))

    def add_usage(self, record: UsageRecord) -> None:
        self.usage.append(record)
        self.append_jsonl("usage.jsonl", record.model_dump(mode="json"))

    def finish(self, metrics: dict[str, Any] | None = None) -> None:
        payload = dict(metrics or {})
        payload["usage"] = summarize_usage(self.usage)
        payload["wall_time_s"] = round((datetime.now() - self.started).total_seconds(), 2)
        self.write_json("metrics.json", payload)
        self._write_manifest(finished=True)

    def _write_manifest(self, finished: bool) -> None:
        self.write_json(
            "manifest.json",
            {
                "run_id": self.run_id,
                "kind": self.kind,
                "config_name": self.config.name,
                "started_at": self.started.isoformat(),
                "finished_at": datetime.now().isoformat() if finished else None,
                "git": git_info(),
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "host": socket.gethostname(),
                "packages": package_versions(),
                "command": " ".join(sys.argv),
            },
        )


class SubRun(RunContext):
    """Vista de una corrida que escribe en una subcarpeta (p. ej. un ambiente de la eval e2e).

    Comparte el registro de uso con la corrida padre.
    """

    def __init__(self, parent: RunContext, prefix: str):
        self.parent = parent
        self.config = parent.config
        self.kind = parent.kind
        self.run_id = parent.run_id
        self.dir = parent.dir / prefix
        self.dir.mkdir(parents=True, exist_ok=True)
        self.started = parent.started
        self.usage = []

    def add_usage(self, record: UsageRecord) -> None:
        self.usage.append(record)
        self.append_jsonl("usage.jsonl", record.model_dump(mode="json"))
        self.parent.add_usage(record)

    def finish(self, metrics: dict[str, Any] | None = None) -> None:
        self.write_json(
            "metrics.json", dict(metrics or {}) | {"usage": summarize_usage(self.usage)}
        )


def _slug(text: str) -> str:
    keep = "".join(c if c.isalnum() or c in "-_." else "-" for c in text.lower())
    return keep.strip("-")[:60] or "corrida"


def list_runs(root: Path, kind: str | None = None) -> list[Path]:
    root = Path(root)
    if not root.exists():
        return []
    runs = [p for p in root.iterdir() if (p / "manifest.json").exists()]
    if kind:
        runs = [p for p in runs if json.loads((p / "manifest.json").read_text())["kind"] == kind]
    return sorted(runs, reverse=True)

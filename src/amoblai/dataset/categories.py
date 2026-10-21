"""Categorías del alcance v1 y su mapeo desde los `type` del dataset IKEA."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

OTHER = "other"


@dataclass(frozen=True)
class Category:
    key: str
    name_es: str
    detector_labels: tuple[str, ...]
    ikea_types: tuple[str, ...]


@dataclass
class CategoryMap:
    categories: dict[str, Category]
    excluded: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> CategoryMap:
        data = yaml.safe_load(Path(path).read_text())
        cats = {
            key: Category(
                key=key,
                name_es=spec.get("name_es", key),
                detector_labels=tuple(spec["detector_labels"]),
                ikea_types=tuple(spec["ikea_types"]),
            )
            for key, spec in data["categories"].items()
        }
        excluded = {e["type"]: e.get("reason", "") for e in data.get("excluded", [])}
        cmap = cls(cats, excluded)
        cmap._validate()
        return cmap

    def _validate(self) -> None:
        seen: dict[str, str] = {}
        for cat in self.categories.values():
            for t in cat.ikea_types:
                if t in seen:
                    raise ValueError(f"El type {t!r} está en {seen[t]!r} y en {cat.key!r}")
                if t in self.excluded:
                    raise ValueError(f"El type {t!r} está incluido y excluido a la vez")
                seen[t] = cat.key
        labels: dict[str, str] = {}
        for cat in self.categories.values():
            for label in cat.detector_labels:
                if label in labels:
                    raise ValueError(f"La etiqueta {label!r} está en dos categorías")
                labels[label] = cat.key

    def fingerprint(self) -> str:
        """Hash del mapeo type → categoría (cambia si se edita categories.yaml)."""
        mapping = {c.key: sorted(c.ikea_types) for c in self.categories.values()}
        payload = json.dumps(mapping, sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()[:12]

    @property
    def scope(self) -> list[str]:
        return list(self.categories)

    def category_of_type(self, ikea_type: str) -> str:
        for cat in self.categories.values():
            if ikea_type in cat.ikea_types:
                return cat.key
        return OTHER

    @property
    def label_to_category(self) -> dict[str, str]:
        return {label: c.key for c in self.categories.values() for label in c.detector_labels}

    @property
    def detector_labels(self) -> list[str]:
        return list(self.label_to_category)

    def name_es(self, key: str) -> str:
        cat = self.categories.get(key)
        return cat.name_es if cat else key

    def mapping_report(self, types: Iterable[str]) -> str:
        """Tabla Markdown con la cantidad de SKUs por `type` y su categoría asignada."""
        counts = Counter(types)
        lines = ["# Mapeo de `type` IKEA → categorías del alcance", ""]
        lines += ["| Categoría | `type` del dataset | SKUs |", "|---|---|---|"]
        for cat in self.categories.values():
            total = 0
            for t in cat.ikea_types:
                n = counts.get(t, 0)
                total += n
                lines.append(f"| {cat.name_es} | {t} | {n} |")
            lines.append(f"| **{cat.name_es} (total)** | | **{total}** |")
        lines += ["", "## Excluidos (dudosos)", "", "| `type` | SKUs | Motivo |", "|---|---|---|"]
        for t, reason in self.excluded.items():
            lines.append(f"| {t} | {counts.get(t, 0)} | {reason} |")
        in_scope = {t for c in self.categories.values() for t in c.ikea_types}
        n_other = sum(n for t, n in counts.items() if t not in in_scope)
        lines += [
            "",
            f"Resto del catálogo (`other`): {n_other} SKUs en "
            f"{len(set(counts) - in_scope)} valores de `type`.",
        ]
        missing = sorted(in_scope - set(counts))
        if missing:
            lines += ["", "Tipos del mapeo que no aparecen en el dataset: " + ", ".join(missing)]
        return "\n".join(lines) + "\n"

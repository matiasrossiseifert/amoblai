"""Las descripciones del catálogo: lotes para los subagentes que las escriben y su validación.

Las descripciones no las escribe ninguna API: las escriben subagentes de Claude Code mirando la
foto de cada producto, con el prompt de roomrag (`describe_product_v2.md`). Cada subagente
recibe un lote (`data/processed/describir/lote_NN.json`), escribe un JSON-lines
(`catalogo/descripciones/lote_NN.jsonl`) y lo valida con:

    uv run python -m amoblai.descripciones catalogo/descripciones/lote_NN.jsonl \\
        data/processed/describir/lote_NN.json

`merge` junta los lotes en `catalogo/descripciones.jsonl` (lo que lee el describer `written`) y
`catalogo/kinds.yaml` (el kind de cada producto, que pisa el de por defecto).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

LABELS = ("Type", "Use", "Style", "Materials", "Colors", "Shape", "Feel", "Goes with")
STYLES = {
    "scandinavian",
    "mid-century modern",
    "minimalist",
    "japandi",
    "industrial",
    "rustic",
    "farmhouse",
    "bohemian",
    "coastal",
    "traditional",
    "classic",
    "art deco",
    "glam",
    "retro",
    "contemporary",
    "modern",
}
MIN_WORDS, MAX_WORDS = 60, 90  # lo que pide el prompt
HARD_MIN, HARD_MAX = 50, 100  # fuera de esto es un error, no un aviso
_NEGATIONS = re.compile(r"\b(not|without|no|never)\b", re.I)
_MEASURES = re.compile(r"\d+\s*(cm|mm|m|in|inch|\")\b", re.I)


def kinds_by_type() -> dict[str, list[str]]:
    from roomrag.kinds import KINDS

    out: dict[str, list[str]] = {}
    for kind, typ in KINDS.items():
        out.setdefault(typ, []).append(kind)
    return out


def make_batches(items: list[dict], out_dir: Path, size: int, root: Path) -> list[Path]:
    """Lotes de `size` productos para los subagentes, con las fotos en rutas absolutas."""
    allowed = kinds_by_type()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for n, start in enumerate(range(0, len(items), size), start=1):
        batch = [
            {
                "id": it["id"],
                "name": it["name"],
                "type_ikea": it["type_ikea"],
                "category": it["category"],
                "default_kind": it["kind"],
                "allowed_kinds": allowed[it["category"]],
                "dimensions_cm": it["dimensions_cm"],
                "photos": [str((Path(root) / p).resolve()) for p in it["photos"]],
            }
            for it in items[start : start + size]
        ]
        path = out_dir / f"lote_{n:02d}.json"
        path.write_text(json.dumps(batch, ensure_ascii=False, indent=1))
        paths.append(path)
    return paths


def check_text(text: str, name: str = "") -> tuple[list[str], list[str]]:
    """(errores, avisos) de una descripción."""
    errors: list[str] = []
    warnings: list[str] = []
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if len(lines) != len(LABELS):
        errors.append(f"{len(lines)} líneas (se piden {len(LABELS)})")
    values = []
    for label, line in zip(LABELS, lines, strict=False):
        if not line.startswith(f"{label}:"):
            errors.append(f"se esperaba '{label}:' y llegó {line[:30]!r}")
            continue
        values.append(line.split(":", 1)[1].strip())
    words = sum(len(v.split()) for v in values)
    if not HARD_MIN <= words <= HARD_MAX:
        errors.append(f"{words} palabras (se piden {MIN_WORDS}-{MAX_WORDS})")
    elif not MIN_WORDS <= words <= MAX_WORDS:
        warnings.append(f"{words} palabras (se piden {MIN_WORDS}-{MAX_WORDS})")
    if len(values) >= 3:
        styles = [s.strip().lower() for s in values[2].split(",") if s.strip()]
        bad = [s for s in styles if s not in STYLES]
        if bad or not 1 <= len(styles) <= 3:
            errors.append(f"Style fuera de la lista o más de tres: {styles}")
    low = text.lower()
    if "ikea" in low:
        errors.append("menciona la marca")
    if name and re.search(rf"\b{re.escape(name)}\b", text):
        errors.append(f"menciona el nombre comercial {name!r}")
    if _MEASURES.search(text):
        errors.append("incluye medidas")
    if "$" in text or "price" in low:
        errors.append("menciona precio")
    if _NEGATIONS.search(text):
        warnings.append("tiene una negación (los embeddings no leen el 'no')")
    return errors, warnings


def validate(out_file: Path, batch_file: Path) -> tuple[list[str], list[str]]:
    """Valida un lote escrito contra su lote de entrada: todos los ids, kinds válidos, textos."""
    batch = {b["id"]: b for b in json.loads(Path(batch_file).read_text())}
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for n, line in enumerate(Path(out_file).read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"línea {n}: no es JSON ({e})")
            continue
        pid = row.get("id")
        if pid not in batch:
            errors.append(f"línea {n}: id {pid!r} no está en el lote")
            continue
        if pid in seen:
            errors.append(f"{pid}: repetido")
        seen.add(pid)
        for key in ("text", "kind", "by", "prompt"):
            if not row.get(key):
                errors.append(f"{pid}: falta {key!r}")
        if row.get("kind") not in batch[pid]["allowed_kinds"]:
            errors.append(
                f"{pid}: kind {row.get('kind')!r} no está en {batch[pid]['allowed_kinds']}"
            )
        e, w = check_text(row.get("text", ""), batch[pid]["name"])
        errors += [f"{pid}: {x}" for x in e]
        warnings += [f"{pid}: {x}" for x in w]
    missing = sorted(set(batch) - seen)
    if missing:
        errors.append(f"faltan {len(missing)} productos: {missing}")
    return errors, warnings


def merge(parts: list[Path], descriptions_out: Path, kinds_out: Path) -> tuple[int, int]:
    """Junta los lotes: descripciones (id, text, by, prompt) y kinds ({id: kind})."""
    rows: dict[str, dict] = {}
    for part in sorted(parts):
        for line in Path(part).read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                rows[row["id"]] = row
    descriptions_out.parent.mkdir(parents=True, exist_ok=True)
    with descriptions_out.open("w") as fh:
        for pid in sorted(rows):
            r = rows[pid]
            keep = {
                "id": pid,
                "text": r["text"].strip() + "\n",
                "by": r["by"],
                "prompt": r["prompt"],
            }
            fh.write(json.dumps(keep, ensure_ascii=False) + "\n")
    kinds = {pid: rows[pid]["kind"] for pid in sorted(rows)}
    header = "# Kind de cada producto (roomrag/kinds.py), asignado mirando su foto.\n"
    kinds_out.write_text(header + yaml.safe_dump(kinds, allow_unicode=True, sort_keys=True))
    return len(rows), len(kinds)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        print("uso: python -m amoblai.descripciones <salida.jsonl> <lote.json>")
        return 2
    errors, warnings = validate(Path(args[0]), Path(args[1]))
    for w in warnings:
        print(f"aviso: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"{len(errors)} errores, {len(warnings)} avisos")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

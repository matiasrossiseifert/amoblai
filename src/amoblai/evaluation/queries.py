"""Las consultas de evaluación: por cada foto de ambiente de IKEA, las búsquedas de sus muebles.

Subagentes de Claude Code miran cada foto (sin ver el catálogo ni las anotaciones) y escriben
una consulta por producto del alcance que ven: con `prompts/consultas_ambiente_v1.md`, las de
sofás, sillones, sillas, mesas y alfombras (SCOPE_TYPES); con `consultas_ambiente_v2.md`, las de
lo que sumó la ampliación del catálogo (EXPANSION_TYPES). Cada uno recibe un lote
(`datos/procesados/consultas[_v2]/lote_NN.json`, con los kinds que valen en cada ambiente),
escribe `datos/evaluacion_ikea/consultas[_v2]/lote_NN.json` y lo valida con:

    uv run python -m amoblai.evaluation.queries datos/evaluacion_ikea/consultas/lote_NN.json \\
        datos/procesados/consultas/lote_NN.json

`merge` junta los lotes en `datos/evaluacion_ikea/consultas.json`: {room_id: {"room",
"pieces"}}; `extend` le suma las piezas de otra pasada (cada una con su `prompt`), después de las
que ya estaban, sin tocarlas.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from amoblai.catalog.descriptions import LABELS, STYLES

SCOPE_TYPES = ("sofa", "chair", "table", "rug")
EXPANSION_TYPES = (
    "desk",
    "shelf",
    "cabinet",
    "dresser",
    "ottoman",
    "stool",
    "bench",
    "lamp",
    "deco",
)


def scope_kinds(types: tuple[str, ...] = SCOPE_TYPES) -> dict[str, str]:
    from amoblai.catalog.kinds import KINDS

    return {k: t for k, t in KINDS.items() if t in types}


def kinds_text(types: tuple[str, ...] = SCOPE_TYPES) -> str:
    by_type: dict[str, list[str]] = {}
    for kind, typ in scope_kinds(types).items():
        by_type.setdefault(typ, []).append(kind)
    return "\n".join(f"    - {t}: {', '.join(ks)}" for t, ks in by_type.items())


def eval_rooms(raw_dir: Path, items: list[dict], room_types: tuple[str, ...]) -> list[dict]:
    """Ambientes en disco de esos tipos con al menos un SKU anotado del catálogo."""
    from amoblai.dataset.ikea import IkeaDataset

    in_catalog = {it["id"] for it in items}
    ds = IkeaDataset.load(raw_dir)
    rooms = [
        {
            "room_id": r.room_id,
            "room_type": r.room_type,
            "photo": str((Path(raw_dir) / r.path).resolve()),
        }
        for r in ds.rooms.values()
        if r.room_type in room_types and r.skus & in_catalog
    ]
    return sorted(rooms, key=lambda r: r["room_id"])


def make_batches(
    rooms: list[dict], out_dir: Path, size: int, types: tuple[str, ...] = SCOPE_TYPES
) -> list[Path]:
    """Lotes de `size` ambientes, cada uno con los kinds que valen (los de `types`)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    kinds = sorted(scope_kinds(types))
    paths = []
    for n, start in enumerate(range(0, len(rooms), size), start=1):
        path = out_dir / f"lote_{n:02d}.json"
        batch = [{**r, "kinds": kinds} for r in rooms[start : start + size]]
        path.write_text(json.dumps(batch, ensure_ascii=False, indent=1))
        paths.append(path)
    return paths


def check_query(query: str) -> list[str]:
    errors = []
    lines = [ln for ln in query.strip().splitlines() if ln.strip()]
    labels = [ln.split(":", 1)[0] for ln in lines]
    if labels != list(LABELS):
        errors.append(f"líneas {labels} (se piden {list(LABELS)})")
    for ln in lines:
        if ln.startswith("Style:"):
            styles = [s.strip().lower() for s in ln.split(":", 1)[1].split(",") if s.strip()]
            if any(s not in STYLES for s in styles) or not 1 <= len(styles) <= 3:
                errors.append(f"Style fuera de la lista: {styles}")
    if "ikea" in query.lower():
        errors.append("menciona la marca")
    return errors


def validate(out_file: Path, batch_file: Path) -> list[str]:
    rooms = json.loads(Path(batch_file).read_text())
    batch = {r["room_id"] for r in rooms}
    kinds = rooms[0].get("kinds") if rooms else None  # los lotes de la v1 no los traen
    kinds = set(kinds) if kinds else set(scope_kinds())
    try:
        data = json.loads(Path(out_file).read_text())
    except json.JSONDecodeError as e:
        return [f"no es JSON: {e}"]
    errors = []
    for room_id in sorted(set(data) - batch):
        errors.append(f"{room_id}: no está en el lote")
    for room_id in sorted(batch - set(data)):
        errors.append(f"{room_id}: falta")
    for room_id, rec in data.items():
        if room_id not in batch:
            continue
        pieces = rec.get("pieces")
        if not isinstance(pieces, list):
            errors.append(f"{room_id}: falta la lista 'pieces'")
            continue
        if not rec.get("room"):
            errors.append(f"{room_id}: falta 'room'")
        for i, p in enumerate(pieces):
            where = f"{room_id} pieza {i}"
            ks = p.get("kinds") or []
            if len(ks) != 1 or ks[0] not in kinds:
                errors.append(f"{where}: kinds {ks} (uno de {sorted(kinds)})")
            if not p.get("piece"):
                errors.append(f"{where}: falta 'piece'")
            errors += [f"{where}: {e}" for e in check_query(p.get("query", ""))]
    return errors


def merge(parts: list[Path], out: Path, prompt_version: str, by: str) -> int:
    rooms: dict[str, dict] = {}
    for part in sorted(parts):
        rooms.update(json.loads(Path(part).read_text()))
    payload = {
        "_meta": {"prompt": prompt_version, "by": by, "rooms": len(rooms)},
        **{k: rooms[k] for k in sorted(rooms)},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    return len(rooms)


def extend(queries: Path, parts: list[Path], prompt_version: str, by: str) -> int:
    """Suma a `queries` las piezas de otra pasada (lotes en `parts`), cada una con su `prompt`,
    detrás de las que ya tenía cada ambiente; un ambiente nuevo entra con su `room`. Devuelve
    cuántas piezas sumó."""
    data = json.loads(Path(queries).read_text())
    added = 0
    for part in sorted(parts):
        for room_id, rec in json.loads(Path(part).read_text()).items():
            entry = data.setdefault(room_id, {"room": rec["room"], "pieces": []})
            entry["pieces"] += [{**p, "prompt": prompt_version} for p in rec["pieces"]]
            added += len(rec["pieces"])
    meta = data.pop("_meta")
    meta.setdefault("passes", []).append({"prompt": prompt_version, "by": by, "pieces": added})
    meta["rooms"] = len(data)
    out = {"_meta": meta, **{k: data[k] for k in sorted(data)}}
    Path(queries).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return added


def load_queries(path: Path) -> dict[str, dict]:
    data = json.loads(Path(path).read_text())
    return {k: v for k, v in data.items() if not k.startswith("_")}


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        print("uso: python -m amoblai.evaluation.queries <salida.json> <lote.json>")
        return 2
    errors = validate(Path(args[0]), Path(args[1]))
    for e in errors:
        print(f"ERROR: {e}")
    print(f"{len(errors)} errores")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

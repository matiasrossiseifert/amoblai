"""Relevancia graduada del contexto: un juez califica los tres primeros candidatos de cada
consulta (lo que el flujo le pasa al LLM que elige) con 2, 1 o 0.

- 2: el mismo producto que se ve en el ambiente, o uno que no se distingue (forma, material,
  color);
- 1: una alternativa aceptable: el mismo tipo de pieza, parecida en estilo y color, que alguien
  que buscaba eso podría comprar;
- 0: no sirve (otro tipo de pieza, o claramente distinto).

Es el context precision de RAGAS cuando no hay ground truth (un LLM etiqueta v_k) y el NDCG
graduado de la clase: mide si el contexto sirve, no solo si trae el SKU anotado, y vale también
para las consultas sin producto anotado en el catálogo. Donde sí hay ground truth, el acuerdo
del juez con él (¿el anotado recibe un 2?) valida al juez.

El juez es un subagente de Claude Code (gratis): `make_batches` arma lotes de consultas con la
foto del ambiente, la pieza, la consulta y las fotos y descripciones de los candidatos (sin
decir cuál es el anotado) en datos/procesados/graduada/lote_NN.json; el subagente escribe
datos/evaluacion_ikea/graduada/lote_NN.json: {"<clave>": {"<id>": 2, ...}}; `score` lo lee.
"""

from __future__ import annotations

import gzip
import json
import random
from collections import defaultdict
from math import log2
from pathlib import Path
from typing import Any

import numpy as np

from amoblai import paths
from amoblai.catalog.loader import load_catalog
from amoblai.config import Config
from amoblai.evaluation.metrics import bootstrap_ci

TOP = 3  # furnish.candidates: lo que ve el LLM que elige
BATCHES = paths.PROCESSED / "graduada"
ANSWERS = paths.DATOS / "evaluacion_ikea" / "graduada"
GUIDE = """Each item is one search: a photo of a furnished room (look at the piece named), the
piece, the search the system ran for it, and the top candidates it returned from the catalog.
Grade each candidate, by looking at its photo against the piece in the room photo:
2 = the same product, or one you cannot tell apart (same shape, material and color);
1 = an acceptable alternative: the same kind of piece, close in style and color, that someone
    who wanted that piece could buy instead;
0 = not useful: another kind of piece, or clearly different.
Judge what you see, not the names."""


def key_of(room_id: str, piece: int) -> str:
    return f"{room_id}#{piece}"


def make_batches(
    cfg: Config,
    run_dir: Path,
    method: str,
    n: int = 150,
    size: int = 15,
    seed: int = 0,
    out_dir: Path = BATCHES,
) -> list[Path]:
    """Lotes para los jueces con `n` consultas al azar (mitad con producto anotado en el
    catálogo, mitad sin) y sus `TOP` primeros candidatos de `method` en la corrida `run_dir`."""
    from amoblai.evaluation.queries import load_queries

    rows = [
        json.loads(x)
        for x in gzip.decompress((Path(run_dir) / "rankings.jsonl.gz").read_bytes()).splitlines()
    ]
    rows = [r for r in rows if r["method"] == method]
    queries = load_queries(paths.EVAL_QUERIES)
    catalog = {p.id: p for p in load_catalog(cfg.rag.catalog, cfg.root).products}
    texts = {
        r["id"]: r["text"]
        for r in (json.loads(x) for x in paths.DESCRIPTIONS.read_text().splitlines() if x)
    }
    rng = random.Random(seed)
    with_gt = [r for r in rows if r["relevant"]]
    without = [r for r in rows if not r["relevant"]]
    picked = rng.sample(with_gt, min(n // 2, len(with_gt)))
    picked += rng.sample(without, min(n - len(picked), len(without)))
    rng.shuffle(picked)
    from amoblai.dataset.ikea import IkeaDataset

    ds = IkeaDataset.load(paths.RAW)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for b, start in enumerate(range(0, len(picked), size), start=1):
        items = []
        for r in picked[start : start + size]:
            piece = queries[r["room_id"]]["pieces"][r["piece"]]
            items.append(
                {
                    "key": key_of(r["room_id"], r["piece"]),
                    "room_photo": str((paths.RAW / ds.rooms[r["room_id"]].path).resolve()),
                    "piece": piece["piece"],
                    "search": r["query"],
                    "candidates": [
                        {
                            "id": i,
                            "photo": str(catalog[i].photos()[0].resolve()),
                            "description": texts.get(i, ""),
                        }
                        for i in r["ranked"][:TOP]
                    ],
                }
            )
        f = out_dir / f"lote_{b:02d}.json"
        f.write_text(json.dumps({"guide": GUIDE, "items": items}, ensure_ascii=False, indent=1))
        written.append(f)
    meta = {"run": Path(run_dir).name, "method": method, "n": len(picked), "seed": seed}
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=1))
    return written


def validate(answer: Path, batch: Path) -> list[str]:
    try:
        got = json.loads(Path(answer).read_text())
    except json.JSONDecodeError as e:
        return [f"no es JSON: {e}"]
    errors = []
    for item in json.loads(Path(batch).read_text())["items"]:
        grades = got.get(item["key"])
        if not isinstance(grades, dict):
            errors.append(f"{item['key']}: falta")
            continue
        for c in item["candidates"]:
            if grades.get(c["id"]) not in (0, 1, 2):
                errors.append(f"{item['key']} {c['id']}: la nota es 0, 1 o 2")
    return errors


def _dcg(grades: list[int]) -> float:
    return sum((2**g - 1) / log2(i + 2) for i, g in enumerate(grades))


def score(run_dir: Path, method: str, answers: Path = ANSWERS) -> dict[str, Any]:
    """Las métricas con las notas de los jueces: nota media, útil@1 y útil@3 (alguno con nota
    ≥ 1), NDCG@3 graduado (contra el orden ideal de las notas que hay) y el acuerdo con el
    ground truth (¿el anotado recibió un 2? ¿algo que no es el anotado recibió un 2?)."""
    grades: dict[str, dict[str, int]] = {}
    for f in sorted(Path(answers).glob("lote_*.json")):
        grades.update(json.loads(f.read_text()))
    rows = [
        json.loads(x)
        for x in gzip.decompress((Path(run_dir) / "rankings.jsonl.gz").read_bytes()).splitlines()
    ]
    rows = {key_of(r["room_id"], r["piece"]): r for r in rows if r["method"] == method}
    per: dict[str, list] = defaultdict(list)
    for key, g in grades.items():
        r = rows[key]
        ids = r["ranked"][:TOP]
        notes = [int(g[i]) for i in ids]
        ideal = _dcg(sorted(notes, reverse=True))
        group = "con anotado" if r["relevant"] else "sin anotado"
        for gr in ("todas", group):
            per[gr].append(
                {
                    "room": r["room_id"],
                    "nota1": notes[0],
                    "util1": float(notes[0] >= 1),
                    "util3": float(max(notes) >= 1),
                    "exacto3": float(max(notes) == 2),
                    "ndcg3": _dcg(notes) / ideal if ideal else 0.0,
                }
            )
        if r["relevant"]:
            rel = set(r["relevant"])
            for i, n in zip(ids, notes, strict=True):
                per["_anotado" if i in rel else "_otro"].append(n)
    out: dict[str, Any] = {"run": Path(run_dir).name, "method": method, "consultas": {}}
    for gr in ("todas", "con anotado", "sin anotado"):
        vals = per[gr]
        if not vals:
            continue
        rooms = [v["room"] for v in vals]
        m = {"n": len(vals)}
        for name in ("nota1", "util1", "util3", "exacto3", "ndcg3"):
            xs = [v[name] for v in vals]
            m[name] = round(float(np.mean(xs)), 4)
            if name in ("util1", "util3"):
                m[f"{name}_ic95"] = [round(x, 4) for x in bootstrap_ci(xs, rooms)]
        out["consultas"][gr] = m
    if per["_anotado"]:
        out["acuerdo_con_gt"] = {
            "anotados_en_top3": len(per["_anotado"]),
            "anotado_con_2": round(float(np.mean([n == 2 for n in per["_anotado"]])), 4),
            "otros_con_2": round(float(np.mean([n == 2 for n in per["_otro"]])), 4)
            if per["_otro"]
            else None,
        }
    return out


def main(argv: list[str] | None = None) -> int:
    import sys

    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        print("uso: python -m amoblai.evaluation.graded <respuesta.json> <lote.json>")
        return 2
    errors = validate(Path(args[0]), Path(args[1]))
    for e in errors:
        print(f"ERROR: {e}")
    print(f"{len(errors)} errores")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

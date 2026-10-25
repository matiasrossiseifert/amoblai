"""A static page to look through the flow's runs: `datos/resultados/amoblar/index.html`.

Each run (a folder with request.json) reads like a chat, step by step: the request and the
photo, what plan decided to look for, the candidates the search brought for each piece, what
choose picked and why, the image prompt, the final image, the metrics if they were run
(6_metricas_imagen.json, 7_metricas_respuesta.json) and what each step cost. Images go by
relative path (the dataset's photos too), so the page opens from disk with no server; it is
not committed, since it points at files git does not have.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _size(d: dict | None) -> str:
    d = d or {}
    names = (("width", "ancho"), ("depth", "prof."), ("height", "alto"))
    return ", ".join(f"{n} {d[a]:.0f} cm" for a, n in names if d.get(a)) or "sin medidas"


def _type_line(description: str) -> str:
    first = (description or "").splitlines()[0] if description else ""
    return first.removeprefix("Type:").strip()


def _latency(rec: dict | None) -> float | None:
    meta = (rec or {}).get("meta") or {}
    return meta.get("latency_s")


def _tokens(rec: dict | None) -> str:
    u = ((rec or {}).get("meta") or {}).get("usage") or {}
    if not u:
        return ""
    return (
        f"{u.get('input_tokens', 0):,} tokens de entrada, {u.get('output_tokens', 0):,} de salida"
    )


def run_data(run: Path, root: Path, out_dir: Path) -> dict[str, Any] | None:
    """Everything the page shows about one run, with image paths relative to `out_dir`."""
    req = _load(run / "request.json")
    if not req:
        return None

    def rel(p: str | Path | None) -> str | None:
        if not p:
            return None
        p = Path(p)
        p = p if p.is_absolute() else root / p
        return os.path.relpath(p, out_dir) if p.exists() else None

    plan = _load(run / "1_searches.json")
    cands = _load(run / "2_candidates.json")
    choice = _load(run / "3_choice.json")
    scene = _load(run / "4_scene.json")
    image = _load(run / "5_image.json")
    img_metrics = _load(run / "6_metricas_imagen.json")
    ans_metrics = _load(run / "7_metricas_respuesta.json")
    files = [f for f in run.iterdir() if f.is_file()]
    picks = {c.get("piece"): c for c in ((choice or {}).get("answer") or {}).get("choices", [])}
    pieces_plan = ((plan or {}).get("answer") or {}).get("pieces", [])

    search = []
    for n, piece in enumerate((cands or {}).get("pieces", []), start=1):
        pick = picks.get(n) or {}
        ranking = pick.get("ranking") or []
        search.append(
            {
                "piece": piece.get("piece"),
                "candidates": [
                    {
                        "id": h["id"],
                        "name": h.get("name"),
                        "kind": h.get("kind") or h.get("category"),
                        "size": _size(h.get("dimensions_cm")),
                        "type": _type_line(h.get("description", "")),
                        "description": h.get("description", ""),
                        "photo": rel((h.get("photos") or [None])[0]),
                        "chosen": h["id"] == pick.get("id") and pick.get("quantity", 1) > 0,
                        "quantity": pick.get("quantity", 1) if h["id"] == pick.get("id") else None,
                        "rank": ranking.index(h["id"]) + 1 if h["id"] in ranking else None,
                    }
                    for h in piece.get("candidates", [])
                ],
                "chosen_why": pick.get("why"),
                "left_out": pick.get("quantity", 1) == 0,
            }
        )
    steps, step_files = [], []
    for name, rec, f in (
        ("plan", plan, "1_searches.json"),
        ("choose", choice, "3_choice.json"),
        ("scene", scene, "4_scene.json"),
        ("imagen", image, "5_image.json"),
    ):
        if rec is None:
            continue
        sha = hashlib.sha256((run / f).read_bytes()).hexdigest()
        step_files.append((name, sha, (run / f).stat().st_mtime))
        steps.append(
            {
                "step": name,
                "prompt": rec.get("prompt") or rec.get("generator"),
                "model": rec.get("model"),
                "cost": rec.get("cost_usd") or 0.0,
                "latency": _latency(rec),
                "tokens": _tokens(rec),
                "sha": sha,
            }
        )
    final = rel(run / image["image"]) if image and image.get("image") else None
    extras = [
        rel(f)
        for f in sorted(files)
        if f.suffix.lower() in (".jpg", ".png")
        and not f.name.startswith(("2_candidates", "room", "final", "6_recortes"))
    ]
    sha = hashlib.sha256((run / "3_choice.json").read_bytes()).hexdigest() if choice else None
    return {
        "id": run.name,
        "when": time.strftime(
            "%Y-%m-%d %H:%M", time.localtime(max(f.stat().st_mtime for f in files))
        ),
        "request": req.get("request"),
        "photo": rel(run / "room.jpg") or rel(req.get("photo")),
        "views": [v for v in [rel(run / "room_2.jpg")] if v],
        "room": ((plan or {}).get("answer") or {}).get("room"),
        "pieces": [
            {
                "piece": p.get("piece"),
                "why": p.get("why"),
                "kinds": p.get("kinds") or [],
                "limits": {k: p.get(k) for k in ("max_width_cm", "max_depth_cm", "max_height_cm")},
                "query": p.get("query"),
            }
            for p in pieces_plan
        ],
        "search": search,
        "choice_why": ((choice or {}).get("answer") or {}).get("why"),
        "scene": {
            "prompt_version": (scene or {}).get("prompt"),
            "llm": bool((scene or {}).get("model")),
            "text": ((scene or {}).get("answer") or {}).get("prompt"),
            "placements": ((scene or {}).get("answer") or {}).get("placements") or [],
        }
        if scene
        else None,
        "image": {
            "final": final,
            "generator": image.get("generator"),
            "model": image.get("model"),
            "pending": image.get("pending"),
            "attempts": [
                {**a, "image": rel(run / a["image"])} for a in image.get("attempts") or []
            ],
        }
        if image
        else None,
        "extras": [x for x in extras if x],
        "metrics_image": img_metrics,
        "crops": rel(run / "6_recortes.jpg"),
        "metrics_answer": ans_metrics,
        "steps": steps,
        "step_files": step_files,
        "cost": round(sum(s["cost"] for s in steps), 4),
        "latency": round(sum(s["latency"] or 0 for s in steps), 1),
        "choice_sha": sha,
    }


def build(runs_dir: Path, out: Path | None = None, root: Path = Path(".")) -> Path:
    """Write the page for every run under `runs_dir` (newest first)."""
    runs_dir = Path(runs_dir).resolve()
    out = Path(out or runs_dir / "index.html").resolve()
    root = Path(root).resolve()
    runs = [
        r for d in sorted(runs_dir.iterdir()) if d.is_dir() and (r := run_data(d, root, out.parent))
    ]
    runs.sort(key=lambda r: r["when"], reverse=True)
    by_sha: dict[str, list[str]] = {}
    for r in runs:
        if r["choice_sha"]:
            by_sha.setdefault(r["choice_sha"], []).append(r["id"])
    for r in runs:
        r["same_choice"] = [x for x in by_sha.get(r["choice_sha"], []) if x != r["id"]]
    # A step whose file is a copy of another run's (the same plan and choice, another scene) was
    # paid once: it shows as reused and does not add to this run's cost. The original is the
    # run with the shortest name (a variant adds a suffix: experimento -> experimento-libre);
    # file times don't tell, git rewrites them on checkout.
    first: dict[tuple[str, str], tuple[tuple[int, float], str]] = {}
    for r in runs:
        for step, sha, mtime in r.pop("step_files"):
            key, rank = (step, sha), (len(r["id"]), mtime)
            if key not in first or rank < first[key][0]:
                first[key] = (rank, r["id"])
        r["_keys"] = {s["step"]: s.pop("sha", None) for s in r["steps"]}
    for r in runs:
        for s in r["steps"]:
            owner = first.get((s["step"], r["_keys"].get(s["step"])))
            if owner and owner[1] != r["id"]:
                s["reused_from"] = owner[1]
        del r["_keys"]
        r["cost"] = round(sum(s["cost"] for s in r["steps"] if not s.get("reused_from")), 4)
    data = {"built": time.strftime("%Y-%m-%d %H:%M"), "runs": runs}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = Path(__file__).with_name("viewer.html").read_text()
    out.write_text(page.replace("__DATA__", payload).replace("__TITLE__", "Corridas de amoblai"))
    return out

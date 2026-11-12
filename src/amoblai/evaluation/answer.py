"""Las métricas de RAGAS (clase 11) del lado del generador, sobre la respuesta en texto del flujo:
los productos elegidos y su porqué (3_choice.json).

- **faithfulness**: un juez parte el porqué en afirmaciones de hecho y dice cuáles se infieren de
  lo que tuvo el generador al escribirlo (el pedido, la foto del ambiente y, de cada producto
  elegido, su foto y la línea con su kind, su tipo y su medida, que es lo que ve el paso choose):
  sostenidas / afirmaciones (prompts/juez_fidelidad_v2.md).
- **answer relevance**: un juez que no ve el pedido escribe, desde la respuesta (la lista y, si
  la hay, la imagen final), N pedidos que esa respuesta contesta; la métrica es el coseno medio
  (Qwen3-Embedding) entre cada uno y el pedido original (prompts/juez_pedidos_v2.md). Dos varas:
  el coseno del pedido original con pedidos que no tienen nada que ver (image.CONTRAST), que es
  un piso, y con los pedidos que el juez escribió para las respuestas de OTRAS corridas
  (`summary`): si la respuesta propia no supera a las ajenas, la métrica no distingue nada.

Las versiones 1 de los dos jueces (2026-10-23) tenían un ejemplo que coincidía con el pedido
evaluado y le daban al juez la descripción completa, que el generador no ve: sus resultados
quedaron en las corridas viejas (7_metricas_respuesta.json) y no se comparan con estos.

El juez es un LLM que mira imágenes: Claude por la API (pago, `--juez opus --pagar`) o un
subagente de Claude Code (`--juez archivo`, gratis). Con `archivo`, `write_tasks` deja por
corrida y por juez el prompt lleno y las imágenes que hay que mirar
(datos/procesados/juez/<corrida>/<juez>.json); el subagente escribe su JSON en
datos/evaluacion_flujo/juez/<corrida>/<juez>.json y `score` lo lee.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from amoblai import paths
from amoblai.catalog.loader import load_catalog
from amoblai.config import Config
from amoblai.prompts import load_prompt

JUDGES = {"fidelidad": "juez_fidelidad_v2.md", "pedidos": "juez_pedidos_v2.md"}
N_REQUESTS = 3  # como el ejemplo de la clase
JUDGE_DIR = paths.DATOS / "evaluacion_flujo" / "juez" / "v2"
TASK_DIR = paths.PROCESSED / "juez" / "v2"
SUMMARY = paths.DATOS / "resultados" / "evaluacion_respuesta" / "resumen.json"


def run_key(run_dir: Path) -> str:
    """El nombre de una corrida entre los jueces: el de su carpeta, con la variante adelante si
    no es de datos/resultados/amoblar (punta_a_punta/catalogos/todos/x -> "todos__x")."""
    run_dir = Path(run_dir)
    if run_dir.parent.resolve() == paths.RUNS.resolve():
        return run_dir.name
    return f"{run_dir.parent.name}__{run_dir.name}"


def _descriptions() -> dict[str, str]:
    """Las descripciones de los dos catálogos (IKEA y ABO), por id."""
    out = {}
    for f in (paths.DESCRIPTIONS, paths.ABO_CATALOG / "descripciones.jsonl"):
        if f.exists():
            rows = [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
            out.update({r["id"]: r["text"] for r in rows})
    return out


def _type_line(text: str, fallback: str) -> str:
    first = text.splitlines()[0] if text else ""
    return first.removeprefix("Type:").strip() or fallback


def _size(dims: dict | None) -> str:
    d = dims or {}
    words = (("width", "wide"), ("depth", "deep"), ("height", "high"))
    return ", ".join(f"{d[a]:.0f} cm {w}" for a, w in words if d.get(a)) or "size unknown"


def answer_text(choice: dict) -> str:
    """El porqué del paso choose como texto: uno por producto y el de la combinación."""
    lines = [f"- {c['id']}: {c['why']}" for c in choice.get("choices", []) if c.get("why")]
    if choice.get("why"):
        lines.append(f"- The combination: {choice['why']}")
    return "\n".join(lines)


def build_tasks(cfg: Config, run_dir: Path) -> dict[str, dict]:
    """Lo que ve cada juez: {juez: {"prompt", "images", "version"}} (rutas de las imágenes)."""
    run_dir = Path(run_dir)
    choice = json.loads((run_dir / "3_choice.json").read_text())["answer"]
    catalog = {p.id: p for p in load_catalog(cfg.rag.catalog, cfg.root).products}
    texts = _descriptions()
    chosen = [
        catalog[c["id"]]
        for c in choice["choices"]
        if c.get("id") in catalog and c.get("quantity", 1)
    ]
    listing = "\n\n".join(
        f"{p.id} ({p.kind}, {_size(p.info.get('dimensions_cm'))}):\n{texts.get(p.id, '')}"
        for p in chosen
    )
    photos = "\n".join(  # lo que ve choose de cada candidato (steps.choose)
        f"Image {n}: {p.id}: {p.kind or p.category}, "
        f"{_type_line(texts.get(p.id, ''), p.category)}, {_size(p.info.get('dimensions_cm'))}"
        for n, p in enumerate(chosen, start=2)
    )
    fid = load_prompt(JUDGES["fidelidad"], cfg.root)
    ped = load_prompt(JUDGES["pedidos"], cfg.root)
    final = None
    if (run_dir / "5_image.json").exists():
        meta = json.loads((run_dir / "5_image.json").read_text())
        if not meta.get("pending") and (run_dir / meta["image"]).exists():
            final = run_dir / meta["image"]
    return {
        "fidelidad": {
            "version": fid.version,
            "prompt": fid.fill(
                products=photos,
                answer=answer_text(choice),
                request=json.loads((run_dir / "request.json").read_text())["request"],
            ),
            "images": [str(run_dir / "room.jpg"), *[str(p.photos()[0]) for p in chosen]],
        },
        "pedidos": {
            "version": ped.version,
            "prompt": ped.fill(
                products=listing,
                n=N_REQUESTS,
                image="The image is the photo of the room with these products."
                if final
                else "There is no photo of the result: judge from the list.",
            ),
            "images": [str(final)] if final else [],
        },
    }


def write_tasks(cfg: Config, run_dir: Path, out_dir: Path = TASK_DIR) -> list[Path]:
    """Las tareas de los jueces de una corrida, para un subagente (`--juez archivo`)."""
    written = []
    for name, task in build_tasks(cfg, run_dir).items():
        f = Path(out_dir) / run_key(run_dir) / f"{name}.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        answer = JUDGE_DIR / run_key(run_dir) / f"{name}.json"
        f.write_text(json.dumps({**task, "answer_file": str(answer)}, ensure_ascii=False, indent=1))
        written.append(f)
    return written


def judge_with_claude(cfg: Config, run_dir: Path, judge: str, out_dir: Path = JUDGE_DIR) -> Path:
    """Un juez por la API (pago: la llamada pasa por el tope de su cuenta, budget)."""
    from amoblai.furnish.llm import image_block, text_block
    from amoblai.furnish.steps import ask

    task = build_tasks(cfg, run_dir)[judge]
    content = [image_block(Path(p), cfg.furnish.photo_max_side) for p in task["images"]]
    a, data = ask(
        cfg,
        f"eval.juez_{judge}",
        [*content, text_block(task["prompt"])],
        cfg.evaluation.rerankers.get("opus"),
    )
    f = Path(out_dir) / run_key(run_dir) / f"{judge}.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(
        json.dumps(
            {**data, "_juez": a.model, "_costo_usd": a.cost_usd, "_prompt": task["version"]},
            ensure_ascii=False,
            indent=1,
        )
    )
    return f


def faithfulness(claims: list[dict]) -> dict[str, Any]:
    """Afirmaciones sostenidas / afirmaciones (RAGAS), en total y sobre productos vs ambiente."""
    if not claims:
        return {"afirmaciones": 0, "faithfulness": None}
    ok = [bool(c.get("supported")) for c in claims]
    product = [
        bool(c.get("supported")) for c in claims if c.get("about") not in ("room", "request")
    ]
    room = [bool(c.get("supported")) for c in claims if c.get("about") == "room"]
    return {
        "afirmaciones": len(claims),
        "faithfulness": round(sum(ok) / len(ok), 4),
        "sobre_productos": round(sum(product) / len(product), 4) if product else None,
        "sobre_el_ambiente": round(sum(room) / len(room), 4) if room else None,
        "no_sostenidas": [c.get("claim") for c in claims if not c.get("supported")],
    }


def answer_relevance(cfg: Config, request: str, generated: list[str]) -> dict[str, Any]:
    """(1/N) Σ cos(E_gi, E_o) de la clase 11, con Qwen3-Embedding; y la vara: lo mismo con los
    pedidos de contraste en lugar de los generados."""
    from amoblai.evaluation.image import CONTRAST
    from amoblai.infra.budget import ledger_for
    from amoblai.rag.embed import get_embedder
    from amoblai.rag.index import vectors_cached

    if not generated:
        return {"answer_relevance": None}
    emb = get_embedder("qwen3", cfg)
    vecs, _ = vectors_cached(
        [request, *generated, *CONTRAST], emb, cfg, ledger_for(cfg.budget, emb.account)
    )
    orig, gen, con = vecs[0], vecs[1 : 1 + len(generated)], vecs[1 + len(generated) :]
    return {
        "pedidos_generados": generated,
        "answer_relevance": round(float(np.mean(gen @ orig)), 4),
        "vara_contrastes": round(float(np.mean(con @ orig)), 4),
    }


def score(cfg: Config, run_dir: Path, judge_dir: Path = JUDGE_DIR) -> dict[str, Any] | None:
    """Las dos métricas de una corrida con las respuestas de los jueces que haya: escribe
    `7_metricas_respuesta.json`. None si todavía no hay ninguna."""
    run_dir = Path(run_dir)
    answers = {}
    for name in JUDGES:
        f = Path(judge_dir) / run_key(run_dir) / f"{name}.json"
        if f.exists():
            answers[name] = json.loads(f.read_text())
    if not answers:
        return None
    request = json.loads((run_dir / "request.json").read_text())["request"]
    out: dict[str, Any] = {"corrida": run_key(run_dir), "pedido": request}
    if "fidelidad" in answers:
        out["fidelidad"] = faithfulness(answers["fidelidad"].get("claims") or [])
        out["fidelidad"]["juez"] = answers["fidelidad"].get("_juez", "subagente de Claude Code")
    if "pedidos" in answers:
        out["relevancia"] = answer_relevance(cfg, request, answers["pedidos"].get("requests") or [])
        out["relevancia"]["juez"] = answers["pedidos"].get("_juez", "subagente de Claude Code")
    (run_dir / "7_metricas_respuesta.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1)
    )
    return out


def summary(cfg: Config, results: list[dict], out: Path = SUMMARY) -> dict[str, Any]:
    """Las dos métricas sobre varias corridas: la media y, para la answer relevance, la vara
    cruzada (el pedido de cada corrida contra los pedidos que el juez escribió para las otras
    corridas con otro pedido). Escribe `resumen.json`."""
    from amoblai.infra.budget import ledger_for
    from amoblai.rag.embed import get_embedder
    from amoblai.rag.index import vectors_cached

    fid = [
        r["fidelidad"] for r in results if r.get("fidelidad", {}).get("faithfulness") is not None
    ]
    rel = [r for r in results if r.get("relevancia", {}).get("answer_relevance") is not None]
    out_data: dict[str, Any] = {"corridas": len(results), "por_corrida": results}
    if fid:
        claims = sum(f["afirmaciones"] for f in fid)
        held = sum(round(f["faithfulness"] * f["afirmaciones"]) for f in fid)
        out_data["faithfulness"] = {
            "media_por_corrida": round(float(np.mean([f["faithfulness"] for f in fid])), 4),
            "afirmaciones": claims,
            "sostenidas": held,
            "global": round(held / claims, 4) if claims else None,
        }
    if rel:
        emb = get_embedder("qwen3", cfg)
        ledger = ledger_for(cfg.budget, emb.account)
        own, cross = [], []
        for r in rel:
            others = [
                g
                for o in rel
                if o["pedido"] != r["pedido"]
                for g in o["relevancia"]["pedidos_generados"]
            ]
            own.append(r["relevancia"]["answer_relevance"])
            if others:
                vecs, _ = vectors_cached([r["pedido"], *others], emb, cfg, ledger)
                cross.append(float(np.mean(vecs[1:] @ vecs[0])))
        out_data["answer_relevance"] = {
            "media": round(float(np.mean(own)), 4),
            "vara_cruzada": round(float(np.mean(cross)), 4) if cross else None,
            "vara_contrastes": round(
                float(np.mean([r["relevancia"]["vara_contrastes"] for r in rel])), 4
            ),
            "supera_a_la_cruzada": sum(o > c for o, c in zip(own, cross, strict=False)),
        }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(out_data, ensure_ascii=False, indent=1))
    return out_data

"""De punta a punta sobre ambientes reales vacíos: el mismo pedido y la misma foto por variantes
del flujo (otro catálogo, otra cantidad de candidatos), y un juez que compara las listas.

No hay ground truth para un ambiente vacío: nadie sabe cuál es "el" sofá correcto. Lo que se
puede medir es cuál de dos listas mandaría un diseñador al cliente. El juez (Claude Opus 5.5,
prompts/juez_listas_v1.md) ve la foto, el pedido y las dos listas (foto de cada producto, su
línea Type, su medida y cuántas unidades), sin saber de qué variante es cada una, y se le
pregunta en los dos órdenes para cancelar el sesgo de posición: una variante gana un ambiente
si gana en los dos órdenes; si cada orden elige otra, es empate. Además puntúa cada producto
(2 cumple, 1 aceptable, 0 no sirve) y cada lista en tres criterios de 1 a 5.

El plan no depende del catálogo (pide kinds y escribe la consulta ideal), así que todas las
variantes parten del mismo plan: la diferencia entre listas sale solo del retrieve y el choose.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import yaml

from amoblai.config import Config
from amoblai.furnish import steps as st
from amoblai.furnish.flow import run_flow
from amoblai.furnish.llm import image_block, text_block
from amoblai.prompts import load_prompt

JUDGE_PROMPT = "juez_listas_v1.md"


def load_rooms(path: Path) -> list[dict]:
    """Los ambientes con su pedido: [{slug, foto, pedido}]."""
    return yaml.safe_load(Path(path).read_text())["ambientes"]


def run_variant(
    cfg: Config,
    rooms: list[dict],
    out: Path,
    plan_from: Path | None = None,
    workers: int = 4,
    log=print,
) -> list[Path]:
    """plan → retrieve → choose de cada ambiente en `out/<slug>`. Con `plan_from`, el plan de
    `plan_from/<slug>` (otra variante) en vez de uno nuevo."""
    cfg.furnish.steps = ["plan", "retrieve", "choose"]

    def one(room: dict) -> Path:
        d = out / room["slug"]
        d.mkdir(parents=True, exist_ok=True)
        if plan_from is not None and not (d / "1_searches.json").exists():
            shutil.copy(plan_from / room["slug"] / "1_searches.json", d / "1_searches.json")
        run_flow(cfg.path(room["foto"]), room["pedido"], cfg, d, log=lambda m: None)
        log(f"{out.name}/{room['slug']}: listo")
        return d

    # el primero solo: carga el embedder y el índice antes de abrir los hilos
    first = [one(rooms[0])] if rooms else []
    with ThreadPoolExecutor(workers) as pool:
        return first + list(pool.map(one, rooms[1:]))


def product_list(run_dir: Path) -> list[dict]:
    """Lo que el flujo eligió en una corrida: la lista de compra, en orden."""
    found = json.loads((run_dir / "2_candidates.json").read_text())
    choice = json.loads((run_dir / "3_choice.json").read_text())
    return [
        {
            "id": h.id,
            "type": st.type_line(h),
            "size": st.size_text(h),
            "units": spec.get("quantity", 1),
            "photo": h.photos[0],
        }
        for spec, h in st.picks(found, choice)
    ]


def _lines(items: list[dict], first: int) -> str:
    return "\n".join(
        f"image {n}. {it['type']}, {it['size']}"
        + (f", {it['units']} units" if it["units"] > 1 else "")
        for n, it in enumerate(items, first)
    )


def judge(cfg: Config, llm: dict, room: dict, list_a: list[dict], list_b: list[dict]) -> dict:
    """Una pasada del juez (A y B en este orden); la respuesta queda en caché."""
    tmpl = load_prompt(JUDGE_PROMPT, cfg.root)
    a_last = 1 + len(list_a)
    text = tmpl.fill(
        request=room["pedido"],
        a_last=a_last,
        b_first=a_last + 1,
        b_last=a_last + len(list_b),
        list_a=_lines(list_a, 2),
        list_b=_lines(list_b, a_last + 1),
    )
    key = {
        "llm": llm,
        "prompt": tmpl.version,
        "text": text,
        "photos": [room["foto"], *(it["photo"] for it in [*list_a, *list_b])],
    }
    sha = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:24]
    f = Path(cfg.cache_dir) / "juez_listas" / f"{sha}.json"
    if f.exists():
        return json.loads(f.read_text())
    content = [image_block(cfg.path(room["foto"]), cfg.furnish.photo_max_side)]
    content += [image_block(cfg.path(it["photo"]), 512) for it in [*list_a, *list_b]]
    a, data = st.ask(cfg, "eval.juez_listas", [*content, text_block(text)], llm)
    out = {**data, "model": a.model, "cost_usd": a.cost_usd}
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(out, ensure_ascii=False))
    return out


def _side(ans: dict, side: str, n: int) -> dict:
    s = ans.get(side) or {}
    grades = [int(g) for g in (s.get("grades") or [])][:n]
    return {
        "grades": grades,
        **{k: float(s[k]) for k in ("request", "room", "together") if k in s},
    }


def compare(
    cfg: Config,
    llm: dict,
    rooms: list[dict],
    root: Path,
    a: str,
    b: str,
    workers: int = 4,
) -> dict[str, Any]:
    """La variante `a` contra la `b` (carpetas `root/a`, `root/b`) en cada ambiente, en los dos
    órdenes. Devuelve el resumen y el detalle por ambiente."""

    def one(room: dict) -> dict:
        la = product_list(root / a / room["slug"])
        lb = product_list(root / b / room["slug"])
        ab = judge(cfg, llm, room, la, lb)
        ba = judge(cfg, llm, room, lb, la)
        votes = [
            {"A": a, "B": b}.get(ab.get("preferred"), "tie"),
            {"A": b, "B": a}.get(ba.get("preferred"), "tie"),
        ]
        winner = votes[0] if votes[0] == votes[1] else "tie"
        sides = {
            a: [_side(ab, "A", len(la)), _side(ba, "B", len(la))],
            b: [_side(ab, "B", len(lb)), _side(ba, "A", len(lb))],
        }
        return {
            "slug": room["slug"],
            "ganador": winner,
            "votos": votes,
            "listas": {a: la, b: lb},
            "puntajes": sides,
            "por_que": [ab.get("why"), ba.get("why")],
            "costo_usd": round((ab.get("cost_usd") or 0) + (ba.get("cost_usd") or 0), 4),
        }

    with ThreadPoolExecutor(workers) as pool:
        detail = list(pool.map(one, rooms))

    def summary(v: str) -> dict:
        grades = [g for d in detail for s in d["puntajes"][v] for g in s["grades"]]
        crit = {
            k: round(
                sum(s[k] for d in detail for s in d["puntajes"][v] if k in s)
                / max(1, sum(1 for d in detail for s in d["puntajes"][v] if k in s)),
                3,
            )
            for k in ("request", "room", "together")
        }
        return {
            "gana": sum(d["ganador"] == v for d in detail),
            "productos_por_lista": round(sum(len(d["listas"][v]) for d in detail) / len(detail), 2),
            "util": round(sum(g == 2 for g in grades) / max(1, len(grades)), 3),
            "aceptable": round(sum(g >= 1 for g in grades) / max(1, len(grades)), 3),
            **crit,
        }

    votes = [x for d in detail for x in d["votos"]]
    return {
        "a": a,
        "b": b,
        "ambientes": len(detail),
        "empates": sum(d["ganador"] == "tie" for d in detail),
        "resumen": {a: summary(a), b: summary(b)},
        # cuánto coinciden los dos órdenes: si el juez cambia de opinión al cambiar el orden,
        # su veredicto no vale mucho (sesgo de posición)
        "acuerdo_entre_ordenes": round(
            sum(d["votos"][0] == d["votos"][1] for d in detail) / len(detail), 3
        ),
        "votos_por_posicion_A": round(
            sum(1 for d in detail if d["votos"][0] == a)
            + sum(1 for d in detail if d["votos"][1] == b),
            3,
        )
        / max(1, len(votes)),
        "costo_usd": round(sum(d["costo_usd"] for d in detail), 4),
        "detalle": detail,
    }


def _style(text: str | None) -> list[str]:
    for line in (text or "").splitlines():
        if line.startswith("Style:"):
            return [x.strip().lower() for x in line.split(":", 1)[1].split(",") if x.strip()]
    return []


def diagnostics(variant_dir: Path) -> dict[str, Any]:
    """Lo que se puede medir gratis, sin juez, sobre las corridas guardadas de una variante (los
    ambientes vacíos reales): en qué puesto del retrieval estaba el producto que eligió choose
    (¿hace trabajo el que elige?, ¿se usan los candidatos 4 y 5?), cuántas piezas dejó afuera
    (negative rejection), qué tan cerca del catálogo quedan las consultas que escribe el plan,
    cuántos elegidos no tienen ninguna medida (el tamaño no se puede verificar), en cuántas piezas
    hay candidatos repetidos del mismo modelo y si el elegido tiene el primer estilo que pidió
    el plan."""
    import numpy as np

    position: dict[str, int] = {}
    first_cos, no_size, style_first, from_abo = [], [], [], []
    pieces = left_out = repeated = rooms = 0
    for run in sorted(Path(variant_dir).glob("*/")):
        if not (run / "3_choice.json").exists():
            continue
        rooms += 1
        found = json.loads((run / "2_candidates.json").read_text())["pieces"]
        choices = json.loads((run / "3_choice.json").read_text())["answer"]["choices"]
        for piece, choice in zip(found, choices, strict=True):
            pieces += 1
            cands = piece["candidates"]
            first_cos.append(cands[0]["score"])
            names = [c["name"] for c in cands if not c["id"].startswith("abo-")]
            repeated += len(names) != len(set(names))
            if not st.quantity(choice):
                left_out += 1
                continue
            rank = next(i for i, c in enumerate(cands, 1) if c["id"] == choice["id"])
            position[str(rank)] = position.get(str(rank), 0) + 1
            chosen = cands[rank - 1]
            dims = chosen.get("dimensions_cm") or {}
            no_size.append(not any(dims.get(a) for a in ("width", "depth", "height")))
            from_abo.append(chosen["id"].startswith("abo-"))
            asked = _style(piece["spec"].get("query"))
            if asked:
                style_first.append(asked[0] in _style(chosen.get("description")))
    chosen_n = sum(position.values())
    return {
        "variante": Path(variant_dir).name,
        "ambientes": rooms,
        "piezas": pieces,
        "piezas_dejadas_afuera": left_out,
        "puesto_del_elegido": {k: position[k] for k in sorted(position)},
        "elegido_es_el_primero": round(position.get("1", 0) / chosen_n, 4) if chosen_n else None,
        "elegido_en_puestos_4_y_5": round(
            (position.get("4", 0) + position.get("5", 0)) / chosen_n, 4
        )
        if chosen_n
        else None,
        "coseno_del_primero": {
            "mediana": round(float(np.median(first_cos)), 4),
            "p10": round(float(np.quantile(first_cos, 0.1)), 4),
            "p90": round(float(np.quantile(first_cos, 0.9)), 4),
        },
        "elegidos_sin_ninguna_medida": round(float(np.mean(no_size)), 4),
        "piezas_con_candidatos_del_mismo_modelo": repeated,
        "elegido_tiene_el_primer_estilo_pedido": round(float(np.mean(style_first)), 4),
        "elegidos_de_abo": round(float(np.mean(from_abo)), 4),
    }

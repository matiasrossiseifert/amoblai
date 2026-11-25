"""amoblai · la web: landing, nuevo ambiente, avance en vivo, resultado, historial, ajustes y la
vista por dentro de cada corrida (/dev).

Usa el código, el catálogo y el .env de este repo. Corre el flujo con la configuración final
(datos/configs/amoblai.yaml) y el modelo de imagen elegido en Ajustes (gpt-image-2 o Nano Banana 2);
los textos que muestra (por qué cada producto y, por dentro, cómo leyó el ambiente y la idea) los
traduce Claude Sonnet al terminar la elección.

    uv run --group apps python apps/web/server.py      (http://127.0.0.1:8000)

Las corridas de la web quedan en apps/web/corridas/<id>/ y su gasto en apps/web/gastos.jsonl, con
los topes de Ajustes (todo fuera de git). También muestra las corridas de la terminal
(datos/resultados/amoblar/) sin tocarlas: su traducción queda en apps/web/.cache/.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
TP = HERE.parents[1]  # la raíz del repo
WEB, RUNS, CACHE = HERE / "web", HERE / "corridas", HERE / ".cache"
LEDGER = HERE / "gastos.jsonl"  # el gasto de la web, aparte del de la terminal
ENV_FILE = TP / ".env"
PORT = int(os.environ.get("AMOBLAI_WEB_PORT", "8000"))
KEYS = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "fal": "FAL_KEY"}
NAMES = {"anthropic": "Anthropic", "openai": "OpenAI", "fal": "fal"}
# Los modelos de imagen de Ajustes: el generador de la config, su cuenta y lo que cuesta un
# intento (gpt-image-2 en calidad media: de 8 a 16 centavos, 13 en promedio en 27 intentos).
IMAGE_MODELS = {
    "openai": {"nombre": "gpt-image-2", "cuenta": "openai", "intento": 0.13},
    "nano_banana_2": {"nombre": "Nano Banana 2", "cuenta": "fal", "intento": 0.08},
}
CAP = 5.0  # US$ por cuenta para la web, hasta que se cambie en Ajustes
TERM = "terminal-"  # las corridas de la terminal, en las URLs: /ambientes/terminal-<carpeta>
os.chdir(TP)  # las rutas de la config (cachés, catálogo) son relativas a la raíz del repo

import httpx  # noqa: E402
import uvicorn  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from fastapi import FastAPI, File, Form, HTTPException, UploadFile  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse, Response  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

from amoblai import paths  # noqa: E402
from amoblai.config import load_config  # noqa: E402
from amoblai.furnish import steps as st  # noqa: E402
from amoblai.furnish.flow import run_flow  # noqa: E402
from amoblai.furnish.llm import text_block  # noqa: E402
from amoblai.infra.budget import BudgetExceeded, Ledger  # noqa: E402
from amoblai.infra.http import ProviderUnavailable  # noqa: E402
from amoblai.prompts import PROMPTS  # noqa: E402

load_dotenv(ENV_FILE, override=False)
TERMINAL = (TP / paths.RUNS).resolve()

# Los 43 tipos del catálogo, como los diría alguien que está amoblando.
KIND_ES = {
    "TV stand": "mueble de TV",
    "armchair": "sillón",
    "bar stool": "banqueta alta",
    "basket": "canasto",
    "bench": "banco",
    "bookcase": "biblioteca",
    "candle holder": "portavelas",
    "ceiling lamp": "plafón",
    "coffee table": "mesa ratona",
    "console table": "mesa consola",
    "curtains": "cortinas",
    "cushion": "almohadón",
    "desk": "escritorio",
    "desk chair": "silla de escritorio",
    "desk lamp": "lámpara de escritorio",
    "dining chair": "silla de comedor",
    "dining table": "mesa de comedor",
    "display cabinet": "vitrina",
    "dresser": "cómoda",
    "file cabinet": "cajonera",
    "floor lamp": "lámpara de pie",
    "low stool": "banqueta",
    "mirror": "espejo",
    "nightstand": "mesa de luz",
    "ottoman": "puf",
    "pendant lamp": "lámpara colgante",
    "picture frame": "portarretratos",
    "plant": "planta",
    "plant pot": "maceta",
    "rug": "alfombra",
    "side table": "mesa auxiliar",
    "sideboard": "aparador",
    "sofa": "sofá",
    "sofa bed": "sofá cama",
    "storage cabinet": "armario",
    "table lamp": "lámpara de mesa",
    "throw": "manta",
    "vase": "florero",
    "wall art": "cuadro",
    "wall clock": "reloj de pared",
    "wall lamp": "aplique",
    "wall shelf": "estante",
    "wardrobe": "ropero",
}
SAMPLES = [
    "datos/ambientes_vacios/publicas/living-laminado-ventanas-persianas.jpg",
    "datos/ambientes_vacios/publicas/living-parquet-balcon-toldos.jpg",
    "datos/ambientes_vacios/publicas/living-comedor-casa-nueva-escalera.jpg",
    "datos/ambientes_vacios/publicas/escritorio-paredes-amarillas-alfombra-azul.jpg",
    "datos/ambientes_vacios/ambiente1-caballito/caballito1.jpg",
    "datos/ambientes_vacios/ambiente2-alvear/alvear1.jpg",
]
STEPS = [  # (clave, título, archivo que deja)
    ("plan", "Leyendo el ambiente", "1_searches.json"),
    ("retrieve", "Buscando en el catálogo", "2_candidates.json"),
    ("choose", "Eligiendo los muebles", "3_choice.json"),
    ("generate", "Dibujando el ambiente", "5_image.json"),
]
FLOW_LOCK = threading.Lock()  # una corrida a la vez: los modelos de la búsqueda son uno solo


# configuración y claves ---------------------------------------------------------------------------


def has_key(account: str) -> bool:
    return bool(os.environ.get(KEYS[account], "").strip())


# Preguntar algo gratis con la clave: sirve para saber si el proveedor la acepta.
CHECKS = {
    "anthropic": ("https://api.anthropic.com/v1/models?limit=1", lambda k: {"x-api-key": k, "anthropic-version": "2023-06-01"}),
    "openai": ("https://api.openai.com/v1/models", lambda k: {"Authorization": f"Bearer {k}"}),
    "fal": ("https://api.fal.ai/v1/models/pricing?endpoint_id=fal-ai/nano-banana-2/edit", lambda k: {"Authorization": f"Key {k}"}),
}
VERIFIED: dict[tuple[str, str], tuple[float, bool | None]] = {}


def key_ok(account: str) -> bool | None:
    """True si el proveedor acepta la clave, False si la rechaza (401), None si no se pudo preguntar."""
    k = os.environ.get(KEYS[account], "").strip()
    if not k:
        return False
    hit = VERIFIED.get((account, k))
    if hit and time.time() - hit[0] < 300:
        return hit[1]
    url, headers = CHECKS[account]
    try:
        code = httpx.get(url, headers=headers(k), timeout=10).status_code
        ok = True if code < 400 else False if code == 401 else None
    except httpx.HTTPError:
        ok = None
    VERIFIED[(account, k)] = (time.time(), ok)
    return ok


PREFS = HERE / "ajustes.json"  # lo que se elige en Ajustes, fuera de git


def prefs() -> dict:
    """Lo que se elige en Ajustes: intentos y modelo de la imagen, y el tope de gasto de cada cuenta."""
    base = int(load_config(TP / paths.CONFIG).furnish.room_check["attempts"])
    saved = read(PREFS) or {}
    caps = saved.get("topes") or {}
    return {
        "intentos": int(saved.get("intentos") or base),
        "intentos_proyecto": base,
        "imagen": saved.get("imagen") if saved.get("imagen") in IMAGE_MODELS else "openai",
        "topes": {a: float(caps.get(a) or CAP) for a in KEYS},
    }


def image_account() -> str:
    return IMAGE_MODELS[prefs()["imagen"]]["cuenta"]


def flow_config(with_image: bool):
    p = prefs()
    over: dict = {
        "furnish": {"generator": p["imagen"], "room_check": {"attempts": p["intentos"]}},
        "budget": {"allow_paid": True, "ledger": str(LEDGER), "accounts": p["topes"]},
    }
    if not with_image:
        over["furnish"]["steps"] = ["plan", "retrieve", "choose"]
    return load_config(TP / paths.CONFIG, over)


def save_env(values: dict[str, str]) -> None:
    """Escribe las claves en .env: reemplaza la línea activa de cada una o la agrega al final."""
    lines = ENV_FILE.read_text().splitlines() if ENV_FILE.exists() else []
    pending = dict(values)
    for i, line in enumerate(lines):
        name = line.split("=", 1)[0].strip()
        if not line.lstrip().startswith("#") and name in pending:
            lines[i] = f"{name}={pending.pop(name)}"
    lines += [f"{k}={v}" for k, v in pending.items()]
    ENV_FILE.write_text("\n".join(lines) + "\n")


def status() -> dict:
    p = prefs()
    keys, spend = {}, {}
    for account, env in KEYS.items():
        v = os.environ.get(env, "").strip()
        keys[account] = {"cargada": bool(v), "final": v[-4:] if v else "", "valida": key_ok(account) if v else None}
        cap = p["topes"][account]
        spend[account] = {"gastado": round(Ledger(LEDGER, cap, account).spent(), 2), "tope": cap}
    return {"claves": keys, "gasto": spend, "modelos": IMAGE_MODELS, **p}


# imágenes ---------------------------------------------------------------------------------------------


def resized(src: Path, width: int) -> Path:
    """`src` en JPEG de `width` px de ancho como mucho, en la caché (por ruta, fecha y ancho)."""
    key = hashlib.sha1(f"{src}|{src.stat().st_mtime_ns}|{width}".encode()).hexdigest()[:20]
    out = CACHE / "img" / f"{key}.jpg"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        im.thumbnail((width, width * 4))
        im.save(out, "JPEG", quality=86, optimize=True)
    return out


def inside(base: Path, rel: str) -> Path:
    p = (base / rel).resolve()
    if not p.is_relative_to(base) or not p.is_file():
        raise HTTPException(404)
    return p


def tp_url(rel: str, w: int = 480) -> str:
    return f"/archivo?p={quote(rel)}&w={w}"


# dónde está cada corrida ----------------------------------------------------------------------------


def read(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def locate(run_id: str) -> tuple[Path, str]:
    """La carpeta de una corrida y de dónde viene: "web" (apps/web/corridas/<id>) o "terminal"
    (datos/resultados/amoblar/<carpeta>, con el prefijo terminal- en la URL)."""
    if run_id.startswith(TERM):
        base, origin, name, marker = TERMINAL, "terminal", run_id[len(TERM) :], "request.json"
    else:
        base, origin, name, marker = RUNS, "web", run_id, "web.json"
    out = (base / name).resolve()
    if out.parent != base or not (out / marker).is_file():
        raise HTTPException(404)
    return out, origin


def tr_file(out: Path, origin: str) -> Path:
    """La traducción de los textos: en la corrida de la web, o en la caché (las de la terminal no se tocan)."""
    return out / "traduccion.json" if origin == "web" else CACHE / "traducciones" / f"{out.name}.json"


def meta_path(out: Path) -> Path:
    return out / "web.json"


def write_meta(out: Path, **changes) -> dict:
    m = {**(read(meta_path(out)) or {}), **changes}
    meta_path(out).write_text(json.dumps(m, ensure_ascii=False, indent=1))
    return m


def meta(out: Path, origin: str) -> dict:
    """Lo que la web sabe de la corrida (web.json); para las de la terminal, lo arma de sus archivos."""
    if origin == "web":
        return read(meta_path(out)) or {}
    req = read(out / "request.json") or {}
    t0 = (out / "request.json").stat().st_mtime
    img = read(out / "5_image.json") or {}
    done = (out / "3_choice.json").exists()
    photo = str(req.get("photo") or "")
    return {
        "pedido": req.get("request", ""),
        "creado": datetime.fromtimestamp(t0).isoformat(timespec="seconds"),
        "creado_ts": t0,
        "con_imagen": bool(img) and not img.get("pending"),
        "estado": "listo" if done else "error",
        "error": None if done else "La corrida quedó a medias. Se retoma desde la terminal, con el mismo comando.",
        "terminado_ts": max((f.stat().st_mtime for f in out.glob("[1-5]_*.json")), default=t0),
        "via": "interfaz vieja" if out.name.startswith("app-") or "/gradio/" in photo else "terminal",
    }


def live_state(run_id: str, m: dict) -> tuple[str, str | None]:
    estado = m.get("estado", "listo")
    if estado in ("corriendo", "en cola") and run_id not in JOBS:
        return "error", m.get("error") or "La corrida se interrumpió (se cerró el servidor). Podés retomarla."
    return estado, m.get("error")


def run_cost(out: Path, origin: str) -> float:
    total = sum((read(p) or {}).get("cost_usd") or 0 for p in out.glob("[1-5]_*.json"))
    return total + ((read(tr_file(out, origin)) or {}).get("costo") or 0)


# lo que muestra una corrida ------------------------------------------------------------------------


def clean_name(name: str) -> str:
    """Los títulos de Amazon son de vendedor: sin la marca adelante ni el detalle después de la coma."""
    name = re.sub(r"^Amazon Brand\s*[–-]\s*", "", name or "").strip()
    short = re.split(r",| - | – |\(", name)[0].strip()
    return short if len(short) >= 4 else name


def size_of(it: dict) -> dict | None:
    d = it.get("dimensions_cm") or {}
    out = {k: round(d[k]) for k in ("width", "depth", "height") if d.get(k)}
    return out or None


def store(product_id: str) -> str:
    return "Amazon" if product_id.startswith("abo-") else "IKEA"


def limits(piece: dict) -> dict:
    return {k[4:-3]: piece[k] for k in ("max_width_cm", "max_depth_cm", "max_height_cm") if piece.get(k)}


def products(out: Path, tr: dict | None) -> list[dict]:
    found, choice = read(out / "2_candidates.json"), read(out / "3_choice.json")
    if not (found and choice):
        return []
    whys = (tr or {}).get("porque") or []
    items = []
    for i, (piece, c) in enumerate(zip(found["pieces"], choice["answer"]["choices"], strict=True)):
        qty = st.quantity(c)
        if not qty:
            continue  # el que elige la dejó afuera
        it = next((h for h in piece["candidates"] if h["id"] == c["id"]), {})
        kind = it.get("kind") or it.get("category") or ""
        items.append(
            {
                "id": c["id"],
                "nombre": clean_name(it.get("name") or c["id"]),
                "tipo": KIND_ES.get(kind, kind),
                "medidas": size_of(it),
                "tienda": store(c["id"]),
                "cantidad": qty,
                "porque": (whys[i] if i < len(whys) and whys[i] else c.get("why", "")),
                "foto": tp_url(it["photos"][0]) if it.get("photos") else None,
            }
        )
    return items


def pieces(out: Path) -> list[dict]:
    plan = read(out / "1_searches.json")
    if not plan:
        return []
    rows = []
    for p in plan["answer"]["pieces"]:
        kinds = [KIND_ES.get(k, k) for k in p.get("kinds") or []]
        rows.append({"tipo": " o ".join(kinds) or "a elegir", "hasta": limits(p)})
    return rows


def run_state(run_id: str) -> dict:
    out, origin = locate(run_id)
    m = meta(out, origin)
    with_image = m.get("con_imagen", True)
    estado, error = live_state(run_id, m)
    start = m.get("creado_ts", time.time())
    steps, prev, current_found = [], start, False
    for key, title, file in STEPS if with_image else STEPS[:3]:
        f = out / file
        if f.exists():
            t = f.stat().st_mtime
            steps.append(
                {"clave": key, "titulo": title, "estado": "hecho", "segundos": round(max(0, t - prev))}
            )
            prev = max(prev, t)
        else:
            s = "pendiente"
            if not current_found:
                current_found = True
                s = {"corriendo": "activo", "en cola": "pendiente", "error": "error"}.get(estado, "pendiente")
            steps.append({"clave": key, "titulo": title, "estado": s})
    tr = read(tr_file(out, origin))
    found = read(out / "2_candidates.json") or {}
    img = read(out / "5_image.json") or {}
    # final.png aparece con cada intento; la imagen vale cuando el paso dejó su registro
    final = next(iter(sorted(out.glob("final.*"))), None) if img and not img.get("pending") else None
    plan = read(out / "1_searches.json")
    choice = read(out / "3_choice.json")
    end = m.get("terminado_ts") or (time.time() if estado in ("corriendo", "en cola") else prev)
    return {
        "id": run_id,
        "origen": origin,
        "via": m.get("via", "web"),
        "pedido": m.get("pedido", ""),
        "creado": m.get("creado"),
        "estado": estado,
        "error": error,
        "segundos": round(max(0, end - start)),
        "con_imagen": with_image,
        "pasos": steps,
        "intento": len(list(out.glob("final_intento_*.png"))) + 1 if not final else None,
        "antes": f"/corridas/{run_id}/room.jpg?w=1600" if (out / "room.jpg").exists() else None,
        "despues": f"/corridas/{run_id}/{final.name}?w=1600" if final else None,
        "descarga": f"/corridas/{run_id}/{final.name}" if final else None,
        "alineada": bool((img.get("room_check") or {}).get("ok")),
        "ambiente": (tr or {}).get("ambiente") or (plan or {}).get("answer", {}).get("room"),
        "resumen": (tr or {}).get("resumen") or (choice or {}).get("answer", {}).get("why"),
        "traducido": bool(tr),
        "piezas": pieces(out),
        "lista": products(out, tr),
        "faltan": (tr or {}).get("faltan") or found.get("empty") or [],
        "costo": round(run_cost(out, origin), 2),
    }


# por dentro: cada etapa con lo que recibió y lo que devolvió ------------------------------------


def usage(rec: dict) -> dict | None:
    u = (rec.get("meta") or {}).get("usage") or {}
    if not u:
        return None
    cached = (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
    return {
        "entrada": (u.get("input_tokens") or u.get("prompt_tokens") or 0) + cached,
        "salida": u.get("output_tokens") or u.get("completion_tokens") or 0,
        "pensando": (u.get("output_tokens_details") or {}).get("thinking_tokens") or 0,
    }


def llm_step(rec: dict) -> dict:
    """Modelo, prompt, costo, segundos y tokens de un paso (los registros de 1_ a 5_)."""
    m = rec.get("meta") or {}
    return {
        "modelo": rec.get("model"),
        "prompt": rec.get("prompt"),
        "costo": round(rec.get("cost_usd") or 0, 4),
        "segundos": m.get("latency_s"),
        "tokens": usage(rec),
        "imagenes": m.get("images"),
    }


def candidate(h: dict, rank: int, chosen_id: str | None, ranking: list) -> dict:
    kind = h.get("kind") or h.get("category") or ""
    return {
        "puesto": rank,
        "id": h["id"],
        "nombre": clean_name(h.get("name") or h["id"]),
        "nombre_completo": h.get("name") or h["id"],
        "tipo": KIND_ES.get(kind, kind),
        "tienda": store(h["id"]),
        "medidas": size_of(h),
        "puntaje": round(h["score"], 3) if h.get("score") is not None else None,
        "descripcion": h.get("description") or "",
        "foto": tp_url(h["photos"][0], 360) if h.get("photos") else None,
        "elegido": h["id"] == chosen_id,
        "ranking": ranking.index(h["id"]) + 1 if h["id"] in ranking else None,
    }


def dev_state(run_id: str) -> dict:
    out, origin = locate(run_id)
    s = run_state(run_id)
    m = meta(out, origin)
    cfg = load_config(TP / paths.CONFIG)
    tr = read(tr_file(out, origin)) or {}
    plan, found, choice, scene, img = (
        read(out / f) for f in ("1_searches.json", "2_candidates.json", "3_choice.json", "4_scene.json", "5_image.json")
    )
    choices = ((choice or {}).get("answer") or {}).get("choices") or []
    whys_es = tr.get("porque") or []
    stages: dict = {}

    if plan:
        a = plan.get("answer") or {}
        stages["plan"] = {
            **llm_step(plan),
            "ambiente": a.get("room", ""),
            "ambiente_es": tr.get("ambiente"),
            "desconocidos": plan.get("unknown_kinds") or [],
            "piezas": [
                {
                    "pieza": p.get("piece", ""),
                    "tipos": [KIND_ES.get(k, k) for k in p.get("kinds") or []],
                    "hasta": limits(p),
                    "porque": p.get("why", ""),
                    "ficha": p.get("query", ""),
                }
                for p in a.get("pieces") or []
            ],
        }

    if found:
        t1, t2 = ((out / f).stat().st_mtime if (out / f).exists() else 0 for f in ("1_searches.json", "2_candidates.json"))
        rows = []
        for i, p in enumerate(found["pieces"]):
            c = choices[i] if i < len(choices) else {}
            chosen_id = c.get("id") if c and st.quantity(c) else None
            rows.append(
                {
                    "pieza": p["piece"],
                    "tipos": [KIND_ES.get(k, k) for k in (p.get("spec") or {}).get("kinds") or []],
                    "candidatos": [
                        candidate(h, j, chosen_id, c.get("ranking") or []) for j, h in enumerate(p["candidates"], 1)
                    ],
                }
            )
        stages["busqueda"] = {
            "metodo": " + ".join([cfg.rag.embedder, *cfg.rag.hybrid]),
            "por_pieza": cfg.furnish.candidates,
            "segundos": round(t2 - t1, 1) if 0 <= t2 - t1 < 600 else None,
            "piezas": rows,
            "vacias": found.get("empty") or [],
        }

    if choice:
        rows = []
        for i, c in enumerate(choices):
            p = found["pieces"][i] if found and i < len(found["pieces"]) else {"piece": "", "candidates": []}
            by_id = {h["id"]: (j, h) for j, h in enumerate(p["candidates"], 1)}
            rank, h = by_id.get(c.get("id"), (None, {}))
            rows.append(
                {
                    "pieza": p["piece"],
                    "id": c.get("id"),
                    "nombre": clean_name(h.get("name") or c.get("id") or ""),
                    "foto": tp_url(h["photos"][0], 240) if h.get("photos") else None,
                    "cantidad": st.quantity(c),
                    "puesto": rank,
                    "ranking": [
                        {
                            "id": r,
                            "puesto": by_id[r][0] if r in by_id else None,
                            "nombre": clean_name(by_id[r][1].get("name") or r) if r in by_id else r,
                        }
                        for r in c.get("ranking") or []
                    ],
                    "porque": c.get("why", ""),
                    "porque_es": whys_es[i] if i < len(whys_es) else None,
                }
            )
        stages["eleccion"] = {
            **llm_step(choice),
            "idea": (choice.get("answer") or {}).get("why", ""),
            "idea_es": tr.get("resumen"),
            "elecciones": rows,
        }

    if scene:
        stages["escena"] = {**llm_step(scene), "texto": (scene.get("answer") or {}).get("prompt", "")}

    def shot(name: str | None) -> str | None:
        return f"/corridas/{run_id}/{name}?w=720" if name and (out / name).exists() else None

    if img:
        tries = [
            {
                "foto": shot(t.get("image")),
                "ok": t.get("ok"),
                "ssim": t.get("ssim"),
                "puntos": t.get("sift_inliers"),
                "reencontrados": t.get("sift_reencontrados"),
                "desplazamiento": t.get("sift_desplazamiento_mediano"),
                "costo": t.get("cost_usd"),
            }
            for t in img.get("attempts") or []
        ]
        stages["imagen"] = {
            "generador": img.get("generator"),
            "modelo": img.get("model"),
            "calidad": (img.get("meta") or {}).get("quality"),
            "costo": round(img.get("cost_usd") or 0, 4),
            "segundos": (img.get("meta") or {}).get("latency_s"),
            "pendiente": bool(img.get("pending")),
            "intentos": tries,
            "final": shot(img.get("image")) if not img.get("pending") else None,
        }
    elif scene and s["estado"] in ("corriendo", "en cola"):  # los intentos van apareciendo
        tries = [{"foto": shot(f.name), "ok": None} for f in sorted(out.glob("final_intento_*.png"))]
        stages["imagen"] = {"en_curso": True, "intentos": tries}
    if "imagen" in stages:
        rc = cfg.furnish.room_check
        stages["imagen"]["umbral"] = {"puntos": int(rc["min_inliers"]), "desplazamiento": rc["max_shift"]}

    if tr:
        stages["traduccion"] = {"modelo": "claude-sonnet-5-5", "costo": round(tr.get("costo") or 0, 4)}

    keep = ("id", "origen", "via", "pedido", "creado", "estado", "error", "costo", "segundos", "antes")
    folder = out.relative_to(TP)
    return {
        **{k: s[k] for k in keep},
        "carpeta": str(folder),
        "detalle": m.get("detalle"),
        "vistas": [f"/corridas/{run_id}/{f.name}?w=720" for f in sorted(out.glob("room_*.jpg"))],
        "etapas": stages,
        "archivos": [{"nombre": f.name, "url": f"/corridas/{run_id}/{f.name}"} for f in sorted(out.glob("*.json"))],
    }


# traducción -----------------------------------------------------------------------------------------

TRANSLATE = """Traducí al español rioplatense (Argentina) los textos de este JSON, que salen de una app que
elige muebles para un ambiente. Que suene natural y breve, como lo escribiría un decorador
argentino ("mesa ratona", "living", "placard"). Mantené los nombres propios de productos, las
marcas y los números. Devolvé solo el JSON, con las mismas claves y el mismo largo de listas.

{data}"""


def translate(out: Path, dest: Path) -> dict | None:
    """Los textos de la corrida en castellano (en `dest`), con Claude Sonnet: menos de un centavo."""
    if dest.exists():
        return read(dest)
    plan, found, choice = (
        read(out / "1_searches.json"),
        read(out / "2_candidates.json"),
        read(out / "3_choice.json"),
    )
    if not (plan and found and choice):
        return None
    data = {
        "ambiente": plan["answer"].get("room", ""),
        "resumen": choice["answer"].get("why", ""),
        "porque": [c.get("why", "") for c in choice["answer"]["choices"]],
        "faltan": found.get("empty") or [],
    }
    cfg = flow_config(False)
    params = {**cfg.furnish.llm, "model": "claude-sonnet-5-5", "effort": "low", "max_tokens": 6000}
    prompt = TRANSLATE.format(data=json.dumps(data, ensure_ascii=False, indent=1))
    a, ans = st.ask(cfg, "web.traducir", [text_block(prompt)], params)
    if len(ans.get("porque") or []) != len(data["porque"]):
        return None
    ans["costo"] = a.cost_usd
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(ans, ensure_ascii=False, indent=1))
    return ans


def translate_quietly(out: Path, dest: Path) -> None:
    try:
        translate(out, dest)
    except Exception as e:  # sin traducción se muestran los textos en inglés
        print(f"traducción de {out.name}: {type(e).__name__}: {e}")


# las corridas ----------------------------------------------------------------------------------------

JOBS: dict[str, threading.Thread] = {}


def friendly(e: Exception) -> str:
    text = str(e)
    low = text.lower()
    if isinstance(e, BudgetExceeded):
        who = next((NAMES[a] for a in KEYS if f"({a})" in text), "una de las cuentas")
        return f"Se llegó al tope de gasto de la web para {who}. Se sube en Ajustes."
    if isinstance(e, ProviderUnavailable):
        who = "OpenAI" if "openai" in low else "fal" if re.search(r"\bfal\b|fal_key", low) else "Anthropic"
        if "401" in text or "403" in text:
            return f"{who} rechazó la clave de API. Reemplazala en Ajustes y retomá la corrida."
        return f"Falta la clave de {who}. Cargala en Ajustes y retomá la corrida."
    if "401" in text or "authentication" in low or "invalid x-api-key" in low or "incorrect api key" in low:
        return "Una de las claves de API no es válida. Revisala en Ajustes."
    if "no pieces" in low:
        return (
            "No encontramos qué muebles poner para este pedido. El catálogo tiene muebles de living, "
            "comedor y escritorio: probá pidiendo alguno."
        )
    if "nothing for" in text:
        return "El catálogo no tiene nada para este ambiente. Tiene muebles de living, comedor y escritorio."
    if "429" in text or "overloaded" in low or "rate" in low:
        return "El servicio está saturado en este momento. Probá de nuevo en un minuto."
    return f"Algo falló en el camino ({type(e).__name__}). Podés retomar la corrida: lo pagado no se repite."


def work(run_id: str) -> None:
    out = RUNS / run_id
    m = read(meta_path(out)) or {}
    photo, request, with_image = out / "entrada.jpg", m["pedido"], m.get("con_imagen", True)
    try:
        with FLOW_LOCK:
            write_meta(out, estado="corriendo", error=None, detalle=None)
            if not (out / "3_choice.json").exists() or not with_image:
                run_flow(photo, request, flow_config(False), out, log=lambda _: None)
            threading.Thread(target=translate_quietly, args=(out, tr_file(out, "web")), daemon=True).start()
            if with_image:
                run_flow(photo, request, flow_config(True), out, log=lambda _: None)
        write_meta(out, estado="listo", terminado_ts=time.time())
    except Exception as e:
        print(f"{run_id}: {type(e).__name__}: {e}", flush=True)
        write_meta(out, estado="error", error=friendly(e), detalle=f"{type(e).__name__}: {e}", terminado_ts=time.time())
    finally:
        JOBS.pop(run_id, None)


def launch(run_id: str) -> None:
    write_meta(RUNS / run_id, estado="en cola", terminado_ts=None)
    t = threading.Thread(target=work, args=(run_id,), daemon=True)
    JOBS[run_id] = t
    t.start()


def row(run_id: str) -> dict | None:
    """Una corrida en la lista: lo justo para la tarjeta, sin armar todo su estado."""
    try:
        out, origin = locate(run_id)
    except HTTPException:
        return None
    m = meta(out, origin)
    choices = ((read(out / "3_choice.json") or {}).get("answer") or {}).get("choices") or []
    img = read(out / "5_image.json") or {}
    final = next(iter(sorted(out.glob("final.*"))), None) if img and not img.get("pending") else None
    pic = final.name if final else "room.jpg" if (out / "room.jpg").exists() else None
    return {
        "id": run_id,
        "origen": origin,
        "via": m.get("via", "web"),
        "pedido": m.get("pedido", ""),
        "creado": m.get("creado"),
        "estado": live_state(run_id, m)[0],
        "productos": sum(1 for c in choices if st.quantity(c)),
        "costo": round(run_cost(out, origin), 2),
        "imagen": f"/corridas/{run_id}/{pic}?w=720" if pic else "",
    }


def history() -> list[dict]:
    """Las corridas de la web y las de la terminal que llegaron a elegir, de la más nueva a la más vieja."""
    ids = [p.parent.name for p in RUNS.glob("*/web.json")]
    ids += [TERM + p.parent.name for p in TERMINAL.glob("*/3_choice.json") if (p.parent / "request.json").exists()]
    rows = [r for r in map(row, ids) if r]
    rows.sort(key=lambda r: r["creado"] or "", reverse=True)
    return rows


# la API ------------------------------------------------------------------------------------------------

app = FastAPI(title="amoblai", docs_url=None, redoc_url=None)


@app.get("/api/estado")
def api_status():
    return status()


@app.post("/api/claves")
def api_keys(body: dict):
    values = {KEYS[a]: str(body.get(a) or "").strip() for a in KEYS if str(body.get(a) or "").strip()}
    if not values:
        raise HTTPException(400, "No llegó ninguna clave")
    os.environ.update(values)
    if body.get("recordar", True):
        save_env(values)
    return status()


@app.post("/api/preferencias")
def api_prefs(body: dict):
    """Cambia lo que llegue: intentos (1 a 5), imagen (un modelo de IMAGE_MODELS) o topes por cuenta."""
    saved = read(PREFS) or {}
    if "intentos" in body:
        try:
            n = int(body["intentos"])
        except (TypeError, ValueError):
            n = 0
        if not 1 <= n <= 5:
            raise HTTPException(400, "Elegí entre 1 y 5 intentos")
        saved["intentos"] = n
    if "imagen" in body:
        if body["imagen"] not in IMAGE_MODELS:
            raise HTTPException(400, "Ese modelo de imagen no está disponible")
        saved["imagen"] = body["imagen"]
    if "topes" in body:
        caps = dict(saved.get("topes") or {})
        for account, value in (body["topes"] or {}).items():
            if account not in KEYS:
                continue
            try:
                usd = float(value)
            except (TypeError, ValueError):
                usd = 0
            if not 0 < usd <= 1000:
                raise HTTPException(400, f"El tope de {NAMES[account]} tiene que ser mayor que cero y de hasta US$ 1.000")
            caps[account] = round(usd, 2)
        saved["topes"] = caps
    PREFS.write_text(json.dumps(saved))
    return status()


@app.get("/api/muestras")
def api_samples():
    return [{"id": rel, "foto": tp_url(rel, 640)} for rel in SAMPLES if (TP / rel).exists()]


@app.get("/api/ambientes")
def api_history():
    return history()


@app.post("/api/ambientes")
async def api_new(pedido: str = Form(...), muestra: str = Form(""), foto: UploadFile | None = File(None)):
    pedido = pedido.strip()
    if not pedido:
        raise HTTPException(400, "Escribí qué querés para el ambiente")
    if not has_key("anthropic"):
        raise HTTPException(400, "Falta la clave de Anthropic. Cargala en Ajustes")
    if key_ok("anthropic") is False:
        raise HTTPException(400, "Anthropic rechaza la clave cargada. Reemplazala en Ajustes")
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = RUNS / run_id
    out.mkdir(parents=True)
    try:
        if foto is not None and foto.filename:
            im = Image.open(io.BytesIO(await foto.read()))
        elif muestra in SAMPLES:
            im = Image.open(TP / muestra)
        else:
            raise HTTPException(400, "Subí una foto del ambiente o elegí una de las de ejemplo")
        ImageOps.exif_transpose(im).convert("RGB").save(out / "entrada.jpg", quality=94)
    except HTTPException:
        shutil.rmtree(out)
        raise
    except OSError:
        shutil.rmtree(out)
        raise HTTPException(400, "No pudimos leer esa imagen. Probá con un JPG o un PNG") from None
    now = datetime.now()
    write_meta(
        out,
        id=run_id,
        pedido=pedido,
        creado=now.isoformat(timespec="seconds"),
        creado_ts=now.timestamp(),
        con_imagen=key_ok(image_account()) is not False,
    )
    launch(run_id)
    return {"id": run_id}


TRIED: set[str] = set()


@app.get("/api/ambientes/{run_id}")
def api_run(run_id: str):
    s = run_state(run_id)
    if s["estado"] == "listo" and s["lista"] and not s["traducido"] and run_id not in TRIED:
        TRIED.add(run_id)  # corridas viejas, de la terminal o cuya traducción falló: una vez, de fondo
        out, origin = locate(run_id)
        threading.Thread(target=translate_quietly, args=(out, tr_file(out, origin)), daemon=True).start()
    return s


@app.post("/api/ambientes/{run_id}/retomar")
def api_resume(run_id: str):
    s = run_state(run_id)
    if s["origen"] != "web":
        raise HTTPException(400, "Las corridas de la terminal se retoman desde la terminal")
    if s["estado"] != "error":
        raise HTTPException(400, "La corrida no está detenida")
    if key_ok("anthropic") is False:
        raise HTTPException(400, "Anthropic sigue rechazando la clave. Reemplazala en Ajustes")
    write_meta(RUNS / run_id, con_imagen=s["con_imagen"] or key_ok(image_account()) is not False)
    launch(run_id)
    return {"id": run_id}


@app.get("/api/dev/{run_id}")
def api_dev(run_id: str):
    return dev_state(run_id)


@app.get("/corridas/{run_id}/{name}")
def media(run_id: str, name: str, w: int = 0):
    p = inside(locate(run_id)[0], name)
    small = w and p.suffix.lower() in (".jpg", ".jpeg", ".png")
    return FileResponse(resized(p, min(w, 2400)) if small else p)


@app.get("/archivo")
def tp_file(p: str, w: int = 480):
    return FileResponse(resized(inside(TP / "datos", p.removeprefix("datos/")), min(w, 2400)))


@app.get("/prompt/{name}")
def prompt_text(name: str):
    """El texto de un prompt (src/amoblai/prompts), tal como lo carga el flujo."""
    p = inside(PROMPTS.resolve(), name if name.endswith(".md") else f"{name}.md")
    return Response(p.read_text(), media_type="text/plain; charset=utf-8")


app.mount("/static", StaticFiles(directory=WEB), name="static")


@app.get("/{path:path}")
def spa(path: str):
    if path.startswith(("api/", "static/")):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    return Response((WEB / "index.html").read_bytes(), media_type="text/html")


def warm_up() -> None:
    """Carga el índice y los modelos de la búsqueda antes de la primera corrida (gratis)."""
    try:
        with FLOW_LOCK:
            st.retrieve(flow_config(False), [{"piece": "sofa", "kinds": ["sofa"], "query": "Type: sofa"}])
    except Exception as e:
        print(f"warm-up: {type(e).__name__}: {e}")


if __name__ == "__main__":
    RUNS.mkdir(exist_ok=True)
    threading.Thread(target=warm_up, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")

"""El recorrido: el flujo ambiente por ambiente, con la planta arriba (el ambiente actual encendido y
el camino hecho en naranja); los desafíos (el cambio desde la propuesta aprobada); y el mapa de
experimentos: la misma planta con una llamada de detalle por experimento, que remite a su lámina
(llena: con lámina propia; punteada: de trámite; roja: sin experimento que lo sostenga).

Se sigue una corrida de la configuración final sobre una foto pública (datos_deck.RUN_REC), y se
muestra otra que el control del ambiente rechazó (RUN_NO). Todo sale de los archivos del repo: los
prompts se leen de src/amoblai/prompts (el extracto es texto literal del archivo), la configuración
de datos/configs/amoblai.yaml y los ejemplos, de datos/resultados/amoblar/final-*/.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

import img
import planta
import sala
from base import (KIND_ES, add, cab, catalogo, dif, esc, f, ficha, foto_producto, ic, item, kind_es, media_desvio,
                  medidas, miles, pct, remate, sg, usd)
from datos_deck import REPO, V1, V2, jsonl

PROMPTS = REPO / "src" / "amoblai" / "prompts"
NF = planta.NOMBRE


# ---------------------------------------------------------------- de dónde sale cada cosa

def config():
    """La configuración real del flujo (datos/configs/amoblai.yaml con los defaults del código)."""
    from amoblai.config import load_config

    return load_config(REPO / "datos" / "configs" / "amoblai.yaml")


def kinds():
    from amoblai.catalog.kinds import KINDS

    return KINDS


def where_de(pieza: dict, slack: float) -> dict:
    """El `where` de ChromaDB de una pieza del plan, como lo arma rag/filters.py."""
    from amoblai.rag.filters import Filters

    most = {f"max_{a}_cm": round(v * (1 + slack), 1) for a in ("width", "depth", "height")
            if (v := pieza.get(f"max_{a}_cm")) is not None}
    return Filters(kinds=pieza["kinds"][:1], **most).where()


def vector(texto: str) -> np.ndarray | None:
    """El vector de Qwen3 de un texto, de la caché de vectores (solo lectura)."""
    import hashlib

    key = {"kind": "local", "model": "Qwen/Qwen3-Embedding-0.6B", "revision": None, "pooling": "last", "max_length": 512}
    h = hashlib.sha256(json.dumps({"embedder": key, "text": texto}, sort_keys=True).encode()).hexdigest()[:24]
    p = REPO / "datos" / "cache" / "rag" / "vectors" / f"{h}.npy"
    return np.load(p) if p.exists() else None


def prompt_txt(nombre: str) -> tuple[dict, list[str]]:
    import yaml

    t = (PROMPTS / f"{nombre}.md").read_text()
    _, fm, body = t.split("---", 2)
    return yaml.safe_load(fm), body.strip("\n").splitlines()


def extracto(nombre: str, specs: list, titulo: str | None = None, cls: str = "") -> str:
    """Un extracto literal del prompt. spec: '…' o dict(l=comienzo de la línea, desde=, hasta=,
    m=[frases a resaltar]). Lo que se recorta de una línea queda como […]."""
    _, lines = prompt_txt(nombre)
    out = []
    for s in specs:
        if s == "…":
            out.append('<p class="el">[…]</p>')
            continue
        line = next((x for x in lines if x.startswith(s["l"])), None)
        if line is None:
            raise ValueError(f"{nombre}: no hay línea que empiece con {s['l']!r}")
        a, b = 0, len(line)
        if s.get("desde"):
            a = line.index(s["desde"])
        if s.get("hasta"):
            b = line.index(s["hasta"], a) + len(s["hasta"])
        frag = line[a:b]
        h = esc(frag)
        for m in s.get("m", []):
            if esc(m) not in h:
                raise ValueError(f"{nombre}: {m!r} no está en {frag!r}")
            h = h.replace(esc(m), f"<mark>{esc(m)}</mark>", 1)
        h = re.sub(r"\{(\w+)\}", r'<span class="var">{\1}</span>', h)
        out.append(f'<p>{"[…] " if a > 0 else ""}{h}{" […]" if b < len(line) else ""}</p>')
    cab_ = f'<div class="prh"><span>prompts/{nombre}.md</span><span>{titulo or "extracto literal · en inglés, como se manda"}</span></div>'
    return f'<div class="hoja pr {cls}">{cab_}<div class="prb">{"".join(out)}</div></div>'


def _corta(texto: str, n: int) -> str:
    """El texto hasta la última palabra entera que entra en n caracteres, con puntos suspensivos."""
    if len(texto) <= n:
        return texto
    return texto[:n].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def xref(e: str, html: str, tipo: str = "si", desde=None) -> str:
    """La llamada a un experimento: arriba su número, abajo la lámina donde está (se resuelve al
    final, en build.referencias). tipo: si (con lámina propia), tram (de trámite), pend."""
    d = f' data-desde="{desde}"' if desde is not None else ""
    return (f'<div class="xrf"{d}><span class="xc {tipo}" data-ir="{{{{IR:{e}}}}}"><b>{e}</b><i>{{{{LAM:{e}}}}}</i></span>'
            f'<p>{html}</p></div>')


def revisiones(filas: list[tuple[str, str]], titulo="cuadro de revisiones del prompt", desde=None) -> str:
    d = f' data-desde="{desde}"' if desde is not None else ""
    rows = "".join(f'<div class="rvn{" ult" if i == len(filas) - 1 else ""}">{esc(v)}</div><p>{t}</p>'
                   for i, (v, t) in enumerate(filas))
    return f'<div class="rev"{d}><div class="rvh">{titulo}</div><div class="rvg">{rows}</div></div>'


def bloque_r(titulo, html, desde=None, cls=""):
    d = f' data-desde="{desde}"' if desde is not None else ""
    return f'<div class="br {cls}"{d}><div class="bt">{titulo}</div>{html}</div>'


def l8(texto: str, n=44) -> str:
    out = ""
    for ln in texto.strip().splitlines():
        k, _, v = ln.partition(":")
        v = v.strip()
        out += f'<div class="l8"><span>{esc(k)}</span>{esc(v[:n])}{"…" if len(v) > n else ""}</div>'
    return out


def vec_svg(v: np.ndarray, w=1024, h=46, cls="vec") -> str:
    """Los 1024 números de un vector, uno por columna: azul si es positivo, naranja si es negativo."""
    m = float(np.abs(v).max()) or 1.0
    bars = []
    for i, x in enumerate(v):
        a = min(1.0, abs(float(x)) / (m * 0.55))
        col = "#2453D6" if x >= 0 else "#FF9A3D"
        bars.append(f'<rect x="{i}" y="0" width="1" height="{h}" fill="{col}" fill-opacity="{a:.2f}"/>')
    return f'<svg class="{cls}" viewBox="0 0 {len(v)} {h}" preserveAspectRatio="none">{"".join(bars)}</svg>'


def referencias_plano() -> str:
    """La leyenda de la planta, como el cuadro de referencias de un plano."""
    def sw(inner):
        return f'<svg viewBox="0 0 54 30" width="54" height="30">{inner}</svg>'
    items = [
        (sw('<rect x="1" y="3" width="52" height="24" fill="#fff" stroke="#13202C" stroke-width="1.4"/>'), "ambiente: una fase del flujo"),
        (sw('<rect x="1" y="3" width="52" height="24" fill="#2453D6"/>'), "dónde estamos"),
        (sw('<rect x="1" y="3" width="52" height="24" fill="#E2E9FB" stroke="#BCC4CA"/>'), "ya recorrido"),
        (sw('<path d="M10,27 L32,27 M10,5 A22,22 0 0 1 32,27" fill="none" stroke="#7E8A98" stroke-width="1.4"/>'
            '<rect x="7" y="0" width="3" height="30" fill="#13202C"/>'), "puerta: pasa lo que sale"),
        (sw('<path d="M2,15 L44,15" stroke="#BCC4CA" stroke-width="2" stroke-dasharray="5 5"/><polygon points="52,15 41,9 41,21" fill="#BCC4CA"/>'), "el recorrido"),
        (sw('<path d="M2,15 L44,15" stroke="#FF9A3D" stroke-width="3"/><polygon points="52,15 41,9 41,21" fill="#FF9A3D"/>'), "lo ya recorrido"),
    ]
    return ('<div class="refs" data-desde="3"><div class="rft">referencias</div>'
            + "".join(f'<span>{a}<i>{esc(b)}</i></span>' for a, b in items) + "</div>")


def num(v, d=3) -> str:
    return f"{v:.{d}f}".replace(".", ",").replace("-", "−")


def rtira(actual, **kw) -> str:
    return f'<div class="rtira">{planta.tira(actual, **kw)}</div>'


def fase(n: int, titulo: str, contenido: str, *, t: int, notas: list[str], rem: str | None = None,
         rem_desde=None, sufijo: str = "", rc_cls: str = "") -> None:
    ala = "una vez, offline" if n in planta.OFFLINE else "en cada pedido"
    body = ('<div class="cuerpo">' + cab(str(n), f"El recorrido · {ala}", titulo) + "</div>"
            + rtira(n) + f'<div class="rc {rc_cls}">{contenido}</div>'
            + (remate(rem, desde=rem_desde) if rem else ""))
    add(body, titulo=f"{n} · {NF[n]}{sufijo}", cap=1, t=t, notas=notas, cls="lam-rec")


# ---------------------------------------------------------------- la búsqueda híbrida, dibujada

def esquema_hibrida(pasan_txt: str, k: int, versiones: bool = True, w: int = 600) -> str:
    """La búsqueda de una pieza: la ficha, el filtro duro, los tres puntajes, la fusión y los k
    mejores. Con `versiones`, lo que ya hacía la versión 1 va en tinta y lo que agrega la versión 2,
    en cobalto y rotulado."""
    H = 392
    o = [f'<svg class="hib" viewBox="0 0 600 {H}" width="{w}" xmlns="http://www.w3.org/2000/svg">']

    def caja(x, y, wd, h, titulo, sub="", nuevo=False, tag=""):
        o.append(f'<rect class="hb{" n" if nuevo else ""}" x="{x}" y="{y}" width="{wd}" height="{h}"/>')
        cy = y + (h / 2 + 6 if not sub else 25)
        o.append(f'<text class="ht" x="{x + wd / 2}" y="{cy}" text-anchor="middle">{esc(titulo)}</text>')
        if sub:
            o.append(f'<text class="hs" x="{x + wd / 2}" y="{y + 47}" text-anchor="middle">{esc(sub)}</text>')
        if tag:
            o.append(f'<text class="hg{" n" if nuevo else ""}" x="{x + wd - 8}" y="{y - 6}" text-anchor="end">{esc(tag)}</text>')

    def fl(x, y1, y2, nuevo=False):
        c = " n" if nuevo else ""
        o.append(f'<line class="hf{c}" x1="{x}" y1="{y1}" x2="{x}" y2="{y2 - 2}"/>'
                 f'<polygon class="hp{c}" points="{x},{y2} {x - 6},{y2 - 10} {x + 6},{y2 - 10}"/>')

    caja(140, 0, 320, 40, "la ficha de la pieza · 8 líneas")
    fl(300, 40, 62)
    caja(0, 62, 600, 40, f"filtro duro: kind y medidas{pasan_txt}")
    sw, gap, y3 = 186, 21, 140
    trio = [("Qwen3", "coseno con la descripción", False, "versión 1"),
            ("BM25", "palabras de la descripción", True, "versión 2"),
            ("SigLIP 2", "la frase contra la foto", True, "versión 2")]
    for i, (t_, sub, nuevo, tag) in enumerate(trio):
        x = i * (sw + gap)
        nv = nuevo and versiones
        fl(x + sw / 2, 102, y3, nv)
        caja(x, y3, sw, 62, t_, sub, nv, tag if versiones else "")
        fl(x + sw / 2, y3 + 62, 252, nv)
    caja(0, 252, 600, 40, "fusión: cada puntaje estandarizado (z-score), y el promedio", nuevo=versiones,
         tag="versión 2" if versiones else "")
    fl(300, 292, 318)
    caja(140, 318, 320, 40, f"los {k} mejores, a la elección")
    if versiones:
        o.append(f'<text class="hn" x="0" y="{H - 8}">en tinta, la versión 1: el filtro, el coseno y los {k} mejores · en azul, lo que agrega la versión 2</text>')
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- las láminas

# cómo se dibuja en el living cada pieza del plan del recorrido (su primer kind → la pieza dibujada)
DIBUJO = {"sofa": "sofa", "rug": "alfombra", "coffee table": "mesa", "floor lamp": "lampara", "plant": "planta",
          "TV stand": "tv", "curtains": "cortinas", "cushion": "almohadones"}


def escena_textos(D: dict) -> dict:
    """Lo que se dice de la escena (plantilla contra escrita por el LLM, en los 11 ambientes: T10), en
    un solo lugar: lo usan la fase 8, el mapa y la lámina de trámite."""
    fin, esc_ = D["IMG_FIN"], D["IMG_ESC"]
    c = usd(D["c_scene"], 3)
    return dict(
        xref=(f"<b>La escena:</b> en los {fin['corridas']} ambientes, con las mismas listas, la plantilla y la escena escrita "
              f"por {'Opus'} empatan: {fin['identificados']} contra {esc_['identificados']} productos reconocidos de "
              f"{fin['productos']}; {fin['ambiente_conservado']} contra {esc_['ambiente_conservado']} cuartos conservados."),
        remate=f"Empate medido en {fin['corridas']} ambientes: queda la plantilla, <mark>una llamada y {c} menos</mark> por pedido.",
        notas=[
            "La escena: el prompt para el modelo de imagen. Probamos dos caminos: que Opus escriba dónde va cada "
            "producto, o una plantilla sin LLM, que se completa con la lista.",
            "[paso] La última plantilla es estricta: es una edición de la foto del cliente, con la "
            "misma cámara, las mismas paredes y ventanas, y exactamente estos productos.",
            f"[paso] Las comparamos en los {fin['corridas']} ambientes, con las mismas listas: empate, en productos "
            f"reconocidos y en cuartos conservados. Queda la plantilla, que ahorra una llamada.",
        ],
        mapa="la plantilla",
        fila=(f"Empate en los {fin['corridas']} ambientes, con las mismas listas ({D['escena_pareado']} de reconocidos, pareado). "
              f"Queda la plantilla: una llamada y {c} menos por pedido."),
    )


def build(D: dict, ctx: dict) -> None:
    from laminas_1 import credito

    D["ESCENA"] = escena_textos(D)
    cfg = D["cfg"]
    fu = cfg.furnish
    CAM, CON, HIB, EMB = D["CAM"], D["CON"], D["HIB"], D["EMB"]
    B1, B2, D21 = D["B1"], D["B2"], D["D21"]
    run = D["run"]
    R = run["dir"]
    slug = run["slug"]
    cred = credito(D, slug)
    req = run["req"]["request"]
    plan_r = run["plan"]
    plan = plan_r["answer"]["pieces"]
    cands = run["cands"]["pieces"]
    ch_r = run["choice"]
    choices = ch_r["answer"]["choices"]
    scene = run["scene"]
    gen = run["gen"]
    picks = ctx["picks"]
    K = kinds()
    n_tipos = len(set(K.values()))
    kf = fu.candidates
    llm = fu.llm
    modelo = llm["model"].replace("claude-opus-5-5", "Opus 5.5")
    nb2 = fu.generators["nano_banana_2"]
    T = D["IMG_TOT"]
    n1 = CAM["qwen3|seller-full|filtro-none|consulta-piece"]
    n2 = CAM["qwen3|description|filtro-none|consulta-piece"]
    q_full, q_piece = CON[V1], CON[V1 + "|consulta-piece"]
    # el producto de ejemplo del pabellón offline: la lámpara de la lista (IKEA, descripta con la v3)
    lamp = next(h["id"] for h, *_ in picks if item(D, h["id"]).get("kind") == "floor lamp")
    assert not lamp.startswith("abo-") and D["desc_prompt"][lamp].startswith("describe_product_v3"), "cambió el producto de ejemplo"
    sofa = picks[0][0]["id"]
    assert item(D, sofa)["kind"] == "sofa"

    # ================================================================ la planta del flujo
    Rg, _ = planta._geo(planta.W, planta.G)
    k = 1776 / (planta.W + 46)
    filas = {
        1: ("la foto, el kind y las medidas", "IKEA + ABO", "una vez"),
        2: ("ocho líneas por producto", "un VLM mira la foto", "una vez"),
        3: ("la descripción, sus palabras y la foto", "Qwen3 · BM25 · SigLIP 2", "una vez"),
        4: ("la foto vacía y el pedido", "texto libre", "lo pone el usuario"),
        5: ("piezas, kind, medida y ficha", modelo, usd(D["c_plan"])),
        6: (f"{kf} candidatos por pieza", "filtro + búsqueda híbrida", "local, gratis"),
        7: ("uno por pieza, y cuántos", modelo, usd(D["c_choose"])),
        8: ("el prompt de la imagen", "plantilla, sin LLM", "gratis"),
        9: ("la foto amoblada", "Nano Banana 2", f"{usd(D['c_img'])} c/u"),
        10: ("¿sigue siendo tu cuarto?", "SIFT + RANSAC", "local, gratis"),
        11: ("la lista y la imagen", "ids y cantidades", f"≈ {usd(D['c_pedido'])} todo"),
    }
    cols = ""
    for n, (q, con, cuesta) in filas.items():
        x0, x1 = Rg[n]
        left = 72 + (x0 + 6) * k + 10
        wd = (x1 - x0) * k - 18
        cols += (f'<div class="loc-c{" off" if n <= 3 else ""}" style="left:{left:.0f}px;width:{wd:.0f}px" data-desde="{1 if n <= 3 else 2}">'
                 f'<p class="q">{esc(q)}</p><p class="con">{esc(con)}</p><p class="cu">{esc(cuesta)}</p></div>')
    marcas = {2: "LLM", 5: "LLM", 7: "LLM", 9: "IMAGEN"}
    body = ('<div class="cuerpo">' + cab("01", "El recorrido · la planta", "El flujo, <em>como la planta de una casa</em>") + "</div>"
            + rtira(None, marcas=marcas)
            + '<div class="cuadro"><div class="cdk">cuadro de locales · qué sale de cada ambiente, con qué, y cuánto cuesta por pedido</div>'
            + cols + "</div>" + referencias_plano()
            + remate("El índice se arma <mark>una vez</mark>; los otros ocho ambientes se recorren <mark>en cada pedido</mark>.", desde=3))
    add(body, titulo="La planta del flujo", cap=1, t=35, cls="lam-rec lam-planta", notas=[
        "Así está armado amoblai, como la planta de una casa: cada fase es un ambiente y se pasa "
        "al siguiente por una puerta.",
        "[paso] A la izquierda, un pabellón que se construye una vez, offline: catálogo, descripción e "
        "índice. El índice llega a la búsqueda por esa pasarela.",
        "[paso] Lo demás se recorre en cada pedido. Por pedido se pagan tres llamadas: "
        f"Opus en el plan y en la elección, y Nano Banana 2 en la imagen; unos {usd(D['c_pedido'])}. Buscar "
        "corre local.",
        "[paso] Los recorremos uno por uno: qué entra, qué sale y qué decidimos.",
    ])

    # ================================================================ 1 · catálogo
    ab = next(c["id"] for c in cands[0]["candidates"] if c["id"].startswith("abo-") and item(D, c["id"]).get("dimensions_cm"))

    def registro(pid, fuente):
        it = item(D, pid)
        dims = it.get("dimensions_cm") or {}
        dd = " × ".join(f"{dims[a]:.0f}" for a in ("width", "depth", "height") if dims.get(a)) or "—"
        u = img.uri(foto_producto(D, pid), 300, 300, fit="contain")
        return (f'<div class="hoja reg"><img src="{u}" alt=""><dl>'
                f'<dt>id</dt><dd>{esc(pid)}</dd><dt>tipo</dt><dd>{esc(it["category"])}</dd>'
                f'<dt>kind</dt><dd class="k">{esc(it["kind"])}</dd><dt>medidas</dt><dd>{dd}{" cm" if dims else ""}</dd>'
                f'<dt>fuente</dt><dd>{fuente}</dd></dl></div>')

    tabla = [k_ for k_, t_ in K.items() if t_ == "table"]
    cont = (
        '<div class="g2" style="grid-template-columns:600px 1fr">'
        '<div class="col">'
        + bloque_r("IKEA · Tautkute et al., 2017",
                   f'<p class="big">{D["n_855"]} → <b>{D["n_ikea"]}</b></p>'
                   f'<p>Lo revisamos a mano: salen {D["n_855"] - D["n_ikea"]} con la foto de otro producto o que no son '
                   f'de living ni comedor. Fotos de {D["ikea_px"]} px; con alguna medida, el {pct(D["ikea_con_medida"])} '
                   f'(<strong>ningún sofá ni sillón</strong>).</p>')
        + bloque_r("ABO · Amazon Berkeley Objects, CVPR 2022",
                   f'<p class="big">{D["abo_listados"]} → <b>{D["n_abo"]}</b></p>'
                   f'<p>De {D["abo_total"]} publicaciones de Amazon: una por modelo, con foto de al menos 800 px. '
                   f'{D["n_abo"]} quedaron descriptas y en el alcance. Con medidas, el {pct(D["abo_con_medidas"])}.</p>', desde=1)
        + xref("E6", f"<b>Qué catálogo:</b> el flujo usa los dos juntos, {miles(D['n_todos'])} productos; lo que tiene "
               f"ground truth se mide solo sobre IKEA.", desde=2)
        + '</div><div class="col">'
        + f'<div class="regs" data-desde="1">{registro(lamp, "IKEA")}{registro(ab, "ABO")}</div>'
        + f'<div class="kinds" data-desde="2"><p><b>{len(K)} kinds en {n_tipos} tipos.</b> El kind es más fino que el tipo, '
          f'y es el filtro duro de la búsqueda: una silla de escritorio no es un sillón.</p>'
          f'<p class="kt"><span>table</span>→ {" · ".join(esc(x) for x in tabla)}</p></div>'
        + "</div></div>")
    fase(1, "Catálogo: <em>productos reales, con su foto y su kind</em>", cont, t=30,
         rem="Del catálogo el flujo usa <mark>la foto, el kind y las medidas</mark>; el nombre comercial, no.", rem_desde=2,
         notas=[
             f"El catálogo. El dataset de IKEA de Tautkute y otros, revisado a mano mirando cada foto: de "
             f"{D['n_855']} productos quedan {D['n_ikea']}.",
             f"[paso] Y un segundo catálogo, Amazon Berkeley Objects, publicaciones reales de Amazon: {D['n_abo']} "
             f"productos, casi todos con medidas. Cada uno entra con su foto, su tipo, su kind y sus medidas.",
             f"[paso] El kind es más fino que el tipo: hay {len(K)}, y es el filtro duro de la búsqueda. El flujo "
             f"usa los dos catálogos: lo mide el experimento 6.",
         ])

    # ================================================================ 2 · descripción
    seller = D["items"][lamp]
    vend = seller.get("description") or ""
    assert vend and not re.search(r"paper|lantern|white", vend, re.I), "el texto del vendedor del ejemplo cambió: revisar la lámina 2"
    pr = extracto("describe_product_v3", [
        dict(l="The images are photos of one product", hasta='called "{name}"'),
        dict(l="Write its description", desde="Exactly these eight lines", hasta="short phrases",
             m=["Exactly these eight lines, in this order"]),
        dict(l="Style:", m=["one to three of these"], hasta="Japandi,"),
        "…",
        dict(l="60 to 90 words", desde="Say only", hasta="No brand, price, measurements",
             m=["Say only what the photos and the name show.", "No brand, price, measurements"]),
    ])
    rev = revisiones([
        ("v2", "Muebles. Las líneas de la consulta; sin marca, precio ni medidas; nada de lo que <b>no</b> es: "
               "los embeddings no leen «not»."),
        ("v3", "Todo el catálogo: lámparas, textiles y deco."),
        ("api v1", "ABO por la API: diez por llamada, y además el kind."),
    ], desde=2)
    cont = (
        '<div class="g3" style="grid-template-columns:420px 1fr 500px">'
        '<div class="col">'
        + bloque_r("por qué", f'<p>El texto del vendedor es marketing. De esta lámpara dice:</p><p class="cita vend">«{esc(vend)}»</p>'
                   f'<p>No dice que es de papel ni que parece un farol.</p>')
        + bloque_r("quién la escribe", "<p><strong>IKEA:</strong> subagentes de Claude Code. <strong>ABO:</strong> "
                   f"{modelo} por la API, a {usd(D['c_desc'], 3)} por producto.</p>")
        + xref("E1", f"<b>Qué se indexa:</b> con la descripción, hit@1 pasa de {f(n1['hit@1'])} a <b>{f(n2['hit@1'])}</b> "
               f"({dif(n2['vs_anterior'])}).")
        + '</div><div class="col" data-desde="1">' + pr + rev + "</div>"
        + f'<div class="col" data-desde="3"><div class="etq">la salida · para la lámpara de la lista</div>'
        + f'<div class="hoja ej8"><div class="ejh"><img src="{img.uri(foto_producto(D, lamp), 200, 200, fit="contain")}" alt="">'
          f'<div><b>{lamp}</b><span>IKEA · {kind_es(D, lamp)}</span></div></div>{l8(D["desc"][lamp], 40)}</div>'
        + "</div></div>")
    fase(2, "Descripción: <em>cada producto, en ocho líneas fijas</em>", cont, t=40,
         rem="Se indexa lo que un modelo <mark>ve en la foto</mark>, no lo que dice la tienda.", rem_desde=3,
         notas=[
             "La descripción. El texto del vendedor es marketing: de esta lámpara dice «da una luz suave», no "
             "que es de papel ni que parece un farol. Por eso un modelo de visión mira la foto y la describe. "
             "Es el preprocesamiento que más pesa: lo mide el experimento 1.",
             "[paso] El prompt pide ocho líneas fijas, en inglés: tipo, uso, estilo de una lista cerrada, "
             "materiales, colores, forma, sensación y con qué combina. Solo lo que se ve.",
             "[paso] La v3 sumó lámparas y deco; la versión por la API, para Amazon, devuelve además el kind.",
             "[paso] Y esto escribió para la lámpara de la lista: papel de arroz, tipo farol, japandi.",
         ])

    # ================================================================ 3 · índice
    doc_idx = next(x["description"] for x in jsonl(D["idx_items"]) if x["id"] == lamp)
    vd = vector(doc_idx)  # el texto exacto que se embebió
    it = D["items"][lamp]
    dims_l = it.get("dimensions_cm") or {}
    mt = ", ".join(f'"{a}": {num(dims_l[a], 0) if dims_l.get(a) is not None else "−1"}' for a in ("width", "depth", "height"))
    meta = f'{{"category": "{it["category"]}", "kind": "{it["kind"]}", {mt}}}'
    first = ", ".join(num(x) for x in vd[:5]) if vd is not None else ""
    siglip = cfg.rag.embedders["siglip2"]["model"].split("/")[-1]
    dec = (
        '<div class="tram4">'
        + xref("E11", "<b>Qué se embebe:</b> la descripción entera, un documento por producto. No se parte.", tipo="tram")
        + xref("E9", f"<b>Con qué:</b> {esc(D['embed_model'])}, local, sin instrucción de consulta: la consulta ya "
               "está escrita como un documento.", tipo="tram")
        + xref("E10", f"<b>Cuántas dimensiones:</b> {miles(D['best_dim'])}. El índice entero pesa {f(D['indice_mb'], 1)} MB.", tipo="tram")
        + xref("E12", f"<b>Dónde:</b> ChromaDB, HNSW en coseno (ef_search {D['hnsw']['ef_search']}, M "
               f"{D['hnsw']['max_neighbors']}), con la metadata de los filtros.", tipo="tram")
        + "</div>"
        + bloque_r("para la búsqueda híbrida, dos índices más",
                   xref("E3", f"<b>Léxico (BM25):</b> las palabras de esas mismas descripciones, sin modelo. <b>Por foto "
                        f"(SigLIP 2):</b> un vector por la foto de cada producto, en el mismo espacio que el texto de la consulta."),
                   desde=1, cls="hib2"))
    doc_lines = D["desc"][lamp].strip().splitlines()
    rec = (f'<div class="hoja reg-ch"><div class="prh"><span>un registro de ChromaDB</span><span>colección del catálogo IKEA + ABO</span></div>'
           f'<div class="rkv"><span>id</span><code>"{lamp}"</code>'
           f'<span>document</span><code>"{esc(doc_lines[0])}\\n{esc(doc_lines[1][:30])}…"</code>'
           f'<span>embedding</span><code>[{first}, … ]  <i>{len(vd) if vd is not None else D["best_dim"]} números, norma 1</i></code>'
           f'<span>metadata</span><code>{esc(meta)}</code></div>'
           f'<div class="vfig">{vec_svg(vd) if vd is not None else ""}<div class="vley"><span>0</span><span>los {D["best_dim"]} números de esta lámpara · azul positivo, naranja negativo</span><span>{D["best_dim"] - 1}</span></div></div>'
           f'<p class="nota">Sin medidas, el catálogo guarda −1: el producto pasa cualquier filtro de tamaño.</p></div>')
    cont = (f'<div class="g2" style="grid-template-columns:660px 1fr"><div class="col">{dec}</div>'
            f'<div class="col" data-desde="2">{rec}</div></div>')
    fase(3, "Índice: <em>un vector por descripción, y dos índices más</em>", cont, t=45,
         rem="Se arma una vez, local y gratis: <mark>la descripción, sus palabras y la foto</mark> de cada producto.", rem_desde=2,
         notas=[
             f"El índice. Se embebe la descripción entera, un documento por producto, con {D['embed_model']}, "
             f"local: {miles(D['best_dim'])} dimensiones, a ChromaDB, con la metadata de los filtros. Embedder, "
             f"splitting, dimensión y base vectorial son las preguntas de trámite, por eso su llamada va punteada: "
             f"las contestamos juntas más adelante.",
             "[paso] Para la búsqueda híbrida se suman dos índices sobre los mismos productos: uno léxico, BM25, "
             "sobre las palabras de las descripciones, y uno por foto, con SigLIP 2, que pone la foto y el texto "
             "de la consulta en un mismo espacio.",
             "[paso] Así queda un registro: el id, el documento, los mil veinticuatro números y la metadata. La "
             "lámpara no tiene medidas: se guarda menos uno y pasa cualquier filtro de tamaño.",
         ])

    # ================================================================ 4 · foto + pedido
    cont = (
        '<div class="g2 fp4" style="grid-template-columns:560px 1fr">'
        f'<div class="col"><div class="etq">la foto · la imagen 1 de todo el recorrido</div>'
        f'<div class="foto" style="width:520px;height:390px"><img src="{img.uri(R / "room.jpg", 1040, 780, q=74)}" alt=""></div>'
        f'<p class="pie-foto">Foto del ambiente: {esc(cred)}</p></div>'
        f'<div class="col" data-desde="1"><div class="etq">el pedido, como lo escribe el usuario</div>'
        f'<p class="cita pedido p4">«{esc(req)}»</p>'
        + bloque_r("qué va a dónde",
                   f"<p><strong>La foto</strong> va al plan y a la elección (reducida a {fu.photo_max_side} px) y al modelo de imagen.</p>"
                   "<p><strong>Otras fotos del mismo ambiente</strong>, opcionales, van solo al LLM, para entenderlo. "
                   "Nunca medimos si cambian la lista.</p>", cls="p4b")
        + "</div></div>")
    fase(4, "Foto y pedido: <em>lo único que pone el usuario</em>", cont, t=15,
         rem="Nada de formularios: <mark>una foto y lo que querés</mark>, en tus palabras.", rem_desde=1,
         notas=[
             "Todo empieza con lo que pone el usuario: una foto del ambiente vacío y el pedido en texto "
             "libre.",
             "[paso] Vamos a seguir este living hasta el final: un pedido japandi, sobre una foto pública, con "
             "la configuración con la que entregamos.",
         ])

    # ================================================================ 5 · plan (el prompt)
    pr = extracto("search_query_v4", [
        dict(l="You are an experienced interior designer", m=["{request}"]),
        dict(l="First read the room", hasta="as a designer would"),
        dict(l="Then decide which pieces", m=["as many as the request and the room call for"]),
        dict(l="- If they name a piece", hasta='"sillón" is an armchair for lounging', m=["A chair is not an armchair"]),
        dict(l="- Fit each one to the room", desde="Fill the space", m=["use its whole length"]),
        dict(l='  - "kinds"', hasta="the one kind the piece is"),
        dict(l='  - "max_width_cm"', desde="the most it can measure", hasta="otherwise null."),
        dict(l='  - "query"', hasta="nothing about what it should not be.", m=["the ideal product in the catalog's eight lines"]),
    ])
    rev = revisiones([
        ("v1", "Pidió un sillón cuando el usuario dijo «una silla», en un estudio con escritorio."),
        ("v2", "Lee el cuarto como un diseñador, respeta la pieza nombrada, elige el kind de una lista fija y escribe "
               "la consulta en las ocho líneas. De una a cuatro piezas."),
        ("v3", "La primera imagen fue un living largo con cuatro muebles y nada más: hasta seis piezas, después de los "
               "muebles lámparas y deco, y todo el largo del cuarto."),
        ("v4", "Un rincón de lectura ya llegaba a seis: sin tope."),
    ], desde=2)
    v1s = [CAM[V1]["hit@1"]] + [h[V1]["hit@1"] for h in D["HIB_R"]]
    cont = (
        '<div class="g3" style="grid-template-columns:470px 1fr 480px">'
        '<div class="col">'
        + bloque_r("qué hace", f"<p><strong>{modelo}</strong> (effort {llm['effort']}) lee la foto y el pedido, lo "
                   f"<strong>descompone en piezas</strong> y, por cada una, devuelve su <strong>kind</strong>, hasta qué "
                   f"<strong>tamaño</strong> entra y <strong>el producto ideal en las ocho líneas</strong> del catálogo: "
                   f"esa ficha es la consulta. El pedido nunca se embebe.</p>"
                   f'<p class="nota">{usd(D["c_plan"])} por pedido, en promedio.</p>')
        + xref("E2", f"<b>Cómo se escribe la consulta:</b> la ficha da <b>{f(q_full['hit@1'])}</b>; la frase natural, sin "
               f"reescribir, {f(q_piece['hit@1'])} ({dif(q_piece['vs_base'], flip=True)}).")
        + xref("E8", f"<b>Tres redactores:</b> según quién escribe las consultas, {media_desvio(v1s)}.", tipo="tram")
        + f'</div><div class="col" data-desde="1">{pr}</div>'
        + f'<div class="col">{rev}</div></div>')
    fase(5, "Plan: <em>descompone el pedido y escribe una ficha por pieza</em>", cont, t=55, sufijo=" · el prompt",
         rem="En palabras de la clase: <mark>query expansion con respuesta hipotética (HyDE)</mark> y <mark>descomposición del pedido</mark>.", rem_desde=2,
         notas=[
             f"El plan. {modelo} recibe la foto y el pedido y hace de diseñador: lee el ambiente, descompone el "
             f"pedido en piezas y, para cada una, da el kind, que va a ser el filtro, la medida máxima, y la "
             f"consulta: el producto ideal escrito en las mismas ocho líneas que el catálogo. En los términos de la "
             f"clase es query expansion con respuesta hipotética, HyDE: en la base no hay preguntas, hay respuestas, "
             f"así que la consulta se escribe como una respuesta. Más la descomposición del pedido: una consulta "
             f"por pieza.",
             "[paso] El prompt pide leer el cuarto como un diseñador, respetar la pieza nombrada, porque una "
             "silla no es un sillón, y no decir lo que no tiene que ser: los embeddings no leen la negación.",
             "[paso] Va por la cuarta versión, cada una por un error que vimos. Cuánto suma escribir la ficha "
             "lo mide el experimento 2.",
         ])

    # ================================================================ 5 · plan (lo que devuelve)
    P = sala.Proj()
    vb = sala.viewbox(P, pad=(20, 20, 10, 20), m=0)
    faltan = [p["kinds"][0] for p in plan if p["kinds"][0] not in DIBUJO]
    assert not faltan, f"el plan del recorrido tiene piezas que el dibujo no tiene: {faltan}"
    kinds_s = [DIBUJO[p["kinds"][0]] for p in plan]
    fant = "".join(sala.caja_alambre(P, sala.CAJA[k_], "fantasma", k_) for k_ in kinds_s)

    def tam(p):
        v = [p.get("max_width_cm"), p.get("max_depth_cm"), p.get("max_height_cm")]
        if not any(v):
            return ""
        return "≤ " + " × ".join(f"{x:.0f}" if x else "–" for x in v) + " cm"

    off = {"sofa": (-150, 70), "alfombra": (75, 45), "mesa": (-175, 210), "tv": (40, 115), "lampara": (-120, -40),
           "almohadones": (-150, -60), "planta": (90, -70), "cortinas": (70, -110)}
    rot = "".join(sala.rotulo(P, k_, KIND_ES.get(p["kinds"][0], p["kinds"][0]), *off[k_], sub=tam(p), cls="rot acc")
                  for k_, p in zip(kinds_s, plan))
    room = sala.sala([], P=P, extra=fant + rot, cotas=False, vb=vb)
    p0 = plan[0]
    q0 = p0["query"].splitlines()

    def hl(s, frases):
        h = esc(s)
        for fr in frases:
            assert esc(fr) in h, f"{fr!r} no está en {s!r}: revisar la lámina del plan"
            h = h.replace(esc(fr), f"<mark>{esc(fr)}</mark>", 1)
        return h

    def hlq(x):
        return hl(x, [fr for fr in ("low three-seater fabric sofa", "warm beige", "low profile") if fr in x])

    medidas_p0 = ", ".join(f'"max_{a}_cm": {p0[f"max_{a}_cm"]:.0f}' for a in ("width", "depth", "height") if p0.get(f"max_{a}_cm"))
    js = (f'<div class="hoja js"><div class="prh"><span>1_searches.json · la pieza 1</span><span>respuesta de {modelo}</span></div><pre>'
          f'"piece": "{hl(p0["piece"], ["low beige fabric sofa", "against the right wall"])}",\n'
          f'"kinds": ["{p0["kinds"][0]}"],\n'
          f'{medidas_p0},\n'
          f'"query":\n' + "\n".join(f'  {hlq(x)}' for x in q0) + "</pre></div>")
    reqh = hl(req, ["un sofá bajo de tela beige contra la pared de la derecha"])
    assert any("warm beige" in x for x in q0) and any("low profile" in x for x in q0), "cambió la consulta del sofá: revisar la nota del plan"
    cont = (
        '<div class="g3" style="grid-template-columns:400px 1fr 590px">'
        f'<div class="col"><div class="etq">el pedido</div><p class="cita pedido p5">«{reqh}»</p>'
        f'<p class="nota">{len(plan)} piezas · {usd(plan_r["cost_usd"])} · {f(plan_r["meta"]["latency_s"], 0)} s</p></div>'
        f'<div class="col p5room" data-desde="1"><div class="etq">esquema · las {len(plan)} piezas, con kind y tamaño máximo</div>{room}</div>'
        f'<div class="col" data-desde="2">{js}</div></div>')
    fase(5, "Plan: <em>el producto ideal, escrito como el catálogo</em>", cont, t=25, sufijo=" · lo que devuelve",
         rem="El plan no ve el catálogo: <mark>describe el producto ideal</mark> con las palabras del catálogo.", rem_desde=2,
         notas=[
             "Qué devuelve el plan para el living japandi.",
             f"[paso] {len(plan)} piezas, cada una con su kind y un tamaño máximo: el sofá, hasta "
             f"{p0['max_width_cm']:.0f} por {p0['max_depth_cm']:.0f}.",
             "[paso] Y la ficha de cada pieza: «tela beige» pasa a «Colors: warm beige»; «bajo», a «low "
             "profile». El plan no ve el catálogo: describe el sofá ideal, en el formato de los documentos.",
         ])

    # ================================================================ 6 · búsqueda (híbrida: la versión 2)
    from amoblai.rag.hybrid import visual_query

    fp = D["filtro_p1"]
    EJE = {"max_width_cm": "ancho", "max_depth_cm": "fondo", "max_height_cm": "alto"}
    filtro_txt = " · ".join([f'kind = {", ".join(fp["kinds"])}'] + [f"{EJE[k_]} ≤ {v:.0f} cm" for k_, v in fp["most"].items()])
    pasan_txt = f' → {fp["pasan"]} de {miles(D["n_todos"])}' if fp["pasan"] else ""
    c0 = cands[0]["candidates"]
    tira_c = "".join(ficha(D, c["id"], 112, pos=i + 1, hi=c["id"] == sofa, titulo=num(c["score"], 2), sub=catalogo(c["id"]), cap=True)
                     for i, c in enumerate(c0))
    pos_sofa = next(i for i, c in enumerate(c0) if c["id"] == sofa) + 1
    vq = visual_query(p0["query"])
    d_kind = CAM[V1]["vs_anterior"]
    cont = (
        '<div class="g3" style="grid-template-columns:480px 600px 1fr">'
        '<div class="col">'
        + bloque_r("qué hace", f"<p>Por pieza: primero el <strong>filtro duro</strong> de metadata (el kind del plan y cada "
                   f"medida hasta un {pct(fu.size_slack)} más; sin medida, pasa). Sobre lo que pasa, <strong>tres "
                   f"puntajes</strong> con la misma ficha, fusionados: los {kf} mejores.</p>"
                   f'<p class="nota">el sofá: {esc(filtro_txt)}{esc(pasan_txt)}</p>')
        + xref("E3", f"<b>Léxica, por foto e híbrida:</b> las tres juntas, <b>{f(B2['hit@1'])}</b> de hit@1 contra "
               f"{f(B1['hit@1'])} del coseno solo ({dif(D21)}).")
        + xref("E13", f"<b>Filtro por kind:</b> en el banco no suma ({dif(d_kind, 'hit@5')} de hit@5); evita un "
               f"{pct(D['otro_kind'])} de candidatos de otro kind.", tipo="tram", desde=1)
        + '</div>'
        + f'<div class="col" data-desde="1"><div class="etq">la búsqueda de una pieza</div>{esquema_hibrida(pasan_txt, kf, versiones=False, w=600)}</div>'
        + f'<div class="col" data-desde="2"><div class="etq">los {len(c0)} sofás que le llegan a la elección · puntaje fusionado · catálogo</div>'
          f'<div class="tira c6">{tira_c}</div>'
          f'<p class="nota">El puntaje es el promedio de los tres z-scores: {num(c0[0]["score"], 2)} son {num(c0[0]["score"], 2)} desvíos '
          f'por encima de la media de los sofás que pasaron el filtro. En azul, el que elige el ambiente siguiente.</p>'
          f'<p class="nota">SigLIP 2 lee la ficha en una frase: «{esc(vq[:74])}…»</p></div>'
        + "</div>")
    fase(6, "Búsqueda: <em>filtro por kind, después búsqueda híbrida</em>", cont, t=45, rc_cls="rc6",
         rem="El filtro decide <mark>qué es</mark>; la descripción, las palabras y la foto, <mark>cuál</mark>.", rem_desde=2,
         notas=[
             f"La búsqueda. Para cada pieza, primero un filtro duro de metadata: el kind del plan y las medidas "
             f"máximas, con un {pct(fu.size_slack)} de margen porque salen de una foto. Para el sofá quedan "
             f"{fp['pasan']} de los {miles(D['n_todos'])} productos.",
             "[paso] Sobre esos, tres puntajes con la misma ficha: el coseno de Qwen3 con la descripción; BM25, "
             "las palabras de la ficha que están en la descripción; y SigLIP 2, la ficha en una frase contra la "
             "foto del producto. Cada puntaje se estandariza y se promedian: es la búsqueda híbrida, la versión 2 "
             "del sistema.",
             f"[paso] Quedan los {kf} mejores: estos sofás, de los dos catálogos. El que termina en la lista es "
             f"el {pos_sofa}.º.",
         ])

    # ================================================================ 7 · elección: la generación de la lista
    pr = extracto("choose_combination_v2", [
        dict(l="We are adding", hasta="one photo each"),
        dict(l="For each piece choose", desde="Choose the pieces together",
             m=["Choose the pieces together, as one look, not each on its own.", "Judge from the photos."]),
        dict(l="Then say how many units", desde="0 when none", hasta="it is left out of the list.", m=["0 when none of its candidates suits this room"]),
    ])
    rev = revisiones([
        ("v1", "Una por pieza, eligiendo el conjunto; candidatos con su línea Type y su medida, no con su nombre."),
        ("v2", "Además, cuántas: 0 la saca de la lista; sillas de a varias."),
    ], desde=2)
    filas7 = ""
    for p, c in zip(cands, choices, strict=True):
        kd = p["spec"]["kinds"][0]
        th = "".join(f'<span class="ct{" ch" if h["id"] == c.get("id") else ""}"><img src="{img.uri(foto_producto(D, h["id"]), 130, 130, fit="contain")}" alt=""><i>{j + 1}</i></span>'
                     for j, h in enumerate(p["candidates"]))
        filas7 += f'<div class="e7f"><span class="e7k">{esc(KIND_ES.get(kd, kd))}</span><div class="ab-t">{th}</div></div>'
    n_first = sum(rk == 1 for *_, rk in picks)
    n_img = ch_r["meta"]["images"]
    d35 = D["CURVA"]["diferencias_pareadas"]["3->5"]
    dh = D["DIAG"]["hibrida"]
    cont = (
        '<div class="g3" style="grid-template-columns:450px 1fr 560px">'
        '<div class="col">'
        + bloque_r("qué hace", f"<p><strong>{modelo}</strong> ve el cuarto y las {kf} fotos de cada pieza, y arma "
                   f"<strong>la lista</strong>: uno por pieza, cuántos, y por qué. Solo puede elegir ids que trajo la "
                   f"búsqueda: si no, el código rechaza la respuesta.</p>"
                   f'<p class="nota">{usd(D["c_choose"])} en promedio · {f(D["lat_choose"], 0)} s (mediana)</p>')
        + xref("E5", f"<b>{kf} candidatos por pieza:</b> de 3 a 5 la elección suma {sg(d35['acierto_eleccion'])} "
               f"{ic(*d35['ic95'])}; en los {dh['ambientes']} ambientes, el {pct(dh['elegido_en_puestos_4_y_5'])} de lo "
               f"elegido salió de los puestos 4 y 5.")
        + '</div>'
        + f'<div class="col" data-desde="1">{pr}{rev}</div>'
        + f'<div class="col" data-desde="3"><div class="etq">lo que ve: {n_img} imágenes · en azul, lo que eligió</div>'
          f'<div class="e7g">{filas7}</div>'
          f'<p class="r7c">Sofá: eligió el <b>{pos_sofa}.º de la búsqueda</b>:</p><p class="cita porque">«{esc(_corta(choices[0]["why"], 105))}»</p></div>'
        + "</div>")
    fase(7, "Elección: <em>Opus mira las fotos y arma la lista</em>", cont, t=40,
         rem=f"Es <mark>la generación</mark> del RAG, no un reranker: tomó el 1.º de la búsqueda en {n_first} de las {len(picks)} piezas.", rem_desde=3,
         notas=[
             f"La elección: es la generación de la lista, la G del RAG. {modelo} ve la foto del ambiente y los "
             f"{kf} candidatos de cada pieza, acá {n_img} imágenes. Solo puede elegir productos que trajo la "
             f"búsqueda: si no, el código rechaza la respuesta.",
             "[paso] El prompt le pide elegir las piezas juntas, como un solo look, juzgando por las fotos, y decir "
             "cuántas unidades.",
             "[paso] La v2 agregó las cantidades: cero deja una pieza afuera.",
             f"[paso] No es un reranker: arma un conjunto para este cuarto. Tomó el primero de la búsqueda en "
             f"{n_first} de las {len(picks)} piezas. Para el sofá eligió el {pos_sofa}.º: era el único realmente "
             f"beige.",
         ])

    # ================================================================ 8 · escena
    escena(D, scene, modelo)

    # ================================================================ 9 · imagen
    ins = f'<div class="ins"><div class="in0"><img src="{img.uri(R / "room.jpg", 600, 450, q=72)}" alt=""><span>1</span></div><div class="ing">'
    for i, (h, *_) in enumerate(picks):
        ins += f'<div class="in1"><img src="{img.uri(foto_producto(D, h["id"]), 150, 150, fit="contain")}" alt=""><span>{i + 2}</span></div>'
    ins += "</div></div>"
    a1 = gen["attempts"][0]
    cont = (
        '<div class="g2" style="grid-template-columns:560px 1fr">'
        '<div class="col">'
        + bloque_r("qué hace", f"<p><strong>Nano Banana 2</strong> (Gemini 3.1 Flash Image), por fal, en modo edición: "
                   f"recibe la foto del cuarto, una foto por producto y el prompt, y devuelve la foto amoblada.</p>"
                   f'<p class="nota">{nb2["resolution"]} · la proporción de la foto · {usd(D["c_img"])} por imagen · '
                   f'{f(gen["meta"]["latency_s"], 0)} s</p>')
        + bloque_r("dos límites", f"<p><strong>Hasta {fu.max_image_products} productos en la imagen</strong>: el modelo acepta "
                   f"14 imágenes, la foto y 13 más. Las piezas que sobran quedan solo en la lista.</p>"
                   "<p><strong>El modelo no salió de un experimento</strong>: la comparación entre modelos de imagen quedó "
                   "diseñada, sin correr.</p>", desde=1)
        + '</div><div class="io9">'
        + f'<div><div class="etq">entra · {gen["meta"]["images_in"]} imágenes y el prompt</div>{ins}</div>'
        + f'<div class="sal" data-desde="1"><div class="etq">sale · intento 1</div><div class="foto" style="width:540px;height:405px">'
          f'<img src="{img.uri(R / a1["image"], 1080, 810, q=74)}" alt=""></div><p class="pie-foto">Foto del ambiente: {esc(cred)}</p></div>'
        + "</div></div>")
    fase(9, "Imagen: <em>Nano Banana 2 edita tu foto</em>", cont, t=20,
         rem="La segunda generación aumentada: la imagen sale de <mark>las fotos de lo que se compra</mark>.", rem_desde=1,
         notas=[
             f"La imagen: Nano Banana 2, de Gemini, por fal, edita la foto con las fotos de los {len(picks)} "
             f"productos y el prompt. {usd(D['c_img'])} por intento.",
             f"[paso] Acepta 14 imágenes, así que muestra hasta {fu.max_image_products} productos; el resto queda "
             f"en la lista. El modelo no lo elegimos con un experimento: esa comparación quedó sin correr.",
         ])

    # ================================================================ 10 · control: una que pasa y una que no
    no = D["run_no"]
    NO = no["dir"]
    att = gen["attempts"]
    best = next(a for a in no["gen"]["attempts"] if a["image"] == no["gen"]["room_check"]["image"])
    best_k = [a["image"] for a in no["gen"]["attempts"]].index(best["image"]) + 1
    assert att[0]["ok"] and not any(a["ok"] for a in no["gen"]["attempts"]), "las corridas de la fase 10 cambiaron: revisar la lámina"
    no_pasan = T["n"] - T["pasan"]

    def tile(path, cap, sub, sello="", ok=None, desde=None):
        d = f' data-desde="{desde}"' if desde is not None else ""
        s = f'<span class="sello{" ok" if ok else ""}">{sello}</span>' if sello else ""
        return (f'<figure class="at"{d}><div class="ai"><img src="{img.uri(path, 600, 450, q=72)}" alt="">{s}</div>'
                f'<figcaption><b>{cap}</b><span>{sub}</span></figcaption></figure>')

    tiles = (tile(R / "room.jpg", "el living del recorrido", "la foto original")
             + tile(R / att[0]["image"], "intento 1", f'{att[0]["sift_inliers"]} puntos · se movió {pct(att[0]["sift_desplazamiento_mediano"], 1)}',
                    "aceptada", True, 1)
             + tile(NO / "room.jpg", "otro pedido: un living clásico", "la foto original", desde=2)
             + tile(NO / best["image"], f"intento {best_k}, el mejor de {len(no['gen']['attempts'])}",
                    f'{best["sift_inliers"]} puntos · se movió {pct(best["sift_desplazamiento_mediano"])}', "rechazada", False, 2))
    cont = (
        '<div class="g2" style="grid-template-columns:470px 1fr">'
        '<div class="col">'
        + bloque_r("qué hace", f"<p>Busca puntos <strong>SIFT</strong> de la foto original en la generada y ajusta una "
                   f"homografía con <strong>RANSAC</strong>. Pasa si reencuentra al menos <b>{D['sift_min_inliers']} puntos</b> "
                   f"y la cámara se movió a lo sumo un <b>{pct(D['sift_max_shift'])}</b> del ancho. Si no, otra imagen, "
                   f"hasta <b>{D['sift_attempts']}</b>; si ninguna pasa, se entrega la mejor, marcada.</p>"
                   '<p class="nota">local · gratis · umbrales puestos a mano</p>')
        + bloque_r(f"en las {T['n']} corridas finales", f"<p><strong>{T['pasan']} pasan, todas al primer intento.</strong> En las "
                   f"otras {no_pasan} fallaron los {D['sift_attempts']} intentos: el modelo vuelve a mover la cámara o a "
                   f"rehacer el cuarto. Contando la tanda de la escena del LLM, reintentar rescató "
                   f"{D['reintentos']['rescatadas']} de {D['reintentos']['fallaron']}.</p>", desde=2)
        + f'</div><div class="col"><div class="atts r10">{tiles}</div>'
        + f'<p class="pie-foto">Fotos de los ambientes: {esc(cred)}; {esc(credito(D, no["slug"]))}</p></div></div>')
    fase(10, "Control: <em>¿sigue siendo tu cuarto?</em>", cont, t=40,
         rem="El control detecta cuando el modelo rehace el cuarto. <mark>Reintentar con el mismo prompt pocas veces lo arregla.</mark>", rem_desde=2,
         notas=[
             f"El control. Buscamos puntos característicos de la foto original en la generada, con SIFT, y una "
             f"homografía con RANSAC. Si se reencuentran al menos {D['sift_min_inliers']} y la cámara casi no se "
             f"movió, es el mismo cuarto; si no, se genera otra, hasta {D['sift_attempts']} veces. Los umbrales "
             f"están puestos a mano.",
             f"[paso] El living del recorrido pasó al primer intento, con {att[0]['sift_inliers']} puntos.",
             f"[paso] Este otro pedido, un living clásico, no: el modelo reencuadró hacia la chimenea en los tres "
             f"intentos, y se entrega el mejor, marcado. En las {T['n']} corridas finales pasan {T['pasan']}, todas "
             f"al primer intento; en las otras {no_pasan} fallaron los tres. El control detecta; reintentar pocas "
             f"veces arregla.",
         ])

    # ================================================================ 11 · lista + imagen
    rows = ""
    for h, q, _ in picks:
        pid = h["id"]
        u = img.uri(foto_producto(D, pid), 96, 96, fit="contain")
        rows += (f'<div class="li"><img src="{u}" alt=""><span class="k">{esc(kind_es(D, pid))}</span>'
                 f'<code>{esc(pid)}</code><span class="m">{esc(medidas(D, pid))}</span><b>×{q}</b></div>')
    tot = plan_r["cost_usd"] + ch_r["cost_usd"] + gen["cost_usd"]
    n_abo = sum(h["id"].startswith("abo-") for h, *_ in picks)
    cont = (
        '<div class="g2" style="grid-template-columns:1fr 560px">'
        f'<div class="col"><div class="etq">la lista · 3_choice.json · {len(picks) - n_abo} de IKEA y {n_abo} de Amazon</div><div class="lista">{rows}</div>'
        f'<p class="nota">esta corrida: plan {usd(plan_r["cost_usd"])} + elección {usd(ch_r["cost_usd"])} + '
        f'{len(att)} imagen{"es" if len(att) > 1 else ""} {usd(gen["cost_usd"])} = <b>{usd(tot)}</b></p>'
        '<p class="nota">Cada fase deja su archivo en la carpeta de la corrida (1_searches.json a 5_image.json): se retoma donde '
        'quedó, y nada se paga dos veces.</p>'
        + f'</div><div class="col" data-desde="1"><div class="etq">la imagen · intento {next(i for i, a in enumerate(att) if a["ok"]) + 1}, aceptada</div>'
          f'<div class="foto" style="width:560px;height:420px"><img src="{img.uri(R / "final.png", 1120, 840, q=76)}" alt=""></div>'
          f'<p class="pie-foto">Foto del ambiente: {esc(cred)}</p></div>'
        + "</div>")
    fase(11, "La salida: <em>una lista que se puede comprar</em>", cont, t=20,
         rem="Cada producto de la lista es un id real del catálogo, <mark>y tu cuarto con ellos</mark>.", rem_desde=1,
         notas=[
             f"Y la salida: la lista de compra, {len(picks)} productos con su id, su medida cuando la hay y la "
             f"cantidad, cada uno con su porqué. Esta corrida costó {usd(tot)}.",
             "[paso] Y la foto de tu cuarto con esos productos. Ese es el recorrido completo.",
         ])

    desafios(D)


# ---------------------------------------------------------------- 8 · la escena (se arma aparte: es la decisión que más se revisó)

def escena(D: dict, scene: dict, modelo: str) -> None:
    sp = scene["answer"]["prompt"]
    plines = sp.split("\n")
    head = plines[0]
    prods = [x for x in plines if x.startswith("image ")]
    hm = esc(head)
    for fr in ["Edit image 1. It is a photo of the client's own room", "that same room, exactly",
               "Do not add, remove, move or enlarge any wall, window, door or opening"]:
        assert esc(fr) in hm, f"el prompt de la escena cambió: falta {fr!r}"
        hm = hm.replace(esc(fr), f"<mark>{esc(fr)}</mark>", 1)
    cut = hm.index("do not extend")
    hm = hm[:cut].rstrip(", ") + " […]"
    add_l = next(x for x in plines if x.startswith("Add exactly"))
    am = esc(add_l[:add_l.index("(books")].rstrip()) + " […]"
    am = am.replace(esc("Add exactly these products and nothing else"), f"<mark>{esc('Add exactly these products and nothing else')}</mark>")
    prod_h = "".join(f"<p>{esc(x)}</p>" for x in prods[:3]) + '<p class="el">[…]</p>' + f"<p>{esc(prods[-1])}</p>"
    prs = (f'<div class="hoja pr"><div class="prh"><span>4_scene.json · el prompt tal como se mandó</span><span>scene_prompt_libre_v4, completado</span></div>'
           f'<div class="prb"><p>{hm}</p><p class="el">[…]</p>{prod_h}<p>{am}</p></div></div>')
    rev = revisiones([
        ("v1 · v2", "<b>Con LLM:</b> Claude escribe dónde va cada producto. La v2 ancla cada lugar a algo visible: la "
                    "primera imagen dejó todo junto a la cámara."),
        ("libre v1", "<b>Sin LLM:</b> el modelo de imagen decide dónde va cada uno."),
        ("v2 · v3", "La v2 repetía muebles por módulos para llenar una pared; la v3 lo cambió por las cantidades de la elección."),
        ("v4", "Estricta: es la foto del cliente; nada agregado ni abierto. Con nueve productos, la v3 había agregado "
               "una ventana y movido la biblioteca."),
    ], titulo="cuadro de revisiones · dos líneas de prompts", desde=2)
    E = D["ESCENA"]
    cont = (
        '<div class="g3" style="grid-template-columns:450px 1fr 500px">'
        '<div class="col">'
        + bloque_r("qué hace", "<p>Ningún LLM: una <strong>plantilla</strong> que se completa con la lista (la línea "
                   "Type de cada producto, su medida o «size unknown», y cuántas unidades) y el pedido.</p>"
                   '<p class="nota">gratis · instantáneo</p>')
        + xref("E15", E["xref"], tipo="tram", desde=2)
        + f'</div><div class="col" data-desde="1">{prs}</div><div class="col">{rev}</div></div>')
    fase(8, "Escena: <em>el prompt de la imagen, una plantilla sin LLM</em>", cont, t=30,
         rem=E["remate"], rem_desde=2, notas=E["notas"])


# ---------------------------------------------------------------- los desafíos

def desafios(D: dict) -> None:
    from graf import hbars

    VT = D["VT"]
    T = D["IMG_TOT"]
    no_pasan = T["n"] - T["pasan"]
    ante = [("Foto + pedido", ""), ("Generar una imagen", "con muebles inventados"), ("Recortar cada mueble", "Grounding DINO + SAM"),
            ("Buscar el más parecido", "por imagen (DINOv3)"), ("Lista de compra", "lo que más se parezca")]
    obra = [("Foto + pedido", ""), ("Plan", "una ficha por pieza"), ("Búsqueda", "en el catálogo descripto"),
            ("Elección: la lista", "productos reales"), ("Imagen", "al final, con ellos")]
    plantas = (f'<div class="dz-p"><div class="dz-k"><b>la propuesta aprobada</b><span>buscar por imagen</span></div>{planta.enfilada(ante, cls="ante")}</div>'
               f'<div class="dz-p"><div class="dz-k ok"><b>lo que construimos</b><span>RAG por texto</span></div>{planta.enfilada(obra)}</div>')
    rows = [dict(label="por imagen (recorte)", value=VT["imagen"], kind="alt"),
            dict(label="por texto (descripción)", value=VT["texto"], kind="main", nota=f'{sg(VT["dif"], 2)} {ic(*VT["ic"], d=2)}')]
    otros = [
        ("El catálogo traía fotos equivocadas",
         f"{D['n_855'] - D['n_ikea']} productos de IKEA con la foto de otro producto o de otra medida, o que no eran de living: "
         f"la lista diría una cosa y la imagen mostraría otra. Se revisó mirando cada foto."),
        ("No hay ground truth de la tarea real",
         "Nadie anotó la lista ideal para un ambiente vacío. Hay uno para el buscador y, para el flujo entero, un juez "
         "que compara listas."),
        ("El modelo de imagen rehace el cuarto",
         f"Mueve la cámara, inventa una ventana. Edición estricta y un control automático; aun así, {no_pasan} de {T['n']} "
         f"no se conservan."),
    ]
    ot = "".join(f'<div class="apri"><span>{i + 2}</span><p><strong>{esc(a)}.</strong> {b}</p></div>' for i, (a, b) in enumerate(otros))
    body = ('<div class="cuerpo">' + cab("01", "El recorrido · desafíos", "Desafíos: <em>de buscar por imagen a RAG por texto</em>") + "</div>"
            + f'<div class="dz">{plantas}</div>'
            + '<div class="dz2"><div class="dzl" data-desde="1"><div class="etq">1 · lo que medimos antes de cambiar: su buscador</div>'
            + hbars(rows, width=820, label_w=300, row_h=58, bar_h=24, x_max=0.8, ticks=[0, .2, .4, .6, .8], top=34, right=290,
                    val_d=2, esq=None, res=None, nota_x=96)
            + f'<p class="nota">Encontrar primero el producto anotado: el mismo ground truth y la misma unidad ({VT["n"]} productos '
              f'anotados, catálogo de {D["n_275"]}). Y por texto hace falta <b>una generación de imagen menos</b> por pedido.</p></div>'
            + f'<div class="dzr" data-desde="2">{ot}</div></div>'
            + remate("Cambiamos la arquitectura con una medición de su buscador. La versión por imagen <mark>nunca corrió de punta a punta</mark>.", desde=1))
    add(body, titulo="Desafíos", cap=1, t=50, cls="lam-dz", notas=[
        "Los desafíos. El más grande fue cambiar la arquitectura que nos aprobaron. La propuesta era generar "
        "primero una imagen amoblada, recortar cada mueble y buscar en el catálogo el más parecido, por imagen.",
        f"[paso] Construimos y medimos su buscador sobre el mismo ground truth: encontraba primero el "
        f"{pct(VT['imagen'])} de los productos anotados, contra {pct(VT['texto'])} buscando por texto. Con eso, y "
        f"con una generación de imagen menos por pedido, cambiamos a RAG por texto. Ojo: esa versión nunca corrió "
        f"de punta a punta; comparamos buscadores, no sistemas.",
        "[paso] Los otros tres: el catálogo traía fotos de otro producto y hubo que revisarlo a mano; no hay "
        "ground truth de la tarea real; y el modelo de imagen rehace el cuarto.",
    ])


# ---------------------------------------------------------------- el mapa de experimentos

def mapa(D: dict) -> None:
    LL = [  # ambiente, experimento, tipo, título (líneas), lo que quedó
        (1, "E6", "si", ["qué", "catálogo"], "IKEA + ABO"),
        (2, "E1", "si", ["qué se", "indexa"], "la descripción"),
        (3, "E9", "tram", ["embedder"], "Qwen3"),
        (3, "E10", "tram", ["dimensión"], miles(D["best_dim"])),
        (3, "E11", "tram", ["splitting", "y líneas"], "1 documento"),
        (3, "E12", "tram", ["base vectorial"], "ChromaDB"),
        (5, "E2", "si", ["cómo se escribe", "la consulta"], "la ficha"),
        (6, "E3", "si", ["léxica, por foto", "e híbrida"], "las tres"),
        (6, "E7", "si", ["con búsqueda", "o sin"], "7 a 0"),
        (6, "E13", "tram", ["filtros"], "kind"),
        (6, "E14", "tram", ["rerankers", "de texto"], "ninguno"),
        (7, "E5", "si", ["elegir con un VLM,", "y cuántos"], f"{D['cfg'].furnish.candidates} candidatos"),
        (8, "E15", "tram", ["la escena"], D["ESCENA"]["mapa"]),
        (9, "—", "pend", ["el modelo", "de imagen"], "sin correr"),
        (10, "—", "pend", ["los umbrales"], "a mano"),
    ]
    H = planta.H
    y1, paso = H + 78, 84
    por = {}
    for row in LL:
        por.setdefault(row[0], []).append(row)
    ex = []
    pasos_por_amb = {1: 1, 2: 1, 3: 1, 5: 2, 6: 2, 7: 2, 8: 3, 9: 3, 10: 3, 11: 3}

    def llamada(lx, cy, e, tipo, tit, dec):
        if e == "—":
            g_ = planta.llamada(lx, cy, "—", "", tipo)
        else:
            g_ = planta.llamada(lx, cy, e, f"{{{{LAM:{e}}}}}", tipo, ir=f"{{{{IR:{e}}}}}")
        tx = lx + 29
        nl = len(tit)
        y0 = cy - (12 if nl == 2 else 3)
        for j, t_ in enumerate(tit):
            g_ += f'<text class="lt" x="{tx:.1f}" y="{y0 + j * 18:.1f}">{esc(t_)}</text>'
        return g_ + f'<text class="ld {tipo}" x="{tx:.1f}" y="{y0 + nl * 18:.1f}">{esc(dec)}</text>'

    for n, rows in por.items():
        lx = planta.x0(n) + 27
        ys = [y1 + i * paso for i in range(len(rows))]
        g_ = f'<g data-desde="{pasos_por_amb[n]}">'
        g_ += f'<line class="guia" x1="{lx:.1f}" y1="{H:.1f}" x2="{lx:.1f}" y2="{ys[-1]:.1f}"/><circle class="guia-p" cx="{lx:.1f}" cy="{H:.1f}" r="4"/>'
        for (amb, e, tipo, tit, dec), cy in zip(rows, ys):
            g_ += llamada(lx, cy, e, tipo, tit, dec)
        ex.append(g_ + "</g>")
    # el banco de prueba: dos experimentos que no miden una fase, miden cuánto creerle al número
    bx0, bx1 = planta.x0(8) + 4, planta.x0(11) + (planta.x0(11) - planta.x0(10)) - 4
    by0, by1 = y1 + paso + 6, y1 + 3 * paso + 26
    banco = (f'<g data-desde="3"><rect class="banco" x="{bx0:.1f}" y="{by0:.1f}" width="{bx1 - bx0:.1f}" height="{by1 - by0:.1f}"/>'
             f'<text class="bk" x="{bx0 + 16:.1f}" y="{by0 + 26:.1f}">el banco de prueba del buscador</text>'
             f'<text class="bs" x="{bx0 + 16:.1f}" y="{by0 + 46:.1f}">{D["N_AMB"]} ambientes de IKEA anotados · {D["N_ANS"]} consultas con respuesta</text>'
             + llamada(bx0 + 42, by0 + 96, "E4", "si", ["¿error, o", "una variante?"], "tres niveles")
             + llamada(bx0 + 42 + (bx1 - bx0) / 2, by0 + 96, "E8", "tram", ["tres", "redactores"], "±2,5 puntos")
             + f'<text class="bs" x="{bx0 + 16:.1f}" y="{by1 - 14:.1f}">no miden una fase: miden cuánto creerle al número</text></g>')
    bottom = y1 + 3 * paso + 40 - H
    svg = planta.tira(None, vistas=range(1, 12), extra="".join(ex) + banco, bottom_pad=bottom)
    ley = ('<div class="mley">'
           '<span><i class="c si"></i>con lámina propia</span>'
           '<span><i class="c prueba"></i>de trámite: van juntos</span>'
           '<span><i class="c pend"></i>sin experimento que lo sostenga</span>'
           '<span class="r">arriba, el experimento · abajo, su lámina (clic para ir)</span></div>')
    body = ('<div class="cuerpo">' + cab("03", "El buscador · el mapa de los experimentos", "Quince experimentos: <em>ocho con lámina, siete de trámite</em>") + "</div>"
            + f'<div class="rtira mapa">{svg}</div>' + ley
            + remate("Cada llamada es una pregunta que le hicimos a una parte del sistema; <mark>dos cosas no las decidió ningún experimento</mark>.", desde=3))
    add(body, titulo="El mapa de experimentos", cap=3, t=45, cls="lam-rec lam-mapa", notas=[
        "La misma planta, con los experimentos encima: cada llamada es una pregunta que le hicimos a una parte "
        "del sistema; arriba el experimento, abajo su lámina. Las llenas, del 1 al 8, tienen lámina propia; las "
        "punteadas, del 9 al 15, son las de trámite.",
        "[paso] En el indexing: qué catálogo, qué se indexa, y las cuatro de trámite del índice.",
        "[paso] En cada pedido: cómo se escribe la consulta, la búsqueda híbrida, con búsqueda o sin búsqueda, y "
        "elegir con un modelo que ve.",
        "[paso] Dos, el 4 y el 8, no miden una fase: miden al banco de prueba. Y dos cosas no las decidió "
        "ningún experimento: el modelo de imagen y los umbrales del control.",
    ])


CSS_R = r"""
/* ---------- el recorrido */
.rtira{position:absolute;left:72px;top:222px;width:1776px}
.rtira svg{width:100%;height:auto}
.rc{position:absolute;left:72px;right:72px;top:402px;bottom:188px}
.lam-rec .remate{bottom:120px;font-size:38px}
.lam-rec .t{font-size:60px}
.rc .g2,.rc .g3{display:grid;column-gap:44px;height:100%}
.rc .col{display:flex;flex-direction:column;gap:16px;min-width:0;min-height:0}
.br .bt{font:400 17px/1 var(--mono);color:var(--cobalto);margin-bottom:9px;display:flex;align-items:center;gap:10px}
.br .bt::after{content:"";flex:1;border-top:1px solid var(--hilo)}
.br p{font:400 22px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.br p+p{margin-top:6px}
.br p strong,.br p b{color:var(--tinta);font-weight:640}
.br p.big{font:400 40px/1 var(--mono);color:var(--tinta-3);margin-bottom:6px}
.br p.big b{color:var(--cobalto);font-weight:700}
.br .vend{font-size:20px;color:var(--tinta-2);border-left:3px solid var(--hilo-2);padding-left:14px}
.rc .nota{font:400 16px/1.4 var(--mono);color:var(--tinta-3);margin-top:4px}
/* la referencia a un experimento: la llamada partida + el texto */
.xrf{display:grid;grid-template-columns:54px 1fr;column-gap:14px;align-items:center}
.xc{width:54px;height:54px;border-radius:50%;border:2px solid var(--cobalto);background:#fff;display:grid;grid-template-rows:1fr 1fr;overflow:hidden;cursor:pointer}
.xc b{font:700 16px/1 var(--mono);color:var(--cobalto);display:flex;align-items:flex-end;justify-content:center;padding-bottom:3px;border-bottom:1.4px solid var(--cobalto)}
.xc i{font:400 14px/1 var(--mono);font-style:normal;color:var(--tinta-2);display:flex;align-items:flex-start;justify-content:center;padding-top:4px}
.xc.prueba{border-style:dashed;border-color:var(--tinta-2)}.xc.prueba b{color:var(--tinta);border-color:var(--tinta-2)}
.xc.pend{border-style:dashed;border-color:var(--cota)}.xc.pend b{color:var(--cota);border-color:var(--cota)}
.xrf p{font:400 20px/1.28 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.xrf p b{color:var(--tinta);font-weight:640}
/* el prompt */
.pr{padding:14px 20px 16px;flex:none}
.prh{display:flex;justify-content:space-between;gap:16px;font:400 14px/1.2 var(--mono);color:var(--tinta-3);padding-bottom:9px;margin-bottom:10px;border-bottom:1px solid var(--hilo)}
.prh span:first-child{color:var(--cobalto);font-weight:700}
.prb p{font:400 15.5px/1.42 var(--mono);color:var(--tinta-2);margin-bottom:6px}
.prb p.el{color:var(--tinta-3);margin:2px 0 6px}
.prb mark{color:var(--tinta)}
.prb .var{color:var(--cobalto);font-weight:700}
/* cuadro de revisiones */
.rev{border-top:1.6px solid var(--tinta);flex:none}
.rvh{font:400 14px/1 var(--mono);color:var(--tinta-3);padding:9px 0 8px;border-bottom:1px solid var(--hilo)}
.rvg{display:grid;grid-template-columns:auto 1fr;column-gap:14px}
.rvn{font:700 14px/1 var(--mono);color:var(--tinta-2);padding:10px 0 0;white-space:nowrap}
.rvn.ult{color:var(--cobalto)}
.rvg p{font:400 17.5px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2);padding:7px 0 8px;border-bottom:1px solid var(--hilo)}
.rvg p b{color:var(--tinta);font-weight:640}
/* ejemplos */
.ej8{padding:16px 20px}
.ejh{display:flex;gap:16px;align-items:center;padding-bottom:12px;margin-bottom:8px;border-bottom:1px solid var(--hilo)}
.ejh img{width:96px;height:96px;object-fit:contain}
.ejh b{display:block;font:700 22px/1.1 var(--mono);color:var(--cobalto)}
.ejh span{font:400 16px/1.2 var(--mono);color:var(--tinta-3)}
.ej8 .l8{font-size:15px;line-height:1.85}
.ej8 .l8 span{width:96px}
.js{padding:14px 18px}
.js pre{font:400 15px/1.5 var(--mono);color:var(--tinta-2);white-space:pre-wrap;word-break:break-word;margin:0}
.js pre mark{color:var(--tinta)}
/* 1 · catálogo */
.regs{display:grid;grid-template-columns:1fr 1fr;gap:28px}
.reg{display:grid;grid-template-columns:150px 1fr;gap:16px;padding:14px 16px;align-items:center}
.reg img{width:150px;height:150px;object-fit:contain}
.reg dl{display:grid;grid-template-columns:92px 1fr;row-gap:5px;font:400 16px/1.25 var(--mono)}
.reg dt{color:var(--tinta-3)}.reg dd{color:var(--tinta);word-break:break-all}.reg dd.k{color:var(--cobalto);font-weight:700}
.kinds p{font:400 22px/1.32 var(--sans);font-stretch:92%;color:var(--tinta-2)}
.kinds p b{color:var(--tinta)}
.kinds .kt{font:400 17px/1.5 var(--mono);color:var(--cobalto);margin-top:10px}
.kinds .kt span{color:var(--tinta);font-weight:700;margin-right:8px}
/* 3 · índice */
.reg-ch{padding:14px 20px 16px}
.rkv{display:grid;grid-template-columns:120px 1fr;row-gap:10px;column-gap:12px;align-items:baseline}
.rkv span{font:400 15px/1.3 var(--mono);color:var(--tinta-3)}
.rkv code{font:400 15.5px/1.4 var(--mono);color:var(--tinta);word-break:break-word}
.rkv code i{font-style:normal;color:var(--cobalto)}
.vfig{margin-top:16px}
.vfig svg{display:block;width:100%;height:46px;border:1px solid var(--hilo)}
.vley{display:flex;justify-content:space-between;font:400 13.5px/1 var(--mono);color:var(--tinta-3);margin-top:6px}
/* 4 · foto + pedido */
.fp4 .fotos{display:flex;gap:18px;align-items:flex-end;margin:12px 0 4px}
.fp4 .vista{position:relative}.fp4 .vista .etq{position:absolute;left:0;bottom:-26px;font-size:15px}
.fp4 .pedido{font-size:20px;line-height:1.36;margin-top:22px;color:var(--tinta-2)}
.fp4 .fpr{display:flex;gap:28px;align-items:flex-start;margin-top:12px}
.fp4 .fpr .pedido{margin-top:0;font-size:20px}
/* 5 · plan */
.p5{font-size:20px;line-height:1.38}
.p5 mark{font-style:italic}
.p5room svg.sala{width:100%;height:400px}
.p5room .sala .rot .rt{font-size:23px}.p5room .sala .rot .rs{font-size:17px}
/* 6 · búsqueda */
.g2b{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.wh pre{font-size:14.5px}
.cosf{padding:14px 18px}
.vrow{display:grid;grid-template-columns:132px 1fr;align-items:center;gap:10px;margin-bottom:10px}
.vrow span{font:400 14px/1.2 var(--mono);color:var(--tinta-2)}
.vrow svg{display:block;width:100%;height:34px;border:1px solid var(--hilo)}
.cosr{font:400 19px/1.2 var(--mono);color:var(--tinta-2);margin-top:6px}
.cosr b{color:var(--cobalto);font-size:24px}
.cands{margin-top:8px}
.cands .etq{font-size:16px;margin-bottom:10px}
.cands .tira{gap:20px}
.br.rr p{font-size:19px}
/* 7 · elección */
.tira.chr{gap:12px}
.tira.chr .ficha figcaption b{font-size:15px}
.r7c{font:400 21px/1.3 var(--sans);font-stretch:92%;color:var(--tinta-2);margin-top:4px}
.r7c b{color:var(--cobalto)}
.rc .porque{font-size:19px;line-height:1.36;color:var(--tinta-2)}
/* 9 · imagen */
.io9{display:grid;grid-template-columns:480px 540px;column-gap:48px;align-items:start}
.io9 .etq{margin-bottom:12px}
.ins{display:flex;flex-direction:column;gap:12px}
.ins .in0,.ins .in1{position:relative;background:#fff;border:1px solid var(--hilo)}
.ins img{display:block}
.ins .in0 img{width:478px;height:300px;object-fit:cover}
.ins .ing{display:grid;grid-template-columns:repeat(8,1fr);gap:8px}
.ins .in1 img{width:100%;aspect-ratio:1;object-fit:contain}
.ins span{position:absolute;left:0;top:0;background:var(--tinta);color:#fff;font:700 12px/1 var(--mono);padding:3px 5px}
/* 10 · control */
.atts.r10{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;position:static}
.atts.r10 .at .ai{position:relative;aspect-ratio:4/3;background:#fff;padding:6px;box-shadow:0 1px 0 rgba(19,32,44,.06),0 18px 30px -22px rgba(19,32,44,.55)}
.atts.r10 .at .ai img{width:100%;height:100%;object-fit:cover}
.atts.r10 figcaption{display:flex;flex-direction:column;gap:3px;margin-top:10px}
.atts.r10 figcaption b{font:600 20px/1.1 var(--sans);font-stretch:88%}
.atts.r10 figcaption span{font:400 15px/1.25 var(--mono);color:var(--tinta-3)}
/* 11 · la lista */
.lista{display:flex;flex-direction:column;border-top:1.6px solid var(--tinta)}
.lista .li{display:grid;grid-template-columns:44px 190px 140px 1fr 50px;align-items:center;column-gap:16px;height:40px;border-bottom:1px solid var(--hilo)}
.lista .li img{width:34px;height:34px;object-fit:contain}
.lista .li .k{font:600 20px/1 var(--sans);font-stretch:88%}
.lista .li code{font:400 16px/1 var(--mono);color:var(--cobalto)}
.lista .li .m{font:400 15px/1 var(--mono);color:var(--tinta-3)}
.lista .li b{font:700 17px/1 var(--mono);text-align:right}
/* la planta: cuadro de locales */
.cuadro{position:absolute;left:0;top:0;width:1920px;height:1080px;pointer-events:none}
.cdk{position:absolute;left:72px;top:408px;font:400 16px/1 var(--mono);color:var(--tinta-3)}
.loc-c{position:absolute;top:446px;border-top:1.6px solid var(--tinta);padding-top:12px}
.loc-c .q{font:600 22px/1.16 var(--sans);font-stretch:84%;color:var(--tinta);min-height:78px}
.loc-c .con{font:400 16.5px/1.25 var(--mono);color:var(--tinta-2);margin-top:10px;min-height:42px}
.loc-c .cu{font:700 16.5px/1.25 var(--mono);color:var(--cobalto);margin-top:8px}
.refs{position:absolute;left:72px;right:72px;top:742px;display:flex;flex-wrap:wrap;align-items:center;column-gap:26px;row-gap:10px;
  padding-top:14px;border-top:1px solid var(--hilo)}
.refs .rft{font:700 15px/1 var(--mono);color:var(--tinta-3);margin-right:6px}
.refs span{display:flex;align-items:center;gap:10px}
.refs i{font:400 16px/1.2 var(--mono);font-style:normal;color:var(--tinta-2)}
.loc-c.off .cu{color:var(--tinta-3);font-weight:400}
/* el mapa de experimentos */
.rtira.mapa{top:222px}
.mley{position:absolute;left:72px;right:72px;top:826px;display:flex;gap:34px;align-items:center;font:400 17px/1.2 var(--mono);color:var(--tinta-2)}
.mley span{display:flex;align-items:center;gap:10px}
.mley .r{margin-left:auto;color:var(--tinta-3)}
.mley i.c{width:26px;height:26px;border-radius:50%;border:2px solid var(--cobalto);background:#fff;display:block}
.mley i.c.prueba{border-style:dashed;border-color:var(--tinta-2)}
.mley i.c.pend{border-style:dashed;border-color:var(--cota)}
"""

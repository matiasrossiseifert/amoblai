"""El recorrido: el flujo ambiente por ambiente, con la planta arriba (el ambiente actual encendido y
el camino hecho en naranja), y el mapa de experimentos: la misma planta con una llamada de detalle
por experimento, que remite a su lámina.

Todo sale de los archivos del repo: los prompts se leen de src/amoblai/prompts (el extracto es
texto literal del archivo), la configuración de datos/configs/amoblai.yaml y los ejemplos de las
corridas de datos/resultados/amoblar/.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

import img
import planta
import sala
from base import KIND_ES, add, cab, esc, f, ficha, foto_producto, medidas, pct, remate, usd
from datos_deck import REPO, RES, jload

A = RES / "amoblar"
CL = A / "caballito-living"
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


def xref(e: str, html: str, tipo: str = "si", desde=None) -> str:
    d = f' data-desde="{desde}"' if desde is not None else ""
    return (f'<div class="xrf"{d}><span class="xc {tipo}" data-ir="{{{{IR:{e}}}}}"><b>{e.rstrip("p")}</b><i>{{{{LAM:{e}}}}}</i></span>'
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


# ---------------------------------------------------------------- las láminas

def build(D: dict, ctx: dict) -> None:
    cfg = config()
    fu = cfg.furnish
    b, o, M = D["best"], D["opus"], D["M"]
    cl = D["img"]["caballito-living"]
    req = cl["req"]["request"]
    plan_r = jload(CL / "1_searches.json")
    plan = plan_r["answer"]["pieces"]
    cands = jload(CL / "2_candidates.json")["pieces"]
    ch_r = cl["choice"]
    choices = ch_r["answer"]["choices"]
    scene = jload(CL / "4_scene.json")
    gen = cl["gen"]
    sofa = choices[0]["id"]
    no_first = sum(1 for c, p in zip(choices, cands) if p["candidates"][0]["id"] != c["id"])
    v0b = D["v0_path"][-1]
    K = kinds()
    n_tipos = len(set(K.values()))
    cv = D["curva"]["por_k"]
    kf, ka = D["k_flujo"], D["k_antes"]
    g = D["grad"]["consultas"]
    rag_f = [r["fidelidad"]["faithfulness"] for r in D["ragas"]]
    rag_r = [r["relevancia"]["answer_relevance"] for r in D["ragas"]]
    llm = fu.llm
    modelo = llm["model"].replace("claude-opus-5-5", "Opus 5.5")
    nb = fu.generators["nano_banana_2"]

    # ================================================================ la planta del flujo
    R, _ = planta._geo(planta.W, planta.G)
    k = 1776 / (planta.W + 46)
    filas = {
        1: ("la foto, el kind y las medidas", "IKEA + ABO", "una vez"),
        2: ("ocho líneas por producto", "un LLM mira la foto", "una vez"),
        3: ("un vector por producto", "Qwen3 → ChromaDB", "una vez"),
        4: ("la foto vacía y el pedido", "texto libre", "lo pone el usuario"),
        5: ("piezas, kind, medida y consulta", modelo, usd(D["costo_plan"])),
        6: (f"{kf} candidatos por pieza", "filtro + coseno", "local, gratis"),
        7: ("uno por pieza, y cuántos", modelo, usd(D["costo_choose"])),
        8: ("el prompt de la imagen", "plantilla, sin LLM", "gratis"),
        9: ("la foto amoblada", "Nano Banana 2", f"{usd(D['img_precio'])} c/u"),
        10: ("¿sigue siendo tu cuarto?", "SIFT + RANSAC", "local, gratis"),
        11: ("la lista y la imagen", "ids y cantidades", f"≈ {usd(D['costo_corrida'])} todo"),
    }
    cols = ""
    for n, (q, con, cuesta) in filas.items():
        x0, x1 = R[n]
        left = 72 + (x0 + 6) * k + 10
        wd = (x1 - x0) * k - 18
        st = n // 4 if n >= 4 else 0
        cols += (f'<div class="loc-c{" off" if n <= 3 else ""}" style="left:{left:.0f}px;width:{wd:.0f}px" data-desde="{1 if n <= 3 else 2}">'
                 f'<p class="q">{esc(q)}</p><p class="con">{esc(con)}</p><p class="cu">{esc(cuesta)}</p></div>')
    marcas = {2: "LLM", 5: "LLM", 7: "LLM", 9: "IMAGEN"}
    body = ('<div class="cuerpo">' + cab("01", "El recorrido · la planta", "El flujo, <em>como la planta de una casa</em>") + "</div>"
            + rtira(None, marcas=marcas)
            + '<div class="cuadro"><div class="cdk">cuadro de locales · qué sale de cada ambiente, con qué, y cuánto cuesta por pedido</div>'
            + cols + "</div>" + referencias_plano()
            + remate("El índice se arma <mark>una vez</mark>; los otros ocho ambientes se recorren <mark>en cada pedido</mark>.", desde=3))
    add(body, titulo="La planta del flujo", cap=1, t=35, cls="lam-rec lam-planta", notas=[
        "Así está armado amoblai, dibujado como la planta de una casa: cada fase es un ambiente y se pasa "
        "al siguiente por una puerta.",
        "[paso] A la izquierda, un pabellón que se construye una vez, offline: catálogo, descripción e "
        "índice. El índice llega a la búsqueda por esa pasarela.",
        "[paso] Lo demás se recorre en cada pedido, de la foto a la lista. Tres ambientes llaman a un LLM, y "
        f"una corrida cuesta unos {usd(D['costo_corrida'])}.",
        "[paso] Los recorremos uno por uno: qué hace, qué decidimos y con qué experimento.",
    ])

    # ================================================================ 1 · catálogo
    ab = "abo-B082QDKRC5"
    ik = "902.976.57"

    def registro(pid, fuente):
        it = D["abo_items"][pid] if pid.startswith("abo-") else D["items"][pid]
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
                   f'de living ni comedor. Fotos de {D["ikea_px"]} px; los asientos, <strong>sin medidas</strong>.</p>')
        + bloque_r("ABO · Amazon Berkeley Objects, CVPR 2022",
                   f'<p class="big">{D["abo_listados"]} → <b>{D["n_abo"]}</b></p>'
                   f'<p>Publicaciones reales de Amazon: una por modelo, con foto de al menos 800 px; {D["n_abo"]} '
                   f'con descripción. Con medidas, el {pct(D["abo_con_medidas"])}.</p>', desde=1)
        + xref("E12", f"<b>Qué catálogo:</b> el flujo usa los dos juntos, {D['n_todos']} productos; las métricas con "
               f"ground truth, solo IKEA.", desde=2)
        + '</div><div class="col">'
        + f'<div class="regs" data-desde="1">{registro(ik, "IKEA")}{registro(ab, "ABO")}</div>'
        + f'<div class="kinds" data-desde="2"><p><b>{len(K)} kinds en {n_tipos} tipos.</b> El kind es más fino que el tipo, '
          f'y es el filtro duro de la búsqueda: una silla de escritorio no es un sillón.</p>'
          f'<p class="kt"><span>table</span>→ {" · ".join(esc(x) for x in tabla)}</p></div>'
        + "</div></div>")
    fase(1, "Catálogo: <em>productos reales, con su foto y su kind</em>", cont, t=30,
         rem="Del catálogo el flujo usa <mark>la foto, el kind y las medidas</mark>; el nombre comercial, no.", rem_desde=2,
         notas=[
             f"El catálogo. El dataset de IKEA de Tautkute y otros, revisado a mano: de {D['n_855']} productos "
             f"quedan {D['n_ikea']}.",
             f"[paso] Y un segundo catálogo, Amazon Berkeley Objects: {D['n_abo']} productos, casi todos con "
             f"medidas. Cada uno entra con su foto, su tipo, su kind y sus medidas.",
             f"[paso] El kind es más fino que el tipo: hay {len(K)}, y es el filtro duro de la búsqueda. Usar los "
             f"dos catálogos lo decidió el experimento 12.",
         ])

    # ================================================================ 2 · descripción
    seller = D["items"][sofa]
    vend = f'Type: {seller["category"]} · Name: {seller["name"]} · Colors: {", ".join(seller.get("colors") or [])} · {seller.get("description", "")}'
    fm3, _ = prompt_txt("describe_product_v3")
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
        + bloque_r("por qué", f'<p>El texto del vendedor es marketing:</p><p class="cita vend">«{esc(seller.get("description", ""))}»</p>'
                   f'<p>No dice que es gris claro ni de tres cuerpos.</p>')
        + bloque_r("quién la escribe", "<p><strong>IKEA:</strong> subagentes de Claude Code. <strong>ABO:</strong> "
                   f"{modelo} por la API.</p>")
        + xref("E1", f"Texto y no imagen: <b>{f(D['v1_275']['hit@1'])}</b> contra {f(v0b['hit1'])}.", desde=0)
        + xref("E2", f"Las ocho líneas contra el texto del vendedor: <b>{f(M['qwen3|description|filtro-type']['hit@1'])}</b> "
               f"contra {f(M['qwen3|seller|filtro-type']['hit@1'])}.")
        + '</div><div class="col" data-desde="1">' + pr + rev + "</div>"
        + f'<div class="col" data-desde="3"><div class="etq">la salida · para el sofá de la lista</div>'
        + f'<div class="hoja ej8"><div class="ejh"><img src="{img.uri(foto_producto(D, sofa), 200, 200, fit="contain")}" alt="">'
          f'<div><b>{sofa}</b><span>{esc(seller["name"])} · {KIND_ES.get(seller["kind"], seller["kind"])}</span></div></div>{l8(D["desc"][sofa], 40)}</div>'
        + "</div></div>")
    fase(2, "Descripción: <em>cada producto, en ocho líneas fijas</em>", cont, t=45,
         rem="Se indexa lo que un modelo <mark>ve en la foto</mark>, no lo que dice la tienda.", rem_desde=3,
         notas=[
             "La descripción. El texto del vendedor es marketing: del sofá no dice que es gris claro ni de tres "
             "cuerpos. Por eso un modelo de visión mira la foto y lo describe. Texto y no imagen, y nuestras "
             "ocho líneas y no las del vendedor: experimentos 1 y 2.",
             "[paso] El prompt pide ocho líneas fijas, en inglés: tipo, uso, estilo de una lista cerrada, "
             "materiales, colores, forma, sensación y con qué combina. Solo lo que se ve.",
             "[paso] La v3 sumó lámparas y deco; la versión por la API, para ABO, devuelve además el kind.",
             "[paso] Y esto escribió para el sofá de la lista.",
         ])

    # ================================================================ 3 · índice
    doc_idx = next(json.loads(x)["description"] for x in
                   (REPO / "datos/cache/rag/index/todos-written_todos-qwen3/items.jsonl").read_text().splitlines()
                   if json.loads(x)["id"] == sofa)
    vd = vector(doc_idx)  # el texto exacto que se embebió
    it = D["items"][sofa]
    meta = f'{{"category": "{it["category"]}", "kind": "{it["kind"]}", "width": −1, "depth": −1, "height": −1}}'
    first = ", ".join(num(x) for x in vd[:5]) if vd is not None else ""
    dims = D["dims"]
    dec = (
        xref("E3", f"<b>Qué se embebe:</b> la descripción entera, un documento por producto. Partirla en líneas "
             f"pierde: {f(D['chunks_al']['hit@1'])} y {f(D['chunks_max']['hit@1'])}, contra <b>{f(b['hit@1'])}</b>.")
        + xref("E2", f"<b>Con qué:</b> {esc(D['embed_model'])}, local. Hashing de palabras "
               f"{f(M['hashing|description|filtro-type']['hit@1'])}, BGE-base {f(M['bge|description|filtro-type']['hit@1'])}. "
               "Sin instrucción de consulta: la consulta ya está escrita como un documento.", desde=1)
        + xref("E4", f"<b>Cuántas dimensiones:</b> {D['best_dim']}. Truncado (Matryoshka), 512 da {f(dims[512]['hit@1'])}; "
               f"32, {f(dims[32]['hit@1'])}. El índice entero pesa {f(D['indice_mb'], 1)} MB.", desde=1)
        + xref("E5", f"<b>Dónde:</b> ChromaDB, HNSW en coseno, ef_search {D['hnsw']['ef_search']}, M "
               f"{D['hnsw']['max_neighbors']}. Mismo ranking que la búsqueda exacta en {D['chroma_igual_type']} de "
               f"{D['chroma_total_type']}.", desde=2))
    doc_lines = D["desc"][sofa].strip().splitlines()
    rec = (f'<div class="hoja reg-ch"><div class="prh"><span>un registro de ChromaDB</span><span>colección del catálogo IKEA + ABO</span></div>'
           f'<div class="rkv"><span>id</span><code>"{sofa}"</code>'
           f'<span>document</span><code>"{esc(doc_lines[0])}\\n{esc(doc_lines[1][:30])}…"</code>'
           f'<span>embedding</span><code>[{first}, … ]  <i>{len(vd) if vd is not None else D["best_dim"]} números, norma 1</i></code>'
           f'<span>metadata</span><code>{esc(meta)}</code></div>'
           f'<div class="vfig">{vec_svg(vd) if vd is not None else ""}<div class="vley"><span>0</span><span>los {D["best_dim"]} números de este sofá · azul positivo, naranja negativo</span><span>{D["best_dim"] - 1}</span></div></div>'
           f'<p class="nota">Sin medidas, el catálogo guarda −1: el producto pasa cualquier filtro de tamaño.</p></div>')
    cont = (f'<div class="g2" style="grid-template-columns:640px 1fr"><div class="col">{dec}</div>'
            f'<div class="col" data-desde="3">{rec}</div></div>')
    fase(3, "Índice: <em>un vector por descripción</em>", cont, t=45,
         rem="Cuatro decisiones, <mark>cuatro experimentos</mark>; ninguna se eligió por gusto.", rem_desde=3,
         notas=[
             f"El índice. Se embebe la descripción entera, un documento por producto; partirla en líneas "
             f"empeora, experimento 3.",
             f"[paso] Con {D['embed_model']}, local, que le ganó a contar palabras y a BGE. Sin la instrucción "
             f"de consulta del modelo: nuestra consulta ya está escrita como un documento. Y las "
             f"{D['best_dim']} dimensiones: el índice entero pesa {f(D['indice_mb'], 1)} MB.",
             f"[paso] Va a ChromaDB, con un índice HNSW en coseno: da exactamente el mismo ranking que la "
             f"búsqueda exacta, y guarda la metadata para filtrar.",
             "[paso] Así queda un registro: el id, el documento, los mil veinticuatro números y la metadata. El "
             "sofá no tiene medidas: el catálogo guarda menos uno y pasa cualquier filtro.",
         ])

    # ================================================================ 4 · foto + pedido
    alv = jload(A / "prueba-alvear2" / "request.json")
    cont = (
        '<div class="g2 fp4" style="grid-template-columns:1fr 1fr">'
        f'<div class="col"><div class="etq">un pedido detallado · una foto</div>'
        f'<div class="fpr"><div class="foto" style="width:380px;height:285px;flex:none"><img src="{img.uri(REPO / cl["req"]["photo"], 760, 570, q=74)}" alt=""></div>'
        f'<p class="cita pedido">«{esc(req)}»</p></div></div>'
        f'<div class="col" data-desde="1"><div class="etq">un pedido corto · dos fotos del mismo cuarto</div>'
        f'<div class="fotos"><div class="foto" style="width:380px;height:254px"><img src="{img.uri(REPO / alv["photo"], 760, 508, q=74)}" alt=""></div>'
        f'<div class="foto vista" style="width:210px;height:140px"><img src="{img.uri(REPO / alv["views"][0], 420, 280, q=74)}" alt=""><span class="etq">otra vista</span></div></div>'
        f'<p class="cita pedido">«{esc(alv["request"])}»</p>'
        f'<p class="nota">La otra vista va a {modelo} en plan y elección, solo para entender el cuarto. Al modelo de imagen '
        f'va únicamente la primera foto.</p></div></div>')
    fase(4, "Foto y pedido: <em>lo único que pone el usuario</em>", cont, t=15,
         rem="Nada de formularios: <mark>una foto y lo que querés</mark>, en tus palabras.", rem_desde=1,
         notas=[
             "Cada pedido empieza con lo que pone el usuario: una foto del ambiente vacío y el pedido en texto "
             "libre.",
             "[paso] Puede sumar otra vista del cuarto: la ven plan y elección, pero se amobla la primera.",
         ])

    # ================================================================ 5 · plan (el prompt)
    fm4, _ = prompt_txt("search_query_v4")
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
    cont = (
        '<div class="g3" style="grid-template-columns:470px 1fr 480px">'
        '<div class="col">'
        + bloque_r("qué hace", f"<p><strong>{modelo}</strong> (effort {llm['effort']}) mira la foto y el pedido, y por cada "
                   f"pieza que hace falta devuelve su <strong>kind</strong>, hasta qué <strong>tamaño</strong> entra y "
                   f"una <strong>consulta en las ocho líneas</strong> del catálogo.</p>"
                   f'<p class="nota">{usd(D["costo_plan"])} por pedido, en promedio.</p>')
        + xref("E6", f"<b>Reescribir la consulta:</b> el nombre del kind solo da {f(D['q_kind']['hit@1'])}; la línea Type, "
               f"{f(D['q_type']['hit@1'])}; las ocho líneas, <b>{f(b['hit@1'])}</b>.")
        + xref("E9", f"Con consultas de otros dos redactores, {f(D['repro'][0]['mean'])} ± {f(D['repro'][0]['sd'])}: "
               "el orden de los métodos se sostiene.", tipo="prueba")
        + f'</div><div class="col" data-desde="1">{pr}</div>'
        + f'<div class="col">{rev}</div></div>')
    fase(5, "Plan: <em>el pedido se reescribe, una consulta por pieza</em>", cont, t=50, sufijo=" · el prompt",
         rem="El paso que más pesa del retrieval es <mark>cómo se escribe la consulta</mark>.", rem_desde=2,
         notas=[
             f"Plan, el ambiente que más pesa. {modelo} mira la foto y el pedido y, por pieza, decide el kind, "
             f"hasta qué tamaño entra y una consulta en las mismas ocho líneas que los documentos. Es query "
             f"rewriting, como HyDE: el experimento 6 muestra que es lo que más pesa del retrieval.",
             "[paso] El prompt pide leer el cuarto como un diseñador, respetar la pieza nombrada, porque una "
             "silla no es un sillón, y no decir lo que no tiene que ser: los embeddings no leen la negación.",
             "[paso] Cuarta versión, cada una por un error: la v1 pidió un sillón por una silla; la v3, por un "
             "living largo con cuatro muebles; la v4 sacó el tope de seis piezas.",
         ])

    # ================================================================ 5 · plan (lo que devuelve)
    P = sala.Proj()
    vb = sala.viewbox(P, pad=(20, 20, 10, 20), m=0)
    kinds_s = ["sofa", "alfombra", "mesa", "tv", "lampara", "almohadones", "planta", "cortinas"]
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
            h = h.replace(esc(fr), f"<mark>{esc(fr)}</mark>", 1)
        return h

    js = (f'<div class="hoja js"><div class="prh"><span>1_searches.json · la pieza 1</span><span>respuesta de {modelo}</span></div><pre>'
          f'"piece": "{hl(p0["piece"], ["light grey three-seat sofa", "against the long left wall"])}",\n'
          f'"kinds": ["{p0["kinds"][0]}"],\n'
          f'"max_width_cm": {p0["max_width_cm"]:.0f}, "max_depth_cm": {p0["max_depth_cm"]:.0f},\n'
          f'"query":\n' + "\n".join(f'  {hl(x, ["three-seat", "light grey"])}' for x in q0) + "</pre></div>")
    reqh = hl(req, ["un sofá de tres cuerpos gris claro contra la pared de la izquierda"])
    cont = (
        '<div class="g3" style="grid-template-columns:400px 1fr 590px">'
        f'<div class="col"><div class="etq">el pedido</div><p class="cita pedido p5">«{reqh}»</p>'
        f'<p class="nota">{len(plan)} piezas · {usd(plan_r["cost_usd"])} · {f(plan_r["meta"]["latency_s"], 0)} s</p></div>'
        f'<div class="col p5room" data-desde="1"><div class="etq">las {len(plan)} piezas, con kind y tamaño máximo</div>{room}</div>'
        f'<div class="col" data-desde="2">{js}</div></div>')
    fase(5, "Plan: <em>el producto ideal, escrito como el catálogo</em>", cont, t=30, sufijo=" · lo que devuelve",
         rem="Plan no ve el catálogo: <mark>describe el producto ideal</mark> con las palabras del catálogo.", rem_desde=2,
         notas=[
             "Qué devuelve plan para el living de la portada. El pedido es largo y bastante preciso.",
             f"[paso] Plan lo convierte en {len(plan)} piezas, cada una con su kind y, cuando el cuarto lo limita, "
             f"un tamaño máximo: el sofá hasta {p0['max_width_cm']:.0f} por {p0['max_depth_cm']:.0f}, la mesa "
             f"ratona hasta 45 de alto.",
             "[paso] Y la consulta de cada pieza: «gris claro» pasa a «Colors: light grey», «tres cuerpos» a "
             "«three-seat». Plan no ve el catálogo: describe el sofá ideal, en el formato de los documentos.",
         ])

    # ================================================================ 6 · búsqueda
    wh = where_de(p0, fu.size_slack)
    whs = json.dumps(wh, ensure_ascii=False)
    whs = (whs.replace('{"$and": [', '{"$and": [\n  ').replace('}]}, {"width"', '}]},\n  {"width"')
           .replace('}, {"depth"', '},\n  {"depth"').replace(', {"$and": [{"kind"', ',\n         {"$and": [{"kind"'))
    vq = vector(p0["query"])
    c0 = cands[0]["candidates"]
    tira_c = "".join(ficha(D, c["id"], 104, pos=i + 1, hi=c["id"] == sofa, titulo=num(c["score"]), cap=True)
                     for i, c in enumerate(c0))
    cos = float(vq @ vd) if (vq is not None and vd is not None) else None
    cont = (
        '<div class="g2" style="grid-template-columns:520px 1fr">'
        '<div class="col">'
        + bloque_r("qué hace", f"<p>Por pieza: primero el <strong>filtro duro</strong> (el kind de plan, y cada medida hasta "
                   f"un {pct(fu.size_slack)} más que el máximo; sin medida, pasa). Después, el <strong>coseno</strong> entre la "
                   f"consulta y las descripciones: los {kf} más cercanos.</p>")
        + xref("E2", f"<b>Filtro:</b> kind, tipo o ninguno dan {f(D['kind']['hit@1'])}, {f(b['hit@1'])} y "
               f"{f(D['none']['hit@1'])}: se pisan. Queda el kind, que decide plan.")
        + xref("E10", f"Lo que trae sirve: el primero tiene nota ≥ 1 en el {pct(g['todas']['util1'])}, aunque no sea "
               "el anotado.", tipo="prueba")
        + bloque_r("reranking: probado", f"<p>Un cross-encoder de texto empeora ({f(D['minilm']['hit@1'])}); "
                   f"{modelo} mirando las fotos sube a <b>{f(o['hit@1'])}</b>. No quedó como paso aparte: lo hace la "
                   f"elección, que ya mira las fotos. Qwen3-Reranker quedó configurado, sin correr.</p>", desde=3, cls="rr")
        + '</div><div class="col">'
        + f'<div class="g2b" data-desde="1"><div class="hoja js wh"><div class="prh"><span>el where de ChromaDB · el sofá</span><span>rag/filters.py</span></div><pre>{esc(whs)}</pre></div>'
        + (f'<div class="hoja cosf"><div class="prh"><span>consulta · documento</span><span>los dos vectores, de la caché</span></div>'
           f'<div class="vrow"><span>consulta</span>{vec_svg(vq, h=34)}</div><div class="vrow"><span>sofá {sofa}</span>{vec_svg(vd, h=34)}</div>'
           f'<p class="cosr">coseno = producto punto = <b>{num(cos)}</b></p></div>' if cos is not None else "")
        + "</div>"
        + f'<div class="cands" data-desde="2"><div class="etq">los {kf} más cercanos por coseno · en azul, el que terminó en la lista</div>'
          f'<div class="tira">{tira_c}</div></div>'
        + "</div></div>")
    fase(6, "Búsqueda: <em>primero el filtro, después el coseno</em>", cont, t=40,
         rem="El filtro decide <mark>qué es</mark>; el coseno decide <mark>cuál</mark>.", rem_desde=2,
         notas=[
             f"La búsqueda. Primero un filtro duro: el kind de plan y el tamaño máximo, con un "
             f"{pct(fu.size_slack)} de margen porque sale de una foto. Kind, tipo o ningún filtro dan casi lo "
             f"mismo, experimento 2.",
             f"[paso] Este es el where del sofá. Después, el coseno entre la consulta y la descripción: "
             f"{num(cos)}.",
             f"[paso] Salen los {kf} más cercanos; el de la lista salió segundo. Los sofás de IKEA no tienen "
             f"medidas: el tamaño no los filtra.",
             "[paso] Reordenarlos con un cross-encoder empeora; con Opus mirando las fotos mejora mucho. Eso lo "
             "hace el ambiente siguiente.",
         ])

    # ================================================================ 7 · elección
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
    i_rug = 1
    cr = cands[i_rug]["candidates"]
    pos_rug = next(i for i, c in enumerate(cr) if c["id"] == choices[i_rug]["id"]) + 1
    tira_r = "".join(ficha(D, c["id"], 84, pos=i + 1, hi=c["id"] == choices[i_rug]["id"], titulo=num(c["score"]), cap=True)
                     for i, c in enumerate(cr))
    n_img = ch_r["meta"]["images"]
    cont = (
        '<div class="g3" style="grid-template-columns:470px 1fr 540px">'
        '<div class="col">'
        + bloque_r("qué hace", f"<p><strong>{modelo}</strong> ve el cuarto y las {kf} fotos de cada pieza, y elige "
                   f"<strong>la combinación</strong>: uno por pieza, cuántos, y por qué.</p>"
                   f'<p class="nota">{usd(D["costo_choose"])} en promedio · {f(D["lat_choose"], 0)} s (mediana)</p>')
        + xref("E7", f"<b>Reranking con un modelo que ve:</b> {f(b['hit@1'])} → <b>{f(o['hit@1'])}</b>.")
        + xref("E8", f"<b>k = {kf}</b> candidatos: de {ka} a {kf} suma {f(cv[str(kf)]['acierto_eleccion'] - cv[str(ka)]['acierto_eleccion'])}.")
        + '</div>'
        + f'<div class="col" data-desde="1">{pr}{rev}</div>'
        + f'<div class="col" data-desde="3"><div class="etq">la alfombra · {n_img} imágenes en la llamada</div>'
          f'<div class="tira chr">{tira_r}</div>'
          f'<p class="r7c">Eligió la <b>{pos_rug}.ª por coseno</b>:</p><p class="cita porque">«{esc(choices[i_rug]["why"])}»</p>'
          f'<p class="nota">En {no_first} de las {len(choices)} piezas no eligió la primera por coseno.</p></div>'
        + "</div>")
    fase(7, "Elección: <em>Opus mira las fotos y arma el conjunto</em>", cont, t=40,
         rem="El coseno compara textos; la elección <mark>mira las fotos</mark> y el cuarto.", rem_desde=3,
         notas=[
             f"La elección. {modelo} ve el cuarto y las {kf} fotos de cada pieza y elige la combinación: uno "
             f"por pieza, cuántos y por qué. Es el reranking del flujo; el experimento 7 mide cuánto suma y el 8, "
             f"por qué {kf}.",
             "[paso] El prompt pide elegir las piezas juntas, como un solo look, juzgando por las fotos.",
             "[paso] La v2 agregó cantidades: cero saca la pieza.",
             f"[paso] Para la alfombra eligió la quinta por coseno, la de 170 por 240 que arma la zona. En "
             f"{no_first} de las {len(choices)} piezas no eligió la primera.",
         ])

    # ================================================================ 8 · escena
    sp = scene["answer"]["prompt"]
    plines = sp.split("\n")
    head = plines[0]
    prods = [x for x in plines if x.startswith("image ")]
    hm = esc(head)
    for fr in ["Edit image 1. It is a photo of the client's own room", "the same room, exactly",
               "Do not add, remove, move or enlarge any wall, window, door or opening"]:
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
    mb = D["img"]["experimento-buen-pedido"]["met"]["ambiente"]["ssim_fuera_de_los_muebles"]
    ms = D["img"]["experimento-buen-pedido-estricto"]["met"]["ambiente"]["ssim_fuera_de_los_muebles"]
    cont = (
        '<div class="g3" style="grid-template-columns:450px 1fr 500px">'
        '<div class="col">'
        + bloque_r("qué hace", "<p>Ningún LLM: una <strong>plantilla</strong> que se completa con la lista (la línea "
                   "Type de cada producto, su medida o «size unknown», y cuántas unidades) y el pedido.</p>"
                   '<p class="nota">gratis · instantáneo</p>')
        + xref("E13p", f"<b>Edición estricta y sin LLM:</b> con nueve productos, la libre cambió el cuarto (SSIM "
               f"{f(mb, 2)}); la estricta lo preservó ({f(ms, 2)}).")
        + f'</div><div class="col" data-desde="1">{prs}</div><div class="col">{rev}</div></div>')
    fase(8, "Escena: <em>el prompt de la imagen, sin LLM</em>", cont, t=40,
         rem="Menos libertad, más fidelidad: <mark>el mismo cuarto, exactamente</mark>.", rem_desde=2,
         notas=[
             "La escena, el prompt del modelo de imagen. Al principio lo escribía Claude; hoy es una plantilla "
             "que se completa con la lista, sin LLM. Lo decidió el experimento 13.",
             "[paso] El que se mandó para el living: es la foto del cliente y tiene que quedar el mismo cuarto, "
             "exactamente. Una línea por producto, con su medida o «size unknown». Y solo esos productos.",
             "[paso] Con LLM, la v2 anclaba cada lugar a algo visible. Sin LLM, la v4 se volvió estricta cuando, "
             "con nueve productos, apareció una ventana que no existía.",
         ])

    # ================================================================ 9 · imagen
    from laminas_r import resumen as resumen_replica  # noqa: PLC0415

    rp = resumen_replica()
    ins = f'<div class="ins"><div class="in0"><img src="{img.uri(CL / "room.jpg", 600, 450, q=72)}" alt=""><span>1</span></div><div class="ing">'
    for i, c in enumerate(choices):
        ins += f'<div class="in1"><img src="{img.uri(foto_producto(D, c["id"]), 150, 150, fit="contain")}" alt=""><span>{i + 2}</span></div>'
    ins += "</div></div>"
    a1 = gen["attempts"][0]
    cont = (
        '<div class="g2" style="grid-template-columns:560px 1fr">'
        '<div class="col">'
        + bloque_r("qué hace", f"<p><strong>Nano Banana 2</strong> (Gemini 3.1 Flash Image), por fal, en modo edición: "
                   f"recibe la foto del cuarto, una foto por producto y el prompt, y devuelve la foto amoblada.</p>"
                   f'<p class="nota">{nb["resolution"]} · la proporción de la foto · {usd(D["img_precio"])} por imagen · '
                   f'{f(gen["meta"]["latency_s"], 0)} s</p>')
        + xref("E14", f"<b>Réplica de un living real:</b> sin decirle dónde, {f(rp['sin'], 0)} de {rp['n']} muebles en su "
               f"lugar; con cajas 3D en la foto, {f(rp['cajas3d'], 0)}. Una prueba: el flujo no cambió.", tipo="prueba")
        + xref("T4", "Qué modelo y qué resolución: diseñado, sin correr.", tipo="pend")
        + '</div><div class="io9">'
        + f'<div><div class="etq">entra · {gen["meta"]["images_in"]} imágenes y el prompt</div>{ins}</div>'
        + f'<div class="sal" data-desde="1"><div class="etq">sale · intento 1</div><div class="foto" style="width:540px;height:405px">'
          f'<img src="{img.uri(CL / a1["image"], 1080, 810, q=74)}" alt=""></div></div>'
        + "</div></div>")
    fase(9, "Imagen: <em>Nano Banana 2 edita tu foto</em>", cont, t=20,
         rem="El modelo de imagen no elige nada: <mark>dibuja lo que eligió el RAG</mark>.", rem_desde=1,
         notas=[
             f"La imagen: Nano Banana 2, de Gemini, por fal, edita la foto con las de los {len(choices)} "
             f"productos y el prompt. {usd(D['img_precio'])} por imagen. Qué modelo usar está diseñado, sin correr.",
             "[paso] Devuelve esto. Los productos son los de la lista… pero miren el cuarto.",
         ])

    # ================================================================ 10 · control
    tiles = (f'<figure class="at"><div class="ai"><img src="{img.uri(CL / "room.jpg", 600, 450, q=72)}" alt=""></div>'
             '<figcaption><b>la foto original</b></figcaption></figure>')
    for i, a in enumerate(gen["attempts"]):
        ok = a["ok"]
        tiles += (f'<figure class="at" data-desde="{1 if i < 2 else 2}"><div class="ai"><img src="{img.uri(CL / a["image"], 600, 450, q=72)}" alt="">'
                  f'<span class="sello{" ok" if ok else ""}">{"aceptada" if ok else "rechazada"}</span></div>'
                  f'<figcaption><b>intento {i + 1}</b><span>{a["sift_inliers"]} inliers · se movió {pct(a["sift_desplazamiento_mediano"], 1)}</span></figcaption></figure>')
    cont = (
        '<div class="g2" style="grid-template-columns:470px 1fr">'
        '<div class="col">'
        + bloque_r("qué hace", f"<p>Busca puntos <strong>SIFT</strong> de la foto original en la generada y ajusta una "
                   f"homografía con <strong>RANSAC</strong>. Pasa si quedan al menos <b>{D['sift_min_inliers']} inliers</b> "
                   f"y la cámara se movió a lo sumo un <b>{pct(D['sift_max_shift'])}</b> del ancho. Si no, otra imagen, "
                   f"hasta <b>{D['sift_attempts']}</b>.</p><p class=\"nota\">local · gratis · furnish/room.py</p>")
        + xref("E13", "El control quedó en el flujo; dónde poner el umbral exacto, pendiente (T4).")
        + f'</div><div class="col"><div class="atts r10">{tiles}</div>'
        + f'<p class="nota">{len(gen["attempts"])} intentos · {usd(gen["cost_usd"])} de imagen en esta corrida</p></div></div>')
    fase(10, "Control: <em>¿sigue siendo tu cuarto?</em>", cont, t=30,
         rem="Si el modelo cambió el cuarto, <mark>la imagen se descarta sola</mark> y se pide otra.", rem_desde=2,
         notas=[
             f"Por eso existe el control. Buscamos puntos característicos de la foto original en la generada, con "
             f"SIFT, y una homografía con RANSAC. Si se reencuentran al menos {D['sift_min_inliers']} y la cámara casi "
             f"no se movió, es el mismo cuarto.",
             f"[paso] Los dos primeros intentos de este living fallaron: {gen['attempts'][0]['sift_inliers']} y "
             f"{gen['attempts'][1]['sift_inliers']} inliers, con la cámara corrida más del 15%. Se rechazaron solos.",
             f"[paso] El tercero reencontró {gen['attempts'][2]['sift_inliers']} y se aceptó. Hasta "
             f"{D['sift_attempts']} intentos; el umbral exacto queda para el experimento pendiente.",
         ])

    # ================================================================ 11 · lista + imagen
    rows = ""
    for i, c in enumerate(choices):
        pid = c["id"]
        it = D["abo_items"][pid] if pid.startswith("abo-") else D["items"][pid]
        u = img.uri(foto_producto(D, pid), 96, 96, fit="contain")
        rows += (f'<div class="li"><img src="{u}" alt=""><span class="k">{esc(KIND_ES.get(it["kind"], it["kind"]))}</span>'
                 f'<code>{esc(pid)}</code><span class="m">{esc(medidas(D, pid))}</span><b>×{c.get("quantity", 1)}</b></div>')
    tot = plan_r["cost_usd"] + ch_r["cost_usd"] + gen["cost_usd"]
    cont = (
        '<div class="g2" style="grid-template-columns:1fr 560px">'
        f'<div class="col"><div class="etq">la lista · 3_choice.json</div><div class="lista">{rows}</div>'
        f'<p class="nota">esta corrida: plan {usd(plan_r["cost_usd"])} + elección {usd(ch_r["cost_usd"])} + '
        f'{len(gen["attempts"])} imágenes {usd(gen["cost_usd"])} = <b>{usd(tot)}</b></p>'
        + xref("E11", f"<b>¿La respuesta inventa?</b> El porqué de cada producto es fiel ({f(min(rag_f), 2)} a "
               f"{f(max(rag_f), 2)}) y responde al pedido ({f(min(rag_r), 2)} a {f(max(rag_r), 2)}).", tipo="prueba")
        + f'</div><div class="col" data-desde="1"><div class="etq">la imagen · intento {next(i for i, a in enumerate(gen["attempts"]) if a["ok"]) + 1}, aceptada</div>'
          f'<div class="foto" style="width:560px;height:420px"><img src="{img.uri(CL / "final.png", 1120, 840, q=76)}" alt=""></div></div>'
        + "</div>")
    fase(11, "La salida: <em>una lista que se puede comprar</em>", cont, t=20,
         rem="Productos reales, con su id y su cantidad, <mark>y tu cuarto con ellos</mark>.", rem_desde=1,
         notas=[
             f"Y la salida: la lista de compra, {len(choices)} productos con su id, su medida cuando la hay y la "
             f"cantidad, cada uno con su porqué. Esta corrida costó {usd(tot)}, por los tres intentos de imagen.",
             "[paso] Y la foto de tu cuarto con esos productos. Ese es el recorrido completo.",
         ])

    mapa(D)


# ---------------------------------------------------------------- el mapa de experimentos

def mapa(D: dict) -> None:
    b = D["best"]
    g = D["grad"]["consultas"]
    LL = [  # ambiente, experimento, tipo, título (líneas), lo que quedó
        (1, "E12", "si", ["qué", "catálogo"], "IKEA + ABO"),
        (2, "E1", "si", ["imagen", "o texto"], "texto"),
        (2, "E2", "si", ["qué texto"], "las 8 líneas"),
        (3, "E2", "si", ["embedder"], "Qwen3"),
        (3, "E3", "si", ["splitting"], "1 documento"),
        (3, "E4", "si", ["dimensión"], str(D["best_dim"])),
        (3, "E5", "si", ["base vectorial"], "ChromaDB"),
        (5, "E6", "si", ["reescribir", "la consulta"], "las 8 líneas"),
        (5, "E9", "prueba", ["otro", "redactor"], "se sostiene"),
        (6, "E2", "si", ["filtro"], "kind"),
        (6, "E10", "prueba", ["relevancia", "graduada"], f"{pct(g['todas']['util1'])} sirve"),
        (7, "E7", "si", ["reranking"], "un VLM"),
        (7, "E8", "si", ["candidatos"], f"k = {D['k_flujo']}"),
        (8, "E13p", "si", ["prompt", "de imagen"], "estricto"),
        (9, "E14", "prueba", ["réplica", "cajas 3D"], "a futuro"),
        (9, "T4", "pend", ["modelo", "de imagen"], "sin correr"),
        (10, "E13", "si", ["control"], f"SIFT, ≤ {D['sift_attempts']}"),
        (11, "E11", "prueba", ["RAGAS"], "porqué fiel"),
    ]
    H = planta.H
    y1, paso = H + 78, 84
    por = {}
    for row in LL:
        por.setdefault(row[0], []).append(row)
    ex = []
    pasos_por_amb = {1: 1, 2: 1, 3: 1, 5: 2, 6: 2, 7: 2, 8: 3, 9: 3, 10: 3, 11: 3}
    for n, rows in por.items():
        lx = planta.x0(n) + 27
        ys = [y1 + i * paso for i in range(len(rows))]
        g_ = f'<g data-desde="{pasos_por_amb[n]}">'
        g_ += f'<line class="guia" x1="{lx:.1f}" y1="{H:.1f}" x2="{lx:.1f}" y2="{ys[-1]:.1f}"/><circle class="guia-p" cx="{lx:.1f}" cy="{H:.1f}" r="4"/>'
        for (amb, e, tipo, tit, dec), cy in zip(rows, ys):
            g_ += planta.llamada(lx, cy, e.rstrip("p"), f"{{{{LAM:{e}}}}}", tipo, ir=f"{{{{IR:{e}}}}}")
            tx = lx + 29
            nl = len(tit)
            y0 = cy - (12 if nl == 2 else 3)
            for j, t_ in enumerate(tit):
                g_ += f'<text class="lt" x="{tx:.1f}" y="{y0 + j * 18:.1f}">{esc(t_)}</text>'
            g_ += f'<text class="ld {tipo}" x="{tx:.1f}" y="{y0 + nl * 18:.1f}">{esc(dec)}</text>'
        g_ += "</g>"
        ex.append(g_)
    bottom = y1 + 3 * paso + 40 - H
    svg = planta.tira(None, vistas=range(1, 12), extra="".join(ex), bottom_pad=bottom)
    ley = ('<div class="mley">'
           '<span><i class="c si"></i>decidió esa parte</span>'
           '<span><i class="c prueba"></i>la puso a prueba: el flujo no cambió</span>'
           '<span><i class="c pend"></i>diseñado, sin correr</span>'
           '<span class="r">arriba, el experimento · abajo, su lámina (clic para ir)</span></div>')
    body = ('<div class="cuerpo">' + cab("01", "El recorrido · el mapa de la charla", "Cada ambiente, <em>con el experimento que lo decidió</em>") + "</div>"
            + f'<div class="rtira mapa">{svg}</div>' + ley
            + remate("Lo que sigue son esos detalles: <mark>cada llamada es una lámina</mark>.", desde=3))
    add(body, titulo="El mapa de experimentos", cap=1, t=40, cls="lam-rec lam-mapa", notas=[
        "El mapa de lo que sigue: la misma planta, con una llamada de detalle por experimento; arriba el "
        "experimento, abajo su lámina.",
        "[paso] En el indexing: qué catálogo, texto o imagen, qué texto, y cuatro decisiones del índice.",
        "[paso] En cada pedido: reescribir la consulta, el filtro, el reranking y cuántos candidatos. Las "
        "punteadas son pruebas que no cambiaron el flujo.",
        "[paso] Y la imagen: el prompt estricto y el control; la réplica, una prueba; el modelo de imagen, sin "
        "correr. Vamos a los detalles.",
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

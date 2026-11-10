#!/usr/bin/env python
"""Arma presentacion.html y guion.md de amoblai (TP 3, 73.69 LLM, ITBA 2026).

Todos los números salen de los archivos de resultados (datos/resultados/...), del catálogo y de
la config: nada se escribe a mano. Las fotos van embebidas como JPEG en base64; las fuentes,
recortadas a Latin-1 y embebidas como woff2 (funciona sin conexión).

    cd /home/fer/tp-llm && uv run python docs/presentaciones_nuevas/b_mismo_contenido/build.py

Identidad visual: «plano y muestrario». Papel de yeso, tinta nogal, acentos de roble, terracota y
salvia; títulos en una serif de revista de interiores; cotas de arquitectura como ejes; el
índice de la charla es el plano de un departamento que se recorre ambiente por ambiente; en cada
experimento, el panel de resultados es un ambiente vacío que se «amuebla» recién después de
contar el porqué y el experimento.
"""

from __future__ import annotations

import base64
import collections
import gzip
import html
import io
import json
import re
import statistics
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
TRAB = OUT / "_trabajo"
D_ = ROOT / "datos"
RES = D_ / "resultados"
EV = RES / "evaluacion"
AM = RES / "amoblar"

TRAB.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------------------------
# Formato de números (coma decimal, como se dice)
# ---------------------------------------------------------------------------------------------

def f2(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def f3(x: float) -> str:
    return f"{x:.3f}".replace(".", ",")


def pct(x: float) -> str:
    return f"{round(x * 100)}%"


def usd(x: float, nd: int = 2) -> str:
    return "US$" + f"{x:.{nd}f}".replace(".", ",")


def mmss(seg: int) -> str:
    return f"{seg // 60}:{seg % 60:02d}"


def esc(s: str) -> str:
    return html.escape(s, quote=False)


# ---------------------------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------------------------

def jload(p: Path):
    return json.loads(p.read_text())


def metricas(run: str) -> dict:
    return jload(EV / run / "metricas.json")


def corrida(run: str) -> dict:
    return jload(EV / run / "corrida.json")


F = metricas("20261110-003643_ablacion-retrieval")          # catálogo final, todas las ablaciones
RR = metricas("20261109-235522_ablacion-reranking")         # reranking con Opus
C855 = metricas("20261023-173217_ablacion-retrieval")       # catálogo de 855
CREV = metricas("20261109-235406_ablacion-catalogo-revisado")
CTOD = metricas("20261110-010145_ablacion-catalogo-todos")
C268 = metricas("20261021-161057_ablacion-retrieval")       # catálogo de 268
TXT = metricas("20261021-133226_ablacion-texto")            # v1 contra v0, mismas fotos
REP2 = metricas("20261023-200437_reproducibilidad-r2")
REP3 = metricas("20261023-202248_reproducibilidad-r3")
CURVA = jload(RES / "evaluacion_candidatos" / "curva_k.json")
GRAD = jload(RES / "evaluacion_graduada" / "graduada.json")
ESP = jload(RES / "evaluacion_espacio" / "espacio.json")
J_ABO5 = jload(RES / "punta_a_punta" / "catalogos" / "juez_ikea_vs_abo_5ambientes.json")
J_TOD5 = jload(RES / "punta_a_punta" / "catalogos" / "juez_ikea_vs_todos_5ambientes.json")
J_TOD = jload(RES / "punta_a_punta" / "catalogos" / "juez_ikea_vs_todos.json")
V0 = jload(next((RES / "v0_imagen" / "corridas").glob("*retriever_abl-retriever-name-dinov3__method-none__category_filter-true")) / "metrics.json")
GRAD_RUN = metricas(GRAD["run"])

BASE = "qwen3|description|filtro-type"


def m(run: dict, key: str, met: str = "hit@1") -> float:
    return run[key][met]


def ic(run: dict, key: str, met: str = "hit@1"):
    return run[key].get(met + "_ic95")


ITEMS = {}
for line in (D_ / "procesados" / "items.jsonl").read_text().splitlines():
    it = json.loads(line)
    ITEMS[it["id"]] = it
DESCR = {}
for line in (D_ / "catalogo" / "descripciones.jsonl").read_text().splitlines():
    it = json.loads(line)
    DESCR[it["id"]] = it["text"]
ABO_DESCR = [json.loads(x) for x in (D_ / "catalogo" / "abo" / "descripciones.jsonl").read_text().splitlines()]

CATS = yaml.safe_load((D_ / "configs" / "categories.yaml").read_text())["categories"]
CFG = yaml.safe_load((D_ / "configs" / "amoblai.yaml").read_text())
try:
    from amoblai.config import FurnishConfig
    ROOM_CHECK = FurnishConfig().room_check
except Exception:  # sin el paquete: se lee del código fuente
    src = (ROOT / "src" / "amoblai" / "config.py").read_text()
    mm = re.search(r'"attempts": (\d+), "min_inliers": (\d+), "max_shift": ([\d.]+)', src)
    ROOM_CHECK = {"attempts": int(mm[1]), "min_inliers": int(mm[2]), "max_shift": float(mm[3])}

PEDIDOS = yaml.safe_load((D_ / "ambientes_vacios" / "pedidos.yaml").read_text())["ambientes"]
PUBLICAS = yaml.safe_load((D_ / "ambientes_vacios" / "publicas.yaml").read_text())["fotos"]
PUB_POR_ARCHIVO = {p["archivo"]: p for p in PUBLICAS}

GASTOS = [json.loads(x) for x in (RES / "gastos.jsonl").read_text().splitlines() if x.strip()]


def gasto(step: str, model: str | None = None):
    xs = [g["cost_usd"] for g in GASTOS if g["step"] == step and (model is None or g.get("model") == model) and not g.get("cached")]
    return xs


def corrida_idx(run: str) -> dict:
    return corrida(run).get("index", {})


# --- números que se dicen ---------------------------------------------------------------------
D = {}
D["n_busquedas"] = F[BASE]["searches"]
D["n_respondibles"] = F[BASE]["answerable"]
D["n_ambientes_gt"] = corrida("20261110-003643_ablacion-retrieval")["rooms"]
D["prod_268"] = corrida_idx("20261021-161057_ablacion-retrieval")["products"]
D["prod_855"] = corrida_idx("20261023-173217_ablacion-retrieval")["products"]
D["prod_819"] = corrida_idx("20261110-003643_ablacion-retrieval")["products"]
D["prod_todos"] = corrida_idx("20261110-010145_ablacion-catalogo-todos")["products"]
assert D["prod_819"] == len(ITEMS)
D["n_abo"] = sum(1 for x in ABO_DESCR if "(API)" in x.get("by", ""))
D["n_tipos"] = len(CATS)
D["n_kinds"] = len({it["kind"] for it in ITEMS.values()})

# Revisión del catálogo ampliado: lo que está después del comentario de la revisión.
_corr_txt = (D_ / "catalogo" / "correcciones.yaml").read_text()
_rev = _corr_txt.split("# Revisión del catálogo ampliado", 1)[1].split("\n", 1)[1]
_rev_entries = yaml.safe_load(_rev) or {}
D["rev_afuera"] = sum(1 for v in _rev_entries.values() if v.get("excluir"))
D["rev_kinds"] = sum(1 for v in _rev_entries.values() if "kind" in v)
assert D["prod_855"] - D["rev_afuera"] == D["prod_819"]

_seats = [it for it in ITEMS.values() if it["category_tp"] in ("sofa", "armchair", "chair", "stool", "bench", "ottoman")]
D["asientos"] = len(_seats)
D["asientos_sin_medida"] = sum(1 for it in _seats if not it["dimensions_cm"])
_fotos_lado = collections.Counter(Image.open(ROOT / it["photos"][0]).size for it in list(ITEMS.values())[:60])
D["foto_lado"] = _fotos_lado.most_common(1)[0][0][0]
_wc = sorted(len(DESCR[i].split()) for i in ITEMS)
D["palabras_lo"] = (_wc[len(_wc) // 20] // 10) * 10
D["palabras_hi"] = -(-_wc[-(len(_wc) // 20)] // 10) * 10

D["n_ambientes_vacios"] = len(PEDIDOS)
D["n_publicos"] = sum(1 for p in PEDIDOS if p["slug"].startswith("publica"))
D["n_propios"] = D["n_ambientes_vacios"] - D["n_publicos"]
D["n_publicas_revisadas"] = len(PUBLICAS)

D["v0_hit1"] = V0["retrieval"]["hit@1"]
D["v0_n"] = V0["retrieval"]["n"]
D["v1_hit1"] = m(TXT, BASE)
D["v1_n"] = TXT[BASE]["answerable"]

D["k_flujo"] = CFG["furnish"]["candidates"]

# experimento 1
D["e1_vendedor"] = m(F, "qwen3|seller|filtro-type")
D["e1_desc"] = m(F, BASE)
D["e1_desc_kind"] = m(F, "qwen3|description|filtro-kind")
D["e1_nombre_kind"] = m(F, "qwen3|name+description|filtro-kind")
D["e1_veces"] = D["e1_desc"] / D["e1_vendedor"]
# experimento 2
D["e2"] = {e: (m(F, f"{e}|description|filtro-type"), m(F, f"{e}|description|filtro-type", "mrr@10")) for e in ("hashing", "bge", "qwen3")}
# experimento 3
D["e3"] = {f: (m(F, f"qwen3|description|filtro-{f}"), m(F, f"qwen3|description|filtro-{f}", "hit@10")) for f in ("none", "type", "kind")}
# experimento 4
D["e4"] = {"whole": m(F, BASE), "aligned": m(F, BASE + "|chunks-lines-aligned"), "max": m(F, BASE + "|chunks-lines-max")}
# experimento 5
D["e5"] = [(d, m(F, BASE + f"|dim-{d}"), ic(F, BASE + f"|dim-{d}")) for d in (32, 64, 128, 256, 512)] + [(1024, m(F, BASE), ic(F, BASE))]
# experimento 6
D["e6_exacta"] = m(F, BASE + "|exact")
D["e6_hnsw"] = m(F, BASE)
D["e6_type"] = m(F, BASE + "|consulta-type")
D["e6_kind"] = m(F, BASE + "|consulta-kind")
# experimento 7
D["e7_base"] = (m(RR, BASE), m(RR, BASE, "mrr@10"), m(RR, BASE, "hit@10"))
D["e7_minilm"] = (m(F, BASE + "|rerank-minilm-reranker"), m(F, BASE + "|rerank-minilm-reranker", "mrr@10"))
D["e7_opus"] = (m(RR, BASE + "|rerank-opus"), m(RR, BASE + "|rerank-opus", "mrr@10"))
D["e7_costo"] = statistics.mean(gasto("eval.rerank", "claude-opus-5-5"))
# experimento 8
D["curva"] = {int(k): v for k, v in CURVA["por_k"].items()}
D["e8_falta3"] = 1 - D["curva"][3]["techo_hit@k"]
# experimento 9
D["e9"] = [(D["prod_268"], m(C268, BASE), C268[BASE]["searches"]), (D["prod_855"], m(C855, BASE), C855[BASE]["searches"]), (D["prod_819"], m(CREV, BASE), CREV[BASE]["searches"])]
# experimento 10


def resumen_juez(j: dict, filtro=None):
    rows = [r for r in j["detalle"] if filtro is None or filtro(r["slug"])]
    a, b = j["a"], j["b"]
    gana_a = sum(1 for r in rows if r["ganador"] == a)
    gana_b = sum(1 for r in rows if r["ganador"] == b)
    emp = sum(1 for r in rows if r["ganador"] not in (a, b))

    def util(side):
        n = t = 0
        for r in rows:
            for p in r["puntajes"][side]:
                n += len(p["grades"])
                t += sum(1 for g in p["grades"] if g == 2)
        return t / n
    return {"n": len(rows), "a": gana_a, "b": gana_b, "emp": emp, "util_a": util(a), "util_b": util(b), "rows": rows}


es_pub = lambda s: s.startswith("publica")  # noqa: E731
D["j_abo5"] = resumen_juez(J_ABO5)
D["j_tod5"] = resumen_juez(J_TOD5)
D["j_nord"] = resumen_juez(J_TOD, lambda s: not es_pub(s))
D["j_otros"] = resumen_juez(J_TOD, es_pub)
D["j_todos"] = resumen_juez(J_TOD)
D["j_acuerdo"] = J_TOD["acuerdo_entre_ordenes"]
D["j_acuerdo5"] = J_ABO5["acuerdo_entre_ordenes"]
D["e10_gt_ikea"] = m(F, BASE)
D["e10_gt_todos"] = m(CTOD, BASE)
# experimento 11
D["g_n"] = GRAD["consultas"]["todas"]["n"]
D["g_anot2"] = GRAD["acuerdo_con_gt"]["anotado_con_2"]
D["g_otros2"] = GRAD["acuerdo_con_gt"]["otros_con_2"]
D["g_util1"] = GRAD["consultas"]["todas"]["util1"]
D["g_util1_ic"] = GRAD["consultas"]["todas"]["util1_ic95"]
D["g_hit1"] = m(GRAD_RUN, GRAD["method"])
D["g_hit1_ic"] = ic(GRAD_RUN, GRAD["method"])
D["rep"] = [m(C855, BASE), m(REP2, BASE), m(REP3, BASE)]
D["rep_sd"] = statistics.stdev(D["rep"])
# experimento 12


def img_metrics(run):
    return jload(AM / run / "6_metricas_imagen.json")


D["e12"] = {}
D["e12_piezas"] = {r: len(jload(AM / r / "3_choice.json")["answer"]["choices"]) for r in ("experimento", "experimento-libre", "experimento-buen-pedido", "experimento-buen-pedido-estricto")}
for r in ("experimento", "experimento-libre", "experimento-buen-pedido", "experimento-buen-pedido-estricto"):
    mi = img_metrics(r)["ambiente"]
    D["e12"][r] = (mi["sift_inliers"], mi["ssim_fuera_de_los_muebles"])
# punta a punta
D["cab_liv"] = jload(AM / "caballito-living" / "5_image.json")
D["cab_com"] = jload(AM / "caballito-comedor" / "5_image.json")
# costos


def costo_pedido(carpeta: Path) -> float:
    t = 0.0
    for f in ("1_searches.json", "3_choice.json"):
        p = carpeta / f
        if p.exists():
            t += jload(p).get("cost_usd") or 0
    return t


_cp = [costo_pedido(p) for p in sorted((RES / "punta_a_punta" / "catalogos" / "todos").iterdir()) if p.is_dir()]
D["costo_claude"] = statistics.mean(_cp)
D["costo_imagen"] = CFG["furnish"]["generators"]["nano_banana_2"]["usd_per_image"]["1K"]
D["costo_describir"] = sum(gasto("catalog.describe")) / D["n_abo"]
# camino
D["camino"] = [
    ("Texto del vendedor + bolsa de palabras", m(F, "hashing|seller|filtro-none")),
    ("+ descripción del VLM", m(F, "hashing|description|filtro-none")),
    ("+ Qwen3-Embedding", m(F, "qwen3|description|filtro-none")),
    ("+ filtro por tipo", m(F, BASE)),
    ("+ un VLM reordena el top-10", m(RR, BASE + "|rerank-opus")),
]

# ---------------------------------------------------------------------------------------------
# Fuentes embebidas (subset Latin-1 → woff2, en caché en _trabajo/fuentes)
# ---------------------------------------------------------------------------------------------

UNICODES = (
    list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)) + [0x152, 0x153, 0x2009, 0x200A, 0x202F]
    + list(range(0x2010, 0x2028)) + list(range(0x2030, 0x203B)) + [0x2190, 0x2191, 0x2192, 0x2193, 0x2212, 0x2248, 0x2260, 0x2264, 0x2265, 0x221A]
)
FUENTES = [
    ("Vitrina", "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Regular.ttf", 400, "normal"),
    ("Vitrina", "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Italic.ttf", 400, "italic"),
    ("Ficha", "/usr/share/fonts/opentype/cabin/Cabin-Regular.otf", 400, "normal"),
    ("Ficha", "/usr/share/fonts/opentype/cabin/Cabin-Italic.otf", 400, "italic"),
    ("Ficha", "/usr/share/fonts/opentype/cabin/Cabin-SemiBold.otf", 600, "normal"),
    ("Ficha", "/usr/share/fonts/opentype/cabin/Cabin-Bold.otf", 700, "normal"),
    ("Cota", "/usr/share/fonts/fonts-go/Go-Mono.ttf", 400, "normal"),
]


def css_fuentes() -> str:
    out = []
    cache = TRAB / "fuentes"
    cache.mkdir(exist_ok=True)
    for fam, path, w, st in FUENTES:
        dst = cache / (Path(path).stem + ".woff2")
        if not dst.exists():
            from fontTools import subset
            opts = subset.Options()
            opts.flavor = "woff2"
            opts.layout_features = ["kern", "liga", "lnum", "tnum", "pnum", "case"]
            opts.name_IDs = ["*"]
            opts.notdef_outline = True
            font = subset.load_font(path, opts)
            sub = subset.Subsetter(opts)
            sub.populate(unicodes=UNICODES)
            sub.subset(font)
            subset.save_font(font, str(dst), opts)
        b = base64.b64encode(dst.read_bytes()).decode()
        out.append(f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:{st};font-display:block;src:url(data:font/woff2;base64,{b}) format('woff2')}}")
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------
# Imágenes embebidas: cada una una sola vez, como clase CSS con background-image
# ---------------------------------------------------------------------------------------------

class Imagenes:
    def __init__(self):
        self.css: dict[str, str] = {}
        self.bytes = 0

    def reg(self, clave: str, src, w: int, h: int | None = None, modo: str = "cover", q: int = 80,
            recorte=None, fondo=(255, 255, 255)) -> str:
        cls = "im-" + re.sub(r"[^a-z0-9]+", "-", clave.lower()).strip("-")
        if cls in self.css:
            return cls
        im = src if isinstance(src, Image.Image) else Image.open(ROOT / src if not str(src).startswith("/") else src)
        im = im.convert("RGB")
        if recorte:
            im = im.crop(recorte)
        if modo == "cover" and h:
            sw, sh = im.size
            r = max(w / sw, h / sh)
            im = im.resize((round(sw * r), round(sh * r)), Image.LANCZOS)
            x0 = (im.width - w) // 2
            y0 = (im.height - h) // 2
            im = im.crop((x0, y0, x0 + w, y0 + h))
        else:
            im.thumbnail((w, h or w), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        b = buf.getvalue()
        self.bytes += len(b)
        self.css[cls] = f".{cls}{{background-image:url(data:image/jpeg;base64,{base64.b64encode(b).decode()})}}"
        return cls

    def style(self) -> str:
        return "\n".join(self.css.values())


IM = Imagenes()


def foto(clave, src, w, h, extra="", estilo="", q=80, recorte=None, enc_w=None, enc_h=None, modo="cover"):
    """Un div del tamaño w×h con la foto recortada a ese tamaño (enc_*: resolución codificada)."""
    cls = IM.reg(clave, src, enc_w or w, enc_h or h, modo=modo, q=q, recorte=recorte)
    return f'<div class="foto {cls} {extra}" style="width:{w}px;height:{h}px;{estilo}"></div>'


def producto(pid: str, w: int, extra="", estilo="", fondo_papel=True) -> str:
    path = ITEMS[pid]["photos"][0] if pid in ITEMS else None
    if path is None:
        return ""
    cls = IM.reg("p-" + pid, path, min(320, w * 1), None, modo="fit", q=78)
    return f'<div class="prod {cls} {extra}" style="width:{w}px;height:{w}px;{estilo}"></div>'


def producto_path(pid: str, path: str, w: int, extra="", estilo="") -> str:
    cls = IM.reg("p-" + pid, path, min(320, w), None, modo="fit", q=78)
    return f'<div class="prod {cls} {extra}" style="width:{w}px;height:{w}px;{estilo}"></div>'


KIND_ES = {
    "bookcase": "Biblioteca", "armchair": "Sillón", "floor lamp": "Lámpara de pie", "side table": "Mesita",
    "rug": "Alfombra", "throw": "Manta", "cushion": "Almohadón", "curtains": "Cortinas", "plant": "Planta",
    "coffee table": "Mesa ratona", "sofa": "Sofá", "pendant lamp": "Lámpara colgante", "TV stand": "Mueble de TV",
    "dining table": "Mesa de comedor", "dining chair": "Silla", "sideboard": "Aparador", "desk lamp": "Lámpara de escritorio",
    "display cabinet": "Vitrina", "console table": "Mesa consola", "picture frame": "Marco",
}


def medida(dim) -> str:
    if not dim:
        return ""
    w, dd = dim.get("width"), dim.get("depth")
    if w and dd:
        return f"{w:g} × {dd:g} cm"
    if w:
        return f"{w:g} cm de ancho"
    return ""


# ---------------------------------------------------------------------------------------------
# Gráficos en SVG
# ---------------------------------------------------------------------------------------------

C_ELEGIDO = "#A94E2B"
C_OTRO = "#CDBEA8"
C_TINTA = "#2A211B"
C_TINTA2 = "#5E5148"
C_TINTA3 = "#8C7E71"
C_HILO = "#D8CDBD"
C_ROBLE = "#B4864F"


def chip(letra: str, oscuro=False) -> str:
    return f'<span class="chip{" oscuro" if oscuro else ""}">{letra}</span>'


def barras(filas, ancho=1000, xmax=1.0, et_w=330, alto=36, sep=16, fmt=f2, ticks=(0, 0.25, 0.5, 0.75, 1.0),
           titulo=None, eje=True, val_w=120) -> str:
    """Barras horizontales con IC; el eje es una cota de arquitectura (trazo con marcas a 45°).

    filas: dicts con et, sub (opcional), v, ic (opcional), tono ('elegido'|'otro'), letra, anot.
    """
    x0 = et_w
    W = ancho - et_w - val_w
    top = 50 if eje else 8
    if titulo:
        top += 36
    h = top + len(filas) * (alto + sep) - sep + 10
    sx = lambda v: x0 + W * v / xmax  # noqa: E731
    out = [f'<svg class="graf" viewBox="0 0 {ancho} {h}" width="{ancho}" height="{h}">']
    if titulo:
        out.append(f'<text x="0" y="26" class="g-tit">{titulo}</text>')
    if eje:
        ye = top - 20
        out.append(f'<line x1="{sx(0)}" y1="{ye}" x2="{sx(xmax)}" y2="{ye}" class="g-cota"/>')
        for t in ticks:
            x = sx(t)
            out.append(f'<line x1="{x - 6}" y1="{ye + 6}" x2="{x + 6}" y2="{ye - 6}" class="g-cota-t"/>')
            out.append(f'<text x="{x}" y="{ye - 12}" class="g-eje" text-anchor="middle">{fmt(t) if t not in (0, 1) else int(t)}</text>')
            out.append(f'<line x1="{x}" y1="{ye + 10}" x2="{x}" y2="{h}" class="g-grilla"/>')
    for i, f in enumerate(filas):
        y = top + i * (alto + sep)
        cy = y + alto / 2
        tono = C_ELEGIDO if f.get("tono") == "elegido" else C_OTRO
        if f.get("letra"):
            out.append(f'<rect x="0" y="{cy - 15}" width="30" height="30" class="g-chip"/><text x="15" y="{cy + 6}" class="g-chip-t" text-anchor="middle">{f["letra"]}</text>')
            tx = 44
        else:
            tx = 0
        if f.get("sub"):
            out.append(f'<text x="{tx}" y="{cy - 4}" class="g-et">{f["et"]}</text><text x="{tx}" y="{cy + 21}" class="g-sub">{f["sub"]}</text>')
        else:
            out.append(f'<text x="{tx}" y="{cy + 8}" class="g-et">{f["et"]}</text>')
        out.append(f'<rect x="{sx(0)}" y="{y}" width="{max(2, sx(f["v"]) - sx(0))}" height="{alto}" fill="{tono}" rx="2"/>')
        xr = sx(f["v"])
        if f.get("ic"):
            lo, hi = f["ic"]
            out.append(f'<line x1="{sx(lo)}" y1="{cy}" x2="{sx(hi)}" y2="{cy}" class="g-ic"/>')
            out.append(f'<line x1="{sx(lo)}" y1="{cy - 9}" x2="{sx(lo)}" y2="{cy + 9}" class="g-ic"/>')
            out.append(f'<line x1="{sx(hi)}" y1="{cy - 9}" x2="{sx(hi)}" y2="{cy + 9}" class="g-ic"/>')
            xr = max(xr, sx(hi))
        cls = "g-val elegido" if f.get("tono") == "elegido" else "g-val"
        out.append(f'<text x="{xr + 14}" y="{cy + 9}" class="{cls}">{f.get("vtxt", fmt(f["v"]))}</text>')
        if f.get("anot"):
            out.append(f'<text x="{xr + 14 + 16 * len(f.get("vtxt", fmt(f["v"])))}" y="{cy + 8}" class="g-anot">{f["anot"]}</text>')
    out.append("</svg>")
    return "".join(out)


def lineas(xs, series, ancho, alto, ymin, ymax, yticks, xlab=None, xfmt=str, ml=70, mr=30, mt=30, mb=96,
           marcas=(), banda=None, logx=False, notas=()):
    """series: dicts con ys, clase ('sol'|'punt'), et (rótulo al final)."""
    import math
    W = ancho - ml - mr
    H = alto - mt - mb
    if logx:
        lx = [math.log2(x) for x in xs]
    else:
        lx = list(xs)
    x_min, x_max = min(lx), max(lx)
    sx = lambda v: ml + W * ((math.log2(v) if logx else v) - x_min) / (x_max - x_min)  # noqa: E731
    sy = lambda v: mt + H * (1 - (v - ymin) / (ymax - ymin))  # noqa: E731
    out = [f'<svg class="graf" viewBox="0 0 {ancho} {alto}" width="{ancho}" height="{alto}">']
    for t in yticks:
        out.append(f'<line x1="{ml}" y1="{sy(t)}" x2="{ml + W}" y2="{sy(t)}" class="g-grilla"/>')
        out.append(f'<text x="{ml - 14}" y="{sy(t) + 6}" class="g-eje" text-anchor="end">{f2(t)}</text>')
    # eje x como cota
    yb = mt + H + 22
    out.append(f'<line x1="{sx(xs[0])}" y1="{yb}" x2="{sx(xs[-1])}" y2="{yb}" class="g-cota"/>')
    for x in xs:
        out.append(f'<line x1="{sx(x) - 6}" y1="{yb + 6}" x2="{sx(x) + 6}" y2="{yb - 6}" class="g-cota-t"/>')
        out.append(f'<text x="{sx(x)}" y="{yb + 34}" class="g-eje" text-anchor="middle">{xfmt(x)}</text>')
    if xlab:
        out.append(f'<text x="{ml + W}" y="{yb + 66}" class="g-sub" text-anchor="end">{xlab}</text>')
    if banda:
        lo, hi = banda
        pts = [f"{sx(x)},{sy(v)}" for x, v in zip(xs, hi)] + [f"{sx(x)},{sy(v)}" for x, v in reversed(list(zip(xs, lo)))]
        out.append(f'<polygon points="{" ".join(pts)}" class="g-banda"/>')
    for s in series:
        pts = " ".join(f"{sx(x)},{sy(v)}" for x, v in zip(xs, s["ys"]))
        out.append(f'<polyline points="{pts}" class="g-linea {s.get("clase", "sol")}"/>')
        for x, v in zip(xs, s["ys"]):
            if s.get("puntos", True):
                out.append(f'<circle cx="{sx(x)}" cy="{sy(v)}" r="{5 if s.get("clase") != "punt" else 4}" class="g-punto {s.get("clase", "sol")}"/>')
        if s.get("et"):
            dy = s.get("et_dy", 0)
            out.append(f'<text x="{sx(xs[-1]) + 14}" y="{sy(s["ys"][-1]) + 7 + dy}" class="g-et-serie {s.get("clase", "sol")}">{s["et"]}</text>')
    for mk in marcas:  # (x, y, texto, dx, dy, ancla, clase)
        x, v, t, dx, dy, anc, cl = mk
        out.append(f'<circle cx="{sx(x)}" cy="{sy(v)}" r="9" class="g-marca {cl}"/>')
        out.append(f'<text x="{sx(x) + dx}" y="{sy(v) + dy}" class="g-marca-t {cl}" text-anchor="{anc}">{t}</text>')
    for nt in notas:
        out.append(nt(sx, sy))
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------------------------------------
# Piezas de las slides
# ---------------------------------------------------------------------------------------------

SLIDES: list[dict] = []


def slide(id_, titulo_corto, seccion, cuerpo, notas, seg, clase="", riel=None, guion_partes=None, sub_guion=""):
    SLIDES.append(dict(id=id_, titulo=titulo_corto, seccion=seccion, html=cuerpo, notas=notas, seg=seg, clase=clase,
                       riel=riel, partes=guion_partes, sub=sub_guion))


def cab(kicker: str, titulo: str, sub: str = "") -> str:
    s = f'<div class="kicker">{kicker}</div><h2 class="titulo">{titulo}</h2>'
    if sub:
        s += f'<p class="bajada">{sub}</p>'
    return f'<header class="cab">{s}</header>'


# --- el plano del departamento (índice de la charla) --------------------------------------------

PARTES = ["Datos", "Arquitectura", "Métricas", "Experimentos", "Cierre"]


def plano(actual: int) -> str:
    """Planta de un departamento de cinco ambientes; `actual` (1..5) es el que se recorre."""
    def hab(n, x, y, w, h, muebles, lx, ly):
        on = " on" if n == actual else (" hecho" if n < actual else "")
        return (f'<g class="hab{on}"><rect x="{x}" y="{y}" width="{w}" height="{h}" class="piso"/>'
                f'<g class="muebles">{muebles}</g>'
                f'<text x="{lx}" y="{ly}" class="hab-n">{n}</text><text x="{lx + 30}" y="{ly}" class="hab-t">{PARTES[n - 1]}</text></g>')

    # muebles en planta (trazo fino)
    estante = '<rect x="70" y="64" width="300" height="34"/>' + "".join(f'<line x1="{70 + i * 30}" y1="64" x2="{70 + i * 30}" y2="98"/>' for i in range(1, 10))
    sillon_d = '<rect x="250" y="170" width="80" height="80" rx="8"/><rect x="250" y="170" width="80" height="20" rx="6"/><circle cx="200" cy="215" r="18"/>'
    mesa_a = '<rect x="520" y="130" width="320" height="100" rx="4"/>' + "".join(
        f'<rect x="{545 + i * 75}" y="100" width="44" height="26" rx="5"/><rect x="{545 + i * 75}" y="234" width="44" height="26" rx="5"/>' for i in range(4))
    lampara_a = '<circle cx="900" cy="90" r="20"/><line x1="886" y1="76" x2="914" y2="104"/><line x1="914" y1="76" x2="886" y2="104"/>'
    escritorio = '<rect x="62" y="380" width="70" height="200" rx="3"/><circle cx="170" cy="470" r="24"/><circle cx="270" cy="660" r="16"/><line x1="258" y1="648" x2="282" y2="672"/><line x1="282" y1="648" x2="258" y2="672"/>'
    living = ('<rect x="380" y="380" width="300" height="230" rx="4" class="alfombra"/>'
              '<rect x="390" y="630" width="280" height="64" rx="10"/><rect x="390" y="660" width="280" height="34" rx="8"/>'
              '<rect x="470" y="470" width="120" height="70" rx="4"/>'
              '<rect x="355" y="430" width="64" height="64" rx="10"/><rect x="640" y="430" width="64" height="64" rx="10"/>')
    cierre = ('<circle cx="790" cy="400" r="26"/><path d="M790 374 L790 426 M764 400 L816 400 M772 382 L808 418 M808 382 L772 418"/>'
              '<circle cx="905" cy="660" r="22"/><path d="M905 638 L905 682 M883 660 L927 660"/>'
              '<rect x="760" y="520" width="170" height="60" rx="8"/>')
    g = [
        hab(1, 40, 40, 360, 290, estante + sillon_d, 70, 300),
        hab(2, 400, 40, 560, 290, mesa_a + lampara_a, 430, 300),
        hab(3, 40, 330, 290, 390, escritorio, 70, 700),
        hab(4, 330, 330, 400, 390, living, 360, 360 + 0),
        hab(5, 730, 330, 230, 390, cierre, 760, 700),
    ]
    # paredes con vanos de puertas; ventanas en el perímetro
    paredes = (
        '<path class="pared" d="M40 40 H960 V720 H40 Z"/>'
        '<path class="pared-int" d="M400 40 V200 M400 280 V330 M40 330 H160 M240 330 H610 M690 330 H800 M880 330 H960 M330 330 V480 M330 560 V720 M730 330 V420 M730 500 V720"/>'
        '<path class="puerta" d="M400 200 A80 80 0 0 1 480 280 M400 200 L400 280"/>'
        '<path class="puerta" d="M160 330 A80 80 0 0 0 240 410"/>'
        '<path class="puerta" d="M610 330 A80 80 0 0 0 690 410"/>'
        '<path class="puerta" d="M800 330 A80 80 0 0 0 880 410"/>'
        '<path class="puerta" d="M330 480 A80 80 0 0 1 410 560"/>'
        '<path class="puerta" d="M730 420 A80 80 0 0 1 810 500"/>'
        '<path class="ventana" d="M560 34 H780 M560 46 H780 M120 714 H260 M120 726 H260 M954 470 V640 M966 470 V640 M34 120 V260 M46 120 V260"/>'
    )
    # cota general del plano
    cota = ('<path class="cota" d="M40 760 H960 M34 766 L46 754 M954 766 L966 754"/>'
            '<text x="500" y="790" class="cota-t" text-anchor="middle">la charla, de un ambiente al otro</text>')
    return f'<svg class="plano" viewBox="0 0 1000 800">{"".join(g)}{paredes}{cota}</svg>'


def separador(n: int, desc: str, contenido: list[str], extra: str = "") -> str:
    items = "".join(f"<li>{esc(c)}</li>" for c in contenido)
    return (f'<div class="sep-txt"><div class="sep-parte">Parte {n} de {len(PARTES)}</div>'
            f'<h2 class="sep-titulo">{PARTES[n - 1]}</h2><p class="sep-desc">{desc}</p>'
            f'<ol class="sep-lista">{items}</ol>{extra}</div>'
            f'<div class="sep-plano">{plano(n)}</div>')


RIEL = ["Por qué", "El experimento", "Resultados", "Decisión"]


def riel_html() -> str:
    return '<ol class="riel">' + "".join(f'<li data-i="{i}"><b>{i + 1}</b>{t}</li>' for i, t in enumerate(RIEL)) + "</ol>"


def vacio_resultados() -> str:
    """El panel de resultados antes de mostrarlos: un ambiente vacío en planta."""
    return ('<div class="vacio" data-hasta="2"><svg viewBox="0 0 600 360" class="vacio-plano">'
            '<path d="M20 20 H580 V340 H20 Z" class="v-pared"/>'
            '<path d="M200 20 H360" class="v-vent"/><path d="M200 14 H360" class="v-vent"/>'
            '<path d="M20 240 A90 90 0 0 1 110 330" class="v-puerta"/>'
            '</svg><div class="vacio-t">Resultados</div><div class="vacio-s">se muestran después del porqué y el experimento</div></div>')


EXP_TOTAL = 12


def experimento(n: int, nombre: str, pregunta: str, porque: str, variantes, metrica: str, resultados: str,
                decision: str, guion: tuple[str, str, str, str], seg: int, porque_extra: str = "",
                riel_map=(0, 1, 2, 3), dec_paso: int = 3, clase_extra: str = "", exp_extra: str = ""):
    vs = "".join(f'<li>{chip(l)}<div><b>{esc(t)}</b><span>{d}</span></div></li>' for l, t, d in variantes)
    cuerpo = (
        f'<div class="exp-top"><div class="kicker">Experimento {n} de {EXP_TOTAL}</div>{riel_html()}</div>'
        f'<h2 class="titulo exp-tit">{nombre}</h2><p class="bajada exp-preg">{pregunta}</p>'
        f'<div class="exp-izq">'
        f'<section class="bloque"><h3 class="b-et">Por qué lo hicimos</h3><p class="b-txt">{porque}</p>{porque_extra}</section>'
        f'<section class="bloque" data-paso="1"><h3 class="b-et">El experimento</h3><ul class="variantes">{vs}</ul>'
        f'{exp_extra}<p class="metrica">{metrica}</p></section>'
        f'</div>'
        f'<div class="exp-der">{vacio_resultados()}{resultados}</div>'
        f'<div class="decision"><span class="d-et">Decisión</span><p class="d-txt" data-paso="{dec_paso}">{decision}</p></div>'
    )
    plano_nombre = re.sub(r'\s*<span[^>]*>(.*?)</span>', r' (\1)', nombre)
    slide(f"exp{n}", f"Exp. {n}: {plano_nombre}", f"Experimentos · {n}. {plano_nombre}", cuerpo,
          guion, seg, clase="exp " + clase_extra, riel=",".join(map(str, riel_map)), guion_partes=guion,
          sub_guion=f"Experimento {n}")


# =============================================================================================
# LAS SLIDES
# =============================================================================================

HERO = AM / "experimento-buen-pedido-estricto"
HERO_REQ = jload(HERO / "request.json")["request"]
HERO_CHOICE = jload(HERO / "3_choice.json")["answer"]["choices"]
HERO_CAND = jload(HERO / "2_candidates.json")["pieces"]
_cand_info = {}
for p in HERO_CAND:
    for c in p["candidates"]:
        _cand_info[c["id"]] = c
N_HERO = len(HERO_CHOICE)

# 1 · Portada ---------------------------------------------------------------------------------
cover_final = foto("hero-final-cover", HERO / "final.png", 1040, 1080, q=82)
cover_room = foto("hero-room-sm", HERO / "room.jpg", 330, 248, q=80)
slide("portada", "Portada", "", f'''
<div class="portada-foto">{cover_final}
  <figure class="inset">{cover_room}<figcaption>la foto que subiste</figcaption></figure>
  <div class="cota-foto"><span>{N_HERO} productos reales de catálogo, en tu ambiente</span></div>
</div>
<div class="portada-txt">
  <div class="kicker">73.69 Large Language Models · ITBA · 2026 · Trabajo práctico 3</div>
  <h1 class="marca">amoblai</h1>
  <p class="portada-preg">Tengo este ambiente vacío:<br><em>¿qué compro, y cómo queda?</em></p>
  <ul class="equipo"><li>Juan Bautista Albertoni Salini</li><li>Matias Juan Rossi Seifert</li><li>Junior Rambau</li></ul>
</div>''',
      "Somos Juan Bautista, Matías y Junior. amoblai responde una pregunta concreta: tengo este ambiente vacío, ¿qué compro y cómo queda? Sacás una foto, escribís qué querés, y te devuelve una lista de productos reales de un catálogo y la imagen del mismo ambiente con esos productos.",
      30, clase="portada")

# 2 · El problema --------------------------------------------------------------------------------
cat_ids = ["391.505.88", "802.456.40", "302.865.67", "802.972.43", "832.351.10", "503.265.29"]
cat_grid = "".join(producto(i, 150) for i in cat_ids)
ikea_room = "datos/dataset/ikea/images/room_scenes/ikea-find-your-living-room-design-inspiration__1364308433351-s4.jpg"
slide("problema", "El problema", "El problema", cab("El problema", "¿Qué compro para este ambiente, y cómo queda?") + f'''
<div class="tres-paneles">
  <figure class="panel"><div class="catalogo-hoja">{cat_grid}</div><figcaption><b>Los catálogos</b> muestran cada mueble suelto, sobre fondo blanco.</figcaption></figure>
  <figure class="panel">{foto("ikea-room-prob", ikea_room, 540, 420)}<figcaption><b>Las fotos de ambientes</b> muestran la casa de otro.</figcaption></figure>
  <figure class="panel tuyo">{foto("cab-living-room", AM / "caballito-living" / "room.jpg", 540, 420)}<figcaption><b>Tu ambiente</b> está vacío, y tenés que decidir sin verlo puesto.</figcaption></figure>
</div>
<div class="preguntas3">
  <div><span class="num">1</span>Qué productos reales, que se puedan comprar, van</div>
  <div><span class="num">2</span>Cuántos, y de qué medida</div>
  <div><span class="num">3</span>Cómo queda el ambiente con ellos</div>
</div>''',
      "Cuando te mudás a un lugar vacío tenés que decidir qué comprar sin poder verlo puesto. Los catálogos muestran cada mueble suelto, sobre fondo blanco, y las fotos de ambientes muestran la casa de otro. Nosotros queremos responder, para este ambiente y este pedido: qué productos reales, que se puedan comprar, van; cuántos y de qué medida; y cómo queda el ambiente con ellos.",
      45)

# 3 · El producto ------------------------------------------------------------------------------
filas_lista = []
for ch in HERO_CHOICE:
    c = _cand_info[ch["id"]]
    k = c.get("kind", "")
    filas_lista.append(f'<li>{producto(ch["id"], 58)}<div class="l-txt"><b>{KIND_ES.get(k, k)}</b><span class="cod">{ch["id"]}{" · " + medida(c.get("dimensions_cm")) if medida(c.get("dimensions_cm")) else ""}</span></div><span class="cant">×{ch["quantity"]}</span></li>')
_n_bib = next(ch["quantity"] for ch in HERO_CHOICE if _cand_info[ch["id"]].get("kind") == "bookcase")
slide("producto", "El producto", "El producto", cab("El producto", "Foto + pedido → lista de compra + imagen") + f'''
<div class="prod-entra">
  <div class="et-flujo">Entra</div>
  {foto("hero-room-md", HERO / "room.jpg", 470, 352)}
  <blockquote class="pedido">«{esc(HERO_REQ)}»</blockquote>
</div>
<div class="prod-flecha"><svg viewBox="0 0 80 40"><path d="M2 20 H70 M56 8 L72 20 L56 32"/></svg></div>
<div class="prod-sale">
  <div class="et-flujo">Sale</div>
  {foto("hero-final-md", HERO / "final.png", 780, 585, q=82)}
  <p class="pie">El mismo ambiente, con esos productos puestos.</p>
</div>
<div class="prod-lista">
  <div class="lista-cab"><b>Lista de compra</b><span>{N_HERO} productos del catálogo</span></div>
  <ul class="lista">{"".join(filas_lista)}</ul>
</div>''',
      f"Así se usa. La entrada es una foto del ambiente y un pedido en texto libre, como este: un rincón de lectura con una biblioteca alta de madera oscura. La salida son dos cosas: la lista de compra, con productos reales del catálogo y cuántas unidades de cada uno (acá, {_n_bib} bibliotecas iguales), y la foto del mismo ambiente con esos productos puestos.",
      55)

# 4 · Por qué RAG ----------------------------------------------------------------------------------
slide("rag", "Por qué RAG", "Por qué RAG", cab("Por qué RAG", "Recomendaciones atadas a productos que existen") + '''
<div class="tres-col">
  <article class="col-rag">
    <h3>Un LLM solo</h3>
    <p>Sabe de decoración, pero no sabe qué hay en un catálogo.</p>
    <div class="ticket-falso"><span class="tf-et">te recomienda</span><b>Sillón de cuero coñac</b><span class="tf-cod">código: ninguno · nadie lo vende</span></div>
  </article>
  <article class="col-rag">
    <h3>Un modelo de imagen solo</h3>
    <p>Amobla lindo, pero inventa los muebles.</p>
    <div class="ticket-falso vacio-lista"><span class="tf-et">lista de compra</span><b>—</b><span class="tf-cod">no hay nada que comprar</span></div>
  </article>
  <article class="col-rag elegida">
    <h3>RAG, con el catálogo como base de conocimiento</h3>
    <ol class="flujo-rag">
      <li><span><b>El LLM</b> decide qué hace falta</span></li>
      <li><span><b>El retrieval</b> trae candidatos reales</span></li>
      <li><span><b>El VLM</b> elige mirando sus fotos</span></li>
      <li><span><b>La imagen</b> se genera desde las fotos de los elegidos</span></li>
    </ol>
  </article>
</div>
<p class="remate">No es un Q&amp;A: la consulta es una foto y un pedido abierto, y la respuesta es una combinación de productos que tiene que funcionar junta.</p>''',
      "¿Por qué un RAG y no un LLM o un modelo de imagen solos? Un LLM sabe de decoración, pero no sabe qué hay en un catálogo: te recomienda un sillón de cuero coñac que nadie vende. Un modelo de imagen amobla lindo, pero inventa los muebles: no hay nada que comprar. Con RAG, el catálogo es la base de conocimiento: el LLM decide qué hace falta, el retrieval trae candidatos reales y el VLM elige mirando sus fotos. Y la imagen se genera desde las fotos de los productos elegidos. No es un Q&A: la consulta es una foto y un pedido abierto, y la respuesta es una combinación de productos que tiene que funcionar junta.",
      48)

# 5 · Separador: Datos -------------------------------------------------------------------------------
slide("sep-datos", "Parte 1: Datos", "Datos", separador(1, "Con qué catálogo trabajamos, cómo medimos el retrieval y con qué ambientes probamos.",
                                                      ["El catálogo", "El ground truth", "Los ambientes vacíos"]),
      "Primero, los datos: con qué catálogo trabajamos, cómo medimos el retrieval y con qué ambientes probamos.",
      12, clase="oscura separador")

# 6 · El catálogo -------------------------------------------------------------------------------------
FICHA_ID = "802.456.40"
ficha_lineas = "".join(
    f'<div class="fl"><dt>{esc(l.split(":", 1)[0])}</dt><dd>{esc(l.split(":", 1)[1].strip())}</dd></div>'
    for l in DESCR[FICHA_ID].strip().splitlines())
slide("catalogo", "El catálogo", "Datos · el catálogo", cab("Datos · el catálogo", "El catálogo: productos IKEA descritos por un VLM") + f'''
<div class="cat-izq">
  <div class="cifra-grande"><span>{D["prod_855"]}</span><i>→</i><span>{D["prod_819"]}</span></div>
  <p class="cifra-pie">productos de living y comedor (muebles, iluminación, textiles y deco), {D["prod_819"]} después de la revisión</p>
  <div class="cifras-chicas"><div><b>{D["n_tipos"]}</b>tipos</div><div><b>{D["n_kinds"]}</b>kinds</div></div>
  <p class="fuente">Dataset IKEA de Tautkute y otros, de uso no comercial.</p>
  <h3 class="b-et">Los problemas del catálogo</h3>
  <ul class="problemas">
    <li><b>Fotos de {D["foto_lado"]} píxeles</b> de lado</li>
    <li><b>{D["asientos_sin_medida"]} de {D["asientos"]} asientos</b> sin medidas</li>
    <li><b>Productos que comparten la foto</b> de otra medida del mismo modelo</li>
  </ul>
</div>
<div class="cat-ficha">
  <div class="ficha-foto">{producto(FICHA_ID, 300)}<span class="cod">{FICHA_ID}</span></div>
  <div class="ficha-txt">
    <div class="ficha-cab">La descripción que escribe un VLM mirando la foto: <b>8 líneas fijas</b>. Es lo que se indexa.</div>
    <dl class="ficha-dl">{ficha_lineas}</dl>
  </div>
</div>''',
      f"El catálogo base es el dataset IKEA de Tautkute y otros, de uso no comercial. Nos quedamos con lo de living y comedor: muebles, iluminación, textiles y deco, {D['prod_855']} productos, {D['prod_819']} después de la revisión. El texto de IKEA es pobre, así que un VLM describe cada producto mirando su foto en 8 líneas fijas (esta es una). Eso es lo que se indexa, y el experimento 1 muestra por qué. Los problemas del catálogo: fotos de {D['foto_lado']} píxeles, asientos sin medidas ({D['asientos_sin_medida']} de {D['asientos']}) y productos que comparten la foto de otra medida.",
      54)

# 7 · Ground truth --------------------------------------------------------------------------------------
GT_ROOM = "ikea-find-your-living-room-design-inspiration__1364308433351-s4.jpg"
_rank_rows = {}
with gzip.open(EV / "20261110-003643_ablacion-retrieval" / "rankings.jsonl.gz", "rt") as fh:
    for line in fh:
        r = json.loads(line)
        if r["method"] == BASE and r["room_id"] == GT_ROOM:
            _rank_rows[r["piece"]] = r
_gt_any = _rank_rows[0]["relevant_any"]
_q_mesa = next(r for r in _rank_rows.values() if r["kind"] == "coffee table")
_q_lampara = next(r for r in _rank_rows.values() if r["kind"] == "floor lamp")
_gt_strip = "".join(producto(i, 84, "con-borde") for i in [x for x in _gt_any if x in ITEMS][:9])


def ranking_strip(r, n, w, gt_marca="el anotado"):
    out = []
    for pos, pid in enumerate(r["ranked"][:n], start=1):
        ok = pid in r["relevant"]
        out.append(f'<div class="rk{" ok" if ok else ""}"><span class="rk-n">{pos}</span>{producto(pid, w)}{f"<span class=rk-ok>{gt_marca}</span>" if ok else ""}</div>')
    return "".join(out)


def query_html(q: str, lineas_max=8) -> str:
    ls = q.strip().splitlines()[:lineas_max]
    return "".join(f'<div><i>{esc(l.split(":", 1)[0])}:</i>{esc(l.split(":", 1)[1])}</div>' for l in ls)


slide("gt", "Ground truth", "Datos · ground truth", cab("Datos · ground truth", "El ground truth: ambientes reales con sus muebles") + f'''
<div class="gt-izq">
  {foto("gt-room", "datos/dataset/ikea/images/room_scenes/" + GT_ROOM, 800, 502)}
  <div class="gt-anot"><span class="mini-et">Productos anotados en esta foto</span><div class="gt-strip">{_gt_strip}</div></div>
</div>
<div class="gt-der">
  <div class="mini-et">Por cada mueble visible, un subagente escribe la búsqueda como la escribiría el plan</div>
  <div class="query">{query_html(_q_mesa["query"])}</div>
  <div class="mini-et">Lo que trae el retrieval: acierta si el anotado sale primero (hit@1) o entre los k primeros (hit@k)</div>
  <div class="rk-fila">{ranking_strip(_q_mesa, 5, 120)}</div>
</div>
<div class="gt-cifras">
  <div><b>{D["n_ambientes_gt"]}</b>fotos de livings y comedores reales de IKEA</div>
  <div><b>{D["n_busquedas"]}</b>búsquedas, una por mueble visible</div>
  <div><b>{D["n_respondibles"]}</b>con su producto en el catálogo</div>
  <div class="gt-ic">Intervalos de confianza: <b>bootstrap por ambiente</b>, porque las búsquedas de un mismo ambiente no son independientes.</div>
</div>''',
      f"Para medir el retrieval necesitamos saber cuál es el producto correcto. El dataset trae {D['n_ambientes_gt']} fotos de livings y comedores reales de IKEA con sus productos anotados. Por cada mueble visible, un subagente escribe la búsqueda como la escribiría nuestro plan, mirando el ambiente: {D['n_busquedas']} búsquedas, {D['n_respondibles']} con su producto en el catálogo. Una búsqueda acierta si el anotado sale primero (hit@1) o entre los k primeros. Los intervalos de confianza son por bootstrap por ambiente, porque las búsquedas de un mismo ambiente no son independientes.",
      54)

# 8 · Ambientes vacíos -------------------------------------------------------------------------------------
ESTILO = {
    "caballito-living": ("Living", "moderno, luminoso"), "caballito-comedor": ("Comedor", "nórdico"),
    "alvear-escritorio": ("Escritorio", "nórdico"), "alvear-living-comedor": ("Living comedor", "nórdico"),
    "experimento-lectura": ("Rincón de lectura", "cálido, maderas"),
    "publica-loft-industrial": ("Loft", "industrial"), "publica-living-clasico": ("Sala con chimenea", "clásico"),
    "publica-comedor-clasico-moderno": ("Comedor abierto", "clásico actual"), "publica-living-japandi": ("Living", "japandi"),
    "publica-living-bohemio": ("Living", "bohemio"), "publica-estudio-sobrio": ("Estudio", "moderno sobrio"),
}
tiles = []
for p in PEDIDOS:
    nombre, estilo = ESTILO[p["slug"]]
    pub = PUB_POR_ARCHIVO.get(p["foto"])
    cred = f'<span class="cred">{esc(pub["autor"])} · {esc(pub["licencia"])}</span>' if pub else ""
    tiles.append(f'<figure class="amb{" pub" if pub else ""}">{foto("vac-" + p["slug"], p["foto"], 270, 180, q=76)}'
                 f'<figcaption><b>{nombre}</b><span>{estilo}</span>{cred}</figcaption></figure>')
slide("vacios", "Ambientes vacíos", "Datos · ambientes vacíos", cab("Datos · ambientes vacíos", "Ambientes vacíos reales para probar de punta a punta") + f'''
<div class="vac-izq">
  <div class="cifra-grande chica"><span>{D["n_ambientes_vacios"]}</span></div>
  <p class="cifra-pie">ambientes vacíos reales, cada uno con un pedido escrito como lo escribiría un usuario que sabe pedir</p>
  <ul class="vac-datos">
    <li><b>{D["n_propios"]}</b> de departamentos nuestros</li>
    <li><b>{D["n_publicos"]}</b> públicos, de Wikimedia Commons y Flickr (Creative Commons), con estilos distintos del nórdico</li>
    <li>elegidos entre <b>{D["n_publicas_revisadas"]}</b> que revisamos uno por uno para descartar renders y fotos generadas con IA</li>
  </ul>
  <p class="nota-borde">Acá no hay ground truth: medimos con un juez y con métricas de imagen.</p>
</div>
<div class="vac-grilla">{"".join(tiles)}</div>''',
      f"Para probar el sistema completo hacen falta ambientes vacíos reales. Tenemos {D['n_ambientes_vacios']}: {D['n_propios']} de departamentos nuestros y {D['n_publicos']} públicos de Wikimedia Commons y Flickr, con licencia Creative Commons, elegidos entre {D['n_publicas_revisadas']} que revisamos uno por uno para descartar renders y fotos generadas con IA. Cada uno tiene un pedido escrito como lo escribiría un usuario que sabe pedir; los públicos, con estilos distintos del nórdico. Acá no hay ground truth: medimos con un juez y con métricas de imagen.",
      48)

# 9 · Separador: Arquitectura --------------------------------------------------------------------------
slide("sep-arq", "Parte 2: Arquitectura", "Arquitectura", separador(2, "De dónde venimos y qué variantes probamos.", ["v0 → v1", "Los dos pipelines", "Los hiperparámetros"]),
      "Después, la arquitectura: de dónde venimos y qué variantes probamos.", 12, clase="oscura separador")

# 10 · v0 → v1 -----------------------------------------------------------------------------------------
_v0_rec = None
for line in (next((RES / "v0_imagen" / "corridas").glob("*retriever_abl-retriever-name-dinov3__method-none__category_filter-true")) / "recortes.jsonl").read_text().splitlines():
    r = json.loads(line)
    if r["room_id"] == GT_ROOM and r["category"] == "sofa":
        _v0_rec = r
_room_im = Image.open(ROOT / "datos/dataset/ikea/images/room_scenes" / GT_ROOM)
_bx = [round(v) for v in _v0_rec["box"]]
_crop = _room_im.crop(_bx)
_sofa_ok = _v0_rec["relevant"][1] if _v0_rec["relevant"][1] in _v0_rec["ranked_skus"] else _v0_rec["relevant"][0]
_sx = 480 / _room_im.width
_box_css = f"left:{_bx[0] * _sx:.0f}px;top:{_bx[1] * _sx:.0f}px;width:{(_bx[2] - _bx[0]) * _sx:.0f}px;height:{(_bx[3] - _bx[1]) * _sx:.0f}px"
_hero_q = HERO_CAND[0]["spec"]["query"]
slide("v0v1", "v0 → v1", "Arquitectura · v0 → v1", cab("Arquitectura · v0 → v1", "Por qué dejamos la búsqueda por imagen") + f'''
<div class="v-col">
  <div class="v-et"><b>v0</b> · buscar por imagen</div>
  <div class="v-foto">{foto("v0-room", "datos/dataset/ikea/images/room_scenes/" + GT_ROOM, 480, round(_room_im.height * _sx))}<div class="caja" style="{_box_css}"></div></div>
  <div class="v0-cadena">{foto("v0-crop", _crop, 170, 78, modo="fit", q=82)}<span class="v-flecha">→</span>{producto(_sofa_ok, 90, "con-borde")}</div>
  <p class="v-txt">Grounding DINO detecta cada mueble, SAM lo recorta y DINOv3 busca la foto del catálogo más parecida. Sirve para encontrar <em>este</em> sofá.</p>
</div>
<div class="v-col v-medio">
  <div class="v-et">Nuestro caso</div>
  <div class="v-foto">{foto("hero-room-v", HERO / "room.jpg", 400, 300)}<div class="nada">¿Qué recortamos?</div></div>
  <p class="v-txt">Un ambiente vacío: no hay nada que recortar.</p>
</div>
<div class="v-col">
  <div class="v-et"><b>v1</b> · buscar por texto</div>
  <p class="v-txt">Un LLM escribe el producto ideal en el mismo formato que el catálogo:</p>
  <div class="query chica">{query_html(_hero_q, 6)}</div>
</div>
<div class="v-res" data-paso="1">
  <div class="v-res-t">Con el mismo ground truth</div>
  {barras([dict(et="v0 · por imagen", sub=f"{D['v0_n']} recortes", v=D['v0_hit1'], ic=V0['retrieval']['hit@1_ci95'], tono="otro"),
           dict(et="v1 · por texto", sub=f"{D['v1_n']} búsquedas", v=D['v1_hit1'], ic=ic(TXT, BASE), tono="elegido")], ancho=1100, et_w=300, alto=36, sep=20, eje=True)}
  <div class="v-res-n">hit@1<br><span>y la v1 funciona con el ambiente vacío</span></div>
</div>''',
      f"La primera versión buscaba por imagen: detectaba cada mueble en la foto con Grounding DINO, lo recortaba con SAM y buscaba la foto del catálogo más parecida con DINOv3. Eso sirve para encontrar este sofá, pero nuestro caso es un ambiente vacío: no hay nada que recortar. La v1 busca por texto: un LLM escribe el producto ideal en el mismo formato que el catálogo. (Flecha.) Con el mismo ground truth, la v1 da {f2(D['v1_hit1'])} de hit@1 contra {f2(D['v0_hit1'])} de la v0, y además funciona con el ambiente vacío.",
      60)

# 11 · Dos pipelines ----------------------------------------------------------------------------------
def caja(t, d, cls=""):
    return f'<div class="pcaja {cls}"><b>{t}</b><span>{d}</span></div>'


slide("pipelines", "Dos pipelines", "Arquitectura · v1", cab("Arquitectura · v1", "Dos pipelines: indexing offline y consulta por pedido") + f'''
<div class="pipe">
  <div class="carril c1">
    <div class="carril-et"><b>Indexing</b><span>corre una vez</span></div>
    {caja("Catálogo", f"IKEA + Amazon Berkeley Objects: {D['prod_todos']} productos con foto")}
    <i class="pf">→</i>
    {caja("Descripción", "un VLM mira cada foto y escribe 8 líneas fijas")}
    <i class="pf">→</i>
    {caja("Embeddings", "Qwen3-Embedding-0.6B, local, en CPU")}
  </div>
  <div class="chroma"><svg viewBox="0 0 240 120"><ellipse cx="120" cy="22" rx="110" ry="18"/><path d="M10 22 V96 A110 18 0 0 0 230 96 V22"/></svg><b>ChromaDB</b><span>HNSW, coseno</span></div>
  <div class="carril c2" data-paso="1">
    <div class="carril-et"><b>Consulta</b><span>corre por pedido</span></div>
    {caja("Foto + pedido", "el ambiente vacío y lo que querés, en texto libre", "entrada")}
    <i class="pf">→</i>
    {caja("Plan", "Claude Opus decide las piezas, su tipo, la medida máxima, y escribe la consulta ideal")}
    <i class="pf">→</i>
    {caja("Retrieve", f"Qwen3 + ChromaDB con filtros duros: {D['k_flujo']} candidatos por pieza", "acento")}
    <i class="pf">→</i>
    {caja("Choose", "Claude mira las fotos, elige uno por pieza pensando la combinación, y cuántas unidades")}
    <i class="pf">→</i>
    {caja("Imagen", "Nano Banana 2 recibe la foto del ambiente y las de los productos")}
    <i class="pf">→</i>
    {caja("Control", f"SIFT: si cambió el cuarto, se descarta y se reintenta (hasta {ROOM_CHECK['attempts']})", "control")}
  </div>
  <svg class="reintento" data-paso="1" viewBox="0 0 400 70"><path d="M363 4 V44 H111 V10"/><path d="M101 20 L111 6 L121 20"/><text x="237" y="66" text-anchor="middle">si cambió el cuarto, otro intento</text></svg>
  <div class="pipe-nota" data-paso="1">Choose solo puede elegir productos recuperados: <em>la respuesta queda atada al catálogo.</em></div>
</div>''',
      f"La arquitectura tiene dos pipelines. El de indexing corre una vez: catálogo, descripciones del VLM, embeddings con Qwen3 y ChromaDB. (Flecha.) El de consulta corre por pedido. Plan: Claude Opus lee la foto y el pedido, decide las piezas, su tipo, la medida máxima y escribe la consulta ideal. Retrieve: Qwen3 y ChromaDB con filtros duros, k candidatos por pieza. Choose: Claude mira las fotos de los candidatos, elige uno por pieza pensando la combinación, y cuántas unidades; solo puede elegir productos recuperados. Y la imagen: Nano Banana 2 recibe la foto del ambiente y las de los productos, y un control automático descarta la imagen si cambió el cuarto.",
      75)

# 12 · Hiperparámetros (sin spoilers: qué probamos y cómo se mide, no qué ganó) --------------------------
HIPER = [
    ("Texto que se indexa", "texto del vendedor · descripción del VLM · nombre + descripción", "hit@1"),
    ("Embedder", "hashing · BGE-base · Qwen3-Embedding", "hit@1, MRR"),
    ("Filtro duro", "ninguno · por tipo · por kind", "hit@1, hit@10"),
    ("Splitting", "documento entero · chunk por línea · línea contra línea", "hit@1"),
    ("Dimensión del embedding", "de 32 a 1024 componentes", "hit@1"),
    ("Base vectorial y consulta", "exacta · HNSW; consulta completa · línea Type · kind", "hit@1"),
    ("Reranking", "ninguno · cross-encoder · VLM", "hit@1, MRR"),
    ("Candidatos por pieza", "k de 1 a 10", "acierto de la elección"),
    ("Alcance del catálogo", f"{D['prod_268']} · {D['prod_855']} · revisado", "hit@1"),
    ("Qué catálogo", "IKEA · Amazon (ABO) · los dos", "juez de a pares"),
    ("Cómo medir", "hit@1 · relevancia graduada · tres redactores", "acuerdo con el GT"),
    ("La imagen", "escena guiada · libre · sin tope · edición estricta", "SIFT, SSIM"),
]
filas_h = "".join(f'<div class="h-n">{i}</div><div class="h-q">{q}</div><div class="h-o">{o}</div><div class="h-m">{mt}</div>' for i, (q, o, mt) in enumerate(HIPER, 1))
slide("hiper", "Los hiperparámetros", "Arquitectura · variantes", cab("Arquitectura · variantes", "Los hiperparámetros que decidimos con experimentos") + f'''
<div class="hiper"><div class="h-cab">#</div><div class="h-cab">Qué decidimos</div><div class="h-cab">Qué probamos, con todo lo demás fijo</div><div class="h-cab">Cómo lo medimos</div>{filas_h}</div>
<p class="hiper-pie">En este orden, que es más o menos el orden en que los hicimos: cada uno deja su decisión en la configuración del siguiente.</p>''',
      "Cada fila de esta tabla es una decisión de la arquitectura que tomamos con un experimento, con todo lo demás fijo. Todavía no decimos qué ganó: eso lo vemos en cada experimento. Los vamos a ver en este orden, que es más o menos el orden en que los hicimos: cada uno deja su decisión en la configuración del siguiente.",
      30)

# 13 · Separador: Métricas -------------------------------------------------------------------------------
slide("sep-met", "Parte 3: Métricas", "Métricas", separador(3, "Antes de los experimentos, las métricas, para que cada número que mostremos se entienda.", ["Con ground truth", "Sin un único correcto", "La imagen"]),
      "Antes de los experimentos, las métricas, para que cada número que mostremos se entienda.", 12, clase="oscura separador")

# 14 · Métricas de retrieval -------------------------------------------------------------------------------
_lamp_rank = _q_lampara["rank"]
slide("met-ret", "Métricas de retrieval", "Métricas · retrieval", cab("Métricas · retrieval", "Con ground truth: ¿trae el producto correcto, y arriba?") + f'''
<div class="met-ej">
  <div class="mini-et">Una búsqueda real del ground truth (una lámpara de pie): sus 10 primeros candidatos</div>
  <div class="met-cotas">
    <div class="mc" style="--k:1"><span>hit@1 = 0</span></div>
    <div class="mc" style="--k:3"><span>hit@3 = 1</span></div>
    <div class="mc" style="--k:5"><span>hit@5 = 1</span></div>
  </div>
  <div class="rk-fila diez">{ranking_strip(_q_lampara, 10, 132)}</div>
  <div class="met-rr">el anotado está en el puesto {_lamp_rank}: <b>1/{_lamp_rank}</b> para el MRR</div>
</div>
<div class="met-defs">
  <div class="md"><h4>hit@k</h4><p>¿El anotado está entre los k primeros? hit@1 es encontrarlo primero; hit@k con k igual a los candidatos que ve el VLM es el techo de lo que puede elegir.</p></div>
  <div class="md"><h4>MRR@10</h4><p>El promedio de 1 / posición del correcto. Premia que esté arriba, no solo que esté.</p></div>
  <div class="md"><h4>Context recall y precision</h4><p>Las de RAGAS: cuántos de los productos de un ambiente aparecen entre los candidatos, y cuán arriba quedan.</p></div>
  <div class="md"><h4>NDCG@10</h4><p>Como el MRR, pero admite relevancia graduada: un candidato “aceptable” suma algo.</p></div>
  <div class="md ic"><h4>IC 95%</h4><p>Si los intervalos de dos métodos se pisan, con estos datos no los podemos distinguir.</p>
    <svg viewBox="0 0 260 60" class="ic-mini"><line x1="20" y1="18" x2="150" y2="18"/><line x1="20" y1="10" x2="20" y2="26"/><line x1="150" y1="10" x2="150" y2="26"/><circle cx="85" cy="18" r="6"/><line x1="110" y1="44" x2="240" y2="44"/><line x1="110" y1="36" x2="110" y2="52"/><line x1="240" y1="36" x2="240" y2="52"/><circle cx="175" cy="44" r="6"/></svg></div>
</div>''',
      "Las métricas de retrieval, donde sí hay ground truth. Arriba, una búsqueda real: el anotado sale segundo. hit@k: si el anotado está entre los k primeros; acá hit@1 da 0 y hit@3 da 1. hit@1 es encontrarlo primero, y hit@k con k igual a los candidatos que ve el VLM es el techo de lo que puede elegir. MRR: el promedio de uno sobre la posición del correcto, premia que esté arriba; esta búsqueda suma un medio. Context recall y context precision son las de RAGAS: cuántos de los productos de un ambiente aparecen entre los candidatos, y cuán arriba quedan. NDCG admite relevancia graduada. Y los intervalos de confianza: si dos métodos tienen intervalos que se pisan, con estos datos no los podemos distinguir.",
      60)

# 15 · Jueces ---------------------------------------------------------------------------------------------------
slide("met-juez", "Jueces y pares", "Métricas · la respuesta", cab("Métricas · la respuesta", "Sin un único correcto: jueces validados y de a pares") + '''
<div class="juez-grilla">
  <div class="jz">
    <h4>Relevancia graduada</h4>
    <p>Un LLM califica cada uno de los 3 primeros candidatos. Antes de creerle, chequeamos que le dé 2 al producto anotado.</p>
    <div class="notas3"><div><b>2</b>el mismo o indistinguible</div><div><b>1</b>una alternativa aceptable</div><div><b>0</b>no sirve</div></div>
  </div>
  <div class="jz">
    <h4>RAGAS sobre la explicación</h4>
    <p>Cada elección viene con su porqué.</p>
    <div class="dos-def"><div><b>Faithfulness</b>¿lo que dice se sostiene con lo que vio?</div><div><b>Answer relevance</b>¿responde al pedido?</div></div>
  </div>
  <div class="jz">
    <h4>Juez de a pares, en los dos órdenes</h4>
    <p>Para comparar variantes sin ground truth: el juez ve las dos listas sin saber cuál es cuál. Una gana un ambiente solo si gana en los dos órdenes; reportamos cuánto coinciden.</p>
    <div class="ordenes"><span class="o"><i>A</i><i>B</i></span><span class="y">y</span><span class="o"><i>B</i><i>A</i></span></div>
  </div>
  <div class="jz">
    <h4>El costo de cada llamada</h4>
    <p>Cada llamada paga queda registrada con su costo; las respuestas de los jueces quedan en caché.</p>
    <div class="recibo-mini"><span>plan</span><span>choose</span><span>juez</span><span>imagen</span></div>
  </div>
</div>''',
      "Cuando no hay un único correcto usamos jueces, pero validados. Relevancia graduada: un LLM califica el top-3 con 2, 1 o 0, y antes chequeamos que le dé 2 al producto anotado. RAGAS sobre la explicación de cada elección: faithfulness, si lo que dice se sostiene con lo que vio, y answer relevance, si responde al pedido. Para comparar variantes sin ground truth, un juez de a pares en los dos órdenes, y reportamos cuánto coinciden los dos órdenes. Y el costo de cada llamada.",
      54)

# 16 · Métricas de imagen -----------------------------------------------------------------------------------------
_hm = img_metrics("experimento-buen-pedido-estricto")
_fin = Image.open(HERO / "final.png").convert("RGB")
_fin_sm = _fin.copy()
_dr = ImageDraw.Draw(_fin_sm, "RGBA")
for p in _hm["productos"]:
    if p.get("box"):
        _dr.rectangle(p["box"], outline=(169, 78, 43, 255), width=5, fill=(169, 78, 43, 70))
_crops = []
for p in _hm["productos"][:3]:
    b = p["box"]
    _crops.append((p, _fin.crop(b)))
crops_html = "".join(
    f'<div class="id-par">{producto(p["id"], 96)}<span class="v-flecha chica">↔</span>{foto("crop-" + p["id"], c, 96, 96, modo="fit", q=82)}<span class="id-p">puesto {p["puesto"]} de {p["entre"]}</span></div>'
    for p, c in _crops)
slide("met-img", "Métricas de imagen", "Métricas · la imagen", cab("Métricas · la imagen", "La imagen: el mismo cuarto, con lo que se pidió") + f'''
<div class="img-tres">
  <div class="it">
    <h4>¿Es el mismo cuarto?</h4>
    <div class="par-fotos">{foto("hero-room-xs", HERO / "room.jpg", 250, 188)}{foto("hero-final-cajas", _fin_sm, 250, 188, q=80)}</div>
    <div class="it-cifras"><div><b>{_hm["ambiente"]["sift_inliers"]}</b>puntos de la foto reencontrados</div><div><b>{f2(_hm["ambiente"]["ssim_fuera_de_los_muebles"])}</b>SSIM fuera de los muebles</div></div>
    <p><b>SIFT</b> reencuentra puntos de la foto original en la imagen y mide cuánto se movió la cámara. <b>SSIM</b> compara lo que no es mueble (afuera de las cajas).</p>
  </div>
  <div class="it">
    <h4>¿Son los mismos productos?</h4>
    <div class="id-lista">{crops_html}</div>
    <div class="it-cifras"><div><b>{_hm["fidelidad"]["detectados"]} de {_hm["fidelidad"]["productos"]}</b>productos detectados</div><div><b>{round(_hm["fidelidad"]["identificados@1"] * _hm["fidelidad"]["productos"])} de {_hm["fidelidad"]["productos"]}</b>con el de la lista primero</div></div>
    <p>Detectamos cada mueble, lo recortamos y vemos si el más parecido del catálogo es el de la lista.</p>
  </div>
  <div class="it">
    <h4>¿Es lo que se pidió?</h4>
    <div class="siglip"><span class="sg-pedido">«{esc(HERO_REQ[:96])}…»</span><span class="sg-x">SigLIP 2</span><span class="sg-img">la imagen final: {f2(_hm["pedido_imagen"]["siglip_final"])} · la foto vacía: {f2(_hm["pedido_imagen"]["siglip_vacia"])}</span></div>
    <div class="it-cifras tres"><div><b>{_hm["fidelidad"]["productos"] - _hm["fidelidad"]["detectados"]}</b>faltan</div><div><b>{len(_hm["repetidas"])}</b>repetidos</div><div><b>{len(_hm["inventadas"])}</b>inventado</div></div>
    <p><b>SigLIP 2</b> entre el pedido y la imagen, y contamos lo que <b>falta</b>, lo <b>repetido</b> y lo <b>inventado</b>.</p>
  </div>
</div>
<p class="remate chico">Además: reproducibilidad, con tres redactores de las búsquedas, y el espacio de embeddings.</p>''',
      "Para la imagen medimos tres cosas. Que sea el mismo cuarto: SIFT reencuentra puntos de la foto original y mide cuánto se movió la cámara, y SSIM compara lo que no es mueble. Que sean los mismos productos: detectamos cada mueble, lo recortamos y vemos si el más parecido del catálogo es el de la lista. Y que sea lo que se pidió: SigLIP 2 entre el pedido y la imagen, y contamos lo que falta, lo repetido y lo inventado. Además, reproducibilidad, con tres redactores, y el espacio de embeddings.",
      54)

# 17 · Separador: Experimentos ----------------------------------------------------------------------------------------
riel_grande = '<ol class="riel-grande">' + "".join(f'<li><b>{i + 1}</b>{t}</li>' for i, t in enumerate(["Por qué lo hicimos y qué queríamos ver", "Qué es el experimento", "Recién ahí, los resultados", "La decisión"])) + "</ol>"
slide("sep-exp", "Parte 4: Experimentos", "Experimentos", separador(4, f"{EXP_TOTAL} experimentos, todos en el mismo orden:", [], riel_grande + '<p class="sep-desc chica">Los resultados y la decisión aparecen con la flecha, cuando ya se contó lo anterior.</p>'),
      "Ahora los experimentos. Todos siguen el mismo orden: primero por qué lo hicimos y qué queríamos ver; después cómo es el experimento; y recién ahí mostramos los resultados y, al final, la decisión. Cada parte aparece con la flecha: el panel de resultados está vacío hasta que contamos las dos primeras.",
      18, clase="oscura separador")

# 18 · Exp 1 --------------------------------------------------------------------------------------------------------------
_nol = ITEMS["102.335.32"]
e1_extra = f'<div class="ejemplo-vend">{producto("102.335.32", 96, "con-borde")}<div><span class="mini-et">El texto de IKEA de este sillón</span><q>{esc(_nol["description"])}</q></div></div>'
e1_res = f'''<div class="res" data-paso="2">
  {barras([dict(letra="A", et="Texto del vendedor", v=D['e1_vendedor'], ic=ic(F, 'qwen3|seller|filtro-type'), tono="otro"),
           dict(letra="B", et="Descripción del VLM", v=D['e1_desc'], ic=ic(F, BASE), tono="elegido")], ancho=1040, titulo="hit@1 · filtro por tipo", et_w=330)}
  <div class="res-nota grande">× {f"{D['e1_veces']:.1f}".replace(".", ",")} <span>el cambio más grande de todo el trabajo</span></div>
  {barras([dict(letra="B", et="Descripción del VLM", v=D['e1_desc_kind'], ic=ic(F, 'qwen3|description|filtro-kind'), tono="elegido"),
           dict(letra="C", et="Nombre + descripción", v=D['e1_nombre_kind'], ic=ic(F, 'qwen3|name+description|filtro-kind'), tono="otro")], ancho=1040, titulo="hit@1 · filtro por kind (el mismo para las dos)", et_w=330)}
  <div class="res-nota">NOLMYRA no le dice nada al embedding.</div>
</div>'''
experimento(1, "Qué texto se indexa", "¿Alcanza con el texto del vendedor, o conviene describir cada producto mirando su foto?",
            "Nadie pide como escribe el vendedor: se pide un sillón nórdico, de madera clara, con tapizado crema, y todo eso está en la foto. Describir cada producto con un VLM es un costo que se paga una sola vez.",
            [("A", "Texto del vendedor", "nombre, tipo, colores y la frase de marketing"),
             ("B", "Descripción del VLM", "8 líneas mirando la foto, en el mismo formato que la consulta del plan"),
             ("C", "Nombre comercial + descripción", "la misma descripción con el nombre adelante")],
            f"Las mismas {D['n_respondibles']} búsquedas, todo lo demás fijo (Qwen3, filtro). Métrica: hit@1.",
            e1_res,
            "Indexamos solo la descripción del VLM. Y queda una idea para todo el trabajo: consulta y documento escritos en el mismo formato.",
            ("Lo primero que miramos fue qué texto trae el catálogo. IKEA tiene nombre, tipo, colores y una frase de marketing del estilo “The armchair is lightweight and easy to move”. Pero nadie pide así: se pide un sillón nórdico, de madera clara, con tapizado crema, y todo eso está en la foto. La pregunta era si alcanzaba con el texto del vendedor o si valía la pena describir cada producto mirando su foto, un costo que se paga una sola vez.",
             f"Indexamos tres textos y corrimos las mismas {D['n_respondibles']} búsquedas del ground truth, con todo lo demás fijo (Qwen3, filtro): el texto del vendedor; la descripción de 8 líneas que escribe un VLM mirando la foto, en el mismo formato en que el plan escribe la consulta; y esa descripción con el nombre comercial adelante.",
             f"Con el texto del vendedor, hit@1 da {f2(D['e1_vendedor'])}; con la descripción del VLM, {f2(D['e1_desc'])}: más de {int(D['e1_veces'])} veces. Es el cambio más grande de todo el trabajo. El nombre comercial adelante empeora: con el mismo filtro, de {f2(D['e1_desc_kind'])} a {f2(D['e1_nombre_kind'])}. NOLMYRA no le dice nada al embedding.",
             "Indexamos solo la descripción del VLM. Y queda una idea que vuelve en todo el trabajo: la consulta y el documento escritos en el mismo formato."),
            70, porque_extra=e1_extra)

# 19 · Exp 2 ---------------------------------------------------------------------------------------------------------------
_e2 = D["e2"]
_e2_fil = lambda met: [dict(letra=l, et=n, v=_e2[k][met], ic=ic(F, f"{k}|description|filtro-type", "hit@1" if met == 0 else "mrr@10"), tono="elegido" if k == "qwen3" else "otro")  # noqa: E731
                       for l, k, n in (("A", "hashing", "Hashing"), ("B", "bge", "BGE-base"), ("C", "qwen3", "Qwen3-Embedding"))]
e2_res = f'''<div class="res" data-paso="2">
  {barras(_e2_fil(0), ancho=1040, titulo="hit@1", et_w=330)}
  {barras(_e2_fil(1), ancho=1040, titulo="MRR@10", et_w=330)}
  <div class="res-nota">Las descripciones usan vocabulario controlado (los estilos y los kinds salen de listas cerradas): hasta contar palabras funciona bastante.</div>
</div>'''
experimento(2, "Embedder", "¿Cuánto aporta el modelo de embeddings?",
            "Un modelo más grande cuesta memoria y tiempo, y nos pusimos una restricción: el retrieval corre local, en CPU, sin pagar una API. ¿Cuánto gana un modelo entrenado contra una línea de base sin modelo?",
            [("A", "Hashing", "bolsa de palabras hasheada, sin ningún modelo"),
             ("B", "BGE-base", "110 millones de parámetros"),
             ("C", "Qwen3-Embedding", "600 millones de parámetros")],
            "El mismo texto y las mismas búsquedas. Métricas: hit@1 y MRR@10.",
            e2_res,
            "Qwen3-Embedding-0.6B (Apache 2.0, corre en CPU). La lección: el formato del texto vale más que el modelo.",
            ("Con el texto resuelto, la pregunta natural es cuánto aporta el modelo de embeddings. Un modelo más grande cuesta memoria y tiempo, y nos pusimos la restricción de que el retrieval corra local, en CPU, sin pagar una API. Queríamos ver cuánto gana un modelo entrenado contra una línea de base sin modelo.",
             "Tres embedders sobre el mismo texto y las mismas búsquedas: hashing, una bolsa de palabras hasheada, sin ningún modelo; BGE-base, de 110 millones de parámetros; y Qwen3-Embedding, de 600 millones.",
             f"Gana Qwen3, con {f2(_e2['qwen3'][0])}. Pero el hashing queda cerca ({f2(_e2['hashing'][0])}) y BGE último ({f2(_e2['bge'][0])}). La explicación: las descripciones usan vocabulario controlado, los estilos y los kinds salen de listas cerradas, así que hasta contar palabras funciona bastante. Qwen3 gana más claro en MRR ({f2(_e2['qwen3'][1])} contra {f2(_e2['hashing'][1])}).",
             "Qwen3-Embedding-0.6B (Apache 2.0, corre en CPU). La lección: el formato del texto vale más que el modelo."),
            66)

# 20 · Exp 3 --------------------------------------------------------------------------------------------------------------
_e3 = D["e3"]
_e3_fil = lambda j, met: [dict(letra=l, et=n, v=_e3[k][j], ic=ic(F, f"qwen3|description|filtro-{k}", met), tono="elegido" if k == "type" else "otro")  # noqa: E731
                          for l, k, n in (("A", "none", "Sin filtro"), ("B", "type", "Filtro por tipo"), ("C", "kind", "Filtro por kind"))]
e3_res = f'''<div class="res" data-paso="2">
  {barras(_e3_fil(0, "hit@1"), ancho=1040, titulo="hit@1: casi no cambia", et_w=330)}
  {barras(_e3_fil(1, "hit@10"), ancho=1040, titulo="hit@10: el filtro fino resta", et_w=330, xmax=1.0)}
  <div class="res-nota">Si el plan pide una mesa auxiliar y el catálogo la tiene como mesa ratona, el filtro por kind la deja afuera.</div>
</div>'''
experimento(3, "Filtros duros", "¿Conviene filtrar por categoría? ¿Con qué granularidad?",
            "El plan sabe qué pieza busca. Por similitud sola, una mesa nórdica de madera clara se puede parecer más a la consulta que un sofá. Filtrar por metadata es gratis, pero si el plan y el catálogo no coinciden en la categoría, el correcto queda afuera.",
            [("A", "Sin filtro", "solo similitud"),
             ("B", "Filtro por tipo", f"{D['n_tipos']} categorías gruesas: sofá, mesa, lámpara…"),
             ("C", "Filtro por kind", f"{D['n_kinds']} categorías finas: mesa ratona, mesa de comedor…")],
            "En ChromaDB el filtro va como <code>where</code>. Métricas: hit@1 y, sobre todo, hit@10.",
            e3_res,
            "Filtrar siempre, más las medidas máximas del plan. El flujo filtra por los kinds que elige el plan (puede dar más de uno); pasarlo a tipo es lo próximo a probar.",
            ("El plan sabe qué pieza está buscando: un sofá, una lámpara. Por similitud sola, una mesa nórdica de madera clara se puede parecer más a la consulta que un sofá. Un filtro por metadata lo evita y es gratis, pero tiene un riesgo: si el plan y el catálogo no coinciden en la categoría, el producto correcto queda afuera. Queríamos ver si conviene filtrar, y con qué granularidad.",
             f"Tres opciones: sin filtro; filtro por tipo, {D['n_tipos']} categorías gruesas como sofá, mesa o lámpara; y filtro por kind, {D['n_kinds']} categorías finas como mesa ratona o mesa de comedor. En ChromaDB el filtro va como where. Miramos hit@1 y sobre todo hit@10.",
             f"Con descripciones buenas, hit@1 casi no cambia. Pero el filtro por kind resta: en hit@10 da {f2(_e3['kind'][1])} contra {f2(_e3['type'][1])} del filtro por tipo. Si el plan pide una mesa auxiliar y el catálogo la tiene como mesa ratona, el filtro fino la deja afuera. El de tipo protege de los errores gruesos sin ese costo.",
             "Filtrar siempre, más las medidas máximas que estima el plan. Con qué granularidad quedó abierto: el flujo filtra por los kinds que elige el plan, que puede dar más de uno (mesa ratona o auxiliar) para no dejar afuera al correcto. La diferencia con el filtro por tipo es de un punto en hit@1, dentro del intervalo, y tres en hit@10; pasar el flujo a tipo es lo próximo que probaríamos."),
            66)

# 21 · Exp 4 --------------------------------------------------------------------------------------------------------------
_e4 = D["e4"]
e4_res = f'''<div class="res" data-paso="2">
  {barras([dict(letra="A", et="Un documento por producto", v=_e4['whole'], ic=ic(F, BASE), tono="elegido"),
           dict(letra="B", et="Un chunk por línea", v=_e4['max'], ic=ic(F, BASE + '|chunks-lines-max'), tono="otro"),
           dict(letra="C", et="Línea contra línea", v=_e4['aligned'], ic=ic(F, BASE + '|chunks-lines-aligned'), tono="otro")], ancho=1040, titulo="hit@1", et_w=360)}
  <div class="res-nota">Una línea suelta como <code>Colors: light wood</code> se parece a cualquier cosa de madera clara: partir pierde el contexto.</div>
</div>'''
experimento(4, "Splitting", "¿Conviene partir cada descripción en chunks?",
            f"En la materia vimos que el chunking es una de las decisiones centrales de un RAG. Nuestros documentos son cortos ({D['palabras_lo']} a {D['palabras_hi']} palabras), pero tienen 8 líneas con roles distintos. Hipótesis: comparar colores contra colores podía ser más preciso que un solo vector por producto.",
            [("A", "Un documento por producto", "las 8 líneas juntas"),
             ("B", "Un chunk por línea", "el producto vale lo que su línea más parecida a la consulta"),
             ("C", "Línea contra línea", "cada línea contra la del mismo rótulo en la consulta, promediado")],
            "Las mismas búsquedas. Métrica: hit@1.",
            e4_res,
            "Un documento por producto: con documentos tan cortos, no hay nada que partir.",
            (f"En la materia vimos que el chunking es una de las decisiones centrales de un RAG. Nuestros documentos son cortos, de {D['palabras_lo']} a {D['palabras_hi']} palabras, pero tienen 8 líneas con roles distintos: tipo, estilo, colores, materiales. La hipótesis era que comparar línea por línea, colores contra colores, podía ser más preciso que un solo vector por producto.",
             "Tres formas: un documento por producto, con las 8 líneas juntas; un chunk por línea, donde el producto vale lo que su línea más parecida a la consulta; y línea contra línea, cada una contra la del mismo rótulo en la consulta, promediado.",
             f"Gana un documento por producto ({f2(_e4['whole'])}). Línea contra línea queda cerca ({f2(_e4['aligned'])}) y el chunk por línea se desploma ({f2(_e4['max'])}): una línea suelta como “Colors: light wood” se parece a cualquier cosa de madera clara. Partir pierde el contexto.",
             "Un documento por producto. Con documentos tan cortos no hay nada que partir."),
            36, clase_extra="rapido")

# 22 · Exp 5 ---------------------------------------------------------------------------------------------------------------
_dims = [d for d, _, _ in D["e5"]]
_vals = [v for _, v, _ in D["e5"]]
_lo = [c[0] for _, _, c in D["e5"]]
_hi = [c[1] for _, _, c in D["e5"]]
_v512 = dict((d, v) for d, v, _ in D["e5"])[512]
_v1024 = dict((d, v) for d, v, _ in D["e5"])[1024]
_v32 = dict((d, v) for d, v, _ in D["e5"])[32]
e5_chart = lineas(_dims, [dict(ys=_vals, clase="sol")], 1040, 520, 0.3, 0.65, [0.3, 0.4, 0.5, 0.6], xlab="componentes del vector (escala log)",
                  logx=True, banda=(_lo, _hi),
                  marcas=[(512, _v512, f"512: {f2(_v512)}, la mitad de memoria", -18, -26, "end", "elegido"),
                          (1024, _v1024, f"1024: {f2(_v1024)}", 0, 46, "end", "base"),
                          (32, _v32, f"32: {f2(_v32)}", 18, 40, "start", "base")])
e5_res = f'<div class="res" data-paso="2"><div class="g-tit-html">hit@1 con su IC 95% (la banda)</div>{e5_chart}</div>'
experimento(5, "Dimensión del embedding", "¿Cuánto se puede achicar el vector sin perder?",
            f"Qwen3 se entrenó con Matryoshka: las primeras componentes del vector concentran la información, así que se puede truncar sin reentrenar. Con {D['prod_819']} productos no importa; en un catálogo de millones, la memoria y la latencia crecen con la dimensión.",
            [("A", "Truncar", "a 32, 64, 128, 256, 512 y 1024 componentes"),
             ("B", "Renormalizar", "y correr las mismas búsquedas")],
            "Métrica: hit@1, con su intervalo de confianza.",
            e5_res,
            "Para este catálogo dejamos 1024, porque no cuesta nada; si creciera, indexaríamos con 512.",
            (f"Qwen3 se entrenó con Matryoshka: las primeras componentes del vector concentran la información, así que se puede truncar sin reentrenar. Con {D['prod_819']} productos no importa, pero en un catálogo de millones la memoria y la latencia crecen con la dimensión. Queríamos saber cuánto se puede achicar sin perder.",
             "Truncamos los vectores a 32, 64, 128, 256, 512 y 1024 componentes, los renormalizamos y corrimos las mismas búsquedas.",
             f"Con 512 da prácticamente lo mismo que con 1024 ({f2(_v512)} contra {f2(_v1024)}), con la mitad de memoria. Por debajo de 128 cae rápido: con 32, {f2(_v32)}.",
             "Para este catálogo dejamos 1024 porque no cuesta nada; si creciera, indexaríamos con 512."),
            36, clase_extra="rapido")

# 23 · Exp 6 ----------------------------------------------------------------------------------------------------------------
e6_res = f'''<div class="res" data-paso="2">
  {barras([dict(letra="A", et="Búsqueda exacta (numpy)", v=D['e6_exacta'], ic=ic(F, BASE + '|exact'), tono="otro", vtxt=f3(D['e6_exacta'])),
           dict(letra="B", et="ChromaDB (HNSW)", v=D['e6_hnsw'], ic=ic(F, BASE), tono="elegido", vtxt=f3(D['e6_hnsw']))], ancho=1040, titulo="hit@1 · la base vectorial", et_w=380, val_w=130)}
  {barras([dict(letra="C", et="Consulta completa (8 líneas)", v=D['e6_hnsw'], ic=ic(F, BASE), tono="elegido"),
           dict(letra="D", et="Solo la línea Type", v=D['e6_type'], ic=ic(F, BASE + '|consulta-type'), tono="otro"),
           dict(letra="E", et="Solo el kind (sin reescribir)", v=D['e6_kind'], ic=ic(F, BASE + '|consulta-kind'), tono="otro")], ancho=1040, titulo="hit@1 · la consulta", et_w=380, val_w=130)}
  <div class="res-nota">El estilo, los colores y la forma son lo que distingue un sofá de otro.</div>
</div>'''
experimento(6, "Base vectorial y query rewriting", "¿HNSW pierde resultados? ¿Hace falta que el plan reescriba la consulta entera?",
            "Pasamos de una búsqueda exacta con numpy a ChromaDB, que usa HNSW, un índice aproximado: había que verificar que no perdiera resultados. Y el plan escribe para cada pieza el producto ideal en 8 líneas: eso cuesta tokens y latencia en cada pedido.",
            [("A · B", "Exacta contra ChromaDB", "con la misma consulta"),
             ("C", "Consulta completa", "las 8 líneas que escribe el plan"),
             ("D · E", "Consultas cortas", "solo la línea Type, o solo el nombre del kind (no reescribir)")],
            "Métrica: hit@1.",
            e6_res,
            "ChromaDB con la consulta completa que escribe el plan: el query rewriting cuesta, pero vale la pena.",
            ("Dos dudas. Primero, pasamos de una búsqueda exacta con numpy a ChromaDB, que usa HNSW, un índice aproximado: había que verificar que no perdiera resultados. Segundo, el query rewriting: el plan escribe para cada pieza el producto ideal en 8 líneas, y eso cuesta tokens y latencia en cada pedido. Queríamos ver si una consulta más corta alcanzaba.",
             "ChromaDB contra la búsqueda exacta, con la misma consulta. Y la consulta completa contra solo la línea Type, y contra solo el nombre del kind, que sería no reescribir.",
             f"HNSW da exactamente lo mismo que la búsqueda exacta ({f3(D['e6_hnsw'])} y {f3(D['e6_exacta'])}). Con solo la línea Type, hit@1 cae a {f2(D['e6_type'])}; con solo el kind, a {f2(D['e6_kind'])}. El estilo, los colores y la forma son lo que distingue un sofá de otro.",
             "ChromaDB con la consulta completa que escribe el plan. El query rewriting cuesta, pero vale la pena."),
            68)

# 24 · Exp 7 ------------------------------------------------------------------------------------------------------------------
_b, _mi, _op = D["e7_base"], D["e7_minilm"], D["e7_opus"]
e7_fil = lambda j, met: [dict(letra="—", et="Sin reranking", v=(_b[j]), ic=ic(RR, BASE, met), tono="otro"),  # noqa: E731
                         dict(letra="A", et="Cross-encoder MiniLM", v=_mi[j], ic=ic(F, BASE + '|rerank-minilm-reranker', met), tono="otro"),
                         dict(letra="B", et="VLM (Claude Opus)", v=_op[j], ic=ic(RR, BASE + '|rerank-opus', met), tono="elegido")]
e7_res = f'''<div class="res" data-paso="2">
  {barras(e7_fil(0, "hit@1"), ancho=1040, titulo="hit@1", et_w=350)}
  {barras(e7_fil(1, "mrr@10"), ancho=1040, titulo="MRR@10", et_w=350)}
  <div class="res-nota">MiniLM está entrenado con preguntas y pasajes web, no con muebles. El VLM mira la foto, que tiene lo que la descripción no dijo. Cuesta unos <b>{usd(D['e7_costo'])}</b> por búsqueda.</div>
</div>'''
experimento(7, "Reranking <span class=\"tag-adv\">Advanced RAG</span>", "¿Un segundo modelo, que mira la consulta y cada candidato juntos, ordena mejor?",
            f"hit@10 daba {f2(_b[2])} pero hit@1 {f2(_b[0])}: el correcto casi siempre está entre los 10 primeros, pero no primero. El cuello de botella era el orden. Advanced RAG propone un reranker: un segundo modelo que mira la consulta y cada candidato juntos.",
            [("A", "Cross-encoder MiniLM", "entrenado en MS MARCO, local y gratis: lee la consulta y la descripción juntas"),
             ("B", "Claude Opus como VLM", "ve la consulta y las fotos de los 10 candidatos, y los ordena")],
            "Los dos reordenan el mismo top-10. Métricas: hit@1 y MRR@10.",
            e7_res,
            "El reranking con VLM funciona, y nuestro paso choose ya es eso: Claude elige mirando las fotos. No agregamos un paso; la pregunta pasa a ser cuántos candidatos mostrarle.",
            (f"Mirando los resultados vimos que hit@10 era {f2(_b[2])} pero hit@1 {f2(_b[0])}: el producto correcto casi siempre está entre los 10 primeros, pero no primero. El cuello de botella era el orden. Advanced RAG propone un reranker, un segundo modelo que mira la consulta y cada candidato juntos. Queríamos ver si eso ordena mejor, y con qué tipo de modelo.",
             "Dos rerankers sobre el top-10: un cross-encoder MiniLM entrenado en MS MARCO, local y gratis, que lee la consulta y la descripción juntas; y Claude Opus como VLM, que ve la consulta y las fotos de los 10 candidatos y los ordena.",
             f"MiniLM empeora ({f2(_mi[0])}): está entrenado con preguntas y pasajes web, no con descripciones de muebles. El VLM sube hit@1 de {f2(_b[0])} a {f2(_op[0])} y MRR de {f2(_b[1])} a {f2(_op[1])}: mira la foto, que tiene lo que la descripción no dijo. Cuesta unos dos centavos de dólar por búsqueda.",
             "El reranking con VLM funciona, y nuestro paso choose ya es eso: Claude elige mirando las fotos de los candidatos. No agregamos un paso: la pregunta pasó a ser cuántos candidatos mostrarle, que es el experimento siguiente."),
            70)

# 25 · Exp 8 ------------------------------------------------------------------------------------------------------------------
_ks = sorted(D["curva"])
_ele = [D["curva"][k]["acierto_eleccion"] for k in _ks]
_tech = [D["curva"][k]["techo_hit@k"] for k in _ks]
_e3v, _e5v = D["curva"][3]["acierto_eleccion"], D["curva"][5]["acierto_eleccion"]
_e8_plano = next(k for k in _ks if abs(D["curva"][k]["acierto_eleccion"] - max(_ele)) < 1e-9)
e8_chart = lineas(_ks, [dict(ys=_tech, clase="punt", et="techo: el correcto está entre los k", et_dy=-4),
                        dict(ys=_ele, clase="sol", et="lo que elegiría el VLM", et_dy=14)], 1040, 540, 0.5, 0.92, [0.5, 0.6, 0.7, 0.8, 0.9],
                  xlab="k: candidatos por pieza", mr=300,
                  marcas=[(3, _e3v, f"k=3: {f3(_e3v)}", 0, 44, "middle", "base"), (5, _e5v, f"k=5: {f3(_e5v)}", 0, 44, "middle", "elegido")])
e8_res = f'<div class="res" data-paso="2">{e8_chart}<div class="res-nota">A partir de {_e8_plano} se aplana, y la distancia al techo crece: entre muchos parecidos, el VLM no siempre reconoce al correcto.</div></div>'
experimento(8, "Candidatos por pieza", "¿Cuántos candidatos le mostramos al VLM?",
            f"El paso choose ya es un reranker que mira fotos, pero le pasábamos 3 candidatos por pieza, y con 3 el correcto faltaba en el {pct(D['e8_falta3'])} de las piezas: una de cada cuatro. Más candidatos suben ese techo, pero son más fotos en la llamada: más caro, y más difícil elegir entre parecidos.",
            [("k", "De 1 a 10 candidatos", "lo que elegiría el VLM entre los primeros k = el mejor ordenado por él de esos k")],
            "Sale gratis del experimento anterior: no hay que pagar nada más. Es un proxy: el choose real además ve el ambiente y el pedido.",
            e8_res,
            f"{D['k_flujo']} candidatos por pieza: casi toda la mejora, y la llamada queda en {D['k_flujo'] * N_HERO} fotos para {N_HERO} piezas.",
            (f"El paso choose ya es un reranker que mira fotos, pero le pasábamos 3 candidatos por pieza, y con 3 el correcto faltaba en una de cada cuatro piezas. Más candidatos suben ese techo, pero son más fotos en la llamada: más caro, y más difícil elegir entre muchos parecidos. Queríamos encontrar el k que maximiza la chance de que el VLM elija bien.",
             "Lo sacamos gratis del experimento anterior: si el VLM ordenó el top-10, lo que elegiría entre los primeros k es el mejor ordenado de esos k. Así sale la curva para k de 1 a 10 sin pagar nada más. Es un proxy: el choose real además ve el ambiente y el pedido.",
             f"La línea punteada es el techo: que el correcto esté entre los k. La sólida es lo que elegiría el VLM. De 3 a 5 candidatos, la elección sube de {f3(_e3v)} a {f3(_e5v)}; a partir de {_e8_plano} se aplana. Y la distancia al techo crece: entre muchos parecidos, el VLM no siempre reconoce al correcto.",
             f"{D['k_flujo']} candidatos por pieza: casi toda la mejora, y la llamada queda en {D['k_flujo'] * N_HERO} fotos para {N_HERO} piezas."),
            68)

# 26 · Exp 9 -------------------------------------------------------------------------------------------------------------------
_e9 = D["e9"]
e9_res = f'''<div class="res" data-paso="2">
  {barras([dict(letra="A", et=f"{_e9[0][0]} productos", sub="sofás, sillones, mesas, alfombras", v=_e9[0][1], ic=ic(C268, BASE), tono="otro"),
           dict(letra="B", et=f"{_e9[1][0]} productos", sub="+ guardado, iluminación, textiles, deco", v=_e9[1][1], ic=ic(C855, BASE), tono="otro"),
           dict(letra="C", et=f"{_e9[2][0]} productos", sub="el ampliado, revisado", v=_e9[2][1], ic=ic(CREV, BASE), tono="elegido")], ancho=1040, titulo="hit@1", et_w=420, alto=50, sep=34)}
  <div class="res-nota aviso">Ojo: no son números directamente comparables. Cambia el universo, y las búsquedas ({_e9[0][2]} en A, {_e9[1][2]} en B y C): las nuevas son de deco, que es más difícil.</div>
</div>'''
experimento(9, "Catálogo: ampliación y revisión", "¿Cuánto cuesta ampliar el catálogo en retrieval, y qué cambia la limpieza?",
            f"El primer alcance eran sofás, sillones, mesas y alfombras: {D['prod_268']} productos. Con pedidos reales, la gente pide una biblioteca, una lámpara de pie, cortinas, y no había nada. Y al describir, los subagentes marcaron productos con la foto de otro o mal clasificados: la lista diría una cosa y la imagen mostraría otra.",
            [("A", f"{D['prod_268']} productos", "el primer alcance"),
             ("B", f"Ampliado a {D['prod_855']}", "guardado, iluminación, textiles y deco"),
             ("C", f"Revisado: {D['prod_819']}", f"{D['rev_afuera']} productos afuera y {D['rev_kinds']} kinds corregidos")],
            "Las mismas métricas sobre los tres catálogos.",
            e9_res,
            "Catálogo ampliado y revisado. Perder unos puntos de hit@1 es el precio de poder amoblar un living completo.",
            (f"El primer alcance eran sofás, sillones, mesas y alfombras: {D['prod_268']} productos. Con pedidos reales, la gente pide una biblioteca, una lámpara de pie, cortinas, y no había nada. Así que ampliamos. Y mientras los subagentes describían los productos, marcaron varios con la foto de otro producto o mal clasificados: la lista diría una cosa y la imagen mostraría otra. Queríamos saber cuánto cuesta ampliar en retrieval y qué cambia la limpieza.",
             f"Las mismas métricas sobre tres catálogos: el de {D['prod_268']}, el ampliado a {D['prod_855']} (guardado, iluminación, textiles y deco) y el revisado, con {D['rev_afuera']} productos afuera y {D['rev_kinds']} kinds corregidos.",
             f"Ampliar baja hit@1 de {f3(_e9[0][1])} a {f3(_e9[1][1])}: hay más productos parecidos y las búsquedas nuevas son de deco, que es más difícil. La revisión casi no lo cambia ({f3(_e9[1][1])} a {f3(_e9[2][1])}), pero hace que el producto de la lista sea el de la foto. Ojo: no son números directamente comparables, porque cambia el universo.",
             "Catálogo ampliado y revisado. Perder unos puntos de hit@1 es el precio de poder amoblar un living completo."),
            68)

# 27 · Exp 10 ------------------------------------------------------------------------------------------------------------------
_ja, _jt5, _jn, _jo = D["j_abo5"], D["j_tod5"], D["j_nord"], D["j_otros"]


def tiles_juez(res, a_lbl, b_lbl, b_cls):
    out = []
    for r in res["rows"]:
        nombre, estilo = ESTILO.get(r["slug"].replace("experimento-lectura", "experimento-lectura"), (r["slug"], ""))
        g = r["ganador"]
        cls = "t-a" if g == res_a(res) else (b_cls if g == res_b(res) else "t-emp")
        lbl = a_lbl if cls == "t-a" else (b_lbl if cls != "t-emp" else "empate")
        out.append(f'<div class="tj {cls}"><b>{nombre}</b><span>{estilo}</span><em>{lbl}</em></div>')
    return "".join(out)


def res_a(res):
    return "ikea"


def res_b(res):
    return next((x for r in res["rows"] for x in r["puntajes"] if x != "ikea"), "")


e10_resA = f'''<div class="res res-a" data-paso="2">
  <div class="marcador"><div class="mk-t">IKEA <b>{_ja["a"]}</b> – <b>{_ja["b"]}</b> Amazon</div><div class="mk-s">{_ja["emp"]} empate · nuestros {_ja["n"]} departamentos</div></div>
  <div class="tiles">{tiles_juez(_ja, "IKEA", "Amazon", "t-b")}</div>
  <div class="marcador"><div class="mk-t">IKEA <b>{_jt5["a"]}</b> – <b>{_jt5["b"]}</b> IKEA + Amazon</div><div class="mk-s">{_jt5["emp"]} empate · los mismos {_jt5["n"]}</div></div>
  <p class="res-nota">Según el juez, Amazon pierde por estilo: maderas oscuras, patas doradas para pedidos nórdicos.</p>
</div>'''
e10_resB = f'''<div class="res res-b" data-paso="3">
  <p class="res-nota giro">Los {_ja["n"]} pedidos eran nórdicos, justo la estética de IKEA. Sumamos {D["n_publicos"]} ambientes públicos reales con pedidos de otros estilos.</p>
  <div class="dos-marcadores">
    <div><div class="marcador"><div class="mk-t">IKEA <b>{_jn["a"]}</b> – <b>{_jn["b"]}</b> IKEA + Amazon</div><div class="mk-s">pedidos nórdicos · {_jn["emp"]} empate</div></div><div class="tiles">{tiles_juez(_jn, "IKEA", "IKEA + Amazon", "t-c")}</div></div>
    <div><div class="marcador"><div class="mk-t">IKEA <b>{_jo["a"]}</b> – <b>{_jo["b"]}</b> IKEA + Amazon</div><div class="mk-s">otros estilos</div></div><div class="tiles">{tiles_juez(_jo, "IKEA", "IKEA + Amazon", "t-c")}</div></div>
  </div>
  <div class="e10-cifras">
    <div><b>{f2(_jo["util_a"])} → {f2(_jo["util_b"])}</b>productos útiles (nota 2) en los otros estilos</div>
    <div><b>{pct(D["j_acuerdo"])}</b>de los ambientes: los dos órdenes del juez coinciden</div>
    <div><b>{f3(D["e10_gt_ikea"])} → {f3(D["e10_gt_todos"])}</b>hit@1 sobre el ground truth de IKEA al sumar Amazon</div>
  </div>
</div>'''
experimento(10, "Qué catálogo", "¿Con otro catálogo, o con los dos juntos, salen mejores listas para ambientes reales?",
            f"El catálogo de IKEA es de 2013, con fotos de {D['foto_lado']} píxeles, asientos sin medidas y una sola estética: la nórdica. Amazon Berkeley Objects (ABO) es un dataset académico con listados reales de Amazon, con medidas y fotos grandes.",
            [("A", "IKEA", f"{D['prod_819']} productos"),
             ("B", "Amazon (ABO)", f"{D['n_abo']} productos, descritos con el mismo formato"),
             ("C", "IKEA + Amazon", f"{D['prod_todos']} productos")],
            "Sin ground truth: nadie anotó qué sofá de Amazon va en un living vacío. De punta a punta, con los mismos ambientes, pedidos y plan; cambia solo el catálogo. Un juez (Claude Opus) ve la foto, el pedido y las dos listas sin saber de qué catálogo es cada una, y elige, en los dos órdenes: una variante gana un ambiente solo si gana en los dos.",
            e10_resA + e10_resB,
            "Usamos los dos catálogos. Y la lección: con ambientes y pedidos poco variados, habríamos tomado la decisión contraria.",
            (f"El catálogo de IKEA tiene límites: es de 2013, las fotos son de {D['foto_lado']} píxeles, los asientos no tienen medidas y tiene una sola estética, la nórdica. Encontramos Amazon Berkeley Objects, un dataset académico con listados reales de Amazon, con medidas y fotos grandes. Queríamos ver si con otro catálogo, o con los dos juntos, salen mejores listas para ambientes reales.",
             "Acá no hay ground truth: nadie anotó qué sofá de Amazon va en un living vacío. Comparamos de punta a punta: mismos ambientes, mismos pedidos y el mismo plan; cambia solo el catálogo. Un juez, Claude Opus, ve la foto, el pedido y las dos listas sin saber de qué catálogo es cada una, y elige. Se le pregunta en los dos órdenes, y una variante gana un ambiente solo si gana en los dos. Primero lo corrimos en nuestros 5 departamentos.",
             f"(Flecha: primera parte.) IKEA le gana a Amazon {_ja['a']} a {_ja['b']}; según el juez, Amazon pierde por estilo (maderas oscuras, patas doradas para pedidos nórdicos). Y IKEA + Amazon empataba con IKEA, {_jt5['a']} a {_jt5['b']}. (Flecha: segunda parte.) Ahí vimos que los {_ja['n']} pedidos eran nórdicos, justo la estética de IKEA, así que sumamos {D['n_publicos']} ambientes públicos reales con pedidos de otros estilos: industrial, clásico, bohemio. En los nórdicos siguen empatados, {_jn['a']} a {_jn['b']}; en los otros estilos, IKEA + Amazon gana {_jo['b']} a {_jo['a']}, y los productos útiles pasan de {f2(_jo['util_a'])} a {f2(_jo['util_b'])}. Los dos órdenes del juez coinciden en el {pct(D['j_acuerdo'])} de los ambientes. Y sumar Amazon casi no cambia el retrieval sobre el ground truth de IKEA: hit@1 de {f3(D['e10_gt_ikea'])} a {f3(D['e10_gt_todos'])}.",
             "Usamos los dos catálogos. Y la lección: con ambientes y pedidos poco variados habríamos tomado la decisión contraria."),
            110, riel_map=(0, 1, 2, 2, 3), dec_paso=4, clase_extra="e10")

# 28 · Exp 11 ------------------------------------------------------------------------------------------------------------------
_rep = D["rep"]
rep_svg_w = 1040


def rep_svg():
    x0, x1 = 330, 960
    lo, hi = 0.45, 0.62
    sx = lambda v: x0 + (x1 - x0) * (v - lo) / (hi - lo)  # noqa: E731
    out = [f'<svg class="graf" viewBox="0 0 {rep_svg_w} 110" width="{rep_svg_w}" height="110">',
           '<text x="0" y="62" class="g-et">Tres redactores</text><text x="0" y="88" class="g-sub">hit@1 de cada uno</text>',
           f'<line x1="{x0}" y1="56" x2="{x1}" y2="56" class="g-grilla"/>']
    for t in (0.45, 0.5, 0.55, 0.6):
        out.append(f'<text x="{sx(t)}" y="100" class="g-eje" text-anchor="middle">{f2(t)}</text><line x1="{sx(t)}" y1="48" x2="{sx(t)}" y2="64" class="g-grilla"/>')
    mu = statistics.mean(_rep)
    out.append(f'<rect x="{sx(mu - D["rep_sd"])}" y="40" width="{sx(mu + D["rep_sd"]) - sx(mu - D["rep_sd"])}" height="32" class="g-banda"/>')
    for v in _rep:
        out.append(f'<circle cx="{sx(v)}" cy="56" r="10" class="g-punto-rep"/>')
    out.append(f'<text x="{sx(mu)}" y="28" class="g-marca-t elegido" text-anchor="middle">± {f"{D["rep_sd"] * 100:.1f}".replace(".", ",")} puntos (desvío)</text>')
    out.append("</svg>")
    return "".join(out)


e11_res = f'''<div class="res" data-paso="2">
  {barras([dict(et="Al producto anotado", v=D['g_anot2'], tono="elegido", vtxt=pct(D['g_anot2'])),
           dict(et="A los demás candidatos", v=D['g_otros2'], tono="otro", vtxt=pct(D['g_otros2']))], ancho=1040, titulo="Validación: ¿cuántas veces el juez pone un 2?", et_w=330, alto=38, sep=18, fmt=pct)}
  {barras([dict(et="hit@1 (ground truth)", v=D['g_hit1'], ic=D['g_hit1_ic'], tono="otro"),
           dict(et="El 1.º sirve (nota 1 o 2)", v=D['g_util1'], ic=D['g_util1_ic'], tono="elegido")], ancho=1040, titulo=f"Las mismas {D['g_n']} búsquedas: el ground truth subestima", et_w=330, alto=38, sep=18, eje=False)}
  {rep_svg()}
</div>'''
experimento(11, "¿Cuánto mide el ground truth?", "Si el sistema trae un sillón casi igual al anotado, ¿se equivocó? ¿Y si las búsquedas las escribiera otro?",
            "Todos los números hasta acá son contra un ground truth con un solo producto correcto por pieza. Y las búsquedas de evaluación las escribieron subagentes: si las escribiera otro, ¿cambiaría el número?",
            [("A", f"Un juez califica el top-3 de {D['g_n']} búsquedas", "2 si es el mismo o indistinguible, 1 si es una alternativa aceptable, 0 si no sirve; antes de creerle, lo validamos contra el ground truth"),
             ("B", "Tres redactores independientes", "escriben las mismas búsquedas")],
            "Métricas: acuerdo del juez con el anotado, útil@1 contra hit@1, y la dispersión de hit@1 entre redactores.",
            e11_res,
            "Reportamos hit@1 para comparar métodos, porque es objetivo y barato, y la relevancia graduada para saber cuán útil es de verdad.",
            ("Todos los números hasta acá son contra un ground truth con un solo producto correcto por pieza. Pero si el sistema trae un sillón casi igual al anotado, ¿se equivocó? Y las búsquedas de evaluación las escribieron subagentes: si las escribiera otro, ¿cambiaría el número? Queríamos saber cuánto mide realmente el ground truth.",
             f"Dos cosas. Un juez califica el top-3 de {D['g_n']} búsquedas: 2 si es el mismo o indistinguible, 1 si es una alternativa aceptable, 0 si no sirve; antes de creerle, lo validamos contra el ground truth. Y tres redactores independientes escribieron las mismas búsquedas.",
             f"El juez le da 2 al producto anotado el {pct(D['g_anot2'])} de las veces y a los demás el {pct(D['g_otros2'])}: es confiable. Con él, el primer candidato sirve en el {pct(D['g_util1'])} de los casos, aunque hit@1 en esas mismas búsquedas sea {f2(D['g_hit1'])}: el ground truth subestima. Con tres redactores, hit@1 varía unos {f'{D['rep_sd'] * 100:.1f}'.replace('.', ',')} puntos: diferencias más chicas que eso entre métodos no son señal.",
             "Reportamos hit@1 para comparar métodos, porque es objetivo y barato, y la relevancia graduada para saber cuán útil es de verdad."),
            70)

# 29 · Exp 12 --------------------------------------------------------------------------------------------------------------------
E12_VAR = [("A", "experimento", "Escena guiada", "el LLM describe dónde va cada cosa"),
           ("B", "experimento-libre", "Escena libre", "el modelo de imagen acomoda"),
           ("C", "experimento-buen-pedido", "Libre y sin tope de piezas", "todas las piezas del pedido"),
           ("D", "experimento-buen-pedido-estricto", "Edición estricta", "mismo encuadre, paredes y aberturas; solo los productos de las fotos")]
_e12_cards = []
for l, run, t, _d in E12_VAR:
    inl, ssim = D["e12"][run]
    ok = inl >= ROOM_CHECK["min_inliers"]
    _e12_cards.append(f'<figure class="e12-c{" mal" if not ok else ""}{" elegida" if l == "D" else ""}">{foto("e12-" + run, AM / run / "final.png", 330, 248, q=78)}'
                      f'<figcaption>{chip(l)}<div class="e12-t"><span class="e12-n"><b>{inl}</b> puntos SIFT</span><span class="e12-s">SSIM fuera de los muebles {f2(ssim)}</span></div></figcaption></figure>')
e12_extra = f'<div class="e12-motivo">{foto("hero-room-e12", HERO / "room.jpg", 160, 120)}<span class="v-flecha">→</span>{foto("e12-experimento-buen-pedido-sm", AM / "experimento-buen-pedido" / "final.png", 160, 120)}<span class="e12-mt">inventó una ventana y movió la biblioteca</span></div>'
e12_res = f'''<div class="res" data-paso="2"><div class="e12-grilla">{"".join(_e12_cards)}</div>
<div class="res-nota">C, libre y sin tope: linda, pero inventó una ventana, y SIFT lo detecta: reencuentra solo {D["e12"]["experimento-buen-pedido"][0]} puntos. D conserva el cuarto, y la biblioteca es la que se pidió.</div></div>'''
experimento(12, "La imagen: del cuarto reimaginado al cuarto del cliente", "¿Cómo pedirle al modelo que respete el ambiente, y cómo detectar cuándo no lo hace?",
            "Al generar imágenes vimos que el modelo no solo agregaba los muebles: redecoraba. Para el usuario eso no sirve: quiere ver su cuarto con esos productos.",
            [(l, t, d) for l, _, t, d in E12_VAR],
            f"Mismo ambiente; arriba (A, B) con el pedido corto ({D['e12_piezas']['experimento']} piezas), abajo (C, D) con el pedido completo ({D['e12_piezas']['experimento-buen-pedido']} piezas, sin tope). Métricas: puntos SIFT reencontrados y SSIM fuera de los muebles.",
            e12_res,
            f"Edición estricta y un control automático: si SIFT no reencuentra el cuarto (al menos {ROOM_CHECK['min_inliers']} puntos), la imagen se descarta y se reintenta, hasta {ROOM_CHECK['attempts']} veces.",
            ("Cuando empezamos a generar imágenes vimos que el modelo no solo agregaba los muebles: redecoraba. En este ejemplo inventó una ventana y movió la biblioteca. Para el usuario eso no sirve: quiere ver su cuarto con esos productos. Queríamos encontrar cómo pedirle al modelo que respete el ambiente, y cómo detectar automáticamente cuando no lo hace.",
             f"El mismo ambiente, cuatro versiones del paso de la imagen; las dos de arriba con el pedido corto ({D['e12_piezas']['experimento']} piezas) y las dos de abajo con el pedido completo ({D['e12_piezas']['experimento-buen-pedido']} piezas, sin tope): una escena que escribe el LLM describiendo dónde va cada cosa; una escena libre; libre y sin tope de piezas; y una edición estricta, que exige el mismo encuadre, las mismas paredes y aberturas y exactamente los productos de las fotos. Medimos con SIFT cuántos puntos de la foto original se reencuentran, y SSIM fuera de los muebles.",
             f"Arriba, las dos primeras conservan el cuarto ({D['e12']['experimento'][0]} y {D['e12']['experimento-libre'][0]} puntos) pero la biblioteca queda chica. Abajo a la izquierda, libre y sin tope: linda, pero inventó una ventana; SIFT lo detecta, reencuentra solo {D['e12']['experimento-buen-pedido'][0]} puntos. La edición estricta conserva el cuarto, con {D['e12']['experimento-buen-pedido-estricto'][0]} puntos, y la biblioteca es la que se pidió.",
             f"Edición estricta y un control automático: si SIFT no reencuentra el cuarto, la imagen se descarta y se reintenta, hasta {ROOM_CHECK['attempts']} veces. En la slide siguiente se ve funcionando."),
            84, porque_extra=e12_extra, clase_extra="e12")

# 30 · Separador: Cierre ----------------------------------------------------------------------------------------------------------
slide("sep-cierre", "Parte 5: Cierre", "Cierre", separador(5, "Todo junto en un departamento real, lo que aprendimos y lo que falta.", ["De punta a punta", "La iteración", "El camino", "Costos", "Limitaciones", "Conclusiones"]),
      "Para cerrar: todo junto en un departamento real, lo que aprendimos en el camino y lo que falta.", 10, clase="oscura separador")

# 31 · De punta a punta ------------------------------------------------------------------------------------------------------------
def intentos(run: str, res: dict, ancho: int, alto: int):
    out = []
    for i, a in enumerate(res["attempts"], 1):
        ok = a["ok"]
        sello = (f'<span class="sello ok"><b>Queda</b>{a["sift_inliers"]} puntos reencontrados</span>' if ok else
                 f'<span class="sello no"><b>Descartada</b>{a["sift_inliers"]} puntos · cámara corrida {pct(a["sift_desplazamiento_mediano"])}</span>')
        out.append(f'<figure class="intento">{foto(f"{run}-int{i}", AM / run / a["image"], ancho, alto, q=78)}{sello}<figcaption>Intento {i}</figcaption></figure>')
    return "".join(out)


_com_choice = jload(AM / "caballito-comedor" / "3_choice.json")["answer"]["choices"]
_com_cand = {c["id"]: c for p in jload(AM / "caballito-comedor" / "2_candidates.json")["pieces"] for c in p["candidates"]}
_com_lista = "".join(f'<li>{producto(ch["id"], 64)}<span>{KIND_ES.get(_com_cand[ch["id"]].get("kind"), _com_cand[ch["id"]].get("kind"))}{" ×" + str(ch["quantity"]) if ch["quantity"] > 1 else ""}</span></li>' for ch in _com_choice)
slide("e2e", "De punta a punta", "Cierre · resultado", cab("Resultado", "De punta a punta, en un departamento real") + f'''
<div class="e2e-fila">
  <div class="e2e-et"><b>Living</b><span>con la configuración final</span></div>
  <figure class="intento">{foto("cab-living-room-sm", AM / "caballito-living" / "room.jpg", 372, 279)}<figcaption>La foto</figcaption></figure>
  {intentos("caballito-living", D["cab_liv"], 372, 279)}
</div>
<div class="e2e-fila">
  <div class="e2e-et"><b>Comedor</b><span>pasó al primer intento</span></div>
  <figure class="intento">{foto("cab-com-room-sm", AM / "caballito-comedor" / "room.jpg", 372, 279)}<figcaption>La foto</figcaption></figure>
  {intentos("caballito-comedor", D["cab_com"], 372, 279)}
  <div class="e2e-lista"><span class="mini-et">La lista</span><ul>{_com_lista}</ul></div>
</div>''',
      f"Y así queda todo junto, con la configuración final, en un departamento real. En el living, los dos primeros intentos de la imagen salieron lindos pero con la cámara corrida (SIFT reencontró {D['cab_liv']['attempts'][0]['sift_inliers']} y {D['cab_liv']['attempts'][1]['sift_inliers']} puntos), y el control los descartó solo; el tercero quedó. El comedor pasó al primer intento.",
      48)

# 32 · La iteración (Ejercicio 4) -------------------------------------------------------------------------------------------------------
ITER = [
    ("En un ambiente vacío no hay nada que recortar", "Búsqueda por texto (v1)", f"hit@1 {f2(D['v0_hit1'])} → {f2(D['v1_hit1'])}"),
    ("El texto del vendedor no describe lo que se ve", "Descripción de 8 líneas con un VLM", f"hit@1 {f2(D['e1_vendedor'])} → {f2(D['e1_desc'])}"),
    ("Una consulta corta no distingue un sofá de otro", "La consulta completa que escribe el plan", f"hit@1 {f2(D['e6_kind'])} → {f2(D['e6_hnsw'])}"),
    ("El correcto estaba en el top-10, pero no primero", "Un VLM elige mirando las fotos", f"hit@1 {f2(_b[0])} → {f2(_op[0])}"),
    ("Con 3 candidatos faltaba el correcto en 1 de cada 4 piezas", f"{D['k_flujo']} candidatos por pieza", f"elección {f3(_e3v)} → {f3(_e5v)}"),
    ("Pedían bibliotecas, lámparas y cortinas, y no había", "Catálogo ampliado y revisado", f"{D['prod_268']} → {D['prod_819']} productos"),
    ("Una sola estética: la nórdica", "IKEA + Amazon", f"otros estilos {_jo['b']} a {_jo['a']}; útiles {f2(_jo['util_a'])} → {f2(_jo['util_b'])}"),
    ("La imagen redecoraba el cuarto", "Edición estricta + control SIFT", f"puntos SIFT {D['e12']['experimento-buen-pedido'][0]} → {D['e12']['experimento-buen-pedido-estricto'][0]}"),
]
filas_it = "".join(f'<div class="it-p">{p}</div><div class="it-c">{c}</div><div class="it-m">{mj}</div>' for p, c, mj in ITER)
slide("iteracion", "La iteración", "Cierre · ejercicio 4", cab("Ejercicio 4", "La iteración: qué falló, qué cambiamos y cuánto mejoró") + f'''
<div class="iter"><div class="h-cab">El problema que encontramos usando el sistema</div><div class="h-cab">Qué cambiamos</div><div class="h-cab">Cuánto mejoró</div>{filas_it}</div>''',
      "Esto es el ejercicio 4 en una tabla: cada fila es un problema que encontramos usando el sistema, el cambio que hicimos y cuánto mejoró. Todos salen de los experimentos que acabamos de ver.",
      42)

# 33 · El camino ----------------------------------------------------------------------------------------------------------------------------
def camino_svg():
    W, H = 1744, 600
    n = len(D["camino"])
    bw = 220
    gap = (W - 120 - n * bw) / (n - 1)
    sy = lambda v: 520 - 440 * v / 0.8  # noqa: E731
    out = [f'<svg class="graf" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    for t in (0, 0.2, 0.4, 0.6, 0.8):
        out.append(f'<line x1="80" y1="{sy(t)}" x2="{W}" y2="{sy(t)}" class="g-grilla"/><text x="66" y="{sy(t) + 6}" class="g-eje" text-anchor="end">{f2(t)}</text>')
    prev = None
    for i, (et, v) in enumerate(D["camino"]):
        x = 120 + i * (bw + gap)
        cls = C_ELEGIDO if i == n - 1 else (C_ROBLE if i else C_OTRO)
        out.append(f'<rect x="{x}" y="{sy(v)}" width="{bw}" height="{sy(0) - sy(v)}" fill="{cls}" rx="2"/>')
        out.append(f'<text x="{x + bw / 2}" y="{sy(v) - 16}" class="g-val grande{" elegido" if i == n - 1 else ""}" text-anchor="middle">{f2(v)}</text>')
        palabras = et.split(" ")
        l1, l2 = [], []
        for w_ in palabras:
            (l1 if len(" ".join(l1 + [w_])) <= 20 and not l2 else l2).append(w_)
        out.append(f'<text x="{x + bw / 2}" y="{sy(0) + 34}" class="g-et" text-anchor="middle">{" ".join(l1)}</text>')
        if l2:
            out.append(f'<text x="{x + bw / 2}" y="{sy(0) + 62}" class="g-et" text-anchor="middle">{" ".join(l2)}</text>')
        if prev is not None:
            d = v - prev
            xm = x - gap / 2
            out.append(f'<text x="{xm}" y="{sy(max(v, prev)) - 70}" class="g-delta" text-anchor="middle">{"+" if d >= 0 else "−"}{f2(abs(d))}</text>')
            out.append(f'<path d="M{xm - 30} {sy(max(v, prev)) - 56} L{xm + 30} {sy(max(v, prev)) - 56} M{xm + 20} {sy(max(v, prev)) - 64} L{xm + 30} {sy(max(v, prev)) - 56} L{xm + 20} {sy(max(v, prev)) - 48}" class="g-flecha"/>')
        prev = v
    out.append("</svg>")
    return "".join(out)


slide("camino", "El camino", "Cierre · resumen", cab("Resumen de los experimentos", f"El camino: de {f2(D['camino'][0][1])} a {f2(D['camino'][-1][1])} de hit@1") + f'''
<div class="camino">{camino_svg()}</div>
<p class="remate chico">Lo que más movió el número fue <b>qué texto se indexa</b>; lo segundo, que <b>un VLM mire las fotos</b>.</p>''',
      f"El resumen en un gráfico: cada barra suma un cambio a la anterior. Del texto del vendedor con una bolsa de palabras ({f2(D['camino'][0][1])}) al VLM reordenando el top-10 ({f2(D['camino'][-1][1])}). El filtro por tipo no mueve hit@1: lo que protege es hit@10. Lo que más movió el número fue qué texto se indexa; lo segundo, que un VLM mire las fotos.",
      42)

# 34 · Costos ------------------------------------------------------------------------------------------------------------------------------------
slide("costo", "Cuánto cuesta", "Cierre · costo", cab("Costo", "Cuánto cuesta un pedido") + f'''
<div class="recibo">
  <div class="rc-cab"><b>amoblai</b><span>un pedido, con la configuración final</span></div>
  <div class="rc-l"><span>Plan + choose · Claude Opus</span><i></i><b>{usd(D['costo_claude'])}</b></div>
  <div class="rc-l"><span>Imagen · Nano Banana 2, por intento</span><i></i><b>{usd(D['costo_imagen'])}</b></div>
  <div class="rc-l"><span>Embeddings y base vectorial · locales</span><i></i><b>{usd(0)}</b></div>
  <div class="rc-sep"></div>
  <div class="rc-l chico"><span>Costo único: describir el catálogo, por producto</span><i></i><b>{usd(D['costo_describir'], 3)}</b></div>
  <div class="rc-pie">promedio de plan + choose en los {len(_cp)} ambientes de la evaluación de punta a punta</div>
</div>
<div class="costo-notas">
  <div><h4>Todo gasto queda registrado</h4><p>Cada llamada paga, con su costo, y con topes por cuenta: lo que pase el tope se rechaza.</p></div>
  <div><h4>Repetir no se vuelve a pagar</h4><p>Las respuestas de los jueces y los rerankers quedan en caché.</p></div>
  <div><h4>Menos de un centavo por producto</h4><p>Describir el catálogo se paga una sola vez.</p></div>
</div>''',
      f"Un pedido cuesta unos {round(D['costo_claude'] * 100)} centavos de dólar de Claude y {round(D['costo_imagen'] * 100)} por intento de imagen. Describir el catálogo es un costo único, de menos de un centavo por producto. Embeddings y base vectorial corren locales. Todo gasto queda registrado, con topes por cuenta, y las respuestas de los jueces quedan en caché: repetir un experimento no se vuelve a pagar.",
      30)

# 35 · Limitaciones y trabajo futuro ------------------------------------------------------------------------------------------------------------
LIM = ["Los catálogos son viejos y de uso no comercial", "Las medidas del ambiente se estiman a ojo",
       "El ground truth es uno solo, con consultas escritas por modelos", "La imagen es una visualización: escala y luz aproximadas",
       "Tenemos pocos ambientes vacíos"]
FUT = ["Medidas reales: un metro en la foto o un modelo de profundidad", "El catálogo de un vendedor actual, con precio y stock",
       "Más ambientes y evaluación humana", "Que el usuario cambie una pieza y se regenere solo eso"]
slide("limites", "Limitaciones y futuro", "Cierre", cab("Cierre", "Limitaciones y trabajo futuro") + f'''
<div class="dos-listas">
  <div><h3>Limitaciones</h3><ul class="lista-lim">{"".join(f"<li>{x}</li>" for x in LIM)}</ul></div>
  <div><h3>Trabajo futuro</h3><ul class="lista-fut">{"".join(f"<li>{x}</li>" for x in FUT)}</ul></div>
</div>''',
      "Limitaciones: los catálogos son viejos y de uso no comercial; las medidas del ambiente se estiman a ojo; el ground truth es uno solo y con consultas escritas por modelos; la imagen es una visualización, con escala y luz aproximadas; y tenemos pocos ambientes vacíos. Como trabajo futuro: medidas reales, con un metro en la foto o un modelo de profundidad; el catálogo de un vendedor actual, con precio y stock; más ambientes y evaluación humana; y que el usuario pueda cambiar una pieza y regenerar solo eso.",
      48)

# 36 · Conclusiones ------------------------------------------------------------------------------------------------------------------------
CONC = [
    ("Lo que más importó fue el texto que se indexa,", "no el modelo."),
    ("El mejor reranker es un VLM mirando las fotos,", "y nuestro paso de elegir ya lo es."),
    ("Las métricas con ground truth subestiman:", "hace falta un juez, validado y preguntado en los dos órdenes."),
    ("El catálogo decide qué se puede recomendar,", "y evaluar con ambientes variados cambió la decisión."),
    ("La imagen necesita un control automático", "para que el cuarto sea el del cliente."),
]
slide("conclusiones", "Conclusiones", "Cierre", f'''
<div class="conc-txt">
  <div class="kicker">Conclusiones</div>
  <ol class="conc">{"".join(f"<li><span><b>{a}</b> {b}</span></li>" for a, b in CONC)}</ol>
  <div class="gracias">Gracias.</div>
  <div class="equipo-pie">Juan Bautista Albertoni Salini · Matias Juan Rossi Seifert · Junior Rambau</div>
</div>
<div class="conc-foto">{foto("hero-final-conc", HERO / "final.png", 700, 1080, q=80)}</div>''',
      "Para cerrar, cinco cosas. Lo que más importó fue el texto que se indexa, no el modelo. El mejor reranker es un VLM mirando las fotos, y nuestro paso de elegir ya lo es. Las métricas con ground truth subestiman, así que hace falta un juez, validado y preguntado en los dos órdenes. El catálogo decide qué se puede recomendar, y evaluar con ambientes variados cambió la decisión. Y la imagen necesita un control automático para que el cuarto sea el del cliente. Gracias.",
      60, clase="oscura conclusiones")


# =============================================================================================
# HTML
# =============================================================================================

CSS = r"""
:root{
  --yeso:#F1ECE3; --papel:#FBF8F2; --lino:#E7DFD2; --hilo:#D8CDBD; --hilo-2:#BCAF9B;
  --tinta:#2A211B; --tinta-2:#5E5148; --tinta-3:#8C7E71;
  --roble:#B4864F; --roble-claro:#E2C9A3;
  --terracota:#A94E2B; --terracota-claro:#F2DED2;
  --salvia:#566B4E; --salvia-claro:#DFE5D6;
  --noche:#211914; --noche-2:#2F241D; --crema:#EFE6D8;
  --serif:'Vitrina','Noto Serif Display',Georgia,serif;
  --sans:'Ficha','Cabin','Helvetica Neue',sans-serif;
  --mono:'Cota','Go Mono',ui-monospace,monospace;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:#16110d;overflow:hidden}
body{font-family:var(--sans);color:var(--tinta);-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
h1,h2,h3,h4,p,ul,ol,figure,blockquote,dl,dd{margin:0;padding:0}
ul,ol{list-style:none}
#escenario{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:0 0;overflow:hidden;background:var(--yeso)}
.slide{position:absolute;inset:0;width:1920px;height:1080px;overflow:hidden;background:var(--yeso);color:var(--tinta);text-align:left;opacity:0;visibility:hidden;
  transition:opacity .35s ease,visibility 0s linear .35s;padding:64px 88px 0}
.slide.activa{opacity:1;visibility:visible;transition:opacity .35s ease}
.slide.oscura{background:var(--noche);color:var(--crema)}
.foto{background-size:cover;background-position:center;background-repeat:no-repeat;background-color:var(--lino);flex:none}
.prod{background-size:contain;background-position:center;background-repeat:no-repeat;mix-blend-mode:multiply;flex:none}
.prod.con-borde{background-color:#fff;mix-blend-mode:normal;border:1px solid var(--hilo);background-origin:content-box;padding:6px}
[data-paso]{opacity:0;transform:translateY(14px);transition:opacity .4s ease,transform .4s ease}
[data-paso].visto{opacity:1;transform:none}
[data-hasta]{transition:opacity .3s ease}
[data-hasta].oculto{opacity:0;pointer-events:none}
.todo [data-paso]{opacity:1!important;transform:none!important}
.todo [data-hasta]{opacity:0!important}
code{font-family:var(--mono);font-size:.86em;background:var(--lino);padding:1px 6px;border-radius:3px}

/* cabecera */
.kicker{font:600 22px/1.2 var(--sans);color:var(--terracota);letter-spacing:.01em}
.oscura .kicker{color:var(--roble-claro)}
.titulo{font:400 62px/1.08 var(--serif);letter-spacing:-.012em;margin-top:10px;max-width:1700px;text-wrap:balance}
.bajada{font:italic 400 32px/1.25 var(--serif);color:var(--tinta-2);margin-top:10px;max-width:1500px}
.cab{margin-bottom:34px}
.mini-et{font:600 19px/1.25 var(--sans);color:var(--tinta-3);margin-bottom:12px}
.b-et{font:600 21px/1.2 var(--sans);color:var(--terracota);margin-bottom:10px}
.remate{font:italic 400 34px/1.3 var(--serif);color:var(--tinta);max-width:1600px}
.remate.chico{font-size:30px}
.cod{font:400 16px/1.2 var(--mono);color:var(--tinta-3)}
.num{display:inline-grid;place-items:center;width:44px;height:44px;border:1.5px solid var(--terracota);color:var(--terracota);border-radius:50%;font:400 24px/1 var(--serif);margin-right:16px;flex:none}

/* HUD */
#hud{position:absolute;left:88px;right:88px;bottom:18px;display:flex;justify-content:space-between;font:400 17px/1 var(--sans);color:var(--tinta-3);z-index:5;pointer-events:none}
#hud.sobre-oscuro{color:rgba(239,230,216,.5)}
#barra{position:absolute;left:0;bottom:0;height:5px;background:var(--roble);transition:width .35s ease;z-index:6}

/* portada */
.portada{padding:0}
.portada-foto{position:absolute;right:0;top:0;width:1040px;height:1080px}
.portada-foto .inset{position:absolute;left:-150px;bottom:110px;background:var(--papel);padding:12px 12px 10px;box-shadow:0 18px 40px -18px rgba(33,25,20,.55);transform:rotate(-2deg)}
.inset figcaption{font:italic 400 20px/1.2 var(--serif);color:var(--tinta-2);margin-top:8px}
.cota-foto{position:absolute;left:40px;right:40px;top:84px;height:2px;background:rgba(251,248,242,.85)}
.cota-foto::before,.cota-foto::after{content:"";position:absolute;top:-9px;width:2px;height:20px;background:rgba(251,248,242,.85);transform:rotate(45deg)}
.cota-foto::before{left:0}.cota-foto::after{right:0}
.cota-foto span{position:absolute;left:50%;top:-40px;transform:translateX(-50%);white-space:nowrap;font:600 21px/1 var(--sans);color:#fff;text-shadow:0 1px 8px rgba(0,0,0,.5)}
.portada-txt{position:absolute;left:96px;top:120px;width:680px}
.marca{font:400 196px/0.95 var(--serif);letter-spacing:-.03em;margin:40px 0 36px;color:var(--tinta)}
.portada-preg{font:400 42px/1.22 var(--serif);color:var(--tinta-2)}
.portada-preg em{color:var(--terracota)}
.equipo{margin-top:70px;display:grid;gap:8px;font:400 27px/1.25 var(--sans)}
.equipo li::before{content:"";display:inline-block;width:22px;height:1.5px;background:var(--roble);vertical-align:middle;margin-right:14px}

/* problema */
.tres-paneles{display:grid;grid-template-columns:repeat(3,540px);gap:62px}
.panel figcaption{font:400 25px/1.3 var(--sans);color:var(--tinta-2);margin-top:16px}
.panel figcaption b{color:var(--tinta);font-weight:600}
.catalogo-hoja{width:540px;height:420px;background:#fff;display:grid;grid-template-columns:repeat(3,1fr);place-items:center;padding:20px;border:1px solid var(--hilo)}
.catalogo-hoja .prod{mix-blend-mode:normal}
.panel.tuyo .foto{outline:3px solid var(--terracota);outline-offset:6px}
.preguntas3{display:grid;grid-template-columns:repeat(3,540px);gap:62px;margin-top:64px;padding-top:40px;border-top:1px solid var(--hilo)}
.preguntas3 div{display:flex;align-items:center;font:400 34px/1.2 var(--serif)}

/* producto */
.et-flujo{font:italic 400 30px/1 var(--serif);color:var(--terracota);margin-bottom:14px}
.prod-entra{position:absolute;left:88px;top:232px;width:470px}
.pedido{font:italic 400 21px/1.4 var(--serif);color:var(--tinta-2);margin-top:20px;border-left:3px solid var(--roble);padding-left:18px}
.prod-flecha{position:absolute;left:574px;top:420px;width:70px}
.prod-flecha path{fill:none;stroke:var(--terracota);stroke-width:3}
.prod-sale{position:absolute;left:660px;top:232px;width:780px}
.pie{font:400 21px/1.3 var(--sans);color:var(--tinta-3);margin-top:12px}
.prod-lista{position:absolute;left:1476px;top:232px;width:356px}
.lista-cab{border-bottom:2px solid var(--tinta);padding-bottom:10px;margin-bottom:6px;display:flex;flex-direction:column;gap:4px;margin-top:44px}
.lista-cab b{font:400 30px/1 var(--serif)}
.lista-cab span{font:400 17px/1.2 var(--sans);color:var(--tinta-3)}
.lista li{display:flex;align-items:center;gap:12px;padding:5px 0;border-bottom:1px solid var(--hilo)}
.l-txt{flex:1;display:flex;flex-direction:column;gap:3px;min-width:0}
.l-txt b{font:600 21px/1.1 var(--sans)}
.l-txt .cod{font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cant{font:400 24px/1 var(--serif);color:var(--terracota)}

/* por qué RAG */
.tres-col{display:grid;grid-template-columns:1fr 1fr 1.25fr;gap:40px}
.col-rag{background:var(--papel);border:1px solid var(--hilo);padding:34px 36px 36px;min-height:440px;display:flex;flex-direction:column}
.col-rag h3{font:400 34px/1.15 var(--serif);margin-bottom:16px}
.col-rag p{font:400 26px/1.35 var(--sans);color:var(--tinta-2)}
.col-rag.elegida{border:2px solid var(--terracota);background:#fff}
.ticket-falso{margin-top:auto;border:1.5px dashed var(--hilo-2);padding:18px 22px;display:flex;flex-direction:column;gap:6px;background:var(--yeso)}
.tf-et{font:400 17px/1 var(--mono);color:var(--tinta-3)}
.ticket-falso b{font:600 26px/1.2 var(--sans);text-decoration:line-through;text-decoration-color:var(--terracota);text-decoration-thickness:3px}
.ticket-falso.vacio-lista b{text-decoration:none;color:var(--tinta-3)}
.tf-cod{font:400 18px/1.2 var(--sans);color:var(--terracota)}
.flujo-rag{counter-reset:f;display:grid;gap:16px;margin-top:4px}
.flujo-rag li{counter-increment:f;display:grid;grid-template-columns:44px 1fr;align-items:center;font:400 26px/1.25 var(--sans);color:var(--tinta-2)}
.flujo-rag li::before{content:counter(f);width:34px;height:34px;border-radius:50%;background:var(--terracota);color:#fff;display:grid;place-items:center;font:600 18px/1 var(--sans)}
.flujo-rag b{color:var(--tinta);font-weight:600}
.slide .remate{margin-top:44px}

/* separadores */
.separador{padding:0}
.sep-txt{position:absolute;left:96px;top:150px;width:720px}
.sep-parte{font:600 24px/1 var(--sans);color:var(--roble-claro)}
.sep-titulo{font:400 112px/1 var(--serif);letter-spacing:-.025em;margin:22px 0 30px;color:var(--crema)}
.sep-desc{font:400 32px/1.3 var(--sans);color:rgba(239,230,216,.78);max-width:660px}
.sep-desc.chica{font-size:24px;margin-top:26px;color:rgba(239,230,216,.6)}
.sep-lista{margin-top:46px;display:grid;gap:12px;counter-reset:s}
.sep-lista li{font:italic 400 30px/1.2 var(--serif);color:rgba(239,230,216,.9);counter-increment:s}
.sep-lista li::before{content:"";display:inline-block;width:28px;height:1.5px;background:var(--roble);vertical-align:middle;margin-right:16px}
.sep-plano{position:absolute;right:70px;top:120px;width:1000px;height:800px}
.plano{width:100%;height:100%;overflow:visible}
.plano .pared{fill:none;stroke:var(--crema);stroke-width:14}
.plano .pared-int{fill:none;stroke:var(--crema);stroke-width:7}
.plano .puerta{fill:none;stroke:rgba(239,230,216,.45);stroke-width:1.5}
.plano .ventana{fill:none;stroke:var(--noche);stroke-width:5}
.plano .piso{fill:transparent;transition:fill .4s}
.plano .muebles *{fill:none;stroke:rgba(239,230,216,.28);stroke-width:2}
.plano .muebles .alfombra{stroke-dasharray:6 6}
.plano .hab-n{font:400 34px/1 var(--serif);fill:rgba(239,230,216,.4)}
.plano .hab-t{font:600 26px/1 var(--sans);fill:rgba(239,230,216,.4)}
.plano .hab.hecho .hab-t,.plano .hab.hecho .hab-n{fill:rgba(239,230,216,.62)}
.plano .hab.on .piso{fill:rgba(180,134,79,.28)}
.plano .hab.on .muebles *{stroke:var(--roble-claro);stroke-width:2.6}
.plano .hab.on .hab-n{fill:var(--roble-claro)}
.plano .hab.on .hab-t{fill:var(--crema)}
.plano .cota{fill:none;stroke:rgba(239,230,216,.4);stroke-width:1.5}
.plano .cota-t{font:italic 400 22px/1 var(--serif);fill:rgba(239,230,216,.5)}
.riel-grande{margin-top:34px;display:grid;gap:14px}
.riel-grande li{display:flex;align-items:center;gap:18px;font:400 30px/1.2 var(--sans);color:var(--crema)}
.riel-grande b{width:46px;height:46px;border-radius:50%;border:1.5px solid var(--roble-claro);display:grid;place-items:center;font:400 24px/1 var(--serif);color:var(--roble-claro);flex:none}
.riel-grande li:nth-child(3) b{background:var(--terracota);border-color:var(--terracota);color:#fff}

/* catálogo */
.cat-izq{position:absolute;left:88px;top:250px;width:640px}
.cifra-grande{display:flex;align-items:baseline;gap:22px;font:400 120px/1 var(--serif);letter-spacing:-.02em}
.cifra-grande i{font-style:normal;color:var(--roble);font-size:80px}
.cifra-grande span:last-child{color:var(--terracota)}
.cifra-grande.chica span{color:var(--terracota)}
.cifra-pie{font:400 25px/1.35 var(--sans);color:var(--tinta-2);margin-top:12px;max-width:600px}
.cifras-chicas{display:flex;gap:40px;margin:26px 0 14px}
.cifras-chicas div{font:400 22px/1.2 var(--sans);color:var(--tinta-2);display:flex;align-items:baseline;gap:10px}
.cifras-chicas b{font:400 52px/1 var(--serif);color:var(--tinta)}
.fuente{font:italic 400 22px/1.3 var(--serif);color:var(--tinta-3);margin-bottom:34px}
.problemas{display:grid;gap:10px}
.problemas li{font:400 23px/1.3 var(--sans);color:var(--tinta-2);padding-left:26px;position:relative}
.problemas li::before{content:"";position:absolute;left:0;top:11px;width:12px;height:12px;border:2px solid var(--terracota);transform:rotate(45deg)}
.problemas b{color:var(--tinta);font-weight:600}
.cat-ficha{position:absolute;left:800px;top:250px;width:1032px;background:var(--papel);border:1px solid var(--hilo);display:grid;grid-template-columns:330px 1fr;gap:34px;padding:34px}
.ficha-foto{display:flex;flex-direction:column;align-items:center;gap:10px;background:#fff;padding:14px 0;border:1px solid var(--hilo);align-self:start}
.ficha-foto .prod{mix-blend-mode:normal}
.ficha-cab{font:400 22px/1.35 var(--sans);color:var(--tinta-2);margin-bottom:16px}
.ficha-cab b{color:var(--terracota)}
.ficha-dl{display:grid;gap:9px}
.fl{display:grid;grid-template-columns:124px 1fr;gap:14px;border-top:1px solid var(--hilo);padding-top:9px}
.fl dt{font:400 17px/1.5 var(--mono);color:var(--terracota)}
.fl dd{font:400 21px/1.36 var(--sans);color:var(--tinta)}

/* ground truth */
.gt-izq{position:absolute;left:88px;top:244px;width:800px}
.gt-anot{margin-top:20px}
.gt-strip{display:flex;gap:6px}
.gt-der{position:absolute;left:940px;top:244px;width:892px}
.query{background:var(--papel);border:1px solid var(--hilo);padding:16px 20px;font:400 16.5px/1.5 var(--mono);color:var(--tinta);margin-bottom:22px}
.query i{font-style:normal;color:var(--terracota);margin-right:8px}
.query.chica{font-size:16px}
.rk-fila{display:flex;gap:12px}
.rk{position:relative;background:#fff;border:1px solid var(--hilo);padding:26px 6px 6px;display:flex;flex-direction:column;align-items:center}
.rk .prod{mix-blend-mode:normal}
.rk-n{position:absolute;left:8px;top:5px;font:400 16px/1 var(--mono);color:var(--tinta-3)}
.rk.ok{border:3px solid var(--terracota)}
.rk-ok{position:absolute;bottom:-30px;left:0;right:0;text-align:center;font:600 17px/1 var(--sans);color:var(--terracota)}
.gt-cifras{position:absolute;left:88px;right:88px;top:876px;display:grid;grid-template-columns:repeat(3,auto) 1fr;gap:56px;align-items:start;border-top:1px solid var(--hilo);padding-top:20px}
.gt-cifras>div{font:400 21px/1.25 var(--sans);color:var(--tinta-2);max-width:270px}
.gt-cifras b{display:block;font:400 56px/1 var(--serif);color:var(--tinta);margin-bottom:4px}
.gt-cifras .gt-ic{max-width:none;font-size:21px}
.gt-cifras .gt-ic b{display:inline;font:600 21px/1 var(--sans);color:var(--terracota)}

/* ambientes vacíos */
.vac-izq{position:absolute;left:88px;top:250px;width:520px}
.vac-datos{margin-top:30px;display:grid;gap:16px}
.vac-datos li{font:400 23px/1.32 var(--sans);color:var(--tinta-2);border-top:1px solid var(--hilo);padding-top:12px}
.vac-datos b{font:400 32px/1 var(--serif);color:var(--tinta);margin-right:4px}
.nota-borde{margin-top:30px;font:italic 400 25px/1.3 var(--serif);color:var(--terracota)}
.vac-grilla{position:absolute;left:660px;top:250px;width:1172px;display:grid;grid-template-columns:repeat(4,270px);column-gap:30px;row-gap:22px}
.vac-grilla .amb:nth-child(n+6){}
.amb figcaption{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 10px;margin-top:7px;font:400 17px/1.2 var(--sans);color:var(--tinta-3)}
.amb figcaption b{font:600 18px/1.2 var(--sans);color:var(--tinta)}
.amb .cred{flex-basis:100%;font:400 13.5px/1.2 var(--sans);color:var(--tinta-3)}

/* v0 → v1 */
.v-col{position:absolute;top:244px}
.v-col:nth-of-type(1){left:88px;width:520px}
.v-medio{left:668px;width:420px}
.v-col:nth-of-type(3){left:1150px;width:682px}
.v-et{font:400 30px/1 var(--serif);margin-bottom:16px;color:var(--tinta-2)}
.v-et b{color:var(--tinta);font-weight:400}
.v-foto{position:relative}
.caja{position:absolute;border:3px solid var(--terracota);background:rgba(169,78,43,.12)}
.v0-cadena{display:flex;align-items:center;gap:16px;margin-top:12px}
.v0-cadena .foto{background-color:transparent}
.v-flecha{font:400 34px/1 var(--serif);color:var(--terracota)}
.v-flecha.chica{font-size:24px}
.v-txt{font:400 22px/1.35 var(--sans);color:var(--tinta-2);margin-top:12px}
.v-medio .v-txt{font:italic 400 28px/1.3 var(--serif);color:var(--tinta)}
.nada{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);border:2.5px dashed #fff;background:rgba(33,25,20,.55);padding:16px 26px;font:italic 400 30px/1 var(--serif);color:#fff;text-shadow:0 1px 6px rgba(0,0,0,.5);white-space:nowrap}
.v-res{position:absolute;left:88px;right:88px;top:840px;display:flex;align-items:center;gap:40px;border-top:1px solid var(--hilo);padding-top:16px}
.v-res-t{font:italic 400 28px/1.2 var(--serif);width:250px;flex:none}
.v-res-n{font:600 22px/1.2 var(--sans);color:var(--tinta)}
.v-res-n span{font:400 20px/1.3 var(--sans);color:var(--salvia)}

/* pipelines */
.pipe{position:relative;height:760px}
.carril{display:flex;align-items:stretch;position:absolute;left:0;right:0}
.carril.c1{top:0;height:150px}
.carril.c2{top:350px;height:220px}
.carril-et{width:170px;flex:none;display:flex;flex-direction:column;justify-content:center;gap:6px;padding-right:12px}
.carril-et b{font:400 32px/1 var(--serif)}
.carril-et span{font:400 19px/1.2 var(--sans);color:var(--tinta-3)}
.pcaja{width:222px;flex:none;background:var(--papel);border:1px solid var(--hilo);padding:16px;display:flex;flex-direction:column;gap:8px}
.pcaja b{font:600 23px/1.1 var(--sans)}
.pcaja span{font:400 18.5px/1.32 var(--sans);color:var(--tinta-2)}
.pcaja.entrada{background:transparent;border-style:dashed;border-color:var(--hilo-2)}
.pcaja.acento{border:2px solid var(--roble)}
.pcaja.control{border:2px solid var(--salvia);background:var(--salvia-claro)}
.pf{width:30px;flex:none;display:grid;place-items:center;font:400 34px/1 var(--serif);font-style:normal;color:var(--terracota)}
.chroma{position:absolute;left:665px;top:186px;width:240px;height:128px;text-align:center}
.chroma svg{position:absolute;inset:0;width:240px;height:120px}
.chroma svg *{fill:var(--papel);stroke:var(--roble);stroke-width:2.5}
.chroma b{position:relative;display:block;padding-top:52px;font:600 24px/1 var(--sans)}
.chroma span{position:relative;display:block;margin-top:6px;font:400 17px/1 var(--sans);color:var(--tinta-3)}
.chroma::before{content:"";position:absolute;left:119px;top:-36px;height:36px;border-left:2px solid var(--roble)}
.chroma::after{content:"";position:absolute;left:119px;top:122px;height:42px;border-left:2px dashed var(--roble)}
.reintento{position:absolute;left:1178px;top:570px;width:400px;height:70px;overflow:visible}
.reintento path{fill:none;stroke:var(--salvia);stroke-width:2.5}
.reintento text{font:italic 400 20px/1 var(--serif);fill:var(--salvia)}
.pipe-nota{position:absolute;left:960px;top:10px;width:780px;font:400 30px/1.3 var(--serif);color:var(--tinta-2)}
.pipe-nota em{color:var(--terracota)}

/* hiperparámetros */
.hiper,.iter{display:grid;column-gap:30px;font:400 22px/1.25 var(--sans)}
.hiper{grid-template-columns:50px 380px 1fr 300px}
.hiper>div,.iter>div{padding:10px 0;border-top:1px solid var(--hilo)}
.h-cab{font:600 18px/1.2 var(--sans)!important;color:var(--tinta-3);border-top:0!important;padding-bottom:6px!important}
.h-n{font:400 24px/1 var(--serif);color:var(--terracota)}
.h-q{font-weight:600}
.h-o{color:var(--tinta-2)}
.h-m{font:400 17px/1.5 var(--mono);color:var(--tinta-3)}
.hiper-pie{font:italic 400 26px/1.3 var(--serif);color:var(--tinta-2);margin-top:24px}

/* métricas */
.met-ej{position:relative}
.met-cotas{position:relative;height:108px;margin-left:0}
.mc{position:absolute;left:0;width:calc(var(--k) * 158px - 8px);height:30px;border-top:2px solid var(--roble)}
.mc:nth-child(1){top:78px}.mc:nth-child(2){top:44px}.mc:nth-child(3){top:10px}
.mc::before,.mc::after{content:"";position:absolute;top:-9px;width:2px;height:16px;background:var(--roble);transform:rotate(45deg)}
.mc::before{left:0}.mc::after{right:0}
.mc span{position:absolute;left:calc(100% + 14px);top:-13px;white-space:nowrap;font:400 18px/1 var(--mono);color:var(--tinta-2)}
.rk-fila.diez{gap:12px}
.met-rr{margin-top:42px;font:400 22px/1 var(--sans);color:var(--tinta-2)}
.met-rr b{font:400 26px/1 var(--mono);color:var(--terracota)}
.met-defs{position:absolute;left:88px;right:88px;top:640px;display:grid;grid-template-columns:repeat(5,1fr);gap:22px}
.md{background:var(--papel);border:1px solid var(--hilo);padding:22px 24px;min-height:280px}
.md h4{font:400 30px/1.1 var(--serif);margin-bottom:10px;color:var(--tinta)}
.md p{font:400 21px/1.38 var(--sans);color:var(--tinta-2)}
.ic-mini{width:100%;height:56px;margin-top:10px}
.ic-mini line{stroke:var(--tinta-2);stroke-width:2.5}
.ic-mini circle{fill:var(--terracota)}
.juez-grilla{display:grid;grid-template-columns:1fr 1fr;gap:26px 34px}
.jz{background:var(--papel);border:1px solid var(--hilo);padding:26px 30px;min-height:320px;display:flex;flex-direction:column}
.jz h4{font:400 33px/1.1 var(--serif);margin-bottom:10px}
.jz p{font:400 23px/1.35 var(--sans);color:var(--tinta-2)}
.notas3{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.notas3 div{border:1px solid var(--hilo);padding:10px 12px;font:400 18px/1.25 var(--sans);color:var(--tinta-2);background:#fff}
.notas3 b{display:block;font:400 40px/1 var(--serif);color:var(--terracota);margin-bottom:4px}
.dos-def{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:12px}
.dos-def div{border-left:3px solid var(--roble);padding-left:14px;font:400 20px/1.3 var(--sans);color:var(--tinta-2)}
.dos-def b{display:block;font:600 22px/1.3 var(--sans);color:var(--tinta)}
.ordenes{margin-top:auto;display:flex;align-items:center;gap:22px}
.ordenes .o{display:flex;gap:6px}
.ordenes i{width:66px;height:52px;border:1.5px solid var(--tinta-2);display:grid;place-items:center;font:400 28px/1 var(--serif);font-style:normal;background:#fff}
.ordenes .y{font:italic 400 26px/1 var(--serif);color:var(--tinta-3)}
.recibo-mini{margin-top:auto;display:flex;gap:10px}
.recibo-mini span{border:1px dashed var(--hilo-2);padding:8px 14px;font:400 17px/1 var(--mono);color:var(--tinta-2);background:#fff}
.img-tres{display:grid;grid-template-columns:repeat(3,1fr);gap:34px}
.it{background:var(--papel);border:1px solid var(--hilo);padding:24px 26px;min-height:600px;display:flex;flex-direction:column;gap:18px}
.it h4{font:400 32px/1.1 var(--serif)}
.it p{font:400 21px/1.38 var(--sans);color:var(--tinta-2);margin-top:auto}
.it p b{color:var(--tinta);font-weight:600}
.par-fotos{display:flex;gap:10px}
.it-cifras{display:grid;grid-template-columns:1fr 1fr;gap:16px;border-top:1px solid var(--hilo);padding-top:12px}
.it-cifras.tres{grid-template-columns:repeat(3,1fr)}
.it-cifras div{font:400 18px/1.25 var(--sans);color:var(--tinta-2)}
.it-cifras b{display:block;font:400 36px/1.05 var(--serif);color:var(--terracota)}
.id-lista{display:grid;gap:8px}
.id-par{display:flex;align-items:center;gap:12px}
.id-par .prod{background-color:#fff;mix-blend-mode:normal;border:1px solid var(--hilo)}
.id-par .foto{background-color:#fff;border:1px solid var(--hilo)}
.id-p{font:400 17px/1.2 var(--mono);color:var(--tinta-2);margin-left:6px}
.siglip{display:flex;flex-direction:column;gap:10px;align-items:stretch}
.sg-pedido{font:italic 400 19px/1.35 var(--serif);color:var(--tinta-2);border-left:3px solid var(--roble);padding-left:14px}
.sg-x{align-self:center;font:400 18px/1 var(--mono);color:#fff;background:var(--terracota);padding:8px 14px}
.sg-img{align-self:center;font:400 19px/1 var(--sans);color:var(--tinta-2);border:1px dashed var(--hilo-2);padding:12px 26px}

/* experimentos */
.exp{padding-top:52px}
.exp-top{display:flex;justify-content:space-between;align-items:center}
.riel{display:flex;gap:26px}
.riel li{display:flex;align-items:center;gap:10px;font:400 19px/1 var(--sans);color:var(--tinta-3);transition:color .3s}
.riel li b{width:32px;height:32px;border-radius:50%;border:1.5px solid var(--hilo-2);display:grid;place-items:center;font:400 17px/1 var(--serif);transition:all .3s}
.riel li.hecho{color:var(--tinta-2)}
.riel li.hecho b{background:var(--tinta-2);border-color:var(--tinta-2);color:var(--yeso)}
.riel li.actual{color:var(--terracota);font-weight:600}
.riel li.actual b{background:var(--terracota);border-color:var(--terracota);color:#fff}
.exp-tit{font-size:56px;margin-top:8px}
.tag-adv{font:600 20px/1 var(--sans);color:var(--salvia);border:1.5px solid var(--salvia);padding:6px 10px;vertical-align:middle;margin-left:14px;letter-spacing:.01em}
.exp-preg{font-size:28px;margin-top:6px}
.exp-izq{position:absolute;left:88px;top:250px;width:640px;display:grid;gap:22px}
.b-txt{font:400 23.5px/1.4 var(--sans);color:var(--tinta)}
.variantes{display:grid;gap:10px;margin-bottom:12px}
.variantes li{display:grid;grid-template-columns:62px 1fr;align-items:start;gap:4px}
.variantes .chip{justify-self:start;margin-top:-2px}
.variantes b{display:block;font:600 22px/1.2 var(--sans)}
.variantes span{display:block;font:400 19.5px/1.3 var(--sans);color:var(--tinta-2)}
.chip{display:inline-grid;place-items:center;min-width:34px;height:34px;padding:0 6px;border:1.5px solid var(--tinta-2);font:400 16px/1 var(--mono);color:var(--tinta);background:var(--papel)}
.metrica{font:italic 400 21px/1.35 var(--serif);color:var(--tinta-2);border-top:1px solid var(--hilo);padding-top:10px}
.exp-der{position:absolute;left:780px;top:250px;width:1052px;height:650px}
.vacio{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.vacio-plano{position:absolute;inset:20px 40px;width:calc(100% - 80px);height:calc(100% - 40px)}
.vacio-plano .v-pared{fill:none;stroke:var(--hilo);stroke-width:6}
.vacio-plano .v-vent{fill:none;stroke:var(--hilo);stroke-width:2}
.vacio-plano .v-puerta{fill:none;stroke:var(--hilo);stroke-width:1.5;stroke-dasharray:4 5}
.vacio-t{position:relative;font:italic 400 44px/1 var(--serif);color:var(--hilo-2)}
.vacio-s{position:relative;font:400 19px/1.3 var(--sans);color:var(--hilo-2);margin-top:12px}
.res{position:absolute;inset:0;display:flex;flex-direction:column;gap:18px}
.res-nota{font:italic 400 23px/1.35 var(--serif);color:var(--tinta-2);max-width:1000px}
.res-nota.grande{font:400 50px/1 var(--serif);color:var(--terracota);display:flex;align-items:baseline;gap:18px;margin:-6px 0 6px}
.res-nota.grande span{font:italic 400 24px/1.2 var(--serif);color:var(--tinta-2)}
.res-nota.aviso{border-left:3px solid var(--terracota);padding-left:16px}
.decision{position:absolute;left:88px;right:88px;top:922px;height:96px;display:flex;align-items:center;gap:30px;border:1.5px dashed var(--hilo-2);padding:0 30px;transition:background .4s,border-color .4s}
.decision:has(.d-txt.visto){background:var(--salvia-claro);border:1.5px solid var(--salvia)}
.d-et{font:600 21px/1 var(--sans);color:var(--hilo-2);flex:none;width:110px}
.decision:has(.d-txt.visto) .d-et{color:var(--salvia)}
.d-txt{font:400 25px/1.3 var(--sans);color:var(--tinta)}
.ejemplo-vend{display:flex;gap:18px;align-items:center;margin-top:16px}
.ejemplo-vend q{display:block;font:italic 400 21px/1.35 var(--serif);color:var(--tinta-2)}
.ejemplo-vend .mini-et{margin-bottom:4px}

/* SVG de gráficos */
.graf{display:block;overflow:visible}
.g-tit{font:600 22px/1 var(--sans);fill:var(--tinta-2)}
.g-tit-html{font:600 22px/1 var(--sans);color:var(--tinta-2)}
.g-et{font:400 23px/1 var(--sans);fill:var(--tinta)}
.g-sub{font:400 17px/1 var(--sans);fill:var(--tinta-3)}
.g-eje{font:400 16px/1 var(--mono);fill:var(--tinta-3)}
.g-cota{stroke:var(--roble);stroke-width:1.5}
.g-cota-t{stroke:var(--roble);stroke-width:2}
.g-grilla{stroke:var(--hilo);stroke-width:1;stroke-dasharray:3 5}
.g-ic{stroke:var(--tinta);stroke-width:2}
.g-val{font:600 25px/1 var(--sans);fill:var(--tinta-2)}
.g-val.elegido{fill:var(--terracota)}
.g-val.grande{font:400 40px/1 var(--serif)}
.g-anot{font:italic 400 20px/1 var(--serif);fill:var(--tinta-2)}
.g-chip{fill:var(--papel);stroke:var(--tinta-2);stroke-width:1.5}
.g-chip-t{font:400 15px/1 var(--mono);fill:var(--tinta)}
.g-linea{fill:none;stroke-width:3.5}
.g-linea.sol{stroke:var(--terracota)}
.g-linea.punt{stroke:var(--tinta-3);stroke-dasharray:8 7;stroke-width:2.5}
.g-punto.sol{fill:var(--terracota)}
.g-punto.punt{fill:var(--yeso);stroke:var(--tinta-3);stroke-width:2}
.g-banda{fill:rgba(169,78,43,.13)}
.g-et-serie{font:400 21px/1 var(--sans)}
.g-et-serie.sol{fill:var(--terracota);font-weight:600}
.g-et-serie.punt{fill:var(--tinta-3)}
.g-marca{fill:none;stroke-width:2.5}
.g-marca.elegido{stroke:var(--terracota)}
.g-marca.base{stroke:var(--tinta-2)}
.g-marca-t{font:600 21px/1 var(--sans)}
.g-marca-t.elegido{fill:var(--terracota)}
.g-marca-t.base{fill:var(--tinta-2)}
.g-punto-rep{fill:var(--terracota);stroke:var(--yeso);stroke-width:2}
.g-delta{font:600 22px/1 var(--sans);fill:var(--salvia)}
.g-flecha{fill:none;stroke:var(--salvia);stroke-width:2}

/* exp 10 */
.e10 .exp-izq .variantes li:nth-child(n){}
.e10 .metrica{font-size:19.5px}
.marcador{display:flex;align-items:baseline;gap:18px;margin-bottom:8px}
.mk-t{font:400 34px/1 var(--serif)}
.mk-t b{font-weight:400;color:var(--terracota)}
.mk-s{font:400 18px/1.2 var(--sans);color:var(--tinta-3)}
.tiles{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
.tj{width:160px;padding:8px 10px;border:1px solid var(--hilo);background:var(--papel);display:flex;flex-direction:column;gap:2px}
.tj b{font:600 16px/1.15 var(--sans)}
.tj span{font:400 14px/1.15 var(--sans);color:var(--tinta-3)}
.tj em{font:600 14px/1 var(--sans);font-style:normal;margin-top:6px}
.tj.t-a{border-top:5px solid var(--roble)}
.tj.t-a em{color:var(--roble)}
.tj.t-b{border-top:5px solid var(--tinta-3)}
.tj.t-b em{color:var(--tinta-3)}
.tj.t-c{border-top:5px solid var(--terracota)}
.tj.t-c em{color:var(--terracota)}
.tj.t-emp{border-top:5px dashed var(--hilo-2)}
.tj.t-emp em{color:var(--tinta-3)}
.res-a{transition:opacity .4s}
.e10 .res-b{background:var(--yeso)}
.giro{border-left:3px solid var(--terracota);padding-left:16px;font-size:22px}
.dos-marcadores{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.dos-marcadores .tiles .tj{width:150px}
.dos-marcadores .mk-t{font-size:29px;white-space:nowrap}
.dos-marcadores .marcador{flex-direction:column;align-items:flex-start;gap:4px}
.e10-cifras{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;border-top:1px solid var(--hilo);padding-top:14px}
.e10-cifras div{font:400 18px/1.3 var(--sans);color:var(--tinta-2)}
.e10-cifras b{display:block;font:400 34px/1.1 var(--serif);color:var(--terracota);margin-bottom:4px}

/* exp 12 */
.e12-motivo{display:flex;align-items:center;gap:12px;margin-top:12px}
.e12-mt{font:italic 400 21px/1.3 var(--serif);color:var(--terracota);width:220px;margin-left:8px}
.e12 .variantes span{font-size:18px}
.e12 .variantes b{font-size:21px}
.e12 .variantes{gap:5px;margin-bottom:8px}
.e12 .b-txt{font-size:22.5px}
.e12 .exp-izq{gap:14px}
.e12 .metrica{font-size:20px}
.e12-grilla{display:grid;grid-template-columns:repeat(2,330px);gap:14px 26px;justify-content:start}
.e12-c figcaption{display:flex;align-items:center;gap:12px;margin-top:8px}
.e12-t{display:flex;flex-direction:column;gap:3px}
.e12-n{font:400 19px/1 var(--sans);color:var(--tinta-2);white-space:nowrap}
.e12-n b{font:400 28px/1 var(--serif);color:var(--tinta)}
.e12-s{font:400 15px/1.1 var(--sans);color:var(--tinta-3)}
.e12-c.mal .foto{outline:3px solid var(--tinta-3);outline-offset:-3px}
.e12-c.mal .e12-n b{color:var(--tinta-3);text-decoration:line-through}
.e12-c.elegida .foto{outline:4px solid var(--terracota);outline-offset:-4px}
.e12-c.elegida .e12-n b{color:var(--terracota)}
.e12 .res{flex-direction:row;gap:26px;align-items:flex-start}
.e12 .res .res-nota{width:300px;flex:none;font-size:22px}

/* de punta a punta */
.e2e-fila{display:flex;gap:16px;align-items:flex-start;margin-bottom:34px}
.e2e-et{width:180px;flex:none;padding-top:6px}
.e2e-et b{display:block;font:400 34px/1 var(--serif)}
.e2e-et span{display:block;font:400 18px/1.3 var(--sans);color:var(--tinta-3);margin-top:8px}
.intento{position:relative}
.intento figcaption{font:400 17px/1 var(--sans);color:var(--tinta-3);margin-top:8px}
.sello{position:absolute;left:12px;top:12px;font:400 16px/1.25 var(--sans);padding:7px 12px;background:rgba(251,248,242,.95);display:flex;flex-direction:column;gap:2px}
.sello b{font:italic 400 21px/1 var(--serif)}
.sello.no{color:var(--terracota);border:2px solid var(--terracota)}
.sello.ok{color:var(--salvia);border:2px solid var(--salvia)}
.e2e-lista{margin-left:10px}
.e2e-lista ul{display:grid;grid-template-columns:1fr 1fr;gap:6px 14px}
.e2e-lista li{display:flex;align-items:center;gap:10px;font:400 21px/1.2 var(--sans)}
.e2e-lista{margin-left:24px;padding-top:4px}

/* iteración */
.iter{grid-template-columns:1fr 500px 470px;font-size:25px}
.iter>div{padding:14px 0!important}
.it-p{color:var(--tinta)}
.it-c{color:var(--tinta-2);font-weight:600}
.it-m{font:400 20px/1.4 var(--mono);color:var(--terracota)}

/* camino */
.camino{margin-top:10px}
.camino .g-et{font-size:21px}

/* costo */
.recibo{position:absolute;left:88px;top:250px;width:860px;background:#fff;padding:36px 44px 50px;box-shadow:0 20px 40px -26px rgba(33,25,20,.45);
}
.recibo::after{content:"";position:absolute;left:0;right:0;bottom:-12px;height:14px;background:linear-gradient(-45deg,transparent 33%,#fff 33%,#fff 66%,transparent 66%) 0 0/20px 28px,linear-gradient(45deg,transparent 33%,#fff 33%,#fff 66%,transparent 66%) 0 0/20px 28px}
.rc-cab{display:flex;flex-direction:column;gap:6px;border-bottom:2px dashed var(--hilo-2);padding-bottom:18px;margin-bottom:12px}
.rc-cab b{font:400 44px/1 var(--serif)}
.rc-cab span{font:400 18px/1 var(--mono);color:var(--tinta-3)}
.rc-l{display:flex;align-items:baseline;gap:12px;padding:14px 0;font:400 25px/1.2 var(--sans)}
.rc-l i{flex:1;border-bottom:2px dotted var(--hilo-2)}
.rc-l b{font:400 32px/1 var(--mono);color:var(--terracota)}
.rc-l.chico{font-size:21px}
.rc-l.chico b{font-size:26px;color:var(--tinta-2)}
.rc-sep{border-top:2px dashed var(--hilo-2);margin:12px 0}
.rc-pie{font:400 16px/1.3 var(--mono);color:var(--tinta-3);margin-top:16px}
.costo-notas{position:absolute;left:1030px;top:250px;width:802px;display:grid;gap:26px}
.costo-notas div{border-top:1px solid var(--hilo);padding-top:16px}
.costo-notas h4{font:400 32px/1.1 var(--serif);margin-bottom:8px}
.costo-notas p{font:400 23px/1.35 var(--sans);color:var(--tinta-2)}

/* limitaciones */
.dos-listas{display:grid;grid-template-columns:1fr 1fr;gap:80px;margin-top:24px}
.dos-listas h3{font:400 40px/1 var(--serif);margin-bottom:24px;padding-bottom:16px;border-bottom:2px solid var(--tinta)}
.dos-listas li{font:400 31px/1.32 var(--sans);color:var(--tinta);padding:24px 0 24px 44px;border-bottom:1px solid var(--hilo);position:relative}
.lista-lim li::before{content:"";position:absolute;left:4px;top:44px;width:16px;height:2px;background:var(--terracota)}
.lista-fut li::before{content:"→";position:absolute;left:0;top:26px;font:400 26px/1 var(--serif);color:var(--salvia)}

/* conclusiones */
.conclusiones{padding:0}
.conc-txt{position:absolute;left:96px;top:110px;width:1040px}
.conc{counter-reset:c;margin-top:34px;display:grid;gap:22px}
.conc li{counter-increment:c;display:grid;grid-template-columns:70px 1fr;font:400 29px/1.32 var(--sans);color:rgba(239,230,216,.8)}
.conc li::before{content:counter(c);font:400 46px/1 var(--serif);color:var(--roble-claro)}
.conc b{font-weight:600;color:var(--crema)}
.gracias{font:italic 400 96px/1 var(--serif);color:var(--crema);margin-top:56px}
.equipo-pie{font:400 22px/1.3 var(--sans);color:rgba(239,230,216,.6);margin-top:20px}
.conc-foto{position:absolute;right:0;top:0;width:700px;height:1080px}
.conc-foto::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,var(--noche) 0,rgba(33,25,20,0) 30%)}

/* índice, notas, presentador */
#indice{position:fixed;inset:0;background:#16110d;z-index:30;display:none;overflow:auto;padding:32px}
#indice.abierto{display:block}
#indice-grilla{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:22px}
.mini-l{border:0;background:none;padding:0;color:var(--crema);font:400 16px/1.3 var(--sans);text-align:left;cursor:pointer}
.mini-v{position:relative;width:100%;aspect-ratio:16/9;overflow:hidden;margin-bottom:6px;pointer-events:none;background:var(--yeso)}
.mini-v .slide{opacity:1;visibility:visible;transform-origin:0 0;transition:none}
.mini-l.actual .mini-v{outline:4px solid var(--roble)}
#notas{position:fixed;left:0;right:0;bottom:0;max-height:38vh;overflow:auto;background:rgba(22,17,13,.94);color:var(--crema);font:400 19px/1.45 var(--sans);padding:18px 28px;z-index:20;display:none}
body.con-notas #notas{display:block}
#notas b{color:var(--roble-claro)}
#negro{position:fixed;inset:0;background:#000;display:none;z-index:40}
#negro.abierto{display:block}
#ayuda{position:fixed;left:50%;transform:translateX(-50%);bottom:12px;font:400 13px/1.4 var(--sans);color:rgba(239,230,216,.55);background:rgba(22,17,13,.7);padding:6px 10px;z-index:10;pointer-events:none;text-align:right;transition:opacity .8s}
body.sin-ayuda #ayuda{opacity:0}
body.presentador{background:#16110d}
body.presentador #ayuda{display:none}
#p-panel{display:none}
body.presentador #p-panel{display:grid;position:fixed;inset:0;grid-template-columns:minmax(0,62fr) minmax(0,38fr);grid-template-rows:auto 1fr;gap:16px;padding:16px;color:var(--crema);font-family:var(--sans)}
#p-sig{position:relative;aspect-ratio:16/9;overflow:hidden;background:var(--yeso);grid-column:2;grid-row:1}
#p-sig .slide{opacity:1;visibility:visible;transform-origin:0 0;transition:none}
#p-info{grid-column:2;grid-row:2;overflow:auto}
#p-reloj{font:400 40px/1 var(--mono);color:var(--roble-claro)}
#p-plan{font:400 17px/1.3 var(--sans);color:rgba(239,230,216,.6);margin:6px 0 14px}
#p-notas{font:400 20px/1.5 var(--sans)}
#p-notas b{color:var(--roble-claro)}

@media print{
  @page{size:1920px 1080px;margin:0}
  html,body{overflow:visible;height:auto;background:#fff}
  #escenario{position:static;transform:none!important;height:auto;overflow:visible}
  .slide{position:relative;opacity:1;visibility:visible;page-break-after:always;break-after:page}
  [data-paso]{opacity:1!important;transform:none!important}
  [data-hasta]{opacity:0!important}
  #hud,#barra,#ayuda,#indice,#notas{display:none!important}
}
"""

JS = r"""
(function(){
  'use strict';
  var $=function(s,c){return (c||document).querySelector(s)}, $$=function(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s))};
  var esc=$('#escenario'), slides=$$('#escenario > .slide'), N=slides.length;
  var NOTAS=JSON.parse($('#datos-notas').textContent);
  var TODO=/[?&]todo/.test(location.search), PRES=/[?&]presentador/.test(location.search);
  var cur=0, paso=0, otra=null, inicio=null;
  function maxPaso(s){var m=0;$$('[data-paso]',s).forEach(function(e){m=Math.max(m,+e.dataset.paso)});return m}
  function pintar(s,p,todo){
    $$('[data-paso]',s).forEach(function(e){e.classList.toggle('visto',todo||+e.dataset.paso<=p)});
    $$('[data-hasta]',s).forEach(function(e){e.classList.toggle('oculto',todo||p>=+e.dataset.hasta)});
    if(s.dataset.riel){var mp=s.dataset.riel.split(',').map(Number);var ri=todo?mp[mp.length-1]:mp[Math.min(p,mp.length-1)];
      $$('.riel li',s).forEach(function(li,i){li.classList.toggle('hecho',i<ri);li.classList.toggle('actual',i===ri)})}
  }
  function escalar(){
    var box=PRES?$('#p-actual').getBoundingClientRect():{left:0,top:0,width:innerWidth,height:innerHeight};
    var k=Math.min(box.width/1920,box.height/1080);
    esc.style.transform='translate('+(box.left+(box.width-1920*k)/2)+'px,'+(box.top+(box.height-1080*k)/2)+'px) scale('+k+')';
    if(PRES)escalarSig();
  }
  function ir(n,p,silencio){
    n=Math.max(0,Math.min(N-1,n));
    slides[cur].classList.remove('activa');
    cur=n;var s=slides[cur];s.classList.add('activa');
    var mx=maxPaso(s);paso=(p==null)?0:(p<0?mx:Math.min(p,mx));
    pintar(s,paso,TODO);
    $('#barra').style.width=((cur+1)/N*100)+'%';
    $('#hud-sec').textContent=s.dataset.seccion||'';
    $('#hud-n').textContent=(cur+1)+' / '+N;
    $('#hud').classList.toggle('sobre-oscuro',s.classList.contains('oscura'));
    $('#notas').innerHTML='<b>'+(cur+1)+'. '+(s.dataset.titulo||'')+'</b> · '+NOTAS[cur].plan+'<br>'+NOTAS[cur].html;
    var h='#'+(cur+1)+(paso?'.'+paso:'');
    if(location.hash!==h)history.replaceState(null,'',location.pathname+location.search+h);
    if(PRES)pintarPresentador();
    if(!silencio){var dest=PRES?window.opener:otra;try{if(dest&&!dest.closed)dest.postMessage({amoblai:1,cur:cur,paso:paso},'*')}catch(e){}}
  }
  function siguiente(){if(inicio===null)inicio=Date.now();var mx=maxPaso(slides[cur]);if(!TODO&&paso<mx){paso++;pintar(slides[cur],paso,false);ir(cur,paso)}else if(cur<N-1)ir(cur+1,0)}
  function anterior(){if(!TODO&&paso>0){paso--;ir(cur,paso)}else if(cur>0)ir(cur-1,-1)}
  // índice
  var ind=$('#indice'),grilla=$('#indice-grilla');
  function clon(s){var c=s.cloneNode(true);c.removeAttribute('id');c.classList.add('activa','todo');return c}
  function abrirIndice(ab){
    ind.classList.toggle('abierto',ab);if(!ab)return;
    if(!grilla.children.length){slides.forEach(function(s,i){var b=document.createElement('button');b.className='mini-l';var v=document.createElement('div');v.className='mini-v';v.appendChild(clon(s));b.appendChild(v);b.appendChild(document.createTextNode((i+1)+'. '+(s.dataset.titulo||'')));b.addEventListener('click',function(){abrirIndice(false);ir(i,0)});grilla.appendChild(b)})}
    $$('.mini-l',ind).forEach(function(b,i){b.classList.toggle('actual',i===cur);var v=$('.mini-v',b);$('.slide',v).style.transform='scale('+(v.clientWidth/1920)+')'});
  }
  // presentador
  function escalarSig(){var v=$('#p-sig'),s=$('.slide',v);if(s)s.style.transform='scale('+(v.clientWidth/1920)+')'}
  function pintarPresentador(){
    var v=$('#p-sig');v.innerHTML='';if(cur<N-1){v.appendChild(clon(slides[cur+1]));escalarSig()}
    var mx=maxPaso(slides[cur]);
    $('#p-plan').textContent='Slide '+(cur+1)+' de '+N+' · paso '+paso+' de '+mx+' · '+NOTAS[cur].plan;
    $('#p-notas').innerHTML=NOTAS[cur].html;
  }
  function reloj(){var t=inicio===null?0:Math.floor((Date.now()-inicio)/1000);$('#p-reloj').textContent=String(Math.floor(t/60)).padStart(2,'0')+':'+String(t%60).padStart(2,'0')}
  setTimeout(function(){document.body.classList.add('sin-ayuda')},6000);if(TODO)document.body.classList.add('sin-ayuda');
  if(PRES){document.body.classList.add('presentador');document.title='Presentador · '+document.title;setInterval(reloj,1000);try{window.opener&&window.opener.postMessage({amoblai:1,hola:1},'*')}catch(e){}}
  addEventListener('message',function(e){var d=e.data;if(!d||!d.amoblai)return;if(d.hola){otra=e.source;otra.postMessage({amoblai:1,cur:cur,paso:paso},'*');return}if(inicio===null)inicio=Date.now();ir(d.cur,d.paso,true)});
  document.addEventListener('keydown',function(e){
    if(e.metaKey||e.ctrlKey||e.altKey)return;var ab=ind.classList.contains('abierto');
    switch(e.key){
      case'ArrowRight':case'ArrowDown':case'PageDown':case' ':case'Enter':if(!ab){siguiente();e.preventDefault()}break;
      case'ArrowLeft':case'ArrowUp':case'PageUp':case'Backspace':if(!ab){anterior();e.preventDefault()}break;
      case'Home':ir(0,0);e.preventDefault();break;
      case'End':ir(N-1,0);e.preventDefault();break;
      case'f':case'F':if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen().catch(function(){});break;
      case'o':case'O':abrirIndice(!ab);break;
      case'n':case'N':document.body.classList.toggle('con-notas');break;
      case'b':case'B':$('#negro').classList.toggle('abierto');break;
      case'p':case'P':if(!PRES)otra=window.open(location.pathname+'?presentador#'+(cur+1)+(paso?'.'+paso:''),'amoblai-presentador','width=1500,height=860');break;
      case'r':case'R':inicio=Date.now();break;
      case'Escape':abrirIndice(false);$('#negro').classList.remove('abierto');break;
    }
  });
  esc.addEventListener('click',function(e){if(!PRES)siguiente()});
  var x0=null;addEventListener('touchstart',function(e){x0=e.changedTouches[0].clientX},{passive:true});
  addEventListener('touchend',function(e){if(x0===null)return;var d=e.changedTouches[0].clientX-x0;x0=null;if(Math.abs(d)>50){if(d<0)siguiente();else anterior()}},{passive:true});
  addEventListener('resize',function(){escalar();if(ind.classList.contains('abierto'))abrirIndice(true)});
  var mm=location.hash.match(/^#(\d+)(?:\.(\d+))?$/);
  escalar();ir(mm?+mm[1]-1:0,mm&&mm[2]?+mm[2]:0,true);
})();
"""


def notas_html(s) -> str:
    if s["partes"]:
        et = ["Por qué lo hicimos y qué queríamos ver (antes de avanzar)", "El experimento (antes de avanzar)", "→ Resultados (flecha)", "→ Decisión (flecha)"]
        return "".join(f"<p><b>{i + 1}. {et[i]}:</b> {esc(t)}</p>" for i, t in enumerate(s["partes"]))
    return f"<p>{esc(s['notas'])}</p>"


def armar():
    t = 0
    notas = []
    for s in SLIDES:
        s["desde"] = t
        notas.append({"plan": f"~{mmss(s['seg'])} min · desde el minuto {mmss(t)}", "html": notas_html(s)})
        t += s["seg"]
    total = t
    secs = []
    for i, s in enumerate(SLIDES):
        attrs = f'data-titulo="{html.escape(s["titulo"])}" data-seccion="{html.escape(s["seccion"])}"'
        if s["riel"]:
            attrs += f' data-riel="{s["riel"]}"'
        secs.append(f'<section class="slide {s["clase"]}" id="s{i + 1}" {attrs}>{s["html"]}</section>')
    cuerpo = "\n".join(secs)
    doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>amoblai · TP 3 · 73.69 LLM</title>
<style>{css_fuentes()}</style>
<style>{CSS}</style>
<style>{IM.style()}</style>
</head><body>
<div id="escenario">
{cuerpo}
<div id="hud"><span id="hud-sec"></span><span id="hud-n"></span></div><div id="barra"></div>
</div>
<div id="p-panel"><div id="p-actual" style="grid-column:1;grid-row:1/3"></div><div id="p-sig"></div><div id="p-info"><div id="p-reloj">00:00</div><div id="p-plan"></div><div id="p-notas"></div></div></div>
<div id="indice"><div id="indice-grilla"></div></div>
<div id="notas"></div><div id="negro"></div>
<div id="ayuda">→ avanza · ← vuelve · F pantalla completa · O índice · N notas · P presentador · B negro</div>
<script type="application/json" id="datos-notas">{json.dumps(notas, ensure_ascii=False).replace("</", "<\\/")}</script>
<script>{JS}</script>
</body></html>"""
    (OUT / "presentacion.html").write_text(doc)
    return total


def guion(total: int):
    n = len(SLIDES)
    # reparto en tres partes de tiempo parecido, cortando en slides
    cortes = []
    objetivo = [total / 3, 2 * total / 3]
    for o in objetivo:
        i = min(range(n), key=lambda j: abs(SLIDES[j]["desde"] - o))
        cortes.append(i)
    partes = [(0, cortes[0]), (cortes[0], cortes[1]), (cortes[1], n)]
    L = ["# Guion de la presentación (amoblai)", "",
         f"Generado por `build.py` junto con `presentacion.html`: los números salen de los mismos archivos de resultados que las slides. {n} slides, unos {round(total / 60)} minutos ({mmss(total)}).", "",
         "**Cómo se pasa.** Flecha derecha, espacio o clic: avanza un paso; flecha izquierda: vuelve un paso. F: pantalla completa; O: índice con miniaturas; N: estas notas abajo de la slide; P: ventana del presentador (slide actual, la siguiente, notas y reloj, sincronizadas); B: pantalla negra. `presentacion.html?todo#12` muestra la slide 12 con todo a la vista (para revisar o imprimir).", "",
         "**En cada experimento** se ve primero solo el porqué (paso 1 del riel, arriba a la derecha). Con la flecha aparece el experimento, a la izquierda (paso 2). **Se cuentan esas dos cosas antes de avanzar:** hasta entonces el panel de resultados es un ambiente vacío. Otra flecha muestra los resultados (paso 3) y otra la decisión, en la banda de abajo (paso 4). En el experimento 10 los resultados tienen dos partes: primero los 5 departamentos, después los 11 ambientes.", "",
         "**Reparto sugerido** (a definir entre los tres):"]
    for k, (a, b) in enumerate(partes, 1):
        dur = sum(s["seg"] for s in SLIDES[a:b])
        L.append(f"- Parte {k}: slides {a + 1} a {b} ({SLIDES[a]['titulo']} → {SLIDES[b - 1]['titulo']}), unos {round(dur / 60)} min.")
    rapidos = [str(i + 1) for i, s in enumerate(SLIDES) if "rapido" in s["clase"] or s["id"] == "costo"]
    L += ["", f"Si falta tiempo, se pueden pasar rápido los experimentos 4 y 5 y la slide de costos (slides {', '.join(rapidos)}, marcadas con *).", ""]
    for i, s in enumerate(SLIDES, 1):
        estrella = " *" if ("rapido" in s["clase"] or s["id"] == "costo") else ""
        L.append(f"## {i}. {re.sub('<[^>]+>', '', s['titulo'])}{estrella}")
        sec = s["sub"] or s["seccion"] or "Portada"
        L.append(f"*{sec} · ~{mmss(s['seg'])} min · desde el minuto {mmss(s['desde'])}*")
        L.append("")
        if s["partes"]:
            et = ["**Por qué lo hicimos y qué queríamos ver** (paso 1, antes de avanzar)", "**El experimento** (paso 2, antes de avanzar)", "**→ Resultados** (flecha)", "**→ Decisión** (flecha)"]
            for k, t in enumerate(s["partes"]):
                L.append(f"{k + 1}. {et[k]}: {t}")
        else:
            L.append(s["notas"])
        L.append("")
    (OUT / "guion.md").write_text("\n".join(L))


if __name__ == "__main__":
    total = armar()
    guion(total)
    size = (OUT / "presentacion.html").stat().st_size
    print(f"{len(SLIDES)} slides · {mmss(total)} · {size / 1e6:.2f} MB (fotos {IM.bytes / 1e6:.2f} MB)")

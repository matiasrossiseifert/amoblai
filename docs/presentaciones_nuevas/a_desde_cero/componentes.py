"""Piezas reutilizables: imágenes embebidas, fichas de producto, la planta que se amuebla en los
separadores y el diagrama de la arquitectura."""

from __future__ import annotations

import base64
import hashlib
import io
from pathlib import Path

from PIL import Image

from graficos import esc

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CACHE = HERE / "_trabajo" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

STATS = {"bytes": 0, "n": 0}


def img_uri(path, w: int, h: int | None = None, q: int = 76, fit: str = "cover",
            bg=(255, 255, 255)) -> str:
    """JPEG en base64. fit='cover' recorta al centro; 'contain' encaja sobre fondo; sin h, solo ancho."""
    path = Path(path)
    if not path.is_absolute():
        path = REPO / path
    key = hashlib.sha1(f"{path}|{path.stat().st_mtime}|{w}|{h}|{q}|{fit}|{bg}".encode()).hexdigest()[:16]
    cached = CACHE / f"{key}.b64"
    if cached.exists():
        b64 = cached.read_text()
    else:
        im = Image.open(path).convert("RGB")
        if h is None:
            r = w / im.width
            im = im.resize((w, max(1, round(im.height * r))), Image.LANCZOS)
        elif fit == "cover":
            r = max(w / im.width, h / im.height)
            im = im.resize((max(w, round(im.width * r)), max(h, round(im.height * r))), Image.LANCZOS)
            x0 = (im.width - w) // 2
            y0 = (im.height - h) // 2
            im = im.crop((x0, y0, x0 + w, y0 + h))
        else:
            r = min(w / im.width, h / im.height)
            im2 = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)
            im = Image.new("RGB", (w, h), bg)
            im.paste(im2, ((w - im2.width) // 2, (h - im2.height) // 2))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        cached.write_text(b64)
    STATS["bytes"] += len(b64)
    STATS["n"] += 1
    return "data:image/jpeg;base64," + b64


def crop_uri(path, box, w: int, h: int, q: int = 80, pad: float = 0.04) -> str:
    """Un recorte (x0, y0, x1, y1) de una imagen, encajado en w × h sobre blanco."""
    path = Path(path)
    if not path.is_absolute():
        path = REPO / path
    key = hashlib.sha1(f"crop|{path}|{path.stat().st_mtime}|{box}|{w}|{h}|{q}".encode()).hexdigest()[:16]
    cached = CACHE / f"{key}.b64"
    if cached.exists():
        b64 = cached.read_text()
    else:
        im = Image.open(path).convert("RGB")
        x0, y0, x1, y1 = box
        dx, dy = (x1 - x0) * pad, (y1 - y0) * pad
        im = im.crop((max(0, x0 - dx), max(0, y0 - dy), min(im.width, x1 + dx), min(im.height, y1 + dy)))
        r = min(w / im.width, h / im.height)
        im2 = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)
        im = Image.new("RGB", (w, h), (255, 255, 255))
        im.paste(im2, ((w - im2.width) // 2, (h - im2.height) // 2))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        cached.write_text(b64)
    STATS["bytes"] += len(b64)
    STATS["n"] += 1
    return "data:image/jpeg;base64," + b64


def product_photo(D, pid: str) -> str:
    if pid.startswith("abo-"):
        return D["abo_items"][pid]["photos"][0]
    return D["items"][pid]["photos"][0]


def type_line(D, pid: str) -> str:
    txt = D["abo_desc"].get(pid) if pid.startswith("abo-") else D["desc"].get(pid)
    if not txt:
        return ""
    first = txt.splitlines()[0]
    return first.split(":", 1)[1].strip() if ":" in first else first


def size_text(D, pid: str) -> str:
    it = D["abo_items"].get(pid) if pid.startswith("abo-") else D["items"].get(pid)
    dims = (it or {}).get("dimensions_cm") or {}
    vals = [dims.get(k) for k in ("width", "depth", "height") if dims.get(k)]
    if not vals:
        return "sin medidas"
    return " × ".join(f"{v:.0f}" for v in vals) + " cm"


def ficha(D, pid, size=170, qty=None, cap=True, hi=False, rank=None, sub=None, cls="", tag=None,
          grade=None, title=None):
    uri = img_uri(product_photo(D, pid), size * 2 if size < 140 else int(size * 1.4), int(size * 1.4) if size >= 140 else size * 2, q=80, fit="contain")
    q = f'<span class="qty">×{qty}</span>' if qty and qty > 1 else ""
    r = f'<span class="rk">{rank}</span>' if rank is not None else ""
    t = f'<span class="ftag">{esc(tag)}</span>' if tag else ""
    g = ""
    if grade is not None:
        g = '<span class="grades">' + "".join(
            f'<i class="g{v}"></i>' for v in grade) + "</span>"
    c = ""
    if cap:
        c = f'<div class="fcap"><b>{esc(title or type_line(D, pid))}</b>{f"<span>{esc(sub)}</span>" if sub else ""}</div>'
    return (f'<figure class="ficha{" hi" if hi else ""} {cls}" style="--fs:{size}px">'
            f'<div class="fph"><img src="{uri}" alt="">{q}{r}{t}</div>{g}{c}</figure>')


def foto(uri, w, h, cap=None, cls="", inner=""):
    c = f'<figcaption>{cap}</figcaption>' if cap else ""
    return (f'<figure class="foto {cls}" style="width:{w}px"><div class="fimg" style="height:{h}px">'
            f'<img src="{uri}" alt="">{inner}</div>{c}</figure>')


# ---------------------------------------------------------------- planta de los separadores

def _wall_rects():
    return [(74, 64, 400, 80), (640, 64, 926, 80), (74, 680, 740, 696), (840, 680, 926, 696),
            (74, 64, 90, 696), (910, 64, 926, 696)]


PIECES = {
    "alfombra": lambda: (
        '<rect x="210" y="300" width="360" height="260" rx="2"/>'
        '<rect x="224" y="314" width="332" height="232" stroke-width="1.2"/>'
        + "".join(f'<line x1="198" y1="{y}" x2="210" y2="{y}" stroke-width="1.2"/>'
                  f'<line x1="570" y1="{y}" x2="582" y2="{y}" stroke-width="1.2"/>'
                  for y in range(308, 556, 14))),
    "sofá": lambda: (
        '<rect x="200" y="644" width="380" height="32" rx="6"/>'
        '<rect x="200" y="588" width="36" height="88" rx="6"/>'
        '<rect x="544" y="588" width="36" height="88" rx="6"/>'
        + "".join(f'<rect x="{240 + i * 101}" y="592" width="97" height="50" rx="5"/>' for i in range(3))),
    "biblioteca": lambda: (
        '<rect x="866" y="140" width="40" height="330"/>'
        + "".join(f'<line x1="866" y1="{y}" x2="906" y2="{y}" stroke-width="1.2"/>' for y in range(195, 470, 55))
        + '<line x1="866" y1="140" x2="906" y2="470" stroke-width="1"/>'),
    "mesa ratona": lambda: (
        '<rect x="320" y="385" width="140" height="85" rx="4"/>'
        '<rect x="330" y="395" width="120" height="65" rx="2" stroke-width="1.2"/>'),
    "sillón": lambda: (
        '<g transform="translate(232,128) rotate(22)">'
        '<rect x="0" y="0" width="96" height="24" rx="6"/>'
        '<rect x="0" y="0" width="20" height="90" rx="6"/><rect x="76" y="0" width="20" height="90" rx="6"/>'
        '<rect x="24" y="28" width="48" height="56" rx="5"/></g>'),
    "lámpara": lambda: (
        '<circle cx="150" cy="168" r="26"/><circle cx="150" cy="168" r="8"/>'
        '<line x1="124" y1="168" x2="176" y2="168" stroke-width="1.2"/>'
        '<line x1="150" y1="142" x2="150" y2="194" stroke-width="1.2"/>'),
    "planta": lambda: (
        "".join(f'<ellipse cx="140" cy="590" rx="11" ry="30" transform="rotate({a} 140 618)"/>'
                for a in range(0, 360, 60))
        + '<circle cx="140" cy="618" r="9"/>'),
    "comedor": lambda: (
        '<rect x="650" y="232" width="150" height="96" rx="3"/>'
        + "".join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4"/>' for x, y, w, h in [
            (668, 198, 40, 26), (742, 198, 40, 26), (668, 336, 40, 26), (742, 336, 40, 26),
            (614, 260, 26, 40), (810, 260, 26, 40)])),
}

LABEL_POS = {"alfombra": (390, 300 - 14), "sofá": (390, 580), "biblioteca": (770, 310),
             "mesa ratona": (390, 488), "sillón": (300, 262), "lámpara": (150, 222),
             "planta": (140, 548), "comedor": (725, 384)}


def planta(old: list[str], new: list[str], top_label: str = "", side_label: str = "",
           complete: bool = False) -> str:
    walls = "".join(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}"/>'
                    for x0, y0, x1, y1 in _wall_rects())
    out = ['<svg class="planta" viewBox="0 0 1000 760" xmlns="http://www.w3.org/2000/svg">',
           '<defs><pattern id="hatch" width="9" height="9" patternUnits="userSpaceOnUse" '
           'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="9" stroke="#E9DFD0" '
           'stroke-width="1.4" stroke-opacity=".55"/></pattern></defs>',
           f'<g fill="url(#hatch)" stroke="#E9DFD0" stroke-width="1.6">{walls}</g>',
           # ventana y puerta
           '<g stroke="#E9DFD0" stroke-width="1.4" fill="none">'
           '<line x1="400" y1="69" x2="640" y2="69"/><line x1="400" y1="75" x2="640" y2="75"/>'
           '<line x1="840" y1="680" x2="840" y2="582"/>'
           '<path d="M740 680 A100 100 0 0 1 840 580" stroke-dasharray="4 5"/></g>']
    # cotas
    out.append('<g stroke="#A8998A" stroke-width="1.3" fill="none">'
               '<line x1="74" y1="32" x2="926" y2="32"/><line x1="68" y1="38" x2="80" y2="26"/>'
               '<line x1="920" y1="38" x2="932" y2="26"/><line x1="74" y1="40" x2="74" y2="58"/>'
               '<line x1="926" y1="40" x2="926" y2="58"/>'
               '<line x1="34" y1="64" x2="34" y2="696"/><line x1="28" y1="70" x2="40" y2="58"/>'
               '<line x1="28" y1="702" x2="40" y2="690"/></g>')
    if top_label:
        out.append(f'<text x="500" y="22" text-anchor="middle" class="pl-lab">{esc(top_label)}</text>')
    if side_label:
        out.append(f'<text x="22" y="380" text-anchor="middle" class="pl-lab" transform="rotate(-90 22 380)">{esc(side_label)}</text>')
    for p in old:
        cls = "pl-new" if complete else "pl-old"
        out.append(f'<g class="{cls}">{PIECES[p]()}</g>')
    for p in new:
        out.append(f'<g class="pl-new">{PIECES[p]()}</g>')
        x, y = LABEL_POS[p]
        out.append(f'<text x="{x}" y="{y}" text-anchor="middle" class="pl-tag">+ {esc(p)}</text>')
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- diagrama de la arquitectura

def _box(x, y, w, h, title, lines, kind="", tag=None, step=None, badge=None):
    st = f' data-step="{step}"' if step is not None else ""
    cls = {"out": "ab-out", "llm": "ab-llm", "": "ab"}[kind]
    s = [f'<g{st} class="{cls}">', f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>']
    s.append(f'<text class="ab-t" x="{x + 22}" y="{y + 40}">{esc(title)}</text>')
    if tag:
        s.append(f'<text class="ab-tag" x="{x + w - 18}" y="{y + 38}" text-anchor="end">{esc(tag)}</text>')
    for i, ln in enumerate(lines):
        s.append(f'<text class="ab-l" x="{x + 22}" y="{y + 74 + i * 27}">{esc(ln)}</text>')
    if badge:
        bx = x + w - 6
        for j, b in enumerate(badge):
            cx = bx - j * 50
            s.append(f'<g class="ab-badge"><rect x="{cx - 44}" y="{y - 17}" width="44" height="30" rx="15"/>'
                     f'<text x="{cx - 22}" y="{y + 4}" text-anchor="middle">{esc(b)}</text></g>')
    s.append("</g>")
    return "".join(s)


def _arrow(d, step=None, cls="aa"):
    st = f' data-step="{step}"' if step is not None else ""
    return f'<path{st} class="{cls}" d="{d}" marker-end="url(#ah)"/>'


def _rag(x, y, txt, step=None, anchor="start"):
    st = f' data-step="{step}"' if step is not None else ""
    return f'<text{st} class="ab-rag" x="{x}" y="{y}" text-anchor="{anchor}">{esc(txt)}</text>'


def arquitectura(D, room_uri: str, steps=True, badges=False, k=5) -> str:
    S = (lambda n: n) if steps else (lambda n: None)
    B = (lambda *b: list(b)) if badges else (lambda *b: None)
    o = ['<svg class="arch" viewBox="0 0 1712 740" xmlns="http://www.w3.org/2000/svg">',
         '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" '
         'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#5D4F45"/></marker></defs>']
    # carril 1: indexing
    o.append('<text class="ab-lane" x="0" y="22">una vez, offline · indexing</text>')
    y1, h1 = 40, 150
    o.append(_box(0, y1, 370, h1, "Catálogo", [f"IKEA {D['n_ikea']} + ABO {D['n_abo']}",
                                               "foto, tipo, kind, medidas"], badge=B("E12")))
    o.append(_box(447, y1, 370, h1, "Descripción de 8 líneas", ["un VLM mira la foto de cada",
                                                               "producto: 1 documento c/u"], badge=B("E3", "E2")))
    o.append(_box(894, y1, 370, h1, "Embedding de texto", [D["embed_model"] + ", local",
                                                          f"{D['best_dim']} dimensiones"], badge=B("E4", "E2")))
    o.append(_box(1341, y1, 371, h1, "ChromaDB", ["HNSW, coseno", "vector + texto + metadata"],
                  badge=B("E5")))
    for x in (370, 817, 1264):
        o.append(_arrow(f"M{x + 4},{y1 + h1 / 2} H{x + 72}"))
    o.append(_rag(0, 222, "data loading y preprocesamiento"))
    o.append(_rag(447, 222, "splitting: un producto, un documento"))
    o.append(_rag(894, 222, "embedding"))
    o.append(_rag(1341, 222, "base de datos vectorial"))
    # carril 2: por pedido
    o.append('<text class="ab-lane" x="0" y="300">por pedido · retrieval y elección</text>')
    y2, h2 = 318, 156
    o.append(f'<g data-step="{S(1)}" class="ab"><rect x="0" y="{y2}" width="250" height="{h2}" rx="6"/>'
             f'<image href="{room_uri}" x="16" y="{y2 + 16}" width="112" height="84" preserveAspectRatio="xMidYMid slice"/>'
             f'<text class="ab-t" x="142" y="{y2 + 44}">Foto</text><text class="ab-t" x="142" y="{y2 + 74}">+ pedido</text>'
             f'<text class="ab-l" x="16" y="{y2 + 134}">«un living luminoso…»</text></g>'
             if steps else
             f'<g class="ab"><rect x="0" y="{y2}" width="250" height="{h2}" rx="6"/>'
             f'<image href="{room_uri}" x="16" y="{y2 + 16}" width="112" height="84" preserveAspectRatio="xMidYMid slice"/>'
             f'<text class="ab-t" x="142" y="{y2 + 44}">Foto</text><text class="ab-t" x="142" y="{y2 + 74}">+ pedido</text>'
             f'<text class="ab-l" x="16" y="{y2 + 134}">«un living luminoso…»</text></g>')
    o.append(_arrow(f"M254,{y2 + h2 / 2} H318", step=S(1)))
    o.append(_box(322, y2, 380, h2, "plan", ["piezas, kind y tamaño máximo;", "el producto ideal en 8 líneas"],
                  kind="llm", tag="Opus 5.5", step=S(1), badge=B("E6")))
    o.append(_arrow(f"M706,{y2 + h2 / 2} H768", step=S(2)))
    o.append(_box(772, y2, 320, h2, "retrieve", ["filtros where: kind, medidas", f"top-{k} por coseno"],
                  step=S(2), badge=B("E2")))
    o.append(_arrow(f"M1670,{y1 + h1 + 4} V262 H932 V{y2 - 4}", step=S(2)))
    o.append(_arrow(f"M1096,{y2 + h2 / 2} H1158", step=S(3)))
    o.append(_box(1162, y2, 330, h2, "choose", [f"mira las {k} fotos de cada pieza;", "elige combinación y cantidades"],
                  kind="llm", tag="Opus 5.5", step=S(3), badge=B("E8", "E7")))
    o.append(_arrow(f"M1496,{y2 + h2 / 2} H1546", step=S(3)))
    o.append(_box(1550, y2, 162, h2, "Lista", ["de compra:", "productos", "reales"][:2], kind="out", step=S(3)))
    o.append(_rag(322, y2 + h2 + 30, "pre-retrieval: query rewriting", step=S(1)))
    o.append(_rag(772, y2 + h2 + 30, "retrieval + metadata filtering", step=S(2)))
    o.append(_rag(1162, y2 + h2 + 30, "post-retrieval: reranking con VLM", step=S(3)))
    # carril 3: imagen
    o.append(f'<text data-step="{S(4)}" class="ab-lane" x="0" y="580">la imagen · generación</text>' if steps
             else '<text class="ab-lane" x="0" y="580">la imagen · generación</text>')
    y3, h3 = 598, 116
    o.append(_arrow(f"M1631,{y2 + h2 + 4} V{y2 + h2 + 48} H512 V{y3 - 4}", step=S(4)))
    o.append(_box(322, y3, 380, h3, "Prompt de edición estricta", ["«el mismo cuarto, exactamente»"],
                  step=S(4), badge=B("E13")))
    o.append(_arrow(f"M706,{y3 + h3 / 2} H768", step=S(4)))
    o.append(_box(772, y3, 320, h3, "Nano Banana 2", ["edita la foto con los productos"], step=S(4)))
    o.append(_arrow(f"M1096,{y3 + h3 / 2} H1158", step=S(4)))
    o.append(_box(1162, y3, 330, h3, "Control SIFT", [f"¿mismo cuarto? si no, otra (≤{D['sift_attempts']})"],
                  step=S(4), badge=B("E13")))
    o.append(_arrow(f"M1496,{y3 + h3 / 2} H1546", step=S(4)))
    o.append(_box(1550, y3, 162, h3, "Imagen", ["amoblada"], kind="out", step=S(4)))
    o.append(_arrow(f"M1260,{y3 + h3 + 4} V732 H932 V{y3 + h3 + 6}", step=S(4), cls="aa dash"))
    o.append(_rag(1280, 730, "si cambió el cuarto, se reintenta", step=S(4)))
    o.append("</svg>")
    return "".join(o)

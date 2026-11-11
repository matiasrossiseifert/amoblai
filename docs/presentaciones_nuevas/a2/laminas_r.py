"""La réplica de un ambiente real (E14) y los pasos a futuro: decirle al generador dónde va cada
mueble. Ronda 1: el prompt largo del flujo, sin cajas, con rectángulos (2D) y con cajas 3D. Ronda 2:
un prompt corto, el mismo en las seis variantes salvo la línea que dice dónde va cada mueble (sin
decirlo, en palabras, con cajas dibujadas en la foto o en una imagen guía aparte).

Los números salen de datos/resultados/replica/living-dagarna/resultados.json (`amoblai
evaluar-replica`); los prompts, de los prompt.txt que se mandaron en cada variante y de
src/amoblai/prompts/; las variantes, de datos/configs/imagen/replica.yaml. Si los datos cambian y
la lectura de las láminas deja de valer, el build falla (ver los assert)."""

from __future__ import annotations

import json
import re

import yaml

import img
import sala
from base import add, cab, esc, exp, f, usd
from datos_deck import REPO, RES

R = RES / "replica" / "living-dagarna"
CFG = REPO / "datos" / "configs" / "imagen" / "replica.yaml"
NOMBRE = {"802.991.95": "sofá con chaise longue", "702.991.91": "puf", "802.133.09": "mesa ratona",
          "302.837.81": "alfombra", "599.026.58": "estantería", "302.865.67": "lámpara de pie"}
CORTO = {"802.991.95": "sofá", "702.991.91": "puf", "802.133.09": "mesa ratona",
         "302.837.81": "alfombra", "599.026.58": "estantería", "302.865.67": "lámpara"}
# ronda 1: el prompt largo del flujo · ronda 2: un prompt corto común
R1 = [("sin_cajas", "sin cajas"), ("con_cajas", "cajas 2D"), ("con_cajas_3d", "cajas 3D")]
R2 = [("simple_sin_cajas", "sin cajas"), ("simple_texto", "en palabras"), ("simple_cajas", "cajas 2D"),
      ("simple_cajas_guia", "cajas 2D · guía aparte"), ("simple_cajas_3d", "cajas 3D"),
      ("simple_cajas_3d_guia", "cajas 3D · guía aparte")]
NOM = dict(R1) | dict(R2)
# frases que se resaltan en la línea que cambia (tienen que estar, literal)
MARCAS = {"simple_sin_cajas": ["where an interior designer would"],
          "simple_texto": ["where its line says"],
          "simple_cajas": ["drawn on it", "remove the rectangles and numbers"],
          "simple_cajas_guia": ["is the same room", "only a guide"],
          "simple_cajas_3d": ["drawn on it", "remove the boxes and numbers"],
          "simple_cajas_3d_guia": ["is the same room", "only a guide"]}


def _load() -> dict:
    return json.loads((R / "resultados.json").read_text())


def _cfg() -> dict:
    return yaml.safe_load(CFG.read_text())


def _modelo(m: str) -> str:
    x = re.match(r"claude-([a-z]+)-(\d+)-(\d+)$", m)
    return f"{x.group(1).capitalize()} {x.group(2)}.{x.group(3)}" if x else m


def _per_product(res: dict, variant: str) -> dict[str, float]:
    """IoU medio de cada producto en las repeticiones (no detectado = 0)."""
    out: dict[str, list[float]] = {}
    for r in res["variantes"][variant]["imagenes"]:
        for p in r["productos"]:
            out.setdefault(p["id"], []).append(p.get("iou") or 0.0)
    return {k: sum(v) / len(v) for k, v in out.items()}


def _dejo(o: str) -> bool:
    """La observación (revisada a ojo, en replica.yaml) dice que quedaron cajas dibujadas o copiadas."""
    return not o.startswith("limpia") and "sin rastro" not in o and re.search(r"\b(deja|copia)\b", o) is not None


def _dibujadas(res: dict, cfg: dict, v: str) -> int | None:
    """Cuántas imágenes dejaron cajas dibujadas; None si la variante no lleva cajas."""
    if not cfg["variantes"][v].get("cajas"):
        return None
    obs = res["observaciones"]
    ims = [r["imagen"] for r in res["variantes"][v]["imagenes"]]
    falta = [i for i in ims if i not in obs]
    if falta:
        raise ValueError(f"réplica: sin observación para {falta}")
    return sum(_dejo(obs[i]) for i in ims)


def _guia_png(c) -> object:
    return R / ("vacio_con_cajas_3d.png" if c == "3d" else "vacio_con_cajas.png")


def _entra(cv: dict, n_img: int) -> list[tuple[object, str]]:
    """Qué imagen del cuarto recibe el modelo: la foto vacía, la foto con las cajas dibujadas, o la
    vacía y al final la guía."""
    c = cv.get("cajas")
    if not c:
        return [(R / "vacio.png", "1")]
    if cv.get("guia"):
        return [(R / "vacio.png", "1"), (_guia_png(c), str(n_img))]
    return [(_guia_png(c), "1")]


def _prompt(v: str) -> list[str]:
    return (R / v / "prompt.txt").read_text().strip("\n").splitlines()


def _palabras(v: str) -> int:
    return len((R / v / "prompt.txt").read_text().split())


def _cambia(lines: list[str]) -> int:
    """El índice de la línea que dice dónde va cada mueble: entre la lista de productos y «Keep the room»."""
    ult = max(i for i, x in enumerate(lines) if x.startswith("image "))
    keep = next(i for i, x in enumerate(lines) if x.startswith("Keep the room"))
    c = [i for i in range(ult + 1, keep) if lines[i].strip()]
    assert len(c) == 1, c
    return c[0]


def _comun(lines: list[str]) -> list[str]:
    """El prompt sin la línea que cambia y sin el «Where: …» de cada producto."""
    i = _cambia(lines)
    return [re.sub(r"\. Where: .*$", "", x) for j, x in enumerate(lines) if j != i]


def _marcar(txt: str, frases: list[str]) -> str:
    h = esc(txt)
    for m in frases:
        if esc(m) not in h:
            raise ValueError(f"réplica: {m!r} no está en {txt!r}")
        h = h.replace(esc(m), f"<mark>{esc(m)}</mark>", 1)
    return h


def _foto(path, w, h, cap="", sub="", sello="", ok=None, cls="") -> str:
    s = f'<span class="sello{" ok" if ok else ""}">{sello}</span>' if sello else ""
    c = f"<figcaption><b>{cap}</b>{f'<span>{sub}</span>' if sub else ''}</figcaption>" if cap else ""
    return (f'<figure class="rt {cls}"><div class="ri" style="width:{w}px;height:{h}px"><img src="{img.uri(path, w * 2, h * 2, q=74)}" alt="">{s}</div>{c}</figure>')


def _iou(res, v) -> float:
    return res["variantes"][v]["resumen"]["iou_medio"]["media"]


def _lugar(res, v) -> float:
    return res["variantes"][v]["resumen"]["en_su_lugar"]["media"]


def _datos() -> dict:
    """Todo lo que usan las láminas de la réplica, leído y validado una vez."""
    res, cfg = _load(), _cfg()
    for v, _ in R1 + R2:
        x = res["variantes"].get(v)
        if not x or len(x["imagenes"]) < cfg["repeticiones"] or not all((R / r["imagen"]).exists() for r in x["imagenes"]):
            raise ValueError(f"réplica: la variante {v} no está completa")
    # la ronda 2 usa el mismo prompt en las seis variantes, salvo la línea que dice dónde
    base = _comun(_prompt("simple_sin_cajas"))
    for v, _ in R2:
        assert _comun(_prompt(v)) == base, f"réplica: el prompt de {v} difiere en más de una línea"
    n = len(res["productos"])
    dib = {v: _dibujadas(res, cfg, v) for v, _ in R1 + R2}
    mejor = max((v for v, _ in R2), key=lambda v: _iou(res, v))
    assert mejor == "simple_cajas_3d" and dib[mejor] == 0, "réplica: cambió la mejor variante; revisar la lectura"
    assert _iou(res, "simple_cajas_guia") < _iou(res, "simple_cajas") and _iou(res, "simple_cajas_3d_guia") < _iou(res, "simple_cajas_3d")
    assert _iou(res, "simple_sin_cajas") < _iou(res, "simple_texto") < min(_iou(res, "simple_cajas"), _iou(res, "simple_cajas_3d"))
    obs = res["observaciones"]

    def mejor_img(v, cond=lambda o: True):
        ims = [(i, r) for i, r in enumerate(res["variantes"][v]["imagenes"]) if cond(obs[r["imagen"]])]
        return max(ims, key=lambda t: t[1]["iou_medio"])

    lug = json.loads((R / "lugares.json").read_text())
    return dict(res=res, cfg=cfg, n=n, dib=dib, mejor=mejor, obs=obs, lug=lug,
                img_guia=n + 2,
                w1={v: _palabras(v) for v, _ in R1}, w2={v: _palabras(v) for v, _ in R2},
                texto=mejor_img("simple_texto"), cajas3d=mejor_img("simple_cajas_3d", lambda o: not _dejo(o)),
                copia=next((i, r) for i, r in enumerate(res["variantes"]["simple_cajas_guia"]["imagenes"])
                           if obs[r["imagen"]].startswith("copia")))


def resumen() -> dict:
    """Para la lámina 9 · Imagen del recorrido: sin decir dónde y con cajas 3D (ronda 2)."""
    res = _load()
    return dict(n=len(res["productos"]), sin=_lugar(res, "sin_cajas"), cajas3d=_lugar(res, "simple_cajas_3d"),
                iou_sin=_iou(res, "sin_cajas"), iou_3d=_iou(res, "simple_cajas_3d"))


# ---------------------------------------------------------------- E14

def replica_slides(D: dict) -> None:
    res = _load()
    sv = res["variantes"]["sin_cajas"]
    s = sv["resumen"]
    n = len(res["productos"])
    reps = len(sv["imagenes"])
    foto = REPO / res["foto"]
    vac = res["vaciado"]
    v2 = next(t for t in vac["intentos"] if t["imagen"] == vac["elegido"])
    W_, H_ = 380, 220
    kpi = ('<div class="rk">'
           f'<div><b>{s["detectados"]["media"]:.0f}/{n}</b><span>productos presentes en cada imagen</span></div>'
           f'<div><b>{f(s["coseno_producto"]["media"], 2)}</b><span>coseno con la foto del producto (DINOv3)</span></div>'
           f'<div class="acc"><b>{f(s["iou_medio"]["media"], 2)}</b><span>IoU medio con la caja real de cada mueble</span></div></div>')
    tiles = (f'<div data-desde="1" class="rcel">{_foto(foto, W_, H_, "la foto real", "un living del ground truth de IKEA")}</div>'
             f'<div data-desde="1" class="rcel">{_foto(R / "vacio.png", W_, H_, "vaciada con Nano Banana 2", f"intento {vac["elegido"][-5]} de {len(vac["intentos"])} · SSIM fuera de muebles {f(v2["ssim_fuera_de_los_muebles"], 2)}")}</div>'
             f'<div data-desde="2" class="rcel">{kpi}</div>')
    for i, r in enumerate(sv["imagenes"]):
        tiles += (f'<div data-desde="2" class="rcel">{_foto(R / r["imagen"], W_, H_, f"réplica {i + 1}", f"IoU {f(r["iou_medio"], 2)} · {r["en_su_lugar"]} de {n} en su lugar")}</div>')
    exp("E14", 6, "¿Reproduce un living real <em>si le damos sus muebles?</em>",
        "<p>En un ambiente vacío nadie sabe cómo «debería» quedar. Un living del ground truth sí: <strong>la "
        "foto real y sus productos</strong>. Medimos el generador solo, con la lista ya decidida.</p>",
        f"<p>Vaciamos la foto real y la volvimos a amoblar con sus {n} muebles, {reps} veces. ¿Dónde quedó cada "
        f"uno (IoU con su caja real) y es el producto (coseno DINOv3)?</p>"
        "<p class=\"cita\">Una sola habitación: es una prueba, no una medición.</p>",
        f'<div class="rgrid">{tiles}</div>',
        f"<strong>Respeta los productos, no la distribución.</strong> Los {n} aparecen y se reconocen, pero "
        f"cada vez arma su propio living: IoU {f(s['iou_medio']['media'], 2)}, {f(s['en_su_lugar']['media'], 1)} "
        f"de {n} en su lugar. El pedido no dice dónde va cada cosa: para eso hay que decírselo.",
        t=40, ancho=True, rot="De punta a punta", planta=[9], notas=[
            "Un experimento más sobre la imagen. En un ambiente vacío nadie sabe cómo debería quedar; en un "
            "living del ground truth sí: tenemos la foto real y sus productos.",
            f"[paso] La vaciamos con el mismo modelo y la volvimos a amoblar con sus {n} muebles, con el paso de "
            f"imagen del flujo, {reps} veces. Medimos dónde quedó cada uno: el IoU contra su caja en la foto real.",
            f"[paso] Los {n} aparecen y se reconocen, pero arma su propio living: IoU "
            f"{f(s['iou_medio']['media'], 2)}, {f(s['en_su_lugar']['media'], 0)} de {n} en su lugar.",
            "[paso] Respeta los productos, no la distribución: el pedido no dice dónde va cada cosa. Al final "
            "probamos decírselo.",
        ])


# ---------------------------------------------------------------- pasos a futuro

def futuro_slides(D: dict) -> None:
    X = _datos()
    res, cfg, n, dib = X["res"], X["cfg"], X["n"], X["dib"]
    V = res["variantes"]
    foto = REPO / res["foto"]

    # ---------- 1 · ronda 1 y por qué una ronda 2
    guia = {"sin_cajas": R / "vacio.png", "con_cajas": R / "vacio_con_cajas.png", "con_cajas_3d": R / "vacio_con_cajas_3d.png"}
    sub_guia = {"sin_cajas": "la foto vaciada, sin nada más (E14)",
                "con_cajas": "un rectángulo por mueble, como en la foto real",
                "con_cajas_3d": "un prisma por mueble: lugar, orientación y volumen"}
    cols = ""
    GW, GH, TW, TH = 520, 326, 162, 102
    for k, nom in R1:
        thumbs = ""
        for j, r in enumerate(V[k]["imagenes"]):
            dejo = cfg["variantes"][k].get("cajas") and _dejo(X["obs"][r["imagen"]])
            thumbs += _foto(R / r["imagen"], TW, TH, f"{j + 1} · IoU {f(r['iou_medio'], 2)}", cls="mini",
                            sello="cajas dibujadas" if dejo else "")
        cols += (f'<div class="fcol"><div class="fch"><span class="fcn">{nom}</span><span class="etq">{sub_guia[k]}</span></div>'
                 f'{_foto(guia[k], GW, GH)}<div class="fth">{thumbs}</div></div>')
    w1 = X["w1"]
    n2, n3 = len(V["con_cajas"]["imagenes"]), len(V["con_cajas_3d"]["imagenes"])
    body = ('<div class="cuerpo">' + cab("→", "Pasos a futuro · ronda 1", "Decirle dónde: <em>cajas en la foto</em>") + '</div>'
            + f'<div class="fcols r1">{cols}</div>'
            + '<div class="decision" data-desde="1"><div class="k">por qué una ronda 2</div><p>'
              f'<strong>Las cajas quedaban dibujadas</strong>: {dib["con_cajas"]} de {n2} imágenes con rectángulos y '
              f'{dib["con_cajas_3d"]} de {n3} con cajas 3D. Y el prompt era <strong>largo</strong>: '
              f'{min(w1.values())} a {max(w1.values())} palabras, con una lista de prohibiciones.</p></div>')
    add(body, titulo="Futuro · cajas en la foto", cap=8, t=25, notas=[
        "Para decirle dónde, dibujamos en la foto vacía una caja por mueble, donde está en la foto real: "
        "primero rectángulos, después cajas 3D, que además dicen hacia dónde mira y cuánto ocupa.",
        f"[paso] Ayudan, pero hubo dos problemas: el modelo dejaba las cajas dibujadas, en "
        f"{dib['con_cajas'] + dib['con_cajas_3d']} de {n2 + n3} imágenes, y el prompt era largo, una lista de "
        f"prohibiciones. Por eso hicimos una ronda 2.",
    ])

    # ---------- 2 · ronda 2: el prompt común y la línea que cambia
    L = _prompt("simple_sin_cajas")
    ic = _cambia(L)
    ps = ""
    for i, x in enumerate(L):
        if not x.strip():
            continue
        if i == ic:
            ps += f'<p class="cmbt">↓ la línea que cambia en cada variante</p><p class="cambia">{esc(x)}</p>'
        else:
            ps += f"<p>{esc(x)}</p>"
    pn = cfg["variantes"]["simple_sin_cajas"]["prompt"].removesuffix(".md")
    hoja = (f'<div class="hoja pr"><div class="prh"><span>simple_sin_cajas/prompt.txt</span><span>tal como se mandó · {pn}</span></div>'
            f'<div class="prb">{ps}</div></div>'
            f'<p class="nota">{X["w2"]["simple_sin_cajas"]} palabras, igual en las seis salvo esa línea. El de la '
            f'ronda 1 tenía de {min(w1.values())} a {max(w1.values())}.</p>')
    filas = ""
    mas = f'<span class="r2m">+ fotos<br>2 a {n + 1}</span>'
    for v, nom in R2:
        cv = cfg["variantes"][v]
        lines = _prompt(v)
        x = lines[_cambia(lines)]
        if v == "simple_cajas_3d_guia":  # la frase de la caja es la misma de cajas 3D: se recorta
            a = x.index("Box N is")
            b = x.index("tall it is.", a) + len("tall it is.")
            x = x[:a] + "[…]" + x[b:]
        t = f"<p>{_marcar(x, MARCAS[v])}</p>"
        if cv.get("lugares"):
            assert all(" Where: " in y for y in lines if y.startswith("image "))
            t += '<p class="r2x">y cada producto termina en <b>«. Where: …»</b></p>'
        ent = ""
        for j, (p, lab) in enumerate(_entra(cv, X["img_guia"])):
            if j == 1:
                ent += mas
            ent += f'<figure><img src="{img.uri(p, 168, 106, q=70)}" alt=""><figcaption>imagen {lab}</figcaption></figure>'
        if len(_entra(cv, X["img_guia"])) == 1:
            ent += mas
        d = ' data-desde="1"' if not cv.get("cajas") else ' data-desde="2"'
        filas += (f'<div class="r2f"{d}><div class="r2n"><b>{esc(nom)}</b><span>{cv["prompt"].removesuffix(".md").replace("scene_prompt_", "")}</span></div>'
                  f'<div class="r2e">{ent}</div><div class="r2t">{t}</div></div>')
    body = ('<div class="cuerpo">' + cab("→", "Pasos a futuro · ronda 2", "Un prompt corto, <em>y una línea que cambia</em>") + '</div>'
            + f'<div class="r2p"><div class="r2h">{hoja}</div><div class="r2l"><div class="r2c"><span>variante</span><span>qué imágenes recibe</span>'
              f'<span>la línea que cambia · literal</span></div>{filas}</div></div>')
    reps = cfg["repeticiones"]
    add(body, titulo="Futuro · ronda 2, el prompt", cap=8, t=45, notas=[
        f"La ronda 2: seis variantes, {reps} imágenes cada una, con el mismo cuarto vaciado y los mismos {n} "
        f"productos. Todas usan este prompt corto: qué hacer, el pedido, una línea por producto y que el cuarto "
        f"quede igual. Son {X['w2']['simple_sin_cajas']} palabras; el de la ronda 1 llegaba a {max(w1.values())}.",
        "[paso] Cambia una sola línea: cómo dice dónde va cada mueble. Sin cajas, donde lo pondría un "
        "diseñador; en palabras, donde dice cada producto. Las tres de la ronda 1 las rehicimos con este "
        "prompt, para que solo cambie eso.",
        f"[paso] Y cuatro con cajas, 2D o 3D: dibujadas en la foto, y que las borre; o la foto limpia y las "
        f"cajas en una guía aparte, la imagen {X['img_guia']}, que no tiene que copiar.",
    ])

    # ---------- 3 · el lugar en palabras
    lt = _prompt("simple_texto")
    prods = [y for y in lt if y.startswith("image ")]
    ids = [p["id"] for p in res["productos"]]
    ej = [ids.index("599.026.58"), ids.index("302.865.67")]  # estantería y lámpara: las que el texto ubica bien

    def where(y, corta=False):
        a = y.index(" Where: ")
        cab_, w = y[:a], y[a + 1:]
        if corta:
            w = w[:w.index(",", w.index(",") + 1)] + " […]"
        return f"<p>{esc(cab_)} <mark>{esc(w[:6])}</mark>{esc(w[6:])}</p>"

    ps = where(prods[0], corta=True) + '<p class="el">[…]</p>' + "".join(where(prods[i]) for i in ej)
    ps += f'<p class="el">[…]</p><p>{_marcar(lt[_cambia(lt)], MARCAS["simple_texto"])}</p>'
    hoja = (f'<div class="hoja pr"><div class="prh"><span>simple_texto/prompt.txt</span><span>tal como se mandó · extracto</span></div>'
            f'<div class="prb">{ps}</div></div>')
    from laminas_rec import extracto  # noqa: PLC0415 (laminas_rec importa este módulo en una función)
    lug = X["lug"]
    pl = cfg["prompt_lugares"].removesuffix(".md")
    ex = extracto(pl, [dict(l="Image 1 is a photo"), dict(l="For each product", hasta="put it in the same place"),
                       dict(l="For each product", desde="Do not describe", m=["Do not describe what the product looks like."])],
                  titulo="quién lo escribió · extracto literal")
    ti, tr = X["texto"]
    tv = V["simple_texto"]["imagenes"]
    mini = "".join(_foto(R / r["imagen"], 196, 123, f"{j + 1} · IoU {f(r['iou_medio'], 2)}", cls="mini")
                   for j, r in enumerate(tv) if j != ti)
    body = ('<div class="cuerpo">' + cab("→", "Pasos a futuro · ronda 2", "El lugar, <em>en palabras</em>") + '</div>'
            + '<div class="r2w"><div class="r2wl">' + hoja
            + f'<div data-desde="1" class="r2q">{ex}<p class="r2a"><b>{_modelo(lug["modelo"])}</b>, una sola llamada '
              f'({usd(lug["costo_usd"])}), <b>mirando la foto real</b> y la vaciada.</p></div></div>'
            + '<div class="r2wr" data-desde="2"><div class="r2par">'
            + _foto(foto, 400, 251, "la foto real")
            + _foto(R / tr["imagen"], 400, 251, f"en palabras · {ti + 1}", f"IoU {f(tr['iou_medio'], 2)} · {tr['en_su_lugar']} de {n} en su lugar",
                    sello="limpia", ok=True)
            + f'</div><div class="r2par">{mini}</div>'
              '<p class="r2o">Las tres con el mismo arreglo: <b>la estantería y la lámpara donde dice el texto</b>; '
              'el sofá mira a la cámara, no hacia la izquierda.</p></div></div>'
            + '<p class="r2ojo" data-desde="1"><b>Ojo:</b> lo escribió viendo la foto real. Mide si alcanza con decirlo '
              'en palabras, no si un LLM sabe decidir dónde va cada mueble.</p>')
    add(body, titulo="Futuro · el lugar en palabras", cap=8, t=30, notas=[
        "En palabras: cada producto termina en «Where» y una o dos frases: contra qué pared y al lado de qué.",
        f"[paso] Las escribió {_modelo(lug['modelo'])}, en una llamada, mirando la foto real y la vaciada. Ojo: "
        "eso mide si alcanza con decirlo en palabras, no si un LLM sabe dónde van.",
        "[paso] Las tres salieron iguales: la estantería y la lámpara donde dice el texto, y el sofá mirando a "
        "la cámara.",
    ])

    # ---------- 4 · la comparación y la decisión
    IMX = 0.6

    def fila(v, cls=""):
        r = V[v]["resumen"]
        iv = r["iou_medio"]
        d = dib[v]
        nimg = len(V[v]["imagenes"])
        dd = ('<span class="no">—</span>' if d is None else
              f'<span class="{"bien" if d == 0 else "mal"}">{d} de {nimg}</span>')
        return (f'<div class="rtr {cls}"><div class="rn">{esc(NOM[v])}</div>'
                f'<div class="ri2"><i style="width:{iv["media"] / IMX * 100:.0f}%"></i><b>{f(iv["media"], 2)}</b>'
                f'<small>{" · ".join(f(x, 2) for x in iv["valores"])}</small></div>'
                f'<div class="rl">{f(r["en_su_lugar"]["media"], 1)}</div><div class="rd">{dd}</div></div>')

    tab = ('<div class="rtab"><div class="rtr rth"><div></div><div>IoU medio · cada imagen</div><div>en su lugar, de '
           f'{n}</div><div>cajas que quedaron</div></div>'
           f'<div class="rtg">ronda 1 · prompt largo · referencia</div>'
           + "".join(fila(v, "r1") for v, _ in R1)
           + '<div data-desde="1"><div class="rtg g2">ronda 2 · prompt corto, el mismo en las seis</div>'
           + "".join(fila(v, "hi" if v == X["mejor"] else "") for v, _ in R2) + '</div></div>'
           + '<p class="nota">IoU: superposición entre la caja de cada mueble en la generada y en la foto real (1 = la misma). '
             f'{reps} imágenes por variante: una diferencia de 0,05 es ruido.</p>')
    ci, cr = X["cajas3d"]
    gi, gr = X["copia"]
    ims = (_foto(foto, 360, 226, "la foto real", "lo que se quiere reproducir")
           + _foto(R / tr["imagen"], 360, 226, f"en palabras · {ti + 1}", f"IoU {f(tr['iou_medio'], 2)} · {tr['en_su_lugar']} de {n}", sello="limpia", ok=True)
           + _foto(R / cr["imagen"], 360, 226, f"cajas 3D · {ci + 1}", f"IoU {f(cr['iou_medio'], 2)} · {cr['en_su_lugar']} de {n}", sello="limpia", ok=True)
           + _foto(R / gr["imagen"], 360, 226, f"cajas 2D · guía aparte · {gi + 1}", "copió los rectángulos de la guía", sello="copió la guía"))
    m = X["mejor"]
    mr = V[m]["resumen"]
    body = ('<div class="cuerpo">' + cab("→", "Pasos a futuro · ronda 2", "¿Cuál pone cada mueble <em>en su lugar?</em>") + '</div>'
            + f'<div class="r2r"><div>{tab}</div><div class="r2im" data-desde="2">{ims}</div></div>'
            + '<div class="decision" data-desde="3"><div class="k">decisión</div><p>'
              f'<strong>Cajas 3D dibujadas en la foto, con el prompt corto</strong>: IoU {f(mr["iou_medio"]["media"], 2)}, '
              f'{f(mr["en_su_lugar"]["media"], 0)} de {n} en su lugar y ninguna quedó dibujada. La guía aparte se descarta. '
              'El flujo no cambia: sin medidas del ambiente no hay cajas.</p></div>')
    i_ = {v: _iou(res, v) for v, _ in R1 + R2}
    add(body, titulo="Futuro · ronda 2, resultados", cap=8, t=55, notas=[
        f"Los resultados. Arriba, la ronda 1 de referencia: sin cajas, {f(i_['sin_cajas'], 2)} de IoU; con "
        f"rectángulos, {f(i_['con_cajas'], 2)}; con cajas 3D, {f(i_['con_cajas_3d'], 2)}.",
        f"[paso] La ronda 2. El prompt corto no empeora nada: con rectángulos da {f(i_['simple_cajas'], 2)} y con "
        f"cajas 3D {f(i_['simple_cajas_3d'], 2)}, y con tres imágenes eso es ruido; lo que cambia es que con cajas 3D "
        f"ninguna quedó dibujada. En palabras casi duplica a no decir nada, {f(i_['simple_texto'], 2)} contra "
        f"{f(i_['simple_sin_cajas'], 2)}, pero pone pocos muebles en su lugar. Y la guía aparte ubica peor que "
        f"dibujar las cajas, y tampoco evita que aparezcan.",
        "[paso] Acá se ven: la de texto, la mejor con cajas 3D, y una con guía que copió los rectángulos.",
        "[paso] La decisión: el flujo no cambia, porque sin medidas no hay cajas; a futuro, cajas 3D en la foto "
        "y prompt corto. Es un cuarto y tres imágenes: una prueba, no una medición.",
    ])

    # ---------- 5 · el producto, con medidas reales: el cuarto dibujado con cajas a escala
    P = sala.Proj()
    vb = sala.viewbox(P, pad=(60, 120, -40, 190))
    cl = D["img"]["caballito-living"]["choice"]["answer"]["choices"]
    pid = {D["items"][c["id"]]["kind"]: c["id"] for c in cl}

    def dims(k):
        return D["items"][pid[k]].get("dimensions_cm") or {}

    def nom_(k):
        return D["items"][pid[k]]["name"]

    def cm(v):
        return f"{v:.0f}"

    rug, mesa, tv = dims("rug"), dims("coffee table"), dims("TV stand")
    # cajas a escala (1 unidad del dibujo = 1 cm) con la medida del catálogo; si falta, la del dibujo y «?»
    rw, rd = rug.get("width"), rug.get("depth")
    R0 = (211 - (rw or 178) / 2, 274 - (rd or 248) / 2, 0, 211 + (rw or 178) / 2, 274 + (rd or 248) / 2, 2.5)
    mw, mdp = mesa.get("width"), mesa.get("depth")
    M0 = (210 - (mw or 76) / 2, 276 - (mdp or 76) / 2, 0, 210 + (mw or 76) / 2, 276 + (mdp or 76) / 2, 45)
    tw = tv.get("width")
    T0 = (sala.W - 44, 266 - (tw or 180) / 2, 0, sala.W - 2, 266 + (tw or 180) / 2, 52)
    cajas = [("alfombra", R0, True), ("mesa", M0, True), ("tv", T0, True), ("sofa", sala.CAJA["sofa"], False),
             ("lampara", sala.CAJA["lampara"], False), ("planta", sala.CAJA["planta"], False)]
    svg_cajas = ""
    for k, bb, ok in sorted(cajas, key=lambda c: P.depth((c[1][0] + c[1][3]) / 2, (c[1][1] + c[1][4]) / 2, 0)):
        svg_cajas += sala.caja_alambre(P, bb, "caja3d" + ("" if ok else " sin"), k)

    def ct(a, b, off, v, lado=1):
        return sala.cota(P, a, b, off, cm(v) if v else "?", cls="cota" + (" med" if v else ""), lado=lado, fs=19)

    x0, y0, _, x1, y1, _ = R0
    cotas = ct((x0, y1, 0), (x1, y1, 0), (0, 30, 0), rw, -1) + ct((x1, y0, 0), (x1, y1, 0), (30, 0, 0), rd, -1)
    x0, y0, _, x1, y1, z1 = M0
    cotas += ct((x0, y1, z1), (x1, y1, z1), (0, 0, 16), mw) + ct((x1, y0, z1), (x1, y1, z1), (0, 0, 16), mdp)
    x0, y0, _, x1, y1, z1 = T0
    cotas += ct((x1, y0, z1), (x1, y1, z1), (0, 0, 16), tw)
    rots = (sala.rotulo(P, "alfombra", "alfombra " + nom_("rug"), 50, 90, cls="rot acc", pt=(R0[3], R0[4], 0))
            + sala.rotulo(P, "mesa", "mesa ratona " + nom_("coffee table"), -80, 150, cls="rot acc", sub="alto ?", pt=(210, M0[4], 0))
            + sala.rotulo(P, "tv", "mueble de TV " + nom_("TV stand"), 60, 40, cls="rot acc", sub="fondo ? · alto ?", pt=(sala.W - 2, T0[4], 26))
            + sala.rotulo(P, "sofa", "sofá " + nom_("sofa"), -250, 10, cls="rot sinm", sub="sin medidas")
            + sala.rotulo(P, "lampara", "lámpara " + nom_("floor lamp"), -380, -20, cls="rot sinm", sub="sin medidas")
            + sala.rotulo(P, "planta", "planta", 110, 40, cls="rot sinm", sub="sin medidas"))
    W_, D_, H_, T_ = sala.W, sala.D, sala.H, sala.T
    cotas_sala = (sala.cota(P, (0, -T_, H_), (W_ + T_, -T_, H_), (0, 0, 34), "ancho = ?", lado=1, fs=17)
                  + sala.cota(P, (-T_, 0, H_), (-T_, D_, H_), (0, 0, 34), "fondo = ?", lado=1, fs=17)
                  + sala.cota(P, (-T_, -T_, 0), (-T_, -T_, H_), (-30, 0, 0), "alto = ?", lado=1, fs=17))
    svg = (sala.abrir(P, vb, attrs='style="position:absolute;left:690px;top:222px;width:1160px"')
           + sala.cascara(P, cotas=False) + cotas_sala
           + f'<g data-desde="1">{svg_cajas}{cotas}{rots}</g></svg>')
    pasos = [
        ("1", "Medir el ambiente", "Una app con el <strong>LiDAR</strong> del teléfono escanea paredes, aberturas y medidas. Hoy el dibujo dice «?»."),
        ("2", "Medidas de cada producto", "De la metadata del catálogo: la <strong>caja 3D a escala</strong> de cada mueble. En rojo, los que no las tienen."),
        ("3", "Ubicar las cajas", "<b>a.</b> <strong>La IA decide</strong> en el plano. <b>b.</b> Una primera generación pone los muebles "
              "<strong>así nomás</strong> y se toma su lugar. <b>c.</b> Sin medir nada, ya: que el plan lo diga <strong>en palabras</strong>."),
        ("4", "Generar", "Cada mueble llena su <strong>caja 3D, dibujada en la foto</strong>, con el prompt corto de la ronda 2."),
    ]
    lst = "".join(f'<div class="fp" data-desde="{i}"><i>{n_}</i><div><b>{t}</b><p>{x}</p></div></div>' for i, (n_, t, x) in enumerate(pasos))
    body = ('<div class="cuerpo">' + cab("→", "Pasos a futuro", "El producto, <em>con medidas reales</em>") + '</div>'
            + f'<div class="fps">{lst}'
            + '<div class="fmas" data-desde="3"><span class="etq">más adelante</span><p>Con <strong>modelos 3D</strong> de los productos, si el '
              'negocio los tiene, en lugar de cajas: se ubica el modelo en el cuarto escaneado y el generador solo lo hace verse real.</p></div>'
            + '</div>' + svg)
    add(body, titulo="Futuro · con medidas reales", cap=8, t=30, cls="lam-medidas", notas=[
        "Y cómo sería en el producto. Uno: medir el ambiente con el LiDAR del teléfono; hoy las cotas dicen «?».",
        "[paso] Dos: la caja 3D de cada producto, con las medidas del catálogo; en rojo, los que no las tienen.",
        "[paso] Tres: ubicar las cajas, que lo decida la IA o una primera generación. Sin medir nada, se puede "
        "probar ya que el plan lo diga en palabras.",
        "[paso] Cuatro: generar con las cajas 3D dibujadas en la foto y el prompt corto.",
    ])


# ---------------------------------------------------------------- anexo

def replica_anexo(D: dict, letra_img: str, letra_mueble: str) -> None:
    X = _datos()
    res, cfg, n, dib = X["res"], X["cfg"], X["n"], X["dib"]
    V = res["variantes"]
    obs = X["obs"]
    cols = ""
    for v, nom in R2:
        ims = ""
        for j, r in enumerate(V[v]["imagenes"]):
            dejo = cfg["variantes"][v].get("cajas") and _dejo(obs[r["imagen"]])
            ims += _foto(R / r["imagen"], 270, 156, f"{j + 1} · IoU {f(r['iou_medio'], 2)} · {r['en_su_lugar']} de {n}",
                         obs[r["imagen"]], cls="mini", sello="cajas dibujadas" if dejo else "")
        cols += (f'<div class="axc"><div class="axh"><b>{esc(nom)}</b><span>IoU {f(_iou(res, v), 2)} · '
                 f'{f(_lugar(res, v), 1)} de {n}</span></div>{ims}</div>')
    body = ('<div class="cuerpo">' + cab(letra_img, "Anexo · réplica", "La ronda 2, <em>imagen por imagen</em>") + '</div>'
            + f'<div class="axg">{cols}</div>')
    add(body, titulo="Réplica, ronda 2: las imágenes", cap=9, t=0, anexo=letra_img, notas=[
        f"Lámina de respaldo: las {len(R2) * cfg['repeticiones']} imágenes de la ronda 2, con su IoU, cuántos muebles "
        "quedaron en su lugar y lo que se ve a ojo (las observaciones de replica.yaml).",
    ])

    per = {v: _per_product(res, v) for v, _ in R1 + R2}
    ids = [p["id"] for p in res["productos"]]
    hdr = ('<div class="amh">variante</div><div class="amh">palabras del prompt</div>'
           + "".join(f'<div class="amh">{CORTO[i]}</div>' for i in ids) + '<div class="amh">IoU medio</div>')

    def celda(x):
        return f'<div class="amv" style="--a:{min(1.0, x / 0.9):.2f}"><b>{f(x, 2)}</b></div>'

    rows = ""
    for ronda, VV in (("ronda 1 · prompt largo", R1), ("ronda 2 · prompt corto", R2)):
        rows += f'<div class="amg">{ronda}</div>'
        for v, nom in VV:
            w = (X["w1"] | X["w2"])[v]
            rows += (f'<div class="amn{" hi" if v == X["mejor"] else ""}">{esc(nom)}</div><div class="amw">{w}</div>'
                     + "".join(celda(per[v][i]) for i in ids) + f'<div class="amt">{f(_iou(res, v), 2)}</div>')
    body = ('<div class="cuerpo">' + cab(letra_mueble, "Anexo · réplica", "El IoU <em>de cada mueble</em>") + '</div>'
            + f'<div class="amtab">{hdr}{rows}</div>'
            + f'<p class="nota amno">Media de {cfg["repeticiones"]} imágenes por variante; un mueble no detectado cuenta 0. '
              'Las palabras de «en palabras» incluyen las frases de dónde va cada producto.</p>')
    add(body, titulo="Réplica: el IoU de cada mueble", cap=9, t=0, anexo=letra_mueble, notas=[
        "Lámina de respaldo: el IoU de cada mueble en las nueve variantes. Las cajas ubican sobre todo los "
        "muebles grandes (estantería, sofá, alfombra); sin decir dónde, la estantería va siempre a la derecha.",
    ])

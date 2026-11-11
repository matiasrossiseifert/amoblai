"""La réplica de un ambiente real (E14) y los pasos a futuro: cajas en la foto (sin cajas, cajas 2D y
cajas 3D) y el producto con medidas reales. Los números salen de
datos/resultados/replica/living-dagarna/resultados.json (`amoblai evaluar-replica`); la variante
con_cajas_3d se lee si ya está, y si no se marca como pendiente."""

from __future__ import annotations

import json

import img
import sala
from base import add, bloque, cab, esc, exp, f, llamada, medidas, remate
from datos_deck import REPO, RES

R = RES / "replica" / "living-dagarna"
NOMBRE = {"802.991.95": "sofá con chaise longue", "702.991.91": "puf", "802.133.09": "mesa ratona",
          "302.837.81": "alfombra", "599.026.58": "estantería", "302.865.67": "lámpara de pie"}
CORTO = {"802.991.95": "sofá", "702.991.91": "puf", "802.133.09": "mesa ratona",
         "302.837.81": "alfombra", "599.026.58": "estantería", "302.865.67": "lámpara"}
VAR = [("sin_cajas", "sin cajas"), ("con_cajas", "cajas 2D"), ("con_cajas_3d", "cajas 3D")]


def _load() -> dict:
    return json.loads((R / "resultados.json").read_text())


def _per_product(res: dict, variant: str) -> dict[str, float]:
    """IoU medio de cada producto en las repeticiones (no detectado = 0)."""
    out: dict[str, list[float]] = {}
    for r in res["variantes"][variant]["imagenes"]:
        for p in r["productos"]:
            out.setdefault(p["id"], []).append(p.get("iou") or 0.0)
    return {k: sum(v) / len(v) for k, v in out.items()}


def _hay(res, v) -> bool:
    """La variante está completa: tantas imágenes como sin cajas, todas en disco y con su resumen."""
    x = res["variantes"].get(v)
    if not x:
        return False
    ims = x.get("imagenes") or []
    n = len(res["variantes"]["sin_cajas"]["imagenes"])
    return (len(ims) >= n and all((R / r["imagen"]).exists() for r in ims)
            and (x.get("resumen") or {}).get("iou_medio", {}).get("media") is not None)


def _dibujadas(res, v):
    """Cuántas imágenes dejaron las cajas dibujadas, según las observaciones escritas a mano."""
    obs = res.get("observaciones", {})
    ims = [r["imagen"] for r in res["variantes"][v]["imagenes"]]
    if not all(i in obs for i in ims):
        return None
    return sum(1 for i in ims if "deja" in obs[i] and "sin rastro" not in obs[i])


def _foto(path, w, h, cap="", sub="", sello="", ok=None, cls="") -> str:
    s = f'<span class="sello{" ok" if ok else ""}">{sello}</span>' if sello else ""
    c = f"<figcaption><b>{cap}</b>{f'<span>{sub}</span>' if sub else ''}</figcaption>" if cap else ""
    return (f'<figure class="rt {cls}"><div class="ri" style="width:{w}px;height:{h}px"><img src="{img.uri(path, w * 2, h * 2, q=74)}" alt="">{s}</div>{c}</figure>')


def _pendiente(w, h, texto="pendiente", sub="la corrida con cajas 3D todavía no terminó") -> str:
    return (f'<figure class="rt"><div class="ri pend" style="width:{w}px;height:{h}px"><span class="chip pend">{texto}</span>'
            f'<small>{sub}</small></div></figure>')


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
        t=70, ancho=True, rot="De punta a punta", notas=[
            "Un experimento más sobre la imagen, que se nos ocurrió mirando el ground truth. En los ambientes "
            "vacíos no tenemos con qué comparar la imagen: nadie sabe cómo debería quedar. Pero un living del "
            "ground truth sí lo tiene: la foto real, y la lista de sus productos. Queríamos medir el generador "
            "solo, con la lista ya decidida, sin el retrieval en el medio.",
            f"[paso] Tomamos la foto real y la vaciamos con el mismo modelo de imagen. Hicieron falta "
            f"{len(vac['intentos'])} intentos: el primero abrió el encuadre y dejó una lámpara; el segundo "
            f"conserva la puerta, las cortinas, la ventana y el piso. Después la volvimos a amoblar con sus {n} "
            f"muebles anotados, con el paso de imagen del flujo tal cual, {reps} veces. Y comparamos con la foto "
            f"real: dónde quedó cada mueble, como IoU entre su caja y la de la foto real, y si es el producto, con "
            f"el coseno de DINOv3. Es una sola habitación: es una prueba, no una medición.",
            f"[paso] Los {n} productos aparecen en todas, y se reconocen: coseno "
            f"{f(s['coseno_producto']['media'], 2)}. Pero cada vez arma su propio living: el sofá a la izquierda, "
            f"la estantería a la derecha. El IoU medio con las cajas reales es {f(s['iou_medio']['media'], 2)}: en "
            f"promedio, {f(s['en_su_lugar']['media'], 1)} de {n} muebles quedan en su lugar.",
            "[paso] La conclusión: el generador respeta los productos, no la distribución. Y no es un error: el "
            "pedido no dice dónde va cada cosa. Si queremos controlar dónde, hay que decírselo. Eso es lo que "
            "probamos al final, como paso a futuro.",
        ])


# ---------------------------------------------------------------- pasos a futuro

def futuro_slides(D: dict) -> None:
    res = _load()
    n = len(res["productos"])
    hay3 = _hay(res, "con_cajas_3d")
    V = {k: res["variantes"][k] for k, _ in VAR if k in res["variantes"] and (k != "con_cajas_3d" or hay3)}
    guia = {"sin_cajas": R / "vacio.png", "con_cajas": R / "vacio_con_cajas.png", "con_cajas_3d": R / "vacio_con_cajas_3d.png"}
    sub_guia = {"sin_cajas": "la foto vaciada, sin nada más (E14)",
                "con_cajas": "un rectángulo por mueble, donde está en la foto real",
                "con_cajas_3d": "un prisma por mueble: lugar, orientación y volumen"}

    # ---------- 1 · la idea y las imágenes
    cols = ""
    GW, GH, TW, TH = 560, 351, 176, 110
    for i, (k, nom) in enumerate(VAR):
        d = "" if i == 0 else f' data-desde="{i}"'
        gfig = _foto(guia[k], GW, GH) if guia[k].exists() else _pendiente(GW, GH)
        if k in V:
            thumbs = ""
            for j, r in enumerate(V[k]["imagenes"]):
                thumbs += _foto(R / r["imagen"], TW, TH, f"{j + 1} · IoU {f(r['iou_medio'], 2)}", cls="mini")
        else:
            thumbs = "".join(_pendiente(TW, TH, "pendiente" if j == 1 else "—", "") for j in range(len(res["variantes"]["sin_cajas"]["imagenes"])))
        cols += (f'<div class="fcol"{d}><div class="fch"><span class="fcn">{nom}</span><span class="etq">{sub_guia[k]}</span></div>'
                 f'{gfig}<div class="fth">{thumbs}</div></div>')
    body = ('<div class="cuerpo">' + cab("→", "Pasos a futuro", "Decirle dónde: <em>cajas en la foto</em>",
                                         "Dibujar en la foto vacía dónde va cada mueble y cuánto ocupa, y pedirle al "
                                         "generador que cada mueble llene su caja. Misma habitación y mismos muebles de E14.") + '</div>'
            + f'<div class="fcols">{cols}</div>')
    t2 = res["variantes"]["con_cajas"]
    add(body, titulo="Futuro · cajas en la foto", cap=8, t=45, notas=[
        "Para terminar, hacia dónde iría el producto. E14 mostró que el generador pone los productos pero "
        "decide él dónde. La idea: dibujar en la foto vacía una caja por mueble, donde tiene que ir y cuánto "
        "ocupa, y pedirle que cada mueble llene su caja. A la izquierda, las tres réplicas sin cajas de recién.",
        f"[paso] Primero con cajas planas, rectángulos, en el lugar exacto de cada mueble en la foto real: "
        f"{len(t2['imagenes'])} imágenes.",
        ("[paso] Y con cajas 3D: un prisma por mueble, apoyado en el piso, que además dice para dónde está "
         "girado y cuánto ocupa hacia el fondo." if hay3 else
         "[paso] Y con cajas 3D: un prisma por mueble, apoyado en el piso, que además dice para dónde está "
         "girado y cuánto ocupa hacia el fondo. Las imágenes con cajas 3D están pendientes."),
    ])

    # ---------- 2 · los números
    per = {k: _per_product(res, k) for k in V}
    ids = [p["id"] for p in res["productos"]]
    ids.sort(key=lambda k: -(per["con_cajas"][k] - per["sin_cajas"][k]))

    def celda(k, txt, cls=""):
        return f'<div class="kv {cls}">{txt}</div>' if k in V else '<div class="kv pend"><span class="chip pend">pendiente</span></div>'

    tab = '<div class="ktab"><div class="kh"></div>' + "".join(f'<div class="kh">{nom}</div>' for _, nom in VAR)
    filas = [
        ("IoU medio con la caja real", lambda k: f(V[k]["resumen"]["iou_medio"]["media"], 2), "acc"),
        (f"muebles en su lugar, de {n}", lambda k: f(V[k]["resumen"]["en_su_lugar"]["media"], 1), ""),
        ("coseno con la foto del producto", lambda k: f(V[k]["resumen"]["coseno_producto"]["media"], 2), ""),
        ("imágenes con las cajas dibujadas", lambda k: (lambda x: "—" if k == "sin_cajas" else ("sin revisar" if x is None else f"{x} de {len(V[k]['imagenes'])}"))(_dibujadas(res, k)), ""),
    ]
    for nom, fn, cls in filas:
        tab += f'<div class="kl">{nom}</div>' + "".join(celda(k, fn(k) if k in V else "", cls) for k, _ in VAR)
    tab += "</div>"
    # IoU por mueble: tres barras por producto
    colv = {"sin_cajas": "#9AA4AF", "con_cajas": "#2453D6", "con_cajas_3d": "#FF9A3D"}
    bars = ""
    for pid in ids:
        bars += f'<div class="pp"><span class="ppn">{CORTO[pid]}</span><div class="ppb">'
        for k, _ in VAR:
            if k in per:
                v = per[k][pid]
                bars += f'<div class="ppr"><i style="width:{v * 100:.0f}%;background:{colv[k]}"></i><b>{f(v, 2)}</b></div>'
            else:
                bars += '<div class="ppr pend"><i></i><b>pend.</b></div>'
        bars += "</div></div>"
    s, c = V["sin_cajas"]["resumen"], V["con_cajas"]["resumen"]
    d2 = _dibujadas(res, "con_cajas")
    extra3 = ""
    if "con_cajas_3d" in V:
        c3 = V["con_cajas_3d"]["resumen"]
        d3 = _dibujadas(res, "con_cajas_3d")
        gana = max(ids, key=lambda k: per["con_cajas_3d"][k] - per["con_cajas"][k])
        extra3 = (f" Con cajas 3D: IoU {f(c3['iou_medio']['media'], 2)} y {f(c3['en_su_lugar']['media'], 1)} de {n} en su "
                  f"lugar" + (f"; {d3} de {len(V['con_cajas_3d']['imagenes'])} con las cajas dibujadas" if d3 is not None else "")
                  + f". La que más gana es la {CORTO[gana]} ({f(per['con_cajas'][gana], 2)} → "
                  f"{f(per['con_cajas_3d'][gana], 2)}): su caja 3D llega al piso.")
    body = ('<div class="cuerpo">' + cab("→", "Pasos a futuro", "¿Las cajas ponen cada mueble <em>en su lugar?</em>") + '</div>'
            + '<div class="fnum"><div class="fnl">' + tab
            + '<p class="nota">IoU: superposición entre la caja de cada mueble en la imagen generada y en la foto real (1 = la misma). '
              'Tres imágenes por variante: es una pista, no un resultado.</p></div>'
            + '<div class="fnr" data-desde="1"><div class="ley">'
            + "".join(f'<span><i style="background:{colv[k]}"></i>{nom}</span>' for k, nom in VAR)
            + '<span>IoU por mueble</span></div>' + f'<div class="ppl">{bars}</div></div></div>'
            + f'<div class="decision" data-desde="2"><div class="k">lo que vimos</div><p><strong>Las cajas ubican los muebles grandes</strong> '
              f'(estantería, sofá, alfombra); los chicos que se superponen, no. El modelo tiende a dejarlas dibujadas: habría que '
              f'pasarlas como máscara.{esc(extra3)}</p></div>')
    add(body, titulo="Futuro · cuánto ayudan las cajas", cap=8, t=45, notas=[
        f"Los números. Con cajas planas, el IoU medio sube de {f(s['iou_medio']['media'], 2)} a "
        f"{f(c['iou_medio']['media'], 2)}, y los muebles en su lugar de {f(s['en_su_lugar']['media'], 1)} a "
        f"{f(c['en_su_lugar']['media'], 1)}. El producto se sigue reconociendo igual."
        + (f" Y un problema: en {d2} de las {len(t2['imagenes'])} imágenes el modelo dejó las cajas dibujadas, y "
           f"hasta las movió." if d2 is not None else "")
        + ("" if "con_cajas_3d" in V else " La columna de cajas 3D queda pendiente."),
        "[paso] Por mueble se ve dónde funciona: la estantería, el sofá y la alfombra van a su caja; el puf, la "
        "mesa ratona y la lámpara, que se superponen con otros, no.",
        "[paso] Lo que vimos: las cajas sirven para los muebles grandes, pero hay que pasarlas de otra forma, "
        "por ejemplo como una máscara aparte, o borrarlas en un segundo paso. Son tres imágenes por variante: "
        "es una pista, no un resultado.",
    ])

    # ---------- 3 · el producto, con medidas reales: el cuarto dibujado con cajas a escala
    P = sala.Proj()
    vb = sala.viewbox(P, pad=(60, 120, -40, 190))
    cl = D["img"]["caballito-living"]["choice"]["answer"]["choices"]
    pid = {D["items"][c["id"]]["kind"]: c["id"] for c in cl}

    def dims(k):
        return D["items"][pid[k]].get("dimensions_cm") or {}

    def nom(k):
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
    rots = (sala.rotulo(P, "alfombra", "alfombra " + nom("rug"), 50, 90, cls="rot acc", pt=(R0[3], R0[4], 0))
            + sala.rotulo(P, "mesa", "mesa ratona " + nom("coffee table"), -80, 150, cls="rot acc", sub="alto ?", pt=(210, M0[4], 0))
            + sala.rotulo(P, "tv", "mueble de TV " + nom("TV stand"), 60, 40, cls="rot acc", sub="fondo ? · alto ?", pt=(sala.W - 2, T0[4], 26))
            + sala.rotulo(P, "sofa", "sofá " + nom("sofa"), -250, 10, cls="rot sinm", sub="sin medidas")
            + sala.rotulo(P, "lampara", "lámpara " + nom("floor lamp"), -380, -20, cls="rot sinm", sub="sin medidas")
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
        ("3", "Ubicar las cajas", "<b>a.</b> <strong>La IA decide</strong> en el plano. <b>b.</b> Una primera generación pone los muebles <strong>así nomás</strong> y se toma su lugar."),
        ("4", "Generar", "Cada mueble llena su caja: <strong>tamaño y lugar reales</strong>."),
    ]
    lst = "".join(f'<div class="fp" data-desde="{i}"><i>{n_}</i><div><b>{t}</b><p>{x}</p></div></div>' for i, (n_, t, x) in enumerate(pasos))
    body = ('<div class="cuerpo">' + cab("→", "Pasos a futuro", "El producto, <em>con medidas reales</em>") + '</div>'
            + f'<div class="fps">{lst}'
            + '<div class="fmas" data-desde="3"><span class="etq">más adelante</span><p>Con <strong>modelos 3D</strong> de los productos, si el '
              'negocio los tiene, en lugar de cajas: se ubica el modelo en el cuarto escaneado y el generador solo lo hace verse real.</p></div>'
            + '</div>' + svg)
    add(body, titulo="Futuro · con medidas reales", cap=8, t=60, cls="lam-medidas", notas=[
        "Y cómo se vería en el producto, sobre nuestro cuarto dibujado. Uno: medir el ambiente, con una app "
        "móvil que use el LiDAR del teléfono para escanear el cuarto: paredes, aberturas y medidas reales. Hoy "
        "las cotas del dibujo dicen «?».",
        "[paso] Dos: las medidas de cada producto en la metadata del catálogo, para tener su caja 3D a escala. "
        "Acá están las del living de la portada: la alfombra y la mesa ratona tienen ancho y fondo, el mueble "
        "de la tele solo el ancho; el sofá, la lámpara y la planta no tienen ninguna.",
        "[paso] Tres: ubicar las cajas, de dos maneras: que la IA decida en el plano dónde va cada una, o que "
        "un primer paso de generación ponga los muebles así nomás, y tomar dónde quedó cada uno para poner ahí "
        "su caja a escala.",
        "[paso] Cuatro: generar, con cada mueble llenando su caja, en su tamaño y lugar reales. Más adelante, "
        "si el negocio tiene modelos 3D de los productos, se usan en lugar de las cajas: se ubica el modelo en "
        "el cuarto escaneado y el generador solo tiene que hacerlo verse real.",
    ])

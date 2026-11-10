"""El experimento de réplica (E14) y los pasos a futuro con cajas. Los números salen de
datos/resultados/replica/living-dagarna/resultados.json (`amoblai evaluar-replica`)."""

from __future__ import annotations

import json

from base import add, blk, exp, f, hd
from componentes import img_uri
from datos_deck import REPO, RES

R = RES / "replica" / "living-dagarna"
# Los 6 muebles, en castellano (los nombres del dataset vienen sin tildes ni diéresis).
NOMBRE = {"802.991.95": "sofá con chaise longue", "702.991.91": "puf", "802.133.09": "mesa ratona",
          "302.837.81": "alfombra", "599.026.58": "estantería", "302.865.67": "lámpara de pie"}
CORTO = {"802.991.95": "sofá", "702.991.91": "puf", "802.133.09": "mesa ratona",
         "302.837.81": "alfombra", "599.026.58": "estantería", "302.865.67": "lámpara"}


def _load() -> dict:
    return json.loads((R / "resultados.json").read_text())


def _per_product(res: dict, variant: str) -> dict[str, float]:
    """IoU medio de cada producto en las repeticiones (no detectado = 0)."""
    rows = res["variantes"][variant]["imagenes"]
    out: dict[str, list[float]] = {}
    for r in rows:
        for p in r["productos"]:
            out.setdefault(p["id"], []).append(p.get("iou") or 0.0)
    return {k: sum(v) / len(v) for k, v in out.items()}


def _tile(path, cap: str, sub: str = "", badge: str = "", ok: bool | None = None) -> str:
    b = ""
    if badge:
        b = f'<span class="rbadge{" ok" if ok else ""}">{badge}</span>'
    s = f"<span>{sub}</span>" if sub else ""
    return (f'<figure class="rt"><div class="rimg"><img src="{img_uri(path, 560, 352, q=74)}" alt="">{b}</div>'
            f"<figcaption><b>{cap}</b>{s}</figcaption></figure>")


def replica_slides(D: dict) -> None:
    res = _load()
    sv, cv = res["variantes"]["sin_cajas"], res["variantes"]["con_cajas"]
    s = sv["resumen"]
    n = len(res["productos"])
    reps = len(sv["imagenes"])
    foto = REPO / res["foto"]
    vac = res["vaciado"]
    v2 = next(t for t in vac["intentos"] if t["imagen"] == vac["elegido"])

    tiles = (_tile(foto, "la foto real", "living del ground truth de IKEA")
             + _tile(R / "vacio.png", "vaciada con Nano Banana 2",
                     f"intento {vac['elegido'][-5]} de {len(vac['intentos'])} · SSIM fuera de los muebles {f(v2['ssim_fuera_de_los_muebles'], 2)}")
             + '<div class="rk"><div class="rkn">' + f"{s['detectados']['media']:.0f}/{n}" + '</div>'
             '<div class="rkl">productos presentes en cada imagen</div>'
             f'<div class="rkn">{f(s["coseno_producto"]["media"], 2)}</div><div class="rkl">coseno con la foto del producto (DINOv3)</div>'
             f'<div class="rkn t">{f(s["iou_medio"]["media"], 2)}</div><div class="rkl">IoU medio con la caja real de cada mueble</div></div>')
    for i, r in enumerate(sv["imagenes"]):
        tiles += _tile(R / r["imagen"], f"réplica {i + 1}",
                       f"IoU {f(r['iou_medio'], 2)} · {r['en_su_lugar']} de {n} en su lugar")
    res_html = f'<div class="rgrid">{tiles}</div>'
    exp("E14", "De punta a punta", "¿El generador reproduce un ambiente real <em>si sabe qué muebles van?</em>",
        "<p>En los ambientes vacíos no hay con qué comparar la imagen: nadie sabe cómo «debería» quedar.</p>"
        "<p>Un living del ground truth sí lo tiene: <strong>la foto real y sus productos anotados</strong>. "
        "Queríamos medir el generador solo, con la lista ya decidida: acá no se prueba el retrieval.</p>",
        f"<ul><li>Vaciamos la foto real con el modelo de imagen.</li>"
        f"<li>La volvimos a amoblar con sus {n} muebles anotados y el paso de imagen del flujo, "
        f"{reps} veces.</li><li>Comparamos con la foto real: dónde quedó cada mueble (IoU de su caja "
        f"con la real) y si es el producto (coseno DINOv3).</li></ul>"
        "<p class=\"why\">Una sola habitación: es una prueba, no una medición.</p>",
        res_html,
        f"<strong>Respeta los productos, no la distribución.</strong> Los {n} aparecen y se reconocen, "
        f"pero cada vez arma su propio living: IoU {f(s['iou_medio']['media'], 2)}, "
        f"{f(s['en_su_lugar']['media'], 1)} de {n} en su lugar. No es un error: el pedido no dice dónde "
        f"va cada cosa. Para eso hay que decírselo.",
        t=75, wide=True, notes=[
            "Un experimento más sobre la imagen, que se nos ocurrió mirando el ground truth. En los "
            "ambientes vacíos no tenemos con qué comparar la imagen: nadie sabe cómo debería quedar. "
            "Pero un living del ground truth sí lo tiene: la foto real, y la lista de sus productos. "
            "Queríamos medir el generador solo, con la lista ya decidida, sin el retrieval en el medio.",
            f"[paso] Tomamos la foto real y la vaciamos con el mismo modelo de imagen. Hicieron falta "
            f"{len(vac['intentos'])} intentos: el primero abrió el encuadre y dejó una lámpara; el segundo "
            f"conserva la puerta, las cortinas, la ventana y el piso. Después la volvimos a amoblar con sus "
            f"{n} muebles anotados, con el paso de imagen del flujo tal cual, {reps} veces. Y comparamos "
            f"con la foto real: dónde quedó cada mueble, como IoU entre su caja y la de la foto real, y si es "
            f"el producto, con el coseno de DINOv3. Es una sola habitación: es una prueba, no una medición.",
            f"[paso] Los {n} productos aparecen en todas, y se reconocen: coseno "
            f"{f(s['coseno_producto']['media'], 2)}. Pero cada vez arma su propio living: el sofá a la "
            f"izquierda, la estantería a la derecha. El IoU medio con las cajas reales es "
            f"{f(s['iou_medio']['media'], 2)}: en promedio, {f(s['en_su_lugar']['media'], 1)} de {n} muebles "
            f"quedan en su lugar.",
            "[paso] La conclusión: el generador respeta los productos, no la distribución. Y no es un "
            "error: el pedido no dice dónde va cada cosa. Si queremos controlar dónde, hay que decírselo. "
            "Eso es lo que probamos al final, como paso a futuro.",
        ])


def futuro_slides(D: dict) -> None:
    res = _load()
    sv, cv = res["variantes"]["sin_cajas"], res["variantes"]["con_cajas"]
    s, c = sv["resumen"], cv["resumen"]
    n = len(res["productos"])
    obs = res.get("observaciones", {})
    ps, pc = _per_product(res, "sin_cajas"), _per_product(res, "con_cajas")
    left_drawn = [r["imagen"] for r in cv["imagenes"] if "deja las cajas" in obs.get(r["imagen"], "")]

    # ---------- pasos a futuro 1: el mini-experimento con cajas
    tiles = _tile(R / "vacio_con_cajas.png", "la foto vaciada, con cajas",
                  "cada caja: donde está el mueble en la foto real")
    for i, r in enumerate(cv["imagenes"]):
        drawn = r["imagen"] in left_drawn
        tiles += _tile(R / r["imagen"], f"con cajas {i + 1}",
                       f"IoU {f(r['iou_medio'], 2)} · {r['en_su_lugar']} de {n} en su lugar",
                       badge="quedaron las cajas" if drawn else "limpia", ok=not drawn)
    order = sorted(ps, key=lambda k: -(pc[k] - ps[k]))
    bars = ""
    for k in order:
        bars += (f'<div class="pp"><span class="pn">{CORTO[k]}</span>'
                 f'<span class="pb"><i class="a" style="width:{ps[k] * 100:.0f}%"></i></span><span class="pv">{f(ps[k], 2)}</span>'
                 f'<span class="pb"><i class="b" style="width:{pc[k] * 100:.0f}%"></i></span><span class="pv t">{f(pc[k], 2)}</span></div>')
    body = hd("Pasos a futuro", "Decirle dónde: <em>cajas en la foto</em>")
    body += (
        '<div class="fx">'
        '<div class="fxl">'
        + blk("La idea", "<p>Dibujar en la foto vacía una <strong>caja por mueble</strong>, donde tiene que "
              "ir y cuánto ocupa, y pedirle al generador que cada mueble <strong>llene su caja</strong>.</p>")
        + blk("La prueba", f"<p>La misma habitación y los mismos {n} muebles de E14, con las cajas en el "
              f"lugar exacto de cada mueble en la foto real: {len(cv['imagenes'])} imágenes con cajas contra "
              f"las {len(sv['imagenes'])} sin cajas.</p>", step=1)
        + '<div data-step="2"><div class="fxk">'
        f'<div><span class="fxn">{f(s["iou_medio"]["media"], 2)} → <b>{f(c["iou_medio"]["media"], 2)}</b></span><span class="fxl2">IoU medio con las cajas reales</span></div>'
        f'<div><span class="fxn">{f(s["en_su_lugar"]["media"], 1)} → <b>{f(c["en_su_lugar"]["media"], 1)}</b></span><span class="fxl2">muebles en su lugar, de {n}</span></div>'
        f'<div><span class="fxn">{len(left_drawn)} de {len(cv["imagenes"])}</span><span class="fxl2">con las cajas todavía dibujadas</span></div>'
        '</div><div class="lbl" style="margin-top:22px">IoU por mueble · <span style="color:#7E858C">sin</span> → <span style="color:var(--terracota)">con cajas</span></div>'
        f'<div class="ppl">{bars}</div></div>'
        "</div>"
        f'<div class="fxr" data-step="2"><div class="rgrid g2">{tiles}</div></div></div>'
        '<div class="dec" data-step="3"><div class="k">Lo que vimos</div><p><strong>Las cajas ubican los muebles '
        'grandes</strong> (estantería, sofá, alfombra); los chicos que se superponen, no. Y el modelo tiende a '
        'dejarlas dibujadas: habría que pasarlas aparte, como máscara, o borrarlas en un segundo paso.</p></div>')
    add(body, sec="Pasos a futuro", title="Futuro · cajas en la foto", t=70, notes=[
        "Para terminar, hacia dónde iría el producto. E14 mostró que el generador pone los productos "
        "pero decide él dónde. La idea: dibujar en la foto vacía una caja por mueble, donde tiene que ir "
        "y cuánto ocupa, y pedirle que cada mueble llene su caja.",
        f"[paso] Lo probamos en chico: la misma habitación y los mismos {n} muebles, con las cajas en el "
        f"lugar exacto de cada mueble en la foto real. {len(cv['imagenes'])} imágenes con cajas contra las "
        f"{len(sv['imagenes'])} sin cajas de recién.",
        f"[paso] Con cajas, el IoU medio sube de {f(s['iou_medio']['media'], 2)} a "
        f"{f(c['iou_medio']['media'], 2)}, y los muebles en su lugar de {f(s['en_su_lugar']['media'], 1)} a "
        f"{f(c['en_su_lugar']['media'], 1)}. Por mueble se ve dónde funciona: la estantería, el sofá y la "
        f"alfombra van a su caja; el puf, la mesa ratona y la lámpara, que se superponen con otros, no. Y "
        f"un problema: en {len(left_drawn)} de las {len(cv['imagenes'])} imágenes el modelo dejó las cajas "
        f"dibujadas, y hasta las movió.",
        "[paso] Lo que vimos: las cajas sirven para los muebles grandes, pero hay que pasarlas de otra "
        "forma, por ejemplo como una máscara aparte, o borrarlas en un segundo paso. Son tres imágenes "
        "por variante: es una pista, no un resultado.",
    ])

    # ---------- pasos a futuro 2: el producto con medidas reales
    steps = [
        ("1", "Medir el ambiente", "Una app móvil con el <strong>LiDAR</strong> del teléfono escanea el cuarto: "
         "paredes, aberturas y medidas reales."),
        ("2", "Medidas de cada producto", "Ancho, profundidad y alto en la metadata del catálogo: "
         "la <strong>caja a escala</strong> de cada mueble."),
        ("3", "Ubicar las cajas", None),
        ("4", "Generar", "Cada mueble llena su caja: <strong>tamaño y lugar reales</strong>; el generador "
         "pone la luz y el realismo."),
    ]
    cards = ""
    for num, title, text in steps:
        if text is None:
            inner = ('<div class="fo"><b>a.</b> En el plano, <strong>la IA decide</strong> dónde va cada caja '
                     '(circulación, aberturas, el pedido).</div>'
                     '<div class="fo"><b>b.</b> Un primer paso de generación <strong>pone los muebles así nomás</strong>; '
                     'tomamos dónde quedó cada uno y ahí va su caja a escala.</div>')
        else:
            inner = f"<p>{text}</p>"
        cards += f'<div class="fc"><div class="fcn">{num}</div><div class="fct">{title}</div>{inner}</div>'
    body = hd("Pasos a futuro", "El producto, <em>con medidas reales</em>")
    body += (
        f'<div class="fcs">{cards}</div>'
        '<div class="f3" data-step="1"><div class="f3k">Más adelante</div><p>Con <strong>modelos 3D</strong> de los '
        'productos, si el negocio los tiene, en lugar de cajas: se ubica el modelo en el cuarto escaneado y el '
        'generador solo tiene que hacerlo verse real. Es la versión más fiel.</p></div>'
        '<div class="fnow" data-step="1"><div class="fn1"><div class="lbl">Lo que ya probamos</div><div class="fth">'
        f'<img src="{img_uri(R / "vacio_con_cajas.png", 420, 264, q=72)}" alt=""><span class="fa">→</span>'
        f'<img src="{img_uri(R / "con_cajas" / "3.png", 420, 264, q=72)}" alt=""></div>'
        '<p class="fnote">El paso 4 con cajas 2D, sacadas de la foto real (lámina anterior).</p></div>'
        '<div class="fn2"><div class="lbl">Lo que falta</div><ul>'
        '<li>Las medidas reales del ambiente: el escaneo.</li>'
        '<li>Las medidas de los productos: los asientos de IKEA no las tienen.</li>'
        '<li>Pasar las cajas sin que queden dibujadas, por ejemplo como máscara.</li>'
        '<li>Elegir cómo se ubican (a o b) y medirlo en muchos ambientes.</li></ul></div></div>')
    add(body, sec="Pasos a futuro", title="Futuro · con medidas reales", t=60, notes=[
        "Y cómo se vería en el producto. Uno: medir el ambiente, con una app móvil que use el LiDAR del "
        "teléfono para escanear el cuarto: paredes, aberturas y medidas reales. Dos: las medidas de cada "
        "producto en la metadata del catálogo, para tener su caja a escala. Tres: ubicar las cajas, de "
        "dos maneras: que la IA decida en el plano dónde va cada una, o que un primer paso de generación "
        "ponga los muebles así nomás, y tomar dónde quedó cada uno para poner ahí su caja a escala. Cuatro: "
        "generar, con cada mueble llenando su caja, en su tamaño y lugar reales.",
        "[paso] Más adelante, si el negocio tiene modelos 3D de los productos, se usan en lugar de las "
        "cajas: se ubica el modelo en el cuarto escaneado y el generador solo tiene que hacerlo verse real. "
        "De todo esto, lo que ya probamos es el paso cuatro con cajas dibujadas en la foto; lo que falta "
        "son las medidas reales, del ambiente y de los productos.",
    ])

"""Apertura (el producto y por qué es un RAG), el recorrido (laminas_rec) y cómo medimos."""

from __future__ import annotations

import img
import sala
from base import (KIND_ES, add, cab, catalogo, dif, esc, f, ficha, foto_producto, ic, kind_es, llamada, medidas,
                  miles, nb, pct, piezas_hasta, remate, sg, usd)
from datos_deck import EJ_ROOM, REPO, V1, V2, elegidos
from graf import forest


def flecha(x1, y1, x2, y2, cls="fl") -> str:
    return (f'<svg class="{cls}" style="position:absolute;left:0;top:0;width:1920px;height:1080px;overflow:visible;pointer-events:none">'
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/><path d="M{x2 - 14},{y2 - 9} L{x2},{y2} L{x2 - 14},{y2 + 9}"/></svg>')


def credito(D, slug: str) -> str:
    """Autor y licencia de la foto pública de ese ambiente (publicas.yaml)."""
    c = D["publicas"][D["pedidos"][slug]["foto"]]
    return f"{c['autor']}, {c['licencia']}"


def creditos(D, slugs) -> str:
    """Los créditos de las fotos públicas de esos ambientes, sin repetir (las propias no llevan)."""
    out = []
    for s in slugs:
        if D["pedidos"][s]["foto"] in D["publicas"]:
            c = credito(D, s)
            if c not in out:
                out.append(c)
    return "; ".join(out)


SEPARADORES = {
    1: ("El recorrido, <em>ambiente por ambiente</em>", "Del catálogo a la lista: qué entra y qué sale de cada fase, y qué decidimos ahí.", []),
    2: ("Antes de comparar, <em>una vara</em>", "Dos bancos de prueba, qué mide cada número y cuánto creerle.", []),
    3: ("Los experimentos: <em>el buscador</em>", "Por cuánto importan: los que sostienen una decisión tienen su lámina.",
        [("E1", "qué se indexa"), ("E2", "cómo se escribe la consulta"), ("E3", "léxica, por foto e híbrida"),
         ("", "el camino, un cambio por paso"), ("E4", "¿error, o una variante?")]),
    4: ("Quién elige, <em>y en cuartos reales</em>", "La elección con un modelo que ve, y el flujo entero con el juez.",
        [("E5", "elegir con un VLM, y cuántos candidatos"), ("E6", "qué catálogo"), ("E7", "con búsqueda o sin búsqueda")]),
    5: ("Lo que iban a preguntar: <em>de trámite</em>", "La respuesta corta de cada uno: correctos, y de respuesta previsible.",
        [("E8", "tres redactores"), ("E9–12", "embedder, dimensión, splitting, base"), ("E13–15", "filtros, rerankers de texto y la escena")]),
    6: ("Ejercicio 4: <em>versión 1 y versión 2</em>", "La limitación medida de la versión anterior, el cambio y los resultados en las dos.", []),
    7: ("Lo que <em>quedó</em>", "El costo, las limitaciones, lo que sigue y las conclusiones.", []),
}
ROT_NUEVO = {  # dónde va el rótulo de la pieza nueva en el separador (dx, dy en unidades del dibujo)
    "alfombra": (150, 80), "sofa": (-120, 90), "tv": (120, 70), "mesa": (150, 120), "lampara": (-130, -40),
    "cortinas": (90, -120), "planta": (110, -60), "almohadones": (-140, -70),
}
SEP_PLANTA = {3: [2, 3, 5, 6], 4: [1, 6, 7], 5: [3, 6], 6: [6]}


def separador(cap: int, notas, t=8):
    from base import CAPS
    titulo, baj, exps = SEPARADORES[cap]
    nuevas = CAPS[cap][1]
    pz = piezas_hasta(cap)
    P = sala.Proj()
    rot = "".join(sala.rotulo(P, k, "+ " + sala.NOMBRE[k], *ROT_NUEVO[k], cls="rot acc") for k in nuevas)
    if cap == 7:
        rot = ""
    lista = ""
    if exps:
        lista = '<ul class="s-lista">' + "".join(f"<li><b>{e}</b>{esc(n)}</li>" for e, n in exps) + "</ul>"
    body = (f'<div class="s-txt"><div class="s-num">{cap:02d}</div><h2>{titulo}</h2><p class="s-baj">{baj}</p>{lista}</div>'
            f'<div class="s-sala">{sala.sala(pz, nuevas=nuevas if cap < 7 else (), P=P, extra=rot)}</div>')
    add(body, titulo=f"Capítulo {CAPS[cap][0]}", cap=cap, t=t, notas=notas, cls="oscura separador",
        planta=SEP_PLANTA.get(cap))


def build(D: dict) -> dict:
    run = D["run"]
    R = run["dir"]
    picks = elegidos(run)
    choices = run["choice"]["answer"]["choices"]
    cands = run["cands"]["pieces"]
    plan = run["plan"]["answer"]["pieces"]
    gen = run["gen"]
    req = run["req"]["request"]
    slug = run["slug"]
    costo_run = run["plan"]["cost_usd"] + run["choice"]["cost_usd"] + gen["cost_usd"]
    n_int = len(gen["attempts"])
    ctx = {"choices": choices, "cands": cands, "plan": plan, "picks": picks}
    k_flujo = D["cfg"].furnish.candidates

    # ================================================================ 1 · portada
    P = sala.Proj()
    body = (
        '<div class="p-txt"><div class="etq">TP 3 · 73.69 Large Language Models · ITBA 2026</div>'
        '<h1>amobl<em>ai</em></h1>'
        '<p class="p-baj">Una foto de tu ambiente vacío y lo que querés, en tus palabras. '
        '<span>Vuelve una lista de muebles reales de un catálogo y la foto de tu cuarto amoblado con ellos.</span></p></div>'
        '<div class="equipo"><span class="etq">grupo</span>Juan Bautista Albertoni Salini<br>Matias Juan Rossi Seifert<br>Junior Rambau</div>'
        f'<div class="p-sala">{sala.sala([], P=P)}</div>')
    add(body, titulo="Portada", cap=0, t=25, cls="oscura portada sin-pie", notas=[
        "Buenas. Somos Juan Bautista, Matías y Junior, y esto es **amoblai**.",
        "Le das una foto de tu ambiente vacío, como este living, y le contás qué querés. Te devuelve "
        "una lista de muebles reales de un catálogo y la foto de tu cuarto amoblado con ellos.",
        "Les contamos qué hace, cómo está armado y cómo lo medimos. Y este cuarto se va a ir amoblando "
        "mientras avanzamos.",
    ])

    # ================================================================ 2 · el problema
    Pg = sala.Proj()
    fant = ""
    preg = ""
    for k in ("sofa", "alfombra", "mesa", "tv", "lampara", "planta"):
        fant += sala.caja_alambre(Pg, sala.CAJA[k], "fantasma", k)
    for k in ("sofa", "mesa", "tv", "lampara"):
        x0, y0, z0, x1, y1, z1 = sala.CAJA[k]
        px, py = Pg.p((x0 + x1) / 2, (y0 + y1) / 2, z1 + 30)
        preg += f'<g class="preg"><circle class="halo" cx="{px:.1f}" cy="{py:.1f}" r="27"/><circle cx="{px:.1f}" cy="{py:.1f}" r="19"/><text x="{px:.1f}" y="{py + 9:.1f}">?</text></g>'
    room_gen = sala.sala([], P=Pg, extra=fant + preg, cotas=False, vb=sala.viewbox(Pg, pad=(30, 20, 10, 20), m=0))
    # seis productos reales del catálogo: los cinco de la lista del recorrido y otro candidato
    cat_ids = [h["id"] for h, *_ in picks]
    otro = next(c["id"] for p in cands for c in p["candidates"] if c["id"] not in cat_ids)
    cat = "".join(ficha(D, pid, 150, titulo=kind_es(D, pid), sub=f"{catalogo(pid)} · {medidas(D, pid)}")
                  for pid in (cat_ids + [otro])[:6])
    body = (
        '<div class="cuerpo">' + cab("00", "El problema", "Tenés el ambiente vacío y una idea. <em>Te faltan los muebles concretos.</em>") + '</div>'
        '<div class="dos-cam">'
        '<div class="cam"><div class="etq">un generador de imágenes</div>'
        f'<div class="cam-fig sala-gen">{room_gen}</div>'
        '<p class="cam-t"><b>Te amobla la foto…</b> con muebles que no existen: sin medida, sin precio, sin dónde comprarlos.</p></div>'
        '<div class="cam" data-desde="1"><div class="etq">un catálogo</div>'
        f'<div class="cam-fig grilla-cat">{cat}</div>'
        '<p class="cam-t"><b>Tiene muebles reales…</b> pero no mira tu cuarto. La combinación la armás vos, pieza por pieza.</p></div>'
        '</div>'
        + remate("Queremos las dos cosas. Es un problema de <mark>RAG</mark>: la respuesta sale de lo que se recupera de un catálogo, no de lo que el modelo imagina.", desde=2))
    add(body, titulo="El problema", cap=0, t=35, cls="lam-problema", notas=[
        "El problema. Te mudás, tenés el ambiente vacío y una idea de lo que querés. Hay dos caminos y "
        "ninguno alcanza.",
        "Un generador de imágenes te amobla la foto, pero con muebles inventados: estas cajas punteadas con "
        "signos de pregunta. No los podés medir ni comprar.",
        "[paso] Un catálogo tiene productos reales, pero no mira tu cuarto: combinar cosas que vayan entre sí "
        "y con tu piso lo hacés vos.",
        "[paso] Queremos las dos cosas a la vez: que la respuesta salga de lo que se recupera del catálogo, no "
        "de la imaginación del modelo.",
    ])

    # ================================================================ 3 · qué hace
    fichas = "".join(ficha(D, h["id"], 150, titulo=kind_es(D, h["id"]), sub=f"{catalogo(h['id'])} · {medidas(D, h['id'])}", cant=q)
                     for h, q, _ in picks)
    n_abo = sum(h["id"].startswith("abo-") for h, *_ in picks)
    body = (
        '<div class="cuerpo">' + cab("00", "Qué hace amoblai", "Una foto y un pedido. <em>Una lista y una imagen.</em>") + '</div>'
        '<div class="flujo3">'
        f'<div class="f3a"><div class="etq">1 · la foto y el pedido</div><div class="foto" style="width:520px;height:390px"><img src="{img.uri(R / "room.jpg", 1040, 780, q=74)}" alt=""></div>'
        f'<p class="cita pedido">«{esc(req)}»</p></div>'
        f'<div class="f3b" data-desde="1"><div class="etq">2 · la lista: {len(picks)} productos del catálogo</div><div class="lista8 l5">{fichas}</div>'
        f'<p class="cita porque"><span class="etq">el porqué del sofá, como lo escribe el modelo</span>«{esc(choices[0]["why"])}»</p></div>'
        f'<div class="f3c" data-desde="2"><div class="etq">3 · la imagen, con esos productos</div><div class="foto" style="width:560px;height:420px"><img src="{img.uri(R / "final.png", 1120, 840, q=76)}" alt=""></div>'
        f'<p class="pie-foto">Foto del ambiente: {esc(credito(D, slug))} · {n_int} intento{"s" if n_int > 1 else ""} de imagen · {usd(costo_run)} la corrida</p></div>'
        '</div>'
        + flecha(608, 470, 664, 470) + f'<div data-desde="2">{flecha(1216, 470, 1272, 470)}</div>')
    add(body, titulo="Qué hace amoblai", cap=0, t=40, cls="lam-que", notas=[
        "Así se usa. El usuario sube la foto del ambiente y escribe el pedido como le sale: un living japandi, "
        "sereno, con un sofá bajo de tela beige, una mesa ratona redonda, una alfombra de fibra natural, una "
        "lámpara de papel y una planta grande.",
        f"[paso] amoblai devuelve la lista: {len(picks)} productos reales, {len(picks) - n_abo} de IKEA y {n_abo} de "
        f"Amazon, con sus medidas cuando el catálogo las tiene. Cada uno viene con su porqué.",
        f"[paso] Y la imagen: el mismo cuarto, con esos productos. Esta corrida costó {usd(costo_run)}. Es la "
        f"que vamos a seguir en el recorrido.",
    ])

    # ================================================================ 4 · por qué RAG: los tres desafíos de la clase
    tres = [
        ("información actualizada", "El catálogo cambia; el modelo no se reentrena",
         "Un producto nuevo es una fila más en el índice: se describe, se embebe y ya se puede recomendar."),
        ("información personalizada", "Este catálogo, este ambiente, este pedido",
         f"El LLM no conoce estos {miles(D['n_todos'])} productos. La búsqueda le trae {k_flujo} candidatos reales por "
         f"pieza, y elige mirando sus fotos y la del cuarto."),
        ("sin alucinaciones", "Solo productos que existen",
         "Un LLM solo recomienda un sillón que nadie vende; un modelo de imagen solo inventa los muebles. Acá la "
         "lista solo puede tener ids que trajo la búsqueda, y la imagen se genera <b>desde las fotos de los elegidos</b>."),
    ]
    cols = "".join(f'<div class="d3{" hi" if i == 2 else ""}" data-desde="{i}"><div class="d3n">{i + 1:02d}</div><div class="etq">{esc(a)}</div>'
                   f'<h3>{esc(b)}</h3><p>{c}</p></div>' for i, (a, b, c) in enumerate(tres))
    body = ('<div class="cuerpo">' + cab("00", "Por qué RAG", "Recomendaciones atadas a <em>productos que existen</em>") + '</div>'
            f'<div class="tres">{cols}</div>'
            '<div class="dos-n" data-desde="3">'
            '<p><b>No es un Q&amp;A.</b> La consulta es una foto y un pedido abierto; la respuesta, una combinación de '
            'productos que tiene que funcionar junta, en ese espacio.</p>'
            '<p><b>Dos generaciones aumentadas</b> con lo recuperado: la lista (qué producto, cuántos y por qué) y la '
            'imagen del ambiente amoblado.</p></div>'
            + remate("Los tres desafíos de la clase: información <mark>actualizada</mark>, <mark>personalizada</mark> y <mark>sin alucinaciones</mark>.", desde=3))
    add(body, titulo="Por qué RAG", cap=0, t=45, notas=[
        "¿Por qué un RAG? Por los tres desafíos de la clase. Información actualizada: el catálogo cambia y el "
        "modelo no se reentrena; un producto nuevo es una fila más en el índice.",
        f"[paso] Información personalizada: el LLM no conoce estos {miles(D['n_todos'])} productos; la búsqueda le "
        f"trae {k_flujo} candidatos reales por pieza.",
        "[paso] Y sin alucinaciones: un LLM solo recomienda un sillón que nadie vende, y un modelo de imagen solo "
        "inventa los muebles. Acá la lista solo puede tener productos que trajo la búsqueda, y la imagen se "
        "genera desde sus fotos.",
        "[paso] No es un Q&A: la consulta es una foto y un pedido abierto, y hay dos generaciones aumentadas, "
        "la lista y la imagen.",
    ])

    # ================================================================ 5 · separador
    separador(1, ["¿Cómo está armado? Lo recorremos como una casa, ambiente por ambiente. Primera pieza del "
                  "cuarto: la alfombra."])

    # ================================================================ el recorrido y los desafíos
    import laminas_rec

    laminas_rec.build(D, ctx)

    # ================================================================ cómo medimos
    separador(2, ["Antes de los experimentos, cómo medimos: qué mide cada número y cuánto creerle. Segunda "
                  "pieza: el sofá."])
    medimos(D)
    return ctx


# ---------------------------------------------------------------- cómo medimos

def medimos(D: dict) -> None:
    B1, B2, D21 = D["B1"], D["B2"], D["D21"]
    N_ANS, N_BUS = D["N_ANS"], D["N_BUS"]

    # ================================================================ dos bancos de prueba
    room_ikea = REPO / "datos/dataset/ikea/images/room_scenes" / EJ_ROOM
    ann = D["ej_annotated"]
    ann_html = "".join(ficha(D, pid, 58, cap=False) for pid in ann)
    amb = list(D["pedidos"].values())
    propios = [a for a in amb if a["foto"] not in D["publicas"]]
    publicos = [a for a in amb if a["foto"] in D["publicas"]]
    th = "".join(f'<div class="bt{" pub" if a["foto"] in D["publicas"] else ""}"><img src="{img.uri(a["foto"], 240, 180, q=70)}" alt=""></div>'
                 for a in propios + publicos)
    body = (
        '<div class="cuerpo">' + cab("02", "Cómo medimos · los datos", "Dos bancos de prueba: <em>con ground truth, y sin él</em>") + '</div>'
        '<div class="bancos">'
        '<div class="bn1"><div class="bnh"><b>con ground truth</b><span>mide el buscador</span></div>'
        f'<div class="bng"><div class="foto" style="width:372px;height:233px"><img src="{img.uri(room_ikea, 744, 466, q=74)}" alt=""></div>'
        f'<div><div class="etq">una foto de IKEA y sus {len(ann)} productos anotados</div><div class="anot2">{ann_html}</div></div></div>'
        '<div class="cifras c4">'
        f'<div><b>{D["N_AMB"]}</b><span>livings y comedores de IKEA con sus productos anotados</span></div>'
        f'<div><b>{N_BUS}</b><span>consultas: una por mueble que se ve, escrita como la escribiría el plan</span></div>'
        f'<div class="acc"><b>{N_ANS}</b><span>tienen su producto en el catálogo de {D["n_ikea"]}: sobre esas se mide</span></div>'
        f'<div><b>{f(D["azar_h1"])}</b><span>hit@1 al azar entre lo que deja pasar el filtro</span></div></div>'
        '<p class="bnota">Es un banco de <b>producto conocido</b>: quien escribe la consulta está viendo el mueble. '
        'Mide el índice, no la recomendación.</p></div>'
        '<div class="bn2" data-desde="1"><div class="bnh"><b>sin ground truth</b><span>mide el flujo entero</span></div>'
        f'<div class="bth">{th}</div>'
        f'<p class="credito">Fotos públicas (Wikimedia Commons y Flickr): {esc(creditos(D, [a["slug"] for a in publicos]))}.</p>'
        f'<p class="bt2"><b>{len(amb)} ambientes vacíos reales</b>, cada uno con su pedido: {len(propios)} nuestros y '
        f'{len(publicos)} públicos, elegidos entre {D["n_publicas_revisadas"]} revisados.</p>'
        '<div class="juez"><div class="jrow"><span class="jo">orden 1</span><span class="jb">A · una configuración</span>'
        '<span class="jb t">B · la otra</span><span class="jv">→ voto</span></div>'
        '<div class="jrow"><span class="jo">orden 2</span><span class="jb t">A · la otra</span>'
        '<span class="jb">B · una configuración</span><span class="jv">→ voto</span></div>'
        '<p>Un juez (Opus) ve la foto, el pedido y las dos listas, a ciegas. <strong>Una gana un ambiente solo si '
        'gana en los dos órdenes</strong>; si no, empate.</p></div></div>'
        '</div>'
        + remate("Dos bancos, dos preguntas: con ground truth se mide <mark>el índice</mark>; con el juez, <mark>la lista</mark>.", desde=2))
    add(body, titulo="Dos bancos de prueba", cap=2, t=45, cls="lam-bancos", notas=[
        f"Usamos dos bancos de prueba, que miden cosas distintas. Para el buscador, {D['N_AMB']} ambientes de "
        f"IKEA con sus productos anotados. Por cada mueble que se ve, un subagente escribió la consulta como la "
        f"escribiría el plan, sin ver el catálogo: {N_BUS} consultas, {N_ANS} con su producto en el catálogo. "
        f"Es un banco de producto conocido: quien escribe está viendo el mueble, así que mide el índice, no la "
        f"recomendación.",
        f"[paso] Para el flujo entero, {len(amb)} ambientes vacíos reales, cada uno con su pedido. Ahí no hay "
        f"ground truth: un juez compara a ciegas las listas de dos configuraciones, en los dos órdenes, y una "
        f"gana solo si gana en los dos.",
        "[paso] Con ground truth medimos el índice; con el juez, la lista.",
    ])

    # ================================================================ las métricas del buscador, en un ejemplo
    ej, em = D["ej"], D["ej_metrics"]
    rel = set(ej["relevant"])
    cinta = "".join(ficha(D, pid, 132, cap=False, pos=i + 1, hi=pid in rel) for i, pid in enumerate(ej["ranked"][:10]))
    ql = ej["query"].splitlines()
    qshow = " · ".join(f"<b>{esc(l.split(':')[0])}:</b> {esc(l.split(':', 1)[1].strip())}"
                       for l in ql if l.split(":")[0] in ("Type", "Colors", "Shape"))
    cr_a, cr_b = D["ej_cr3"]
    assert (em["hit1"], em["hit3"]) == (0, 1), "el ejemplo de las métricas cambió: revisar la lámina y su nota"
    mc = [
        (1, "hit@k", "¿Está el anotado entre los primeros k? <b>hit@5 es el titular</b>: son los 5 candidatos que ve el que elige.",
         "hit@1 · hit@3 · hit@5", f"{em['hit1']} · {em['hit3']} · {em['hit5']}",
         f"hit@1 {f(B2['hit@1'])} · hit@5 <b>{f(B2['hit@5'])}</b>"),
        (1, "MRR@10", "Uno sobre el puesto del primer relevante: premia que esté arriba aunque no sea primero.",
         f"1 / {em['rank']}", f(em["rr"]), f"<b>{f(B2['mrr@10'])}</b>"),
        (2, "NDCG@10", "Ganancia descontada por log₂(puesto + 1), sobre la del orden ideal.",
         f"(1 / log₂ {em['rank'] + 1}) / 1", f(em["ndcg"]), f"<b>{f(B2['ndcg@10'])}</b>"),
        (2, "context precision@10", "La de la clase: precisión@k promediada donde hay un relevante.",
         f"(1/{em['rank']}) / 1", f(em["cp"]), f"<b>{f(B2['context_precision@10'])}</b>"),
        (2, "context recall@3", "Por <b>ambiente</b>: de sus productos anotados, cuántos aparecen en algún top-3.",
         f"{cr_a} de {cr_b} en esta foto", f(cr_a / cr_b), f"<b>{f(B2['context_recall@3'])}</b>"),
    ]
    cols = "".join(f'<div class="mc" data-desde="{st}"><div class="mn">{n}</div><p>{d}</p><code>{fo}</code><b>{v}</b>'
                   f'<div class="mhoy"><span>en las {N_ANS}, hoy</span>{hoy}</div></div>'
                   for st, n, d, fo, v, hoy in mc)
    body = (
        '<div class="cuerpo">' + cab("02", "Cómo medimos · el buscador", "Cinco métricas, <em>sobre una sola búsqueda</em>") + '</div>'
        f'<div class="mq"><span class="etq">la consulta · la alfombra de la foto anterior</span><p>{qshow}</p></div>'
        f'<div class="cinta"><div class="cinta-r"></div>{cinta}</div>'
        f'<div class="cinta-l"><span>la búsqueda del flujo deja el producto anotado <b>{em["rank"]}.º</b> de {ej["universe"]} alfombras</span></div>'
        f'<div class="metricas m2">{cols}</div>')
    add(body, titulo="Las métricas del buscador, en un ejemplo", cap=2, t=50, notas=[
        f"Las métricas del buscador, sobre una sola búsqueda: la alfombra crema de pelo largo de la foto "
        f"anterior. La búsqueda del flujo ordena las {ej['universe']} alfombras y la anotada queda {em['rank']}.ª.",
        f"[paso] **hit@k**: si el anotado está entre los primeros k. Acá hit@1 da 0, y hit@3 y hit@5 dan 1. El "
        f"titular es hit@5, porque son los cinco candidatos que ve el que elige: hoy, {f(B2['hit@5'])}. **MRR** "
        f"es uno sobre el puesto del primer relevante: un tercio.",
        f"[paso] Las de la clase: **NDCG** y **context precision**, que con uno o dos relevantes por consulta "
        f"repiten al MRR, con una correlación mayor a 0,99; y **context recall**, que acá es por ambiente: de "
        f"los productos anotados de la foto, cuántos aparecen en algún top-3.",
    ])

    # ================================================================ diferencias pareadas
    CAM, EMB = D["CAM"], D["EMB"]
    d_desc = CAM["qwen3|description|filtro-none|consulta-piece"]["vs_anterior"]
    d_hash = EMB["hashing|description|filtro-kind"]["vs_base"]  # hashing − Qwen3: se da vuelta
    d_kind = CAM[V1]["vs_anterior"]
    q3, hs = EMB[V1], EMB["hashing|description|filtro-kind"]

    def fila(label, sub, v, k, lectura, flip=False):
        x, (lo, hi) = v[k], v[f"{k}_ic95"]
        if flip:
            x, lo, hi = -x, -hi, -lo
        return dict(label=label, sub=sub, value=x, lo=lo, hi=hi, texto=f"{sg(x)} {ic(lo, hi)}", lectura=lectura)

    rows = [
        fila("describir cada producto", "contra el texto del vendedor · hit@1", d_desc, "hit@1", "lejos del cero: es señal"),
        fila("búsqueda híbrida", "contra el coseno solo · hit@1", D21, "hit@1", "no toca el cero: es señal"),
        fila("Qwen3", f"contra contar palabras · hit@1 · {f(q3['hit@1'])} y {f(hs['hit@1'])}", d_hash, "hit@1",
             "cruza el cero: no se distinguen", flip=True),
        fila("filtro por kind", "contra ningún filtro · hit@5", d_kind, "hit@5", "no toca el cero: resta"),
    ]
    body = (
        '<div class="cuerpo">' + cab("02", "Cómo medimos · diferencias pareadas", "¿Cuándo una diferencia <em>es una diferencia?</em>") + '</div>'
        '<div class="boot"><div class="xl">'
        '<div class="bloque"><div class="bt">el problema</div><p>Las consultas de un mismo ambiente no son independientes: '
        'comparten la foto, la luz, el estilo. Y mirar el intervalo de cada método <strong>por separado</strong> engaña.</p></div>'
        f'<div class="bloque" data-desde="1"><div class="bt">diferencia pareada</div><p>Dos métodos sobre <strong>las mismas '
        f'{N_ANS} consultas</strong>: la diferencia media y su IC 95%, por bootstrap de <strong>ambientes</strong> '
        f'(se sortean {D["N_AMB_ANS"]} con reposición, mil veces).</p></div></div>'
        '<div class="boot-g" data-desde="1"><div class="ley"><span>la diferencia entre dos métodos, con su intervalo del 95% · a la derecha del cero, suma</span></div>'
        + forest(rows, width=1150, label_w=400, row_h=112, right=330, xmin=-0.1, xmax=0.3)
        + '</div></div>'
        + remate("La regla de toda la charla: si el intervalo de la diferencia toca el cero, <mark>no decimos que una gana</mark>.", desde=2))
    add(body, titulo="Diferencias pareadas", cap=2, t=40, notas=[
        "¿Cuándo una diferencia es una diferencia? Las consultas de un mismo ambiente no son independientes. Y "
        "mirar el intervalo de cada método por separado nos había hecho leer mejoras que eran ruido, y al revés.",
        "[paso] Por eso comparamos dos métodos sobre las mismas consultas: la diferencia media y su intervalo "
        "de 95 por ciento, remuestreando ambientes.",
        f"[paso] Cuatro ejemplos. Describir cada producto y la búsqueda híbrida: el intervalo no toca el cero, "
        f"es señal. Qwen3 contra contar palabras: {f(q3['hit@1'])} contra {f(hs['hit@1'])} parecía ganar, pero el "
        f"intervalo cruza el cero. Y el filtro por kind parecía no cambiar nada, y resta en hit@5. Esa es la "
        f"regla de toda la charla.",
    ])

    generador(D)
    imagen(D)

    # ================================================================ las trampas, dichas en voz alta
    jr = D["JR"]["resumen"]
    cf = sorted(D["DIAG_CAT"][v]["puntaje_del_primero"]["mediana"] for v in ("ikea", "todos"))
    bm = D["EMB"]["bm25|description|filtro-kind"]
    n_amb = len(D["pedidos"])
    tr = [
        ("El banco de la búsqueda es de producto conocido",
         f"Quien escribió la consulta veía el mueble: mide identificar un producto, no recomendar. En el flujo real "
         f"el plan lo imagina, y sus consultas quedan más lejos del catálogo: el coseno del primer candidato es "
         f"{f(cf[0], 2)}–{f(cf[1], 2)}, contra {f(D['cos_banco'])} en el banco."),
        ("El mismo modelo escribe los dos lados",
         f"Consultas y descripciones salen del mismo modelo, con el mismo molde de ocho líneas. Por eso contar "
         f"palabras rinde casi como el embedder (BM25: {f(bm['hit@1'])} contra {f(B1['hit@1'])}). Representa al "
         f"sistema, porque el plan también es Claude; no a alguien que escribe con otras palabras."),
        ("No hay conjunto apartado",
         f"Todo se eligió y se reporta sobre los mismos {D['N_AMB_ANS']} ambientes. Las diferencias grandes se "
         f"sostienen igual; las de 2 puntos no las leemos como señal."),
        (f"De punta a punta son {n_amb} ambientes",
         f"El juez es el mismo modelo que elige. Con la misma configuración corrida dos veces, el que elige cambia "
         f"{D['ruido_cambian']} de {D['ruido_total']} productos y el juez reparte {jr['hibrida']['gana']} a "
         f"{jr['hibrida_bis']['gana']}: un ambiente ganado no dice nada solo, cuenta la asimetría. El pedido abierto no "
         f"está evaluado."),
    ]
    cells = "".join(f'<div class="tp" data-desde="{i // 2}"><div class="tpn">{i + 1:02d}</div><h3>{esc(a)}</h3><p>{b}</p></div>'
                    for i, (a, b) in enumerate(tr))
    body = ('<div class="cuerpo">' + cab("02", "Cómo medimos · cuánto creerle", "Las trampas, <em>dichas en voz alta</em>") + '</div>'
            f'<div class="trampas">{cells}</div>'
            + remate(f"El ground truth sirve para comparar cambios grandes del índice. Lo que le sirve al usuario lo dice el juez, con <mark>n = {n_amb}</mark>.", desde=1))
    add(body, titulo="Las trampas, dichas en voz alta", cap=2, t=40, notas=[
        "Y las trampas, dichas en voz alta. Uno: el banco de la búsqueda es de producto conocido; en el flujo "
        "real el plan imagina el producto, no lo ve. Dos: el mismo modelo escribe las consultas y las "
        "descripciones, con el mismo molde; por eso contar palabras rinde casi como el embedder.",
        f"[paso] Tres: no hay conjunto apartado. Y cuatro: de punta a punta son {n_amb} ambientes, el juez es el "
        f"mismo modelo que elige, y el ruido solo ya mueve ambientes: la misma configuración corrida dos veces "
        f"reparte {jr['hibrida']['gana']} a {jr['hibrida_bis']['gana']}. Por eso leemos las asimetrías grandes, y "
        f"las diferencias de dos puntos, no.",
    ])


# ---------------------------------------------------------------- el generador y los jueces

def acuerdo(j: dict) -> str:
    """En cuántos ambientes los dos órdenes del juez votaron lo mismo."""
    return f'{sum(d["votos"][0] == d["votos"][1] for d in j["detalle"])} de {len(j["detalle"])}'


def generador(D: dict) -> None:
    from laminas_rec import extracto

    RESP, R1 = D["RESP"], D["RESP1"]
    jr = D["JR"]["resumen"]
    F, AR = RESP["faithfulness"], RESP["answer_relevance"]
    assert 0.85 <= F["global"] < 0.9, "cambió la faithfulness: revisar la frase de cierre de la lámina del generador"
    fid = [x["fidelidad"]["faithfulness"] for x in RESP["por_corrida"]]
    no_sost = RESP["por_corrida"][0]["fidelidad"]["no_sostenidas"][:2]
    g = D["GRAD"]["acuerdo_con_gt"]
    v1f = D["generador_v1"]
    dots = "".join(f'<i style="left:{x * 100:.1f}%"></i>' for x in fid)
    viejo = extracto("juez_pedidos_v1", [dict(l="A furnishing app takes a photo", hasta="shopping list of products",
                                              m=['"un living nórdico y cálido"'])],
                     titulo="el juez de antes · extracto literal")
    body = (
        '<div class="cuerpo">' + cab("02", "Cómo medimos · el generador y los jueces",
                                     f"El generador: <em>faithfulness {f(F['global'], 2)} y answer relevance {f(AR['media'], 2)}</em>") + '</div>'
        '<div class="gen">'
        '<div class="gl">'
        f'<div class="gm"><div class="gmv">{f(F["global"], 2)}</div><div><h3>Faithfulness del porqué</h3>'
        f'<p><b>{F["sostenidas"]} de {F["afirmaciones"]}</b> afirmaciones se infieren de lo que vio el generador: el pedido, '
        f'la foto del cuarto y, de cada producto, su foto y una línea con su tipo y su medida.</p></div>'
        f'<div class="gbar"><em style="width:{F["global"] * 100:.1f}%"></em>{dots}</div>'
        f'<p class="gn">Cada punto, una lista: de {f(min(fid), 2)} a {f(max(fid), 2)}. Lo que no se sostiene es casi siempre '
        f'<b>la especie de la madera</b>, que afirma sin verla escrita: «{esc(no_sost[0])}», «{esc(no_sost[1])}».</p></div>'
        f'<div class="gm" data-desde="1"><div class="gmv">{f(AR["media"], 2)}</div><div><h3>Answer relevance</h3>'
        '<p>Un juez que no ve el pedido escribe tres pedidos que la lista contesta; se mide su coseno con el pedido original.</p></div>'
        f'<div class="gbar"><em style="width:{AR["media"] * 100:.1f}%"></em>'
        f'<u style="left:{AR["vara_cruzada"] * 100:.1f}%"><span>{f(AR["vara_cruzada"], 2)} · otras listas</span></u>'
        f'<u class="b" style="left:{AR["vara_contrastes"] * 100:.1f}%"><span>{f(AR["vara_contrastes"], 2)} · sin relación</span></u></div>'
        f'<p class="gn">La vara: los pedidos que el juez escribió para <b>otras</b> listas. La propia les gana en '
        f'{AR["supera_a_la_cruzada"]} de {RESP["corridas"]}.</p></div>'
        f'<p class="gn sobre">Las dos, sobre las {RESP["corridas"]} listas de la versión 2. Sobre otras {R1["corridas"]} listas '
        f'(con la búsqueda de la versión 1) dan {f(R1["faithfulness"]["global"], 2)} y {f(R1["answer_relevance"]["media"], 2)}: '
        f'no es una mejora de la versión 2 (por ambiente sube en {D["resp_sube"]} y baja en {D["resp_baja"]}).</p>'
        '</div>'
        '<div class="gr" data-desde="2">' + viejo
        + '<div class="gnotas">'
        f'<div class="apri"><span>1</span><p><strong>Data leakage.</strong> Ese ejemplo era, palabra por palabra, el comienzo del '
        f'pedido que se evaluaba: el juez lo copiaba. Y el juez de fidelidad leía la ficha completa, que el generador no ve. '
        f'Daban {v1f[0]}–{v1f[1]} y {v1f[2]}–{v1f[3]}: los rehicimos sin el ejemplo y con el contexto real.</p></div>'
        f'<div class="apri"><span>2</span><p><strong>Validado contra el ground truth, un juez</strong>: el de relevancia le da la '
        f'nota máxima al producto anotado el {pct(g["anotado_con_2"])} de las veces, y a los demás el {pct(g["otros_con_2"])}.</p></div>'
        f'<div class="apri"><span>3</span><p><strong>El juez de listas</strong> no está validado contra personas: se le pregunta en '
        f'los dos órdenes, y coinciden en {acuerdo(D["JA"])} ambientes contra el azar, {acuerdo(D["JC"])} entre catálogos y '
        f'{acuerdo(D["JV"])} entre versiones. Con la misma configuración dos veces reparte {jr["hibrida"]["gana"]} a '
        f'{jr["hibrida_bis"]["gana"]}.</p></div>'
        '</div></div></div>'
        + remate("El porqué se sostiene en <mark>casi 9 de cada 10 afirmaciones</mark>. Y la lista responde a su pedido más que a los ajenos.", desde=2))
    add(body, titulo="El generador y los jueces", cap=2, t=55, cls="lam-gen", planta=[7], notas=[
        f"El generador es el paso que elige y explica. **Faithfulness**: partimos el porqué en afirmaciones, y un "
        f"juez dice cuáles se infieren de lo que el generador vio. Da {f(F['global'], 2)}: {F['sostenidas']} de "
        f"{F['afirmaciones']}. Lo que no se sostiene es casi siempre la especie de la madera, que afirma sin verla "
        f"escrita.",
        f"[paso] **Answer relevance**: un juez que no ve el pedido escribe los pedidos que esa lista contesta. Da "
        f"{f(AR['media'], 2)}, contra {f(AR['vara_cruzada'], 2)} con pedidos escritos para otras listas.",
        "[paso] Estas métricas las rehicimos, y es una historia de data leakage: el prompt del juez traía de "
        "ejemplo «un living nórdico y cálido», que era justo como empezaba el pedido evaluado, y lo copiaba. Y "
        "sobre los jueces: validado contra el ground truth hay uno solo; el de listas se controla con los dos "
        "órdenes.",
    ])


# ---------------------------------------------------------------- la imagen: las 11 corridas finales

def imagen(D: dict) -> None:
    run = D["run"]
    R = run["dir"]
    picks = elegidos(run)
    T = D["IMG_TOT"]
    fin = D["FINALES"]
    assert T["pasan"] == T["pasan_al_primero"], "alguna corrida final pasó el control al reintentar: revisar la lámina de la imagen"
    pares = ""
    for (h, *_), p in zip(picks, run["met"]["productos"], strict=True):
        assert h["id"] == p["id"]
        cat = f'<img src="{img.uri(foto_producto(D, h["id"]), 150, 150, q=78, fit="contain")}" alt="">'
        if p["detectado"]:
            ok = p["puesto"] == 1
            pares += (f'<div class="pr2">{cat}<img class="rec" src="{img.crop(R / "final.png", p["box"], 150, 150)}" alt="">'
                      f'<span class="{"ok" if ok else ""}">{p["puesto"]}.º de {p["entre"]}</span></div>')
        else:
            pares += f'<div class="pr2">{cat}<i></i><span>no detectado</span></div>'
    run_rec = sum(p.get("puesto") == 1 for p in run["met"]["productos"])
    th = ""
    for x in fin:
        ok = x["img"]["room_check"]["ok"]
        rec = sum(p.get("puesto") == 1 for p in x["met"]["productos"])
        th += (f'<div class="fi2"><img src="{img.uri(x["dir"] / "final.png", 320, 214, q=70)}" alt="">'
               f'<span class="sello{" ok" if ok else ""}">{"pasa" if ok else "no pasa"} · {rec} de {len(x["met"]["productos"])}</span></div>')
    pub = [x["slug"] for x in fin if D["pedidos"][x["slug"]]["foto"] in D["publicas"]]
    body = (
        '<div class="cuerpo">' + cab("02", "Cómo medimos · la imagen",
                                     f"La imagen: <em>{T['reconocidos']} de {T['productos']} productos, {T['pasan']} de {T['n']} cuartos</em>") + '</div>'
        '<div class="imgm">'
        '<div class="im1"><div class="bnh"><b>¿son esos productos?</b><span>el living del recorrido: catálogo, recorte y puesto</span></div>'
        f'<div class="pares2">{pares}</div>'
        f'<p class="gn">Se detecta cada mueble en la imagen, se recorta y se compara con las fotos del catálogo de su tipo '
        f'(DINOv3): <b>reconocido</b> si el más parecido es el de la lista. Acá, {run_rec} de {len(run["met"]["productos"])}.</p>'
        f'<div class="gm g2"><div class="gmv">{T["reconocidos"]} de {T["productos"]}</div><div><p>productos reconocidos como el exacto '
        f'(<b>{pct(T["reconocidos"] / T["productos"])}</b>) en las {T["n"]} imágenes de la configuración final; aparecen '
        f'{T["detectados"]}. Coseno medio {f(T["coseno"], 2)}.</p></div></div></div>'
        '<div class="im2" data-desde="1"><div class="bnh"><b>¿es ese cuarto?</b><span>las '
        f'{T["n"]} imágenes: control del ambiente · productos reconocidos</span></div>'
        f'<div class="fin2">{th}<div class="finr"><b>{T["pasan"]} de {T["n"]}</b><span>conservan el cuarto, todas al primer intento</span></div></div>'
        f'<p class="credito">Fotos públicas: {esc(creditos(D, pub))}.</p></div>'
        '</div>'
        + remate("La lista es confiable; la imagen es una visualización: acierta el producto exacto <mark>4 de cada 10 veces</mark> y conserva el cuarto <mark>2 de cada 3</mark>.", desde=1))
    add(body, titulo="La imagen: las 11 corridas finales", cap=2, t=45, cls="lam-img", planta=[9, 10], notas=[
        f"La imagen la medimos sobre las {T['n']} corridas de la configuración final, no sobre la mejor. Primero: "
        f"¿son esos productos? Detectamos cada mueble, lo recortamos y lo comparamos con las fotos del catálogo "
        f"de su tipo: reconocido, si el más parecido es el de la lista. En el living del recorrido salen primeros "
        f"el sofá, la lámpara y la planta; la alfombra y la mesa, no. En total se reconocen {T['reconocidos']} de "
        f"{T['productos']}, el {pct(T['reconocidos'] / T['productos'])}, aunque aparecen {T['detectados']}.",
        f"[paso] Segundo: ¿es ese cuarto? El control pasa en {T['pasan']} de {T['n']}, todas al primer intento. O "
        f"sea: la lista es confiable; la imagen es una visualización.",
    ])

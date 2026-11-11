"""Apertura, arquitectura y cómo medimos."""

from __future__ import annotations

import img
import sala
from base import (KIND_ES, add, cab, esc, f, ficha, foto_producto, llamada, medidas, pct, piezas_hasta,
                  remate, usd)
from datos_deck import EJ_ROOM, REPO, RES, jload
from graf import hist

A = RES / "amoblar"
CL = A / "caballito-living"


def flecha(x1, y1, x2, y2, cls="fl") -> str:
    return (f'<svg class="{cls}" style="position:absolute;left:0;top:0;width:1920px;height:1080px;overflow:visible;pointer-events:none">'
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/><path d="M{x2 - 14},{y2 - 9} L{x2},{y2} L{x2 - 14},{y2 + 9}"/></svg>')


SEPARADORES = {
    1: ("Cómo está <em>armado</em>", "Un RAG sobre un catálogo de muebles: qué se indexa, cómo se busca, quién elige y cómo se dibuja.", []),
    2: ("Antes de comparar, <em>una vara</em>", "Un ground truth, cinco métricas de ranking y un intervalo de confianza para cada número.", []),
    3: ("Qué guardamos <em>en el índice</em>", "Indexing: qué representa a cada producto y dónde vive.",
        [("E1", "imagen o texto"), ("E2", "texto, embedder y filtro"), ("E3", "splitting"),
         ("E4", "dimensión del embedding"), ("E5", "base vectorial")]),
    4: ("Cómo buscamos <em>y quién elige</em>", "Lo que pasa en cada pedido, antes y después del retrieval.",
        [("E6", "query rewriting"), ("E7", "reranking"), ("E8", "cuántos candidatos")]),
    5: ("Cuánto creerle <em>a los números</em>", "Si cambia quien escribe las consultas, si no está el producto exacto, si la respuesta inventa.",
        [("E9", "reproducibilidad"), ("E10", "relevancia graduada"), ("E11", "RAGAS sobre la respuesta")]),
    6: ("De punta a punta, <em>en cuartos reales</em>", "Ambientes vacíos de verdad, pedidos de verdad: el catálogo y la imagen.",
        [("E12", "qué catálogo"), ("E13", "la imagen y su control"), ("E14", "réplica de un ambiente real"), ("T4", "lo que sigue")]),
    7: ("Lo que <em>quedó</em>", "La arquitectura final, el camino de los números, los costos y lo que aprendimos.", []),
}
ROT_NUEVO = {  # dónde va el rótulo de la pieza nueva en el separador (dx, dy en unidades del dibujo)
    "alfombra": (150, 80), "sofa": (-120, 90), "tv": (120, 70), "mesa": (150, 120), "lampara": (-130, -40),
    "cortinas": (90, -120), "planta": (110, -60), "almohadones": (-140, -70),
}


def separador(cap: int, notas, t=10):
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
    add(body, titulo=f"Capítulo {CAPS[cap][0]}", cap=cap, t=t, notas=notas, cls="oscura separador")


def build(D: dict) -> dict:
    cl = D["img"]["caballito-living"]
    choices = cl["choice"]["answer"]["choices"]
    cands = jload(CL / "2_candidates.json")["pieces"]
    plan = jload(CL / "1_searches.json")["answer"]["pieces"]
    no_first = sum(1 for c, p in zip(choices, cands) if p["candidates"][0]["id"] != c["id"])
    costo_cl = jload(CL / "1_searches.json")["cost_usd"] + cl["choice"]["cost_usd"] + cl["gen"]["cost_usd"]
    n_int = len(cl["gen"]["attempts"])
    ctx = {"choices": choices, "cands": cands, "plan": plan}

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
        "La idea es simple de decir: le das una foto de tu ambiente vacío, como este living dibujado, y "
        "le contás qué querés. amoblai te devuelve una lista de muebles reales de un catálogo y la foto "
        "de tu cuarto amoblado con ellos.",
        "En la próxima media hora les contamos qué hace, cómo está armado y, sobre todo, cómo lo medimos: "
        "cada decisión salió de un experimento. Y este cuarto vacío se va a ir amoblando a medida que "
        "avanzamos.",
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
    cat_ids = [c["id"] for c in choices[:6]]
    cat = "".join(ficha(D, pid, 150, titulo=KIND_ES.get(D["items"][pid]["kind"], ""), sub=D["items"][pid]["name"])
                  for pid in cat_ids)
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
    add(body, titulo="El problema", cap=0, t=45, cls="lam-problema", notas=[
        "Arranquemos por el problema. Te mudás, tenés el ambiente vacío y una idea de lo que querés. Hoy "
        "hay dos caminos y ninguno alcanza.",
        "Un generador de imágenes te amobla la foto, pero con muebles inventados: son estas cajas "
        "punteadas con signos de pregunta. No los podés medir ni comprar.",
        "[paso] Un catálogo tiene productos reales, pero no mira tu cuarto: filtrás por tipo, color, "
        "precio, y combinar ocho cosas que vayan entre sí y con tu piso lo hacés vos.",
        "[paso] Nosotros queremos las dos cosas a la vez. Y eso, en el fondo, es un problema de RAG: la "
        "respuesta tiene que salir de lo que recuperamos del catálogo, no de la imaginación del modelo.",
    ])

    # ================================================================ 3 · qué hace
    req = cl["req"]["request"]
    fichas = ""
    for c in choices:
        pid = c["id"]
        k = D["items"][pid]["kind"]
        fichas += ficha(D, pid, 116, titulo=KIND_ES.get(k, k), sub=medidas(D, pid), cant=c.get("quantity"))
    body = (
        '<div class="cuerpo">' + cab("00", "Qué hace amoblai", "Una foto y un pedido. <em>Una lista y una imagen.</em>") + '</div>'
        '<div class="flujo3">'
        f'<div class="f3a"><div class="etq">1 · la foto y el pedido</div><div class="foto" style="width:520px;height:390px"><img src="{img.uri(CL / "room.jpg", 1040, 780, q=74)}" alt=""></div>'
        f'<p class="cita pedido">«{esc(req)}»</p></div>'
        f'<div class="f3b" data-desde="1"><div class="etq">2 · la lista: {len(choices)} productos del catálogo</div><div class="lista8">{fichas}</div>'
        f'<p class="cita porque"><span class="etq">el porqué del sofá, como lo escribe el modelo</span>«{esc(choices[0]["why"])}»</p></div>'
        f'<div class="f3c" data-desde="2"><div class="etq">3 · la imagen, con esos productos</div><div class="foto" style="width:560px;height:420px"><img src="{img.uri(CL / "final.png", 1120, 840, q=76)}" alt=""></div>'
        f'<p class="pie-foto">living de un departamento propio · {n_int} intentos de imagen · {usd(costo_cl)} la corrida</p></div>'
        '</div>'
        + flecha(608, 470, 664, 470) + f'<div data-desde="2">{flecha(1216, 470, 1272, 470)}</div>')
    add(body, titulo="Qué hace amoblai", cap=0, t=60, cls="lam-que", notas=[
        "Así se usa. El usuario sube la foto del ambiente y escribe el pedido como le sale: «un living "
        "moderno y luminoso para recibir amigos, un sofá de tres cuerpos gris claro contra la pared de la "
        "izquierda, una mesa ratona de madera clara, una alfombra grande…».",
        f"[paso] amoblai devuelve la lista: {len(choices)} productos reales del catálogo, con cantidades "
        f"(los almohadones van por dos) y medidas cuando el catálogo las tiene. Cada uno viene con su "
        f"porqué. Un detalle que vamos a retomar: en {no_first} de las {len(choices)} piezas eligió un "
        f"producto que no era el más parecido por coseno.",
        f"[paso] Y la imagen: el mismo cuarto, con esos productos. Esta corrida costó {usd(costo_cl)}, con "
        f"{n_int} intentos de imagen. Por qué hubo {n_int} lo vemos al final.",
    ])

    # ================================================================ 4 · lo que tiene que cumplir
    rows = [
        ("Que los productos sean los que van", "retrieval contra un ground truth: hit@k, MRR, NDCG, context precision y recall",
         ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"]),
        ("Y si no está el exacto, algo que sirva", "relevancia graduada por un juez LLM", ["E10"]),
        ("Que se pueda creer cada número", "intervalos bootstrap y consultas reescritas tres veces", ["E9"]),
        ("Un porqué que no invente", "faithfulness (RAGAS)", ["E11"]),
        ("Que responda a lo que pidió", "answer relevance (RAGAS) y un juez de a pares", ["E11", "E12"]),
        ("Tu cuarto, no otro", "SSIM fuera de los muebles, SIFT, fidelidad de cada producto", ["E13", "E14"]),
    ]
    tr = "".join(
        f'<div class="pn">{i + 1:02d}</div><div class="pr">{esc(a)}</div><div class="pm">{esc(b)}</div>'
        f'<div class="pe">{"".join(f"<span class=chip>{e}</span>" for e in es)}</div>'
        for i, (a, b, es) in enumerate(rows))
    body = ('<div class="cuerpo">' + cab("00", "El programa", "Lo que tiene que cumplir, <em>y cómo lo vamos a medir</em>") + '</div>'
            '<div class="programa"><div class="ph"></div><div class="ph">lo que promete</div><div class="ph">cómo lo medimos</div>'
            f'<div class="ph">dónde</div>{tr}</div>')
    add(body, titulo="Lo que tiene que cumplir", cap=0, t=30, notas=[
        "Antes de entrar en la arquitectura, lo que amoblai promete, porque de acá salen las métricas. Es "
        "el programa, como en un proyecto de arquitectura.",
        "Que los productos sean los que van: eso es retrieval y se mide contra un ground truth, con las "
        "métricas de ranking de la materia. Que si el exacto no está, traiga algo que sirva. Que cada "
        "número se pueda creer. Que el porqué no invente y que la respuesta conteste lo que se pidió: ahí "
        "entran RAGAS y un juez. Y que la imagen sea tu cuarto y no otro. La columna de la derecha dice qué "
        "experimento mide cada cosa.",
    ])

    # ================================================================ 5 · separador
    separador(1, ["Entonces: ¿cómo está armado? Primera pieza del cuarto: la alfombra, la base sobre la que se apoya todo."])

    # ================================================================ 6 · indexing
    sofa = choices[0]["id"]
    doc = D["desc"][sofa].splitlines()
    doc_html = "".join(f'<div class="l8"><span>{esc(l.split(":", 1)[0])}</span>{esc(l.split(":", 1)[1].strip())}</div>' for l in doc)
    vec = "".join(f'<i style="opacity:{0.15 + 0.85 * ((i * 37) % 23) / 22:.2f}"></i>' for i in range(64))
    body = (
        '<div class="cuerpo">' + cab("01", "Arquitectura · indexing", "Una vez, offline: <em>el catálogo se vuelve un índice</em>") + '</div>'
        '<div class="indexado">'
        f'<div class="ix ix1"><div class="ixn">1</div><div class="ixh">Catálogo</div>'
        f'<div class="hoja ixfig"><img src="{img.uri(foto_producto(D, sofa), 360, 360, fit="contain")}" alt=""><span class="etq">{sofa} · {esc(D["items"][sofa]["name"])}</span></div>'
        f'<p>IKEA <b>{D["n_ikea"]}</b> + ABO <b>{D["n_abo"]}</b> productos: foto, tipo, kind y medidas.</p><div class="etq ixr">data loading y preprocesamiento</div></div>'
        f'<div class="ix ix2" data-desde="1"><div class="ixn">2</div><div class="ixh">Descripción de 8 líneas</div>'
        f'<div class="hoja ixfig doc8">{doc_html}</div>'
        f'<p>Un VLM mira la foto de cada producto y la describe siempre en las mismas ocho líneas.</p><div class="etq ixr">splitting: un producto, un documento</div></div>'
        f'<div class="ix ix3" data-desde="2"><div class="ixn">3</div><div class="ixh">Embedding</div>'
        f'<div class="ixfig vec"><div class="vgrid">{vec}</div><span class="etq">[ {D["best_dim"]} números ]</span></div>'
        f'<p>{esc(D["embed_model"])}, corre local: cada documento, un vector de {D["best_dim"]} dimensiones.</p><div class="etq ixr">embedding</div></div>'
        f'<div class="ix ix4" data-desde="3"><div class="ixn">4</div><div class="ixh">ChromaDB</div>'
        '<div class="ixfig db"><svg viewBox="0 0 220 230"><g fill="#fff" stroke="#13202C" stroke-width="2">'
        '<path d="M20,60 v120 a90,26 0 0 0 180,0 v-120"/><ellipse cx="110" cy="60" rx="90" ry="26"/>'
        '<path d="M20,100 a90,26 0 0 0 180,0" fill="none"/><path d="M20,140 a90,26 0 0 0 180,0" fill="none"/></g>'
        f'<text x="110" y="66" text-anchor="middle" style="font:700 17px var(--mono);fill:#2453D6">{D["n_todos"]}</text></svg></div>'
        '<p>HNSW con coseno: el vector, el texto y la metadata (kind, medidas) juntos.</p><div class="etq ixr">base de datos vectorial</div></div>'
        '</div>'
        + f'<div data-desde="1">{flecha(468, 480, 512, 480)}</div>' + f'<div data-desde="2">{flecha(916, 480, 960, 480)}</div>' + f'<div data-desde="3">{flecha(1364, 480, 1408, 480)}</div>'
        + remate("Lo que se busca después no son fotos: son <mark>descripciones</mark>.", desde=3))
    add(body, titulo="Indexing", cap=1, t=40, notas=[
        f"La arquitectura tiene dos tiempos. El primero pasa una sola vez, offline: el indexing. El "
        f"catálogo son {D['n_ikea']} productos de IKEA más {D['n_abo']} de Amazon Berkeley Objects, cada "
        f"uno con su foto, su tipo, su kind y sus medidas cuando las tiene.",
        "[paso] Un modelo de visión mira la foto de cada producto y escribe una descripción en ocho líneas "
        "fijas: tipo, uso, estilo, materiales, colores, forma, sensación y con qué combina. Un producto, "
        "un documento.",
        f"[paso] Esa descripción se embebe con {D['embed_model']}, que corre local: {D['best_dim']} números "
        f"por producto.",
        "[paso] Y va a ChromaDB junto con la metadata. Lo importante: lo que después buscamos no son "
        "fotos, son descripciones.",
    ])

    # ================================================================ 7 · por pedido, por capas
    capas_slide(D, ctx)

    # ================================================================ 8 · documento y consulta
    q_lines = cands[0]["spec"]["query"].splitlines()

    def l8(ls, n=48):
        out = ""
        for ln in ls:
            k, _, v = ln.partition(":")
            v = v.strip()
            out += f'<div class="l8"><span>{esc(k)}</span>{esc(v[:n])}{"…" if len(v) > n else ""}</div>'
        return out

    strip = ""
    for i, c in enumerate(cands[0]["candidates"]):
        ch = c["id"] == sofa
        strip += ficha(D, c["id"], 112, pos=i + 1, hi=ch, tag="elegido" if ch else None, cap=True,
                       titulo=f(c["score"]), sub=None)
    sc = next(c["score"] for c in cands[0]["candidates"] if c["id"] == sofa)
    rk = next(i for i, c in enumerate(cands[0]["candidates"]) if c["id"] == sofa) + 1
    body = (
        '<div class="cuerpo">' + cab("01", "Arquitectura · el corazón del retrieval", "Documento y consulta, <em>en las mismas ocho líneas</em>") + '</div>'
        '<div class="dq">'
        f'<div class="hoja dqc"><div class="dqh"><img src="{img.uri(foto_producto(D, sofa), 200, 200, fit="contain")}" alt="">'
        f'<div><div class="etq">el documento · lo que se indexa</div><b>{sofa} · sofá</b><span>lo escribió un VLM mirando la foto del producto</span></div></div>{l8(doc)}</div>'
        '<div class="dqmid" data-desde="1"><span>coseno</span></div>'
        f'<div class="hoja dqc" data-desde="1"><div class="dqh"><img class="rm" src="{img.uri(CL / "room.jpg", 280, 210)}" alt="">'
        f'<div><div class="etq">la consulta · lo que escribe plan</div><b>pieza 1 del living</b><span>plan no ve el catálogo: describe el producto ideal</span></div></div>{l8(q_lines)}</div>'
        '</div>'
        f'<div class="dqs" data-desde="2"><div class="dqsl"><div class="etq">los {len(cands[0]["candidates"])} más cercanos por coseno</div>'
        f'<p>Este sofá salió <b>{rk}.º</b>, con {f(sc)}. Choose lo eligió igual, mirando las fotos.</p></div><div class="tira">{strip}</div></div>')
    add(body, titulo="Documento y consulta", cap=1, t=45, notas=[
        "Esto es el corazón del retrieval. A la izquierda, el documento de un sofá del catálogo: lo "
        "escribió un modelo mirando su foto, en las ocho líneas.",
        "[paso] A la derecha, la consulta que escribió plan para el living de recién, sin ver el catálogo. "
        "Mismo formato, mismo vocabulario: «light grey», «Scandinavian», «white walls». La idea es que "
        "documento y consulta se parezcan como dos fichas del mismo catálogo, y se comparan por coseno.",
        f"[paso] Abajo, los cinco más cercanos. El sofá que terminó en la lista salió {rk}.º, con {f(sc)}, "
        f"muy cerca del primero. Choose lo eligió igual, porque mirando las fotos es el gris claro de "
        f"brazos anchos que pidió el usuario.",
    ])

    # ================================================================ 9 · variantes
    body = ('<div class="cuerpo">' + cab("01", "Arquitectura · el mapa de la charla", "Cada caja tuvo alternativas. <em>Las elegimos midiendo.</em>") + '</div>'
            + variantes_html(elegidas=False))
    add(body, titulo="Variantes", cap=1, t=30, notas=[
        "Cada caja del diagrama tuvo alternativas. Esta planilla es el mapa de la charla: cada fila es una "
        "decisión, y a la derecha está el experimento que la resolvió.",
        "La mayoría son hiperparámetros del retrieval, que es lo que se puede medir contra un ground truth. "
        "Lo de borde gris es de la v0, que buscaba por imagen. Y la última fila, el modelo de imagen, quedó "
        "diseñada pero sin correr. Al final volvemos a esta planilla con lo que elegimos.",
    ])

    # ================================================================ 10 · línea de tiempo
    fe = D["fechas"]
    dd = lambda d: d.strftime("%d/%m")
    evs = [
        ("v0", fe["v0"], "v0: buscar por imagen", "Detectar cada mueble en la foto, recortarlo y compararlo con las fotos del catálogo.", 0),
        ("", fe["v1"], "v1: buscar por texto", f"Descripciones de ocho líneas, Qwen3 y ChromaDB, sobre {D['n_275']} productos.", 0),
        ("", fe["rerank"], "Reranking y más catálogo", f"Opus reordena mirando las fotos. El catálogo pasa a {D['n_855']}: lámparas, deco, guardado.", 1),
        ("", fe["metricas"], "Métricas de la clase", "RAGAS, NDCG, reproducibilidad y relevancia graduada.", 1),
        ("", fe["sift"], "Control de la imagen", "SIFT + RANSAC contra la foto original, con reintento.", 1),
        ("", fe["revisado"], "Catálogo revisado", f"Se sacan {D['n_855'] - D['n_ikea']} productos con la foto de otro o fuera del alcance: quedan {D['n_ikea']}.", 2),
        ("", fe["abo"], "Un segundo catálogo", f"Amazon Berkeley Objects: {D['n_abo']} productos más, con medidas.", 2),
        ("sig", None, "Lo que sigue", "Los experimentos de la imagen, diseñados y sin correr.", 2),
    ]
    x0, x1, yax = 100, 1550, 610
    gap = (x1 - x0) / (len(evs) - 1)
    tl = (f'<svg class="tl-eje" viewBox="0 0 1920 1080"><line x1="72" y1="{yax}" x2="1848" y2="{yax}"/>'
          + "".join(f'<line class="tk" x1="{x0 + i * gap - 9:.0f}" y1="{yax + 9}" x2="{x0 + i * gap + 9:.0f}" y2="{yax - 9}"/>' for i in range(len(evs)))
          + "</svg>")
    for i, (cls, d, h, p, st) in enumerate(evs):
        up = i % 2 == 0
        x = x0 + i * gap
        der = False
        sty = (f"right:{1920 - x - 2:.0f}px;" if der else f"left:{x - 1:.0f}px;") + ("bottom:" + str(1080 - yax + 30) + "px" if up else "top:" + str(yax + 30) + "px")
        tl += (f'<div class="ev {cls} {"up" if up else "dn"}{" der" if der else ""}" style="{sty}"{" data-desde=" + chr(34) + str(st) + chr(34) if st else ""}>'
               f'<div class="evd">{dd(d) if d else "después"}</div><h4>{esc(h)}</h4><p>{esc(p)}</p></div>')
    body = ('<div class="cuerpo">' + cab("01", "Arquitectura · cronología", "Cómo se fue <em>transformando</em>") + '</div>'
            f'<div class="tl">{tl}</div>'
            + remate("Cada cambio de arquitectura salió de <mark>un experimento</mark>.", desde=2))
    add(body, titulo="Línea de tiempo", cap=1, t=30, notas=[
        f"Y así se fue transformando. El {dd(fe['v0'])} arrancamos con una v0 que buscaba por imagen. El "
        f"{dd(fe['v1'])} pasamos a texto, que es la arquitectura que acaban de ver; el primer experimento "
        f"explica por qué.",
        "[paso] Después vinieron el reranking con Opus y un catálogo más grande, las métricas de RAGAS y la "
        "reproducibilidad, y el control de la imagen.",
        f"[paso] En noviembre revisamos el catálogo a mano y sumamos un segundo catálogo, el {dd(fe['abo'])}. "
        f"Lo que sigue son los experimentos de imagen, que están diseñados.",
    ])

    # ================================================================ 11 · separador
    separador(2, ["Antes de los experimentos, cómo medimos. Esto vale para todo lo que sigue. Segunda pieza: el sofá."])

    # ================================================================ 12 · ground truth
    room_ikea = REPO / "datos/dataset/ikea/images/room_scenes" / EJ_ROOM
    ann = D["ej_annotated"]
    ann_html = "".join(ficha(D, pid, 104, cap=False) for pid in ann)
    body = (
        '<div class="cuerpo">' + cab("02", "Cómo medimos · el ground truth", "IKEA ya anota <em>qué hay en cada foto</em>") + '</div>'
        '<div class="gt">'
        f'<div><div class="foto" style="width:760px;height:476px"><img src="{img.uri(room_ikea, 1520, 952, q=76)}" alt=""></div>'
        '<p class="pie-foto">una foto de ambiente del dataset IKEA (Tautkute et al.)</p></div>'
        f'<div><div class="etq">sus {len(ann)} productos anotados</div><div class="anot">{ann_html}</div></div></div>'
        '<div class="cifras" data-desde="1">'
        f'<div><b>{D["rooms"]}</b><span>livings y comedores con productos anotados</span></div>'
        f'<div><b>{D["n_busquedas"]}</b><span>búsquedas: una por pieza que se ve, escrita como la escribiría plan</span></div>'
        f'<div class="acc"><b>{D["n_resp"]}</b><span>tienen su producto en el catálogo: sobre esas se mide</span></div>'
        f'<div><b>{f(D["azar_h1"])}</b><span>hit@1 eligiendo al azar entre lo que deja pasar el filtro</span></div></div>')
    add(body, titulo="Ground truth", cap=2, t=45, notas=[
        "Para medir el retrieval hacen falta respuestas correctas. El dataset de IKEA de Tautkute y otros "
        "trae fotos de ambientes armados y, para cada foto, qué productos del catálogo aparecen. Esta es "
        f"una, con sus {len(ann)} productos anotados.",
        f"[paso] Usamos los {D['rooms']} livings y comedores. Para cada foto, subagentes de Claude "
        f"escribieron una consulta por pieza que se ve, en las ocho líneas, como lo haría plan y sin ver el "
        f"catálogo ni las anotaciones. Son {D['n_busquedas']} búsquedas; {D['n_resp']} tienen su producto "
        f"en el catálogo, y sobre esas se mide. Una búsqueda acierta si trae el producto anotado de esa "
        f"pieza. De referencia: elegir al azar entre lo que deja pasar el filtro acierta el primero en el "
        f"{pct(D['azar_h1'], 1)} de los casos.",
    ])

    # ================================================================ 13 · métricas en un ejemplo
    ej, em = D["ej"], D["ej_metrics"]
    rel = set(ej["relevant"])
    cinta = "".join(ficha(D, pid, 132, cap=False, pos=i + 1, hi=pid in rel) for i, pid in enumerate(ej["ranked"][:10]))
    ql = ej["query"].splitlines()
    qshow = " · ".join(f"<b>{esc(l.split(':')[0])}:</b> {esc(l.split(':', 1)[1].strip())}"
                       for l in ql if l.split(":")[0] in ("Type", "Colors", "Shape"))
    cr_a, cr_b = D["ej_cr3"]
    mc = [
        (1, "hit@k", "¿Está el anotado entre los primeros k?", f"hit@1 · hit@3 · hit@5", f"{em['hit1']} · {em['hit3']} · {em['hit5']}"),
        (1, "MRR@10", "Uno sobre el puesto del primer relevante.", f"1 / {em['rank']}", f(em["rr"])),
        (2, "NDCG@10", "Ganancia descontada por log₂(puesto + 1), sobre la del orden ideal.", f"(1 / log₂ {em['rank'] + 1}) / 1", f(em["ndcg"])),
        (2, "context precision@10", "RAGAS: precisión@k promediada donde hay un relevante.", f"(1/{em['rank']}) / 1", f(em["cp"])),
        (3, "context recall@3", "RAGAS, por ambiente: de los anotados, cuántos aparecen en algún top-3.", f"{cr_a} de {cr_b} en esta foto", f(cr_a / cr_b)),
    ]
    cols = "".join(f'<div class="mc" data-desde="{st}"><div class="mn">{n}</div><p>{d}</p><code>{fo}</code><b>{v}</b></div>'
                   for st, n, d, fo, v in mc)
    body = (
        '<div class="cuerpo">' + cab("02", "Cómo medimos · las métricas", "Cinco métricas, <em>sobre una sola búsqueda</em>") + '</div>'
        f'<div class="mq"><span class="etq">la consulta · la alfombra de la foto anterior</span><p>{qshow}</p></div>'
        f'<div class="cinta"><div class="cinta-r"></div>{cinta}</div>'
        f'<div class="cinta-l"><span>el producto anotado quedó <b>{em["rank"]}.º</b> de {ej["universe"]} alfombras</span></div>'
        f'<div class="metricas">{cols}</div>')
    add(body, titulo="Las métricas, en un ejemplo", cap=2, t=70, notas=[
        f"Las métricas, sobre una sola búsqueda: la alfombra crema de pelo largo de la foto anterior. El "
        f"retrieval ordena las {ej['universe']} alfombras del catálogo y el producto anotado queda {em['rank']}.º.",
        f"[paso] **hit@k** pregunta si el anotado está entre los primeros k: acá hit@1 y hit@3 dan 0 y hit@5 "
        f"da 1. Promediado sobre todas las búsquedas es una proporción de aciertos, y es la métrica que más "
        f"vamos a usar. **MRR** es uno sobre el puesto del primer relevante: 1/{em['rank']}, {f(em['rr'], 2)}. "
        f"Premia que esté arriba aunque no sea primero.",
        f"[paso] **NDCG** descuenta la ganancia por el logaritmo del puesto y la normaliza por el orden ideal: "
        f"{f(em['ndcg'])}. **Context precision** de RAGAS promedia la precisión en cada puesto donde hay un "
        f"relevante; con un solo relevante coincide con MRR. En las {D['n_configs']} configuraciones que "
        f"corrimos, MRR y context precision correlacionan {f(D['corr_cp'], 4)}: miden casi lo mismo.",
        f"[paso] **Context recall**, también de RAGAS, se mira por ambiente: de los productos anotados de la "
        f"foto, cuántos aparecen en el top-3 de alguna de sus búsquedas. Acá, {cr_a} de {cr_b}.",
    ])

    # ================================================================ 14 · intervalos
    body = (
        '<div class="cuerpo">' + cab("02", "Cómo medimos · intervalos", "¿Cuándo una diferencia <em>es una diferencia?</em>") + '</div>'
        '<div class="boot"><div class="xl">'
        '<div class="bloque"><div class="bt">el problema</div><p>Las búsquedas de un mismo ambiente no son independientes: '
        'comparten la foto, la luz, el estilo. Un intervalo que las trate como sueltas sale demasiado angosto.</p></div>'
        f'<div class="bloque" data-desde="1"><div class="bt">bootstrap por ambiente</div><p>Se sortean {D["boot_rooms"]} ambientes '
        f'<strong>con reposición</strong>, se recalcula el hit@1 con todas sus búsquedas, y se repite {D["boot_n"]} veces. '
        'El intervalo del 95% va del percentil 2,5 al 97,5.</p></div></div>'
        f'<div class="boot-g" data-desde="1"><div class="ley"><span><i style="background:#2453D6"></i>dentro del 95%</span>'
        f'<span><i style="background:#C9CFD5"></i>afuera</span><span>hit@1 de cada una de las {D["boot_n"]} muestras · Qwen3, descripciones, filtro por tipo</span></div>'
        + hist(D["boot_means"], D["boot_lo"], D["boot_hi"], D["best"]["hit@1"], width=1080, height=520)
        + '</div></div>'
        + remate("La regla de toda la charla: si los intervalos de dos variantes se pisan, <mark>no decimos que una gana</mark>.", desde=2))
    add(body, titulo="Intervalos de confianza", cap=2, t=40, notas=[
        "Cada número de la charla va con un intervalo de confianza del 95%, por bootstrap. Pero ojo: las "
        "búsquedas de un mismo ambiente no son independientes, comparten la foto y el estilo.",
        f"[paso] Entonces remuestreamos ambientes, no búsquedas: sorteamos {D['boot_rooms']} ambientes con "
        f"reposición, recalculamos el hit@1, y lo repetimos {D['boot_n']} veces. El histograma son esas "
        f"medias; el intervalo va de {f(D['boot_lo'])} a {f(D['boot_hi'])}.",
        "[paso] Y la regla que usamos en toda la charla: si dos intervalos se pisan, no decimos que una "
        "variante le gana a la otra.",
    ])
    return ctx


# ---------------------------------------------------------------- 7 · el flujo por capas

def capas_slide(D, ctx):
    choices, cands, plan = ctx["choices"], ctx["cands"], ctx["plan"]
    P = sala.Proj()
    vb = sala.viewbox(P, pad=(20, 20, 10, 20), m=0)
    left, top, ancho = 980, 236, 860
    E = sala.Encuadre(P, left, top, ancho, vb)
    kinds = ["sofa", "alfombra", "mesa", "tv", "lampara", "almohadones", "planta", "cortinas"]
    # el plan: cajas fantasma con kind y tamaño máximo (lo que escribió plan)
    fant = "".join(sala.caja_alambre(P, sala.CAJA[k], "fantasma", k) for k in kinds)

    def tam(p):
        v = [p.get("max_width_cm"), p.get("max_depth_cm"), p.get("max_height_cm")]
        if not any(v):
            return ""
        return "≤ " + " × ".join(f"{x:.0f}" if x else "–" for x in v) + " cm"

    off = {"sofa": (-150, 70), "alfombra": (75, 45), "mesa": (-175, 210), "tv": (40, 115), "lampara": (-120, -40),
           "almohadones": (-150, -60), "planta": (90, -70), "cortinas": (70, -110)}
    rot_plan = ""
    for k, p in zip(kinds, plan):
        nm = KIND_ES.get(p["kinds"][0], p["kinds"][0])
        rot_plan += sala.rotulo(P, k, nm, *off[k], sub=tam(p), cls="rot acc")
    # la elección: los muebles dibujados
    mueb = sala.muebles(P, kinds)
    svg = (sala.abrir(P, vb, attrs=f'style="position:absolute;left:{left}px;top:{top}px;width:{ancho}px"')
           + sala.cascara(P, cotas=False)
           + f'<g data-hasta="2">{fant}</g>'
           + f'<g data-desde="2">{mueb}</g>'
           + f'<g data-hasta="1">{rot_plan}</g>'
           + "</svg>")
    # retrieve: los 5 candidatos de 4 piezas, en una columna al lado del cuarto, con su línea de llamada
    fans, lineas = "", ""
    idx = {"lampara": 4, "sofa": 0, "mesa": 2, "alfombra": 1}
    orden = sorted(idx, key=lambda k: E(*sala.ANCLA[k])[1])
    fx, fy0, fh, fgap = 600, 300, 112, 30
    for n, k in enumerate(orden):
        i = idx[k]
        ax, ay = E(*sala.ANCLA[k])
        y = fy0 + n * (fh + fgap)
        thumbs = ""
        for j, c in enumerate(cands[i]["candidates"]):
            ch = c["id"] == choices[i]["id"]
            u = img.uri(foto_producto(D, c["id"]), 130, 130, fit="contain")
            thumbs += f'<span class="ct{" ch" if ch else ""}"><img src="{u}" alt=""><i>{j + 1}</i></span>'
        fans += (f'<div class="abanico" style="left:{fx}px;top:{y}px" data-desde="1" data-hasta="3" data-en="2">'
                 f'<span class="ab-k">{KIND_ES.get(plan[i]["kinds"][0])} · los 5 más cercanos</span><div class="ab-t">{thumbs}</div></div>')
        x1, y1 = fx + 352, y + fh / 2
        lineas += (f'<path d="M{x1},{y1:.0f} L{x1 + 30},{y1:.0f} L{ax:.0f},{ay:.0f}"/><circle cx="{ax:.0f}" cy="{ay:.0f}" r="5"/>')
    fans += (f'<svg class="ab-lin" data-desde="1" data-hasta="3" style="position:absolute;left:0;top:0;width:1920px;height:1080px;overflow:visible;pointer-events:none">{lineas}</svg>')
    etapas = [
        ("plan", "Opus 5.5", "Mira la foto y el pedido: qué piezas, de qué kind, hasta qué tamaño. Escribe el producto ideal en 8 líneas.", "pre-retrieval · query rewriting"),
        ("retrieve", "ChromaDB", "Filtra por kind y medidas (where) y trae los k más cercanos por coseno.", "retrieval + metadata filtering"),
        ("choose", "Opus 5.5", "Mira las k fotos de cada pieza y elige la combinación y las cantidades.", "post-retrieval · reranking con un VLM"),
        ("imagen", "Nano Banana 2", f"Edición estricta de la foto; SIFT controla que siga siendo el mismo cuarto (hasta {D['sift_attempts']} intentos).", "generación + control"),
    ]
    ets = "".join(f'<div class="et" data-en="{i}"><div class="etn">{n}<span>{m}</span></div><p>{t}</p><div class="etq">{r}</div></div>'
                  for i, (n, m, t, r) in enumerate(etapas))
    cg = D["img"]["caballito-living"]["gen"]
    acc = next(i for i, a in enumerate(cg["attempts"]) if a["ok"]) + 1
    foto_fin = (f'<div class="capa-foto" data-desde="3" style="left:{left + 40}px;top:{top + 40}px;width:{ancho - 80}px">'
                f'<div class="foto"><img src="{img.uri(CL / "final.png", 1960, 1470, q=76)}" alt=""><span class="sello ok">intento {acc} · aceptada por SIFT</span></div></div>')
    body = ('<div class="cuerpo">' + cab("01", "Arquitectura · por pedido", "Por pedido: <em>plan, retrieve, choose</em> y la imagen") + '</div>'
            f'<div class="etapas">{ets}</div>' + svg + fans + foto_fin)
    add(body, titulo="Por pedido", cap=1, t=70, cls="lam-capas", notas=[
        "El segundo tiempo pasa en cada pedido, y lo vamos a ver como capas sobre el cuarto. Primero, "
        "**plan**, con Claude Opus 5.5: mira la foto y el pedido y decide qué piezas hacen falta, el kind de "
        "cada una y su tamaño máximo; son estas cajas punteadas. Y escribe el producto ideal de cada pieza "
        "en las mismas ocho líneas del catálogo. Es query rewriting.",
        "[paso] **retrieve** aplica esos filtros como where de Chroma y trae los k más cercanos por coseno: "
        "acá, los cinco candidatos de algunas piezas.",
        "[paso] **choose**, otra vez Opus, mira las fotos de los candidatos de cada pieza y elige la "
        "combinación y las cantidades. Es un reranking después del retrieval, hecho por un modelo que ve. "
        "Las cajas se vuelven muebles.",
        f"[paso] Y la imagen: un prompt de edición estricta, Nano Banana 2 edita la foto, y un control con "
        f"SIFT verifica que siga siendo el mismo cuarto; si no, se reintenta, hasta {D['sift_attempts']} veces.",
    ])


VARIANTES = [
    ("Qué se indexa", [("foto del producto", "v0"), ("texto del vendedor", "no"), ("descripción de 8 líneas", "si"), ("nombre + descripción", "no")], ["E1", "E2"]),
    ("Embedder", [("CLIP · DINOv2 · DINOv3", "v0"), ("hashing de palabras", "no"), ("BGE-base", "no"), ("Qwen3-Embedding", "si")], ["E1", "E2"]),
    ("Filtro de metadata", [("ninguno", "no"), ("tipo grueso", "no"), ("kind fino", "si")], ["E2"]),
    ("Documento", [("un producto entero", "si"), ("una línea por chunk", "no"), ("línea contra línea", "no")], ["E3"]),
    ("Dimensión", [("32 · 64 · 128 · 256 · 512", "no"), ("1024", "si")], ["E4"]),
    ("Base vectorial", [("ChromaDB, HNSW", "si"), ("búsqueda exacta", "no")], ["E5"]),
    ("Consulta", [("solo el kind", "no"), ("solo la línea Type", "no"), ("las 8 líneas", "si")], ["E6"]),
    ("Reranking", [("ninguno", "no"), ("cross-encoder de texto", "no"), ("VLM mirando fotos", "si")], ["E7"]),
    ("Candidatos por pieza", [("3", "no"), ("5", "si"), ("8", "no")], ["E8"]),
    ("Catálogo", [("IKEA", "no"), ("ABO", "no"), ("IKEA + ABO", "si")], ["E12"]),
    ("Prompt de la imagen", [("el LLM escribe la escena", "no"), ("edición libre", "no"), ("edición estricta + SIFT", "si")], ["E13"]),
    ("Modelo de imagen", [("Nano Banana 2", "si"), ("Nano Banana Pro", "pend"), ("gpt-image", "pend")], ["T4"]),
]


def variantes_html(elegidas: bool) -> str:
    out = ['<div class="planilla"><div class="ph">decisión</div><div class="ph">alternativas</div><div class="ph d">experimento</div>']
    for st, ops, exs in VARIANTES:
        chips = ""
        for o, s in ops:
            c = {"v0": "chip v0", "pend": "chip pend"}.get(s, "chip si" if (s == "si" and elegidas) else "chip")
            chips += f'<span class="{c}">{esc(o)}</span>'
        tags = "".join(f'<span class="xe{" pend" if e == "T4" else ""}">{e}</span>' for e in exs)
        out.append(f'<div class="pd">{esc(st)}</div><div class="pa">{chips}</div><div class="px">{tags}</div>')
    out.append("</div>")
    return "".join(out)

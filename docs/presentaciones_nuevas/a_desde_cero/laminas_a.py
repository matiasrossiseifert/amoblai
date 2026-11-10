"""Primera parte: el producto, la arquitectura y cómo medimos."""

from __future__ import annotations

from base import KIND_ES, add, blk, esc, f, hd, pct, usd
from componentes import (arquitectura, ficha, foto, img_uri, planta, product_photo, size_text)
from datos_deck import RES, jload
from graficos import hist

A = RES / "amoblar"

CAPITULOS = [
    # (sección, título del separador, bajada, piezas nuevas de la planta, experimentos)
    ("Arquitectura", "Cómo está <em>armado</em>",
     "Un RAG sobre un catálogo de muebles: qué se indexa, cómo se busca, quién elige y cómo se dibuja.",
     ["alfombra"], []),
    ("Cómo medimos", "Antes de comparar, <em>una vara</em>",
     "Un ground truth, cinco métricas de ranking y un intervalo de confianza para cada número.",
     ["sofá"], []),
    ("Qué guardamos", "Qué guardamos <em>en el índice</em>",
     "Indexing: qué representa a cada producto y dónde vive.",
     ["biblioteca"], [("E1", "imagen o texto"), ("E2", "texto, embedder y filtro"), ("E3", "splitting"),
                      ("E4", "dimensión del embedding"), ("E5", "base vectorial")]),
    ("Cómo buscamos", "Cómo buscamos <em>y quién elige</em>",
     "Lo que pasa en cada pedido, antes y después del retrieval.",
     ["mesa ratona", "sillón"], [("E6", "query rewriting"), ("E7", "reranking"),
                                 ("E8", "cuántos candidatos")]),
    ("Cuánto creerle", "Cuánto creerle <em>a los números</em>",
     "Si cambia quien escribe las consultas, si no está el producto exacto, si la respuesta inventa.",
     ["lámpara"], [("E9", "reproducibilidad"), ("E10", "relevancia graduada"),
                   ("E11", "RAGAS sobre la respuesta")]),
    ("De punta a punta", "De punta a punta, <em>en cuartos reales</em>",
     "Ambientes vacíos de verdad, pedidos de verdad: el catálogo y la imagen.",
     ["planta", "comedor"], [("E12", "qué catálogo"), ("E13", "la imagen y su control"),
                             ("T4", "lo que sigue")]),
    ("Cierre", "Lo que <em>quedó</em>",
     "La arquitectura final, el camino de los números, los costos y lo que aprendimos.",
     [], []),
]


def divider(i: int, notes: list[str], t: int = 10) -> None:
    sec, title, sub, new, exps = CAPITULOS[i]
    old = [p for c in CAPITULOS[:i] for p in c[3]]
    complete = i == len(CAPITULOS) - 1
    ol = ""
    if exps:
        ol = "<ol>" + "".join(f"<li><b>{e}</b>{esc(n)}</li>" for e, n in exps) + "</ol>"
    body = (f'<div class="dl"><div class="dk">{i + 1:02d} · {esc(sec)}</div><h2>{title}</h2>'
            f'<p class="ds">{sub}</p>{ol}</div>'
            f'<div class="dr">{planta(old, new, complete=complete)}</div>')
    add(body, sec=sec, title=sec, t=t, notes=notes, cls="div")


def build(D: dict) -> None:
    cl = D["img"]["caballito-living"]
    room_cl = A / "caballito-living" / "room.jpg"
    final_cl = A / "caballito-living" / "final.png"
    choices = cl["choice"]["answer"]["choices"]
    cands = jload(A / "caballito-living" / "2_candidates.json")["pieces"]
    no_first = sum(1 for c, p in zip(choices, cands) if p["candidates"][0]["id"] != c["id"])
    costo_cl = (jload(A / "caballito-living" / "1_searches.json")["cost_usd"]
                + cl["choice"]["cost_usd"] + cl["gen"]["cost_usd"])
    n_int = len(cl["gen"]["attempts"])

    # ------------------------------------------------------------------ 1. portada
    body = (
        '<div class="cl"><div class="eb">TP 3 · 73.69 Large Language Models · ITBA 2026</div>'
        '<h1>amobl<em>ai</em></h1>'
        '<p class="sub">Una foto de tu ambiente vacío y lo que querés, en tus palabras. '
        'Vuelve una lista de muebles reales de un catálogo y la foto de tu cuarto amoblado con ellos.</p></div>'
        '<div class="team">Juan Bautista Albertoni Salini<br>Matias Juan Rossi Seifert<br>Junior Rambau</div>'
        f'<div class="split"><div class="in"><img src="{img_uri(room_cl, 1100, 825, q=74)}" alt="">'
        f'<img class="after" src="{img_uri(final_cl, 1100, 825, q=74)}" alt="">'
        '<div class="line"></div><div class="knob">↔</div>'
        '<span class="lab a">la foto</span><span class="lab b">amoblai</span></div></div>'
        f'<div class="scap">Living de un departamento propio. A la derecha, la imagen generada con los '
        f'{len(choices)} productos de la lista.</div>'
    )
    add(body, sec="amoblai", title="Portada", t=30, cls="cover", notes=[
        "Buenas. Somos Juan Bautista, Matías y Junior, y esto es **amoblai**.",
        f"A la izquierda, la foto de un living vacío, de un departamento propio. A la derecha, lo "
        f"que devuelve amoblai: el mismo living con {len(choices)} productos reales de un catálogo.",
        "En la próxima media hora les contamos qué hace, cómo está armado y, sobre todo, cómo lo "
        "medimos: cada decisión de la arquitectura salió de un experimento, y los vamos a ir viendo "
        "uno por uno.",
    ])

    # ------------------------------------------------------------------ 2. el problema
    cards = [
        ("Un generador de imágenes te amobla la foto…",
         "…con muebles que no existen. No tienen medida, ni precio, ni dónde comprarlos."),
        ("Un catálogo tiene muebles reales…",
         "…pero no mira tu cuarto. Buscás por filtros y la combinación la armás vos, pieza por pieza."),
        ("Nosotros queremos las dos cosas",
         "Productos reales, elegidos para esa foto y ese pedido, y la imagen de tu ambiente con "
         "exactamente esos productos."),
    ]
    cs = "".join(
        f'<div class="card pc"{"" if i == 0 else f" data-step={i}"}><div class="num">{i + 1}</div>'
        f'<h3>{esc(a)}</h3><p>{esc(b)}</p></div>'
        for i, (a, b) in enumerate(cards))
    body = hd("El problema", "Tenés el ambiente vacío y una idea. <em>Te faltan los muebles concretos.</em>")
    body += f'<div class="pcards">{cs}</div>'
    body += ('<div class="pfoot" data-step="2"><b>Es un problema de RAG.</b> La respuesta tiene que salir '
             'de lo que se recupera de un catálogo, no de lo que el modelo imagina: el LLM planifica, '
             'busca y elige, pero solo entre productos que existen.</div>')
    add(body, sec="amoblai", title="El problema", t=50, notes=[
        "Arranquemos por el problema. Te mudás, tenés el ambiente vacío y una idea de lo que querés. "
        "Hoy hay dos caminos y ninguno alcanza.",
        "Un generador de imágenes te amobla la foto, pero con muebles inventados: no los podés "
        "medir ni comprar. [paso] Un catálogo tiene productos reales, pero no mira tu cuarto: "
        "filtrás por tipo, color, precio, y combinar ocho cosas que vayan entre sí y con tu piso lo "
        "hacés vos.",
        "[paso] Nosotros queremos las dos cosas a la vez. Y eso, en el fondo, es un problema de RAG: "
        "la respuesta tiene que salir de lo que recuperamos del catálogo, no de la imaginación del "
        "modelo.",
    ])

    # ------------------------------------------------------------------ 3. qué hace
    req = cl["req"]["request"]
    fichas_html = ""
    for c in choices:
        pid = c["id"]
        k = D["items"][pid]["kind"]
        fichas_html += ficha(D, pid, size=126, qty=c.get("quantity"), title=KIND_ES.get(k, k),
                             sub=f"{pid} · {size_text(D, pid)}")
    why_sofa = choices[0]["why"]
    body = hd("El producto", "Una foto y un pedido. <em>Una lista y una imagen.</em>")
    body += (
        '<div class="prod">'
        f'<div class="pl"><p class="quote pq">{esc(req)}</p>'
        '<div class="pphotos">'
        + foto(img_uri(room_cl, 960, 720, q=72), 470, 352, cap="la foto que sube el usuario")
        + '<div class="parr" data-step="2">→</div>'
        + f'<div data-step="2">{foto(img_uri(final_cl, 960, 720, q=74), 470, 352, cap=f"la imagen, con los productos de la lista")}</div>'
        + '</div></div>'
        f'<div class="pr" data-step="1"><div class="lbl">La lista: {len(choices)} productos del catálogo</div>'
        f'<div class="fgrid g4">{fichas_html}</div>'
        f'<div class="pwhy"><span class="cap">el porqué del sofá, como lo escribe el modelo</span>'
        f'<p>«{esc(why_sofa)}»</p></div></div>'
        '</div>')
    add(body, sec="amoblai", title="Qué hace amoblai", t=75, notes=[
        "Así se usa. El usuario sube la foto del ambiente y escribe el pedido como le sale: "
        "«un living moderno y luminoso para recibir amigos, un sofá gris claro contra la pared de la "
        "izquierda, una mesa ratona de madera clara, una alfombra grande…».",
        f"[paso] amoblai devuelve la lista: {len(choices)} productos reales del catálogo, con "
        f"cantidades (los almohadones van por dos) y medidas cuando el catálogo las tiene. Cada uno "
        f"viene con su porqué. Un detalle que vamos a retomar: en {no_first} de las {len(choices)} "
        f"piezas eligió un producto que no era el más parecido por coseno.",
        f"[paso] Y la imagen: el mismo cuarto, con esos productos. Esta corrida costó {usd(costo_cl)}, "
        f"con {n_int} intentos de imagen. Por qué hubo {n_int} lo vemos al final.",
    ])

    # ------------------------------------------------------------------ 4. lo que tiene que cumplir
    rows = [
        ("Que los productos sean los que van", "retrieval contra un ground truth: hit@k, MRR, NDCG, "
         "context precision y recall", ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"]),
        ("Y si no está el exacto, algo que sirva", "relevancia graduada por un juez LLM", ["E10"]),
        ("Que se pueda creer cada número", "intervalos bootstrap y consultas reescritas tres veces",
         ["E9"]),
        ("Un porqué que no invente", "faithfulness (RAGAS)", ["E11"]),
        ("Que responda a lo que pidió", "answer relevance (RAGAS) y un juez de a pares", ["E11", "E12"]),
        ("Tu cuarto, no otro", "SSIM fuera de los muebles, SIFT, fidelidad de cada producto", ["E13"]),
    ]
    tr = "".join(
        f'<div class="pr1">{esc(a)}</div><div class="pr2">{esc(b)}</div>'
        f'<div class="pr3">{"".join(f"<span class=etag>{e}</span>" for e in es)}</div>'
        for a, b, es in rows)
    body = hd("El producto", "Lo que tiene que cumplir, <em>y cómo lo vamos a medir</em>")
    body += ('<div class="ptab"><div class="ph1">lo que promete</div><div class="ph1">cómo lo medimos</div>'
             f'<div class="ph1">dónde</div>{tr}</div>')
    add(body, sec="amoblai", title="Lo que tiene que cumplir", t=40, notes=[
        "Antes de entrar en la arquitectura, lo que amoblai promete, porque de acá salen las métricas.",
        "Que los productos sean los que van: eso es retrieval y se mide contra un ground truth, con las "
        "métricas de ranking de la materia. Que si el exacto no está, traiga algo que sirva. Que cada "
        "número se pueda creer. Que el porqué no invente y que la respuesta conteste lo que se pidió: "
        "ahí entran RAGAS y un juez. Y que la imagen sea tu cuarto y no otro.",
        "La columna de la derecha es el índice: E1 a E13 son los experimentos que vienen.",
    ])

    # ------------------------------------------------------------------ 5. separador
    divider(0, ["Entonces: ¿cómo está armado?"], t=10)

    # ------------------------------------------------------------------ 6. arquitectura
    room_th = img_uri(room_cl, 240, 180, q=72)
    body = hd("Arquitectura", "Un RAG en tres tiempos: <em>indexar, buscar y elegir, dibujar</em>")
    body += f'<div class="archwrap">{arquitectura(D, room_th, steps=True, badges=False, k="k")}</div>'
    add(body, sec="Arquitectura", title="Arquitectura", t=100, notes=[
        f"Arriba, lo que se hace una sola vez: el indexing. El catálogo son {D['n_ikea']} productos "
        f"de IKEA más {D['n_abo']} de Amazon Berkeley Objects. Un modelo de visión mira la foto de "
        f"cada producto y escribe una descripción en ocho líneas fijas: tipo, uso, estilo, "
        f"materiales, colores, forma, sensación y con qué combina. Esa descripción se embebe con "
        f"{D['embed_model']}, que corre local, y va a ChromaDB junto con la metadata: tipo, kind y medidas.",
        "[paso] Por cada pedido, el paso **plan**, con Claude Opus 5.5, mira la foto y el pedido, "
        "decide qué piezas hacen falta, el kind de cada una y su tamaño máximo, y escribe el producto "
        "ideal en las mismas ocho líneas del catálogo. Es query rewriting.",
        "[paso] **retrieve** aplica esos filtros como where de Chroma y trae los k más cercanos por coseno.",
        "[paso] **choose**, otra vez Opus, mira las fotos de los k candidatos de cada pieza y elige la "
        "combinación y las cantidades. Es un reranking después del retrieval, hecho por un modelo que ve.",
        f"[paso] Y la imagen: un prompt de edición estricta, Nano Banana 2 edita la foto, y un control "
        f"con SIFT verifica que siga siendo el mismo cuarto; si no, se reintenta, hasta {D['sift_attempts']} veces.",
    ])

    # ------------------------------------------------------------------ 7. documento y consulta
    sofa = choices[0]["id"]
    q_sofa = cands[0]["spec"]["query"]
    doc_lines = D["desc"][sofa].splitlines()
    q_lines = q_sofa.splitlines()

    def lines8(ls):
        out = []
        for ln in ls:
            k, _, v = ln.partition(":")
            out.append(f'<div class="l8"><span class="k">{esc(k)}</span><span class="v">{esc(v.strip())}</span></div>')
        return "".join(out)

    cand_strip = ""
    for i, c in enumerate(cands[0]["candidates"]):
        chosen = c["id"] == sofa
        cand_strip += ficha(D, c["id"], size=104, cap=False, rank=i + 1, hi=chosen,
                            tag="elegido" if chosen else None).replace(
            "</figure>", f'<div class="cos">{f(c["score"])}</div></figure>')
    sc = next(c["score"] for c in cands[0]["candidates"] if c["id"] == sofa)
    rk = next(i for i, c in enumerate(cands[0]["candidates"]) if c["id"] == sofa) + 1
    body = hd("Arquitectura", "Documento y consulta, <em>en las mismas ocho líneas</em>")
    body += (
        '<div class="dq">'
        f'<div class="dqc"><div class="dqh"><img src="{img_uri(product_photo(D, sofa), 200, 200, q=80, fit="contain")}" alt="">'
        f'<div><div class="lbl">El documento: lo que se indexa</div><p>{sofa} · sofá. Lo escribió un VLM mirando la foto del producto.</p></div></div>'
        f'{lines8(doc_lines)}</div>'
        f'<div class="dqc" data-step="1"><div class="dqh"><img class="rm" src="{img_uri(room_cl, 260, 196, q=72)}" alt="">'
        f'<div><div class="lbl">La consulta: lo que escribe plan</div><p>Pieza 1 del living. Plan no ve el catálogo: describe el producto ideal.</p></div></div>'
        f'{lines8(q_lines)}</div></div>'
        f'<div class="dqs" data-step="2"><div class="dqsl"><div class="lbl">Los {len(cands[0]["candidates"])} más cercanos por coseno</div>'
        f'<p>Este sofá salió {rk}.º, con {f(sc)}. Choose lo eligió igual, mirando las fotos.</p></div>'
        f'<div class="strip">{cand_strip}</div></div>')
    add(body, sec="Arquitectura", title="Documento y consulta", t=50, notes=[
        "Esto es el corazón del retrieval. A la izquierda, el documento de un sofá del catálogo: lo "
        "escribió un modelo mirando su foto, en las ocho líneas.",
        "[paso] A la derecha, la consulta que escribió plan para el living de recién, sin ver el "
        "catálogo. Mismo formato, mismo vocabulario: «light grey», «Scandinavian», «white walls». "
        "La idea es que documento y consulta se parezcan como dos fichas del mismo catálogo.",
        f"[paso] Abajo, los cinco más cercanos por coseno. El sofá que terminó en la lista salió "
        f"{rk}.º, con {f(sc)}, muy cerca del primero. Choose lo eligió igual, porque mirando las "
        f"fotos es el gris claro de brazos anchos que pidió el usuario.",
    ])

    # ------------------------------------------------------------------ 8. variantes
    body = hd("Arquitectura", "Cada caja tuvo alternativas. <em>Las elegimos midiendo.</em>")
    body += variantes_html(D, elegidas=False)
    add(body, sec="Arquitectura", title="Variantes", t=40, notes=[
        "Cada caja del diagrama tuvo alternativas. Esta tabla es el mapa de la charla: cada fila es "
        "una decisión, y a la derecha está el experimento que la resolvió.",
        "La mayoría son hiperparámetros del retrieval, que es lo que se puede medir contra un ground "
        "truth. Lo gris es de la v0, que buscaba por imagen. Y la última fila, el modelo de imagen, "
        "quedó diseñada pero sin correr. Al final volvemos a esta tabla con lo que elegimos.",
    ])

    # ------------------------------------------------------------------ 9. línea de tiempo
    fe = D["fechas"]
    dd = lambda d: d.strftime("%d/%m")
    evs = [
        ("v0", fe["v0"], "v0: buscar por imagen", "Detectar cada mueble en la foto, recortarlo y compararlo con las fotos del catálogo."),
        ("", fe["v1"], "v1: buscar por texto", f"Descripciones de ocho líneas, Qwen3 y ChromaDB, sobre {D['n_275']} productos."),
        ("", fe["rerank"], "Reranking y más catálogo", f"Opus reordena mirando las fotos. El catálogo pasa a {D['n_855']}: lámparas, deco, guardado."),
        ("", fe["metricas"], "Métricas de la clase", "RAGAS, NDCG, reproducibilidad y relevancia graduada."),
        ("", fe["sift"], "Control de la imagen", "SIFT + RANSAC contra la foto original, con reintento."),
        ("", fe["revisado"], "Catálogo revisado", f"Se sacan {D['n_855'] - D['n_ikea']} productos con la foto de otro o fuera del alcance: quedan {D['n_ikea']}."),
        ("", fe["abo"], "Un segundo catálogo", f"Amazon Berkeley Objects: {D['n_abo']} productos más, con medidas."),
        ("next", None, "Lo que sigue", "Los experimentos de la imagen, diseñados y sin correr."),
    ]
    W, BW = 1712, 330
    gap = (W - BW) / (len(evs) - 1)
    tl = '<div class="tl"><div class="axis"></div>'
    for i, (cls, d, h, p) in enumerate(evs):
        side = "up" if i % 2 == 0 else "dn"
        dt = dd(d) if d else "después"
        stp = "" if i < 2 else f' data-step="{1 if i < 5 else 2}"'
        tl += (f'<div class="ev {cls} {side}" style="left:{i * gap:.0f}px"{stp}><i class="dot"></i><i class="stem"></i>'
               f'<div class="bx"><div class="dt">{dt}</div><h4>{esc(h)}</h4><p>{esc(p)}</p></div></div>')
    tl += "</div>"
    body = hd("Arquitectura", "Cómo se fue transformando")
    body += tl
    add(body, sec="Arquitectura", title="Línea de tiempo", t=35, notes=[
        f"Y así se fue transformando. El {dd(fe['v0'])} arrancamos con una v0 que buscaba por imagen. "
        f"El {dd(fe['v1'])} pasamos a texto, que es la arquitectura que acaban de ver; el primer "
        f"experimento explica por qué.",
        f"[paso] Después vinieron el reranking con Opus y un catálogo más grande, las métricas de "
        f"RAGAS y la reproducibilidad, y el control de la imagen.",
        f"[paso] En noviembre revisamos el catálogo a mano y sumamos un segundo catálogo, el "
        f"{dd(fe['abo'])}. Lo que sigue son los experimentos de imagen, que están diseñados.",
    ])

    # ------------------------------------------------------------------ 10. separador
    divider(1, ["Antes de los experimentos, cómo medimos. Esto vale para todo lo que sigue."], t=10)

    # ------------------------------------------------------------------ 11. ground truth
    from datos_deck import EJ_ROOM, REPO
    room_ikea = REPO / "datos/dataset/ikea/images/room_scenes" / EJ_ROOM
    ann = D["ej_annotated"]
    ann_html = "".join(ficha(D, pid, size=98, cap=False) for pid in ann)
    body = hd("Cómo medimos", "Un ground truth que ya existía: <em>IKEA dice qué hay en cada foto</em>")
    body += (
        '<div class="gt">'
        + foto(img_uri(room_ikea, 1000, 628, q=76), 760, 477,
               cap="Una foto de ambiente del dataset IKEA (Tautkute et al.)")
        + f'<div class="gtr"><div class="lbl">Sus {len(ann)} productos anotados</div>'
        f'<div class="fgrid g5">{ann_html}</div></div></div>'
        '<div class="stats" data-step="1">'
        f'<div><div class="big">{D["rooms"]}</div><div class="kl">livings y comedores con productos anotados</div></div>'
        f'<div><div class="big">{D["n_busquedas"]}</div><div class="kl">búsquedas: una por pieza que se ve, escrita como la escribiría plan</div></div>'
        f'<div><div class="big t">{D["n_resp"]}</div><div class="kl">tienen su producto en el catálogo: sobre esas se mide</div></div>'
        f'<div><div class="big">{f(D["azar_h1"])}</div><div class="kl">hit@1 eligiendo al azar entre lo que deja pasar el filtro</div></div>'
        '</div>')
    add(body, sec="Cómo medimos", title="Ground truth", t=60, notes=[
        "Para medir el retrieval hacen falta respuestas correctas. El dataset de IKEA de Tautkute y "
        "otros trae fotos de ambientes armados y, para cada foto, qué productos del catálogo aparecen. "
        f"Esta es una, con sus {len(ann)} productos anotados.",
        f"[paso] Usamos los {D['rooms']} livings y comedores. Para cada foto, subagentes de Claude "
        f"escribieron una consulta por pieza que se ve, en las ocho líneas, como lo haría plan y sin "
        f"ver el catálogo ni las anotaciones. Son {D['n_busquedas']} búsquedas; {D['n_resp']} tienen "
        f"su producto en el catálogo, y sobre esas se mide. Una búsqueda acierta si trae el producto "
        f"anotado de esa pieza.",
        f"Para tener una referencia: elegir al azar entre lo que deja pasar el filtro acierta el "
        f"primero en el {pct(D['azar_h1'], 1)} de los casos.",
    ])

    # ------------------------------------------------------------------ 12. métricas en un ejemplo
    ej, em = D["ej"], D["ej_metrics"]
    rel = set(ej["relevant"])
    strip = "".join(ficha(D, pid, size=152, cap=False, rank=i + 1, hi=pid in rel)
                    for i, pid in enumerate(ej["ranked"][:10]))
    ql = ej["query"].splitlines()
    qshow = " · ".join(f"<b>{esc(l.split(':')[0])}:</b> {esc(l.split(':', 1)[1].strip())}"
                       for l in ql if l.split(":")[0] in ("Type", "Colors", "Shape"))
    cr_a, cr_b = D["ej_cr3"]
    mc = [
        (1, "hit@k", "¿Está el anotado entre los primeros k?",
         f"hit@1 = {em['hit1']} · hit@3 = {em['hit3']} · hit@5 = {em['hit5']}", None),
        (1, "MRR@10", "Uno sobre el puesto del primer relevante. Premia que esté arriba.",
         f"1 / {em['rank']}", em["rr"]),
        (2, "NDCG@10", "Ganancia descontada por log₂(puesto + 1), sobre la del orden ideal.",
         f"(1 / log₂ {em['rank'] + 1}) / 1", em["ndcg"]),
        (2, "Context precision@10", "RAGAS: la precisión@k promediada en los puestos donde hay un relevante.",
         f"Σ P@k·v_k / relevantes = (1/{em['rank']}) / 1", em["cp"]),
        (3, "Context recall@3", "RAGAS, por ambiente: de sus productos anotados, cuántos aparecen en el top-3 de alguna búsqueda.",
         f"{cr_a} de {cr_b} en esta foto", cr_a / cr_b),
    ]
    cards = ""
    for st, name, dfn, form, val in mc:
        v = f'<div class="mv">{f(val)}</div>' if val is not None else '<div class="mv">0 · 0 · 1</div>'
        cards += (f'<div class="mcard" data-step="{st}"><div class="mn">{name}</div><p>{dfn}</p>'
                  f'<div class="mf">{form}</div>{v}</div>')
    body = hd("Cómo medimos", "Cinco métricas, <em>sobre una sola búsqueda</em>")
    body += (f'<div class="mq"><span class="lbl">la consulta (alfombra de la foto anterior)</span><p>{qshow}</p></div>'
             f'<div class="strip s10">{strip}</div>'
             '<div class="mlegend"><span><i class="hi"></i>el producto anotado: puesto '
             f'{em["rank"]} de {ej["universe"]} alfombras</span></div>'
             f'<div class="mcards">{cards}</div>')
    add(body, sec="Cómo medimos", title="Las métricas, en un ejemplo", t=85, notes=[
        f"Las métricas, sobre una sola búsqueda: la alfombra crema de pelo largo de la foto anterior. "
        f"El retrieval ordena las {ej['universe']} alfombras del catálogo y el producto anotado queda "
        f"{em['rank']}.º.",
        f"[paso] **hit@k** pregunta si el anotado está entre los primeros k: acá hit@1 y hit@3 dan 0 y "
        f"hit@5 da 1. Promediado sobre todas las búsquedas es una proporción de aciertos, y es la "
        f"métrica que más vamos a usar. **MRR** es uno sobre el puesto del primer relevante: 1/{em['rank']}, "
        f"{f(em['rr'], 2)}. Premia que esté arriba aunque no sea primero.",
        f"[paso] **NDCG** descuenta la ganancia por el logaritmo del puesto y la normaliza por el orden "
        f"ideal: {f(em['ndcg'])}. **Context precision** de RAGAS promedia la precisión en cada puesto "
        f"donde hay un relevante; con un solo relevante coincide con MRR. De hecho, en las "
        f"{D['n_configs']} configuraciones que corrimos, MRR y context precision correlacionan "
        f"{f(D['corr_cp'], 4)}: miden casi lo mismo.",
        f"[paso] **Context recall**, también de RAGAS, se mira por ambiente: de los productos anotados "
        f"de la foto, cuántos aparecen en el top-3 de alguna de sus búsquedas. Acá, {cr_a} de {cr_b}.",
    ])

    # ------------------------------------------------------------------ 13. intervalos
    body = hd("Cómo medimos", "¿Cuándo una diferencia <em>es una diferencia?</em>")
    body += (
        '<div class="boot"><div class="xl">'
        + blk("El problema", "<p>Las búsquedas de un mismo ambiente no son independientes: comparten "
              "la foto, la luz, el estilo. Un intervalo que las trate como sueltas sale demasiado angosto.</p>")
        + blk("Bootstrap por ambiente",
              f"<p>Se sortean {D['boot_rooms']} ambientes <strong>con reposición</strong>, se recalcula "
              f"el hit@1 con todas sus búsquedas, y se repite {D['boot_n']} veces. El intervalo del 95% "
              f"va del percentil 2,5 al 97,5.</p>", step=1)
        + blk("La regla de toda la charla",
              "<p>Si los intervalos de dos variantes se pisan, no decimos que una le gana a la otra.</p>",
              step=2)
        + '</div><div class="bootc" data-step="1"><div class="legend"><span><i style="background:#B0502A"></i>'
        f'dentro del 95%</span><span><i style="background:#B9BDC0"></i>afuera</span>'
        f'<span>│ hit@1 medido: {f(D["best"]["hit@1"])}</span></div>'
        + hist(D["boot_means"], D["boot_lo"], D["boot_hi"], D["best"]["hit@1"], width=960, height=590)
        + f'<div class="cap" style="margin-top:8px">hit@1 de cada una de las {D["boot_n"]} muestras · '
        f'Qwen3, descripciones, filtro por tipo</div></div></div>')
    add(body, sec="Cómo medimos", title="Intervalos de confianza", t=40, notes=[
        "Cada número de la charla va con un intervalo de confianza del 95%, por bootstrap. Pero ojo: "
        "las búsquedas de un mismo ambiente no son independientes, comparten la foto y el estilo.",
        f"[paso] Entonces remuestreamos ambientes, no búsquedas: sorteamos {D['boot_rooms']} ambientes "
        f"con reposición, recalculamos el hit@1, y lo repetimos {D['boot_n']} veces. El histograma son "
        f"esas medias; el intervalo va de {f(D['boot_lo'])} a {f(D['boot_hi'])}.",
        "[paso] Y la regla que usamos en toda la charla: si dos intervalos se pisan, no decimos que una "
        "variante le gana a la otra.",
    ])


VARIANTES = [
    # (decisión, [(opción, estado)], experimentos)   estado: si | no | v0 | pend
    ("Qué se indexa", [("foto del producto", "v0"), ("texto del vendedor", "no"),
                       ("descripción de 8 líneas", "si"), ("nombre + descripción", "no")], ["E1", "E2"]),
    ("Embedder", [("CLIP · DINOv2 · DINOv3", "v0"), ("hashing de palabras", "no"), ("BGE-base", "no"),
                  ("Qwen3-Embedding", "si")], ["E1", "E2"]),
    ("Filtro de metadata", [("ninguno", "no"), ("tipo grueso", "no"), ("kind fino", "si")], ["E2"]),
    ("Documento", [("un producto entero", "si"), ("una línea por chunk", "no"),
                   ("línea contra línea", "no")], ["E3"]),
    ("Dimensión", [("32 · 64 · 128 · 256 · 512", "no"), ("1024", "si")], ["E4"]),
    ("Base vectorial", [("ChromaDB, HNSW", "si"), ("búsqueda exacta", "no")], ["E5"]),
    ("Consulta", [("solo el kind", "no"), ("solo la línea Type", "no"), ("las 8 líneas", "si")], ["E6"]),
    ("Reranking", [("ninguno", "no"), ("cross-encoder de texto", "no"), ("VLM mirando fotos", "si")], ["E7"]),
    ("Candidatos por pieza", [("3", "no"), ("5", "si"), ("8", "no")], ["E8"]),
    ("Catálogo", [("IKEA", "no"), ("ABO", "no"), ("IKEA + ABO", "si")], ["E12"]),
    ("Prompt de la imagen", [("el LLM escribe la escena", "no"), ("edición libre", "no"),
                             ("edición estricta + SIFT", "si")], ["E13"]),
    ("Modelo de imagen", [("Nano Banana 2", "si"), ("Nano Banana Pro", "pend"), ("gpt-image", "pend")], ["T4"]),
]


def variantes_html(D, elegidas: bool) -> str:
    out = ['<div class="vt"><div class="hdr">decisión</div><div class="hdr">alternativas</div>'
           '<div class="hdr ex">experimento</div>']
    for st, ops, exs in VARIANTES:
        chips = ""
        for o, s in ops:
            if s == "v0":
                c = "chip v0"
            elif s == "pend":
                c = "chip pend"
            elif s == "si" and elegidas:
                c = "chip si"
            else:
                c = "chip"
            chips += f'<span class="{c}">{esc(o)}</span>'
        tags = "".join(f'<span class="etag{" pend" if e == "T4" else ""}">{e}</span>' for e in exs)
        out.append(f'<div class="st">{esc(st)}</div><div>{chips}</div><div class="ex">{tags}</div>')
    out.append("</div>")
    return "".join(out)

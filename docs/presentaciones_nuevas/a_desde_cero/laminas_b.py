"""Segunda parte: los experimentos (E1–E13), lo que sigue, el cierre y el apéndice."""

from __future__ import annotations

import re

from base import CAT_ES, KIND_ES, add, blk, esc, exp, f, hd, hdx, pct, usd
from pathlib import Path

from componentes import crop_uri, ficha, foto, img_uri, product_photo
from visuales import sift_pair, ssim_mask
from datos_deck import BEST, REPO, RES
from graficos import COL, dots_repro, dumbbell, hbars, heatmap, line_chart
from laminas_a import divider, variantes_html
from laminas_c import futuro_slides, replica_slides

A = RES / "amoblar"


def ci(m, k="hit@1"):
    return tuple(m[f"{k}_ic95"])


def build(D: dict) -> None:
    b = D["best"]
    divider(2, ["Primer capítulo de experimentos: qué guardamos en el índice. Cinco decisiones del indexing."])

    # ================================================================== E1 imagen o texto
    lab = {"E0-naive-clip": "CLIP, el recorte tal cual", "E1-quitar-fondo": "+ quitar el fondo",
           "E2-filtro-categoria": "+ filtro por categoría", "E3-dinov2": "DINOv2 en lugar de CLIP",
           "E3-dinov3": "DINOv3 en lugar de DINOv2", "E4-dinov3-sin-quitar-fondo": "DINOv3, sin quitar el fondo"}
    rows = [dict(label=lab[p["paso"]], value=p["hit1"], ci=tuple(p["ic"]), kind="alt",
                 sub="imagen · v0" if i == 0 else None) for i, p in enumerate(D["v0_path"])]
    v0best = D["v0_path"][-1]
    rows.append(dict(label="Texto: descripciones + Qwen3", value=D["v1_275"]["hit@1"],
                     ci=ci(D["v1_275"]), kind="main", sub="texto · v1"))
    res = ('<div class="legend"><span>hit@1 con IC 95% · mismo ground truth, catálogo de '
           f'{D["n_275"]} productos</span></div>'
           + hbars(rows, width=980, label_w=360, row_h=64, x_max=0.8, ticks=[0, .2, .4, .6, .8],
                   tick_fmt=lambda t: f(t, 1)))
    exp("E1", "Qué guardamos", "¿Buscamos los muebles <em>por imagen o por texto?</em>",
        "<p>La v0 buscaba por imagen: detectar cada mueble en una foto, recortarlo y compararlo con "
        "las fotos del catálogo. Es lo natural para «encontrá este mueble».</p><p>Pero en amoblai "
        "<strong>el ambiente está vacío</strong>: no hay nada que recortar. Lo que hay es un pedido.</p>",
        f"<p>El mismo ground truth y el mismo catálogo que vio la v0 ({D['n_275']} productos).</p>"
        f"<ul><li><strong>Imagen:</strong> seis pasos acumulados, de CLIP a DINOv3, sobre "
        f"{v0best['n']} recortes de muebles.</li><li><strong>Texto:</strong> descripciones de ocho "
        f"líneas y Qwen3, sobre {D['v1_275']['answerable']} búsquedas.</li></ul>",
        res,
        f"<strong>Texto.</strong> Le gana al mejor retrieval por imagen ({f(D['v1_275']['hit@1'])} "
        f"contra {f(v0best['hit1'])}), funciona con el cuarto vacío y deja que un LLM escriba la "
        f"consulta a partir del pedido.",
        t=65, notes=[
            "Primer experimento, y el que cambió todo: ¿buscamos por imagen o por texto?",
            "La v0 buscaba por imagen: detectaba cada mueble en la foto, lo recortaba y lo comparaba "
            "con las fotos del catálogo. Es lo natural si la pregunta es «encontrá este mueble». Pero "
            "en amoblai el ambiente está vacío: no hay nada que recortar, hay un pedido.",
            f"[paso] Para comparar en serio usamos el mismo ground truth y el mismo catálogo que vio la "
            f"v0, {D['n_275']} productos. Por imagen, seis pasos acumulados, de CLIP a DINOv3. Por "
            f"texto, las descripciones con Qwen3.",
            f"[paso] La imagen mejoró mucho con cada paso: de {f(D['v0_path'][0]['hit1'])} a "
            f"{f(v0best['hit1'])}. Pero el texto llega a {f(D['v1_275']['hit@1'])}, con intervalos "
            f"que apenas se tocan.",
            "[paso] Decidimos texto. Gana, y además es lo único que funciona con el caso real: un "
            "cuarto vacío y un pedido escrito.",
        ])

    # ================================================================== E2 texto, embedder, filtro
    M = D["M"]
    emb = [("hashing", "hashing"), ("bge", "BGE-base"), ("qwen3", "Qwen3")]
    txt = [("seller", "vendedor"), ("description", "descripción")]
    fil = [("none", "sin filtro"), ("type", "tipo grueso"), ("kind", "kind fino")]
    rlab, vals = [], []
    for tk, tl in txt:
        for ek, el in emb:
            rlab.append(f"{tl} · {el}")
            vals.append([M[f"{ek}|{tk}|filtro-{fk}"]["hit@1"] for fk, _ in fil])
    res = ('<div class="legend"><span>hit@1 · texto del producto · embedder × filtro de metadata</span></div>'
           + heatmap(rlab, [x[1] for x in fil], vals, width=980, label_w=330, cell_h=60, vmin=0.05,
                     vmax=0.6, best=(5, 1), groups={0: 1, 3: 1})
           + f'<p class="note">Con el nombre comercial delante de la descripción: <b>{f(D["namedesc"]["hit@1"])}</b> '
             f'(Qwen3, kind), contra {f(D["kind"]["hit@1"])} sin el nombre. IC de la mejor celda: '
             f'{f(ci(b)[0])}–{f(ci(b)[1])}.</p>')
    exp("E2", "Qué guardamos", "¿Qué texto indexamos, <em>con qué embedder y qué filtro?</em>",
        "<p>El catálogo trae el texto del vendedor: el nombre y una frase de marketing. Nuestra "
        "hipótesis: describir cada producto en <strong>las mismas ocho líneas que la consulta</strong> "
        "hace que se encuentren.</p><p>Y queríamos saber cuánto aporta un embedder neuronal frente a "
        "contar palabras, y si filtrar por metadata ayuda.</p>",
        f"<p>Una grilla completa sobre las {D['n_resp']} búsquedas y el catálogo de {D['n_ikea']}:</p>"
        "<ul><li>2 textos: vendedor o descripción</li><li>3 embedders: hashing de palabras, BGE-base, "
        "Qwen3-Embedding-0.6B</li><li>3 filtros: ninguno, tipo grueso (sofá, mesa…) o kind fino "
        "(mesa ratona, mesa auxiliar…)</li></ul>",
        res,
        f"<strong>Descripciones de ocho líneas con Qwen3.</strong> El texto pesa mucho más que el "
        f"embedder: con descripciones, hasta el hashing llega a {f(D['desc_hash']['hit@1'])} sin filtro. "
        f"Los tres filtros quedan dentro del intervalo; el flujo usa el kind, que decide el plan.",
        t=70, notes=[
            "Ya en texto: ¿qué texto ponemos de cada producto, con qué embedder y con qué filtro?",
            "El catálogo trae el texto del vendedor: el nombre y una frase de marketing. Nuestra "
            "hipótesis era que describir cada producto en las mismas ocho líneas que la consulta iba a "
            "hacer que se encuentren.",
            "[paso] Corrimos la grilla completa: dos textos, tres embedders (desde contar palabras "
            "hasta Qwen3) y tres filtros de metadata.",
            f"[paso] La lectura es por filas. Con el texto del vendedor, nada pasa de "
            f"{f(max(max(v) for v in vals[:3]))}. Con nuestras descripciones, todo salta a más de 0,47. "
            f"El embedder suma menos: Qwen3 es el mejor, pero el hashing queda cerca. Y poner el nombre "
            f"comercial adelante empeora: agrega palabras que la consulta no tiene.",
            f"[paso] Decidimos descripciones con Qwen3. Los filtros, con descripciones, casi no cambian "
            f"nada, porque la línea Type ya dice qué es cada cosa. El flujo filtra por el kind que "
            f"decide el plan; type, kind o ninguno quedan dentro del intervalo.",
        ])

    # ================================================================== E3 splitting
    rows = [dict(label="un documento por producto", value=b["hit@1"], ci=ci(b), kind="main"),
            dict(label="línea contra línea, mismo rótulo", value=D["chunks_al"]["hit@1"],
                 ci=ci(D["chunks_al"]), kind="alt", sub="Colors con Colors…, promedio"),
            dict(label="cada línea, un chunk", value=D["chunks_max"]["hit@1"], ci=ci(D["chunks_max"]),
                 kind="alt", sub="el producto puntúa con su mejor línea")]
    res = ('<div class="legend"><span>hit@1 con IC 95% · Qwen3, filtro por tipo</span></div>'
           + hbars(rows, width=980, label_w=380, row_h=110, bar_h=30, x_max=0.8, ticks=[0, .2, .4, .6, .8],
                   tick_fmt=lambda t: f(t, 1), refs=[(D["azar_h1"], "azar")]))
    exp("E3", "Qué guardamos", "¿Partimos cada descripción <em>en chunks?</em>",
        "<p>La receta de RAG dice partir los documentos en pedazos. Pero nuestra descripción ya es "
        "corta: ocho líneas.</p><p>¿Conviene igual comparar por partes, por ejemplo los colores con "
        "los colores?</p>",
        "<p>Tres formas de partir, con todo lo demás igual:</p><ul><li>un documento por producto;</li>"
        "<li>cada línea un chunk, y el producto puntúa con su mejor línea;</li><li>línea contra línea "
        "del mismo rótulo, promediando.</li></ul>",
        res,
        f"<strong>Un producto, un documento.</strong> Partir por líneas pierde el contexto "
        f"({f(D['chunks_max']['hit@1'])}); alinear por rótulo casi empata ({f(D['chunks_al']['hit@1'])}) "
        f"con ocho vectores por producto en lugar de uno.",
        t=35, notes=[
            "Splitting. La receta de RAG dice partir los documentos en chunks, pero nuestra "
            "descripción ya es corta. ¿Conviene igual comparar por partes?",
            "[paso] Probamos tres formas: el documento entero, cada línea como chunk, y línea contra "
            "línea del mismo rótulo, colores con colores.",
            f"[paso] Partir en líneas sueltas se cae a {f(D['chunks_max']['hit@1'])}: una línea sola "
            f"no dice de qué producto habla. Alinear por rótulo casi empata.",
            "[paso] Nos quedamos con un documento por producto: igual de bueno y ocho veces más simple.",
        ])

    # ================================================================== E4 dimensión
    dims = sorted(D["dims"])
    h1 = [D["dims"][d]["hit@1"] for d in dims]
    h10 = [D["dims"][d]["hit@10"] for d in dims]
    cis = [tuple(D["dims"][d]["hit@1_ic95"]) for d in dims]
    res = ('<div class="legend"><span><i style="background:#B0502A"></i>hit@1, con IC 95%</span>'
           '<span><i style="background:#7E858C"></i>hit@10</span></div>'
           + line_chart([dict(name="hit@1", ys=h1, color=COL["main"], ci=cis),
                         dict(name="hit@10", ys=h10, color=COL["alt"], dash=True)],
                        dims, width=960, height=470, ymin=0.3, ymax=1.0, yticks=[.3, .5, .7, .9],
                        xlab="dimensiones del vector (truncado y renormalizado)", right=120))
    exp("E4", "Qué guardamos", "¿Cuántas dimensiones <em>necesita el embedding?</em>",
        "<p>Qwen3-Embedding se entrenó con <strong>Matryoshka</strong>: las primeras componentes del "
        "vector ya forman un embedding válido.</p><p>Menos dimensiones es un índice más chico y "
        "búsquedas más rápidas. ¿Cuánto se pierde?</p>",
        f"<p>Truncamos los vectores a {', '.join(str(d) for d in dims[:-1])} y {dims[-1]} componentes "
        f"y los renormalizamos, sin reentrenar nada. Todo lo demás, igual.</p>",
        res,
        f"<strong>{dims[-1]} dimensiones.</strong> Desde 512 la curva está plana y dentro del "
        f"intervalo, pero el catálogo entero ocupa {f(D['indice_mb'], 1)} MB: a esta escala no hay "
        f"nada que ahorrar. Con millones de productos, 256 o 512.",
        t=40, notes=[
            "Dimensión del embedding. Qwen3 se entrenó con Matryoshka: las primeras componentes del "
            "vector ya son un embedding válido, y uno más chico es más barato de guardar y de buscar.",
            "[paso] Truncamos a 32, 64, hasta 1024, y renormalizamos. Sin reentrenar.",
            f"[paso] Con 32 componentes ya da {f(h1[0])}; desde 512 la curva se aplana "
            f"({f(D['dims'][512]['hit@1'])} contra {f(h1[-1])}).",
            f"[paso] Nos quedamos con las {dims[-1]}: todo el catálogo ocupa {f(D['indice_mb'], 1)} "
            f"megas. Con un catálogo de millones, elegiríamos 256 o 512.",
        ])

    # ================================================================== E5 base vectorial
    tot = D["chroma_total_type"]
    res = ('<div class="bign">'
           f'<div><div class="big t">{D["chroma_igual_type"]}<span class="of"> / {tot}</span></div>'
           '<div class="kl">búsquedas con el <strong>ranking completo idéntico</strong>, filtro por tipo</div></div>'
           f'<div><div class="big t">{D["chroma_igual_kind"]}<span class="of"> / {D["chroma_total_kind"]}</span></div>'
           '<div class="kl">ídem, con filtro por kind</div></div>'
           f'<div><div class="big">{f(D["exact"]["hit@1"])} = {f(b["hit@1"])}</div>'
           '<div class="kl">hit@1 exacta = hit@1 ChromaDB</div></div></div>')
    hn = D["hnsw"]
    exp("E5", "Qué guardamos", "¿La base vectorial <em>se pierde resultados?</em>",
        "<p>ChromaDB usa <strong>HNSW</strong>, una búsqueda aproximada: recorre un grafo de vecinos en "
        "lugar de comparar contra todos los vectores.</p><p>Es la pieza estándar de un RAG, pero "
        "«aproximada» puede querer decir que se le escapa el correcto.</p>",
        f"<p>Las {tot} búsquedas dos veces: con HNSW (coseno, ef_search {hn.get('ef_search', '—')}, "
        f"{hn.get('max_neighbors', '—')} vecinos por nodo) y con búsqueda exacta en numpy. Comparamos el "
        f"ranking completo, búsqueda por búsqueda.</p>",
        res,
        "<strong>ChromaDB.</strong> A esta escala la búsqueda aproximada es exacta, y suma filtros de "
        "metadata, persistencia y la descripción guardada al lado del vector.",
        t=30, notes=[
            "La base vectorial. ChromaDB usa HNSW, una búsqueda aproximada sobre un grafo de vecinos. "
            "¿Se le escapa el correcto?",
            "[paso] Corrimos todas las búsquedas con HNSW y con búsqueda exacta, y comparamos el "
            "ranking entero.",
            f"[paso] Idénticos en las {tot}. Con este tamaño de catálogo, aproximado es exacto.",
            "[paso] Nos quedamos con Chroma por todo lo demás que trae: filtros, persistencia, el "
            "texto al lado del vector.",
        ])

    divider(3, ["Segundo capítulo: lo que pasa en cada pedido, antes y después de buscar."])

    # ================================================================== E6 query rewriting
    rows = [dict(label="las ocho líneas", value=b["hit@1"], ci=ci(b), kind="main", sub="lo que escribe plan"),
            dict(label="solo la línea Type", value=D["q_type"]["hit@1"], ci=ci(D["q_type"]), kind="alt",
                 sub="«rug, high pile shag»"),
            dict(label="solo el nombre del kind", value=D["q_kind"]["hit@1"], ci=ci(D["q_kind"]),
                 kind="muted", sub="«rug»: sin reescribir")]
    res = ('<div class="legend"><span>hit@1 con IC 95% · misma búsqueda, tres consultas</span></div>'
           + hbars(rows, width=980, label_w=340, row_h=110, bar_h=30, x_max=0.8, ticks=[0, .2, .4, .6, .8],
                   tick_fmt=lambda t: f(t, 1), refs=[(D["azar_h1"], "azar")]))
    exp("E6", "Cómo buscamos", "¿Hace falta que el LLM <em>reescriba la consulta?</em>",
        "<p>Plan podría buscar «alfombra» y listo. En cambio escribe el producto ideal en ocho líneas, "
        "como un documento hipotético del catálogo: la idea de HyDE.</p><p>Es una llamada a Opus en "
        "cada pedido. ¿Se paga?</p>",
        "<p>La misma búsqueda con tres consultas:</p><ul><li>las ocho líneas completas;</li><li>solo "
        "la línea Type, una frase corta;</li><li>solo el nombre del kind, sin reescribir nada.</li></ul>",
        res,
        f"<strong>Reescribir, y en las ocho líneas.</strong> Es la decisión que más pesa en todo el "
        f"retrieval: de {f(D['q_kind']['hit@1'])} a {f(b['hit@1'])}.",
        t=45, notes=[
            "Query rewriting. Plan podría buscar la palabra «alfombra» y listo. En cambio escribe el "
            "producto ideal en las ocho líneas, como un documento hipotético del catálogo, que es la "
            "idea de HyDE. Cuesta una llamada a Opus por pedido: ¿vale la pena?",
            "[paso] Misma búsqueda con tres consultas: las ocho líneas, solo la línea Type, o solo el "
            "nombre del kind.",
            f"[paso] Con el nombre solo, {f(D['q_kind']['hit@1'])}, apenas arriba del azar. Con la "
            f"línea Type, {f(D['q_type']['hit@1'])}. Con las ocho líneas, {f(b['hit@1'])}.",
            "[paso] Es la decisión que más pesa de todo el retrieval. Los colores, la forma y el "
            "estilo son lo que distingue una alfombra de otras ochenta.",
        ])

    # ================================================================== E7 reranking
    o = D["opus"]
    rows = [dict(label="sin reranking", value=b["hit@1"], ci=ci(b), kind="alt",
                 sub=f"Qwen3 · MRR@10 {f(b['mrr@10'])}"),
            dict(label="cross-encoder de texto", value=D["minilm"]["hit@1"], ci=ci(D["minilm"]),
                 kind="muted", sub=f"MiniLM, local · MRR@10 {f(D['minilm']['mrr@10'])}"),
            dict(label="Opus mirando las fotos", value=o["hit@1"], ci=ci(o), kind="main",
                 sub=f"{usd(D['rerank_costo_llamada'])} por búsqueda · MRR@10 {f(o['mrr@10'])}")]
    res = ('<div class="legend"><span>hit@1 con IC 95% · reordenando el top-10 de Qwen3</span></div>'
           + hbars(rows, width=980, label_w=360, row_h=110, bar_h=30, x_max=0.8, ticks=[0, .2, .4, .6, .8],
                   tick_fmt=lambda t: f(t, 1)))
    exp("E7", "Cómo buscamos", "¿Conviene reordenar los candidatos <em>mirando las fotos?</em>",
        "<p>El embedding compara textos. Pero dos alfombras crema de pelo largo se describen casi igual "
        "y se distinguen a la vista.</p><p>La idea: que un modelo que ve reordene los primeros diez.</p>",
        "<p>Dos rerankers sobre el top-10:</p><ul><li>un <strong>cross-encoder de texto</strong> "
        "(MiniLM de MS MARCO, gratis) que lee consulta y descripción juntas;</li><li><strong>Claude "
        "Opus 5.5</strong> mirando la foto del ambiente y las de los candidatos.</li></ul>",
        res,
        None,
        t=55, notes=[
            "Reranking. El embedding compara textos, pero dos alfombras crema de pelo largo se "
            "describen casi igual y se distinguen mirando. La idea es que un modelo que ve reordene "
            "los primeros diez.",
            "[paso] Probamos dos: un cross-encoder de texto, gratis, que lee consulta y descripción "
            f"juntas; y Opus mirando las fotos, a unos {usd(D['rerank_costo_llamada'])} por búsqueda.",
            f"[paso] El cross-encoder empeora: {f(D['minilm']['hit@1'])}. Está entrenado en búsqueda "
            f"web y no aporta nada que el embedding no tenga. Opus sube de {f(b['hit@1'])} a "
            f"{f(o['hit@1'])}, con intervalos que no se tocan: es la mejora más grande después del "
            f"query rewriting.",
        ])

    # ---------- E7: dónde ayuda
    opc = D["opus"].get("hit@1_por_categoria", {})
    drows = [dict(label=CAT_ES.get(c, c), a=b["hit@1_por_categoria"][c], b=opc.get(c, float("nan")),
                  n=D["cats_n"][c]) for c in D["cats"] if c in opc]
    drows.sort(key=lambda r: r["a"])
    ej, er = D["ej"], D["ej_rr"]
    rel = set(ej["relevant"])
    s1 = "".join(ficha(D, p, size=118, cap=False, rank=i + 1, hi=p in rel) for i, p in enumerate(ej["ranked"][:5]))
    s2 = "".join(ficha(D, p, size=118, cap=False, rank=i + 1, hi=p in rel) for i, p in enumerate(er["ranked"][:5]))
    body = hdx("E7", "Cómo buscamos", "Dónde ayuda <em>mirar las fotos</em>")
    body += (
        '<div class="e7b"><div><div class="legend"><span><i style="background:#fff;border:3px solid #7E858C;box-sizing:border-box"></i>Qwen3</span>'
        '<span><i style="background:#B0502A"></i>+ Opus</span><span>hit@1 por categoría (consultas)</span></div>'
        + dumbbell(drows, width=900, label_w=230, row_h=62)
        + '</div><div class="e7r">'
        '<div class="lbl">La alfombra de las métricas</div>'
        f'<p class="cap">Qwen3: el anotado queda {ej["rank"]}.º</p><div class="strip">{s1}</div>'
        f'<p class="cap" style="margin-top:22px">Después de Opus: {er["rank"]}.º</p><div class="strip">{s2}</div>'
        f'<p class="note">Con el catálogo chico de {D["n_268"]} productos, solo muebles, el salto era de '
        f'{f(D["base268"]["hit@1"])} a {f(D["opus268"]["hit@1"])}.</p>'
        '</div></div>'
        f'<div class="dec" data-step="1"><div class="k">Decisión</div><p><strong>Reordenar con un modelo que ve.</strong> '
        f'Opus sube hit@1 de {f(b["hit@1"])} a {f(o["hit@1"])}, sobre todo donde los productos se parecen; el '
        f'cross-encoder de texto empeora. En el flujo, ese reranker es el paso choose.</p></div>')
    rug = next((r for r in drows if r["label"] == "alfombras"), drows[0])
    add(body, sec="Cómo buscamos", title="E7 · Dónde ayuda", t=45, phases="2,3", notes=[
        f"Dónde ayuda. Por categoría, el salto es mayor donde los productos se parecen entre sí: "
        f"alfombras, de {f(rug['a'], 2)} a {f(rug['b'], 2)}, estantes, deco, lámparas. Donde el "
        f"texto ya alcanzaba, como sillas, sube menos.",
        f"A la derecha, la búsqueda de la alfombra que usamos para explicar las métricas: Qwen3 la "
        f"dejó {ej['rank']}.ª; Opus, mirando, la sube a la {er['rank']}.ª.",
        "[paso] Decisión: reordenar con un modelo que ve. En el flujo, ese reranker es el paso choose: "
        "el mismo Opus, que además elige la combinación entera.",
    ])

    # ================================================================== E8 cuántos candidatos
    cv = D["curva"]["por_k"]
    ks = sorted(int(k) for k in cv)
    ac = [cv[str(k)]["acierto_eleccion"] for k in ks]
    te = [cv[str(k)]["techo_hit@k"] for k in ks]
    cis = [tuple(cv[str(k)]["ic95"]) for k in ks]
    kf, ka = D["k_flujo"], D["k_antes"]
    d35 = cv[str(kf)]["acierto_eleccion"] - cv[str(ka)]["acierto_eleccion"]
    d58 = cv["8"]["acierto_eleccion"] - cv[str(kf)]["acierto_eleccion"]
    res = ('<div class="legend"><span><i style="background:#B0502A"></i>acierto de la elección, IC 95%</span>'
           '<span><i style="background:#7E858C"></i>techo: el anotado está entre los k</span></div>'
           + line_chart([dict(name="acierto", ys=ac, color=COL["main"], ci=cis),
                         dict(name="techo", ys=te, color=COL["alt"], dash=True)],
                        ks, width=960, height=480, ymin=0.4, ymax=1.0, yticks=[.4, .6, .8, 1.0],
                        marks=[(ka, "antes"), (kf, "el flujo")], xlab="k: candidatos por pieza",
                        right=120))
    exp("E8", "Cómo buscamos", "¿Cuántos candidatos le mostramos <em>a choose?</em>",
        "<p>Choose mira k fotos por pieza. Con más candidatos es más probable que el correcto esté…</p>"
        "<p>…pero son más imágenes por llamada: más costo, más latencia y más opciones para "
        "confundirse.</p>",
        "<p>Sin gastar de nuevo: del reranking de Opus sobre el top-10 sale qué elegiría entre los "
        "primeros k, para k de 1 a 10.</p><p>Lo comparamos con el <strong>techo</strong>, hit@k: que el "
        "anotado esté entre los k.</p>",
        res,
        f"<strong>k = {kf}</strong> (antes, {ka}). De {ka} a {kf} suma {f(d35)} de acierto; de {kf} a 8, "
        f"{f(d58)}, con un {pct(8 / kf - 1)} más de fotos en cada llamada.",
        t=45, notes=[
            "¿Cuántos candidatos le mostramos a choose? Más candidatos, más chance de que esté el "
            "correcto, pero más fotos por llamada: más costo, más latencia y más con qué confundirse.",
            "[paso] No hizo falta gastar de nuevo: del reranking de Opus sobre el top-10 sale qué "
            "elegiría entre los primeros k. Lo comparamos con el techo, que el correcto esté entre los k.",
            f"[paso] El techo sube rápido, pero el acierto real se aplana: de {ka} a {kf} candidatos "
            f"suma {f(d35)}; de {kf} a 8, {f(d58)}.",
            f"[paso] Pasamos de {ka} a {kf}. Más allá, el costo crece más que el acierto.",
        ])

    divider(4, ["Tercer capítulo: cuánto creerle a todo esto."])

    # ================================================================== E9 reproducibilidad
    rp = D["repro"]
    rrows = [dict(label=r["label"], h=r["h"], mean=r["mean"], sd=r["sd"]) for r in rp if r["mean"] > 0.3]
    nv = next(r for r in rp if r["mean"] <= 0.3)
    res = ('<div class="legend"><span>hit@1 en cada una de las tres escrituras · media ± desvío</span></div>'
           + dots_repro(rrows, width=980, label_w=330, row_h=96, xmin=0.44, xmax=0.60,
                        ticks=[.44, .48, .52, .56, .60], tick_d=2, right=190)
           + f'<p class="note">Fuera de escala: {esc(nv["label"])}, {f(nv["mean"])} ± {f(nv["sd"])}. '
             f'Búsquedas con respuesta en cada escritura: {", ".join(str(n) for n in D["repro_n"])}.</p>')
    q = rp[0]
    exp("E9", "Cuánto creerle", "Si otro escribe las consultas, <em>¿cambia el resultado?</em>",
        "<p>Las consultas de la evaluación las escribieron subagentes de Claude. Otro redactor "
        "escribiría otras.</p><p>Si el orden de los métodos depende de una redacción en particular, "
        "las conclusiones no valen.</p>",
        f"<p>Tres escrituras independientes de todas las consultas, con el mismo prompt y las mismas "
        f"fotos, sobre el catálogo de {D['repro_catalogo']} productos.</p><p>Cinco métodos, cada uno "
        f"en las tres.</p>",
        res,
        f"<strong>Las conclusiones se sostienen.</strong> El mejor método da {f(q['mean'])} ± "
        f"{f(q['sd'])} y le gana a BGE, a hashing y al filtro por kind en las tres. Diferencias de "
        f"menos de ~{f(q['sd'], 2)} entre métodos las tratamos como empate.",
        t=45, notes=[
            "Reproducibilidad. Las consultas las escribieron subagentes de Claude; otro redactor "
            "escribiría otras. Si el ranking de métodos depende de una redacción, no vale.",
            f"[paso] Hicimos escribir todas las consultas tres veces, de forma independiente, y "
            f"corrimos cinco métodos en cada escritura.",
            f"[paso] El mejor método da {f(q['mean'])} más menos {f(q['sd'])}. El orden se mantiene en "
            f"las tres: Qwen3 con filtro por tipo arriba, el texto del vendedor abajo de todo.",
            f"[paso] Conclusión: el orden es firme, pero diferencias de dos o tres centésimas entre "
            f"métodos son ruido de redacción. Por eso varias «mejoras» las tratamos como empate.",
        ])

    # ================================================================== E10 relevancia graduada
    g = D["grad"]["consultas"]
    ag = D["grad"]["acuerdo_con_gt"]
    sin = 1 - D["n_resp"] / D["n_busquedas"]
    rows = [dict(label="hit@1 exacto", value=D["h1_855"], kind="ink", sub="el SKU anotado, primero"),
            dict(label="útil@1, todas", value=g["todas"]["util1"], ci=tuple(g["todas"]["util1_ic95"]),
                 kind="main", sub="el primero tiene nota ≥ 1"),
            dict(label="útil@3, todas", value=g["todas"]["util3"], ci=tuple(g["todas"]["util3_ic95"]),
                 kind="main", sub="alguno de los tres tiene nota ≥ 1"),
            dict(label="útil@1, sin el exacto", value=g["sin anotado"]["util1"],
                 ci=tuple(g["sin anotado"]["util1_ic95"]), kind="alt",
                 sub="el producto no está en el catálogo"),
            dict(label="útil@3, sin el exacto", value=g["sin anotado"]["util3"],
                 ci=tuple(g["sin anotado"]["util3_ic95"]), kind="alt")]
    res = ('<div class="legend"><span>proporción de búsquedas, IC 95% · catálogo de '
           f'{D["grad_catalogo"]}</span></div>'
           + hbars(rows, width=980, label_w=330, row_h=74, x_max=1.0)
           + f'<p class="note"><b>¿Se le puede creer al juez?</b> Le pone 2 al producto anotado en el '
             f'{pct(ag["anotado_con_2"])} de los casos, y a los demás en el {pct(ag["otros_con_2"])}. '
             f'NDCG@3 graduado: {f(g["todas"]["ndcg3"])}.</p>')
    exp("E10", "Cuánto creerle", "¿Sirve lo que trae, <em>aunque no sea el producto exacto?</em>",
        f"<p>hit@k solo cuenta el SKU anotado. Si el sofá correcto no está, uno muy parecido igual "
        f"sirve.</p><p>Y el {pct(sin)} de las búsquedas no tiene su producto en el catálogo: hit@k "
        f"no las puede medir.</p>",
        f"<p>Un juez LLM mira la foto del ambiente y los tres primeros candidatos, sin saber cuál es el "
        f"anotado, y pone <strong>2</strong> (el mismo o indistinguible), <strong>1</strong> (alternativa "
        f"aceptable) o <strong>0</strong>.</p><p>{g['todas']['n']} búsquedas al azar: "
        f"{g['con anotado']['n']} con el producto en el catálogo y {g['sin anotado']['n']} sin.</p>",
        res,
        f"<strong>hit@1 subestima lo útil.</strong> El primero sirve en el {pct(g['todas']['util1'])} "
        f"de los casos, y en el {pct(g['sin anotado']['util1'])} cuando el exacto no existe. El juez "
        f"complementa a hit@k; no lo reemplaza.",
        t=45, notes=[
            "Relevancia graduada. hit@k solo cuenta el producto exacto; si el sofá anotado no está, "
            f"uno muy parecido le sirve igual al usuario. Y más de un tercio de las búsquedas no tiene "
            f"su producto en el catálogo.",
            "[paso] Un juez LLM mira la foto del ambiente y los tres primeros, sin saber cuál es el "
            "anotado, y les pone 2, 1 o 0. Esto es el context precision de RAGAS en su versión sin "
            "ground truth, y el NDCG graduado de la clase.",
            f"[paso] El primero sirve en el {pct(g['todas']['util1'])} de los casos, contra un hit@1 "
            f"exacto de {f(D['h1_855'], 2)}. Y sin el producto en el catálogo, igual en el "
            f"{pct(g['sin anotado']['util1'])}. Validamos al juez: le pone 2 al anotado en el "
            f"{pct(ag['anotado_con_2'])} y a los demás en el {pct(ag['otros_con_2'])}.",
            "[paso] hit@1 es una cota inferior de lo útil. Usamos el juez como complemento, validado "
            "contra las anotaciones.",
        ])

    # ================================================================== E11 RAGAS
    trs = ""
    for r in D["ragas"]:
        fa = r["fidelidad"]
        rl = r["relevancia"]
        trs += (
            f'<div class="rg-l">{esc(r["label"])}</div>'
            f'<div class="rg-b"><div class="rbar"><i style="width:{fa["faithfulness"] * 100:.1f}%"></i></div>'
            f'<span class="rv">{f(fa["faithfulness"], 2)}</span><span class="rn">{fa["afirmaciones"]} afirm.</span></div>'
            f'<div class="rg-b"><div class="rbar two"><i class="vara" style="left:{rl["vara_contrastes"] * 100:.1f}%"></i>'
            f'<i style="width:{rl["answer_relevance"] * 100:.1f}%"></i></div>'
            f'<span class="rv">{f(rl["answer_relevance"], 2)}</span><span class="rn">vara {f(rl["vara_contrastes"], 2)}</span></div>')
    bad = D["ragas"][0]["fidelidad"]["no_sostenidas"]
    res = ('<div class="rg"><div class="rg-h"></div><div class="rg-h">faithfulness</div>'
           '<div class="rg-h">answer relevance</div>'
           f'{trs}</div><p class="note">La raya negra es la vara: el mismo coseno contra pedidos sin relación.</p>'
           '<div class="rq"><div class="lbl">Lo que no se sostiene (vista 1)</div>'
           + "".join(f"<p>«{esc(x)}»</p>" for x in bad) + "</div>")
    exp("E11", "Cuánto creerle", "¿La respuesta inventa, <em>o responde lo que se pidió?</em>",
        "<p>Choose explica cada elección. Una explicación que afirma algo falso, una medida o un "
        "material, es una alucinación que el usuario va a creer.</p><p>Y la lista entera tiene que "
        "contestar el pedido, no solo cada pieza.</p>",
        "<p>Dos métricas de RAGAS, con un juez LLM, sobre cuatro respuestas del flujo:</p><ul>"
        "<li><strong>Faithfulness:</strong> la explicación partida en afirmaciones; qué fracción se "
        "sostiene con lo que vio el sistema.</li><li><strong>Answer relevance:</strong> el juez, sin ver "
        "el pedido, escribe tres pedidos que esa respuesta contesta; coseno medio con el original.</li></ul>",
        res,
        "<strong>El porqué es fiel; lo que falla son medidas.</strong> Lo no sostenido son tamaños que "
        "el catálogo no tiene: los asientos de IKEA no traen medidas. Eso nos llevó a buscar un "
        "catálogo que sí las tenga.",
        t=55, notes=[
            "RAGAS sobre la respuesta. Choose explica cada elección; si afirma una medida o un material "
            "falso, es una alucinación que el usuario se va a creer.",
            "[paso] Medimos dos cosas con un juez. Faithfulness: se parte la explicación en "
            "afirmaciones y se cuenta qué fracción se sostiene con lo que vio el sistema. Answer "
            "relevance: el juez, sin ver el pedido, escribe tres pedidos que esa respuesta "
            "contestaría, y medimos el coseno con el original. La vara es el mismo coseno contra "
            "pedidos que no tienen nada que ver.",
            f"[paso] Faithfulness entre {f(min(r['fidelidad']['faithfulness'] for r in D['ragas']), 2)} "
            f"y {f(max(r['fidelidad']['faithfulness'] for r in D['ragas']), 2)}; answer relevance muy por "
            f"encima de la vara. Lo interesante es qué no se sostiene: que el piso es de roble, que la "
            f"alfombra llega abajo del sofá. Son medidas y cosas que el catálogo no dice.",
            "[paso] El modelo no inventa productos; lo que le falta es información. Los asientos de "
            "IKEA no tienen medidas en el dataset, y eso nos llevó al último capítulo: otro catálogo.",
        ])

    divider(5, ["Último capítulo de experimentos: de punta a punta, en ambientes vacíos reales."])

    # ================================================================== E12 qué catálogo
    jg = D["j_grupos"]
    j11 = D["j_todos11"]
    body = hdx("E12", "De punta a punta", "¿Alcanza con IKEA, <em>o hace falta otro catálogo?</em>")
    order = ["caballito-living", "caballito-comedor", "alvear-escritorio", "alvear-living-comedor",
             "experimento-lectura"]
    body += (
        '<div class="e12a"><div class="xl">'
        + blk("Por qué",
              f"<p>El catálogo de IKEA del dataset es de un solo estilo, y sus asientos "
              f"<strong>no tienen medidas</strong> ({pct(D['ikea_asientos_sin_medidas'])} de sofás, "
              f"sillones y sillas sin medidas). E11 mostró que lo que falla son justamente medidas.</p>"
              f"<p><strong>Amazon Berkeley Objects</strong> son publicaciones reales de Amazon, de "
              f"muchos estilos, el {pct(D['abo_con_medidas'])} con medidas. Describimos {D['n_abo']} "
              f"productos con las mismas ocho líneas.</p>")
        + '<div class="cmp"><div></div><div class="ch">IKEA</div><div class="ch">ABO</div>'
        f'<div class="cl2">productos</div><div class="cv">{D["n_ikea"]}</div><div class="cv">{D["n_abo"]}</div>'
        f'<div class="cl2">asientos con medidas</div><div class="cv">{pct(1 - D["ikea_asientos_sin_medidas"])}</div><div class="cv">{pct(D["abo_con_medidas"])}*</div>'
        f'<div class="cl2">ground truth</div><div class="cv">sí</div><div class="cv">no</div></div>'
        '<p class="cap">* sobre todos los productos de ABO descriptos</p>'
        '</div><div class="xl" data-step="1">'
        + blk("Qué hicimos",
              f"<p>{j11['ambientes']} ambientes vacíos reales: {jg['propios']['n']} de departamentos "
              f"propios, con pedidos nórdicos, y {jg['publicos']['n']} fotos públicas con pedidos de "
              f"otros estilos. El flujo completo con cada catálogo, y un juez que compara las dos listas:</p>")
        + '<div class="judge"><div class="jrow"><span class="jo">orden 1</span><span class="jb">A · IKEA</span>'
        '<span class="jb t">B · IKEA + ABO</span><span class="jv">→ voto</span></div>'
        '<div class="jrow"><span class="jo">orden 2</span><span class="jb t">A · IKEA + ABO</span>'
        '<span class="jb">B · IKEA</span><span class="jv">→ voto</span></div>'
        '<p>Opus ve la foto, el pedido y las fotos de las dos listas. <strong>Una lista gana solo si '
        'gana en los dos órdenes</strong>; si no, empate.</p></div>'
        '<dl class="defs"><dt>sesgo de posición</dt><dd>fracción de votos para la lista que va primera; 0,5 es sin sesgo</dd>'
        '<dt>acuerdo entre órdenes</dt><dd>fracción de ambientes donde los dos votos coinciden</dd>'
        '<dt>cumple</dt><dd>fracción de productos con nota 2 del juez: lo pedido, y va con el cuarto</dd></dl>'
        '</div></div>')
    add(body, sec="De punta a punta", title="E12 · Qué catálogo (diseño)", t=55, phases="0,1", notes=[
        f"¿Alcanza con IKEA? El catálogo del dataset es de un solo estilo, y sus asientos no tienen "
        f"medidas: ninguno. E11 nos mostró que lo que falla son justamente medidas. Amazon Berkeley "
        f"Objects son publicaciones reales de Amazon, de muchos estilos y casi todas con medidas. "
        f"Describimos {D['n_abo']} productos con las mismas ocho líneas.",
        f"[paso] Acá no hay ground truth, así que lo medimos de punta a punta: {j11['ambientes']} "
        f"ambientes vacíos reales, cinco nuestros con pedidos nórdicos y seis fotos públicas con "
        f"pedidos de otros estilos. Corremos el flujo con cada catálogo y un juez compara las dos "
        f"listas. Como los LLM tienden a preferir la primera opción, se pregunta en los dos órdenes, y "
        f"una lista gana solo si gana en los dos. Medimos también el sesgo de posición y el acuerdo "
        f"entre órdenes.",
    ])

    # ---------- E12 resultados
    det = {x["slug"]: x for x in j11["detalle"]}
    slugs = order + [s for s in det if s.startswith("publica")]
    labels = {"caballito-living": "living", "caballito-comedor": "comedor", "alvear-escritorio": "escritorio",
              "alvear-living-comedor": "living comedor", "experimento-lectura": "lectura",
              "publica-loft-industrial": "loft industrial", "publica-living-clasico": "clásico",
              "publica-comedor-clasico-moderno": "comedor clásico", "publica-living-japandi": "japandi",
              "publica-living-bohemio": "bohemio", "publica-estudio-sobrio": "estudio sobrio"}
    cells = ""
    for s in slugs:
        x = det[s]
        ph = D["pedidos"][s]["foto"]
        votes = "".join(f'<i class="{"vt2" if v == "todos" else "vi" if v == "ikea" else "vtie"}"></i>'
                        for v in x["votos"])
        w = {"todos": "IKEA+ABO", "ikea": "IKEA", "tie": "empate"}[x["ganador"]]
        cells += (f'<div class="jr"><div class="th"><img src="{img_uri(ph, 260, 195, q=70)}" alt=""></div>'
                  f'<div class="v">{votes}</div><div class="w{" t" if x["ganador"] == "todos" else ""}">{w}</div>'
                  f'<div class="nm">{labels.get(s, s)}</div></div>')
    pub_credit = "; ".join(
        f"{labels[s]}: {D['publicas'][D['pedidos'][s]['foto'].split('/')[-1]]['autor']}, "
        f"{D['publicas'][D['pedidos'][s]['foto'].split('/')[-1]]['licencia']}"
        for s in slugs if s.startswith("publica"))
    P, U = jg["propios"], jg["publicos"]
    ja = D["j_abo5"]["resumen"]
    body = hdx("E12", "De punta a punta", "IKEA contra IKEA + ABO, <em>en once cuartos reales</em>")
    body += (
        '<div class="e12b">'
        '<div class="legend"><span><i class="vi" style="display:inline-block"></i>votó IKEA</span>'
        '<span><i class="vt2" style="display:inline-block"></i>votó IKEA + ABO</span>'
        '<span>un punto por orden · los cinco primeros son departamentos propios; los seis siguientes, fotos públicas</span></div>'
        f'<div class="jg">{cells}</div>'
        f'<p class="credit">Fotos públicas (Wikimedia Commons / Flickr): {esc(pub_credit)}.</p>'
        '<div class="e12g">'
        f'<div class="card"><h3>Departamentos propios · pedidos nórdicos</h3><p class="sc">IKEA {P["gana_ikea"]} · '
        f'empate {P["empates"]} · IKEA+ABO {P["gana_todos"]}</p><p>cumple: {f(P["util_ikea"])} contra {f(P["util_todos"])}</p></div>'
        f'<div class="card hi"><h3>Fotos públicas · otros estilos</h3><p class="sc">IKEA+ABO {U["gana_todos"]} · '
        f'IKEA {U["gana_ikea"]}</p><p>cumple: de {f(U["util_ikea"])} a <strong>{f(U["util_todos"])}</strong></p></div>'
        f'<div class="card"><h3>Y además</h3><p>ABO solo contra IKEA, en los 5 propios: IKEA {ja["ikea"]["gana"]}, ABO {ja["abo"]["gana"]}.</p>'
        f'<p>Con ABO como distractor, hit@1 sobre el ground truth de IKEA: {f(b["hit@1"])} → {f(D["todos_ret"]["hit@1"])}.</p>'
        f'<p>Acuerdo entre órdenes {f(j11["acuerdo_entre_ordenes"], 2)} · votos a la posición A {f(j11["votos_por_posicion_A"], 2)}.</p></div>'
        '</div></div>'
        f'<div class="dec" data-step="1"><div class="k">Decisión</div><p><strong>IKEA + ABO en el flujo.</strong> '
        f'Empata en los pedidos nórdicos, gana {U["gana_todos"]} a {U["gana_ikea"]} en los demás estilos y, como '
        f'distractor, casi no mueve el retrieval. Las evaluaciones con ground truth siguen siendo solo IKEA.</p></div>')
    add(body, sec="De punta a punta", title="E12 · Resultados", t=60, phases="2,3", notes=[
        f"Los resultados. Cada columna es un ambiente, con los dos votos del juez. En los cinco "
        f"departamentos propios, con pedidos nórdicos, IKEA solo e IKEA más ABO empatan: "
        f"{P['gana_ikea']} a {P['gana_todos']} con un empate. En las seis fotos públicas, con pedidos "
        f"industrial, clásico, bohemio, gana IKEA más ABO {U['gana_todos']} a {U['gana_ikea']}, y la "
        f"fracción de productos que cumplen sube de {f(U['util_ikea'], 2)} a {f(U['util_todos'], 2)}.",
        f"Además, ABO solo pierde contra IKEA en los cuartos nórdicos, y sumar ABO como distractor casi "
        f"no cambia el retrieval sobre el ground truth de IKEA. El juez coincide consigo mismo en los "
        f"dos órdenes en el {pct(j11['acuerdo_entre_ordenes'])} de los casos.",
        "[paso] Decisión: el flujo usa los dos catálogos. Lo que no cambia: las métricas con ground "
        "truth se siguen calculando solo sobre IKEA.",
    ])

    # ---------- E12 un caso
    lx = det["publica-loft-industrial"]
    lph = D["pedidos"]["publica-loft-industrial"]["foto"]
    lcred = D["publicas"][lph.split("/")[-1]]

    def lista(cat):
        grs = [s["grades"] for s in lx["puntajes"][cat]]
        out = ""
        for i, p in enumerate(lx["listas"][cat]):
            it = D["abo_items"].get(p["id"]) if p["id"].startswith("abo-") else D["items"].get(p["id"])
            kd = (it or {}).get("kind", "")
            out += ficha(D, p["id"], size=104, cap=True, qty=p.get("units"),
                         title=KIND_ES.get(kd, kd or p["type"]),
                         sub="ABO" if p["id"].startswith("abo-") else "IKEA",
                         grade=[gg[i] for gg in grs if i < len(gg)])
        return out

    body = hdx("E12", "De punta a punta", "Un caso: <em>el loft industrial</em>")
    body += (
        '<div class="loft"><div class="lfl">'
        + foto(img_uri(lph, 760, 570, q=72), 470, 352,
               cap=f"Foto: {esc(lcred['autor'])}, {esc(lcred['licencia'])}")
        + f'<p class="quote lq">{esc(D["pedidos"]["publica-loft-industrial"]["pedido"])}</p></div>'
        '<div class="lfr">'
        f'<div class="lbl">IKEA solo</div><div class="strip lst">{lista("ikea")}</div>'
        f'<div class="lbl" style="margin-top:14px">IKEA + ABO · ganó en los dos órdenes</div><div class="strip lst">{lista("todos")}</div>'
        '<div class="glegend"><span><i class="g2"></i>2 cumple</span><span><i class="g1"></i>1 aceptable</span>'
        '<span><i class="g0"></i>0 no sirve</span><span>una barra por orden</span></div>'
        f'<p class="why">«{esc(lx["por_que"][1])}»</p><p class="cap">el porqué del juez, en el orden 2 (A = IKEA + ABO)</p>'
        '</div></div>')
    add(body, sec="De punta a punta", title="E12 · Un caso", t=20, phases="2", notes=[
        "Un caso para ver qué está mirando el juez: un loft con vigas y un pedido industrial, sofá de "
        "cuero envejecido, mesa de madera con patas de metal negro, biblioteca de metal y madera.",
        "IKEA solo no tiene esos productos y propone lo más cercano: un sofá de cuero liso, una mesa "
        "toda de madera, un estante de vidrio. Con ABO aparecen el sofá de cuero coñac, la mesa "
        "industrial y la biblioteca. Las barritas son la nota del juez a cada producto, en cada orden.",
    ])

    # ================================================================== E13 la imagen: métricas
    cm = D["img"]["caballito-living"]["met"]
    prods = [p for p in cm["productos"] if p.get("detectado")]
    pairs = ""
    final_cl = A / "caballito-living" / "final.png"
    for p in [x for x in prods if x["id"] in ("190.114.33", "202.080.42", "602.740.06")]:
        pairs += (f'<div class="pair"><img src="{img_uri(product_photo(D, p["id"]), 180, 180, q=80, fit="contain")}" alt="">'
                  f'<img src="{crop_uri(final_cl, p["box"], 180, 180)}" alt="">'
                  f'<span>{KIND_ES.get(p["kind"], p["kind"])}: {p["puesto"]}.º de {p["entre"]}</span></div>')
    ri = D["ref_ikea"]
    boxes = [p["box"] for p in prods]
    mask = ssim_mask(Path("datos/resultados/amoblar/caballito-living/final.png"), boxes)
    pair, pinfo = sift_pair(Path("datos/resultados/amoblar/caballito-living/room.jpg"),
                            Path("datos/resultados/amoblar/caballito-living/final.png"))
    body = hd("De punta a punta", "Cómo medimos una imagen, <em>sin ground truth</em>")
    body += (
        '<div class="imet">'
        '<div class="card im imr"><div><div class="mn">SSIM fuera de los muebles</div><p>Similitud estructural '
        '(luz, contraste y textura, por ventanas) entre la foto original y la generada, <strong>solo fuera '
        'de las cajas de los muebles</strong>. 1 es idéntico: el cuarto se preservó.</p></div>'
        f'<figure><img src="{img_uri(mask, 680, 510, q=74)}" alt=""><figcaption>lo rayado no cuenta · el living de la portada</figcaption></figure></div>'
        '<div class="card im" data-step="1"><div class="mn">SIFT + RANSAC</div><p>Puntos característicos de la '
        'foto original: ¿cuántos se reencuentran en la generada con una homografía consistente (inliers), '
        'y cuánto se movieron? Si la cámara se movió o el cuarto cambió, caen los inliers y sube el '
        'desplazamiento.</p>'
        f'<div class="sift2"><img class="siftimg" src="{img_uri(pair, 1120, None, q=74)}" alt="">'
        f'<div><span class="cap">la foto original y la imagen aceptada: cada línea es un punto que RANSAC acepta '
        f'({D["img"]["caballito-living"]["met"]["ambiente"]["sift_inliers"]} inliers en la corrida)</span>'
        f'<p class="th">control del flujo: inliers ≥ {D["sift_min_inliers"]} y desplazamiento ≤ {pct(D["sift_max_shift"])} '
        f'del ancho; si no, otra imagen (hasta {D["sift_attempts"]} intentos)</p></div></div></div>'
        '<div class="card im" data-step="2"><div class="mn">Fidelidad de producto</div><p>Grounding DINO detecta cada '
        'mueble; DINOv3 compara el recorte con todas las fotos del catálogo de su tipo. ¿El de la lista '
        f'sale primero? <strong>identificados@1</strong>. Vara: con fotos reales de IKEA da {f(ri["hit@1"])}.</p>'
        f'<div class="pairs">{pairs}</div></div>'
        '<div class="card im" data-step="3"><div class="mn">Pedido ↔ imagen</div><p>SigLIP 2 mide la '
        'alineación entre el texto del pedido y la imagen: cuánto sube respecto de la foto vacía, y en qué '
        'puesto queda el pedido real entre pedidos de contraste.</p>'
        '<p class="note">Todas corren local y gratis: se pueden calcular en cada corrida del flujo.</p></div>'
        '</div>')
    add(body, sec="De punta a punta", title="E13 · Métricas de imagen", t=40, notes=[
        "Para la imagen no hay ground truth, así que armamos métricas que comparan contra lo que sí "
        "tenemos: la foto original y las fotos del catálogo.",
        "**SSIM** fuera de los muebles: la similitud estructural entre la foto original y la generada, "
        "solo donde no hay muebles. Si da cerca de uno, el cuarto se preservó.",
        f"[paso] **SIFT con RANSAC**: buscamos puntos característicos de la foto original en la "
        f"generada. Si la cámara se movió o el cuarto cambió, se reencuentran pocos y se desplazan. "
        f"Con esto armamos el control automático: al menos {D['sift_min_inliers']} inliers y un "
        f"desplazamiento de a lo sumo el {pct(D['sift_max_shift'])} del ancho.",
        f"[paso] **Fidelidad de producto**: detectamos cada mueble, recortamos y vemos si el más "
        f"parecido del catálogo es el de la lista. Como vara, con fotos reales de IKEA esto da "
        f"{f(ri['hit@1'])}: es difícil incluso con fotos de verdad.",
        "[paso] Y SigLIP 2 para ver si la imagen se alinea con el pedido.",
    ])

    # ================================================================== E13 prompt de la escena
    def tile(run, cap):
        m = D["img"][run]["met"]["ambiente"]
        bad = m["sift_desplazamiento_mediano"] > D["sift_max_shift"] or m["sift_inliers"] < D["sift_min_inliers"]
        badge = '<span class="badge no">cambió el cuarto</span>' if bad else ""
        return (f'<figure class="vt3"><div class="vimg"><img src="{img_uri(A / run / "final.png", 600, 450, q=72)}" alt="">{badge}</div>'
                f'<figcaption><b>{cap}</b><span>SSIM {f(m["ssim_fuera_de_los_muebles"], 2)} · SIFT {pct(m["sift_reencontrados"], 1)} · '
                f'despl. {pct(m["sift_desplazamiento_mediano"], 2)}</span></figcaption></figure>')

    orig = img_uri(A / "experimento" / "room.jpg", 600, 450, q=72)
    ex_a, ex_b = D["img"]["experimento"]["choice"]["answer"]["choices"], D["img"]["experimento-buen-pedido"]["choice"]["answer"]["choices"]
    res = (
        '<div class="vgrid">'
        f'<figure class="vt3"><div class="vimg"><img src="{orig}" alt=""></div><figcaption><b>la foto · pedido corto</b>'
        f'<span>{len(ex_a)} productos · foto de un integrante</span></figcaption></figure>'
        + tile("experimento", "(a) el LLM escribe la escena") + tile("experimento-libre", "(b) edición libre")
        + f'<figure class="vt3"><div class="vimg"><img src="{orig}" alt=""></div><figcaption><b>la misma foto · pedido detallado</b>'
        f'<span>{len(ex_b)} productos</span></figcaption></figure>'
        + tile("experimento-buen-pedido", "(c) edición libre") + tile("experimento-buen-pedido-estricto", "(d) edición estricta")
        + '</div>')
    mb, ms = D["img"]["experimento-buen-pedido"]["met"]["ambiente"], D["img"]["experimento-buen-pedido-estricto"]["met"]["ambiente"]
    exp("E13", "De punta a punta", "¿Cómo pedimos la imagen <em>para que no cambie el cuarto?</em>",
        "<p>El modelo de imagen tiende a «mejorar» la foto: mueve la cámara, agranda ventanas, repinta.</p>"
        "<p>Para el usuario es grave: compraría para un cuarto que no es el suyo.</p>",
        "<p>Sobre la misma foto y la misma lista, cambia solo el pedido de edición:</p><ul>"
        "<li>(a) Claude escribe la escena: dónde va cada cosa;</li><li>(b, c) un template de edición "
        "libre, sin LLM;</li><li>(d) edición estricta: «el mismo cuarto, exactamente».</li></ul>"
        "<p>Una imagen por variante.</p>",
        res,
        f"<strong>Edición estricta, sin LLM, más un control automático.</strong> Con {len(ex_b)} productos "
        f"la edición libre cambió el cuarto (SSIM {f(mb['ssim_fuera_de_los_muebles'], 2)}); la estricta "
        f"lo preservó ({f(ms['ssim_fuera_de_los_muebles'], 2)}). Una imagen por variante es una "
        f"anécdota: por eso el control en cada corrida.",
        t=65, wide=True, notes=[
            "La imagen. El modelo tiende a «mejorar» la foto: mueve la cámara, agranda ventanas, "
            "repinta. Para el usuario es grave, porque compraría para un cuarto que no es el suyo.",
            "[paso] Probamos distintas formas de pedir la edición, siempre con la misma foto y la misma "
            "lista: que Claude escriba la escena, un template de edición libre, y uno de edición "
            "estricta. Ojo: una imagen por variante.",
            f"[paso] Con el pedido corto, las dos primeras preservan el cuarto parecido. Con el pedido "
            f"detallado y {len(ex_b)} productos, la edición libre lo cambió: el SSIM fuera de los muebles "
            f"cae a {f(mb['ssim_fuera_de_los_muebles'], 2)} y SIFT ve la cámara movida. La estricta lo "
            f"preserva.",
            "[paso] Elegimos edición estricta, sin LLM: más barata y más fiel. Pero una imagen por "
            "variante es una anécdota, así que además pusimos un control automático en cada corrida.",
        ])

    # ---------- E13 el control en acción
    cg = D["img"]["caballito-living"]["gen"]
    tiles = (f'<figure class="at"><div class="aimg"><img src="{img_uri(A / "caballito-living" / "room.jpg", 640, 480, q=72)}" alt=""></div>'
             '<figcaption><b>la foto original</b></figcaption></figure>')
    for i, a in enumerate(cg["attempts"]):
        ok = a["ok"]
        tiles += (f'<figure class="at"><div class="aimg"><img src="{img_uri(A / "caballito-living" / a["image"], 640, 480, q=72)}" alt="">'
                  f'<span class="badge {"ok" if ok else "no"}">{"aceptada" if ok else "rechazada"}</span></div>'
                  f'<figcaption><b>intento {i + 1}</b><span>inliers {a["sift_inliers"]} · reencontrados {pct(a["sift_reencontrados"], 1)}</span>'
                  f'<span>desplazamiento {pct(a["sift_desplazamiento_mediano"], 1)}</span></figcaption></figure>')
    body = hdx("E13", "De punta a punta", "El control, <em>en una corrida real</em>")
    body += (f'<div class="atts">{tiles}</div>'
             f'<p class="note" style="font-size:20px">Living de un departamento propio · {len(cg["attempts"])} intentos · '
             f'{usd(cg["cost_usd"])} de imagen · SSIM fuera de los muebles de la aceptada: '
             f'{f(cm["ambiente"]["ssim_fuera_de_los_muebles"], 3)}</p><div style="flex:1"></div>'
             f'<div class="dec" data-step="1"><div class="k">Decisión</div><p><strong>El control queda en el flujo:</strong> '
             f'inliers ≥ {D["sift_min_inliers"]} y desplazamiento ≤ {pct(D["sift_max_shift"])}, hasta '
             f'{D["sift_attempts"]} intentos. Los dos rechazos se ven a ojo: el cuarto se dio vuelta. Dónde poner '
             f'el umbral exacto es un experimento pendiente.</p></div>')
    add(body, sec="De punta a punta", title="E13 · El control en acción", t=30, phases="2,3", notes=[
        f"Y acá el control en una corrida real: el living de la portada. Los dos primeros intentos "
        f"cambiaron el cuarto, la cámara se movió, y SIFT reencontró menos del 5% de los puntos con "
        f"desplazamientos de más del 15%. Se rechazaron solos. El tercero preservó el cuarto y se "
        f"aceptó. Por eso esa corrida tuvo tres intentos.",
        f"[paso] El control queda en el flujo, con hasta {D['sift_attempts']} intentos. Dónde poner el "
        f"umbral exacto es lo que sigue.",
    ])

    # ================================================================== E14 réplica
    replica_slides(D)

    # ================================================================== T4
    def md(s):
        return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(s))

    trs = "".join(f'<div class="t4c b">{esc(r[0])}</div><div class="t4c">{md(r[1])}</div><div class="t4c">{md(r[2])}</div>'
                  f'<div class="t4c m">{md(r[3])}</div><div class="t4c m">{md(r[4])}</div>' for r in D["t4"])
    jr = D.get("t4_jueces", ["", "", "", "", ""])
    trs += (f'<div class="t4c b"></div><div class="t4c">{md(jr[1])}</div><div class="t4c">{md(jr[2])}</div>'
            f'<div class="t4c m">{md(jr[3])}</div><div class="t4c m">{md(jr[4])}</div>')
    body = hd("De punta a punta", "Lo que sigue: <em>medir la imagen en serio</em>")
    body += ('<div class="t4tag"><span class="chip pend">diseñado, sin correr: no hay resultados</span>'
             '<span class="cap">sobre los ambientes de pedidos.yaml, con la lista que eligió el flujo: solo cambia la imagen</span></div>'
             '<div class="t4"><div class="t4h">exp.</div><div class="t4h">pregunta</div><div class="t4h">variantes</div>'
             f'<div class="t4h">imágenes</div><div class="t4h">costo estimado</div>{trs}</div>'
             f'<p class="t4tot"><b>Total estimado:</b> {esc(D["t4_total"])} Métricas: las de E13 más un juez de a pares en los dos órdenes, como en E12.</p>')
    add(body, sec="De punta a punta", title="T4 · Lo que sigue", t=20, notes=[
        "Lo que sigue, y lo decimos claro: esto está diseñado y no corrido, no hay resultados.",
        "La imagen la medimos con una imagen por variante. El plan es repetirlo bien, en todos los "
        "ambientes: escena escrita por el LLM contra edición estricta, qué modelo de imagen, qué "
        "resolución, si las fotos del catálogo cambian la fidelidad, y calibrar el umbral del control "
        "SIFT con todos esos intentos. Con las métricas de E13 y un juez de a pares en los dos órdenes, "
        f"como en E12. Cuesta {D['t4_total'].rstrip('.')}",
    ])

    # ================================================================== cierre
    divider(6, ["Cerramos."])

    body = hd("Cierre", "Lo que decidimos, <em>y qué experimento lo decidió</em>")
    body += variantes_html(D, elegidas=True)
    add(body, sec="Cierre", title="Lo que decidimos", t=25, notes=[
        "Volvemos a la tabla del principio, ahora con lo que elegimos en cada fila y el experimento "
        "que lo decidió.",
        "Descripciones de ocho líneas, Qwen3 entero, Chroma, un documento por producto; la consulta "
        "reescrita en ocho líneas; un modelo que ve para elegir entre cinco; los dos catálogos; y "
        "edición estricta con control SIFT. El modelo de imagen es el único que quedó sin medir.",
    ])

    rows = [dict(label="Naive: texto del vendedor", value=D["naive"]["hit@1"], ci=ci(D["naive"]), kind="muted",
                 sub="hashing de palabras, sin filtro"),
            dict(label="+ descripciones de ocho líneas", value=D["desc_hash"]["hit@1"], ci=ci(D["desc_hash"]),
                 kind="alt", sub="E2"),
            dict(label="+ Qwen3, filtro, ChromaDB", value=b["hit@1"], ci=ci(b), kind="alt", sub="E2 · E4 · E5"),
            dict(label="+ reranking mirando las fotos", value=o["hit@1"], ci=ci(o), kind="main", sub="E7")]
    body = hd("Cierre", f"De {f(D['naive']['hit@1'])} a {f(o['hit@1'])} de hit@1, <em>paso a paso</em>")
    body += ('<div class="path"><div class="legend"><span>hit@1 con IC 95% · '
             f'{D["n_resp"]} búsquedas · catálogo de {D["n_ikea"]}</span></div>'
             + hbars(rows, width=1712, label_w=480, row_h=118, bar_h=34, x_max=0.8, ticks=[0, .2, .4, .6, .8],
                     tick_fmt=lambda t: f(t, 1), refs=[(D["azar_h1"], f"azar {f(D['azar_h1'])}")])
             + "</div>")
    add(body, sec="Cierre", title="El camino", t=25, notes=[
        f"El camino de los números. El punto de partida ingenuo, texto del vendedor y contar palabras, "
        f"da {f(D['naive']['hit@1'])}. Escribir nuestras descripciones lo lleva a "
        f"{f(D['desc_hash']['hit@1'])}: el salto más grande lo dio qué texto guardamos, no el modelo. "
        f"Qwen3, filtro y Chroma suman poco más, hasta {f(b['hit@1'])}. Y un modelo que mira las fotos "
        f"al final lo lleva a {f(o['hit@1'])}.",
    ])

    # ---------- costos
    gp = D["gasto_paso"]
    nombres = {"eval.rerank": "evaluación: reranking", "catalog.describe": "catálogo: descripciones ABO",
               "furnish.choose": "flujo: choose", "eval.juez_listas": "evaluación: juez de listas",
               "furnish.plan": "flujo: plan", "furnish.generate": "flujo: imágenes", "furnish.scene": "flujo: scene (antes con LLM)"}
    mx = max(gp.values())
    rows = [dict(label=nombres.get(k, k), value=v, kind="main" if k.startswith("furnish") else "alt")
            for k, v in sorted(gp.items(), key=lambda kv: -kv[1])]
    xm = (int(mx / 4) + 1) * 4
    led = hbars(rows, width=940, label_w=360, row_h=72, bar_h=22, x_max=xm,
                ticks=[0, xm / 4, xm / 2, 3 * xm / 4, xm], fmt=lambda v: usd(v), tick_fmt=lambda t: f"{t:.0f}",
                right_pad=120)
    parts = [("plan", D["costo_plan"]), ("choose", D["costo_choose"]), ("imagen", D["img_precio"])]
    tot = D["costo_corrida"]
    bar = "".join(f'<div class="cb" style="flex:{v / tot:.3f}"><b>{n}</b><span>{usd(v)}</span></div>' for n, v in parts)
    body = hd("Cierre", "Lo que cuesta")
    body += (
        '<div class="cost"><div class="cl1">'
        f'<div class="lbl">Una corrida del flujo</div><div class="big t">≈ {usd(tot)}</div>'
        f'<div class="cbar">{bar}</div>'
        f'<p class="note">Promedio de las corridas de punta a punta. Cada reintento de imagen suma {usd(D["img_precio"])}. '
        f'Choose tarda {f(D["lat_choose"], 0)} s (mediana): mira {D["k_flujo"]} fotos por pieza.</p>'
        f'<div class="lbl" style="margin-top:36px">En todo el trabajo</div><div class="big">{usd(D["gasto_total"])}</div>'
        f'<p class="note">{D["n_llamadas"]} llamadas pagas en el registro de gastos, desde el {D["fechas"]["v1"].strftime("%d/%m")}. '
        'El retrieval, los embeddings y todas las métricas de imagen corren local, gratis.</p></div>'
        f'<div class="cl2"><div class="legend"><span>registro de gastos, por paso</span><span><i style="background:#B0502A"></i>el flujo</span>'
        f'<span><i style="background:#7E858C"></i>evaluación y catálogo</span></div>{led}</div></div>')
    add(body, sec="Cierre", title="Costos", t=25, notes=[
        f"Lo que cuesta. Una corrida del flujo, unos {usd(tot)}: plan, choose, que es lo más caro "
        f"porque mira fotos, y la imagen, más {usd(D['img_precio'])} por cada reintento.",
        f"En todo el trabajo gastamos {usd(D['gasto_total'])} registrados, y lo que más se llevó fue "
        f"evaluar: el reranking con Opus sobre todas las búsquedas. Todo lo demás, el retrieval, los "
        f"embeddings y las métricas de imagen, corre local y gratis.",
    ])

    # ---------- aprendizajes y límites
    L = [
        f"Lo que más pesa es <strong>qué texto se indexa y cómo se escribe la consulta</strong>: "
        f"descripciones y query rewriting llevan hit@1 de {f(D['naive']['hit@1'], 2)} a "
        f"{f(D['desc_hash']['hit@1'], 2)}; el embedder suma poco.",
        f"Un <strong>modelo que ve</strong>, al final, vale más que cualquier ajuste fino del retrieval: "
        f"+{f(o['hit@1'] - b['hit@1'], 2)} de hit@1.",
        "<strong>Intervalos y repeticiones</strong> evitaron conclusiones falsas: filtros, dimensiones y "
        "embedders que parecían mejores eran ruido.",
        "Las métricas sin ground truth, el juez y RAGAS, encontraron lo que hit@k no ve: <strong>medidas "
        "que faltan</strong> y un catálogo que no alcanza para otros estilos.",
    ]
    Lim = [
        "La imagen se midió con <strong>una imagen por variante</strong>. T4 está diseñado para eso.",
        "El ground truth es de IKEA: <strong>ABO solo se evaluó con un juez</strong>.",
        f"Los jueces son <strong>Claude evaluando a Claude</strong>. Validamos el juez contra las "
        f"anotaciones ({pct(D['grad']['acuerdo_con_gt']['anotado_con_2'])} contra "
        f"{pct(D['grad']['acuerdo_con_gt']['otros_con_2'])}), no contra personas.",
        "Los asientos de IKEA <strong>no tienen medidas</strong>: el filtro por tamaño no los alcanza.",
    ]
    body = hd("Cierre", "Lo que aprendimos, <em>y lo que todavía no sabemos</em>")
    body += ('<div class="learn"><div class="lc">'
             + "".join(f'<div class="li"><span class="ln">{i + 1}</span><p>{x}</p></div>' for i, x in enumerate(L))
             + '</div><div class="lc lim" data-step="1"><div class="lbl">Límites</div>'
             + "".join(f'<div class="li"><span class="ln">–</span><p>{x}</p></div>' for x in Lim)
             + "</div></div>")
    add(body, sec="Cierre", title="Aprendizajes y límites", t=60, notes=[
        "Cuatro cosas que aprendimos. Uno: lo que más pesó fue qué texto guardamos y cómo escribimos "
        "la consulta, más que el modelo de embeddings. Dos: un modelo que ve, al final, vale más que "
        "cualquier ajuste fino del retrieval. Tres: medir con intervalos y repetir nos salvó de "
        "declarar ganadoras a varias cosas que eran ruido. Cuatro: las métricas sin ground truth "
        "encontraron problemas que hit@k no veía, como las medidas que faltan.",
        "[paso] Y los límites, con honestidad: la imagen se midió con muy pocas imágenes; ABO solo "
        "tiene evaluación con juez; los jueces son Claude evaluando a Claude, validados contra las "
        "anotaciones pero no contra personas; y los asientos de IKEA siguen sin medidas.",
    ])

    # ---------- pasos a futuro: cajas y medidas reales
    futuro_slides(D)

    # ---------- gracias
    cc = A / "caballito-comedor"
    cch = D["img"]["caballito-comedor"]["choice"]["answer"]["choices"]
    nombres_cc = []
    for c in cch:
        k = D["items"][c["id"]]["kind"]
        q = c.get("quantity", 1)
        nm = KIND_ES.get(k, k)
        nombres_cc.append(f"{q} {nm}s" if q > 1 and not nm.endswith("s") else nm)
    lista_cc = ", ".join(nombres_cc[:-1]) + " y " + nombres_cc[-1]
    body = ('<div class="cl"><div class="eb">amoblai · TP 3 · 73.69 LLM · ITBA 2026</div>'
            '<h1 class="gr">Gracias</h1><p class="sub">¿Preguntas?</p></div>'
            '<div class="team">Juan Bautista Albertoni Salini<br>Matias Juan Rossi Seifert<br>Junior Rambau</div>'
            f'<div class="split"><div class="in"><img src="{img_uri(cc / "room.jpg", 1100, 825, q=74)}" alt="">'
            f'<img class="after" src="{img_uri(cc / "final.png", 1100, 825, q=74)}" alt="">'
            '<div class="line"></div><div class="knob">↔</div>'
            '<span class="lab a">la foto</span><span class="lab b">amoblai</span></div></div>'
            f'<div class="scap">El comedor del mismo departamento, con {lista_cc} del catálogo.</div>')
    add(body, sec="Cierre", title="Gracias", t=15, cls="cover", notes=[
        "Les dejamos el comedor del mismo departamento, amoblado por amoblai. Gracias; ¿preguntas?",
    ])

    # ================================================================== apéndice
    rai = [
        ("Privacidad de la foto", "Un interior es un dato personal y viaja a dos proveedores.",
         "Consentimiento, borrar EXIF/GPS, difuminar caras y papeles, proveedores sin retención, borrado a los 30 días."),
        ("Una imagen que engaña", "Si cambia el cuarto o el mueble, el usuario compra algo que no entra.",
         "Edición estricta y control SIFT (ya); fidelidad por recorte (ya); marca de agua y medidas reales al lado."),
        ("Alucinación en la lista", "Un producto que no existe o un atributo falso.",
         "Solo elige entre ids recuperados y validados (ya); faithfulness con juez (ya); revisión humana por muestreo."),
        ("Sesgos", "Un catálogo de una marca empuja una estética y un rango de precios.",
         "Varios catálogos (IKEA + ABO, ya); métricas por estilo; presupuesto y accesibilidad como filtros duros."),
        ("Prompt injection", "Un pedido o un texto en la foto que cambia las instrucciones.",
         "El pedido entra como dato; JSON validado contra esquema (ya); lista cerrada de productos; moderación."),
        ("Producción", "Pedidos de 1 a 2 minutos, proveedores que fallan, costo por pedido.",
         "Cola asíncrona, pasos que se retoman (ya), proveedor de respaldo, trazas por paso, evaluación offline en CI."),
    ]
    body = hd("Apéndice", "IA responsable y producción <em>(Ejercicio 3)</em>")
    body += ('<div class="rai"><div class="rh">riesgo</div><div class="rh">qué puede pasar</div><div class="rh">cómo lo mitigamos</div>'
             + "".join(f'<div class="r1">{esc(a)}</div><div class="r2">{esc(bb)}</div><div class="r3">{esc(c)}</div>' for a, bb, c in rai)
             + "</div>")
    add(body, sec="Apéndice", title="Apéndice · IA responsable", t=0, notes=[
        "Lámina de respaldo para la discusión del ejercicio 3: riesgos de IA responsable y estrategia "
        "de producción. Lo marcado «ya» está implementado en el prototipo.",
    ])

    keys = [k for k in D["M"]]
    rows_html = ""
    for k in keys:
        m = D["M"][k]
        corto = (k.replace("description", "desc.").replace("name+desc.", "nombre+desc.").replace("filtro-", "")
                 .replace("rerank-minilm-reranker", "rerank MiniLM").replace("consulta-", "consulta ")
                 .replace("chunks-lines-", "chunks ").replace("seller", "vendedor").replace("|", " · "))
        rows_html += (f'<div class="ab1">{esc(corto)}</div><div class="ab2">{f(m["hit@1"])}</div>'
                      f'<div class="ab2">{f(m["hit@10"])}</div><div class="ab2">{f(m["mrr@10"])}</div>'
                      f'<div class="ab2">{f(m["ndcg@10"])}</div><div class="ab2">{f(m["context_recall@3"])}</div>')
    hdr = ('<div class="abh">método</div><div class="abh">hit@1</div><div class="abh">hit@10</div>'
           '<div class="abh">MRR@10</div><div class="abh">NDCG@10</div><div class="abh">CR@3</div>')
    half = (len(keys) + 1) // 2
    rws = rows_html.split('<div class="ab1">')[1:]
    col1 = "".join('<div class="ab1">' + r for r in rws[:half])
    col2 = "".join('<div class="ab1">' + r for r in rws[half:])
    body = hd("Apéndice", f"La ablación completa <em>({len(keys)} configuraciones)</em>")
    body += f'<div class="abl"><div class="abt">{hdr}{col1}</div><div class="abt">{hdr}{col2}</div></div>'
    body += (f'<p class="cap" style="margin-top:12px">{D["n_resp"]} búsquedas · catálogo de {D["n_ikea"]} · '
             f'embedder · texto · filtro · variante. Reranking con Opus: hit@1 {f(o["hit@1"])}.</p>')
    add(body, sec="Apéndice", title="Apéndice · Ablación completa", t=0, notes=[
        "Lámina de respaldo: todas las configuraciones de la ablación final, por si preguntan por "
        "alguna combinación.",
    ])

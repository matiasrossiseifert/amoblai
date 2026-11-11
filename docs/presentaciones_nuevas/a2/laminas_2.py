"""Los experimentos: qué guardamos (E1–E5), cómo buscamos (E6–E8), cuánto creerle (E9–E11) y de
punta a punta (E12–E14, T4). Cada uno en el mismo orden: por qué → qué hicimos → resultados →
decisión."""

from __future__ import annotations

import re
from pathlib import Path

import img
from base import (CAT_ES, KIND_ES, add, bloque, cab, esc, exp, f, ficha, llamada, pasos_x, pct, remate, usd)
from datos_deck import RES
from graf import dots_repro, dumbbell, hbars, heatmap, line_chart
from laminas_1 import separador
from laminas_r import replica_slides

A = RES / "amoblar"


def ci(m, k="hit@1"):
    return tuple(m[f"{k}_ic95"])


def ley(*items, nota=""):
    out = '<div class="ley" data-desde="1">'
    for col, txt in items:
        out += f'<span><i style="background:{col}"></i>{txt}</span>'
    if nota:
        out += f"<span>{nota}</span>"
    return out + "</div>"


AZUL, GRIS, CLARO, TINTA = "#2453D6", "#9AA4AF", "#C9CFD5", "#13202C"


def xcab(num, rot, titulo):
    return (f'<div class="cuerpo"><div class="xcab">{llamada(num, rot)}{pasos_x()}</div>'
            f'<h2 class="t xt">{titulo}</h2></div>')


def build(D: dict, ctx: dict) -> None:
    b = D["best"]
    o = D["opus"]

    # ================================================================ 03 · qué guardamos
    separador(3, ["Primer capítulo de experimentos: qué guardamos en el índice. Cinco decisiones del "
                  "indexing. Y al cuarto se le suma el mueble de la tele."])

    # ---------------------------------------------------------------- E1
    v0 = D["v0_path"]
    lab = {"E0-naive-clip": "CLIP, el recorte tal cual", "E1-quitar-fondo": "+ quitar el fondo",
           "E2-filtro-categoria": "+ filtro por categoría", "E3-dinov2": "DINOv2 en lugar de CLIP",
           "E3-dinov3": "DINOv3 en lugar de DINOv2", "E4-dinov3-sin-quitar-fondo": "DINOv3, sin quitar el fondo"}
    rows = [dict(label=lab[p["paso"]], value=p["hit1"], ci=tuple(p["ic"]), kind="alt") for p in v0]
    rows.append(dict(label="texto: descripciones + Qwen3", value=D["v1_275"]["hit@1"], ci=ci(D["v1_275"]), kind="main"))
    v0b = v0[-1]
    res = (ley((GRIS, "por imagen · v0"), (AZUL, "por texto · v1"), nota=f"hit@1 · IC 95% · catálogo de {D['n_275']}")
           + hbars(rows, width=1150, label_w=400, row_h=64, bar_h=26, x_max=0.8, ticks=[0, .2, .4, .6, .8]))
    exp("E1", 3, "¿Buscamos los muebles <em>por imagen o por texto?</em>",
        "<p>La v0 buscaba por imagen: recortar cada mueble de una foto y compararlo con las fotos del "
        "catálogo.</p><p>Pero en amoblai <strong>el ambiente está vacío</strong>: no hay nada que "
        "recortar. Lo que hay es un pedido.</p>",
        f"<p>El mismo ground truth y el catálogo que vio la v0 ({D['n_275']} productos):</p><ul>"
        f"<li><strong>imagen:</strong> seis pasos acumulados, de CLIP a DINOv3;</li>"
        f"<li><strong>texto:</strong> descripciones de ocho líneas y Qwen3.</li></ul>",
        res,
        f"<strong>Texto.</strong> Le gana al mejor retrieval por imagen ({f(D['v1_275']['hit@1'])} contra "
        f"{f(v0b['hit1'])}), funciona con el cuarto vacío y deja que un LLM escriba la consulta.",
        t=60, notas=[
            "Primer experimento, y el que cambió todo: ¿buscamos por imagen o por texto?",
            "La v0 buscaba por imagen: detectaba cada mueble en la foto, lo recortaba y lo comparaba con "
            "las fotos del catálogo. Es lo natural si la pregunta es «encontrá este mueble». Pero en "
            "amoblai el ambiente está vacío: no hay nada que recortar, hay un pedido.",
            f"[paso] Para comparar en serio usamos el mismo ground truth y el mismo catálogo que vio la "
            f"v0, {D['n_275']} productos. Por imagen, seis pasos acumulados, de CLIP a DINOv3, sobre "
            f"{v0b['n']} recortes. Por texto, las descripciones con Qwen3, sobre "
            f"{D['v1_275']['answerable']} búsquedas.",
            f"[paso] La imagen mejoró mucho con cada paso: de {f(v0[0]['hit1'])} a {f(v0b['hit1'])}. Pero "
            f"el texto llega a {f(D['v1_275']['hit@1'])}, con intervalos que apenas se tocan.",
            "[paso] Decidimos texto. Gana, y además es lo único que funciona con el caso real: un cuarto "
            "vacío y un pedido escrito.",
        ])

    # ---------------------------------------------------------------- E2
    M = D["M"]
    emb = [("hashing", "hashing"), ("bge", "BGE-base"), ("qwen3", "Qwen3")]
    txt = [("seller", "vendedor"), ("description", "descripción")]
    fil = [("none", "sin filtro"), ("type", "tipo grueso"), ("kind", "kind fino")]
    rlab, vals = [], []
    for tk, tl in txt:
        for ek, el in emb:
            rlab.append(f"{tl} · {el}")
            vals.append([M[f"{ek}|{tk}|filtro-{fk}"]["hit@1"] for fk, _ in fil])
    res = ('<div class="ley" data-desde="1"><span>hit@1 · filas: texto del producto y embedder · columnas: filtro de metadata</span></div>'
           + heatmap(rlab, [x[1] for x in fil], vals, width=1080, label_w=330, cell_h=62, vmin=0.05, vmax=0.6,
                     best=(5, 1), gaps=(3,))
           + f'<p class="nota" data-desde="2">Con el nombre comercial delante de la descripción: <b>{f(D["namedesc"]["hit@1"])}</b> '
             f'(Qwen3, kind), contra {f(D["kind"]["hit@1"])} sin el nombre. IC de la mejor celda: {f(ci(b)[0])}–{f(ci(b)[1])}.</p>')
    exp("E2", 3, "¿Qué texto indexamos, <em>con qué embedder y qué filtro?</em>",
        "<p>El catálogo trae el texto del vendedor: nombre y una frase de marketing.</p><p>La hipótesis: "
        "describir cada producto en <strong>las mismas ocho líneas que la consulta</strong> hace que se "
        "encuentren.</p>",
        f"<p>La grilla completa, {D['n_resp']} búsquedas, catálogo de {D['n_ikea']}:</p><ul>"
        "<li>2 textos: vendedor o descripción</li><li>3 embedders: hashing de palabras, BGE-base, Qwen3</li>"
        "<li>3 filtros: ninguno, tipo grueso o kind fino</li></ul>",
        res,
        f"<strong>Descripciones de ocho líneas con Qwen3.</strong> El texto pesa más que el embedder: con "
        f"descripciones, hasta el hashing llega a {f(D['desc_hash']['hit@1'])} sin filtro. Los tres filtros "
        f"quedan dentro del intervalo; el flujo usa el kind, que decide plan.",
        t=65, notas=[
            "Ya en texto: ¿qué texto ponemos de cada producto, con qué embedder y con qué filtro?",
            "El catálogo trae el texto del vendedor: el nombre y una frase de marketing. Nuestra hipótesis "
            "era que describir cada producto en las mismas ocho líneas que la consulta iba a hacer que se "
            "encuentren. Y queríamos saber cuánto aporta un embedder neuronal frente a contar palabras, y "
            "si filtrar por metadata ayuda.",
            "[paso] Corrimos la grilla completa: dos textos, tres embedders (desde contar palabras hasta "
            "Qwen3) y tres filtros: ninguno, el tipo grueso (sofá, mesa) o el kind fino (mesa ratona, mesa "
            "auxiliar).",
            f"[paso] La lectura es por filas. Con el texto del vendedor, nada pasa de "
            f"{f(max(max(v) for v in vals[:3]))}. Con nuestras descripciones, todo salta a más de 0,47. El "
            f"embedder suma menos: Qwen3 es el mejor, pero el hashing queda cerca. Y poner el nombre "
            f"comercial adelante empeora: agrega palabras que la consulta no tiene.",
            "[paso] Decidimos descripciones con Qwen3. Los filtros, con descripciones, casi no cambian "
            "nada, porque la línea Type ya dice qué es cada cosa. El flujo filtra por el kind que decide "
            "el plan; type, kind o ninguno quedan dentro del intervalo.",
        ])

    # ---------------------------------------------------------------- E3
    rows = [dict(label="un documento por producto", value=b["hit@1"], ci=ci(b), kind="main", sub="las ocho líneas juntas"),
            dict(label="línea contra línea", value=D["chunks_al"]["hit@1"], ci=ci(D["chunks_al"]), kind="alt",
                 sub="Colors con Colors…, promedio"),
            dict(label="cada línea, un chunk", value=D["chunks_max"]["hit@1"], ci=ci(D["chunks_max"]), kind="alt",
                 sub="el producto puntúa con su mejor línea")]
    res = (ley(nota="hit@1 · IC 95% · Qwen3, filtro por tipo")
           + hbars(rows, width=1150, label_w=400, row_h=118, bar_h=32, x_max=0.8, ticks=[0, .2, .4, .6, .8],
                   refs=[(D["azar_h1"], "azar")]))
    exp("E3", 3, "¿Partimos cada descripción <em>en chunks?</em>",
        "<p>La receta de RAG dice partir los documentos en pedazos. Pero nuestra descripción ya es corta: "
        "ocho líneas.</p><p>¿Conviene igual comparar por partes, los colores con los colores?</p>",
        "<p>Tres formas de partir, con todo lo demás igual: el documento entero, cada línea como chunk, y "
        "línea contra línea del mismo rótulo.</p>",
        res,
        f"<strong>Un producto, un documento.</strong> Partir por líneas pierde el contexto "
        f"({f(D['chunks_max']['hit@1'])}); alinear por rótulo casi empata ({f(D['chunks_al']['hit@1'])}) con "
        f"ocho vectores por producto en lugar de uno.",
        t=35, notas=[
            "Splitting. La receta de RAG dice partir los documentos en chunks, pero nuestra descripción ya "
            "es corta. ¿Conviene igual comparar por partes?",
            "[paso] Probamos tres formas: el documento entero, cada línea como chunk, y línea contra línea "
            "del mismo rótulo, colores con colores.",
            f"[paso] Partir en líneas sueltas se cae a {f(D['chunks_max']['hit@1'])}: una línea sola no dice "
            f"de qué producto habla. Alinear por rótulo casi empata.",
            "[paso] Nos quedamos con un documento por producto: igual de bueno y ocho veces más simple.",
        ])

    # ---------------------------------------------------------------- E4
    dims = sorted(D["dims"])
    h1 = [D["dims"][d]["hit@1"] for d in dims]
    h10 = [D["dims"][d]["hit@10"] for d in dims]
    cis = [tuple(D["dims"][d]["hit@1_ic95"]) for d in dims]
    res = (ley((AZUL, "hit@1, con IC 95%"), (GRIS, "hit@10"))
           + line_chart([dict(name="hit@1", ys=h1, kind="main", ci=cis, label="hit@1"),
                         dict(name="hit@10", ys=h10, kind="alt", dash=True, label="hit@10")],
                        dims, width=1120, height=500, ymin=0.3, ymax=1.0, yticks=[.3, .5, .7, .9],
                        xlab="dimensiones del vector (truncado y renormalizado)", right=130))
    exp("E4", 3, "¿Cuántas dimensiones <em>necesita el embedding?</em>",
        "<p>Qwen3-Embedding se entrenó con <strong>Matryoshka</strong>: las primeras componentes del vector "
        "ya son un embedding válido.</p><p>Menos dimensiones: índice más chico, búsqueda más rápida. ¿Cuánto "
        "se pierde?</p>",
        f"<p>Truncamos los vectores a {', '.join(str(d) for d in dims[:-1])} y {dims[-1]} componentes y los "
        f"renormalizamos, sin reentrenar nada.</p>",
        res,
        f"<strong>{dims[-1]} dimensiones.</strong> Desde 512 la curva está plana y dentro del intervalo, "
        f"pero el catálogo entero ocupa {f(D['indice_mb'], 1)} MB: a esta escala no hay nada que ahorrar. Con "
        f"millones de productos, 256 o 512.",
        t=40, notas=[
            "Dimensión del embedding. Qwen3 se entrenó con Matryoshka: las primeras componentes del vector "
            "ya son un embedding válido, y uno más chico es más barato de guardar y de buscar.",
            "[paso] Truncamos a 32, 64, hasta 1024, y renormalizamos. Sin reentrenar.",
            f"[paso] Con 32 componentes ya da {f(h1[0])}; desde 512 la curva se aplana "
            f"({f(D['dims'][512]['hit@1'])} contra {f(h1[-1])}).",
            f"[paso] Nos quedamos con las {dims[-1]}: todo el catálogo ocupa {f(D['indice_mb'], 1)} megas. "
            f"Con un catálogo de millones, elegiríamos 256 o 512.",
        ])

    # ---------------------------------------------------------------- E5
    tot = D["chroma_total_type"]
    hn = D["hnsw"]
    res = ('<div class="bign" data-desde="1">'
           f'<div class="bn"><div class="bnv"><span data-desde="2">{D["chroma_igual_type"]}</span><small> / {tot}</small></div>'
           '<p>búsquedas con el <strong>ranking completo idéntico</strong> · filtro por tipo</p></div>'
           f'<div class="bn"><div class="bnv"><span data-desde="2">{D["chroma_igual_kind"]}</span><small> / {D["chroma_total_kind"]}</small></div>'
           '<p>ídem, con filtro por kind</p></div>'
           f'<div class="bn"><div class="bnv sm"><span data-desde="2">{f(D["exact"]["hit@1"])} = {f(b["hit@1"])}</span></div>'
           '<p>hit@1 de la búsqueda exacta = hit@1 de ChromaDB</p></div></div>')
    exp("E5", 3, "¿La base vectorial <em>se pierde resultados?</em>",
        "<p>ChromaDB usa <strong>HNSW</strong>, una búsqueda aproximada: recorre un grafo de vecinos en lugar "
        "de comparar contra todos.</p><p>«Aproximada» puede querer decir que se le escapa el correcto.</p>",
        f"<p>Las {tot} búsquedas dos veces: con HNSW (coseno, ef_search {hn.get('ef_search', '—')}, "
        f"{hn.get('max_neighbors', '—')} vecinos por nodo) y con búsqueda exacta en numpy. Comparamos el "
        f"ranking completo, una por una.</p>",
        res,
        "<strong>ChromaDB.</strong> A esta escala la búsqueda aproximada es exacta, y suma filtros de "
        "metadata, persistencia y la descripción guardada al lado del vector.",
        t=30, notas=[
            "La base vectorial. ChromaDB usa HNSW, una búsqueda aproximada sobre un grafo de vecinos. ¿Se le "
            "escapa el correcto?",
            "[paso] Corrimos todas las búsquedas con HNSW y con búsqueda exacta, y comparamos el ranking "
            "entero.",
            f"[paso] Idénticos en las {tot}. Con este tamaño de catálogo, aproximado es exacto.",
            "[paso] Nos quedamos con Chroma por todo lo demás que trae: filtros, persistencia, el texto al "
            "lado del vector.",
        ])

    # ================================================================ 04 · cómo buscamos
    separador(4, ["Segundo capítulo: lo que pasa en cada pedido, antes y después de buscar. Llega la mesa ratona."])

    # ---------------------------------------------------------------- E6
    rows = [dict(label="las ocho líneas", value=b["hit@1"], ci=ci(b), kind="main", sub="lo que escribe plan"),
            dict(label="solo la línea Type", value=D["q_type"]["hit@1"], ci=ci(D["q_type"]), kind="alt",
                 sub="«rug, high pile shag»"),
            dict(label="solo el nombre del kind", value=D["q_kind"]["hit@1"], ci=ci(D["q_kind"]), kind="muted",
                 sub="«rug»: sin reescribir")]
    res = (ley(nota="hit@1 · IC 95% · la misma búsqueda con tres consultas")
           + hbars(rows, width=1150, label_w=400, row_h=118, bar_h=32, x_max=0.8, ticks=[0, .2, .4, .6, .8],
                   refs=[(D["azar_h1"], "azar")]))
    exp("E6", 4, "¿Hace falta que el LLM <em>reescriba la consulta?</em>",
        "<p>Plan podría buscar «alfombra» y listo. En cambio escribe el producto ideal en ocho líneas, como "
        "un documento hipotético del catálogo: la idea de HyDE.</p><p>Es una llamada a Opus por pedido. ¿Se "
        "paga?</p>",
        "<p>La misma búsqueda con tres consultas: las ocho líneas, solo la línea Type, o solo el nombre del "
        "kind.</p>",
        res,
        f"<strong>Reescribir, y en las ocho líneas.</strong> Es la decisión que más pesa en todo el "
        f"retrieval: de {f(D['q_kind']['hit@1'])} a {f(b['hit@1'])}.",
        t=45, notas=[
            "Query rewriting. Plan podría buscar la palabra «alfombra» y listo. En cambio escribe el producto "
            "ideal en las ocho líneas, como un documento hipotético del catálogo, que es la idea de HyDE. "
            "Cuesta una llamada a Opus por pedido: ¿vale la pena?",
            "[paso] Misma búsqueda con tres consultas: las ocho líneas, solo la línea Type, o solo el nombre "
            "del kind.",
            f"[paso] Con el nombre solo, {f(D['q_kind']['hit@1'])}, apenas arriba del azar. Con la línea "
            f"Type, {f(D['q_type']['hit@1'])}. Con las ocho líneas, {f(b['hit@1'])}.",
            "[paso] Es la decisión que más pesa de todo el retrieval. Los colores, la forma y el estilo son "
            "lo que distingue una alfombra de otras ochenta.",
        ])

    # ---------------------------------------------------------------- E7
    rows = [dict(label="sin reranking", value=b["hit@1"], ci=ci(b), kind="alt", sub=f"Qwen3 · MRR@10 {f(b['mrr@10'])}"),
            dict(label="cross-encoder de texto", value=D["minilm"]["hit@1"], ci=ci(D["minilm"]), kind="muted",
                 sub=f"MiniLM, local · MRR@10 {f(D['minilm']['mrr@10'])}"),
            dict(label="Opus mirando las fotos", value=o["hit@1"], ci=ci(o), kind="main",
                 sub=f"{usd(D['rerank_costo_llamada'])} por búsqueda · MRR@10 {f(o['mrr@10'])}")]
    res = (ley(nota="hit@1 · IC 95% · reordenando el top-10 de Qwen3")
           + hbars(rows, width=1150, label_w=400, row_h=118, bar_h=32, x_max=0.8, ticks=[0, .2, .4, .6, .8]))
    exp("E7", 4, "¿Conviene reordenar los candidatos <em>mirando las fotos?</em>",
        "<p>El embedding compara textos. Pero dos alfombras crema de pelo largo se describen casi igual y "
        "se distinguen a la vista.</p><p>La idea: que un modelo que ve reordene los primeros diez.</p>",
        "<p>Dos rerankers sobre el top-10:</p><ul><li>un <strong>cross-encoder de texto</strong> (MiniLM de "
        "MS MARCO, gratis);</li><li><strong>Claude Opus 5.5</strong> mirando la foto del ambiente y las de "
        "los candidatos.</li></ul>",
        res, None, t=55, notas=[
            "Reranking. El embedding compara textos, pero dos alfombras crema de pelo largo se describen casi "
            "igual y se distinguen mirando. La idea es que un modelo que ve reordene los primeros diez.",
            f"[paso] Probamos dos: un cross-encoder de texto, gratis, que lee consulta y descripción juntas; y "
            f"Opus mirando las fotos, a unos {usd(D['rerank_costo_llamada'])} por búsqueda.",
            f"[paso] El cross-encoder empeora: {f(D['minilm']['hit@1'])}. Está entrenado en búsqueda web y no "
            f"aporta nada que el embedding no tenga. Opus sube de {f(b['hit@1'])} a {f(o['hit@1'])}, con "
            f"intervalos que no se tocan: es la mejora más grande después del query rewriting.",
        ])

    # ---------------------------------------------------------------- E7 · dónde ayuda
    opc = o.get("hit@1_por_categoria", {})
    drows = [dict(label=CAT_ES.get(c, c), a=b["hit@1_por_categoria"][c], b=opc[c], n=D["cats_n"][c])
             for c in D["cats"] if c in opc]
    drows.sort(key=lambda r: r["a"])
    ej, er = D["ej"], D["ej_rr"]
    rel = set(ej["relevant"])
    s1 = "".join(ficha(D, p, 112, cap=False, pos=i + 1, hi=p in rel) for i, p in enumerate(ej["ranked"][:5]))
    s2 = "".join(ficha(D, p, 112, cap=False, pos=i + 1, hi=p in rel) for i, p in enumerate(er["ranked"][:5]))
    rug = next((r for r in drows if r["label"] == "alfombras"), drows[0])
    body = (xcab("E7", "Cómo buscamos", "Dónde ayuda <em>mirar las fotos</em>")
            + '<div class="e7b"><div>'
            + '<div class="ley"><span><i style="background:#fff;box-shadow:inset 0 0 0 3px #9AA4AF"></i>Qwen3</span>'
              '<span><i style="background:#2453D6"></i>+ Opus</span><span>hit@1 por categoría · n = consultas</span></div>'
            + dumbbell(drows, width=880, label_w=230, row_h=50)
            + '</div><div class="e7r">'
            + '<div class="etq">la alfombra de las métricas</div>'
            + f'<p class="e7c">Qwen3: el anotado queda <b>{ej["rank"]}.º</b></p><div class="tira">{s1}</div>'
            + f'<p class="e7c">Después de Opus: <b>{er["rank"]}.º</b></p><div class="tira">{s2}</div>'
            + f'<p class="nota">Con el catálogo chico de {D["n_268"]} productos, solo muebles, el salto era de '
              f'{f(D["base268"]["hit@1"])} a {f(D["opus268"]["hit@1"])}.</p>'
            + '</div></div>'
            + f'<div class="decision" data-desde="1"><div class="k">decisión</div><p><strong>Reordenar con un modelo que ve.</strong> '
              f'Opus sube hit@1 de {f(b["hit@1"])} a {f(o["hit@1"])}, sobre todo donde los productos se parecen; el '
              f'cross-encoder empeora. En el flujo, ese reranker es el paso choose.</p></div>')
    add(body, titulo="E7 · Dónde ayuda", cap=4, t=45, fases="2,3", notas=[
        f"Dónde ayuda. Por categoría, el salto es mayor donde los productos se parecen entre sí: alfombras, "
        f"de {f(rug['a'], 2)} a {f(rug['b'], 2)}, estantes, deco, lámparas. Donde el texto ya alcanzaba, como "
        f"sillas, sube menos.",
        f"A la derecha, la búsqueda de la alfombra que usamos para explicar las métricas: Qwen3 la dejó "
        f"{ej['rank']}.ª; Opus, mirando, la sube a la {er['rank']}.ª.",
        "[paso] Decisión: reordenar con un modelo que ve. En el flujo, ese reranker es el paso choose: el "
        "mismo Opus, que además elige la combinación entera.",
    ])

    # ---------------------------------------------------------------- E8
    cv = D["curva"]["por_k"]
    ks = sorted(int(k) for k in cv)
    ac = [cv[str(k)]["acierto_eleccion"] for k in ks]
    te = [cv[str(k)]["techo_hit@k"] for k in ks]
    cis = [tuple(cv[str(k)]["ic95"]) for k in ks]
    kf, ka = D["k_flujo"], D["k_antes"]
    d35 = cv[str(kf)]["acierto_eleccion"] - cv[str(ka)]["acierto_eleccion"]
    d58 = cv["8"]["acierto_eleccion"] - cv[str(kf)]["acierto_eleccion"]
    res = (ley((AZUL, "acierto de la elección, IC 95%"), (GRIS, "techo: el anotado está entre los k"))
           + line_chart([dict(name="acierto", ys=ac, kind="main", ci=cis, label="acierto"),
                         dict(name="techo", ys=te, kind="alt", dash=True, label="techo")],
                        ks, width=1120, height=500, ymin=0.4, ymax=1.0, yticks=[.4, .6, .8, 1.0],
                        marks=[(ka, "antes"), (kf, "el flujo")], xlab="k: candidatos por pieza", right=130))
    exp("E8", 4, "¿Cuántos candidatos le mostramos <em>a choose?</em>",
        "<p>Choose mira k fotos por pieza. Con más candidatos es más probable que esté el correcto…</p>"
        "<p>…pero son más imágenes por llamada: más costo, más latencia, más con qué confundirse.</p>",
        "<p>Sin gastar de nuevo: del reranking de Opus sobre el top-10 sale qué elegiría entre los primeros "
        "k. Lo comparamos con el <strong>techo</strong>: que el anotado esté entre los k.</p>",
        res,
        f"<strong>k = {kf}</strong> (antes, {ka}). De {ka} a {kf} suma {f(d35)} de acierto; de {kf} a 8, "
        f"{f(d58)}, con un {pct(8 / kf - 1)} más de fotos en cada llamada.",
        t=45, notas=[
            "¿Cuántos candidatos le mostramos a choose? Más candidatos, más chance de que esté el correcto, "
            "pero más fotos por llamada: más costo, más latencia y más con qué confundirse.",
            "[paso] No hizo falta gastar de nuevo: del reranking de Opus sobre el top-10 sale qué elegiría "
            "entre los primeros k. Lo comparamos con el techo, que el correcto esté entre los k.",
            f"[paso] El techo sube rápido, pero el acierto real se aplana: de {ka} a {kf} candidatos suma "
            f"{f(d35)}; de {kf} a 8, {f(d58)}.",
            f"[paso] Pasamos de {ka} a {kf}. Más allá, el costo crece más que el acierto.",
        ])

    # ================================================================ 05 · cuánto creerle
    separador(5, ["Tercer capítulo: cuánto creerle a todo esto. Se prende la lámpara."])

    # ---------------------------------------------------------------- E9
    rp = D["repro"]
    rrows = [dict(label=r["label"], h=r["h"], mean=r["mean"], sd=r["sd"]) for r in rp if r["mean"] > 0.3]
    nv = next(r for r in rp if r["mean"] <= 0.3)
    q = rp[0]
    res = ('<div class="ley" data-desde="1"><span>hit@1 en cada una de las tres escrituras · la raya es la media, la banda ± un desvío</span></div>'
           + dots_repro(rrows, width=1140, label_w=340, row_h=96, xmin=0.44, xmax=0.60,
                        ticks=[.44, .48, .52, .56, .60], tick_d=2, right=200)
           + f'<p class="nota" data-desde="2">Fuera de escala: {esc(nv["label"])}, {f(nv["mean"])} ± {f(nv["sd"])}. '
             f'Búsquedas con respuesta en cada escritura: {", ".join(str(n) for n in D["repro_n"])}.</p>')
    exp("E9", 5, "Si otro escribe las consultas, <em>¿cambia el resultado?</em>",
        "<p>Las consultas de la evaluación las escribieron subagentes de Claude. Otro redactor escribiría "
        "otras.</p><p>Si el orden de los métodos depende de una redacción, las conclusiones no valen.</p>",
        f"<p>Tres escrituras independientes de todas las consultas, mismo prompt y mismas fotos, catálogo de "
        f"{D['repro_catalogo']}. Cinco métodos en cada una.</p>",
        res,
        f"<strong>Las conclusiones se sostienen.</strong> El mejor método da {f(q['mean'])} ± {f(q['sd'])} y "
        f"le gana a BGE, a hashing y al filtro por kind en las tres. Diferencias de menos de ~{f(q['sd'], 2)} "
        f"entre métodos las tratamos como empate.",
        t=45, notas=[
            "Reproducibilidad. Las consultas las escribieron subagentes de Claude; otro redactor escribiría "
            "otras. Si el ranking de métodos depende de una redacción, no vale.",
            "[paso] Hicimos escribir todas las consultas tres veces, de forma independiente, y corrimos cinco "
            "métodos en cada escritura.",
            f"[paso] El mejor método da {f(q['mean'])} más menos {f(q['sd'])}. El orden se mantiene en las "
            f"tres: Qwen3 con filtro por tipo arriba, el texto del vendedor abajo de todo.",
            "[paso] Conclusión: el orden es firme, pero diferencias de dos o tres centésimas entre métodos son "
            "ruido de redacción. Por eso varias «mejoras» las tratamos como empate.",
        ])

    # ---------------------------------------------------------------- E10
    g = D["grad"]["consultas"]
    ag = D["grad"]["acuerdo_con_gt"]
    sin = 1 - D["n_resp"] / D["n_busquedas"]
    rows = [dict(label="hit@1 exacto", value=D["h1_855"], kind="ink", sub="el SKU anotado, primero"),
            dict(label="útil@1, todas", value=g["todas"]["util1"], ci=tuple(g["todas"]["util1_ic95"]), kind="main",
                 sub="el primero tiene nota ≥ 1"),
            dict(label="útil@3, todas", value=g["todas"]["util3"], ci=tuple(g["todas"]["util3_ic95"]), kind="main",
                 sub="alguno de los tres tiene nota ≥ 1"),
            dict(label="útil@1, sin el exacto", value=g["sin anotado"]["util1"], ci=tuple(g["sin anotado"]["util1_ic95"]),
                 kind="alt", sub="el producto no está en el catálogo"),
            dict(label="útil@3, sin el exacto", value=g["sin anotado"]["util3"], ci=tuple(g["sin anotado"]["util3_ic95"]),
                 kind="alt")]
    res = (ley(nota=f"proporción de búsquedas · IC 95% · catálogo de {D['grad_catalogo']}")
           + hbars(rows, width=1150, label_w=400, row_h=78, bar_h=26, x_max=1.0)
           + f'<p class="nota" data-desde="2"><b>¿Se le puede creer al juez?</b> Le pone 2 al producto anotado en el '
             f'{pct(ag["anotado_con_2"])} de los casos, y a los demás en el {pct(ag["otros_con_2"])}. NDCG@3 graduado: '
             f'{f(g["todas"]["ndcg3"])}.</p>')
    exp("E10", 5, "¿Sirve lo que trae, <em>aunque no sea el producto exacto?</em>",
        f"<p>hit@k solo cuenta el SKU anotado. Si el sofá correcto no está, uno muy parecido igual sirve.</p>"
        f"<p>Y el {pct(sin)} de las búsquedas no tiene su producto en el catálogo: hit@k no las puede medir.</p>",
        f"<p>Un juez LLM mira la foto y los tres primeros, sin saber cuál es el anotado: <strong>2</strong> el "
        f"mismo o indistinguible, <strong>1</strong> alternativa aceptable, <strong>0</strong> no sirve. "
        f"{g['todas']['n']} búsquedas al azar, {g['sin anotado']['n']} sin el producto en el catálogo.</p>",
        res,
        f"<strong>hit@1 subestima lo útil.</strong> El primero sirve en el {pct(g['todas']['util1'])} de los "
        f"casos, y en el {pct(g['sin anotado']['util1'])} cuando el exacto no existe. El juez complementa a "
        f"hit@k; no lo reemplaza.",
        t=45, notas=[
            "Relevancia graduada. hit@k solo cuenta el producto exacto; si el sofá anotado no está, uno muy "
            "parecido le sirve igual al usuario. Y más de un tercio de las búsquedas no tiene su producto en "
            "el catálogo.",
            f"[paso] Un juez LLM mira la foto del ambiente y los tres primeros, sin saber cuál es el anotado, "
            f"y les pone 2, 1 o 0. Son {g['todas']['n']} búsquedas al azar: {g['con anotado']['n']} con el "
            f"producto en el catálogo y {g['sin anotado']['n']} sin. Esto es el context precision de RAGAS en "
            f"su versión sin ground truth, y el NDCG graduado de la clase.",
            f"[paso] El primero sirve en el {pct(g['todas']['util1'])} de los casos, contra un hit@1 exacto de "
            f"{f(D['h1_855'], 2)}. Y sin el producto en el catálogo, igual en el "
            f"{pct(g['sin anotado']['util1'])}. Validamos al juez: le pone 2 al anotado en el "
            f"{pct(ag['anotado_con_2'])} y a los demás en el {pct(ag['otros_con_2'])}.",
            "[paso] hit@1 es una cota inferior de lo útil. Usamos el juez como complemento, validado contra "
            "las anotaciones.",
        ])

    # ---------------------------------------------------------------- E11
    trs = ""
    for r in D["ragas"]:
        fa, rl = r["fidelidad"], r["relevancia"]
        trs += (f'<div class="rg-l">{esc(r["label"])}</div>'
                f'<div class="rg-b"><div class="rbar"><i style="width:{fa["faithfulness"] * 100:.1f}%"></i></div>'
                f'<span class="rv">{f(fa["faithfulness"], 2)}</span><span class="rn">{fa["afirmaciones"]} afirm.</span></div>'
                f'<div class="rg-b"><div class="rbar"><i style="width:{rl["answer_relevance"] * 100:.1f}%"></i>'
                f'<em class="vara" style="left:{rl["vara_contrastes"] * 100:.1f}%"></em></div>'
                f'<span class="rv">{f(rl["answer_relevance"], 2)}</span><span class="rn">vara {f(rl["vara_contrastes"], 2)}</span></div>')
    bad = D["ragas"][0]["fidelidad"]["no_sostenidas"]
    res = ('<div class="rg" data-desde="1"><div class="rg-h">respuesta</div><div class="rg-h">faithfulness</div>'
           f'<div class="rg-h">answer relevance</div><div class="rg-res" data-desde="2">{trs}</div></div>'
           '<p class="nota" data-desde="2">La raya roja es la vara: el mismo coseno contra pedidos sin relación.</p>'
           '<div class="rq" data-desde="2"><div class="etq">lo que no se sostiene · living, vista 1</div>'
           + "".join(f'<p class="cita">«{esc(x)}»</p>' for x in bad) + "</div>")
    exp("E11", 5, "¿La respuesta inventa, <em>o responde lo que se pidió?</em>",
        "<p>Choose explica cada elección. Una explicación que afirma algo falso, una medida o un material, es "
        "una alucinación que el usuario va a creer.</p>",
        "<p>Dos métricas de RAGAS, con un juez, sobre cuatro respuestas del flujo:</p><ul>"
        "<li><strong>faithfulness:</strong> qué fracción de las afirmaciones se sostiene con lo que vio el "
        "sistema;</li><li><strong>answer relevance:</strong> el juez, sin ver el pedido, escribe tres pedidos "
        "que esa respuesta contesta; coseno con el original.</li></ul>",
        res,
        "<strong>El porqué es fiel; lo que falla son medidas.</strong> Lo no sostenido son tamaños que el "
        "catálogo no tiene: los asientos de IKEA no traen medidas. Eso nos llevó a buscar otro catálogo.",
        t=50, notas=[
            "RAGAS sobre la respuesta. Choose explica cada elección; si afirma una medida o un material "
            "falso, es una alucinación que el usuario se va a creer. Y la lista entera tiene que contestar el "
            "pedido, no solo cada pieza.",
            "[paso] Medimos dos cosas con un juez. Faithfulness: se parte la explicación en afirmaciones y se "
            "cuenta qué fracción se sostiene con lo que vio el sistema. Answer relevance: el juez, sin ver el "
            "pedido, escribe tres pedidos que esa respuesta contestaría, y medimos el coseno con el original. "
            "La vara es el mismo coseno contra pedidos que no tienen nada que ver.",
            f"[paso] Faithfulness entre {f(min(r['fidelidad']['faithfulness'] for r in D['ragas']), 2)} y "
            f"{f(max(r['fidelidad']['faithfulness'] for r in D['ragas']), 2)}; answer relevance muy por encima "
            f"de la vara. Lo interesante es qué no se sostiene: que el piso es de roble, que la alfombra llega "
            f"abajo del sofá. Son medidas y cosas que el catálogo no dice.",
            "[paso] El modelo no inventa productos; lo que le falta es información. Los asientos de IKEA no "
            "tienen medidas en el dataset, y eso nos llevó al último capítulo: otro catálogo.",
        ])

    # ================================================================ 06 · de punta a punta
    separador(6, ["Último capítulo de experimentos: de punta a punta, en ambientes vacíos reales. Cortinas y planta."])
    e12(D)
    e13(D)
    replica_slides(D)
    t4(D)


# ---------------------------------------------------------------- E12

LAB12 = {"caballito-living": "living", "caballito-comedor": "comedor", "alvear-escritorio": "escritorio",
         "alvear-living-comedor": "living comedor", "experimento-lectura": "lectura",
         "publica-loft-industrial": "loft industrial", "publica-living-clasico": "clásico",
         "publica-comedor-clasico-moderno": "comedor clásico", "publica-living-japandi": "japandi",
         "publica-living-bohemio": "bohemio", "publica-estudio-sobrio": "estudio sobrio"}


def credito(D, foto: str) -> str:
    c = D["publicas"][foto.split("/")[-1]]
    return f"{c['autor']}, {c['licencia']}"


def e12(D):
    b = D["best"]
    jg, j11 = D["j_grupos"], D["j_todos11"]
    # ---- diseño
    body = (xcab("E12", "De punta a punta", "¿Alcanza con IKEA, <em>o hace falta otro catálogo?</em>")
            + '<div class="e12a"><div class="xl">'
            + bloque("por qué",
                     f"<p>El catálogo de IKEA del dataset es de un solo estilo, y sus asientos <strong>no tienen "
                     f"medidas</strong>. E11 mostró que lo que falla son justamente medidas.</p>"
                     f"<p><strong>Amazon Berkeley Objects</strong>: publicaciones reales de Amazon, de muchos "
                     f"estilos. Describimos {D['n_abo']} productos con las mismas ocho líneas.</p>")
            + '<div class="cmp"><div></div><div class="ch">IKEA</div><div class="ch">ABO</div>'
            f'<div class="cl">productos</div><div class="cv">{D["n_ikea"]}</div><div class="cv">{D["n_abo"]}</div>'
            f'<div class="cl">con medidas</div><div class="cv">asientos: {pct(1 - D["ikea_asientos_sin_medidas"])}</div><div class="cv">{pct(D["abo_con_medidas"])}*</div>'
            f'<div class="cl">ground truth</div><div class="cv">sí</div><div class="cv">no</div></div>'
            '<p class="nota" style="margin-top:6px">* sobre todos los productos de ABO descriptos</p>'
            '</div><div class="xl" data-desde="1">'
            + bloque("qué hicimos",
                     f"<p>Sin ground truth, de punta a punta: {j11['ambientes']} ambientes vacíos reales "
                     f"({jg['propios']['n']} propios, con pedidos nórdicos; {jg['publicos']['n']} fotos públicas, "
                     f"con otros estilos). El flujo con cada catálogo y un juez que compara las dos listas:</p>")
            + '<div class="juez"><div class="jrow"><span class="jo">orden 1</span><span class="jb">A · IKEA</span>'
              '<span class="jb t">B · IKEA + ABO</span><span class="jv">→ voto</span></div>'
              '<div class="jrow"><span class="jo">orden 2</span><span class="jb t">A · IKEA + ABO</span>'
              '<span class="jb">B · IKEA</span><span class="jv">→ voto</span></div>'
              '<p>Opus ve la foto, el pedido y las fotos de las dos listas. <strong>Una lista gana solo si gana en '
              'los dos órdenes</strong>; si no, empate.</p></div>'
            + '<dl class="defs"><dt>sesgo de posición</dt><dd>fracción de votos para la lista que va primera; 0,5 es sin sesgo</dd>'
              '<dt>acuerdo entre órdenes</dt><dd>fracción de ambientes donde los dos votos coinciden</dd>'
              '<dt>cumple</dt><dd>fracción de productos con nota 2 del juez: lo pedido, y va con el cuarto</dd></dl>'
            + '</div></div>')
    add(body, titulo="E12 · Qué catálogo (diseño)", cap=6, t=50, fases="0,1", notas=[
        f"¿Alcanza con IKEA? El catálogo del dataset es de un solo estilo, y sus asientos no tienen medidas: "
        f"ninguno. E11 nos mostró que lo que falla son justamente medidas. Amazon Berkeley Objects son "
        f"publicaciones reales de Amazon, de muchos estilos y casi todas con medidas. Describimos {D['n_abo']} "
        f"productos con las mismas ocho líneas.",
        f"[paso] Acá no hay ground truth, así que lo medimos de punta a punta: {j11['ambientes']} ambientes "
        f"vacíos reales, cinco nuestros con pedidos nórdicos y seis fotos públicas con pedidos de otros "
        f"estilos. Corremos el flujo con cada catálogo y un juez compara las dos listas. Como los LLM tienden "
        f"a preferir la primera opción, se pregunta en los dos órdenes, y una lista gana solo si gana en los "
        f"dos. Medimos también el sesgo de posición y el acuerdo entre órdenes.",
    ])

    # ---- resultados
    det = {x["slug"]: x for x in j11["detalle"]}
    orden = ["caballito-living", "caballito-comedor", "alvear-escritorio", "alvear-living-comedor", "experimento-lectura"]
    slugs = orden + [s for s in det if s.startswith("publica")]
    cells = ""
    for s in slugs:
        x = det[s]
        ph = D["pedidos"][s]["foto"]
        votos = "".join(f'<i class="{"vt" if v == "todos" else "vi" if v == "ikea" else "ve"}"></i>' for v in x["votos"])
        w = {"todos": "IKEA+ABO", "ikea": "IKEA", "tie": "empate"}[x["ganador"]]
        cells += (f'<div class="jr{" pub" if s.startswith("publica") else ""}"><div class="th"><img src="{img.uri(ph, 300, 225, q=70)}" alt=""></div>'
                  f'<div class="nm">{LAB12.get(s, s)}</div><div class="v" data-desde="1">{votos}<b class="{"t" if x["ganador"] == "todos" else ""}">{w}</b></div></div>')
    pubs = [s for s in slugs if s.startswith("publica")]
    cred = "; ".join(f"{LAB12[s]}: {credito(D, D['pedidos'][s]['foto'])}" for s in pubs)
    P, U = jg["propios"], jg["publicos"]
    ja = D["j_abo5"]["resumen"]
    body = (xcab("E12", "De punta a punta", "IKEA contra IKEA + ABO, <em>en once cuartos reales</em>")
            + '<div class="e12b">'
            + '<div class="ley"><span><i style="background:#9AA4AF"></i>votó IKEA</span><span><i style="background:#2453D6"></i>votó IKEA + ABO</span>'
              '<span>un punto por orden</span></div>'
            + f'<div class="jg"><div class="jgk"><span>departamentos propios · pedidos nórdicos</span><span>fotos públicas · otros estilos</span></div>{cells}</div>'
            + f'<p class="credito">Fotos públicas (Wikimedia Commons / Flickr): {esc(cred)}.</p>'
            + '<div class="e12g" data-desde="1">'
            + f'<div class="cc"><div class="etq">propios · nórdicos</div><p class="ccn">{P["gana_ikea"]} · {P["empates"]} · {P["gana_todos"]}</p>'
              f'<p>IKEA · empate · IKEA+ABO<br>cumple: {f(P["util_ikea"])} contra {f(P["util_todos"])}</p></div>'
            + f'<div class="cc hi"><div class="etq">públicas · otros estilos</div><p class="ccn">{U["gana_todos"]} a {U["gana_ikea"]}</p>'
              f'<p>para IKEA+ABO<br>cumple: de {f(U["util_ikea"])} a <strong>{f(U["util_todos"])}</strong></p></div>'
            + f'<div class="cc"><div class="etq">y además</div><p>ABO solo contra IKEA, en los 5 propios: IKEA {ja["ikea"]["gana"]}, ABO {ja["abo"]["gana"]}.</p>'
              f'<p>Con ABO como distractor, hit@1 sobre el ground truth de IKEA: {f(b["hit@1"])} → {f(D["todos_ret"]["hit@1"])}.</p>'
              f'<p>Acuerdo entre órdenes {f(j11["acuerdo_entre_ordenes"], 2)} · votos a la posición A {f(j11["votos_por_posicion_A"], 2)}.</p></div>'
            + '</div></div>'
            + f'<div class="decision" data-desde="2"><div class="k">decisión</div><p><strong>IKEA + ABO en el flujo.</strong> '
              f'Empata en los pedidos nórdicos, gana {U["gana_todos"]} a {U["gana_ikea"]} en los demás estilos y, como '
              f'distractor, casi no mueve el retrieval. Las evaluaciones con ground truth siguen siendo solo IKEA.</p></div>')
    add(body, titulo="E12 · Resultados", cap=6, t=55, fases="2,2,3", notas=[
        "Los resultados. Cada columna es un ambiente: los cinco primeros son departamentos propios, los seis "
        "siguientes fotos públicas.",
        f"[paso] Con los dos votos del juez: en los propios, con pedidos nórdicos, IKEA solo e IKEA más ABO "
        f"empatan: {P['gana_ikea']} a {P['gana_todos']} con un empate. En las seis fotos públicas, con pedidos "
        f"industrial, clásico, bohemio, gana IKEA más ABO {U['gana_todos']} a {U['gana_ikea']}, y la fracción "
        f"de productos que cumplen sube de {f(U['util_ikea'], 2)} a {f(U['util_todos'], 2)}. Además, ABO solo "
        f"pierde contra IKEA en los cuartos nórdicos, y sumar ABO como distractor casi no cambia el retrieval "
        f"sobre el ground truth de IKEA. El juez coincide consigo mismo en los dos órdenes en el "
        f"{pct(j11['acuerdo_entre_ordenes'])} de los casos.",
        "[paso] Decisión: el flujo usa los dos catálogos. Lo que no cambia: las métricas con ground truth se "
        "siguen calculando solo sobre IKEA.",
    ])

    # ---- un caso
    lx = det["publica-loft-industrial"]
    lph = D["pedidos"]["publica-loft-industrial"]["foto"]

    def lista(cat):
        grs = [s["grades"] for s in lx["puntajes"][cat]]
        out = ""
        for i, p in enumerate(lx["listas"][cat]):
            it = D["abo_items"].get(p["id"]) if p["id"].startswith("abo-") else D["items"].get(p["id"])
            kd = (it or {}).get("kind", "")
            out += ficha(D, p["id"], 100, titulo=KIND_ES.get(kd, kd or p["type"]), sub="ABO" if p["id"].startswith("abo-") else "IKEA",
                         cant=p.get("units"), notas=[gg[i] for gg in grs if i < len(gg)])
        return out

    body = (xcab("E12", "De punta a punta", "Un caso: <em>el loft industrial</em>")
            + '<div class="loft"><div class="lfl">'
            + f'<div class="foto" style="width:500px;height:375px"><img src="{img.uri(lph, 1000, 750, q=74)}" alt=""></div>'
            + f'<p class="pie-foto">Foto: {esc(credito(D, lph))}</p>'
            + f'<p class="cita pedido">«{esc(D["pedidos"]["publica-loft-industrial"]["pedido"])}»</p></div>'
            + '<div class="lfr">'
            + f'<div class="etq">IKEA solo</div><div class="tira lst">{lista("ikea")}</div>'
            + f'<div class="etq" style="margin-top:20px;color:var(--cobalto)">IKEA + ABO · ganó en los dos órdenes</div><div class="tira lst">{lista("todos")}</div>'
            + '<div class="gley"><span><i class="g2"></i>2 cumple</span><span><i class="g1"></i>1 aceptable</span><span><i class="g0"></i>0 no sirve</span>'
              '<span>una barra por orden</span></div>'
            + f'<p class="cita porque">«{esc(lx["por_que"][1])}»</p><p class="nota">el porqué del juez, en el orden 2 (A = IKEA + ABO)</p>'
            + '</div></div>')
    add(body, titulo="E12 · Un caso", cap=6, t=20, fases="2", notas=[
        "Un caso para ver qué está mirando el juez: un loft con vigas y un pedido industrial, sofá de cuero "
        "envejecido, mesa de madera con patas de metal negro, biblioteca de metal y madera.",
        "IKEA solo no tiene esos productos y propone lo más cercano: un sofá de cuero liso, una mesa toda de "
        "madera, un estante de vidrio. Con ABO aparecen el sofá de cuero coñac, la mesa industrial y la "
        "biblioteca. Las barritas son la nota del juez a cada producto, en cada orden.",
    ])


# ---------------------------------------------------------------- E13

def e13(D):
    cl = D["img"]["caballito-living"]
    cm = cl["met"]
    prods = [p for p in cm["productos"] if p.get("detectado")]
    final_cl = A / "caballito-living" / "final.png"
    pairs = ""
    for p in [x for x in prods if x["id"] in ("190.114.33", "202.080.42", "602.740.06")]:
        pairs += (f'<div class="par"><img src="{img.uri(D["items"][p["id"]]["photos"][0], 200, 200, q=80, fit="contain")}" alt="">'
                  f'<img src="{img.crop(final_cl, p["box"], 200, 200)}" alt="">'
                  f'<span>{KIND_ES.get(p["kind"], p["kind"])}: {p["puesto"]}.º de {p["entre"]}</span></div>')
    ri = D["ref_ikea"]
    mask = img.ssim_mask(Path("datos/resultados/amoblar/caballito-living/final.png"), [p["box"] for p in prods])
    pair, _ = img.sift_pair(Path("datos/resultados/amoblar/caballito-living/room.jpg"), final_cl)
    body = ('<div class="cuerpo">' + cab("06", "De punta a punta · E13", "Cómo medimos una imagen, <em>sin ground truth</em>") + '</div>'
            + '<div class="imet">'
            + '<div class="im"><div class="imn"><i>1</i>SSIM fuera de los muebles</div><p>Similitud estructural entre la foto original y la '
              'generada, <strong>solo fuera de las cajas de los muebles</strong>. 1 es idéntico: el cuarto se preservó.</p>'
              f'<img class="imf" src="{img.uri(mask, 760, 570, q=74)}" alt=""><p class="nota">lo rayado no cuenta · el living de la portada</p></div>'
            + '<div class="im" data-desde="1"><div class="imn"><i>2</i>SIFT + RANSAC</div><p>¿Cuántos puntos de la foto original se reencuentran '
              'en la generada con una homografía consistente, y cuánto se movieron?</p>'
              f'<img class="imf" src="{img.uri(pair, 1000, None, q=74)}" alt="">'
              f'<p class="nota">{cm["ambiente"]["sift_inliers"]} inliers · control del flujo: ≥ {D["sift_min_inliers"]} inliers y '
              f'desplazamiento ≤ {pct(D["sift_max_shift"])} del ancho, hasta {D["sift_attempts"]} intentos</p></div>'
            + '<div class="im" data-desde="2"><div class="imn"><i>3</i>Fidelidad de producto</div><p>Grounding DINO detecta cada mueble; DINOv3 '
              'compara el recorte con todas las fotos del catálogo de su tipo. ¿El de la lista sale primero?</p>'
              f'<div class="pares">{pairs}</div><p class="nota">vara: con fotos reales de IKEA, identificados@1 = {f(ri["hit@1"])}</p></div>'
            + '<div class="im" data-desde="3"><div class="imn"><i>4</i>Pedido ↔ imagen</div><p>SigLIP 2 mide la alineación entre el texto del '
              'pedido y la imagen: cuánto sube respecto de la foto vacía, y en qué puesto queda el pedido real entre pedidos de contraste.</p>'
              '</div>'
            + '</div>'
            + remate("Las cuatro corren <mark>local y gratis</mark>: se pueden calcular en cada corrida del flujo.", desde=3))
    add(body, titulo="E13 · Métricas de imagen", cap=6, t=40, notas=[
        "Para la imagen no hay ground truth, así que armamos métricas que comparan contra lo que sí tenemos: "
        "la foto original y las fotos del catálogo.",
        "**SSIM** fuera de los muebles: la similitud estructural, luz, contraste y textura por ventanas, entre "
        "la foto original y la generada, solo donde no hay muebles. Si da cerca de uno, el cuarto se preservó.",
        f"[paso] **SIFT con RANSAC**: buscamos puntos característicos de la foto original en la generada. Si "
        f"la cámara se movió o el cuarto cambió, se reencuentran pocos y se desplazan. Con esto armamos el "
        f"control automático: al menos {D['sift_min_inliers']} inliers y un desplazamiento de a lo sumo el "
        f"{pct(D['sift_max_shift'])} del ancho.",
        f"[paso] **Fidelidad de producto**: detectamos cada mueble, recortamos y vemos si el más parecido del "
        f"catálogo es el de la lista. Como vara, con fotos reales de IKEA esto da {f(ri['hit@1'])}: es difícil "
        f"incluso con fotos de verdad.",
        "[paso] Y SigLIP 2 para ver si la imagen se alinea con el pedido. Todas corren local y gratis.",
    ])

    # ---- el prompt de la escena
    def tile(run, cap):
        m = D["img"][run]["met"]["ambiente"]
        bad = m["sift_desplazamiento_mediano"] > D["sift_max_shift"] or m["sift_inliers"] < D["sift_min_inliers"]
        sello = '<span class="sello">cambió el cuarto</span>' if bad else ""
        return (f'<figure class="vt"><div class="vi"><img src="{img.uri(A / run / "final.png", 660, 440, q=72)}" alt="">{sello}</div>'
                f'<figcaption><b>{cap}</b><span>SSIM {f(m["ssim_fuera_de_los_muebles"], 2)} · SIFT {pct(m["sift_reencontrados"], 1)} · '
                f'despl. {pct(m["sift_desplazamiento_mediano"], 2)}</span></figcaption></figure>')

    orig = img.uri(A / "experimento" / "room.jpg", 660, 440, q=72)
    ex_a = D["img"]["experimento"]["choice"]["answer"]["choices"]
    ex_b = D["img"]["experimento-buen-pedido"]["choice"]["answer"]["choices"]
    res = ('<div class="vgrid">'
           f'<figure class="vt" data-desde="1"><div class="vi"><img src="{orig}" alt=""></div><figcaption><b>la foto · pedido corto</b>'
           f'<span>{len(ex_a)} productos · foto de un integrante</span></figcaption></figure>'
           f'<div class="vr" data-desde="2">{tile("experimento", "(a) el LLM escribe la escena")}{tile("experimento-libre", "(b) edición libre")}</div>'
           f'<figure class="vt" data-desde="1"><div class="vi"><img src="{orig}" alt=""></div><figcaption><b>la misma foto · pedido detallado</b>'
           f'<span>{len(ex_b)} productos</span></figcaption></figure>'
           f'<div class="vr" data-desde="2">{tile("experimento-buen-pedido", "(c) edición libre")}{tile("experimento-buen-pedido-estricto", "(d) edición estricta")}</div>'
           '</div>')
    mb = D["img"]["experimento-buen-pedido"]["met"]["ambiente"]
    ms = D["img"]["experimento-buen-pedido-estricto"]["met"]["ambiente"]
    exp("E13", 6, "¿Cómo pedimos la imagen <em>para que no cambie el cuarto?</em>",
        "<p>El modelo de imagen tiende a «mejorar» la foto: mueve la cámara, agranda ventanas, repinta. El "
        "usuario compraría para un cuarto que no es el suyo.</p>",
        "<p>Misma foto, misma lista; cambia solo el pedido de edición:</p><ul><li>(a) Claude escribe la escena;</li>"
        "<li>(b, c) template de edición libre;</li><li>(d) edición estricta: «el mismo cuarto, exactamente».</li></ul>"
        "<p>Una imagen por variante.</p>",
        res,
        f"<strong>Edición estricta, sin LLM, y un control automático.</strong> Con {len(ex_b)} productos la "
        f"edición libre cambió el cuarto (SSIM {f(mb['ssim_fuera_de_los_muebles'], 2)}); la estricta lo "
        f"preservó ({f(ms['ssim_fuera_de_los_muebles'], 2)}). Una imagen por variante es una anécdota: por eso "
        f"el control en cada corrida.",
        t=60, ancho=True, rot="De punta a punta", notas=[
            "La imagen. El modelo tiende a «mejorar» la foto: mueve la cámara, agranda ventanas, repinta. Para "
            "el usuario es grave, porque compraría para un cuarto que no es el suyo.",
            "[paso] Probamos distintas formas de pedir la edición, siempre con la misma foto y la misma lista: "
            "que Claude escriba la escena, un template de edición libre, y uno de edición estricta. Ojo: una "
            "imagen por variante.",
            f"[paso] Con el pedido corto, las dos primeras preservan el cuarto parecido. Con el pedido detallado "
            f"y {len(ex_b)} productos, la edición libre lo cambió: el SSIM fuera de los muebles cae a "
            f"{f(mb['ssim_fuera_de_los_muebles'], 2)} y SIFT ve la cámara movida. La estricta lo preserva.",
            "[paso] Elegimos edición estricta, sin LLM: más barata y más fiel. Pero una imagen por variante es "
            "una anécdota, así que además pusimos un control automático en cada corrida.",
        ])

    # ---- el control en acción
    cg = cl["gen"]
    tiles = (f'<figure class="at"><div class="ai"><img src="{img.uri(A / "caballito-living" / "room.jpg", 800, 600, q=72)}" alt=""></div>'
             '<figcaption><b>la foto original</b><span>living de un departamento propio</span></figcaption></figure>')
    for i, a in enumerate(cg["attempts"]):
        ok = a["ok"]
        tiles += (f'<figure class="at"><div class="ai"><img src="{img.uri(A / "caballito-living" / a["image"], 800, 600, q=72)}" alt="">'
                  f'<span class="sello{" ok" if ok else ""}">{"aceptada" if ok else "rechazada"}</span></div>'
                  f'<figcaption><b>intento {i + 1}</b><span>inliers {a["sift_inliers"]} · reencontrados {pct(a["sift_reencontrados"], 1)}</span>'
                  f'<span>desplazamiento {pct(a["sift_desplazamiento_mediano"], 1)}</span></figcaption></figure>')
    body = (xcab("E13", "De punta a punta", "El control, <em>en una corrida real</em>")
            + f'<div class="atts">{tiles}</div>'
            + f'<p class="nota atn">{len(cg["attempts"])} intentos · {usd(cg["cost_usd"])} de imagen · SSIM fuera de los muebles de la aceptada: '
              f'{f(cm["ambiente"]["ssim_fuera_de_los_muebles"], 3)}</p>'
            + f'<div class="decision" data-desde="1"><div class="k">decisión</div><p><strong>El control queda en el flujo:</strong> '
              f'inliers ≥ {D["sift_min_inliers"]} y desplazamiento ≤ {pct(D["sift_max_shift"])}, hasta {D["sift_attempts"]} intentos. '
              'Los dos rechazos se ven a ojo: el cuarto se dio vuelta. Dónde poner el umbral exacto es un experimento pendiente.</p></div>')
    add(body, titulo="E13 · El control en acción", cap=6, t=30, fases="2,3", notas=[
        "Y acá el control en una corrida real: el living de la portada. Los dos primeros intentos cambiaron el "
        "cuarto, la cámara se movió, y SIFT reencontró menos del 5% de los puntos con desplazamientos de más "
        "del 15%. Se rechazaron solos. El tercero preservó el cuarto y se aceptó. Por eso esa corrida tuvo "
        "tres intentos.",
        f"[paso] El control queda en el flujo, con hasta {D['sift_attempts']} intentos. Dónde poner el umbral "
        f"exacto es lo que sigue.",
    ])


# ---------------------------------------------------------------- T4

def t4(D):
    def md(s):
        return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(s))

    trs = "".join(f'<div class="t4c b">{esc(r[0])}</div><div class="t4c">{md(r[1])}</div><div class="t4c">{md(r[2])}</div>'
                  f'<div class="t4c m">{md(r[3])}</div><div class="t4c m">{md(r[4])}</div>' for r in D["t4"])
    jr = D.get("t4_jueces", ["", "", "", "", ""])
    trs += (f'<div class="t4c b"></div><div class="t4c">{md(jr[1])}</div><div class="t4c">{md(jr[2])}</div>'
            f'<div class="t4c m">{md(jr[3])}</div><div class="t4c m">{md(jr[4])}</div>')
    body = ('<div class="cuerpo">' + cab("06", "De punta a punta · T4", "Lo que sigue: <em>medir la imagen en serio</em>") + '</div>'
            + '<div class="t4tag"><span class="chip pend">diseñado, sin correr: no hay resultados</span>'
              '<span class="nota" style="margin:0">sobre los ambientes de pedidos.yaml, con la lista que eligió el flujo: solo cambia la imagen</span></div>'
            + '<div class="t4"><div class="t4h">exp.</div><div class="t4h">pregunta</div><div class="t4h">variantes</div>'
              f'<div class="t4h">imágenes</div><div class="t4h">costo estimado</div>{trs}</div>'
            + f'<p class="t4tot"><b>Total estimado:</b> {esc(D["t4_total"])} Métricas: las de E13 más un juez de a pares en los dos órdenes, como en E12.</p>')
    add(body, titulo="T4 · Lo que sigue", cap=6, t=20, notas=[
        "Lo que sigue, y lo decimos claro: esto está diseñado y no corrido, no hay resultados.",
        "La imagen la medimos con una imagen por variante. El plan es repetirlo bien, en todos los ambientes: "
        "escena escrita por el LLM contra edición estricta, qué modelo de imagen, qué resolución, si las fotos "
        "del catálogo cambian la fidelidad, y calibrar el umbral del control SIFT con todos esos intentos. Con "
        f"las métricas de E13 y un juez de a pares en los dos órdenes, como en E12. Cuesta {D['t4_total'].rstrip('.')}.",
    ])

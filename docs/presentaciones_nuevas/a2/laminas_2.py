"""Los experimentos, por su ranking (docs/REVISION.md, sección 4): el buscador (el mapa, E1 a E3, el
camino incremental y E4), la lista (E5 a E7), los de trámite (E8 y dos láminas con E9 a E14) y el
Ejercicio 4 (versión 1 y versión 2, en tres láminas). Cada experimento con lámina propia va en el
mismo orden: por qué → qué hicimos → resultados (con la diferencia pareada) → decisión."""

from __future__ import annotations

import statistics

import img
import laminas_rec
from base import (KIND_ES, add, bloque, cab, ci95, dif, esc, exp, f, ficha, foto_producto, ic, llamada, media_desvio,
                  miles, nb, pasos_x, pct, remate, sg, usd)
from datos_deck import BASE, CASO, EJ_PIECE, EJ_ROOM, V1, V2, p_signos, rankings
from graf import camino, dots_repro, hbars, line_chart
from laminas_1 import credito, creditos, separador

AZUL, GRIS, CLARO, TINTA = "#2453D6", "#9AA4AF", "#C9CFD5", "#13202C"
K_NAIVE = "qwen3|seller-full|filtro-none|consulta-piece"
K_DESC = "qwen3|description|filtro-none|consulta-piece"
K_HYDE = "qwen3|description|filtro-none"
LAB = {"caballito-living": "living", "caballito-comedor": "comedor", "alvear-escritorio": "escritorio",
       "alvear-living-comedor": "living comedor", "experimento-lectura": "lectura",
       "publica-loft-industrial": "loft industrial", "publica-living-clasico": "clásico",
       "publica-comedor-clasico-moderno": "comedor clásico", "publica-living-japandi": "japandi",
       "publica-living-bohemio": "bohemio", "publica-estudio-sobrio": "estudio sobrio"}


def ley(*items, nota="", desde=1):
    out = f'<div class="ley" data-desde="{desde}">'
    for col, txt in items:
        out += f'<span><i style="background:{col}"></i>{txt}</span>'
    if nota:
        out += f"<span>{nota}</span>"
    return out + "</div>"


def xcab(num, rot, titulo):
    return (f'<div class="cuerpo"><div class="xcab">{llamada(num, rot)}{pasos_x()}</div>'
            f'<h2 class="t xt">{titulo}</h2></div>')


def tira_votos(D, det: list[dict], gana: str, nombres: dict, desde=1) -> str:
    """Los ambientes de una comparación de punta a punta: la foto, y un punto por cada orden del
    juez (lleno: votó `gana`; gris: votó la otra; hueco: empate)."""
    cells = ""
    for x in det:
        s = x["slug"]
        votos = "".join(f'<i class="{"vt" if v == gana else "ve" if v == "tie" else "vi"}"></i>' for v in x["votos"])
        w = nombres.get(x["ganador"], "empate")
        cells += (f'<div class="jr{" pub" if s.startswith("publica") else ""}"><div class="th"><img src="{img.uri(D["pedidos"][s]["foto"], 300, 225, q=70)}" alt=""></div>'
                  f'<div class="nm">{LAB.get(s, s)}</div><div class="v" data-desde="{desde}">{votos}<b class="{"t" if x["ganador"] == gana else ""}">{w}</b></div></div>')
    return cells


def micro(rows, xmax: float = 0.8) -> str:
    """Barras chicas para una fila de trámite. rows: (rótulo, valor para la barra, texto, elegido)."""
    return '<div class="mb">' + "".join(
        f'<div class="mbr{" hi" if hi else ""}"><span>{esc(lab)}</span><i><em style="width:{min(1.0, v / xmax) * 100:.1f}%"></em></i><b>{txt}</b></div>'
        for lab, v, txt, hi in rows) + "</div>"


def build(D: dict, ctx: dict) -> None:
    CAM, CON, HIB, EMB, ABL = D["CAM"], D["CON"], D["HIB"], D["EMB"], D["ABL"]
    B1, B2, D21 = D["B1"], D["B2"], D["D21"]
    N_ANS = D["N_ANS"]
    kf = D["cfg"].furnish.candidates

    # ================================================================ 03 · el buscador
    separador(3, ["Ahora los experimentos, por cuánto importan. Los que sostienen una decisión tienen su lámina; "
                  "los de trámite van juntos. Llega el mueble de la tele."])
    laminas_rec.mapa(D)

    # ---------------------------------------------------------------- E1 · qué se indexa
    n1, n2 = CAM[K_NAIVE], CAM[K_DESC]
    d_idx = n2["vs_anterior"]
    sf, df = ABL["qwen3|seller|filtro-none"], ABL["qwen3|description|filtro-none"]
    d_ficha, d_name = D["d_ficha"], D["d_name"]
    rows = [dict(label="texto del vendedor", sub="hit@1", value=n1["hit@1"], ci=ci95(n1), kind="alt"),
            dict(label="nuestra descripción", sub="hit@1", value=n2["hit@1"], ci=ci95(n2), kind="main", nota=dif(d_idx)),
            dict(label="texto del vendedor", sub="hit@5", value=n1["hit@5"], ci=ci95(n1, "hit@5"), kind="alt"),
            dict(label="nuestra descripción", sub="hit@5", value=n2["hit@5"], ci=ci95(n2, "hit@5"), kind="main", nota=dif(d_idx, "hit@5"))]
    res = (ley((GRIS, "texto del vendedor"), (AZUL, "descripción desde la foto"), nota=f"IC 95% · {N_ANS} consultas")
           + hbars(rows, width=1150, label_w=300, row_h=84, bar_h=28, x_max=0.8, ticks=[0, .2, .4, .6, .8], right=350,
                   gaps=(2,), nota_t="diferencia pareada · IC 95%")
           + f'<p class="nota" data-desde="2">Con la consulta escrita como ficha la diferencia es mayor: de {f(sf["hit@1"])} a '
             f'<b>{f(df["hit@1"])}</b> ({sg(d_ficha["hit@1"], 2)}): los dos cambios se potencian. Con el nombre comercial '
             f'delante de la descripción, peor: {dif(d_name)}.</p>')
    exp("E1", 3, "¿Texto del vendedor, <em>o describir cada producto?</em>",
        "<p>El texto de IKEA es una frase de marketing, y un usuario pide <strong>estilo, color y materiales</strong>: "
        "cosas que están en la foto, no en el texto.</p>",
        "<p>Dos textos en el índice, con todo lo demás fijo:</p><ul>"
        "<li><strong>el del vendedor</strong>: nombre, su tipo, colores y la frase;</li>"
        "<li><strong>la descripción</strong> de ocho líneas, hecha desde la foto.</li></ul>"
        "<p>Qwen3, sin filtro, y la consulta en una frase corta sin reescribir: un solo cambio.</p>",
        res,
        f"<strong>Se indexa la descripción hecha desde la foto.</strong> Casi triplica el acierto ({dif(d_idx)} de hit@1). "
        f"Es el preprocesamiento que más pesa, y un costo único, offline: {usd(D['c_desc'], 3)} por producto.",
        t=50, planta=[2], notas=[
            "Experimento 1: qué se indexa. El texto de IKEA es una frase de marketing, y la gente pide estilo, "
            "color y materiales, que están en la foto. ¿Vale la pena describir cada producto?",
            "[paso] Indexamos dos textos, con todo lo demás fijo: el texto del vendedor y la descripción de ocho "
            "líneas. La consulta, una frase corta sin reescribir, para medir un solo cambio.",
            f"[paso] Con el texto del vendedor, hit@1 da {f(n1['hit@1'], 2)}; con la descripción, {f(n2['hit@1'], 2)}: "
            f"casi el triple, y hit@5 pasa de {f(n1['hit@5'], 2)} a {f(n2['hit@5'], 2)}. La diferencia es pareada y "
            f"su intervalo no toca el cero. Con la consulta escrita como ficha, la diferencia supera 0,4.",
            "[paso] Se indexa la descripción hecha desde la foto. Es el preprocesamiento que más pesa de todo el "
            "trabajo.",
        ])

    # ---------------------------------------------------------------- E2 · cómo se escribe la consulta
    q_full, q_piece = CON[V1], CON[V1 + "|consulta-piece"]
    q_type, q_kind = CON[V1 + "|consulta-type"], CON[V1 + "|consulta-kind"]
    s_full, s_piece = CON["siglip2|description|filtro-kind"], CON["siglip2|description|filtro-kind|consulta-piece"]
    d_q = q_piece["vs_base"]  # la frase natural menos la ficha
    frases = D["frases"]
    med = statistics.median(len(x.split()) for x in frases)
    rows = [dict(label="la ficha de 8 líneas", sub="densa · lo que escribe el plan", value=q_full["hit@1"], ci=ci95(q_full), kind="main",
                 nota=dif(d_q, flip=True)),
            dict(label="la frase natural", sub="densa · sin reescribir", value=q_piece["hit@1"], ci=ci95(q_piece), kind="alt"),
            dict(label="solo la línea Type", sub="densa", value=q_type["hit@1"], ci=ci95(q_type), kind="muted"),
            dict(label="solo el nombre del kind", sub="densa · el piso", value=q_kind["hit@1"], ci=ci95(q_kind), kind="muted"),
            dict(label="la ficha", sub="por foto · SigLIP 2", value=s_full["hit@1"], ci=ci95(s_full), kind="alt"),
            dict(label="la frase natural", sub="por foto · sin reescribir", value=s_piece["hit@1"], ci=ci95(s_piece), kind="main",
                 nota=dif(s_piece["vs_anterior"]))]
    res = (ley(nota="hit@1 · IC 95% · arriba, el coseno del flujo; abajo, la consulta contra la foto del producto")
           + hbars(rows, width=1150, label_w=330, row_h=74, bar_h=24, x_max=0.8, ticks=[0, .2, .4, .6, .8], right=350,
                   gaps=(4,), nota_t="contra la otra forma · IC 95%"))
    exp("E2", 3, "¿Cuánto suma escribir la consulta <em>como una ficha?</em>",
        "<p>El plan no busca con el pedido: escribe el producto ideal en las ocho líneas del catálogo "
        "(<strong>respuesta hipotética, HyDE</strong>). Es la técnica de Advanced RAG del flujo, y no la habíamos "
        "medido contra no hacerla.</p>",
        f"<p><strong>La ficha</strong> contra <strong>la frase natural</strong>, sin reescribir: como el redactor nombró "
        f"la pieza («{esc(frases[0])}»; {f(med, 0)} palabras de mediana).</p>"
        "<p>Y el piso: solo la línea Type, solo el kind. Con el coseno del flujo y contra la foto.</p>",
        res,
        f"<strong>El plan escribe la ficha</strong>: {dif(d_q, flip=True)} sobre no reescribir. Antes la comparábamos con "
        f"«solo el kind», que es azar por construcción (buscar «rug» entre {D['n_alfombras']} alfombras). Y un dato: "
        f"la foto casi no necesita la reescritura.",
        t=60, planta=[5], notas=[
            "Experimento 2: cómo se escribe la consulta. El plan no busca con el pedido: escribe el producto "
            "ideal en las ocho líneas del catálogo. Es la técnica de Advanced RAG del flujo, y no la habíamos "
            "medido contra no hacerla: la comparábamos con buscar solo con el nombre del kind, que es azar por "
            "construcción.",
            "[paso] La ficha contra la frase natural, sin reescribir: las pocas palabras con que el redactor "
            "nombró la pieza. Con la búsqueda del flujo, y también contra la foto del producto.",
            f"[paso] La ficha da {f(q_full['hit@1'])} y la frase natural {f(q_piece['hit@1'])}: suma "
            f"{sg(-d_q['hit@1'], 2)}, con un intervalo lejos del cero. Y lo que no esperábamos: contra la foto, la "
            f"frase sin reescribir da {f(s_piece['hit@1'])}, casi lo mismo que la ficha. El texto necesita que la "
            f"consulta hable como el catálogo; la foto, casi no.",
            "[paso] El plan sigue escribiendo la ficha. Y queda un argumento para la búsqueda híbrida: las dos "
            "rutas fallan distinto.",
        ])

    # ---------------------------------------------------------------- E3 · búsqueda léxica, por foto e híbrida
    HK = {"lexica": "bm25|description|filtro-kind", "foto": "siglip2|description|filtro-kind", "clip": "clip|description|filtro-kind",
          "densa+lexica": V1 + "|+bm25", "densa+foto": V1 + "|+siglip2", "lexica+foto": "bm25|description|filtro-kind|+siglip2",
          "rrf": V2 + "|fusion-rrf"}

    def hrow(key, label, kind="alt"):
        x = HIB[key]
        return dict(label=label, value=x["hit@1"], ci=ci95(x), kind=kind,
                    nota=dif(x["vs_base"]) if "vs_base" in x else "la base: versión 1")

    rows = [hrow(V1, "densa: Qwen3", "ink"), hrow(HK["lexica"], "léxica: BM25"), hrow(HK["foto"], "por foto: SigLIP 2"),
            hrow(HK["clip"], "por foto: CLIP ViT-B/32", "muted"), hrow(HK["densa+lexica"], "densa + léxica"),
            hrow(HK["densa+foto"], "densa + foto"), hrow(HK["lexica+foto"], "léxica + foto"),
            hrow(V2, "densa + léxica + foto", "main")]
    eo = D["ej_otros"]
    res = (ley(nota="hit@1 · IC 95% · arriba, cada buscador solo; abajo, fusionados (z-score, promedio)")
           + hbars(rows, width=1150, label_w=330, row_h=53, bar_h=22, x_max=0.8, ticks=[0, .2, .4, .6, .8], right=350,
                   gaps=(4,), nota_t="contra la densa · IC 95%")
           + f'<p class="nota" data-desde="2">La alfombra del ejemplo: la densa la deja {eo["densa"]}.ª; la léxica, {eo["lexica"]}.ª; '
             f'por foto, <b>{eo["foto"]}.ª</b>; las tres juntas, {eo["hibrida"]}.ª.</p>')
    exp("E3", 3, "¿Suman la búsqueda por palabras <em>y la foto del producto?</em>",
        "<p>Dos dudas de fondo. ¿Hace falta el embedder neuronal, o alcanza con <strong>contar palabras</strong>?</p>"
        "<p>Y el catálogo tiene fotos: la clase dio dos rutas, pasar la imagen a texto (lo que hacíamos) o "
        "<strong>embeberla directamente</strong>.</p>",
        "<ul><li><strong>densa</strong> (Qwen3) y <strong>léxica</strong> (BM25), sobre las mismas descripciones;</li>"
        "<li><strong>por foto</strong> (SigLIP 2 o CLIP): la consulta en una frase contra la foto, sin descripción;</li>"
        "<li><strong>fusión</strong>: cada puntaje estandarizado, y el promedio.</li></ul>",
        res,
        f"<strong>La búsqueda del flujo pasa a ser híbrida: es la versión 2</strong> (Ejercicio 4). Solos, los tres rinden "
        f"parecido; se equivocan en cosas distintas, y juntos suman {dif(D21)} de hit@1 y {dif(D21, 'hit@5')} de hit@5.",
        t=60, planta=[3, 6], notas=[
            "Experimento 3: búsqueda léxica, por foto e híbrida. Dos dudas de fondo sobre el índice. ¿El embedder "
            "neuronal hace falta, o alcanza con contar palabras? Y el catálogo tiene fotos: la clase dio dos "
            "rutas, pasar la imagen a texto, que es lo que hacíamos, o embeberla directamente. Esa nunca la "
            "habíamos medido.",
            "[paso] Tres buscadores sobre las mismas consultas: el denso, Qwen3 sobre las descripciones; el "
            "léxico, BM25; y por foto, SigLIP 2, con la consulta en una frase contra la foto del producto. Y sus "
            "fusiones.",
            f"[paso] Solos, los tres rinden parecido: {f(HIB[V1]['hit@1'])}, {f(HIB[HK['lexica']]['hit@1'])} y "
            f"{f(HIB[HK['foto']]['hit@1'])}. Ni el embedder le gana a contar palabras, ni describir le gana a embeber "
            f"la foto. Pero se equivocan en cosas distintas: fusionados dan {f(HIB[V2]['hit@1'])}, "
            f"{sg(D21['hit@1'])} de hit@1, con un intervalo que no toca el cero.",
            "[paso] La búsqueda híbrida pasa a ser la del flujo: es la versión 2, el Ejercicio 4. Usa las dos "
            "rutas de la clase a la vez.",
        ])

    # ---------------------------------------------------------------- el camino incremental: un cambio por paso
    r_opus = D["RER"][BASE + "|rerank-opus"]
    k5 = D["CURVA"]["por_k"]["5"]["acierto_eleccion"]
    pasos = []
    for key, label, kind, fuerte in [
            (K_NAIVE, "RAG naive: texto del vendedor, consulta sin reescribir", "muted", False),
            (K_DESC, "+ cada producto descripto desde su foto", "alt", False),
            (K_HYDE, "+ la consulta escrita como una ficha (HyDE)", "alt", False),
            (V1, "+ filtro por kind: versión 1", "ink", True),
            (V1 + "|+bm25", "+ búsqueda léxica (BM25) fusionada", "alt", False),
            (V2, "+ la foto del producto (SigLIP 2): versión 2", "main", True)]:
        x = CAM[key]
        d = x.get("vs_anterior")
        pasos.append(dict(label=label, value=x["hit@1"], ci=ci95(x), kind=kind, fuerte=fuerte, h5=f(x["hit@5"]),
                          cambio=dif(d) if d else None, sube=bool(d and d["hit@1_ic95"][0] > 0)))
    aparte = [dict(label="un VLM elige entre los 5 primeros", value=k5, nota="sobre el paso 3, con filtro por tipo"),
              dict(label=f"un VLM reordena el top-10: el {f(r_opus['hit@1'], 2)} de antes", value=r_opus["hit@1"],
                   nota="contra la consulta, sin el cuarto")]
    d_desc, d_hyde, d_kind = CAM[K_DESC]["vs_anterior"], CAM[K_HYDE]["vs_anterior"], CAM[V1]["vs_anterior"]
    body = ('<div class="cuerpo">' + cab("03", "El buscador · la ablación incremental",
                                         f"El camino: de {f(n1['hit@1'], 2)} a {f(B2['hit@1'], 2)} de hit@1, <em>un cambio por paso</em>") + '</div>'
            + '<div class="camino">'
            + camino(pasos, aparte, width=1776, label_w=690, bar_w=470, row_h=60, bar_h=28)
            + '</div>'
            + remate(f"El {f(r_opus['hit@1'], 2)} que mostrábamos no era un escalón: es un VLM reordenando el top-10, <mark>una técnica aislada, no el flujo</mark>."))
    add(body, titulo="El camino, un cambio por paso", cap=3, t=50, planta=[2, 5, 6], notas=[
        f"La ablación incremental: un cambio por paso, con su diferencia pareada. Arrancamos del RAG naive, el "
        f"texto del vendedor y la consulta sin reescribir: {f(n1['hit@1'], 2)}. Describir cada producto desde su "
        f"foto lo lleva a {f(n2['hit@1'], 2)}; escribir la consulta como una ficha, a {f(CAM[K_HYDE]['hit@1'], 2)}. "
        f"Esos dos pasos son los que más pesan. El filtro por kind no suma en este banco: lo usamos por otra "
        f"razón, que vemos en los de trámite. Con el filtro, esa es la versión 1 del flujo. Con la búsqueda "
        f"léxica, {f(CAM[V1 + '|+bm25']['hit@1'], 2)}; con la foto, {f(B2['hit@1'], 2)}: la versión 2.",
        f"Aparte queda el {f(r_opus['hit@1'], 2)} que mostrábamos antes: es un VLM reordenando el top-10, una "
        f"técnica aislada, no un escalón del flujo.",
    ])

    # ---------------------------------------------------------------- E4 · ¿error, o el mismo mueble en otro color?
    e_q = EMB[V1]
    util1, util3 = D["util1"], D["util3"]
    G = D["GRAD"]["consultas"]
    fam = {k_: EMB[f"{k_}|description|filtro-kind"]["vs_base"] for k_ in ("bm25", "siglip2", "bge")}
    assert fam["bm25"]["familia_hit@1_ic95"][0] < 0 < fam["bm25"]["familia_hit@1_ic95"][1] and fam["bge"]["familia_hit@1_ic95"][1] < 0, \
        "por familia cambió el orden entre buscadores: revisar el texto del experimento 4"
    cada = round(1 / D["frac_variante"])
    rk = rankings(D["EMB_DIR"])[V1]

    def variante(pred, pie):
        """Un caso donde el primero «falla» y es el mismo modelo: la foto del anotado y la del primero."""
        r = next(x for x in rk if pred(x))
        assert r.get("rank_family") == 1 and (r["rank"] or 99) > 1, "el caso de variante ya no lo es: elegir otro"
        a, b = r["relevant"][0], r["ranked"][0]
        ia, ib = D["items"][a], D["items"][b]
        assert ia["name"] == ib["name"], "el caso de variante ya no es el mismo modelo"
        return (f'<div class="vr2"><figure><img src="{img.uri(foto_producto(D, a), 180, 180, fit="contain")}" alt=""><figcaption>el anotado</figcaption></figure>'
                f'<figure class="p"><img src="{img.uri(foto_producto(D, b), 180, 180, fit="contain")}" alt=""><figcaption>el 1.º de la búsqueda</figcaption></figure>'
                f'<p>{pie(ia, ib)}</p></div>'), (ia, ib)

    def dim(it):
        d_ = it.get("dimensions_cm") or {}
        return f'{d_["width"]:.0f} × {d_["depth"]:.0f} cm'

    v_a, (ia, ib) = variante(lambda x: x["phrase"] == "birch nesting tables at front left",
                             lambda ia, ib: "Mesas nido: la anotada, en abedul; la primera, <b>el mismo modelo en marrón negro</b>.")
    assert "Birch" in ia["colors"][0] and "Black-brown" in ib["colors"][0], "cambiaron los colores del caso de variante"
    v_b, _ = variante(lambda x: x["room_id"] == EJ_ROOM and x["piece"] == EJ_PIECE,
                      lambda ia, ib: f"La alfombra del ejemplo: la anotada mide {dim(ia)}; la primera, <b>el mismo modelo de {dim(ib)}</b>.")
    rows = [dict(label="el producto exacto", value=e_q["hit@1"], ci=ci95(e_q), kind="alt", sub="hit@1"),
            dict(label="el mismo modelo", value=e_q["familia_hit@1"], ci=ci95(e_q, "familia_hit@1"), kind="alt",
                 sub="otra variante también vale"),
            dict(label="uno que sirve", value=util1, kind="main", sub="según un juez: nota 1 o 2")]
    res = (ley(nota="el primer candidato de la búsqueda de la versión 1")
           + hbars(rows, width=1150, label_w=330, row_h=76, bar_h=26, x_max=1.0, right=120)
           + f'<div class="vars" data-desde="2">{v_a}{v_b}</div>'
           + f'<p class="nota" data-desde="2">El juez: {G["todas"]["n"]} consultas, reponderado a todas (alguno del top-3 sirve: {f(util3, 2)}).</p>')
    exp("E4", 3, "Cuando el primero no es el anotado, <em>¿se equivocó?</em>",
        f"<p>hit@1 exige el producto anotado <strong>exacto</strong>, y el catálogo está lleno de variantes del mismo "
        f"modelo: el {pct(D['con_variantes'])} de las consultas busca un producto que tiene variantes.</p>",
        "<p>Tres niveles de correcto para el primer candidato:</p><ul>"
        "<li><strong>exacto</strong>: el producto anotado;</li>"
        "<li><strong>el mismo modelo</strong>: mismo nombre comercial y mismo grupo;</li>"
        "<li><strong>sirve</strong>: un juez lo califica con 2, 1 o 0.</li></ul>",
        res,
        f"<strong>El banco subestima el nivel, no el orden.</strong> Una de cada {cada} veces que el primero «falla» es el mismo "
        f"mueble en otra medida u otro color; por familia tampoco se distinguen Qwen3, BM25 y SigLIP 2, y BGE sigue peor. "
        f"El exacto para comparar; los tres juntos para decir cuánto sirve.",
        t=40, planta=[6], k_dec="conclusión", notas=[
            "Experimento 4. hit@1 exige el producto anotado exacto, y el catálogo está lleno de variantes del "
            "mismo modelo. ¿Cuánto de lo que cuenta como error es el mismo mueble en otro color?",
            "[paso] Tres niveles de correcto para el primer candidato: el producto exacto, el mismo modelo, y uno "
            "que sirve según un juez.",
            f"[paso] El exacto, {f(e_q['hit@1'], 2)}; el mismo modelo, {f(e_q['familia_hit@1'], 2)}; uno que sirve, "
            f"{f(util1, 2)}. Una de cada {cada} veces que el primero falla es otra variante: las mismas mesas en otro "
            f"color, la misma alfombra en otra medida.",
            "[paso] El banco subestima el nivel, no el orden: la comparación entre buscadores no cambia.",
        ])

    # ================================================================ 04 · la lista
    separador(4, ["Segundo grupo: quién elige, y el flujo entero en cuartos reales, con el juez. Llega la mesa ratona."])

    # ---------------------------------------------------------------- E5 · elegir con un VLM, y cuántos candidatos
    r0 = D["RER"][BASE]
    d_opus = D["d_opus"]
    cv = D["CURVA"]["por_k"]
    ks = sorted(int(x) for x in cv)
    ac = [cv[str(x)]["acierto_eleccion"] for x in ks]
    te = [cv[str(x)]["techo_hit@k"] for x in ks]
    cis = [tuple(cv[str(x)]["ic95"]) for x in ks]
    d35 = D["CURVA"]["diferencias_pareadas"]["3->5"]
    d35_txt = f'{sg(d35["acierto_eleccion"])} {ic(*d35["ic95"])}'
    dh = D["DIAG"]["hibrida"]
    res = (ley((AZUL, "acierto de la elección del VLM, IC 95%"), (GRIS, "techo: el anotado está entre los k"))
           + line_chart([dict(name="acierto", ys=ac, kind="main", ci=cis, label="acierto"),
                         dict(name="techo", ys=te, kind="alt", dash=True, label="techo")],
                        ks, width=1120, height=410, ymin=0.4, ymax=1.0, yticks=[.4, .6, .8, 1.0],
                        marks=[(3, "antes"), (kf, "el flujo")], xlab="k: candidatos por pieza", right=130)
           + '<div class="e5n" data-desde="2">'
             f'<div><b>{f(r0["hit@1"])} → {f(r_opus["hit@1"])}</b><span>hit@1 reordenando el top-10 mirando las fotos: '
             f'{dif(d_opus)}, a {usd(D["c_rerank"])} por búsqueda</span></div>'
             f'<div><b>{d35_txt}</b><span>de 3 a 5 candidatos; a partir de 8 se aplana</span></div></div>')
    exp("E5", 4, "Elegir con un VLM, <em>y cuántos candidatos</em>",
        f"<p>hit@10 es {f(r0['hit@10'], 2)} pero hit@1 {f(r0['hit@1'], 2)}: el correcto casi siempre está entre los 10 "
        f"primeros, pero no primero. En el flujo, quien elige <strong>mira las fotos</strong>.</p>",
        "<p>Opus recibe la consulta y las fotos del top-10, y las ordena. De ahí sale gratis la curva: si eligiera "
        "entre los primeros k, ¿acertaría? <strong>Techo</strong>: el correcto está entre esos k.</p>",
        res,
        f"<strong>{kf} candidatos por pieza</strong> (antes 3). Ojo: es una <strong>técnica aislada</strong>, no un paso del "
        f"flujo. Ese reranker ordena contra la consulta, sin ver el ambiente; el que elige en el flujo arma un conjunto "
        f"para el cuarto, y no tiene ground truth.",
        t=55, planta=[6, 7], notas=[
            f"Experimento 5. hit@10 es {f(r0['hit@10'], 2)} pero hit@1 {f(r0['hit@1'], 2)}: el correcto casi siempre está "
            f"entre los diez primeros, pero no primero. ¿Mirar las fotos ordena mejor que el coseno? ¿Y cuántos "
            f"candidatos conviene pasar?",
            "[paso] Opus recibe la consulta y las fotos de los diez primeros, y los ordena. De ahí sale gratis la "
            "curva: si eligiera entre los primeros k, ¿acertaría? La punteada es el techo.",
            f"[paso] Reordenando el top-10, hit@1 pasa de {f(r0['hit@1'])} a {f(r_opus['hit@1'])}. De 3 a 5 candidatos "
            f"la elección sube {f(100 * d35['acierto_eleccion'], 0)} puntos, también significativo; a partir de 8 se "
            f"aplana.",
            f"[paso] Cinco candidatos por pieza. Pero ojo: es una técnica aislada, no un paso del flujo. Ese "
            f"reranker ordena contra la consulta, sin ver el ambiente; el que elige en el flujo arma un conjunto "
            f"para el cuarto, y no tiene ground truth. Por eso este número no es el del sistema.",
        ])

    e6(D)
    e7(D)

    # ================================================================ 05 · de trámite
    separador(5, ["Lo que la cátedra dijo que iba a preguntar, con la respuesta corta. Se prende la lámpara."])
    tramite(D)

    # ================================================================ 06 · ejercicio 4
    separador(6, ["El Ejercicio 4: versión 1 y versión 2 de la arquitectura. Cortinas y planta."])
    ejercicio4(D)


# ---------------------------------------------------------------- E6 · qué catálogo

def e6(D):
    JC, J5 = D["JC"], D["J5"]
    jg = D["j_grupos"]
    P, U, TT = jg["propios"], jg["publicos"], jg["total"]
    p_cat = p_signos(TT["gana_todos"], TT["gana_ikea"])
    det = {x["slug"]: x for x in JC["detalle"]}
    slugs = [s for s in D["pedidos"] if s in det]
    slugs = [s for s in slugs if not s.startswith("publica")] + [s for s in slugs if s.startswith("publica")]
    cells = tira_votos(D, [det[s] for s in slugs], "todos", {"todos": "IKEA+ABO", "ikea": "IKEA"})
    s5 = J5["resumen"]
    body = (xcab("E6", "La lista", "¿Qué catálogo: <em>IKEA, Amazon o los dos?</em>")
            + '<div class="e6a">'
            + bloque("por qué", f"<p>IKEA 2013 tiene fotos chicas, asientos sin medidas y una sola estética. <strong>Amazon "
                     f"Berkeley Objects</strong> tiene publicaciones reales, con medidas en el {pct(D['abo_con_medidas'])}, pero "
                     f"no tiene ambientes anotados: hay que medirlo de punta a punta.</p>")
            + bloque("qué hicimos", f"<p>Los mismos {JC['ambientes']} ambientes, pedidos y plan; cambia solo el catálogo. El juez "
                     f"compara las dos listas a ciegas, en los dos órdenes.</p>", desde=0)
            + '</div>'
            + '<div class="e12b e6b">'
            + '<div class="ley" data-desde="1"><span><i style="background:#9AA4AF"></i>votó IKEA</span><span><i style="background:#2453D6"></i>votó IKEA + ABO</span>'
              '<span>un punto por orden</span></div>'
            + f'<div class="jg"><div class="jgk"><span>departamentos propios · pedidos nórdicos</span><span>fotos públicas · otros estilos</span></div>{cells}</div>'
            + f'<p class="credito">Fotos públicas (Wikimedia Commons y Flickr): {esc(creditos(D, [s for s in slugs if s.startswith("publica")]))}.</p>'
            + '<div class="e12g" data-desde="1">'
            + f'<div class="cc"><div class="etq">propios · nórdicos</div><p class="ccn">{P["gana_ikea"]} a {P["gana_todos"]}</p>'
              f'<p>empatan, con {P["empates"]} empate · útiles: {f(P["util_ikea"], 2)} y {f(P["util_todos"], 2)}</p></div>'
            + f'<div class="cc hi"><div class="etq">públicas · otros estilos</div><p class="ccn">{U["gana_todos"]} a {U["gana_ikea"]}</p>'
              f'<p>para IKEA + ABO · útiles: de {f(U["util_ikea"], 2)} a <strong>{f(U["util_todos"], 2)}</strong></p></div>'
            + f'<div class="cc"><div class="etq">en total</div><p class="ccn">{TT["gana_todos"]} a {TT["gana_ikea"]} <small>p = {f(p_cat, 2)}</small></p>'
              f'<p>test de signos sobre los {TT["gana_todos"] + TT["gana_ikea"]} decididos · ABO solo contra IKEA, en los 5 propios: '
              f'pierde {s5["ikea"]["gana"]} a {s5["abo"]["gana"]}</p></div>'
            + '</div></div>'
            + f'<div class="decision" data-desde="2"><div class="k">decisión</div><p><strong>El flujo usa IKEA + ABO.</strong> '
              f'Pero {TT["gana_todos"]} a {TT["gana_ikea"]} es p = {f(p_cat, 2)}, y los pedidos de otros estilos <strong>los escribimos '
              f'sabiendo qué le falta a IKEA</strong>: la decisión es razonable; el titular «{U["gana_todos"]} a {U["gana_ikea"]}», no.</p></div>')
    add(body, titulo="E6 · ¿Qué catálogo: IKEA, Amazon o los dos?", cap=4, t=55, fases="1,2,3", planta=[1], cls="lam-e6", notas=[
        "Experimento 6: qué catálogo. IKEA es de 2013, con una sola estética, la nórdica. Amazon Berkeley Objects "
        "tiene publicaciones reales, con medidas, pero no tiene ambientes anotados: hay que medirlo de punta a "
        "punta. Los mismos ambientes, pedidos y plan; cambia solo el catálogo, y el juez compara las dos listas a "
        "ciegas, en los dos órdenes.",
        f"[paso] En nuestros cinco departamentos, con pedidos nórdicos, los dos juntos empatan con IKEA. En los seis "
        f"ambientes públicos, con otros estilos, IKEA más Amazon gana {U['gana_todos']} a {U['gana_ikea']}. En total, "
        f"{TT['gana_todos']} a {TT['gana_ikea']}.",
        f"[paso] Usamos los dos catálogos. Con dos salvedades: {TT['gana_todos']} a {TT['gana_ikea']} en once ambientes "
        f"da p igual a {f(p_cat, 2)}, no es concluyente; y los pedidos de otros estilos los escribimos nosotros, "
        f"sabiendo qué le falta a IKEA. Muestra que Amazon cubre ese hueco, no cuán frecuente es.",
    ])


# ---------------------------------------------------------------- E7 · con búsqueda contra sin búsqueda: los dos extremos

def e7(D):
    JA, JX = D["JA"], D["JX"]
    sa, sx = JA["resumen"], JX["resumen"]
    votos_a = [v for d in JA["detalle"] for v in d["votos"]]
    p_azar = p_signos(sa["densa"]["gana"], sa["azar"]["gana"])
    C = D["CTX"]
    kf = D["cfg"].furnish.candidates
    det_x = {d["slug"]: d for d in JX["detalle"]}
    orden = [s_ for s_ in D["pedidos"] if s_ in det_x]
    orden = [s_ for s_ in orden if not s_.startswith("publica")] + [s_ for s_ in orden if s_.startswith("publica")]
    cells_a = tira_votos(D, JA["detalle"], "densa", {"densa": "búsqueda", "azar": "azar"}, desde=2)
    cells_x = tira_votos(D, [det_x[s_] for s_ in orden], "hibrida", {"hibrida": "búsqueda", "contexto": "catálogo"}, desde=2)
    pub = [s_ for s_ in orden if s_.startswith("publica")]
    mil = round(C["tokens"] / 1000)
    tercio = C["tokens"] / 1e6
    assert 0.3 < tercio < 0.37 and sx["hibrida"]["gana"] == sx["contexto"]["gana"], "cambió el experimento del catálogo en el contexto: revisar E7"
    res = ('<div class="ley" data-desde="1"><span><i style="background:#2453D6"></i>votó la lista con búsqueda</span>'
           '<span><i style="background:#9AA4AF"></i>votó la otra</span><span>un punto por orden del juez</span></div>'
           '<div class="x7" data-desde="1">'
           f'<div class="x7k"><b>sin ranking</b><span>{kf} al azar del kind · {JA["ambientes"]} ambientes</span></div>'
           f'<div class="x7a"><div class="jg">{cells_a}</div>'
           f'<div class="cc hi" data-desde="2"><p class="ccn">{sa["densa"]["gana"]} a {sa["azar"]["gana"]}</p><p>los {len(votos_a)} votos · '
           f'p = {f(p_azar, 3)} · útiles {f(sa["densa"]["util"], 2)} contra {f(sa["azar"]["util"], 2)}</p></div></div>'
           f'<div class="x7k"><b>con todo a la vista</b><span>el catálogo entero en el prompt · {JX["ambientes"]} ambientes</span></div>'
           f'<div class="x7a"><div class="jg">{cells_x}</div></div>'
           '<div></div>'
           f'<div class="cc x7s" data-desde="2"><p class="ccn">{sx["hibrida"]["gana"]} a {sx["contexto"]["gana"]}</p><p>y {JX["empates"]} empate · '
           f'productos útiles {f(sx["hibrida"]["util"], 2)} y {f(sx["contexto"]["util"], 2)} · lo que eligió viendo todo estaba entre los '
           f'{kf} de la búsqueda en {C["en5"]} de {C["piezas"]} piezas</p></div>'
           '</div>'
           f'<p class="credito" data-desde="1">Fotos públicas: {esc(creditos(D, pub))}.</p>'
           '<div class="hoja rag" data-desde="3"><h3>¿Hacía falta RAG, si el catálogo entra en el contexto?</h3>'
           f'<p><b>Por calidad, no: empatan.</b> Por costo, depende del tráfico: con el catálogo en la caché de prompt, {usd(C["caliente"])} '
           f'por pedido contra {usd(C["rag_usd"], 3)} de elegir entre candidatos con foto; sin caché, {usd(C["sin_cache"])}. La búsqueda '
           f'<b>escala</b> (las {miles(D["n_todos"])} fichas ya son {mil} mil tokens, un tercio del contexto; ABO completo son '
           f'{D["abo_total"]} publicaciones) y no depende de la caché, que dura 5 minutos y se invalida con cualquier cambio del catálogo.</p></div>')
    exp("E7", 4, "Con búsqueda contra sin búsqueda: <em>los dos extremos</em>",
        "<p>Es el <strong>«con y sin retrieval»</strong> del flujo, con sus dos extremos: sin ranking, y con todo a la vista. "
        "El segundo es la pregunta incómoda: si el catálogo entra en el contexto, ¿hacía falta RAG?</p>",
        f"<p>Mismo plan, mismo modelo que elige, mismo juez. Cambia solo qué recibe el que elige:</p><ul>"
        f"<li><strong>{kf} al azar</strong> entre los que pasan los mismos filtros;</li>"
        f"<li><strong>las {miles(D['n_todos'])} fichas</strong> en el prompt, en texto, sin ranking ni fotos.</li></ul>",
        res,
        f"<strong>La búsqueda hace falta cuando el que elige ve {kf} productos, y empata cuando puede leerlos todos.</strong> Con "
        f"{miles(D['n_todos'])} productos, RAG no hace mejor la lista: es la arquitectura que escala.",
        t=60, planta=[6], k_dec="conclusión", cls="lam-e7", notas=[
            "Experimento 7: con búsqueda contra sin búsqueda. Es el con y sin retrieval del flujo, con dos "
            "extremos. Uno: darle al que elige cinco productos al azar del kind pedido. Dos, la pregunta incómoda: "
            "si el catálogo entra en el contexto, ¿hacía falta RAG?",
            f"[paso] Mismo plan, mismo modelo que elige, mismo juez. Contra el azar, en {JA['ambientes']} ambientes. Y "
            f"contra el catálogo entero en el prompt, las {miles(D['n_todos'])} fichas en texto, en los {JX['ambientes']}.",
            f"[paso] Contra el azar, {sa['densa']['gana']} a {sa['azar']['gana']}, con los {len(votos_a)} votos. Contra el "
            f"catálogo entero, {sx['hibrida']['gana']} a {sx['contexto']['gana']}, con los mismos productos útiles: empatan.",
            "[paso] La búsqueda hace falta cuando el que elige ve cinco productos, y empata cuando puede leerlos "
            "todos. Con el catálogo en la caché de prompt cuesta lo mismo; sin caché, diez veces más. Con mil "
            "quinientos productos, RAG no hace mejor la lista: lo elegimos porque escala, y porque no depende del "
            "tráfico ni de un modelo de contexto largo.",
        ])


# ---------------------------------------------------------------- de trámite: E8 y dos láminas con E9 a E14

def tramite(D):
    CAM, HIB, EMB, ABL, LIN, RLOC = D["CAM"], D["HIB"], D["EMB"], D["ABL"], D["LIN"], D["RLOC"]
    B1 = D["B1"]
    HIB_R = D["HIB_R"]

    # ---------------------------------------------------------------- E8 · tres redactores
    tres = [HIB] + HIB_R

    def serie(key):
        return [x[key]["hit@1"] for x in tres]

    v1s, v2s = serie(V1), serie(V2)
    lex, fot = serie("bm25|description|filtro-kind"), serie("siglip2|description|filtro-kind")

    def fila(label, xs):
        return dict(label=label, h=xs, mean=statistics.mean(xs), sd=statistics.stdev(xs))

    rrows = [fila("versión 2: híbrida", v2s), fila("versión 1: densa", v1s), fila("léxica sola: BM25", lex),
             fila("por foto sola: SigLIP 2", fot)]
    difs = " · ".join(sg(x[V2]["vs_base"]["hit@1"]) for x in tres)
    assert all(x[V2]["vs_base"]["hit@1_ic95"][0] > 0 for x in tres), "la mejora de la híbrida ya no se repite con los tres redactores"
    res = ('<div class="ley" data-desde="1"><span>hit@1 con cada una de las tres escrituras · la raya es la media, la banda ± un desvío</span></div>'
           + dots_repro(rrows, width=1140, label_w=340, row_h=92, xmin=0.44, xmax=0.64,
                        ticks=[.44, .48, .52, .56, .60, .64], tick_d=2, right=200)
           + f'<p class="nota" data-desde="2">La versión 2 menos la versión 1, pareado, con cada redactor: <b>{difs}</b>; las tres con un '
             f'intervalo que no toca el cero.</p>')
    sd1 = statistics.stdev(v1s)
    exp("E8", 5, "¿Cuánto cambia el número <em>según quién escribe?</em>",
        "<p>Las consultas de evaluación las escribió un modelo. La clase pidió <strong>promedio de ejecuciones y "
        "desvío</strong>: si el número cambia mucho con quién escribe, mide al redactor y no al sistema.</p>",
        "<p>Las mismas consultas, escritas otras dos veces por subagentes independientes, mirando las mismas fotos. "
        "Los mismos buscadores sobre cada escritura.</p>",
        res,
        f"<strong>El número se mueve unos {f(100 * sd1, 1)} puntos sin cambiar el sistema</strong>: versión 1, {media_desvio(v1s)}; "
        f"versión 2, {media_desvio(v2s)}. Una diferencia de 2 puntos entre dos métodos no es señal: por eso los embedders "
        f"«no se distinguen», y la híbrida sí.",
        t=35, planta=[5, 6], k_dec="conclusión", notas=[
            "Experimento 8: tres redactores. Las consultas de evaluación las escribió un modelo. La clase pidió "
            "promedio y desvío: ¿cuánto cambia el número sin cambiar el sistema?",
            "[paso] Las mismas consultas, escritas otras dos veces por subagentes independientes.",
            f"[paso] La versión 1 da {media_desvio(v1s)}; la versión 2, {media_desvio(v2s)}. La mejora de la híbrida se "
            f"repite con los tres.",
            "[paso] El número se mueve unos dos puntos y medio según quién escribe: por eso no leemos diferencias "
            "de dos puntos.",
        ])

    # ---------------------------------------------------------------- de trámite 1: el índice
    def emb(k_):
        return EMB[f"{k_}|description|filtro-kind"]

    def sin(x):
        return LIN[f"{V1}|sin-{x}"]

    def h15(x):
        return f'{f(x["hit@1"])} / {f(x["hit@5"])}'

    dims = {d_: (ABL[f"{BASE}|dim-{d_}"] if d_ != 1024 else ABL[BASE])["hit@1"] for d_ in (32, 128, 512, 1024)}
    doc_, chunk, alin = ABL[BASE], ABL[BASE + "|chunks-lines-max"], ABL[BASE + "|chunks-lines-aligned"]
    visto = sin("Use+Style+Feel+Goes with")
    d512 = D["d512"]

    def fila_t(e, nombre, comp, resp, tipo="tram"):
        c = laminas_rec.xref(e, f"<b>{nombre}</b>", tipo=tipo) if e else f'<div class="xrf sin"><span></span><p><b>{nombre}</b></p></div>'
        return f'<div class="tr1">{c}</div><div class="tr2">{comp}</div><div class="tr3"><p>{resp}</p></div>'

    TH = ('<div class="trh">la pregunta</div><div class="trh">{}</div><div class="trh">la respuesta</div>')
    tabla = (TH.format("qué se comparó · hit@1")
             + fila_t("E9", "Embedder",
                      micro([("hashing", emb("hashing")["hit@1"], f(emb("hashing")["hit@1"]), False),
                             ("BM25", emb("bm25")["hit@1"], f(emb("bm25")["hit@1"]), False),
                             ("BGE-base", emb("bge")["hit@1"], f(emb("bge")["hit@1"]), False),
                             ("Qwen3", EMB[V1]["hit@1"], f(EMB[V1]["hit@1"]), True)]),
                      f'Solo se sostiene Qwen3 sobre BGE ({nb(dif(emb("bge")["vs_base"], flip=True))}). Contra contar palabras no se '
                      f'distingue ({nb(dif(emb("hashing")["vs_base"], flip=True))}). Queda Qwen3 por robustez a la paráfrasis, sin '
                      f'evidencia medida.')
             + fila_t("E10", "Dimensión",
                      micro([(miles(d_), v, f(v), d_ == 1024) for d_, v in dims.items()]),
                      f'Con 512 da lo mismo que con 1.024 ({nb(dif(d512))}). Con {miles(D["n_todos"])} productos la memoria no pesa '
                      f'({f(D["indice_mb"], 1)} MB): queda 1.024.')
             + fila_t("E11", "Splitting y líneas",
                      micro([("un documento", doc_["hit@1"], f(doc_["hit@1"]), True),
                             ("un chunk por línea", chunk["hit@1"], f(chunk["hit@1"]), False),
                             ("línea contra línea", alin["hit@1"], f(alin["hit@1"]), False)]),
                      f'No se parte: un producto es un documento de unas 80 palabras. Lo que importa es qué líneas lo componen: sin '
                      f'Colors, {nb(dif(sin("Colors")["vs_base"]))}; sin Shape, {nb(dif(sin("Shape")["vs_base"]))}; con solo las '
                      f'cuatro de lo que se ve, igual que con las ocho ({f(visto["hit@1"])}).')
             + fila_t("E12", "Base vectorial",
                      f'<p class="tgr"><b>{D["chroma_igual"]} de {D["chroma_total"]}</b><span>consultas con el mismo ranking: ChromaDB '
                      f'(HNSW, coseno) y recorrer todos los vectores con numpy</span></p>',
                      'A este tamaño, aproximado es exacto. ChromaDB da la persistencia y los filtros de metadata en la misma '
                      'consulta, y es la pieza que escala.'))
    body = ('<div class="cuerpo">' + cab("05", "De trámite · 1 de 2", "Las cuatro preguntas <em>sobre el índice</em>") + '</div>'
            + f'<div class="tram">{tabla}</div>'
            + remate("Con el texto bien escrito, el índice casi no decide nada: son respuestas que hay que tener, <mark>no un gran experimento</mark>."))
    add(body, titulo="De trámite · el índice", cap=5, t=45, planta=[3], cls="lam-tram", notas=[
        f"Los de trámite: lo que la cátedra dijo que iba a preguntar, con la respuesta corta. Embedder: Qwen3 solo "
        f"se sostiene sobre BGE; contra contar palabras no se distingue, porque consultas y descripciones comparten "
        f"el molde. Dimensión: con 512 da lo mismo que con 1.024, y con {miles(D['n_todos'])} productos la memoria no "
        f"pesa. Splitting: no partimos, un producto es un documento; lo que importa es qué líneas lo componen, y "
        f"son las de lo que se ve: colores y forma. Base vectorial: ChromaDB da el mismo ranking que la búsqueda "
        f"exacta en las {D['chroma_total']} consultas; la usamos por la persistencia y los filtros.",
    ])

    # ---------------------------------------------------------------- de trámite 2: filtros, rerankers de texto y el catálogo
    f_none, f_type = HIB["qwen3|description|filtro-none"], HIB[BASE]
    mini, qrr = ABL[BASE + "|rerank-minilm-reranker"], RLOC[BASE + "|rerank-qwen3-reranker"]
    d_kind = CAM[V1]["vs_anterior"]
    d_abo = D["d_abo"]
    old, new = D["CAT_OLD"], D["CAT_NEW"]
    E = D["ESCENA"]
    FM = D["FM"]
    fin, esc_ = D["IMG_FIN"], D["IMG_ESC"]
    tabla = (TH.format("qué se comparó")
             + fila_t("E13", "Filtros de metadata",
                      micro([("sin filtro", f_none["hit@5"], h15(f_none), False), ("por tipo", f_type["hit@5"], h15(f_type), False),
                             ("por kind", B1["hit@5"], h15(B1), True)], xmax=1.0),
                      f'No suman en este banco, y el de kind cuesta 2 puntos de hit@5 ({nb(dif(d_kind, "hit@5"))}). Se usa porque en los '
                      f'pedidos reales evita un {pct(D["otro_kind"])} de candidatos de otro kind (se pide un sillón y aparece una silla '
                      f'de comedor). El de medidas cambia {FM["candidatos_reemplazados"]} de {FM["candidatos"]} candidatos '
                      f'({pct(FM["candidatos_reemplazados"] / FM["candidatos"])}): queda como resguardo, sin evidencia de que mejore la lista.')
             + fila_t("E14", "Rerankers de texto",
                      micro([("sin rerank", RLOC[BASE]["hit@5"], h15(RLOC[BASE]), True), ("MiniLM", mini["hit@5"], h15(mini), False),
                             ("Qwen3-Reranker", qrr["hit@5"], h15(qrr), False)], xmax=1.0),
                      f'Empeoran ({nb(dif(qrr["vs_base"]))} de hit@1 el mejor): releen el mismo texto que ya usó la búsqueda. El que '
                      f'suma es el que mira las fotos (E5).')
             + fila_t("E15", "La escena",
                      micro([("plantilla", fin["identificados"] / fin["productos"],
                              f'{fin["identificados"]} de {fin["productos"]} · {fin["ambiente_conservado"]} de {fin["corridas"]}', True),
                             ("escrita por el LLM", esc_["identificados"] / esc_["productos"],
                              f'{esc_["identificados"]} de {esc_["productos"]} · {esc_["ambiente_conservado"]} de {esc_["corridas"]}', False)], xmax=1.0),
                      E["fila"])
             + fila_t(None, "El catálogo: ampliado, revisado y con ABO",
                      micro([(f'{D["n_855"]} productos', old["hit@5"], h15(old), False), (f'{D["n_ikea"]}, revisado', new["hit@5"], h15(new), True),
                             (f'+ {D["n_abo"]} de ABO', D["TODOS"]["hit@5"], h15(D["TODOS"]), False)], xmax=1.0),
                      f'Decisiones de datos: revisar hace que la lista y la imagen muestren el mismo producto. Sumar ABO de distractores '
                      f'solo puede bajar el número ({nb(dif(d_abo, "hit@5"))} de hit@5): es el costo, chico, de cubrir más estilos.'))
    body = ('<div class="cuerpo">' + cab("05", "De trámite · 2 de 2", "Filtros, rerankers de texto <em>y el catálogo</em>") + '</div>'
            + f'<div class="tram t2">{tabla}</div>'
            + remate("Sin experimento quedan <mark>el modelo de imagen</mark> (comparación diseñada, sin correr) y <mark>los umbrales del control</mark>."))
    add(body, titulo="De trámite · filtros, rerankers y catálogo", cap=5, t=45, planta=[1, 6], cls="lam-tram", notas=[
        f"Filtros de metadata: en este banco no suman, y el de kind cuesta dos puntos de hit@5. Lo usamos igual, "
        f"por algo que el banco no mide: en los pedidos reales, sin él, el {pct(D['otro_kind'])} de los candidatos "
        f"sería de otro kind; pedís un sillón y aparece una silla de comedor. El de medidas cambia pocos candidatos y queda como "
        f"resguardo. "
        f"Rerankers de texto: probamos el MiniLM de la clase y Qwen3-Reranker, y los dos empeoran, porque releen el "
        f"texto que ya usó la búsqueda. La escena: la plantilla y la escrita por el LLM empatan en los once "
        f"ambientes; queda la plantilla, que ahorra una llamada. Y el catálogo: sumar Amazon le cuesta al buscador "
        f"{f(-100 * d_abo['hit@5'], 1)} puntos de hit@5.",
    ])


# ---------------------------------------------------------------- Ejercicio 4: versión 1 y versión 2

def ejercicio4(D):
    CAM, HIB = D["CAM"], D["HIB"]
    B1, B2, D21 = D["B1"], D["B2"], D["D21"]
    cfg = D["cfg"]
    kf = cfg.furnish.candidates
    caso = D["caso"]
    assert caso[V1]["rank"] > kf and caso[V2]["rank"] == 1, "el caso del Ejercicio 4 ya no muestra la limitación: elegir otro"

    def fila_caso(key):
        r = caso[key]
        return '<div class="tira f5">' + "".join(
            ficha(D, pid, 108, cap=False, pos=i + 1, hi=pid in r["relevant"]) for i, pid in enumerate(r["ranked"][:5])) + "</div>"

    cat1 = B1["hit@1_por_categoria"]
    bm_solo, foto_solo = HIB["bm25|description|filtro-kind"], HIB["siglip2|description|filtro-kind"]
    cada5 = round(1 / (1 - B1["hit@5"]))
    anot = "".join(ficha(D, pid, 108, cap=False, hi=True) for pid in caso[V1]["relevant"])
    body = ('<div class="cuerpo">' + cab("06", "Ejercicio 4 · 1 de 3 · la versión anterior y su limitación",
                                         "Versión 1: <em>lee la descripción, no ve el producto</em>") + '</div>'
            + '<div class="v1">'
            + '<div class="v1l">'
            + bloque("la versión 1: el sistema hasta el 11/11",
                     "<p>La búsqueda era el coseno de Qwen3 entre la ficha y las descripciones, con el filtro por kind: "
                     "<code>rag.hybrid: []</code>. Lo demás, igual que hoy.</p>")
            + '<div class="bloque" data-desde="1"><div class="bt">su limitación, medida sobre el ground truth</div>'
              '<div class="trio">'
              f'<div><b>{f(B1["hit@1"], 2)}</b><span>hit@1: entre productos casi iguales, el primero es el anotado la mitad de las veces</span></div>'
              f'<div><b>1 de cada {cada5}</b><span>piezas donde el correcto no llega a los {kf} candidatos (hit@5 {f(B1["hit@5"], 2)}): el que '
              f'elige ya no puede acertar</span></div>'
              f'<div><b>{f(cat1["rug"], 2)} · {f(cat1["deco"], 2)}</b><span>en alfombras y deco, donde hay muchos parecidos ({D["n_alfombras"]} '
              f'alfombras, {D["n_almohadones"]} almohadones); en sillas, {f(cat1["chair"], 2)}</span></div>'
              '</div></div>'
            + '</div>'
            + '<div class="v1r" data-desde="2"><div class="etq">un caso del banco de prueba</div>'
              f'<p class="cita vend">Se busca: «{esc(CASO)}» (un almohadón blanco con un estampado de hojas negras).</p>'
              f'<div class="etq e2">los {kf} candidatos de la versión 1</div>' + fila_caso(V1)
            + f'<p class="nota">Blancos y negros, ninguno con hojas: el anotado quedó {caso[V1]["rank"]}.º, fuera de lo que ve el que elige.</p>'
              f'<div class="etq e2">lo anotado en ese ambiente</div><div class="tira f5">{anot}</div>'
            + '</div></div>'
            + remate(f"Había información sin usar: contar palabras ({f(bm_solo['hit@1'])}) y la foto sola ({f(foto_solo['hit@1'])}) rendían "
                     f"como el embedder, <mark>y fallaban en cosas distintas</mark>.", desde=2))
    add(body, titulo="Ejercicio 4 · versión 1 y su limitación", cap=6, t=50, planta=[6], cls="lam-v1", notas=[
        "El Ejercicio 4. La versión 1 es el sistema hasta el 11 de noviembre: la búsqueda era el coseno del "
        "embedder sobre las descripciones, con el filtro por kind.",
        f"[paso] Su limitación, medida: entre productos casi iguales, el primero es el anotado el "
        f"{pct(B1['hit@1'])} de las veces, y en una de cada {cada5} piezas el correcto no llega a los cinco "
        f"candidatos. Falla donde hay muchos parecidos: alfombras y deco.",
        f"[paso] Un caso: se busca un almohadón blanco con hojas negras, y la versión 1 trae almohadones blancos y "
        f"negros; el anotado quedó {caso[V1]['rank']}.º. El índice lee una descripción, pero no ve el producto ni "
        f"aprovecha las palabras exactas. Y BM25 y la foto sola rendían como el embedder, fallando en cosas distintas.",
    ])

    # ---------------------------------------------------------------- 2 de 3: el cambio y la configuración
    cfg_txt = D["cfg_txt"]
    assert cfg.rag.hybrid == ["bm25", "siglip2"] and cfg.rag.fusion == "sum" and "  hybrid: [bm25, siglip2]" in cfg_txt, \
        "amoblai.yaml ya no es la versión 2: revisar la lámina del cambio"
    otros = [caso[V2]["ranked"].index(pid) + 1 for pid in caso[V2]["relevant"] if pid in caso[V2]["ranked"][1:5]]
    otro_txt = f"; el otro anotado, {otros[0]}.º" if otros else ""
    yaml_ = ('<div class="hoja js yml"><div class="prh"><span>datos/configs/amoblai.yaml</span><span>antes y después</span></div><pre>'
             'rag:\n  embedder: qwen3\n'
             '<span class="del">- hybrid: []                  # versión 1</span>\n'
             '<span class="add">+ hybrid: [bm25, siglip2]     # versión 2</span>\n'
             '  fusion: sum                 <i># z-score, y el promedio</i></pre></div>')
    porque = [("Sale de una <strong>limitación medida</strong> de la versión 1: el índice no ve el producto ni usa las palabras exactas."),
              ("Es una técnica de <strong>Advanced RAG</strong>: búsqueda híbrida (densa + léxica) y multimodal (la foto embebida)."),
              ("<strong>No cuesta nada por pedido</strong>: BM25 y SigLIP 2 corren locales, y los vectores de las fotos se calculan una vez.")]
    pq = "".join(f'<div class="apri"><span>{i + 1}</span><p>{x}</p></div>' for i, x in enumerate(porque))
    body = ('<div class="cuerpo">' + cab("06", "Ejercicio 4 · 2 de 3 · el cambio y la configuración",
                                         "Versión 2: <em>búsqueda híbrida, una línea de configuración</em>") + '</div>'
            + '<div class="v2">'
            + f'<div class="v2l"><div class="etq">el cambio: una línea de configuración</div>{yaml_}'
              f'<div class="v2p" data-desde="1"><div class="etq">por qué este cambio</div>{pq}</div></div>'
            + f'<div class="v2r"><div class="etq">la búsqueda, antes y después</div>{laminas_rec.esquema_hibrida("", kf, versiones=True, w=600)}'
              f'<div class="v2c" data-desde="2"><div class="etq">el caso del almohadón, con la versión 2</div>'
              f'<div class="v2f">{fila_caso(V2)}<p class="nota">El anotado sale <b>1.º</b> (antes, {caso[V1]["rank"]}.º){otro_txt}.</p></div></div></div>'
            + '</div>'
            + remate("Tres miradas del mismo producto: lo que dice <mark>su descripción</mark>, <mark>sus palabras</mark> exactas y <mark>su foto</mark>.", desde=2))
    add(body, titulo="Ejercicio 4 · el cambio y la configuración", cap=6, t=40, planta=[3, 6], cls="lam-v2", notas=[
        "El cambio es una línea de configuración: rag.hybrid pasa de una lista vacía a BM25 y SigLIP 2. La "
        "búsqueda ahora calcula tres puntajes para cada producto que pasa el filtro: el coseno con la "
        "descripción, que ya estaba; BM25, las palabras; y SigLIP 2, la ficha en una frase contra la foto. Se "
        "estandarizan y se promedian.",
        "[paso] ¿Por qué este cambio? Sale de una limitación medida; es una técnica de Advanced RAG, búsqueda "
        "híbrida y multimodal; y no cuesta nada por pedido, porque corre local.",
        "[paso] En el caso del almohadón, ahora el anotado sale primero.",
    ])

    # ---------------------------------------------------------------- 3 de 3: resultados en las dos versiones
    JV = D["JV"]
    jv = JV["resumen"]
    votos = [v for d in JV["detalle"] for v in d["votos"]]
    vh, vd = votos.count("hibrida"), votos.count("densa")
    p_ver = p_signos(jv["hibrida"]["gana"], jv["densa"]["gana"])
    tres = [HIB] + D["HIB_R"]
    v1s, v2s = [x[V1]["hit@1"] for x in tres], [x[V2]["hit@1"] for x in tres]
    difs_r = " · ".join(sg(x[V2]["vs_base"]["hit@1"]) for x in tres)
    jr = D["JR"]["resumen"]

    def fila(label, a, b, d="", cls=""):
        return f'<div class="dl {cls}">{label}</div><div class="d1 {cls}">{a}</div><div class="d2 {cls}">{b}</div><div class="dd {cls}">{d}</div>'

    tabla = ('<div class="dh"></div><div class="dh c">versión 1</div><div class="dh c v">versión 2</div><div class="dh">diferencia</div>'
             + fila("Configuración", "<code>rag.hybrid: []</code>", "<code>rag.hybrid: [bm25, siglip2]</code>", "densa → densa + léxica + foto")
             + f'<div class="ds">sobre el ground truth · {D["N_ANS"]} consultas con respuesta</div>'
             + fila("hit@1", f(B1["hit@1"]), f(B2["hit@1"]), dif(D21))
             + fila("hit@5 · lo que ve el que elige", f(B1["hit@5"]), f(B2["hit@5"]), dif(D21, "hit@5"))
             + fila("MRR@10", f(B1["mrr@10"]), f(B2["mrr@10"]), dif(D21, "mrr@10"))
             + fila("hit@1 con tres redactores · media ± desvío", media_desvio(v1s), media_desvio(v2s), f"{difs_r}: se repite con los tres")
             + f'<div class="ds">de punta a punta · {JV["ambientes"]} ambientes vacíos reales, el mismo plan, el juez en los dos órdenes</div>'
             + fila("Ambientes que gana", str(jv["densa"]["gana"]), str(jv["hibrida"]["gana"]),
                    f'{JV["empates"]} empates · {vh} votos a {vd} · p = {f(p_ver, 2)}')
             + fila("Productos útiles según el juez", f(jv["densa"]["util"], 2), f(jv["hibrida"]["util"], 2))
             + fila("Costo por pedido", usd(D["c_pedido"]), "igual", "BM25 y SigLIP 2 corren locales"))
    body = ('<div class="cuerpo">' + cab("06", "Ejercicio 4 · 3 de 3 · resultados en las dos versiones",
                                         "Resultados: <em>gana en el banco y no pierde con el juez</em>") + '</div>'
            + f'<div class="dosv">{tabla}</div>'
            + '<div class="dosn" data-desde="1">'
              '<div class="claro"><b>Lo que es claro.</b> En el ground truth, los intervalos de la diferencia no tocan el cero, y la '
              'mejora se repite con los tres redactores.</div>'
              f'<div class="no"><b>Lo que no.</b> De punta a punta son {JV["ambientes"]} ambientes: {jv["hibrida"]["gana"]} a '
              f'{jv["densa"]["gana"]} da p = {f(p_ver, 2)}, y en {JV["empates"]} el juez no se decide. El ruido solo (la versión 2 contra sí misma) reparte '
              f'{jr["hibrida"]["gana"]} a {jr["hibrida_bis"]["gana"]}.</div></div>'
            + remate("La versión 2 es hoy la búsqueda del flujo: clara en el ground truth, y <mark>«no peor, probablemente mejor»</mark> en la tarea real.", desde=1))
    add(body, titulo="Ejercicio 4 · resultados en las dos versiones", cap=6, t=60, planta=[6], cls="lam-dosv", notas=[
        f"Los resultados en las dos versiones. Sobre el ground truth: hit@1 pasa de {f(B1['hit@1'])} a {f(B2['hit@1'])}, "
        f"y hit@5, lo que ve el que elige, de {f(B1['hit@5'])} a {f(B2['hit@5'])}. Las diferencias son pareadas y sus "
        f"intervalos no tocan el cero; con los otros dos redactores, la mejora se repite. De punta a punta, en los "
        f"{JV['ambientes']} ambientes, con el mismo plan y el juez en los dos órdenes: la versión 2 gana "
        f"{jv['hibrida']['gana']}, empata {JV['empates']} y no pierde ninguno. Los productos útiles pasan de "
        f"{f(jv['densa']['util'], 2)} a {f(jv['hibrida']['util'], 2)}, y el costo es el mismo.",
        f"[paso] Con honestidad: lo del ground truth es claro; de punta a punta son once ambientes, cinco a cero da "
        f"p igual a {f(p_ver, 2)}, y en seis el juez no se decide; y la misma configuración corrida dos veces reparte "
        f"{jr['hibrida']['gana']} a {jr['hibrida_bis']['gana']}. Clara en el banco; no peor, probablemente mejor, en la "
        f"tarea real.",
    ])

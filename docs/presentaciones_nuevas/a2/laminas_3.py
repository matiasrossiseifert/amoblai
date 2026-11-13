"""El cierre: el costo (del registro de gastos), las limitaciones, el trabajo futuro (con la réplica
de un ambiente real, que quedó como una prueba), las conclusiones y el gracias; y el anexo (IA
responsable, la grilla completa, la cronología y la planilla de alternativas)."""

from __future__ import annotations

import datetime as dt

import img
import sala
from base import add, cab, esc, f, miles, pct, piezas_hasta, remate, sg, usd
from datos_deck import AMO, BASE, RES, p_signos
from graf import hbars
from laminas_1 import credito, creditos, separador

CORTO = {  # los rótulos del registro de gastos (infra/budget.py), abreviados para el gráfico
    "Evaluación: un VLM ordena el top-10 (ground truth de IKEA)": "evaluar el reranking con un VLM",
    "El flujo: elección de la lista": "el flujo: la elección",
    "Catálogo: descripciones de los productos de ABO": "describir el catálogo de ABO",
    "Evaluación de punta a punta: juez que compara dos listas": "el juez de punta a punta",
    "Experimento: elegir con el catálogo entero en el prompt": "el catálogo entero en el prompt",
    "El flujo: imagen del ambiente amoblado": "el flujo: las imágenes",
    "Réplica de un ambiente real (ubicación de los muebles)": "la réplica de un ambiente",
    "Evaluación del generador: faithfulness": "el generador: faithfulness",
    "El flujo: plan (lee la foto y el pedido, escribe las consultas)": "el flujo: el plan",
    "El flujo: prompt de la imagen escrito por el LLM (una variante)": "la escena escrita por el LLM",
    "Evaluación del generador: answer relevance": "el generador: answer relevance",
}
CIERRE = ["publica-living-japandi", "publica-loft-industrial", "publica-living-bohemio", "publica-comedor-clasico-moderno"]


def build(D: dict, ctx: dict) -> None:
    B1, B2, D21, CAM = D["B1"], D["B2"], D["D21"], D["CAM"]
    T = D["IMG_TOT"]
    JV, JA, JX = D["JV"], D["JA"], D["JX"]
    jv, sa, sx, jr = JV["resumen"], JA["resumen"], JX["resumen"], D["JR"]["resumen"]
    FM = D["FM"]
    n_amb = len(D["pedidos"])
    separador(7, ["Cerramos. El cuarto ya está completo: le faltaban los almohadones."])

    # ---------------------------------------------------------------- el costo
    g = D["gasto"]
    top = sorted(D["por_uso"].items(), key=lambda kv: -kv[1])[:8]
    mx = max(v for _, v in top)
    xm = (int(mx / 4) + 1) * 4
    rows = [dict(label=CORTO.get(k, k), value=v, kind="main" if k.startswith("El flujo") else "alt") for k, v in top]
    led = hbars(rows, width=960, label_w=400, row_h=62, bar_h=20, x_max=xm, ticks=[0, xm / 4, xm / 2, 3 * xm / 4, xm],
                fmt=lambda v: usd(v), tick_fmt=lambda t: f"{t:.0f}", esq=None, res=None, right=130)
    parts = [("plan", D["c_plan"]), ("elección", D["c_choose"]), ("imagen", D["c_img"])]
    tot = D["c_pedido"]
    bar = "".join(f'<div class="cb cb{i}" style="flex:{v / tot:.3f}"><b>{n}</b><span>{usd(v)}</span></div>' for i, (n, v) in enumerate(parts))
    lo, hi = D["c_choose_rango"]
    body = ('<div class="cuerpo">' + cab("07", "Cierre · el costo", "Cuánto cuesta un pedido, <em>y cuánto costó el trabajo</em>") + '</div>'
            + '<div class="costo"><div class="co1">'
            + f'<div class="etq">un pedido</div><div class="gran">≈ {usd(tot)}</div><div class="cbar">{bar}</div>'
            + f'<p class="nota">La elección va de {usd(lo)} a {usd(hi)} según cuántas piezas y de qué catálogo; cada reintento de '
              f'imagen suma {usd(D["c_img"])}. <b>Buscar no cuesta nada</b>: Qwen3, BM25, SigLIP 2 y ChromaDB corren locales.</p>'
            + f'<div class="etq" style="margin-top:36px">todo el trabajo</div><div class="gran g2">{usd(D["gasto_total"])}</div>'
            + f'<p class="nota">Anthropic {usd(g["anthropic"])} (tope de {f(D["topes"]["anthropic"], 0)}) y fal {usd(g["fal"])}. '
              f'{miles(D["n_llamadas"])} llamadas pagas, cada una en un registro con su costo, sus tokens y su latencia; lo ya pagado '
              f'queda en caché.</p></div>'
            + '<div class="co2" data-desde="1"><div class="ley"><span><i style="background:#2453D6"></i>el flujo</span>'
              '<span><i style="background:#9AA4AF"></i>evaluación, catálogo y pruebas</span><span>en qué se fue · registro de gastos</span></div>'
            + led + '</div></div>')
    add(body, titulo="El costo", cap=7, t=25, notas=[
        f"Costos, del registro de gastos. Un pedido cuesta unos {f(100 * tot, 0)} centavos de dólar: "
        f"{f(100 * D['c_plan'], 0)} el plan, {f(100 * D['c_choose'], 0)} la elección y {f(100 * D['c_img'], 0)} la imagen. "
        f"Buscar no cuesta nada: todo corre local.",
        f"[paso] El trabajo entero costó {f(D['gasto_total'], 0)} dólares; lo más caro fue evaluar el reranking con el "
        f"VLM. Cada llamada paga queda registrada, con topes por cuenta, y lo ya pagado queda en caché.",
    ])

    # ---------------------------------------------------------------- limitaciones
    no_sost = 1 - D["RESP"]["faithfulness"]["global"]
    dh = D["DIAG"]["hibrida"]
    S = [
        f"<strong>No dice «no hay»</strong>: cuando el catálogo no tiene lo pedido, pone lo más parecido sin avisar (dejó afuera "
        f"{dh['piezas_dejadas_afuera']} de {dh['piezas']} piezas).",
        f"<strong>El tamaño no se puede verificar</strong>: el límite lo estima el plan a ojo, y solo el {pct(D['ikea_con_medida'])} "
        f"de IKEA tiene alguna medida. El filtro de medidas cambia {FM['candidatos_reemplazados']} de {FM['candidatos']} candidatos, "
        f"sin evidencia de que mejore la lista.",
        f"<strong>La imagen es una visualización</strong>: acierta el producto exacto 4 de cada 10 veces y conserva el cuarto en "
        f"{T['pasan']} de {T['n']}.",
        f"<strong>El generador afirma cosas que no ve</strong>: el {pct(no_sost)} de las afirmaciones del porqué no se sostiene.",
    ]
    Ev = [
        "<strong>El banco de la búsqueda es de producto conocido</strong>, lo escribió el mismo modelo que las descripciones, y "
        "no hay conjunto apartado.",
        f"<strong>De punta a punta son {n_amb} ambientes</strong>, con un juez que es el mismo modelo que elige, sin validar "
        f"contra personas.",
        f"<strong>El ruido solo ya mueve ambientes</strong>: la misma configuración corrida dos veces reparte "
        f"{jr['hibrida']['gana']} a {jr['hibrida_bis']['gana']}.",
        "<strong>El pedido abierto no está evaluado</strong>: los pedidos enumeran las piezas.",
    ]
    body = ('<div class="cuerpo">' + cab("07", "Cierre", "Limitaciones: <em>lo que todavía no podemos afirmar</em>") + '</div>'
            + '<div class="apr lims"><div class="ac lim"><div class="act">del sistema</div>'
            + "".join(f'<div class="apri"><span>–</span><p>{x}</p></div>' for x in S)
            + '</div><div class="ac lim" data-desde="1"><div class="act">de la evaluación</div>'
            + "".join(f'<div class="apri"><span>–</span><p>{x}</p></div>' for x in Ev)
            + "</div></div>"
            + remate("Ninguna invalida la lista: los productos son reales y salen de la búsqueda. Sí acotan <mark>cuánto podemos afirmar</mark>.", desde=1))
    add(body, titulo="Limitaciones", cap=7, t=30, notas=[
        "Limitaciones. Del sistema: no dice «no hay», pone lo más parecido sin avisar; el tamaño no se puede "
        "verificar; la imagen es una visualización; y el generador afirma cosas que no ve.",
        f"[paso] De la evaluación: el banco de la búsqueda es de producto conocido y no hay conjunto apartado; de "
        f"punta a punta son {n_amb} ambientes, con un juez sin validar contra personas; y el ruido solo ya mueve "
        f"ambientes.",
    ])

    # ---------------------------------------------------------------- trabajo futuro, con la réplica
    REP = D["REPLICA"]
    RV = {k: v["resumen"]["iou_medio"]["media"] for k, v in REP["variantes"].items()}
    assert RV["simple_sin_cajas"] < RV["simple_texto"] < RV["simple_cajas"] < RV["simple_cajas_3d"], "la réplica cambió: revisar la lectura"
    RD = RES / "replica" / "living-dagarna"
    mejor = max(REP["variantes"]["simple_cajas_3d"]["imagenes"], key=lambda r: r["iou_medio"])
    rrows = [dict(label="sin indicar el lugar", value=RV["simple_sin_cajas"], kind="alt"),
             dict(label="dicho en palabras", value=RV["simple_texto"], kind="alt"),
             dict(label="rectángulos dibujados", value=RV["simple_cajas"], kind="alt"),
             dict(label="cajas 3D dibujadas", value=RV["simple_cajas_3d"], kind="main")]
    prox = [
        "<strong>Que diga «no hay»</strong>: que el que elige avise cuando ningún candidato cumple, y mostrarlo.",
        "<strong>Un banco escrito por personas</strong>, con un conjunto apartado, y el voto a ciegas del equipo para validar al juez.",
        "<strong>Más ambientes y más repeticiones</strong>: con once, solo se ven las asimetrías grandes.",
        "<strong>Pasarle los materiales al que elige</strong>: hoy ve el tipo y la medida, y adivina la madera por la foto.",
        "<strong>Medidas reales del ambiente</strong>: el filtro de tamaño sería un filtro de verdad.",
        f"<strong>Un modelo más barato para elegir</strong>: hoy es Opus ({usd(D['c_choose'])} por pedido), y no medimos cuánto se pierde.",
    ]
    body = ('<div class="cuerpo">' + cab("07", "Cierre", "Trabajo futuro: <em>del RAG, y de cómo lo medimos</em>") + '</div>'
            + '<div class="fut"><div class="futl"><div class="act">lo próximo</div>'
            + "".join(f'<div class="apri"><span>{i + 1}</span><p>{x}</p></div>' for i, x in enumerate(prox))
            + '</div><div class="futr" data-desde="1"><div class="act r">fuera del RAG · ubicar los muebles · una prueba</div>'
            + hbars(rrows, width=820, label_w=300, row_h=50, bar_h=20, x_max=1.0, top=36, right=110, val_d=2, esq=None, res=None)
            + '<div class="futf">'
            + f'<figure><img src="{img.uri(RD / "real_con_cajas_3d.jpg", 780, 490, q=72)}" alt=""><figcaption>la foto real, con las cajas 3D de sus muebles</figcaption></figure>'
            + f'<figure><img src="{img.uri(RD / mejor["imagen"], 780, 490, q=72)}" alt=""><figcaption>generada con esas cajas sobre la foto vacía</figcaption></figure></div>'
            + f'<p class="nota">IoU medio con la posición real. Un living del ground truth de IKEA, vaciado y vuelto a amoblar con sus '
              f'{len(REP["productos"])} muebles: <b>un solo cuarto, 3 imágenes por variante</b> (en la primera ronda, {f(RV["sin_cajas"], 2)}, '
              f'{f(RV["con_cajas"], 2)} y {f(RV["con_cajas_3d"], 2)}). Lo único que se sostiene: indicar el lugar ayuda.</p>'
            + '</div></div>'
            + remate("Ubicar cada mueble a escala pide medir el ambiente: queda como <mark>trabajo futuro</mark>.", desde=1))
    add(body, titulo="Trabajo futuro", cap=7, t=35, cls="lam-fut", notas=[
        "Trabajo futuro. Lo próximo es del RAG y de cómo lo medimos: que el sistema diga «no hay»; un banco de "
        "consultas escrito por personas, con un conjunto apartado; validar al juez con nuestro voto a ciegas; más "
        "ambientes y más repeticiones. Más lejos: medidas reales del ambiente.",
        "[paso] Y fuera del RAG hicimos una prueba: vaciamos un living real y lo volvimos a amoblar con sus muebles. "
        "Es un solo cuarto; lo único que se sostiene es que indicarle al modelo dónde va cada mueble ayuda.",
    ])

    # ---------------------------------------------------------------- conclusiones
    d_desc = CAM["qwen3|description|filtro-none|consulta-piece"]["vs_anterior"]
    d_hyde = CAM["qwen3|description|filtro-none"]["vs_anterior"]
    fin = {x["slug"]: x for x in D["FINALES"]}
    assert all(fin[s]["img"]["attempts"][0]["ok"] for s in CIERRE), "las del cierre tienen que haber pasado el control al primer intento"
    C = [
        f"<strong>Lo que más pesa es la base de conocimiento y cómo se escribe la consulta</strong>: describir cada producto desde su "
        f"foto ({sg(d_desc['hit@1'], 2)} de hit@1) y escribir la consulta como una ficha ({sg(d_hyde['hit@1'], 2)}). El embedder, en "
        f"este banco, casi no importa.",
        f"<strong>La versión 2 es la búsqueda híbrida</strong>: la descripción, sus palabras y la foto suman {sg(D21['hit@1'])} de "
        f"hit@1, sin costo por pedido; de punta a punta gana {jv['hibrida']['gana']}, empata {JV['empates']} y no pierde.",
        f"<strong>La búsqueda aporta en la tarea real</strong>: {sa['densa']['gana']} a {sa['azar']['gana']} contra candidatos al azar. "
        f"Contra el catálogo entero en el prompt empata ({sx['hibrida']['gana']} a {sx['contexto']['gana']}): RAG es lo que escala, "
        f"no lo que mejora la lista.",
        "<strong>Medir bien fue la mitad del trabajo</strong>: diferencias pareadas, tres redactores, un juez en los dos órdenes y "
        "su piso de ruido. Nos hizo cambiar el número de cabecera y rehacer las métricas del generador.",
        f"<strong>La lista es confiable; la imagen es una visualización</strong>: reconoce el {pct(T['reconocidos'] / T['productos'])} "
        f"de los productos y conserva el cuarto en {T['pasan']} de {T['n']}.",
    ]
    th = "".join(f'<img src="{img.uri(AMO / f"final-{s}" / "final.png", 520, 346, q=72)}" alt="">' for s in CIERRE)
    body = ('<div class="cuerpo">' + cab("07", "Cierre", "Conclusiones") + '</div>'
            + '<div class="concl"><div class="cl">'
            + "".join(f'<div class="apri" data-desde="{i}"><span>{i + 1}</span><p>{x}</p></div>' for i, x in enumerate(C))
            + f'</div><div class="cr"><div class="etq">cuatro de las {T["n"]} corridas de la configuración final</div><div class="cth">{th}</div>'
              f'<p class="credito">Pasaron el control al primer intento. Fotos de los ambientes: {esc(creditos(D, CIERRE))}.</p></div></div>')
    add(body, titulo="Conclusiones", cap=7, t=40, cls="lam-concl", notas=[
        "Para cerrar. Uno: lo que más pesa es la base de conocimiento y cómo se escribe la consulta; el embedder "
        "casi no importa.",
        f"[paso] Dos: la versión 2 es la búsqueda híbrida: suma en el ground truth, sin costo, y de punta a punta "
        f"gana {jv['hibrida']['gana']}, empata {JV['empates']} y no pierde.",
        f"[paso] Tres: la búsqueda aporta en la tarea real, {sa['densa']['gana']} a {sa['azar']['gana']} contra "
        f"candidatos al azar; y contra el catálogo entero en el prompt, empata: RAG es lo que escala.",
        "[paso] Cuatro: medir bien fue medio trabajo; nos hizo cambiar el número de cabecera y rehacer las "
        "métricas del generador.",
        "[paso] Y cinco: la lista es confiable; la imagen es una visualización.",
    ])

    # ---------------------------------------------------------------- gracias
    run = D["run"]
    P = sala.Proj()
    body = ('<div class="g-txt"><div class="etq">amoblai · TP 3 · 73.69 LLM · ITBA 2026</div><h1>Gracias</h1>'
            '<p class="g-sub">¿Preguntas?</p></div>'
            '<div class="equipo"><span class="etq">grupo</span>Juan Bautista Albertoni Salini<br>Matias Juan Rossi Seifert<br>Junior Rambau</div>'
            f'<div class="g-sala">{sala.sala(piezas_hasta(7), P=P)}</div>'
            '<div class="g-fotos">'
            f'<figure><div class="foto"><img src="{img.uri(run["dir"] / "room.jpg", 600, 450, q=74)}" alt=""></div><figcaption>la foto</figcaption></figure>'
            '<span class="gf">→</span>'
            f'<figure><div class="foto"><img src="{img.uri(run["dir"] / "final.png", 600, 450, q=76)}" alt=""></div><figcaption>amoblai</figcaption></figure>'
            f'<p class="pie-foto">El living del recorrido. Foto del ambiente: {esc(credito(D, run["slug"]))}.</p></div>')
    add(body, titulo="Gracias", cap=7, t=10, cls="oscura gracias sin-pie", notas=[
        "Les dejamos el living del recorrido, amoblado por amoblai. Gracias; ¿preguntas?",
    ])

    anexo(D)


# ---------------------------------------------------------------- anexo

VARIANTES = [
    ("Qué se indexa", [("texto del vendedor", "no"), ("descripción de 8 líneas", "si"), ("nombre + descripción", "no")], "E1"),
    ("La consulta", [("solo el kind", "no"), ("solo la línea Type", "no"), ("la frase natural", "no"), ("la ficha de 8 líneas", "si")], "E2"),
    ("Buscador", [("densa", "no"), ("léxica", "no"), ("por foto", "no"), ("densa + léxica + foto", "si")], "E3"),
    ("Candidatos por pieza", [("3", "no"), ("5", "si"), ("8", "no")], "E5"),
    ("Catálogo", [("IKEA", "no"), ("ABO", "no"), ("IKEA + ABO", "si")], "E6"),
    ("Embedder", [("hashing", "no"), ("BM25", "no"), ("BGE-base", "no"), ("Qwen3-Embedding", "si")], "E9"),
    ("Dimensión", [("32 · 128 · 512", "no"), ("1024", "si")], "E10"),
    ("Documento", [("un producto entero", "si"), ("una línea por chunk", "no"), ("línea contra línea", "no")], "E11"),
    ("Base vectorial", [("ChromaDB, HNSW", "si"), ("búsqueda exacta", "no")], "E12"),
    ("Filtro de metadata", [("ninguno", "no"), ("tipo grueso", "no"), ("kind fino", "si")], "E13"),
    ("Reranker de texto", [("ninguno", "si"), ("MiniLM", "no"), ("Qwen3-Reranker", "no")], "E14"),
    ("Prompt de la imagen", [("el LLM escribe la escena", "no"), ("plantilla, edición estricta", "si")], "E15"),
    ("Modelo de imagen", [("Nano Banana 2", "si"), ("Nano Banana Pro", "pend"), ("gpt-image", "pend")], "sin correr"),
]


def anexo(D: dict) -> None:
    o = D["RER"][BASE + "|rerank-opus"]

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
    body = ('<div class="cuerpo">' + cab("A", "Anexo", "IA responsable y producción <em>(Ejercicio 3)</em>") + '</div>'
            + '<div class="rai"><div class="rh">riesgo</div><div class="rh">qué puede pasar</div><div class="rh">cómo lo mitigamos</div>'
            + "".join(f'<div class="r1">{esc(a)}</div><div class="r2">{esc(bb)}</div><div class="r3">{esc(c)}</div>' for a, bb, c in rai)
            + "</div>")
    add(body, titulo="IA responsable", cap=9, t=0, anexo="A", notas=[
        "Lámina de respaldo para la discusión del ejercicio 3: riesgos de IA responsable y estrategia de "
        "producción. Lo marcado «ya» está implementado en el prototipo.",
    ])

    M = D["ABL"]
    keys = list(M)
    filas = []
    for k in keys:
        m = M[k]
        corto = (k.replace("description", "desc.").replace("name+desc.", "nombre+desc.").replace("filtro-", "")
                 .replace("rerank-minilm-reranker", "rerank MiniLM").replace("consulta-", "consulta ")
                 .replace("chunks-lines-", "chunks ").replace("seller", "vendedor").replace("|", " · "))
        filas.append(f'<div class="ab1{" hi" if k == "qwen3|description|filtro-kind" else ""}">{esc(corto)}</div>'
                     + "".join(f'<div class="ab2">{f(m[x])}</div>' for x in ("hit@1", "hit@10", "mrr@10", "ndcg@10", "context_recall@3")))
    hdr = ('<div class="abh">método</div><div class="abh">hit@1</div><div class="abh">hit@10</div>'
           '<div class="abh">MRR@10</div><div class="abh">NDCG@10</div><div class="abh">CR@3</div>')
    half = (len(filas) + 1) // 2
    body = ('<div class="cuerpo">' + cab("B", "Anexo", f"La grilla de octubre <em>({len(keys)} configuraciones)</em>") + '</div>'
            + f'<div class="abl"><div class="abt">{hdr}{"".join(filas[:half])}</div><div class="abt">{hdr}{"".join(filas[half:])}</div></div>'
            + f'<p class="nota abn">{D["N_ANS"]} consultas · catálogo de {D["n_ikea"]} · embedder · texto · filtro · variante. En azul, la '
              f'búsqueda de la versión 1 (la densa, con filtro por kind); la versión 2 (híbrida) da hit@1 {f(D["B2"]["hit@1"])}. Un VLM '
              f'reordenando el top-10: {f(o["hit@1"])}.</p>')
    add(body, titulo="La grilla completa", cap=9, t=0, anexo="B", notas=[
        "Lámina de respaldo: todas las configuraciones de la grilla (embedder, texto, filtro, dimensión, chunks), "
        "por si preguntan por alguna combinación. Las diferencias entre filas vecinas hay que leerlas con la "
        "diferencia pareada, no con estos números sueltos.",
    ])

    linea_de_tiempo(D, "C")

    out = ['<div class="planilla"><div class="ph">decisión</div><div class="ph">alternativas</div><div class="ph d">experimento</div>']
    for st, ops, e in VARIANTES:
        chips = ""
        for op, s_ in ops:
            c = {"pend": "chip pend"}.get(s_, "chip si" if s_ == "si" else "chip")
            chips += f'<span class="{c}">{esc(op)}</span>'
        out.append(f'<div class="pd">{esc(st)}</div><div class="pa">{chips}</div><div class="px"><span class="xe{" pend" if not e.startswith("E") else ""}">{e}</span></div>')
    out.append("</div>")
    body = ('<div class="cuerpo">' + cab("D", "Anexo · la planilla", "Cada decisión tuvo alternativas: <em>lo que quedó</em>") + '</div>'
            + "".join(out))
    add(body, titulo="La planilla de alternativas", cap=9, t=0, anexo="D", cls="lam-decidimos", notas=[
        "Lámina de respaldo: las alternativas de cada decisión, la que quedó y el experimento que la midió. Del E9 "
        "al E15 son los de trámite: el experimento no siempre sostiene la elección (el embedder y el filtro quedan "
        "por otra razón). En la charla, esto lo cuenta el mapa de experimentos.",
    ])


def linea_de_tiempo(D: dict, anexo: str) -> None:
    """La cronología del proyecto (anexo: la charla la reemplaza por el recorrido)."""
    fe = D["fechas"]
    dd = lambda d: d.strftime("%d/%m")
    evs = [
        ("v0", fe["v0"], "La propuesta: buscar por imagen", "Detectar cada mueble, recortarlo y compararlo con las fotos del catálogo. Se construyó y se midió su buscador.", 0),
        ("", fe["v1"], "RAG por texto", f"Descripciones de ocho líneas, Qwen3 y ChromaDB, sobre {D['n_275']} productos.", 0),
        ("", fe["rerank"], "Elegir con un VLM, y más catálogo", f"Opus ordena mirando las fotos. El catálogo pasa a {D['n_855']}: lámparas, deco, guardado.", 1),
        ("", fe["metricas"], "Métricas de la clase", "Context precision y recall, NDCG, tres redactores y relevancia graduada.", 1),
        ("", fe["revisado"], "Catálogo revisado", f"Se sacan {D['n_855'] - D['n_ikea']} productos con la foto de otro o fuera del alcance: quedan {D['n_ikea']}.", 2),
        ("", fe["abo"], "Un segundo catálogo", f"Amazon Berkeley Objects: {D['n_abo']} productos más, con medidas.", 2),
        ("", fe["revision"], "Revisión crítica y versión 2", "Diferencias pareadas, métricas del generador rehechas y búsqueda híbrida.", 2),
        ("sig", None, "Lo que sigue", "Que diga «no hay», un banco escrito por personas, validar al juez.", 2),
    ]
    x0, x1, yax = 100, 1550, 610
    gap = (x1 - x0) / (len(evs) - 1)
    tl = (f'<svg class="tl-eje" viewBox="0 0 1920 1080"><line x1="72" y1="{yax}" x2="1848" y2="{yax}"/>'
          + "".join(f'<line class="tk" x1="{x0 + i * gap - 9:.0f}" y1="{yax + 9}" x2="{x0 + i * gap + 9:.0f}" y2="{yax - 9}"/>' for i in range(len(evs)))
          + "</svg>")
    for i, (cls, d, h, p, st) in enumerate(evs):
        up = i % 2 == 0
        x = x0 + i * gap
        sty = f"left:{x - 1:.0f}px;" + ("bottom:" + str(1080 - yax + 30) + "px" if up else "top:" + str(yax + 30) + "px")
        tl += (f'<div class="ev {cls} {"up" if up else "dn"}" style="{sty}"{" data-desde=" + chr(34) + str(st) + chr(34) if st else ""}>'
               f'<div class="evd">{dd(d) if d else "después"}</div><h4>{esc(h)}</h4><p>{esc(p)}</p></div>')
    antes = fe["revision"] - dt.timedelta(days=1)
    body = ('<div class="cuerpo">' + cab(anexo, "Anexo · cronología", "Cómo se fue <em>transformando</em>") + '</div>'
            f'<div class="tl">{tl}</div>'
            + remate(f"La versión 1 es el sistema hasta el {dd(antes)}; la versión 2, <mark>la búsqueda híbrida</mark> del {dd(fe['revision'])}.", desde=2))
    add(body, titulo="Línea de tiempo", cap=9, t=0, anexo=anexo, notas=[
        f"Lámina de respaldo: la cronología. El {dd(fe['v0'])} arrancamos con la propuesta aprobada, que buscaba por "
        f"imagen; medimos su buscador y el {dd(fe['v1'])} pasamos a RAG por texto.",
        "[paso] Después vinieron la elección con un VLM, un catálogo más grande y las métricas de la clase.",
        f"[paso] En noviembre revisamos el catálogo a mano, sumamos un segundo catálogo y, el {dd(fe['revision'])}, la "
        f"revisión crítica: de ahí sale la versión 2.",
    ])

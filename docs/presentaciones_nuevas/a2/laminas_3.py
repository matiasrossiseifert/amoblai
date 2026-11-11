"""El cierre: lo que decidimos, el camino de los números, los costos, lo aprendido, los pasos a
futuro, el gracias y el anexo."""

from __future__ import annotations

import img
import sala
from base import KIND_ES, add, cab, esc, f, pct, piezas_hasta, remate, usd
from datos_deck import RES
from graf import hbars
from laminas_1 import separador, variantes_html
from laminas_r import futuro_slides

A = RES / "amoblar"


def ci(m, k="hit@1"):
    return tuple(m[f"{k}_ic95"])


def build(D: dict, ctx: dict) -> None:
    b, o = D["best"], D["opus"]
    separador(7, ["Cerramos. El cuarto ya está completo: le faltaban los almohadones."])

    # ---------------------------------------------------------------- lo que decidimos
    body = ('<div class="cuerpo">' + cab("07", "Cierre", "Lo que decidimos, <em>y qué experimento lo decidió</em>") + '</div>'
            + variantes_html(elegidas=True))
    add(body, titulo="Lo que decidimos", cap=7, t=25, cls="lam-decidimos", notas=[
        "Volvemos a la planilla del principio, ahora con lo que elegimos en cada fila y el experimento que lo "
        "decidió.",
        "Descripciones de ocho líneas, Qwen3 entero, Chroma, un documento por producto; la consulta reescrita "
        "en ocho líneas; un modelo que ve para elegir entre cinco; los dos catálogos; y edición estricta con "
        "control SIFT. El modelo de imagen es el único que quedó sin medir.",
    ])

    # ---------------------------------------------------------------- el camino
    rows = [dict(label="naive: texto del vendedor", value=D["naive"]["hit@1"], ci=ci(D["naive"]), kind="muted",
                 sub="hashing de palabras, sin filtro"),
            dict(label="+ descripciones de ocho líneas", value=D["desc_hash"]["hit@1"], ci=ci(D["desc_hash"]), kind="alt", sub="E2"),
            dict(label="+ Qwen3, filtro, ChromaDB", value=b["hit@1"], ci=ci(b), kind="alt", sub="E2 · E4 · E5"),
            dict(label="+ reranking mirando las fotos", value=o["hit@1"], ci=ci(o), kind="main", sub="E7")]
    body = ('<div class="cuerpo">' + cab("07", "Cierre · el camino", f"De {f(D['naive']['hit@1'])} a {f(o['hit@1'])} de hit@1, <em>paso a paso</em>") + '</div>'
            + '<div class="camino">' + f'<div class="ley"><span>hit@1 · IC 95% · {D["n_resp"]} búsquedas · catálogo de {D["n_ikea"]}</span></div>'
            + hbars(rows, width=1776, label_w=520, row_h=124, bar_h=40, x_max=0.8, ticks=[0, .2, .4, .6, .8],
                    refs=[(D["azar_h1"], f"azar {f(D['azar_h1'])}")], esq=None, res=None, right=150)
            + '</div>'
            + remate("El salto más grande lo dio <mark>qué texto guardamos</mark>, no el modelo."))
    add(body, titulo="El camino", cap=7, t=25, notas=[
        f"El camino de los números. El punto de partida ingenuo, texto del vendedor y contar palabras, da "
        f"{f(D['naive']['hit@1'])}. Escribir nuestras descripciones lo lleva a {f(D['desc_hash']['hit@1'])}: el "
        f"salto más grande lo dio qué texto guardamos, no el modelo. Qwen3, filtro y Chroma suman poco más, hasta "
        f"{f(b['hit@1'])}. Y un modelo que mira las fotos al final lo lleva a {f(o['hit@1'])}.",
    ])

    # ---------------------------------------------------------------- costos
    gp = D["gasto_paso"]
    nombres = {"eval.rerank": "evaluación: reranking", "catalog.describe": "catálogo: descripciones ABO",
               "furnish.choose": "flujo: choose", "eval.juez_listas": "evaluación: juez de listas",
               "furnish.plan": "flujo: plan", "furnish.generate": "flujo: imágenes", "furnish.scene": "flujo: scene (antes con LLM)",
               "eval.replica.sin_cajas": "réplica: sin cajas", "eval.replica.con_cajas": "réplica: cajas 2D",
               "eval.replica.con_cajas_3d": "réplica: cajas 3D", "eval.replica.vaciar": "réplica: vaciar la foto"}
    mx = max(gp.values())
    xm = (int(mx / 4) + 1) * 4
    rows = [dict(label=nombres.get(k, k), value=v, kind="main" if k.startswith("furnish") else "alt")
            for k, v in sorted(gp.items(), key=lambda kv: -kv[1])]
    led = hbars(rows, width=960, label_w=370, row_h=min(66, 640 // max(1, len(rows))), bar_h=20, x_max=xm, ticks=[0, xm / 4, xm / 2, 3 * xm / 4, xm],
                fmt=lambda v: usd(v), tick_fmt=lambda t: f"{t:.0f}", esq=None, res=None, right=130)
    parts = [("plan", D["costo_plan"]), ("choose", D["costo_choose"]), ("imagen", D["img_precio"])]
    tot = D["costo_corrida"]
    bar = "".join(f'<div class="cb cb{i}" style="flex:{v / tot:.3f}"><b>{n}</b><span>{usd(v)}</span></div>' for i, (n, v) in enumerate(parts))
    body = ('<div class="cuerpo">' + cab("07", "Cierre · costos", "Lo que <em>cuesta</em>") + '</div>'
            + '<div class="costo"><div class="co1">'
            + f'<div class="etq">una corrida del flujo</div><div class="gran">≈ {usd(tot)}</div><div class="cbar">{bar}</div>'
            + f'<p class="nota">Promedio de las corridas de punta a punta. Cada reintento de imagen suma {usd(D["img_precio"])}. '
              f'Choose tarda {f(D["lat_choose"], 0)} s (mediana): mira {D["k_flujo"]} fotos por pieza.</p>'
            + f'<div class="etq" style="margin-top:44px">en todo el trabajo</div><div class="gran g2">{usd(D["gasto_total"])}</div>'
            + f'<p class="nota">{D["n_llamadas"]} llamadas pagas en el registro de gastos, desde el {D["fechas"]["v1"].strftime("%d/%m")}. '
              'El retrieval, los embeddings y todas las métricas de imagen corren local, gratis.</p></div>'
            + '<div class="co2" data-desde="1"><div class="ley"><span><i style="background:#2453D6"></i>el flujo</span>'
              '<span><i style="background:#9AA4AF"></i>evaluación y catálogo</span><span>registro de gastos, por paso</span></div>'
            + led + '</div></div>')
    add(body, titulo="Costos", cap=7, t=25, notas=[
        f"Lo que cuesta. Una corrida del flujo, unos {usd(tot)}: plan, choose, que es lo más caro porque mira "
        f"fotos, y la imagen, más {usd(D['img_precio'])} por cada reintento.",
        f"[paso] En todo el trabajo gastamos {usd(D['gasto_total'])} registrados, y lo que más se llevó fue "
        f"evaluar: el reranking con Opus sobre todas las búsquedas. Todo lo demás, el retrieval, los embeddings y "
        f"las métricas de imagen, corre local y gratis.",
    ])

    # ---------------------------------------------------------------- aprendizajes y límites
    L = [
        f"Lo que más pesa es <strong>qué texto se indexa y cómo se escribe la consulta</strong>: descripciones y "
        f"query rewriting llevan hit@1 de {f(D['naive']['hit@1'], 2)} a {f(D['desc_hash']['hit@1'], 2)}; el embedder suma poco.",
        f"Un <strong>modelo que ve</strong>, al final, vale más que cualquier ajuste fino del retrieval: "
        f"+{f(o['hit@1'] - b['hit@1'], 2)} de hit@1.",
        "<strong>Intervalos y repeticiones</strong> evitaron conclusiones falsas: filtros, dimensiones y embedders "
        "que parecían mejores eran ruido.",
        "Las métricas sin ground truth, el juez y RAGAS, encontraron lo que hit@k no ve: <strong>medidas que "
        "faltan</strong> y un catálogo que no alcanza para otros estilos.",
    ]
    Lim = [
        "La imagen se midió con <strong>una imagen por variante</strong>. T4 está diseñado para eso.",
        "El ground truth es de IKEA: <strong>ABO solo se evaluó con un juez</strong>.",
        f"Los jueces son <strong>Claude evaluando a Claude</strong>. Validamos el juez contra las anotaciones "
        f"({pct(D['grad']['acuerdo_con_gt']['anotado_con_2'])} contra {pct(D['grad']['acuerdo_con_gt']['otros_con_2'])}), no contra personas.",
        "Los asientos de IKEA <strong>no tienen medidas</strong>: el filtro por tamaño no los alcanza.",
    ]
    body = ('<div class="cuerpo">' + cab("07", "Cierre", "Lo que aprendimos, <em>y lo que todavía no sabemos</em>") + '</div>'
            + '<div class="apr"><div class="ac"><div class="act">aprendimos</div>'
            + "".join(f'<div class="apri"><span>{i + 1}</span><p>{x}</p></div>' for i, x in enumerate(L))
            + '</div><div class="ac lim" data-desde="1"><div class="act">límites</div>'
            + "".join(f'<div class="apri"><span>–</span><p>{x}</p></div>' for x in Lim)
            + "</div></div>")
    add(body, titulo="Aprendizajes y límites", cap=7, t=55, notas=[
        "Cuatro cosas que aprendimos. Uno: lo que más pesó fue qué texto guardamos y cómo escribimos la "
        "consulta, más que el modelo de embeddings. Dos: un modelo que ve, al final, vale más que cualquier "
        "ajuste fino del retrieval. Tres: medir con intervalos y repetir nos salvó de declarar ganadoras a "
        "varias cosas que eran ruido. Cuatro: las métricas sin ground truth encontraron problemas que hit@k no "
        "veía, como las medidas que faltan.",
        "[paso] Y los límites, con honestidad: la imagen se midió con muy pocas imágenes; ABO solo tiene "
        "evaluación con juez; los jueces son Claude evaluando a Claude, validados contra las anotaciones pero "
        "no contra personas; y los asientos de IKEA siguen sin medidas.",
    ])

    # ---------------------------------------------------------------- pasos a futuro
    futuro_slides(D)

    # ---------------------------------------------------------------- gracias
    cc = A / "caballito-comedor"
    cch = D["img"]["caballito-comedor"]["choice"]["answer"]["choices"]
    nombres_cc = []
    for c in cch:
        k = D["items"][c["id"]]["kind"]
        q = c.get("quantity", 1)
        nm = KIND_ES.get(k, k)
        nombres_cc.append(f"{q} {nm}s" if q > 1 and not nm.endswith("s") else nm)
    lista_cc = ", ".join(nombres_cc[:-1]) + " y " + nombres_cc[-1]
    P = sala.Proj()
    body = ('<div class="g-txt"><div class="etq">amoblai · TP 3 · 73.69 LLM · ITBA 2026</div><h1>Gracias</h1>'
            '<p class="g-sub">¿Preguntas?</p></div>'
            '<div class="equipo"><span class="etq">grupo</span>Juan Bautista Albertoni Salini<br>Matias Juan Rossi Seifert<br>Junior Rambau</div>'
            f'<div class="g-sala">{sala.sala(piezas_hasta(7), P=P)}</div>'
            '<div class="g-fotos">'
            f'<figure><div class="foto"><img src="{img.uri(cc / "room.jpg", 600, 450, q=74)}" alt=""></div><figcaption>la foto</figcaption></figure>'
            '<span class="gf">→</span>'
            f'<figure><div class="foto"><img src="{img.uri(cc / "final.png", 600, 450, q=76)}" alt=""></div><figcaption>amoblai</figcaption></figure>'
            f'<p class="pie-foto">El comedor del mismo departamento, con {esc(lista_cc)} del catálogo.</p></div>')
    add(body, titulo="Gracias", cap=7, t=15, cls="oscura gracias sin-pie", notas=[
        "Les dejamos el comedor del mismo departamento, amoblado por amoblai. Gracias; ¿preguntas?",
    ])

    # ---------------------------------------------------------------- anexo
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

    keys = list(D["M"])
    filas = []
    for k in keys:
        m = D["M"][k]
        corto = (k.replace("description", "desc.").replace("name+desc.", "nombre+desc.").replace("filtro-", "")
                 .replace("rerank-minilm-reranker", "rerank MiniLM").replace("consulta-", "consulta ")
                 .replace("chunks-lines-", "chunks ").replace("seller", "vendedor").replace("|", " · "))
        filas.append(f'<div class="ab1{" hi" if k == "qwen3|description|filtro-type" else ""}">{esc(corto)}</div>'
                     + "".join(f'<div class="ab2">{f(m[x])}</div>' for x in ("hit@1", "hit@10", "mrr@10", "ndcg@10", "context_recall@3")))
    hdr = ('<div class="abh">método</div><div class="abh">hit@1</div><div class="abh">hit@10</div>'
           '<div class="abh">MRR@10</div><div class="abh">NDCG@10</div><div class="abh">CR@3</div>')
    half = (len(filas) + 1) // 2
    body = ('<div class="cuerpo">' + cab("B", "Anexo", f"La ablación completa <em>({len(keys)} configuraciones)</em>") + '</div>'
            + f'<div class="abl"><div class="abt">{hdr}{"".join(filas[:half])}</div><div class="abt">{hdr}{"".join(filas[half:])}</div></div>'
            + f'<p class="nota abn">{D["n_resp"]} búsquedas · catálogo de {D["n_ikea"]} · embedder · texto · filtro · variante. '
              f'Reranking con Opus: hit@1 {f(o["hit@1"])}.</p>')
    add(body, titulo="Ablación completa", cap=9, t=0, anexo="B", notas=[
        "Lámina de respaldo: todas las configuraciones de la ablación final, por si preguntan por alguna "
        "combinación.",
    ])

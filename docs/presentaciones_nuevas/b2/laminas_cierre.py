"""El cierre (el ejemplo de punta a punta lo absorbió el recorrido, fases 9 y 10): la iteración, el camino, el costo, las limitaciones, el paso a
futuro (el producto con medidas reales; las cajas se probaron en el experimento 13), las conclusiones y gracias."""

from __future__ import annotations

from datos import (D, HERO, N_HERO, ROOM_CHECK, f2, f3, usd)
from piezas import codigo_barras, flujo, foto, kick
from registro import lam

# =============================================================================================
# La iteración (ejercicio 4): un ticket ancho
# =============================================================================================
_b, _op = D["e7_base"], D["e7_opus"]
_e3v, _e5v = D["curva"][3]["acierto_eleccion"], D["curva"][5]["acierto_eleccion"]
_jo = D["j_otros"]
ITER = [
    ("En un ambiente vacío no hay nada que recortar", "Búsqueda por texto (v1)", f"hit@1 {f2(D['v0_hit1'])} → {f2(D['v1_hit1'])}"),
    ("El texto del vendedor no describe lo que se ve", "Descripción de 8 líneas con un VLM", f"hit@1 {f2(D['e1_vendedor'])} → {f2(D['e1_desc'])}"),
    ("Una consulta corta no distingue un sofá de otro", "La consulta completa que escribe el plan", f"hit@1 {f2(D['e6_kind'])} → {f2(D['e6_hnsw'])}"),
    ("El correcto estaba en el top-10, pero no primero", "Un VLM elige mirando las fotos", f"hit@1 {f2(_b[0])} → {f2(_op[0])}"),
    ("Con 3 candidatos faltaba el correcto en 1 de cada 4 piezas", f"{D['k_flujo']} candidatos por pieza", f"elección {f3(_e3v)} → {f3(_e5v)}"),
    ("Pedían bibliotecas, lámparas y cortinas, y no había", "Catálogo ampliado y revisado", f"{D['prod_268']} → {D['prod_819']} productos"),
    ("Una sola estética: la nórdica", "IKEA + Amazon", f"otros estilos {_jo['b']} a {_jo['a']} · útiles {f2(_jo['util_a'])} → {f2(_jo['util_b'])}"),
    ("La imagen redecoraba el cuarto", "Edición estricta + control SIFT", f"SIFT {D['e12']['experimento-buen-pedido'][0]} → {D['e12']['experimento-buen-pedido-estricto'][0]} puntos"),
]
_it = "".join(f'<div class="it-l"><span class="it-n">{i:02d}</span><span class="it-p">{p}</span><span class="it-c">{c}</span>'
              f'<span class="it-m">{m_}</span></div>' for i, (p, c, m_) in enumerate(ITER, 1))
lam("iteracion", "La iteración", "Cierre", f'''
{kick("05", "cierre · ejercicio 4")}
<h2 class="t chico">La iteración: <em>qué falló, qué cambiamos y cuánto mejoró</em></h2>
<div class="ticket iter-tk">
  <div class="it-cab"><span></span><span>el problema que encontramos usando el sistema</span><span>qué cambiamos</span><span>cuánto mejoró</span></div>
  {_it}
  <div class="tk-pie iter-pie"><span>todos salen de los experimentos</span>{codigo_barras("iteracion", 220, 30)}</div>
</div>''',
    "Esto es el ejercicio 4 en un ticket: cada línea es un problema que encontramos usando el sistema, el cambio que hicimos y "
    "cuánto mejoró. Todos salen de los experimentos que acabamos de ver.",
    35, clase="clara")

# =============================================================================================
# El camino: cascada de hit@1
# =============================================================================================


def _camino_svg():
    W, H = 1728, 560
    n = len(D["camino"])
    bw = 230
    x0 = 110
    gap = (W - x0 - 20 - n * bw) / (n - 1)
    base, top = 470, 70
    sy = lambda v: base - (base - top) * v / 0.8  # noqa: E731
    o = [f'<svg class="graf-l camino" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    for t in (0, 0.2, 0.4, 0.6, 0.8):
        o.append(f'<line x1="{x0 - 20}" y1="{sy(t)}" x2="{W}" y2="{sy(t)}" class="gl-grilla"/>'
                 f'<text x="{x0 - 34}" y="{sy(t) + 6}" class="gl-eje" text-anchor="end">{f2(t)}</text>')
    prev = None
    for i, (et, v) in enumerate(D["camino"]):
        x = x0 + i * (bw + gap)
        ult = i == n - 1
        o.append(f'<g class="cm-b{" gana" if ult else ""}" data-paso="{i}">')
        if prev is not None:
            o.append(f'<line x1="{x - gap}" y1="{sy(prev)}" x2="{x}" y2="{sy(prev)}" class="cm-guia"/>')
        o.append(f'<rect x="{x}" y="{sy(v)}" width="{bw}" height="{sy(0) - sy(v)}" rx="3"/>')
        o.append(f'<text x="{x + bw / 2}" y="{sy(v) - 18}" class="cm-v" text-anchor="middle">{f2(v)}</text>')
        if prev is not None:
            d = v - prev
            o.append(f'<text x="{x + bw / 2}" y="{sy(v) - 62}" class="cm-d" text-anchor="middle">{"+" if d >= 0 else "−"}{f2(abs(d))}</text>')
        words, l1, l2 = et.split(" "), [], []
        for w_ in words:
            (l1 if len(" ".join(l1 + [w_])) <= 19 and not l2 else l2).append(w_)
        o.append(f'<text x="{x + bw / 2}" y="{sy(0) + 38}" class="cm-et" text-anchor="middle">{" ".join(l1)}</text>')
        if l2:
            o.append(f'<text x="{x + bw / 2}" y="{sy(0) + 66}" class="cm-et" text-anchor="middle">{" ".join(l2)}</text>')
        o.append("</g>")
        prev = v
    o.append("</svg>")
    return "".join(o)


lam("camino", "El camino", "Cierre", f'''
{kick("05", "cierre · resumen")}
<h2 class="t chico">El camino: de {f2(D["camino"][0][1])} a <em>{f2(D["camino"][-1][1])}</em> de hit@1</h2>
<div class="camino-w">{_camino_svg()}</div>
<p class="remate" data-paso="{len(D["camino"]) - 1}">Lo que más movió el número fue <mark>qué texto se indexa</mark>; lo segundo, que un VLM mire las fotos.</p>''',
    [f"El resumen en un gráfico: cada barra suma un cambio a la anterior. Arrancamos con el texto del vendedor y una bolsa de "
     f"palabras: {f2(D['camino'][0][1])}.",
     f"La descripción del VLM: {f2(D['camino'][1][1])}.",
     f"Qwen3: {f2(D['camino'][2][1])}.",
     "El filtro por tipo no mueve hit@1: lo que protege es hit@10.",
     f"Y el VLM reordenando el top-10: {f2(D['camino'][-1][1])}. Lo que más movió el número fue qué texto se indexa; lo "
     "segundo, que un VLM mire las fotos."],
    35, clase="clara")

# =============================================================================================
# Cuánto cuesta
# =============================================================================================
lam("costo", "Cuánto cuesta", "Cierre", f'''
{kick("05", "cierre · costo")}
<h2 class="t chico">Cuánto cuesta <em>un pedido</em></h2>
<div class="ticket costo-tk">
  <div class="tk-cab"><b>amoblai</b><span>un pedido<br>configuración final</span></div>
  <div class="tk-l"><span class="tk-n">Plan + elección · Claude Opus</span><span class="tk-dots"></span><b>{usd(D['costo_claude'])}</b></div>
  <div class="tk-l"><span class="tk-n">Imagen · Nano Banana 2, por intento</span><span class="tk-dots"></span><b>{usd(D['costo_imagen'])}</b></div>
  <div class="tk-l"><span class="tk-n">Embeddings y base vectorial · locales</span><span class="tk-dots"></span><b>{usd(0)}</b></div>
  <div class="tk-tot"><span>costo único · describir el catálogo, por producto</span><span>{usd(D['costo_describir'], 3)}</span></div>
  <p class="tk-pie">plan + elección: promedio en los {D['costo_n']} ambientes de la evaluación de punta a punta</p>
  {codigo_barras("costo", 260, 34)}
</div>
<div class="costo-notas">
  <div><h4>Todo gasto queda registrado</h4><p>Cada llamada paga, con su costo, y con topes por cuenta: lo que pase el tope se rechaza.</p></div>
  <div><h4>Repetir no se vuelve a pagar</h4><p>Las respuestas de los jueces y los rerankers quedan en caché.</p></div>
  <div><h4>Menos de un centavo por producto</h4><p>Describir el catálogo se paga una sola vez.</p></div>
</div>''',
    f"Un pedido cuesta unos {round(D['costo_claude'] * 100)} centavos de dólar de Claude y {round(D['costo_imagen'] * 100)} por "
    "intento de imagen. Describir el catálogo es un costo único, de menos de un centavo por producto. Embeddings y base "
    "vectorial corren locales. Todo gasto queda registrado, con topes por cuenta, y las respuestas de los jueces quedan en "
    "caché: repetir un experimento no se vuelve a pagar.",
    25)

# =============================================================================================
# Limitaciones
# =============================================================================================
LIM = ["Los catálogos son viejos y de uso no comercial", "Las medidas del ambiente se estiman a ojo",
       "El ground truth es uno solo, con consultas escritas por modelos", "La imagen es una visualización: escala y luz aproximadas",
       "Tenemos pocos ambientes vacíos"]
FUT = ["El catálogo de un vendedor actual, con precio y stock", "Más ambientes y evaluación humana",
       "Que el usuario cambie una pieza y se regenere solo eso"]
lam("limites", "Limitaciones", "Cierre", f'''
{kick("05", "cierre · limitaciones")}
<h2 class="t chico">Lo que <em>todavía no resuelve</em></h2>
<div class="lim-dos">
  <div><span class="et">limitaciones</span><ol class="lim">{"".join(f"<li>{x}</li>" for x in LIM)}</ol></div>
  <div data-paso="1"><span class="et">además, a futuro</span><ol class="lim fut">{"".join(f"<li>{x}</li>" for x in FUT)}</ol>
    <p class="lim-sig">Y las medidas reales, que son lo que sigue →</p></div>
</div>''',
    ["Limitaciones: los catálogos son viejos y de uso no comercial; las medidas del ambiente se estiman a ojo; el ground truth "
     "es uno solo y con consultas escritas por modelos; la imagen es una visualización, con escala y luz aproximadas; y tenemos "
     "pocos ambientes vacíos.",
     "A futuro: el catálogo de un vendedor actual, con precio y stock; más ambientes y evaluación humana; que el usuario "
      "cambie una pieza y regenere solo eso. Y lo más importante, las medidas reales, que mostramos ahora."],
    30)

# =============================================================================================
# Pasos a futuro: el producto con medidas reales
# =============================================================================================
_pasos = [("Medir el ambiente", "Una app móvil con el <b>LiDAR</b> del teléfono escanea el cuarto: paredes, aberturas y medidas reales."),
          ("Medidas de cada producto", "Ancho, profundidad y alto en la metadata del catálogo: la <b>caja 3D a escala</b> de cada mueble."),
          ("Ubicar las cajas", "<i class=\"op\"><b>a.</b> En el plano, la IA decide dónde va cada caja (circulación, aberturas, el pedido).</i>"
           "<i class=\"op\"><b>b.</b> Una primera generación pone los muebles; se toma dónde quedó cada uno y ahí va su caja a escala.</i>"),
          ("Generar", "Cada mueble llena su <b>caja 3D, dibujada en la foto</b> como en el experimento 13: tamaño y lugar reales.")]
_pl = "".join(f'<li data-en="{i}"><em>{i}</em><div><b>{t}</b><span>{d}</span></div></li>' for i, (t, d) in enumerate(_pasos, 1))
lam("futuro-medidas", "Futuro: medidas reales", "Pasos a futuro", f'''
<div class="izq ancho">
  {kick("06", "pasos a futuro · el producto")}
  <h2 class="t chico">El producto, <em>con medidas reales</em></h2>
  <ol class="fpasos">{_pl}</ol>
  <div class="f3d" data-paso="5"><span class="et">más adelante</span><p>Con <b>modelos 3D</b> de los productos, si el negocio los tiene, en lugar de cajas: se ubica el modelo en el cuarto escaneado y el generador solo tiene que hacerlo verse real.</p></div>
</div>
<div class="esq esq-fut">{flujo(fut=True)}</div>
<div class="falta" data-paso="5"><span class="et">lo que falta</span><ul>
  <li>Las medidas reales del ambiente: el escaneo.</li><li>Las medidas de los productos: {D["asientos_sin_medida"]} de {D["asientos"]} asientos de IKEA no las tienen.</li>
  <li>Probarlo en muchos cuartos: la réplica es uno solo.</li><li>Elegir cómo se ubican las cajas (a o b).</li></ul></div>''',
    ["Cómo se vería en el producto, sobre el mismo flujo.",
     "Uno: medir el ambiente, con una app móvil que use el LiDAR del teléfono para escanear el cuarto: paredes, aberturas y "
     "medidas reales.",
     "Dos: las medidas de cada producto en la metadata del catálogo, para tener su caja 3D a escala.",
     "Tres: ubicar las cajas, de dos maneras: que la IA decida en el plano dónde va cada una, o que una primera generación ponga "
     "los muebles, y tomar dónde quedó cada uno para poner ahí su caja a escala.",
     "Cuatro: generar, con cada mueble en su caja 3D dibujada en la foto, como en la réplica.",
     "Más adelante, con modelos 3D de los productos, si el negocio los tiene, en lugar de cajas: el generador solo tiene que "
     "hacerlos verse reales. Lo que falta: las medidas, del ambiente y de los productos; probarlo en muchos cuartos; y "
     "elegir cómo se ubican las cajas."],
    50, focos=["", "foto", "catalogo descripcion indice", "escena", "imagen", ""])

# =============================================================================================
# Conclusiones y gracias
# =============================================================================================
CONC = [
    ("Lo que más importó fue el texto que se indexa,", "no el modelo."),
    ("El mejor reranker es un VLM mirando las fotos,", "y nuestro paso de elegir ya lo es."),
    ("Las métricas con ground truth subestiman:", "hace falta un juez, validado y preguntado en los dos órdenes."),
    ("El catálogo decide qué se puede recomendar,", "y evaluar con ambientes variados cambió la decisión."),
    ("La imagen necesita un control automático", "para que el cuarto sea el del cliente."),
]
lam("conclusiones", "Conclusiones", "Cierre", f'''
<div class="conc-izq">
  {kick("05", "conclusiones")}
  <ol class="conc">{"".join(f'<li data-paso="{i}"><em>{i + 1}</em><p><b>{a}</b> {b}</p></li>' for i, (a, b) in enumerate(CONC))}</ol>
</div>
<div class="conc-der">{foto("hero-final-conc", HERO / "final.png", 640, 480, q=80)}
  <div class="conc-et"><span>el rincón de lectura: {N_HERO} productos del catálogo, en el mismo cuarto</span></div></div>''',
    ["Para cerrar, cinco cosas. Lo que más importó fue el texto que se indexa, no el modelo.",
     "El mejor reranker es un VLM mirando las fotos, y nuestro paso de elegir ya lo es.",
     "Las métricas con ground truth subestiman, así que hace falta un juez, validado y preguntado en los dos órdenes.",
     "El catálogo decide qué se puede recomendar, y evaluar con ambientes variados cambió la decisión.",
     "Y la imagen necesita un control automático para que el cuarto sea el del cliente."],
    50)

lam("gracias", "Gracias", "", f'''
<div class="esq-portada">{flujo(cls="arte", etiquetas_fin={"descripcion": "descripción VLM", "indice": "Qwen3 · 1024", "busqueda": f"filtro · k = {D['k_flujo']}", "eleccion": "VLM elige", "imagen": "edición estricta", "control": f"SIFT ≥ {ROOM_CHECK['min_inliers']}"})}</div>
<div class="portada-txt">
  {kick("TP", "73.69 Large Language Models · ITBA · 2026")}
  <h1 class="marca gracias">Gracias.</h1>
  <p class="portada-preg">¿Preguntas?</p>
  <ul class="equipo"><li>Juan Bautista Albertoni Salini</li><li>Matias Juan Rossi Seifert</li><li>Junior Rambau</li></ul>
</div>''', "Gracias. ¿Preguntas?", 5, clase="portada sin-hud")

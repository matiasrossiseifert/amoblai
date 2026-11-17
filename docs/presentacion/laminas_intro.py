"""El producto y por qué es un RAG; los desafíos; los datos para medir,
las métricas y sus advertencias; y el mapa de los experimentos. (El catálogo y el flujo los cuenta el
recorrido por las fases: laminas_recorrido.py.)"""

from __future__ import annotations

from PIL import Image

from datos import (AM, B1, D, DIAG_CAT, EMB, ESTILO, F, GT_ANY,
                   GT_ROOM_PATH, J_RUIDO, RUIDO_CAMBIAN, RUIDO_PROD,
                   HERO, HERO_MET, HERO_PICKS, HERO_REQ, HIB_DIR, K, KIND_ES,
                   N_AMB, N_AMB_ANS, N_ANS, N_BUS, N_HERO, N_HERO_ABO, N_HERO_UNID, PEDIDOS, PUB_POR_ARCHIVO,
                   Q_LAMPARA, Q_MESA, V1, esc, f2, f3, miles, rankings, ROOT, jload, HERO_CHOOSE, ROOM_CHECK, JV)
from piezas import TRAMITE, consulta, etq, flujo, foto, kick, producto, ranking
from registro import lam

import statistics

# =============================================================================================
# 1 · Portada
# =============================================================================================
lam("portada", "Portada", "", f'''
<div class="esq-portada">{flujo(cls="arte")}</div>
<div class="portada-txt">
  {kick("TP", "73.69 Large Language Models · ITBA · 2026")}
  <h1 class="marca">amoblai</h1>
  <p class="portada-preg">Tengo este ambiente vacío:<br><em>¿qué compro, y cómo queda?</em></p>
  <ul class="equipo"><li>Juan Bautista Albertoni Salini</li><li>Matias Juan Rossi Seifert</li><li>Junior Rambau</li></ul>
</div>''',
    "Somos Juan Bautista, Matías y Junior. amoblai responde una pregunta concreta: tengo este ambiente vacío, ¿qué compro y "
    "cómo queda? Sacás una foto, escribís qué querés, y te devuelve una lista de productos reales de un catálogo y la imagen "
    "del mismo ambiente con esos productos.",
    25, clase="portada sin-hud")

# =============================================================================================
# 2 · El problema
# =============================================================================================
_cat_ids = ["391.505.88", "802.456.40", "302.865.67", "802.972.43", "832.351.10", "503.265.29"]
_tags = "".join(etq(i, 150, estilo=f"--r:{r}deg") for i, r in zip(_cat_ids, (-2, 1.5, -1, 2, -1.5, 1)))
lam("problema", "El problema", "El problema", f'''
{kick("01", "el problema")}
<h2 class="t">¿Qué compro para este ambiente, <em>y cómo queda?</em></h2>
<div class="pb-tres">
  <figure class="pb-p"><div class="pb-tags">{_tags}</div>
    <figcaption><b>Los catálogos</b> muestran cada mueble suelto.</figcaption></figure>
  <figure class="pb-p">{foto("gt-room-pb", GT_ROOM_PATH, 520, 390)}
    <figcaption><b>Las fotos de ambientes</b> muestran la casa de otro.</figcaption></figure>
  <figure class="pb-p tuyo">{foto("cab-living-pb", AM / "caballito-living" / "room.jpg", 520, 390)}
    <figcaption><b>Tu ambiente</b> está vacío, y tenés que decidir sin verlo puesto.</figcaption></figure>
</div>
<ol class="pb-preg" data-paso="1">
  <li><b>1</b>Qué productos reales, que se puedan comprar, van</li>
  <li><b>2</b>Cómo queda el ambiente con ellos</li>
</ol>''',
    ["Cuando te mudás a un lugar vacío tenés que decidir qué comprar sin poder verlo puesto. Los catálogos muestran cada "
     "mueble suelto, y las fotos de ambientes muestran la casa de otro.",
     "Queremos responder, para este ambiente y este pedido: qué productos reales van, y cómo queda el ambiente con ellos."],
    35)

# =============================================================================================
# 3 · El producto: una corrida de la configuración final (el loft que después sigue el recorrido)
# =============================================================================================
_filas = []
for _h, _q, _rk, _c in HERO_PICKS:
    _k = _h.get("kind", "")
    _filas.append(f'<div class="li">{producto(_h["id"], 52)}<div class="li-t"><b>{KIND_ES.get(_k, _k)}</b>'
                  f'<span>{_h["id"].removeprefix("abo-")}</span></div>'
                  f'<span class="li-q">×{_q}</span></div>')
lam("producto", "El producto", "El producto", f'''
{kick("01", "el producto")}
<h2 class="t">Una foto y un pedido. <em>Una lista de compra y una imagen.</em></h2>
<div class="pr-entra">
  <span class="et">entra</span>
  {foto("hero-room", HERO / "room.jpg", 420, 280)}
  <blockquote class="pedido">«{esc(HERO_REQ)}»</blockquote>
</div>
<div class="pr-img" data-paso="1">
  <span class="et">sale</span>
  {foto("hero-final", HERO / "final.png", 760, 507, q=82)}
  <p class="pr-pie">El mismo ambiente, con muebles del catálogo.</p>
</div>
<div class="ticket pr-ticket" data-paso="1">
  <div class="tk-cab"><b>Lista de compra</b><span>amoblai<br>{N_HERO} productos</span></div>
  {"".join(_filas)}
  <div class="tk-tot"><span>{N_HERO_ABO} de Amazon · {N_HERO - N_HERO_ABO} de IKEA</span><span>{N_HERO_UNID} unidades</span></div>
</div>''',
    ["Así se usa. La entrada es una foto del ambiente y un pedido en texto libre, como este: un loft donde piden un living de "
     "estilo industrial, con un sofá de cuero envejecido.",
     f"La salida son dos cosas: la lista de compra, con productos reales del catálogo, acá {N_HERO}, entre IKEA y Amazon, y "
     "la foto del mismo ambiente con esos productos puestos."],
    45)


# =============================================================================================
# 4 · Por qué RAG: lo que da contra un LLM solo, en los tres términos de la clase
# =============================================================================================
_RAG = [("información actualizada", "Para sumar productos, hay que reentrenarlo", "Un producto nuevo es una fila más en el índice"),
        ("información personalizada", "No conoce este catálogo", f"La búsqueda le trae {K} candidatos por pieza"),
        ("sin alucinaciones", "Puede recomendar un sillón que nadie vende", "Solo elige productos del catálogo")]
_rag_f = "".join(f'<div class="rc-f" data-paso="{i}"><span class="rag-d">{d}</span><p>{no}</p><p class="si">{si}</p></div>'
                 for i, (d, no, si) in enumerate(_RAG)).replace(' data-paso="0"', "", 1)
lam("rag", "Por qué RAG", "El producto", f'''
{kick("01", "por qué RAG")}
<h2 class="t">Recomendaciones atadas a <em>productos que existen</em></h2>
<div class="rag-cmp">
  <div class="rc-cab"><span></span><b>Un LLM solo</b><b class="si">Con RAG</b></div>
  {_rag_f}
</div>''',
    ["¿Por qué un RAG? Por tres cosas. Información actualizada: para que un LLM solo conozca "
     "productos nuevos habría que reentrenarlo; acá un producto nuevo es una fila más en el índice.",
     f"Información personalizada: el modelo no conoce estos {miles(D['prod_todos'])} productos; la búsqueda le trae, por "
     f"cada pieza, {K} candidatos reales con su foto.",
     "Y sin alucinaciones: un LLM solo puede recomendar un sillón que nadie vende; acá solo puede elegir productos que "
     "trajo la búsqueda, y la imagen se arma con sus fotos."],
    45, clase="clara")


# =============================================================================================
# Desafíos: los cuatro que más nos costaron, cada uno con cómo lo resolvimos (sin resultados: los
# números van en los experimentos)
# =============================================================================================
_DZ = [("El texto del catálogo es marketing", "describimos cada producto mirando su foto"),
       ("Catálogo", "IKEA y Amazon, revisados"),
       ("No hay ground truth de la tarea real", "un juez compara dos listas, en los dos órdenes"),
       ("El modelo de imagen rehace el cuarto", "un control: ¿es el mismo cuarto?")]
lam("desafios", "Desafíos", "Desafíos", f'''
{kick("02", "desafíos")}
<h2 class="t chico">Cuatro desafíos, <em>y cómo los resolvimos</em></h2>
<ol class="dz4">{"".join(f"<li><i>{n}</i><div><b>{a}</b><p>→ {b}</p></div></li>" for n, (a, b) in enumerate(_DZ, 1))}</ol>''',
    ["Los desafíos. Uno: el texto del catálogo es marketing, y la gente pide estilo, color y materiales; hubo que describir "
     "cada producto mirando su foto. Dos: el catálogo; algunos productos traían la foto de otro, o de otra medida. Revisamos "
     "los dos, IKEA a mano, y en Amazon el modelo que describe descarta las fotos que no muestran el producto. Tres: no hay ground "
     "truth de la tarea real; la búsqueda la medimos con fotos de IKEA anotadas, y la lista, con un juez que compara dos "
     "listas. Y cuatro: el modelo de imagen rehace el cuarto; por eso, el control."],
    40, clase="clara")

# =============================================================================================
# El banco de la búsqueda: ambientes de IKEA con sus productos anotados
# =============================================================================================
_gt_tags = "".join(producto(i, 78, "gt-p") for i in GT_ANY[:9])
lam("gt", "Cómo medimos la búsqueda", "Datos", f'''
{kick("03", "cómo evaluamos · con ground truth")}
<h2 class="t">Cómo medimos la búsqueda: <em>ambientes anotados</em></h2>
<div class="gt-izq">
  {foto("gt-room", GT_ROOM_PATH, 760, 430)}
  <span class="et">productos anotados</span>
  <div class="gt-strip">{_gt_tags}</div>
</div>
<div class="gt-der">
  <span class="et">la consulta de un mueble</span>
  {consulta(Q_MESA["query"], n=4, cls="gt-q")}
  <div data-paso="1">
    <span class="et">lo que trae la búsqueda: acierta si el anotado sale primero</span>
    {ranking(Q_MESA, 5, 140)}
  </div>
</div>
<div class="gt-cifras b-gt" data-paso="2">
  <div><b>{N_AMB}</b>ambientes de IKEA</div>
  <div><b>{N_BUS}</b>consultas</div>
  <div><b>{N_ANS}</b>con su producto en el catálogo</div>
</div>''',
    [f"Usamos dos sets de evaluación, que miden cosas distintas. Para la búsqueda, {N_AMB} ambientes de IKEA con sus productos "
     "anotados. Por cada mueble visible, un subagente escribió la consulta como la escribiría el plan, sin ver el catálogo.",
     "Una consulta acierta si el anotado sale primero, o entre los k primeros.",
     f"Son {N_BUS} consultas, {N_ANS} con su producto en el catálogo de {D['prod_819']}. Es de producto conocido: "
     "quien escribe está viendo el mueble, así que mide el índice, no la recomendación."],
    50, clase="clara")

# =============================================================================================
# Ambientes vacíos reales: el flujo entero, sin ground truth
# =============================================================================================
_tiles = []
for _p in PEDIDOS:
    _nombre, _estilo = ESTILO[_p["slug"]]
    _pub = PUB_POR_ARCHIVO.get(_p["foto"])
    _tiles.append(f'<figure class="amb{" pub" if _pub else ""}">{foto("vac-" + _p["slug"], _p["foto"], 262, 176, q=76)}'
                  f'<figcaption><b>{_nombre}</b><span>{_estilo}</span></figcaption></figure>')
lam("vacios", "Ambientes vacíos", "Datos", f'''
{kick("03", "cómo evaluamos · sin ground truth")}
<h2 class="t chico">Ambientes vacíos reales, <em>para probar de punta a punta</em></h2>
<div class="vac-izq b-vac">
  <div class="lj">
    <span class="et">sin ground truth · el juez de listas</span>
    <ol>
      <li><div class="lj-ab"><i>A</i><i>B</i></div><p>Ve la foto, el pedido y <b>dos listas</b>, sin saber de qué configuración es cada una.</p></li>
      <li><div class="lj-ab lj-n"><i>2</i><i>1</i><i>0</i></div><p>Califica cada producto y <b>elige</b>: A, B o empate.</p></li>
      <li><div class="lj-ab lj-o"><span><i>A</i><i>B</i></span><span><i>B</i><i>A</i></span></div><p>Se corre en los <b>dos órdenes</b>: gana el ambiente solo si gana en los dos.</p></li>
    </ol>
  </div>
</div>
<div class="vac-grilla">{"".join(_tiles)}</div>''',
    f"Para el flujo entero, {D['n_ambientes_vacios']} ambientes vacíos reales, cada uno con su pedido: {D['n_propios']} "
    f"nuestros y {D['n_publicos']} públicos, de estilos distintos del nórdico. Ahí no hay ground truth: compara un juez, que "
    "vemos en un caso.",
    40)

# =============================================================================================
# El juez de listas, en un caso: qué ve, cómo califica y qué elige (sin decir qué configuración es cada lista)
# =============================================================================================
_LJ = next(x for x in JV["detalle"] if x["slug"] == "publica-living-japandi")
_la, _lb = JV["a"], JV["b"]                         # en el primer orden, A es la lista de JV["a"]
assert _LJ["votos"] == [_lb, _lb], "cambió el veredicto del japandi: revisar la lámina del juez de listas"
_pa, _pb = _LJ["puntajes"][_la][0], _LJ["puntajes"][_lb][0]
_ia, _ib = _LJ["listas"][_la], _LJ["listas"][_lb]
assert len(_ia) == len(_ib) == len(_pa["grades"]) == len(_pb["grades"])


def _lj_lista(items, pts, otra):
    filas = "".join(f'<li class="{"dif" if it["id"] != o["id"] else ""}">{producto(it["id"], 56)}<span>{esc(it["type"])}</span>'
                    f'<i class="g{g}">{g}</i></li>' for it, g, o in zip(items, pts["grades"], otra, strict=True))
    utiles = sum(g == 2 for g in pts["grades"])
    return f'<ul class="lj-l">{filas}</ul><p class="lj-s">productos útiles (con 2): <b>{utiles} de {len(items)}</b></p>'


_why = _LJ["por_que"][0].split(". ")[0] + "."
_ped = next(x for x in PEDIDOS if x["slug"] == "publica-living-japandi")
lam("met-lj", "El juez de listas, en un caso", "Datos", f'''
{kick("03", "cómo evaluamos · el juez de listas, en un caso")}
<h2 class="t chico">El juez de listas, en un caso: <em>el living japandi</em></h2>
<div class="ljc-in">
  <span class="et">entra · la foto y el pedido</span>
  {foto("lj-room", ROOT / _ped["foto"], 440, 293, q=78)}
  <p>«Quiero un living japandi: un sofá bajo de tela beige, una mesa ratona redonda de madera, una alfombra de fibra natural,
    una lámpara de papel y una planta grande en maceta de cerámica…»</p>
</div>
<div class="ljc-listas" data-paso="1">
  <div><span class="et">lista A</span>{_lj_lista(_ia, _pa, _ib)}</div>
  <div><span class="et">lista B</span>{_lj_lista(_ib, _pb, _ia)}</div>
  <p class="ljc-ley"><b>2</b> sirve · <b>1</b> aceptable · <b>0</b> no sirve</p>
</div>
<div class="ljc-out">
  <div data-paso="2"><span class="et">sale</span><p class="ljc-el">elige <b>B</b></p>
    <p class="ljc-why">«{esc(_why)}»</p></div>
  <div class="ljc-rev" data-paso="3"><span class="et">y al revés</span>
    <div class="lj-ab lj-o"><span><i>B</i><i>A</i></span></div>
    <p>Elige otra vez la misma: <b>gana el ambiente</b>.</p></div>
  <p class="fj-a" data-paso="3"><kbd>A</kbd> el prompt completo</p>
</div>''',
    ["Un caso. El juez ve la foto, el pedido y dos listas, sin saber de dónde viene cada una.",
     "A cada producto le pone 2, 1 o 0; los que sacan 2 son los productos útiles.",
     "Elige B, por el sofá beige.",
     "Y al revés: si vuelve a elegir la misma, gana el ambiente; si no, empate."],
    35, clase="clara")

# =============================================================================================
# Las métricas del buscador, con el valor de hoy: cada una en una línea
# =============================================================================================
_lr = Q_LAMPARA["rank"]
_cotas = "".join(f'<div style="--k:{k}"><span>hit@{k} = {int(_lr <= k)}</span></div>' for k in (1, 3, 5))
_corr = statistics.correlation([v["mrr@10"] for v in F.values()], [v["context_precision@10"] for v in F.values()])
assert _corr > 0.99
_mdefs = [
    ("hit@k", f"¿Está entre los k primeros? El titular es hit@{K}: los {K} que ve el que elige."),
    ("MRR@10", "El promedio de 1 / posición del anotado."),
    ("Context precision y NDCG", "Con uno o dos relevantes por consulta, dan casi lo mismo que el MRR."),
    ("Diferencia pareada", "Dos métodos, las mismas consultas: si el IC no toca el 0, no es ruido."),
    ("IC 95% por bootstrap", "Se remuestrean ambientes, no consultas."),
]
_md = "".join(f'<div class="md b-md"><h4>{a}</h4><p>{d}</p></div>' for a, d in _mdefs)
lam("met-ret", "Métricas del buscador", "Métricas", f'''
{kick("04", "cómo evaluamos · el buscador")}
<h2 class="t">El buscador: <em>¿trae el producto anotado, y arriba?</em></h2>
<div class="met-ej">
  <span class="et">una consulta real: sus 10 primeros candidatos</span>
  <div class="met-cotas">{_cotas}</div>
  {ranking(Q_LAMPARA, 10, 150)}
  <p class="met-rr">el anotado está en el puesto {_lr}: suma <b>1/{_lr}</b> al MRR</p>
</div>
<div class="met-defs b-defs" data-paso="1">{_md}</div>''',
    [f"Las métricas del buscador. Arriba, una consulta real: el anotado sale en el puesto {_lr}, así que hit@1 da cero y "
     f"hit@{3 if _lr <= 3 else 5} da uno.",
     "El titular es hit@5, porque son los cinco candidatos que ve el que elige. Para comparar dos "
     "métodos usamos la diferencia pareada: las mismas consultas, la diferencia media y su intervalo de 95 por ciento, por "
     "bootstrap de ambientes. Si no toca el cero, no es ruido. Mirar el intervalo de cada método por separado nos había hecho "
     "leer mejoras que eran ruido. Context precision y NDCG, con uno o dos relevantes por consulta, repiten al MRR."],
    50, clase="clara")

# =============================================================================================
# El generador (faithfulness y answer relevance) y los jueces
# =============================================================================================
lam("met-juez", "El generador", "Métricas", f'''
{kick("04", "cómo evaluamos · el generador")}
<h2 class="t chico">El generador: <em>¿es cierto lo que dice?</em> ¿<em>contesta el pedido?</em></h2>
<div class="b-gen">
  <div class="b-m"><b class="fx">sostenidas ÷ afirmaciones</b><h4>Faithfulness del porqué</h4>
    <p>Un juez parte el porqué en afirmaciones de hecho y marca cuáles se infieren de lo que vio el generador.</p></div>
  <div class="b-m"><b class="fx">coseno(pedido del juez, pedido real)</b><h4>Answer relevance</h4>
    <p>Un juez lee la lista, sin ver el pedido, y escribe el pedido que contesta.</p>
    <span class="et">la vara: el mismo coseno, con pedidos de otras listas</span></div>
</div>
''',
    ["El generador es Opus eligiendo, con un porqué por producto. Faithfulness: un juez parte el porqué en afirmaciones y "
     "marca cuáles se infieren de lo que vio. Answer relevance: un juez que no ve el pedido escribe el que la lista contesta, "
     "y medimos el coseno con el original; la vara, con pedidos de otras listas."],
    40)

# =============================================================================================
# Faithfulness, en un caso: qué le entra al juez, qué hace y qué sale (el loft de la configuración final)
# =============================================================================================
_FJ = jload(ROOT / "datos" / "evaluacion_flujo" / "juez" / "v2" / "hibrida__publica-loft-industrial" / "fidelidad.json")
_cl = {c["claim"]: c for c in _FJ["claims"]}
_n_ok = sum(c["supported"] for c in _FJ["claims"])
_MUESTRA = [("Sofa is leather", "lo dicen la línea y la foto"),
            ("Coffee table has a wood top", "se ve en la foto"),
            ("Coffee table top is solid wood", "la línea no lo dice"),
            ("Person asked for a dark pot", "el pedido no habla de una maceta"),
            ("Textiles introduce no bright white", "la alfombra tiene flecos blancos")]
assert all(c in _cl for c, _ in _MUESTRA), "cambió la salida del juez del loft: revisar la lámina de faithfulness"
assert sum(not _cl[c]["supported"] for c, _ in _MUESTRA) == len(_FJ["claims"]) - _n_ok, "no se muestran todas las no sostenidas"
_resto = len(_FJ["claims"]) - len(_MUESTRA)
_ch = {c["id"]: c["why"] for c in HERO_CHOOSE["answer"]["choices"]}
_mesa, _maceta = (next(i for i in _ch if _ch[i].startswith(s)) for s in ("Its solid wood top", "A dark matte pot"))
_porque = [(_ch[_mesa], "solid wood top"), (_ch[_maceta], "as requested"),
           (HERO_CHOOSE["answer"]["why"].split(". ")[-1], "without introducing bright white")]
assert all(m in s for s, m in _porque)
_pq = "".join(f'<li>«{esc(s).replace(esc(m), f"<mark>{esc(m)}</mark>")}»</li>' for s, m in _porque)
_sale = "".join(f'<li class="{"ok" if _cl[c]["supported"] else "no"}"><i>{"✓" if _cl[c]["supported"] else "✗"}</i>'
                f'<div><code>{esc(c)}</code><span>{e}</span></div></li>' for c, e in _MUESTRA)
_fotos_j = foto("fj-room", HERO / "room.jpg", 150, 100, q=78) + "".join(producto(h["id"], 52) for h, *_ in HERO_PICKS)
lam("met-fid", "Faithfulness, en un caso", "Métricas", f'''
{kick("04", "cómo evaluamos · faithfulness, en un caso")}
<h2 class="t chico">Faithfulness, en un caso: <em>el loft</em></h2>
<div class="fj-col fj-in">
  <span class="et">entra · lo mismo que vio Opus al elegir</span>
  <div class="fj-fotos">{_fotos_j}</div>
  <p class="fj-l">y la línea de cada producto: <code>coffee table, industrial rectangular coffee table, 135 cm wide…</code></p>
  <span class="et">el pedido</span>
  <p class="fj-ped">«…una mesa ratona de madera maciza con patas de metal negro… Nada de blanco brillante…»</p>
  <span class="et">el porqué de Opus · 3 de sus 8 líneas</span>
  <ul class="fj-pq">{_pq}</ul>
</div>
<div class="fj-fl fj-f1">→</div>
<div class="fj-col fj-juez" data-paso="1">
  <span class="et">el juez · {esc(_FJ["_juez"]).replace("claude-opus-5-5", "Opus 5.5")}</span>
  <ol><li>Parte el porqué en <b>afirmaciones de hecho</b>; las opiniones no cuentan.</li>
      <li>¿Cada una <b>se infiere</b> del pedido, las fotos o las líneas?</li>
      <li>Responde en JSON.</li></ol>
  <p class="fj-a"><kbd>A</kbd> el prompt completo</p>
</div>
<div class="fj-fl fj-f2" data-paso="2">→</div>
<div class="fj-col fj-out" data-paso="2">
  <span class="et">sale · {len(_FJ["claims"])} afirmaciones</span>
  <ul class="fj-cl">{_sale}<li class="ok resto"><i>✓</i><div><span>y {_resto} más, todas sostenidas</span></div></li></ul>
  <p class="fj-res">faithfulness = {_n_ok} / {len(_FJ["claims"])} = <b>{f2(_n_ok / len(_FJ["claims"]))}</b></p>
</div>''',
    ["El loft. Al juez le entra lo que vio Opus: las fotos, la línea de cada producto, el pedido y el porqué.",
     "Lo parte en afirmaciones y marca cada una.",
     f"Sostiene {_n_ok} de {len(_FJ['claims'])}. Fallan «madera maciza», que la línea no dice; «como pediste», con una maceta "
     "que nadie pidió; y «nada de blanco», con flecos blancos."],
    35, clase="clara")

# =============================================================================================
# La imagen: las 11 corridas de la configuración final
# =============================================================================================
_fin = Image.open(HERO / "final.png").convert("RGB")
_pares = []
for (_h, *_), _p in zip(HERO_PICKS, HERO_MET["productos"], strict=True):
    assert _h["id"] == _p["id"]
    if _p["detectado"]:
        _pares.append(f'<div class="id-par{" ok" if _p["puesto"] == 1 else ""}">{producto(_p["id"], 66)}<span class="id-fl">↔</span>'
                      f'{foto("crop-" + _p["id"], _fin.crop(_p["box"]), 66, 66, modo="fit", q=82)}'
                      f'<span class="id-p"><b>{_p["puesto"]}.º</b> de {_p["entre"]}</span></div>')
_rc = jload(HERO / "5_image.json")["room_check"]
assert _rc["ok"]
lam("met-img", "La imagen", "Métricas", f'''
{kick("04", "cómo evaluamos · la imagen")}
<h2 class="t chico">La imagen: <em>¿son esos productos?</em> ¿<em>es ese cuarto?</em></h2>
<div class="img-dos b-img">
  <div class="it"><h4>¿Son esos productos? En el loft</h4>
    <div class="id-lista"><div class="id-cab"><span>en la lista</span><span>en la imagen</span><span>entre los de su tipo, sale</span></div>{"".join(_pares)}</div>
    <p><b>Reconocido</b>: el recorte se parece más a su producto que a cualquier otro de su tipo.</p></div>
  <div class="it" data-paso="1"><h4>¿Es ese cuarto? El control, en el loft</h4>
    <div class="rc-par"><figure>{foto("rc-antes", HERO / "room.jpg", 520, 347, q=78)}<figcaption>la foto</figcaption></figure>
      <figure>{foto("rc-despues", HERO / "final.png", 520, 347, q=78)}<figcaption>la imagen</figcaption></figure></div>
    <p>SIFT busca en la imagen los puntos de la foto. Pasa con <b>{int(ROOM_CHECK["min_inliers"])} o más</b> y la cámara quieta; si no,
      se genera otra, hasta {int(ROOM_CHECK["attempts"])} veces. En el loft: {_rc["sift_inliers"]} puntos.</p></div>
</div>''',
    ["La imagen, con dos preguntas. ¿Son esos productos? Recortamos cada mueble y, con DINOv3, lo comparamos con los de su "
     "tipo: reconocido, si el más parecido es el de la lista. En el loft, la alfombra no.",
     "¿Es ese cuarto? SIFT busca en la imagen los puntos de la foto; si encuentra pocos, se genera otra."],
    40, clase="clara")

# =============================================================================================
# Advertencias: cuánto confiar en los números
# =============================================================================================
_cos_banco = statistics.median(r["scores"][0] for r in rankings(HIB_DIR)[V1] if r["relevant"] and r["scores"])
_cos_flujo = sorted(DIAG_CAT[v]["puntaje_del_primero"]["mediana"] for v in ("ikea", "todos"))
_bm = EMB["bm25|description|filtro-kind"]
TRAMPAS = [
    ("El set de evaluación de la búsqueda es de producto conocido", "Quien escribe la consulta ve el mueble; en el flujo, el plan lo imagina."),
    ("El mismo modelo escribe los dos lados",
     f"Por eso contar palabras rinde casi como el embedder: {f3(_bm['hit@1'])} contra {f3(B1['hit@1'])}."),
    ("No hay conjunto apartado", f"Todo se eligió sobre los mismos {N_AMB_ANS} ambientes: 2 puntos no son señal."),
    (f"De punta a punta son {D['n_ambientes_vacios']} ambientes",
     f"El juez es el mismo modelo que elige: la misma versión, corrida dos veces, sale {J_RUIDO['a']} a {J_RUIDO['b']}."),
]
_tr = "".join(f'<div class="b-trf" data-paso="{i}"><i>{i + 1}</i><b>{a}</b><p>{b}</p></div>' for i, (a, b) in enumerate(TRAMPAS))
lam("trampas", "Advertencias", "Métricas", f'''
{kick("04", "cómo evaluamos · cuánto confiar")}
<h2 class="t">Advertencias</h2>
<div class="b-tr">{_tr}</div>''',
    ["Cuatro advertencias, y por qué medimos igual. Uno: el set de la búsqueda es de producto conocido. Quien escribe la "
     "consulta ve el mueble; en el flujo, el plan lo imagina, y el coseno del primer candidato baja de "
     f"{f3(_cos_banco)} a {f2(_cos_flujo[0])}–{f2(_cos_flujo[1])}: esos números son optimistas. Lo usamos porque es la única "
     "forma de tener respuesta correcta para cientos de consultas, y todas las variantes reciben las mismas: sirve para comparar.",
     "Dos: el mismo modelo escribe las descripciones y las consultas, con el mismo molde; por eso contar palabras rinde casi "
     "como el embedder. Pero así funciona el sistema: el plan también escribe una ficha.",
     f"Tres: no hay conjunto apartado; todo se eligió sobre los mismos {N_AMB_ANS} ambientes. Partirlos dejaba muy pocos. En "
     "cambio, comparamos siempre de a pares, con su intervalo, y medimos el ruido con tres redactores: dos puntos no son señal.",
     f"Y cuatro: de punta a punta son {D['n_ambientes_vacios']} ambientes, y el juez es el mismo modelo que elige. La misma "
     f"configuración, corrida dos veces, cambió {RUIDO_CAMBIAN} de {RUIDO_PROD} productos, y el juez repartió los ambientes "
     f"{J_RUIDO['a']} a {J_RUIDO['b']}. Por eso el juez corre en los dos órdenes y solo leemos resultados desparejos, como un "
     "cinco a cero. Más ambientes, y validar al juez con personas, quedan para el trabajo futuro."],
    40)

# =============================================================================================
# Configuración inicial, fase por fase, y qué experimento la pone a prueba
# =============================================================================================
_PARTIDA = [("Qué se indexa", "el texto del vendedor", (1,)),
            ("La consulta", "el pedido, sin reescribir", (2,)),
            ("El índice", "Qwen3 · 1024 dimensiones · un documento por producto · ChromaDB", (9, 10, 11, 12)),
            ("Filtros", "ninguno", (13,)),
            ("La búsqueda", "solo densa: el coseno", (3,)),
            ("Reordenar", "no se reordena", (5, 14)),
            ("La elección", "Opus elige entre los 3 primeros, mirando las fotos", (5, 6)),
            ("La escena", "la escribe el LLM", (15,))]
_pt = "".join(f'<li><b>{a}</b><span>{b}</span><div>{"".join(f"<em class=tp>{n}</em>" for n in ns)}</div></li>'
              for a, b, ns in _PARTIDA)
lam("partida", "Configuración inicial", "Experimentos", f'''
{kick("E", "experimentos · un RAG naive")}
<h2 class="t">Configuración inicial</h2>
<ul class="pt-l"><li class="pt-cab"><b>fase</b><span>arrancamos con</span><div>lo prueba</div></li>{_pt}</ul>
<div class="pt-pie"><p><b>Lo que gana, se suma</b>: el camino incremental, después del experimento 3.</p>
<p><b>Cada experimento cambia una sola cosa</b>; la lámina dice sobre qué configuración.</p></div>''',
    ["Arrancamos de un RAG naive; al lado de cada fase, el experimento que la pone a prueba. Lo que gana se suma, y cada "
     "experimento cambia una sola cosa."],
    30, clase="clara")

# =============================================================================================
# El mapa de los experimentos: un pin por pregunta, sobre la fase a la que se la hicimos
# =============================================================================================
EXPS = [
    (1, "Qué se indexa", "texto del vendedor · descripción desde la foto"),
    (2, "Cómo se escribe la consulta", "la ficha · la frase natural · Type · kind"),
    (3, "Léxica, por foto e híbrida", "Qwen3 · BM25 · SigLIP 2 · fusionadas"),
    (4, "¿Error, o una variante?", "exacto · el mismo modelo · sirve (juez)"),
    (5, "Elegir con un VLM, y cuántos", "top-10 mirando las fotos · k de 1 a 10"),
    (6, "Con búsqueda o sin búsqueda", f"los {K} mejores · {K} al azar · el catálogo entero (juez)"),
    (7, "Tres redactores", "las mismas consultas, escritas tres veces"),
    (8, "Buscar por imagen", "el recorte de cada mueble · la descripción"),
    (9, "Embedder", "hashing · BM25 · BGE · Qwen3"),
    (10, "Dimensión del vector", "de 32 a 1024 (Matryoshka)"),
    (11, "Splitting y líneas", "documento · por línea · qué líneas pesan"),
    (12, "Base vectorial", "ChromaDB (HNSW) · búsqueda exacta"),
    (13, "Filtros de metadata", "ninguno · por tipo · por kind"),
    (14, "Rerankers de texto", "MiniLM · Qwen3-Reranker"),
    (15, "La escena", "plantilla · escrita por el LLM"),
]
assert {n for n, *_ in EXPS if n > 8} == TRAMITE
_h = "".join(f'<li class="{"tram" if n in TRAMITE else ""}"><em>{n}</em><b>{q}</b><span>{o}</span></li>' for n, q, o in EXPS)
lam("hiper", "El mapa de los experimentos", "Experimentos", f'''
{kick("E", "experimentos · el mapa")}
<h2 class="t">Experimentos</h2>
<ol class="hiper h14">{_h}</ol>
<div class="esq esq-hiper">{flujo(pines=range(1, 16), banco=f"{N_AMB} ambientes de IKEA anotados · {N_ANS} consultas con respuesta")}</div>''',
    "Ahora los experimentos, por cuánto importan. El mismo mapa: cada pin es una pregunta que le "
    "hicimos a una parte del sistema. Del 1 al 8, los que más pesan; el 4 y el 7 miden al set de evaluación. Del 9 al "
    "15, los de trámite, una lámina rápida cada uno. "
    "Y dos cosas no las decidió ningún experimento: el modelo de imagen y "
    "los umbrales del control.",
    35)

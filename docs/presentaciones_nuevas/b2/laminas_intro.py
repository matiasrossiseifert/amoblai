"""El producto y por qué es un RAG; los desafíos (el cambio de arquitectura); los datos para medir,
las métricas y sus trampas; y el mapa de los experimentos. (El catálogo y el flujo los cuenta el
recorrido por las fases: laminas_recorrido.py.)"""

from __future__ import annotations

from PIL import Image

from datos import (AM, B1, B2, D, D21, DIAG_CAT, DOC, EMB, ESTILO, F, FINALES, FOTO, G_ANOT2, G_OTROS2, GEN_BAJA, GEN_SUBE, GT_ANY,
                   GT_ROOM_PATH, J_RUIDO, RESP2, ROOM_CHECK, RUIDO_CAMBIAN, RUIDO_PROD,
                   HERO, HERO_MET, HERO_PICKS, HERO_REQ, HERO_SLUG, HIB_DIR, IMG_TOT, J_AZAR, J_CAT, J_VER, K, KIND_ES,
                   N_AMB, N_AMB_ANS, N_ANS, N_BUS, N_HERO, N_HERO_ABO, N_HERO_UNID, NO_PASAN, PEDIDOS, PUB_POR_ARCHIVO,
                   Q_LAMPARA, Q_MESA, RESP, ROOT, SOFA, V0_REC, V0_SOFA_OK, V1, VT, credito, dif, esc, f2, f3, ic_txt,
                   medida, miles, nb, pct, rankings, sg)
from piezas import TRAMITE, barras, consulta, etq, flujo, foto, kick, producto, ranking
from recorrido import prompt_tk
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
    <figcaption><b>Los catálogos</b> muestran cada mueble suelto, sobre fondo blanco.</figcaption></figure>
  <figure class="pb-p">{foto("gt-room-pb", GT_ROOM_PATH, 520, 390)}
    <figcaption><b>Las fotos de ambientes</b> muestran la casa de otro.</figcaption></figure>
  <figure class="pb-p tuyo">{foto("cab-living-pb", AM / "caballito-living" / "room.jpg", 520, 390)}
    <figcaption><b>Tu ambiente</b> está vacío, y tenés que decidir sin verlo puesto.</figcaption></figure>
</div>
<ol class="pb-preg" data-paso="1">
  <li><b>1</b>Qué productos reales, que se puedan comprar, van</li>
  <li><b>2</b>Cuántos, y de qué medida</li>
  <li><b>3</b>Cómo queda el ambiente con ellos</li>
</ol>''',
    ["Cuando te mudás a un lugar vacío tenés que decidir qué comprar sin poder verlo puesto. Los catálogos muestran cada "
     "mueble suelto, sobre fondo blanco, y las fotos de ambientes muestran la casa de otro.",
     "Queremos responder, para este ambiente y este pedido: qué productos reales van, cuántos, y cómo queda el ambiente con "
     "ellos."],
    35)

# =============================================================================================
# 3 · El producto: una corrida de la configuración final (el loft que después sigue el recorrido)
# =============================================================================================
_filas = []
for _h, _q, _rk, _c in HERO_PICKS:
    _k = _h.get("kind", "")
    _md = medida(_h.get("dimensions_cm"))
    _cat = "Amazon" if _h["id"].startswith("abo-") else "IKEA"
    _filas.append(f'<div class="li">{producto(_h["id"], 52)}<div class="li-t"><b>{KIND_ES.get(_k, _k)}</b>'
                  f'<span>{_cat} · {_h["id"].removeprefix("abo-")}{" · " + _md if _md else ""}</span></div>'
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
  <p class="pr-pie">El mismo ambiente, con esos productos puestos.</p>
  <p class="cred-l">Foto del ambiente: {credito(HERO_SLUG)}</p>
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
# 4 · Por qué RAG: los tres desafíos de la clase
# =============================================================================================
def _tk(cab, sub, lineas, pie=""):
    ls = "".join(f'<div class="tk-l"><span class="tk-q">{i}</span><span class="tk-n">{a}</span><span class="tk-dots"></span>'
                 f'<span class="tk-v">{b}</span></div>' for i, (a, b) in enumerate(lineas, 1))
    return f'<div class="ticket rag-tk"><div class="tk-cab"><b>{cab}</b><span>{sub}</span></div>{ls}{pie}</div>'


lam("rag", "Por qué RAG", "El producto", f'''
{kick("01", "por qué RAG · los tres desafíos de la clase")}
<h2 class="t">Recomendaciones atadas a <em>productos que existen</em></h2>
<div class="rag-tres tres">
  <div class="rag-c">
    <span class="rag-d">información actualizada</span>
    <h3>El catálogo cambia; el modelo no se reentrena</h3><p>Un producto nuevo es una fila más en el índice.</p>
    {_tk("Alta de un producto", "indexing", [("Describirlo desde su foto", "VLM"), ("Embeberlo", "Qwen3"),
                                             ("Insertarlo en el índice", "ChromaDB")], '<div class="sello-tk ok">sin reentrenar</div>')}
  </div>
  <div class="rag-c" data-paso="1">
    <span class="rag-d">información personalizada</span>
    <h3>Este catálogo, este ambiente, este pedido</h3><p>El LLM no conoce estos {miles(D["prod_todos"])} productos: la búsqueda se los trae.</p>
    {_tk("Lo que ve el que elige", "contexto", [("La foto del ambiente", "1"), ("El pedido, en texto libre", "1"),
                                                 ("Candidatos reales por pieza", f"{K}, con foto")])}
  </div>
  <div class="rag-c elegida" data-paso="2">
    <span class="rag-d">sin alucinaciones</span>
    <h3>Solo productos que existen</h3><p>Un LLM solo recomienda un sillón que nadie vende; un modelo de imagen solo inventa los muebles.</p>
    <div class="ticket rag-tk"><div class="tk-cab"><b>Recomendación</b><span>LLM solo</span></div>
      <div class="tk-l"><span class="tk-q">1</span><span class="tk-n">Sillón de cuero coñac</span><span class="tk-dots"></span><span class="tk-v">art. ———</span></div>
      <div class="sello-tk">nadie lo vende</div>
      <div class="tk-tot"><span>amoblai · art. {SOFA.removeprefix("abo-")}</span><span>id del catálogo</span></div></div>
  </div>
</div>
<p class="remate" data-paso="2">No es un Q&amp;A: la consulta es una foto y un pedido abierto, y hay <mark>dos generaciones aumentadas</mark>: la lista y la imagen.</p>''',
    ["¿Por qué un RAG? Por los tres desafíos de la clase. Información actualizada: el catálogo cambia y el modelo no se "
     "reentrena; un producto nuevo es una fila más en el índice.",
     f"Información personalizada: el LLM no conoce estos {miles(D['prod_todos'])} productos; la búsqueda le trae cinco "
     "candidatos reales por pieza, y elige mirando sus fotos y la del cuarto.",
     "Y sin alucinaciones: un LLM solo recomienda un sillón que nadie vende, y un modelo de imagen solo inventa los muebles; "
     "acá la lista solo puede tener productos que trajo la búsqueda, y la imagen se genera desde sus fotos. No es un Q&A: "
     "hay dos generaciones aumentadas, la lista y la imagen."],
    45, clase="clara")


# =============================================================================================
# Desafíos: de la propuesta aprobada (buscar por imagen) a RAG por texto, y otros tres
# =============================================================================================
def _fila_flujo(nombre, sub, chips, cls):
    cs = "<i>→</i>".join(f'<div class="dz-c"><b>{t}</b>{f"<span>{s}</span>" if s else ""}</div>' for t, s in chips)
    return f'<div class="dz-fila {cls}"><div class="dz-n"><b>{nombre}</b><span>{sub}</span></div>{cs}</div>'


_room_im = Image.open(ROOT / GT_ROOM_PATH)
_bx = [round(v) for v in V0_REC["box"]]
_crop = _room_im.crop(_bx)
_sx = 208 / _room_im.width
_box_css = (f"left:{_bx[0] * _sx:.0f}px;top:{_bx[1] * _sx:.0f}px;width:{(_bx[2] - _bx[0]) * _sx:.0f}px;"
            f"height:{(_bx[3] - _bx[1]) * _sx:.0f}px")
lam("desafios", "Desafíos", "Desafíos", f'''
{kick("02", "desafíos · el cambio de arquitectura")}
<h2 class="t chico">De buscar por imagen a <em>RAG por texto</em>, y otros tres desafíos</h2>
<div class="dz-flujos">
  {_fila_flujo("La propuesta aprobada", "buscar por imagen", [("Foto + pedido", ""), ("Generar una imagen", "con muebles inventados"),
               ("Recortar cada mueble", "Grounding DINO + SAM"), ("Buscar el más parecido", "por imagen (DINOv3)"),
               ("Lista de compra", "lo que más se parezca")], "vieja")}
  {_fila_flujo("Lo que quedó", "RAG por texto", [("Foto + pedido", ""), ("Plan", "una ficha por pieza"),
               ("Búsqueda", "en el catálogo descripto"), ("Elección: la lista", "productos reales"), ("Imagen", "al final, con ellos")], "nueva")}
</div>
<div class="dz-abajo">
  <div data-paso="1">
    <span class="et">lo que construimos y medimos antes de cambiar: su buscador</span>
    <div class="dz-v0">
      <div class="v-foto">{foto("v0-room", GT_ROOM_PATH, 208, round(_room_im.height * _sx))}<div class="v-caja" style="{_box_css}"></div></div>
      <span class="v-fl">→</span>{foto("v0-crop", _crop, 150, 74, modo="fit", q=82)}<span class="v-fl">→</span>{producto(V0_SOFA_OK, 84)}
      <p>Detectar cada mueble, recortarlo y buscar la foto del catálogo más parecida.</p>
    </div>
    {barras([dict(et="Por imagen", v=VT["imagen"]),
             dict(et="Por texto", v=VT["texto"], gana=True, nota=f'{sg(VT["dif"], 2)} {ic_txt(*VT["ic"], nd=2)}')],
            titulo=f"encontrar primero el producto anotado · mismo ground truth, {VT['n']} productos",
            paso=1, gana_paso=1, cls="dz-barras")}
  </div>
  <div data-paso="2">
    <span class="et">otros tres</span>
    <ol class="dz-otros">
      <li><b>El catálogo traía fotos equivocadas</b><span>{D["rev_afuera"]} productos de IKEA con la foto de otro producto o de otra medida, o que no eran de living: la lista diría una cosa y la imagen otra. Se revisó mirando cada foto.</span></li>
      <li><b>No hay ground truth de la tarea real</b><span>Nadie anotó la lista ideal para un ambiente vacío. Hay uno para la búsqueda y, para el flujo entero, un juez que compara listas.</span></li>
      <li><b>El modelo de imagen rehace el cuarto</b><span>Mueve la cámara, inventa una ventana. Edición estricta y un control automático; aun así, {NO_PASAN} de {len(FINALES)} no se conservan.</span></li>
    </ol>
  </div>
</div>
<p class="remate chico" data-paso="1">La versión por imagen <mark>nunca corrió de punta a punta</mark>: comparamos buscadores, no sistemas.</p>''',
    ["Los desafíos. El más grande fue cambiar la arquitectura que nos aprobaron. La propuesta era generar primero una imagen "
     "amoblada, recortar cada mueble y buscar en el catálogo el más parecido, por imagen.",
     f"Construimos y medimos su buscador sobre el mismo ground truth: encontraba primero el {round(100 * VT['imagen'])} por "
     f"ciento de los productos anotados, contra {round(100 * VT['texto'])} buscando por texto. Con eso, y con una generación de "
     "imagen menos por pedido, cambiamos a RAG por texto. Ojo: esa versión nunca corrió de punta a punta; comparamos "
     "buscadores, no sistemas.",
     "Los otros tres: el catálogo traía fotos de otro producto y hubo que revisarlo a mano; no hay ground truth de la tarea "
     "real; y el modelo de imagen rehace el cuarto."],
    55, clase="clara")

# =============================================================================================
# El banco de la búsqueda: ambientes de IKEA con sus productos anotados
# =============================================================================================
_gt_tags = "".join(producto(i, 78, "gt-p") for i in GT_ANY[:9])
lam("gt", "El banco de la búsqueda", "Datos", f'''
{kick("03", "cómo evaluamos · con ground truth")}
<h2 class="t">El banco de la búsqueda: <em>ambientes anotados</em></h2>
<div class="gt-izq">
  {foto("gt-room", GT_ROOM_PATH, 760, 430)}
  <span class="et">productos anotados en esta foto</span>
  <div class="gt-strip">{_gt_tags}</div>
</div>
<div class="gt-der">
  <span class="et">por cada mueble visible, un subagente escribe la consulta como la escribiría el plan, sin ver el catálogo</span>
  {consulta(Q_MESA["query"], cls="gt-q")}
  <div data-paso="1">
    <span class="et">lo que trae la búsqueda del flujo: acierta si el anotado sale primero (hit@1) o entre los k primeros (hit@k)</span>
    {ranking(Q_MESA, 5, 112)}
  </div>
</div>
<div class="gt-cifras" data-paso="2">
  <div><b>{N_AMB}</b>livings y comedores de IKEA, con sus productos anotados</div>
  <div><b>{N_BUS}</b>consultas, una por mueble visible</div>
  <div><b>{N_ANS}</b>con su producto en el catálogo de {D["prod_819"]}</div>
  <div class="gt-ic">Es un banco de <b>producto conocido</b>: quien escribe la consulta ve el mueble. Mide el índice, no la recomendación.</div>
</div>''',
    [f"Usamos dos bancos de prueba, que miden cosas distintas. Para la búsqueda, {N_AMB} ambientes de IKEA con sus productos "
     "anotados. Por cada mueble visible, un subagente escribió la consulta como la escribiría el plan, sin ver el catálogo.",
     "Una consulta acierta si el anotado sale primero, o entre los k primeros.",
     f"Son {N_BUS} consultas, {N_ANS} con su producto en el catálogo. Es un banco de producto conocido: quien escribe está "
     "viendo el mueble, así que mide el índice, no la recomendación."],
    50, clase="clara")

# =============================================================================================
# Ambientes vacíos reales: el flujo entero, sin ground truth
# =============================================================================================
_tiles = []
for _p in PEDIDOS:
    _nombre, _estilo = ESTILO[_p["slug"]]
    _pub = PUB_POR_ARCHIVO.get(_p["foto"])
    _cred = f'<span class="cred">{esc(_pub["autor"])} · {esc(_pub["licencia"])}</span>' if _pub else ""
    _tiles.append(f'<figure class="amb{" pub" if _pub else ""}">{foto("vac-" + _p["slug"], _p["foto"], 262, 176, q=76)}'
                  f'<figcaption><b>{_nombre}</b><span>{_estilo}</span>{_cred}</figcaption></figure>')
lam("vacios", "Ambientes vacíos", "Datos", f'''
{kick("03", "cómo evaluamos · sin ground truth")}
<h2 class="t chico">Ambientes vacíos reales, <em>para probar de punta a punta</em></h2>
<div class="vac-izq">
  <div class="cifra"><span>{D["n_ambientes_vacios"]}</span></div>
  <p class="cifra-pie">ambientes vacíos reales, cada uno con un pedido escrito como lo escribiría un usuario que sabe pedir</p>
  <ul class="vac-datos">
    <li><b>{D["n_propios"]}</b> de departamentos nuestros</li>
    <li><b>{D["n_publicos"]}</b> públicos, de Wikimedia Commons y Flickr (Creative Commons), con estilos distintos del nórdico</li>
    <li>elegidos entre <b>{D["n_publicas_revisadas"]}</b> que revisamos uno por uno para descartar renders y fotos generadas con IA</li>
  </ul>
  <p class="vac-nota">Acá no hay ground truth: un juez compara a ciegas las listas de dos configuraciones, <b>en los dos órdenes</b>. La imagen se mide aparte.</p>
</div>
<div class="vac-grilla">{"".join(_tiles)}</div>''',
    f"Para el flujo entero, {D['n_ambientes_vacios']} ambientes vacíos reales, cada uno con su pedido: {D['n_propios']} de "
    f"departamentos nuestros y {D['n_publicos']} públicos, con licencia Creative Commons y estilos distintos del nórdico. Ahí "
    "no hay ground truth: un juez compara a ciegas las listas de dos configuraciones, en los dos órdenes, y una gana un "
    "ambiente solo si gana en los dos. La imagen se mide aparte.",
    40)

# =============================================================================================
# Las métricas del buscador, con el valor de hoy
# =============================================================================================
_lr = Q_LAMPARA["rank"]
_cotas = "".join(f'<div style="--k:{k}"><span>hit@{k} = {int(_lr <= k)}</span></div>' for k in (1, 3, 5))
_corr = statistics.correlation([v["mrr@10"] for v in F.values()], [v["context_precision@10"] for v in F.values()])
assert _corr > 0.99
_mdefs = [
    ("hit@k", f"¿El anotado está entre los k primeros? <b>hit@5 es el titular</b>: son los {K} candidatos que ve el que elige. "
              f"Hoy: hit@1 {f3(B2['hit@1'])} y hit@5 <b>{f3(B2['hit@5'])}</b>."),
    ("Diferencia pareada", f"Dos métodos sobre <b>las mismas consultas</b>: la diferencia media y su IC 95%. Si no toca el cero, "
                           f"no es ruido. Versión 2 menos versión 1: {nb(dif(D21))}."),
    ("IC 95% por bootstrap", "Se remuestrean <b>ambientes</b>, no consultas: las consultas de un mismo ambiente no son "
                             f"independientes. hit@1 {f3(B2['hit@1'])} {ic_txt(*B2['hit@1_ic95'], nd=2)}."),
    ("MRR@10", f"El promedio de 1 / posición del anotado: premia que esté arriba. Hoy {f3(B2['mrr@10'])}."),
    ("Las de la clase", f"Context precision@10 ({f2(B2['context_precision@10'])}) y NDCG@10 ({f2(B2['ndcg@10'])}) repiten al MRR, "
                        f"con uno o dos relevantes por consulta. Context recall es por ambiente: {f2(B2['context_recall@3'])} con k = 3."),
]
_md = "".join(f'<div class="md"><h4>{a}</h4><p>{b}</p></div>' for a, b in _mdefs)
lam("met-ret", "Métricas del buscador", "Métricas", f'''
{kick("04", "cómo evaluamos · el buscador")}
<h2 class="t">El buscador: <em>¿trae el producto anotado, y arriba?</em></h2>
<div class="met-ej">
  <span class="et">una consulta real del banco (una lámpara de pie): sus 10 primeros candidatos con la búsqueda del flujo</span>
  <div class="met-cotas">{_cotas}</div>
  {ranking(Q_LAMPARA, 10, 150)}
  <p class="met-rr">el anotado está en el puesto {_lr}: suma <b>1/{_lr}</b> al MRR</p>
</div>
<div class="met-defs" data-paso="1">{_md}</div>''',
    [f"Las métricas del buscador. Arriba, una consulta real: el anotado sale en el puesto {_lr}, así que hit@1 da cero y "
     f"hit@{3 if _lr <= 3 else 5} da uno.",
     f"El titular es hit@5, porque son los cinco candidatos que ve el que elige: hoy, {f3(B2['hit@5'])}. Para comparar dos "
     "métodos usamos la diferencia pareada: las mismas consultas, la diferencia media y su intervalo de 95 por ciento, por "
     "bootstrap de ambientes. Si no toca el cero, no es ruido. Mirar el intervalo de cada método por separado nos había hecho "
     "leer mejoras que eran ruido. Las de la clase, context precision y NDCG, acá repiten al MRR; context recall es por "
     "ambiente."],
    50, clase="clara")

# =============================================================================================
# El generador (faithfulness y answer relevance) y los jueces
# =============================================================================================
_F, _AR = RESP2["faithfulness"], RESP2["answer_relevance"]     # sobre las 11 listas de la versión 2 (el flujo de hoy)
_F1, _AR1 = RESP["faithfulness"], RESP["answer_relevance"]     # sobre otras 11 listas (la búsqueda de la versión 1): la réplica
_MADERAS = ("ash", "birch", "beech", "oak", "pine", "walnut")
_no_sost = [x for c in RESP2["por_corrida"] for x in c["fidelidad"]["no_sostenidas"] if any(w in x.lower().split() for w in _MADERAS)]
_no_sost = [_no_sost[0], next(x for x in _no_sost[1:] if not (set(x.lower().split()) & set(_no_sost[0].lower().split()) & set(_MADERAS)))]
assert len(_no_sost) == 2
lam("met-juez", "El generador y los jueces", "Métricas", f'''
{kick("04", "cómo evaluamos · el generador y los jueces")}
<h2 class="t chico">El generador: <em>faithfulness {f2(_F["global"])}</em> y <em>answer relevance {f2(_AR["media"])}</em></h2>
<div class="jz-grilla gen">
  <div class="jz"><h4>Faithfulness del porqué<b>{f2(_F["global"])}</b></h4>
    <p><b>{_F["sostenidas"]} de {_F["afirmaciones"]}</b> afirmaciones se infieren de lo que vio el generador: el pedido, la foto del cuarto y, de cada producto, su foto y una línea con su tipo y su medida. Lo que no se sostiene es casi siempre <b>la especie de la madera</b>:</p>
    <div class="jz-q"><span>«{esc(_no_sost[0])}»</span><span>«{esc(_no_sost[1])}»</span></div></div>
  <div class="jz"><h4>Answer relevance<b>{f2(_AR["media"])}</b></h4>
    <p>Un juez que no ve el pedido escribe tres pedidos que la lista contesta; se mide su coseno con el original. La vara: los pedidos escritos para <b>otras</b> listas dan <b>{f2(_AR["vara_cruzada"])}</b>; la propia les gana en {_AR["supera_a_la_cruzada"]} de {RESP2["corridas"]}.</p></div>
  <p class="jz-rep">Sobre las {RESP2["corridas"]} listas de la versión 2. Con otras {RESP["corridas"]} listas, las de la versión 1, dieron <b>{f2(_F1["global"])}</b> y <b>{f2(_AR1["media"])}</b> contra {f2(_AR1["vara_cruzada"])}: los dos números se repiten. No es una mejora de la versión 2: por ambiente, la faithfulness sube en {GEN_SUBE} y baja en {GEN_BAJA}.</p>
  <div class="jz" data-paso="1"><h4><span>Las rehicimos: había <em>data leakage</em></span></h4>
    <p>El prompt del juez traía de ejemplo el comienzo del pedido que se evaluaba, y lo copiaba. Y el juez de fidelidad leía la ficha completa, que el generador no ve. Daban {DOC["generador_v1"][0]} y {DOC["generador_v1"][1]}.</p>
    {prompt_tk("juez_pedidos_v1.md", [("A furnishing app takes a photo of a room and a request in Spanish", '"un comedor para seis")')],
               resaltar=['"un living nórdico y cálido"'], rotulo="el juez de antes · extracto", cls="jz-pr")}</div>
  <div class="jz" data-paso="2"><h4>Jueces: validado contra el ground truth, uno</h4>
    <p>El de relevancia graduada le da la nota máxima al producto anotado el {pct(G_ANOT2)} de las veces, y a los demás el {pct(G_OTROS2)}. <b>El de listas no está validado contra personas</b>: se le pregunta en los dos órdenes, y coinciden en {J_AZAR["acuerdo"]} de {J_AZAR["n"]} ambientes contra el azar, en {J_CAT["acuerdo"]} de {J_CAT["n"]} entre catálogos y en {J_VER["acuerdo"]} de {J_VER["n"]} entre versiones.</p>
    <div class="ordenes"><span><i>A</i><i>B</i></span><em>y</em><span><i>B</i><i>A</i></span></div></div>
</div>
<p class="remate chico" data-paso="2">El porqué se sostiene en casi <mark>9 de cada 10 afirmaciones</mark>; lo que agrega de más es la madera.</p>''',
    [f"Faithfulness: partimos el porqué en afirmaciones, y un juez dice cuáles se "
     f"infieren de lo que el generador vio. Da {f2(_F['global'])}: {_F['sostenidas']} de {_F['afirmaciones']}. Lo que no se "
     "sostiene es casi siempre la especie de la madera. Answer relevance: un juez que no ve el "
     f"pedido escribe los pedidos que esa lista contesta. Da {f2(_AR['media'])}, contra {f2(_AR['vara_cruzada'])} con pedidos "
     f"escritos para otras listas. Con otras once listas, las de la versión 1, dieron {f2(_F1['global'])} y {f2(_AR1['media'])}: "
     "los números se repiten.",
     "Estas métricas las rehicimos por data leakage: el prompt del juez traía de ejemplo «un living nórdico "
     "y cálido», que era justo como empezaba el pedido evaluado, y lo copiaba.",
     "Y sobre los jueces: validado contra el ground truth hay uno solo; el de listas se controla con los dos órdenes."],
    50)

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
_no_det = [KIND_ES.get(p["kind"], p["kind"]).lower() for p in HERO_MET["productos"] if not p["detectado"]]
_hero_rec = sum(p.get("puesto") == 1 for p in HERO_MET["productos"])
_fin_th = "".join(
    f'<figure class="fin{"" if f["img"]["room_check"]["ok"] else " no"}">{foto("fin-" + f["slug"], f["dir"] / "final.png", 170, 113, q=74)}'
    f'<figcaption><b>{"pasa" if f["img"]["room_check"]["ok"] else "no pasa"}</b>'
    f'{sum(p.get("puesto") == 1 for p in f["met"]["productos"])} de {len(f["met"]["productos"])}</figcaption></figure>'
    for f in FINALES)
_cred_fin = credito(*[f["slug"] for f in FINALES if FOTO[f["slug"]] in PUB_POR_ARCHIVO])
assert IMG_TOT["pasan"] == IMG_TOT["pasan_al_primero"], "alguna corrida final pasó el control al reintentar: revisar la lámina de la imagen"
lam("met-img", "La imagen", "Métricas", f'''
{kick("04", "cómo evaluamos · la imagen")}
<h2 class="t chico">La imagen: <em>{IMG_TOT["reconocidos"]} de {IMG_TOT["productos"]}</em> productos reconocidos, <em>{IMG_TOT["pasan"]} de {len(FINALES)}</em> cuartos</h2>
<div class="img-dos">
  <div class="it"><h4>¿Son esos productos? En el loft</h4>
    <div class="id-lista"><div class="id-cab"><span>en la lista</span><span>en la imagen</span><span>entre los de su tipo, sale</span></div>{"".join(_pares)}</div>
    <p>Se detecta cada mueble, se recorta y se compara con las fotos del catálogo de su tipo (DINOv3). <b>Reconocido</b> si el más parecido es el de la lista: acá, {_hero_rec} de {len(HERO_MET["productos"])} ({" y ".join(_no_det)}: sin detectar).</p></div>
  <div class="it" data-paso="1"><h4>Las {len(FINALES)} imágenes de la configuración final</h4>
    <span class="et">el control del ambiente (¿es ese cuarto?) · productos reconocidos</span>
    <div class="fines">{_fin_th}</div>
    <div class="it-cifras tres"><div><b>{IMG_TOT["reconocidos"]} de {IMG_TOT["productos"]}</b>reconocidos como el producto exacto ({pct(IMG_TOT["reconocidos"] / IMG_TOT["productos"])})</div>
      <div><b>{IMG_TOT["detectados"]}</b>aparecen (detectados) · coseno medio {f2(IMG_TOT["coseno"])}</div>
      <div><b>{IMG_TOT["pasan"]} de {len(FINALES)}</b>conservan el cuarto, todas al primer intento; en las otras {NO_PASAN} fallaron los {ROOM_CHECK["attempts"]}</div></div>
    <p class="cred-l">Fotos públicas: {_cred_fin}.</p></div>
</div>
<p class="remate chico" data-paso="1">La lista es confiable; la imagen es <mark>una visualización</mark>: acierta el producto exacto 4 de cada 10 veces y conserva el cuarto en {IMG_TOT["pasan"]} de {len(FINALES)}.</p>''',
    [f"La imagen la medimos sobre las {len(FINALES)} corridas finales, no sobre la mejor. Primero: ¿son esos productos? "
     "Detectamos cada mueble, lo recortamos y lo comparamos con las fotos del catálogo de su tipo: reconocido, si el más "
     "parecido es el de la lista. En el loft, el sofá, la biblioteca y la lámpara salen primeros; la alfombra, no. En total se "
     f"reconocen {IMG_TOT['reconocidos']} de {IMG_TOT['productos']}, el {round(100 * IMG_TOT['reconocidos'] / IMG_TOT['productos'])} "
     f"por ciento, aunque aparecen {IMG_TOT['detectados']}.",
     f"Segundo: ¿es ese cuarto? El control pasa en {IMG_TOT['pasan']} de {len(FINALES)}. O sea: la lista es confiable; la imagen "
     "es una visualización, que acierta el producto exacto cuatro de cada diez veces."],
    45, clase="clara")

# =============================================================================================
# Las trampas, dichas en voz alta
# =============================================================================================
_cos_banco = statistics.median(r["scores"][0] for r in rankings(HIB_DIR)[V1] if r["relevant"] and r["scores"])
_cos_flujo = sorted(DIAG_CAT[v]["puntaje_del_primero"]["mediana"] for v in ("ikea", "todos"))
_bm = EMB["bm25|description|filtro-kind"]
TRAMPAS = [
    ("El banco de la búsqueda es de producto conocido",
     f"Quien escribió la consulta veía el mueble: mide identificar un producto, no recomendar. En el flujo real el plan lo "
     f"imagina, y sus consultas quedan más lejos del catálogo: el coseno del primer candidato baja de {f3(_cos_banco)} a "
     f"{f2(_cos_flujo[0])}–{f2(_cos_flujo[1])}."),
    ("El mismo modelo escribe los dos lados",
     f"Consultas y descripciones salen del mismo modelo, con el mismo molde de 8 líneas. Por eso contar palabras rinde casi como "
     f"el embedder (BM25: {f3(_bm['hit@1'])} contra {f3(B1['hit@1'])}). Representa al sistema; no a alguien que escribe con otras palabras."),
    ("No hay conjunto apartado",
     f"Todo se eligió y se reporta sobre los mismos {N_AMB_ANS} ambientes. Las diferencias grandes se sostienen igual; las de 2 "
     "puntos no las leemos como señal."),
    (f"De punta a punta son {D['n_ambientes_vacios']} ambientes",
     f"El juez es el mismo modelo que elige. Corrimos la versión 2 dos veces: el que elige cambia {RUIDO_CAMBIAN} de "
     f"{RUIDO_PROD} productos, y el juez reparte los ambientes {J_RUIDO['a']} a {J_RUIDO['b']}. Que una variante «gane un "
     "ambiente» no es evidencia por sí solo: cuenta la asimetría. Y el pedido abierto no está evaluado: los pedidos enumeran las piezas."),
]
_tr = "".join(f'<div class="jz" data-paso="{i}"><h4><i>{i + 1}</i>{a}</h4><p>{b}</p></div>' for i, (a, b) in enumerate(TRAMPAS))
lam("trampas", "Las trampas", "Métricas", f'''
{kick("04", "cómo evaluamos · cuánto creerle")}
<h2 class="t">Las trampas, <em>dichas en voz alta</em></h2>
<div class="jz-grilla tr">{_tr}</div>
<p class="remate chico" data-paso="{len(TRAMPAS) - 1}">El ground truth sirve para comparar cambios grandes del índice. Lo que le sirve al usuario lo dice el juez, con <mark>n = {D["n_ambientes_vacios"]}</mark>.</p>''',
    ["Las trampas, en voz alta. Uno: el banco de la búsqueda es de producto conocido; en el flujo real el plan imagina "
     "el producto, no lo ve.",
     "Dos: el mismo modelo escribe las consultas y las descripciones, con el mismo molde; por eso contar palabras rinde casi "
     "como el embedder.",
     "Tres: no hay conjunto apartado.",
     f"Y cuatro: de punta a punta son {D['n_ambientes_vacios']} ambientes, y el juez es el mismo modelo que elige. Corrimos la "
     f"misma configuración dos veces: el que elige cambió {RUIDO_CAMBIAN} de {RUIDO_PROD} productos, y el juez repartió los "
     f"ambientes {J_RUIDO['a']} a {J_RUIDO['b']}. Ganar un ambiente no es evidencia: lo que cuenta es la "
     "asimetría. Por eso leemos las diferencias grandes, y las de dos puntos, no."],
    40)

# =============================================================================================
# El mapa de los experimentos: un pin por pregunta, sobre la fase a la que se la hicimos
# =============================================================================================
EXPS = [
    (1, "Qué se indexa", "texto del vendedor · descripción desde la foto"),
    (2, "Cómo se escribe la consulta", "la ficha · la frase natural · Type · kind"),
    (3, "Léxica, por foto e híbrida", "Qwen3 · BM25 · SigLIP 2 · fusionadas"),
    (4, "¿Error, o una variante?", "exacto · el mismo modelo · sirve (juez)"),
    (5, "Elegir con un VLM, y cuántos", "top-10 mirando las fotos · k de 1 a 10"),
    (6, "Qué catálogo", "IKEA · Amazon (ABO) · los dos (juez)"),
    (7, "Con búsqueda o sin búsqueda", f"los {K} mejores · {K} al azar · el catálogo entero (juez)"),
    (8, "Tres redactores", "las mismas consultas, escritas tres veces"),
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
<h2 class="t chico">Quince preguntas: <em>ocho con lámina propia</em>, siete de trámite</h2>
<ol class="hiper h14">{_h}</ol>
<p class="hiper-pie">cada pin, sobre la fase a la que le hizo la pregunta · lleno: con lámina propia · hueco: de trámite · <b>sin experimento: el modelo de imagen y los umbrales del control</b></p>
<div class="esq esq-hiper">{flujo(pines=range(1, 16), banco=f"{N_AMB} ambientes de IKEA anotados · {N_ANS} consultas con respuesta")}</div>''',
    "Ahora los experimentos, por cuánto importan. El mismo mapa: cada pin es una pregunta que le "
    "hicimos a una parte del sistema. Los llenos, del 1 al 8, tienen lámina propia. Dos de ellos, el 4 y el 8, no miden una "
    "fase: miden al banco de prueba. Los huecos, del 9 al 15, son los de trámite. "
    "Y dos cosas no las decidió ningún experimento: el modelo de imagen y "
    "los umbrales del control.",
    35)

"""El producto, la decisión v0 → v1, el mapa de los experimentos, los datos para medir y las métricas.
(El catálogo y el flujo los cuenta el recorrido por las fases: laminas_recorrido.py.)"""

from __future__ import annotations

from PIL import Image, ImageDraw

from datos import (AM, CAND_INFO, D, GT_ANY, GT_ROOM_PATH, HERO, HERO_CAND, HERO_CHOICE, HERO_IMG, HERO_REQ,
                   KIND_ES, N_HERO, N_HERO_UNID, PEDIDOS, PUB_POR_ARCHIVO, Q_LAMPARA, Q_MESA, ROOT,
                   TXT, V0_REC, V0_SOFA_OK, BASE, ESTILO, esc, f2, ic, medida)
from piezas import barras, consulta, etq, flujo, foto, kick, producto, ranking
from registro import lam

# =============================================================================================
# 1 · Portada
# =============================================================================================
_est = HERO_IMG["ambiente"]["sift_inliers"]
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
     "Nosotros queremos responder, para este ambiente y este pedido: qué productos reales, que se puedan comprar, van; "
     "cuántos y de qué medida; y cómo queda el ambiente con ellos."],
    35)

# =============================================================================================
# 3 · El producto
# =============================================================================================
_filas = []
for ch in HERO_CHOICE:
    c = CAND_INFO[ch["id"]]
    k = c.get("kind", "")
    md = medida(c.get("dimensions_cm"))
    _filas.append(f'<div class="li">{producto(ch["id"], 52)}<div class="li-t"><b>{KIND_ES.get(k, k)}</b>'
                  f'<span>{ch["id"]}{" · " + md if md else ""}</span></div><span class="li-q">×{ch["quantity"]}</span></div>')
_n_bib = next(ch["quantity"] for ch in HERO_CHOICE if CAND_INFO[ch["id"]].get("kind") == "bookcase")
lam("producto", "El producto", "El producto", f'''
{kick("01", "el producto")}
<h2 class="t">Una foto y un pedido. <em>Una lista de compra y una imagen.</em></h2>
<div class="pr-entra">
  <span class="et">entra</span>
  {foto("hero-room", HERO / "room.jpg", 420, 315)}
  <blockquote class="pedido">«{esc(HERO_REQ)}»</blockquote>
</div>
<div class="pr-img" data-paso="1">
  <span class="et">sale</span>
  {foto("hero-final", HERO / "final.png", 760, 570, q=82)}
  <p class="pr-pie">El mismo ambiente, con esos productos puestos.</p>
</div>
<div class="ticket pr-ticket" data-paso="1">
  <div class="tk-cab"><b>Lista de compra</b><span>amoblai<br>{N_HERO} productos</span></div>
  {"".join(_filas)}
  <div class="tk-tot"><span>{N_HERO} productos</span><span>{N_HERO_UNID} unidades</span></div>
</div>''',
    ["Así se usa. La entrada es una foto del ambiente y un pedido en texto libre, como este: un rincón de lectura con una "
     "biblioteca alta de madera oscura.",
     f"La salida son dos cosas: la lista de compra, con productos reales del catálogo y cuántas unidades de cada uno (acá, "
     f"{_n_bib} bibliotecas iguales), y la foto del mismo ambiente con esos productos puestos."],
    45)

# =============================================================================================
# 4 · Por qué RAG
# =============================================================================================
_rag_l = "".join(f'<div class="tk-l"><span class="tk-q">{i}</span><span class="tk-n">{a}</span><span class="tk-dots"></span>'
                 f'<span class="tk-v">{b}</span></div>' for i, (a, b) in enumerate(
                     [("El LLM decide qué hace falta", "plan"), ("El retrieval trae candidatos reales", "búsqueda"),
                      ("El VLM elige mirando sus fotos", "elección"), ("La imagen sale de las fotos elegidas", "imagen")], 1))
lam("rag", "Por qué RAG", "El producto", f'''
{kick("01", "por qué RAG")}
<h2 class="t">Recomendaciones atadas a <em>productos que existen</em></h2>
<div class="rag-tres">
  <div class="rag-c">
    <h3>Un LLM solo</h3><p>Sabe de decoración, pero no sabe qué hay en un catálogo.</p>
    <div class="ticket rag-tk"><div class="tk-cab"><b>Recomendación</b><span>LLM</span></div>
      <div class="tk-l"><span class="tk-q">1</span><span class="tk-n">Sillón de cuero coñac</span><span class="tk-dots"></span><span class="tk-v">art. ———</span></div>
      <div class="sello-tk">nadie lo vende</div></div>
  </div>
  <div class="rag-c">
    <h3>Un modelo de imagen solo</h3><p>Amobla lindo, pero inventa los muebles.</p>
    <div class="ticket rag-tk"><div class="tk-cab"><b>Lista de compra</b><span>imagen</span></div>
      <div class="tk-vacio">—</div>
      <div class="sello-tk">no hay nada que comprar</div></div>
  </div>
  <div class="rag-c elegida" data-paso="1">
    <h3>RAG: el catálogo es la base de conocimiento</h3><p>Cada paso trabaja sobre productos reales.</p>
    <div class="ticket rag-tk"><div class="tk-cab"><b>amoblai</b><span>RAG</span></div>{_rag_l}
      <div class="tk-tot"><span>art. {HERO_CHOICE[0]["id"]}</span><span>×{HERO_CHOICE[0]["quantity"]}</span></div></div>
  </div>
</div>
<p class="remate" data-paso="1">No es un Q&amp;A: la consulta es una foto y un pedido abierto, y la respuesta es una <mark>combinación de productos</mark> que tiene que funcionar junta.</p>''',
    ["¿Por qué un RAG y no un LLM o un modelo de imagen solos? Un LLM sabe de decoración, pero no sabe qué hay en un "
     "catálogo: te recomienda un sillón de cuero coñac que nadie vende. Un modelo de imagen amobla lindo, pero inventa los "
     "muebles.",
     "Con RAG, el catálogo es la base de conocimiento: el LLM decide qué hace falta, el retrieval trae candidatos reales, el "
     "VLM elige mirando sus fotos, y la imagen sale de esas fotos. No es un Q&A: la respuesta es una combinación de productos "
     "que tiene que funcionar junta."],
    45, clase="clara")

# =============================================================================================
# 6 · Ground truth
# =============================================================================================
_gt_tags = "".join(producto(i, 78, "gt-p") for i in GT_ANY[:9])
lam("gt", "Ground truth", "Datos", f'''
{kick("03", "datos para medir · ground truth")}
<h2 class="t">El ground truth: <em>ambientes reales con sus muebles</em></h2>
<div class="gt-izq">
  {foto("gt-room", GT_ROOM_PATH, 760, 477)}
  <span class="et">productos anotados en esta foto</span>
  <div class="gt-strip">{_gt_tags}</div>
</div>
<div class="gt-der">
  <span class="et">por cada mueble visible, un subagente escribe la búsqueda como la escribiría el plan</span>
  {consulta(Q_MESA["query"], cls="gt-q")}
  <div data-paso="1">
    <span class="et">lo que trae el retrieval: acierta si el anotado sale primero (hit@1) o entre los k primeros (hit@k)</span>
    {ranking(Q_MESA, 5, 128)}
  </div>
</div>
<div class="gt-cifras" data-paso="2">
  <div><b>{D["n_ambientes_gt"]}</b>fotos de livings y comedores reales de IKEA</div>
  <div><b>{D["n_busquedas"]}</b>búsquedas, una por mueble visible</div>
  <div><b>{D["n_respondibles"]}</b>con su producto en el catálogo</div>
  <div class="gt-ic">Intervalos de confianza: <b>bootstrap por ambiente</b>, porque las búsquedas de un mismo ambiente no son independientes.</div>
</div>''',
    [f"Para medir el retrieval necesitamos saber cuál es el producto correcto. El dataset trae {D['n_ambientes_gt']} fotos de "
     "livings y comedores reales de IKEA con sus productos anotados. Por cada mueble visible, un subagente escribe la búsqueda "
     "como la escribiría nuestro plan, mirando el ambiente.",
     "Una búsqueda acierta si el anotado sale primero (hit@1) o entre los k primeros.",
     f"En total, {D['n_busquedas']} búsquedas, {D['n_respondibles']} con su producto en el catálogo. Los intervalos de "
     "confianza son por bootstrap por ambiente, porque las búsquedas de un mismo ambiente no son independientes."],
    50, clase="clara")

# =============================================================================================
# 7 · Ambientes vacíos
# =============================================================================================
_tiles = []
for p in PEDIDOS:
    nombre, estilo = ESTILO[p["slug"]]
    pub = PUB_POR_ARCHIVO.get(p["foto"])
    cred = f'<span class="cred">{esc(pub["autor"])} · {esc(pub["licencia"])}</span>' if pub else ""
    _tiles.append(f'<figure class="amb{" pub" if pub else ""}">{foto("vac-" + p["slug"], p["foto"], 262, 176, q=76)}'
                  f'<figcaption><b>{nombre}</b><span>{estilo}</span>{cred}</figcaption></figure>')
lam("vacios", "Ambientes vacíos", "Datos", f'''
{kick("03", "datos para medir · ambientes vacíos")}
<h2 class="t chico">Ambientes vacíos reales, <em>para probar de punta a punta</em></h2>
<div class="vac-izq">
  <div class="cifra"><span>{D["n_ambientes_vacios"]}</span></div>
  <p class="cifra-pie">ambientes vacíos reales, cada uno con un pedido escrito como lo escribiría un usuario que sabe pedir</p>
  <ul class="vac-datos">
    <li><b>{D["n_propios"]}</b> de departamentos nuestros</li>
    <li><b>{D["n_publicos"]}</b> públicos, de Wikimedia Commons y Flickr (Creative Commons), con estilos distintos del nórdico</li>
    <li>elegidos entre <b>{D["n_publicas_revisadas"]}</b> que revisamos uno por uno para descartar renders y fotos generadas con IA</li>
  </ul>
  <p class="vac-nota">Acá no hay ground truth: medimos con un juez y con métricas de imagen.</p>
</div>
<div class="vac-grilla">{"".join(_tiles)}</div>''',
    f"Para probar el sistema completo hacen falta ambientes vacíos reales. Tenemos {D['n_ambientes_vacios']}: "
    f"{D['n_propios']} de departamentos nuestros y {D['n_publicos']} públicos de Wikimedia Commons y Flickr, con licencia "
    f"Creative Commons, elegidos entre {D['n_publicas_revisadas']} que revisamos uno por uno para descartar renders y fotos "
    "generadas con IA. Cada uno tiene un pedido escrito como lo escribiría un usuario que sabe pedir; los públicos, con estilos "
    "distintos del nórdico. Acá no hay ground truth: medimos con un juez y con métricas de imagen.",
    40)

# =============================================================================================
# 8 · v0 → v1
# =============================================================================================
_room_im = Image.open(ROOT / GT_ROOM_PATH)
_bx = [round(v) for v in V0_REC["box"]]
_crop = _room_im.crop(_bx)
_sx = 470 / _room_im.width
_box_css = (f"left:{_bx[0] * _sx:.0f}px;top:{_bx[1] * _sx:.0f}px;width:{(_bx[2] - _bx[0]) * _sx:.0f}px;"
            f"height:{(_bx[3] - _bx[1]) * _sx:.0f}px")
_hero_q = HERO_CAND[0]["spec"]["query"]
lam("v0v1", "v0 → v1", "Arquitectura", f'''
{kick("02", "arquitectura · v0 → v1")}
<h2 class="t">Por qué dejamos <em>la búsqueda por imagen</em></h2>
<div class="v-col v-a">
  <div class="v-et"><b>v0</b> buscar por imagen</div>
  <div class="v-foto">{foto("v0-room", GT_ROOM_PATH, 470, round(_room_im.height * _sx))}<div class="v-caja" style="{_box_css}"></div></div>
  <div class="v0-cadena">{foto("v0-crop", _crop, 170, 84, modo="fit", q=82)}<span class="v-fl">→</span>{producto(V0_SOFA_OK, 92)}</div>
  <p class="v-txt">Grounding DINO detecta cada mueble, SAM lo recorta y DINOv3 busca la foto del catálogo más parecida. Sirve para encontrar <b>este</b> sofá.</p>
</div>
<div class="v-col v-b">
  <div class="v-et">nuestro caso</div>
  <div class="v-foto">{foto("hero-room-v", HERO / "room.jpg", 400, 300)}<div class="v-nada">¿qué recortamos?</div></div>
  <p class="v-txt">Un ambiente vacío: no hay nada que recortar.</p>
</div>
<div class="v-col v-c">
  <div class="v-et"><b>v1</b> buscar por texto</div>
  <p class="v-txt">Un LLM escribe el producto ideal en el mismo formato que el catálogo:</p>
  {consulta(_hero_q, 6, "v-q")}
</div>
<div class="v-res" data-paso="1">
  {barras([dict(et="v0 · por imagen", sub=f"{D['v0_n']} recortes", v=D['v0_hit1'], ic=D["v0_ic"]),
           dict(et="v1 · por texto", sub=f"{D['v1_n']} búsquedas", v=D['v1_hit1'], ic=ic(TXT, BASE), gana=True)],
          titulo="hit@1 · con el mismo ground truth", paso=1, gana_paso=1, cls="v-barras")}
  <p class="v-res-n">y la v1 funciona <b>con el ambiente vacío</b></p>
</div>''',
    ["La primera versión buscaba por imagen: detectaba cada mueble en la foto con Grounding DINO, lo recortaba con SAM y "
     "buscaba la foto del catálogo más parecida con DINOv3. Eso sirve para encontrar este sofá, pero nuestro caso es un "
     "ambiente vacío: no hay nada que recortar. La v1 busca por texto: un LLM escribe el producto ideal en el mismo formato "
     "que el catálogo.",
     f"Con el mismo ground truth, la v1 da {f2(D['v1_hit1'])} de hit@1 contra {f2(D['v0_hit1'])} de la v0, y además funciona "
     "con el ambiente vacío."],
    55, clase="clara")

# =============================================================================================
# 10 · Los hiperparámetros: un pin por experimento
# =============================================================================================
HIPER = [
    ("Texto que se indexa", "vendedor · VLM · nombre + VLM", "hit@1"),
    ("Embedder", "hashing · BGE-base · Qwen3", "hit@1, MRR"),
    ("Filtro duro", "ninguno · por tipo · por kind", "hit@1, hit@10"),
    ("Splitting", "entero · por línea · línea a línea", "hit@1"),
    ("Dimensión del vector", "de 32 a 1024 componentes", "hit@1"),
    ("Base y consulta", "exacta · HNSW; completa · Type · kind", "hit@1"),
    ("Reranking", "ninguno · cross-encoder · VLM", "hit@1, MRR"),
    ("Candidatos por pieza", "k de 1 a 10", "acierto al elegir"),
    ("Alcance del catálogo", f"{D['prod_268']} · {D['prod_855']} · revisado", "hit@1"),
    ("Qué catálogo", "IKEA · Amazon (ABO) · los dos", "juez de a pares"),
    ("Cómo medir", "hit@1 · graduada · 3 redactores", "acuerdo con el GT"),
    ("La imagen", "guiada · libre · sin tope · estricta", "SIFT, SSIM"),
    ("Réplica: decirle dónde", "nada · palabras · cajas 2D o 3D", "IoU con la foto real"),
]
_h = "".join(f'<li><em>{i}</em><b>{q}</b><span>{o}</span><i>{mt}</i></li>' for i, (q, o, mt) in enumerate(HIPER, 1))
lam("hiper", "Los hiperparámetros", "Arquitectura", f'''
{kick("02", "arquitectura · los experimentos")}
<h2 class="t chico">Trece decisiones, <em>un experimento cada una</em></h2>
<ol class="hiper">{_h}</ol>
<p class="hiper-pie">qué probamos, con todo lo demás fijo · cómo lo medimos</p>
<p class="hiper-rm">el mapa del <b>recorrido</b> · el número dice en qué fase pega cada experimento</p>
<div class="esq esq-hiper">{flujo(pines=range(1, 14))}</div>''',
    "Estas son las decisiones que fuimos nombrando en el recorrido, sobre el mismo mapa: cada número marca en qué fase pega su "
    "experimento. Todavía no decimos qué ganó. Primero, con qué datos y qué métricas medimos; después, cada experimento en dos "
    "láminas, la pregunta y el resultado con su decisión, en el orden en que los hicimos: cada uno deja su decisión en la "
    "configuración del siguiente.",
    30)

# =============================================================================================
# 11 · Métricas de retrieval
# =============================================================================================
_lamp_rank = Q_LAMPARA["rank"]
_mdefs = [("hit@k", "¿El anotado está entre los k primeros? hit@1 es encontrarlo primero; hit@k con k igual a los candidatos "
           "que ve el VLM es el techo de lo que puede elegir."),
          ("MRR@10", "El promedio de 1 / posición del correcto. Premia que esté arriba, no solo que esté."),
          ("Context recall y precision", "Las de RAGAS: cuántos de los productos de un ambiente aparecen entre los candidatos, y cuán arriba quedan."),
          ("NDCG@10", "Como el MRR, pero admite relevancia graduada: un candidato «aceptable» suma algo."),
          ("IC 95%", "Si los intervalos de dos métodos se pisan, con estos datos no los podemos distinguir.")]
_md = "".join(f'<div class="md"><h4>{a}</h4><p>{b}</p></div>' for a, b in _mdefs)
lam("met-ret", "Métricas de retrieval", "Métricas", f'''
{kick("04", "métricas · retrieval")}
<h2 class="t">Con ground truth: <em>¿trae el producto correcto, y arriba?</em></h2>
<div class="met-ej">
  <span class="et">una búsqueda real del ground truth (una lámpara de pie): sus 10 primeros candidatos</span>
  <div class="met-cotas">
    <div style="--k:1"><span>hit@1 = 0</span></div><div style="--k:3"><span>hit@3 = 1</span></div><div style="--k:5"><span>hit@5 = 1</span></div>
  </div>
  {ranking(Q_LAMPARA, 10, 150)}
  <p class="met-rr">el anotado está en el puesto {_lamp_rank}: suma <b>1/{_lamp_rank}</b> al MRR</p>
</div>
<div class="met-defs" data-paso="1">{_md}</div>''',
    ["Las métricas de retrieval, donde sí hay ground truth. Arriba, una búsqueda real: el anotado sale segundo. hit@k: si el "
     "anotado está entre los k primeros; acá hit@1 da 0 y hit@3 da 1. MRR: el promedio de uno sobre la posición del correcto; "
     "esta búsqueda suma un medio.",
     "hit@k con k igual a los candidatos que ve el VLM es el techo de lo que puede elegir. Context recall y precision son las "
     "de RAGAS. NDCG admite relevancia graduada. Y si los intervalos de confianza de dos métodos se pisan, no los podemos "
     "distinguir."],
    50, clase="clara")

# =============================================================================================
# 12 · Jueces
# =============================================================================================
lam("met-juez", "Jueces y pares", "Métricas", f'''
{kick("04", "métricas · la respuesta")}
<h2 class="t">Sin un único correcto: <em>jueces validados, y de a pares</em></h2>
<div class="jz-grilla">
  <div class="jz"><h4>Relevancia graduada</h4>
    <p>Un LLM califica cada uno de los 3 primeros candidatos. Antes de creerle, chequeamos que le dé 2 al producto anotado.</p>
    <div class="notas3"><div><b>2</b>el mismo o indistinguible</div><div><b>1</b>una alternativa aceptable</div><div><b>0</b>no sirve</div></div></div>
  <div class="jz"><h4>RAGAS sobre la explicación</h4>
    <p>Cada elección viene con su porqué.</p>
    <div class="dos-def"><div><b>Faithfulness</b>¿lo que dice se sostiene con lo que vio?</div><div><b>Answer relevance</b>¿responde al pedido?</div></div></div>
  <div class="jz"><h4>Juez de a pares, en los dos órdenes</h4>
    <p>Para comparar variantes sin ground truth: el juez ve las dos listas sin saber cuál es cuál. Una gana un ambiente solo si gana en los dos órdenes; reportamos cuánto coinciden.</p>
    <div class="ordenes"><span><i>A</i><i>B</i></span><em>y</em><span><i>B</i><i>A</i></span></div></div>
  <div class="jz"><h4>El costo de cada llamada</h4>
    <p>Cada llamada paga queda registrada con su costo; las respuestas de los jueces quedan en caché.</p>
    <div class="recibo-mini"><span>plan</span><span>elección</span><span>juez</span><span>imagen</span></div></div>
</div>''',
    "Cuando no hay un único correcto usamos jueces, pero validados. Relevancia graduada: un LLM califica el top-3 con 2, 1 o 0, "
    "y antes chequeamos que le dé 2 al anotado. RAGAS sobre la explicación de cada elección: faithfulness y answer relevance. "
    "Para comparar variantes sin ground truth, un juez de a pares en los dos órdenes. Y el costo de cada llamada.",
    40)

# =============================================================================================
# 13 · Métricas de imagen
# =============================================================================================
_hm = HERO_IMG
_fin = Image.open(HERO / "final.png").convert("RGB")
_fin_cajas = _fin.copy()
_dr = ImageDraw.Draw(_fin_cajas, "RGBA")
for p in _hm["productos"]:
    if p.get("box"):
        _dr.rectangle(p["box"], outline=(255, 91, 63, 255), width=5, fill=(255, 91, 63, 50))
_pares = "".join(
    f'<div class="id-par">{producto(p["id"], 100)}<span class="id-fl">↔</span>'
    f'{foto("crop-" + p["id"], _fin.crop(p["box"]), 100, 100, modo="fit", q=82)}<span class="id-p"><b>{p["puesto"]}.º</b> de {p["entre"]}</span></div>'
    for p in _hm["productos"][:3])
_fid = _hm["fidelidad"]
lam("met-img", "Métricas de imagen", "Métricas", f'''
{kick("04", "métricas · la imagen")}
<h2 class="t">La imagen: <em>el mismo cuarto, con lo que se pidió</em></h2>
<div class="img-tres">
  <div class="it"><h4>¿Es el mismo cuarto?</h4>
    <div class="par-fotos">{foto("hero-final-cajas", _fin_cajas, 536, 402, q=80)}<div class="pf-in">{foto("hero-room-xs", HERO / "room.jpg", 176, 132)}<span>la foto vacía</span></div></div>
    <div class="it-cifras"><div><b>{_hm["ambiente"]["sift_inliers"]}</b>puntos de la foto reencontrados</div><div><b>{f2(_hm["ambiente"]["ssim_fuera_de_los_muebles"])}</b>SSIM fuera de los muebles</div></div>
    <p><b>SIFT</b> reencuentra puntos de la foto original y mide cuánto se movió la cámara. <b>SSIM</b> compara lo que no es mueble (afuera de las cajas).</p></div>
  <div class="it"><h4>¿Son los mismos productos?</h4>
    <div class="id-lista"><div class="id-cab"><span>en la lista</span><span>en la imagen</span><span>el de la lista sale</span></div>{_pares}</div>
    <div class="it-cifras"><div><b>{_fid["detectados"]} de {_fid["productos"]}</b>productos detectados</div><div><b>{round(_fid["identificados@1"] * _fid["productos"])} de {_fid["productos"]}</b>con el de la lista primero</div></div>
    <p>Detectamos cada mueble, lo recortamos y vemos si el más parecido del catálogo es el de la lista.</p></div>
  <div class="it"><h4>¿Es lo que se pidió?</h4>
    <div class="siglip"><span class="sg-ped">«{esc(HERO_REQ[:150])}…»</span><span class="sg-x">SigLIP 2 · parecido entre el pedido y</span>
      <div class="sg-b"><span>la imagen final</span><i style="--w:{_hm["pedido_imagen"]["siglip_final"] / 0.15 * 100:.0f}%"></i><b>{f2(_hm["pedido_imagen"]["siglip_final"])}</b></div>
      <div class="sg-b v"><span>la foto vacía</span><i style="--w:{_hm["pedido_imagen"]["siglip_vacia"] / 0.15 * 100:.0f}%"></i><b>{f2(_hm["pedido_imagen"]["siglip_vacia"])}</b></div></div>
    <div class="it-cifras tres"><div><b>{_fid["productos"] - _fid["detectados"]}</b>faltan</div><div><b>{len(_hm["repetidas"])}</b>repetidos</div><div><b>{len(_hm["inventadas"])}</b>inventado</div></div>
    <p><b>SigLIP 2</b> entre el pedido y la imagen, y contamos lo que <b>falta</b>, lo <b>repetido</b> y lo <b>inventado</b>.</p></div>
</div>
<p class="img-pie">Además: reproducibilidad, con tres redactores de las búsquedas, y el espacio de embeddings.</p>''',
    "Para la imagen medimos tres cosas. Que sea el mismo cuarto: SIFT reencuentra puntos de la foto original y mide cuánto se "
    "movió la cámara, y SSIM compara lo que no es mueble. Que sean los mismos productos: detectamos cada mueble, lo recortamos "
    "y vemos si el más parecido del catálogo es el de la lista. Y que sea lo que se pidió: SigLIP 2 entre el pedido y la imagen, "
    "y contamos lo que falta, lo repetido y lo inventado. Además, reproducibilidad, con tres redactores, y el espacio de "
    "embeddings.",
    45, clase="clara")

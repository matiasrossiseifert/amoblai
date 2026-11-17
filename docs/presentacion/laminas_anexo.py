"""Anexo: láminas que no se pasan, para mostrar si preguntan. Van después de «gracias», no suman
tiempo al guion y se abren con la tecla A desde la lámina que las nombra en `anexo` (la A, en el
anexo, vuelve a esa lámina y a ese paso).

    A · el prompt completo de la descripción (fase 2), desde la D7
    B · cuánto cuesta un pedido y cuánto costó el trabajo (laminas_cierre.py)
    C · lo que cuesta cada opción: los costos que salieron de las láminas del recorrido y de los experimentos
    D · las fotos públicas de los ambientes, con su autor y su licencia (las láminas van sin pie de foto)
    E · el prompt completo del juez de faithfulness, desde la lámina del caso (el loft)
    F · el prompt completo del juez de listas, desde la lámina del caso (el japandi)
"""

from __future__ import annotations

from datos import C_CHOOSE_V2, C_CTX_CACHE, C_CTX_SIN, C_DESC, C_RERANK, C_SCENE, ESTILO, K, PEDIDOS, PUB_POR_ARCHIVO, esc, usd
from piezas import kick
from recorrido import _marcar, cuerpo_prompt
from registro import LAMINAS, lam

_P = "describe_product_v3.md"
_txt = cuerpo_prompt(_P).strip()
_corte = _txt.index("Three examples")
_instr, _ejemplos = _txt[:_corte].rstrip(), _txt[_corte:]
_regla = "Say only what the photos and the name show. No brand, price, measurements, care or assembly."
assert _regla in _instr, _regla

lam("anexo-descripcion", "Anexo A: el prompt de la descripción", "Anexo", f'''
{kick("A", "anexo · fase 2 · descripción")}
<h2 class="t chico anx-t">El prompt completo de la descripción</h2>
<div class="pr-tk anx-pr">
  <div class="pr-cab"><b>{_P}</b><span>completo, tal cual se manda · <i class="ph">{{marcadores}}</i>: los datos de cada producto</span></div>
  <div class="anx-cols"><pre class="pr-tx">{_marcar(_instr, [_regla])}</pre><pre class="pr-tx anx-ej">{_marcar(_ejemplos, [])}</pre></div>
</div>''',
    ["Si preguntan qué recibe el modelo que describe: las fotos del producto, y en el texto su tipo, su nombre y sus medidas, "
     "que son los marcadores en color. Las medidas le dan la escala, pero no las puede escribir. Con la A se vuelve al recorrido."],
    0, clase="clara anexo")

next(s for s in LAMINAS if s["id"] == "rec-descripcion")["anexo"] = "anexo-descripcion"


def _l(n, v, tag=""):
    return (f'<div class="tk-l"><span class="tk-n">{n}</span>{f"<i class=anx-tag>{tag}</i>" if tag else ""}'
            f'<span class="tk-dots"></span><b>{v}</b></div>')


lam("anexo-costos-opciones", "Anexo C: lo que cuesta cada opción", "Anexo", f'''
{kick("C", "anexo · costo de cada opción")}
<h2 class="t chico">Lo que cuesta <em>cada opción</em></h2>
<div class="ticket anx-tk">
  <div class="tk-cab"><b>cada opción</b><span>del registro de gastos</span></div>
  {_l("Describir un producto", usd(C_DESC, 3), "fase 2 · una vez")}
  <div class="anx-sep"></div>
  {_l("Escena con la plantilla", usd(0), "exp. 15 · por pedido")}
  {_l("Escena escrita por el LLM", usd(C_SCENE, 3))}
  <div class="anx-sep"></div>
  {_l("Reordenar el top-10 con un VLM", usd(C_RERANK), "exp. 5 · por búsqueda")}
  <div class="anx-sep"></div>
  {_l(f"Elegir entre {K}, con foto", usd(C_CHOOSE_V2, 3), "exp. 6 · por pedido")}
  {_l("Elegir con el catálogo entero, en caché", usd(C_CTX_CACHE))}
  {_l("Elegir con el catálogo entero, sin caché", usd(C_CTX_SIN))}
</div>''',
    [f"Lo que cuesta cada opción. Describir un producto por la API, {usd(C_DESC, 3)}, una vez. La escena escrita por el LLM "
     f"suma {usd(C_SCENE, 3)} por pedido; la plantilla, nada. Reordenar con un VLM, {usd(C_RERANK)} por búsqueda. Y elegir: "
     f"entre {K} con foto, {usd(C_CHOOSE_V2, 3)}; con el catálogo entero, {usd(C_CTX_CACHE)} con la caché caliente y "
     f"{usd(C_CTX_SIN)} sin caché."],
    0, clase="anexo")

_pubs = [(p["slug"], PUB_POR_ARCHIVO[p["foto"]]) for p in PEDIDOS if p["foto"] in PUB_POR_ARCHIVO]
_sitio = lambda u: "Wikimedia Commons" if "wikimedia" in u else ("Flickr" if "flickr" in u else u.split("/")[2])
_fotos = "".join(f'<li><b>{ESTILO[s][0]}</b><span>{ESTILO[s][1]}</span><p>{esc(f["autor"])} · {esc(f["licencia"])} · {_sitio(f["url_pagina"])}</p></li>'
                 for s, f in _pubs)
lam("anexo-fotos", "Anexo D: las fotos de los ambientes", "Anexo", f'''
{kick("D", "anexo · créditos")}
<h2 class="t chico">Las fotos públicas <em>de los ambientes</em></h2>
<ul class="anx-fotos">{_fotos}</ul>''',
    [f"Las {len(_pubs)} fotos públicas de los ambientes vacíos, con su autor y su licencia. Las otras son de departamentos "
     "reales, de uso privado."],
    0, clase="clara anexo")

_PJ = "juez_fidelidad_v2.md"
_txt_j = cuerpo_prompt(_PJ).strip()
_regla_j = "A measure the line does not give is not supported, even if it looks plausible in the photo."
assert _regla_j in _txt_j, _regla_j
lam("anexo-juez", "Anexo E: el prompt del juez de faithfulness", "Anexo", f'''
{kick("E", "anexo · el juez de faithfulness")}
<h2 class="t chico anx-t">El prompt completo del juez de faithfulness</h2>
<div class="pr-tk anx-pr anx-pj">
  <div class="pr-cab"><b>{_PJ}</b><span>completo, tal cual se manda · <i class="ph">{{marcadores}}</i>: lo que vio el generador</span></div>
  <pre class="pr-tx">{_marcar(_txt_j, [_regla_j])}</pre>
</div>''',
    ["Si preguntan cómo juzga: le damos la foto del ambiente, la de cada producto elegido con su línea, el pedido y el porqué. "
     "Parte el porqué en afirmaciones y marca cada una. Con la A se vuelve al caso."],
    0, clase="clara anexo")

next(s for s in LAMINAS if s["id"] == "met-fid")["anexo"] = "anexo-juez"

_PL = "juez_listas_v1.md"
_txt_l = cuerpo_prompt(_PL).strip()
_regla_l = 'Then say which proposal you would send the client: "A", "B", or "tie" only if you truly can\'t choose.'
assert _regla_l in _txt_l, _regla_l
lam("anexo-juez-listas", "Anexo F: el prompt del juez de listas", "Anexo", f'''
{kick("F", "anexo · el juez de listas")}
<h2 class="t chico anx-t">El prompt completo del juez de listas</h2>
<div class="pr-tk anx-pr anx-pj anx-pl">
  <div class="pr-cab"><b>{_PL}</b><span>completo, tal cual se manda · <i class="ph">{{marcadores}}</i>: el pedido y las dos listas</span></div>
  <pre class="pr-tx">{_marcar(_txt_l, [_regla_l])}</pre>
</div>''',
    ["Si preguntan cómo compara: ve la foto, el pedido y las dos listas con la foto de cada producto; califica cada producto, "
     "puntúa cada lista en tres criterios y elige. Con la A se vuelve al caso."],
    0, clase="clara anexo")

next(s for s in LAMINAS if s["id"] == "met-lj")["anexo"] = "anexo-juez-listas"

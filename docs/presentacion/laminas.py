"""Las láminas, en orden: cada módulo las registra al importarse y acá se ordenan. Cada número sale
de datos.py. El hilo es el de la revisión del 2026-11-12 (docs/REVISION.md):

    el producto y por qué es un RAG · el recorrido por las once fases, con el mapa · los desafíos ·
    cómo evaluamos (los dos sets de evaluación, las métricas, las advertencias) · los experimentos por su ranking
    (ocho con lámina propia, el camino incremental, siete de trámite) · el Ejercicio 4 (versión 1 y
    versión 2) · limitaciones, trabajo futuro y conclusiones (los costos, en el anexo)
"""

import laminas_intro  # noqa: F401  producto, por qué RAG, desafíos, datos para medir, métricas, advertencias, mapa de experimentos
import laminas_recorrido  # noqa: F401  el recorrido por las once fases
import laminas_exp  # noqa: F401  los experimentos, por su ranking
import laminas_cierre  # noqa: F401  Ejercicio 4, limitaciones, trabajo futuro, conclusiones (y el anexo B, costo)
import laminas_anexo  # noqa: F401  el anexo (no se pasa: se abre con la A)
import laminas_extra  # noqa: E402  los experimentos de punta a punta, el 5b y el coseno sin juez
import os  # noqa: E402

SIMPLE = bool(os.environ.get("SIMPLE"))

from registro import LAMINAS  # noqa: E402

ORDEN = [
    "portada", "problema", "producto", "rag",
    "rec-mapa", "rec-catalogo", "rec-descripcion", "rec-indice", "rec-plan", "rec-plan-prompt", "rec-busqueda",
    "rec-eleccion", "rec-escena", "rec-imagen", "rec-lista",
    "desafios",
    "gt", "vacios", "met-lj", "met-ret", "met-juez", "met-fid", "met-img", "trampas",
    "partida", "hiper", "e1", "e1r", "e2", "e2r", "e3", "e3r", "camino", "e4", "e5", "e5r", "e6", "e6r", "e6c", "e7", "e8",
    "e9", "e10", "e11", "e12", "e13", "e14", "e15",
    "ej4-v1", "ej4-v2", "ej4-res",
    "limites", "futuro", "conclusiones", "gracias",
    "anexo-descripcion", "anexo-costo", "anexo-costos-opciones", "anexo-fotos", "anexo-juez", "anexo-juez-listas",
]
for _id, _despues in laminas_extra.DESPUES:  # cada una, después de la que dice
    ORDEN.insert(ORDEN.index(_despues) + 1, _id)
_por_id = {s["id"]: s for s in LAMINAS}
assert set(ORDEN) == set(_por_id) and len(ORDEN) == len(LAMINAS), (set(ORDEN) ^ set(_por_id))
if SIMPLE:  # presentacion_simple.html: los experimentos, una lámina cada uno (laminas_simple.py)
    import laminas_simple

    _por_id.update({s["id"]: s for s in LAMINAS if s["id"] in laminas_simple.IDS})
    ORDEN = ORDEN[:ORDEN.index("e1")] + laminas_simple.IDS + ORDEN[ORDEN.index("ej4-v1"):]
    # Los experimentos del 2026-11-16 (laminas_modelos.py): después del Ejercicio 4, así el camino
    # queda como estaba y lo que cambia una decisión es un paso más, al final
    import laminas_modelos

    _por_id.update({s["id"]: s for s in LAMINAS if s["id"] in laminas_modelos.IDS})
    ORDEN.insert(ORDEN.index("ej4-res") + 1, "__modelos__")
    _i = ORDEN.index("__modelos__")
    ORDEN[_i:_i + 1] = laminas_modelos.IDS
LAMINAS[:] = [_por_id[i] for i in ORDEN]

# Segundos por lámina: las palabras de sus notas a PPM palabras por minuto (con un piso para las
# láminas que se miran más de lo que se leen). 135 por minuto, el mismo ritmo que usa el guion de
# la presentación principal (las 155 de antes pedían hablar sin pausas). Se ajusta acá después de
# ensayar. "seg_real" es lo que se suma (sin redondear, para que el total no dependa de
# de qué lado de un redondeo cae cada lámina); "seg", lo que se muestra, de a 5 segundos.
PPM = 135
_MIN = {**{f"e{n}": 15 for n in range(9, 16)}, **{f"s{n}": 15 for n in range(9, 16)}, "s-camino": 30, "portada": 25, "gracias": 5, "producto": 30, "conclusiones": 40, "camino": 30, "hiper": 30, "rec-mapa": 35, "rec-lista": 25}
for _s in LAMINAS:
    _n = _s["notas"]
    _s["palabras"] = len((" ".join(_n) if isinstance(_n, list) else _n).split())
    _s["seg_real"] = max(_MIN.get(_s["id"], 20), _s["palabras"] * 60 / PPM)
    _s["seg"] = round(_s["seg_real"] / 5) * 5
    if _s["id"].startswith("anexo-"):  # el anexo no se pasa: no suma tiempo ni palabras
        _s["palabras"] = _s["seg_real"] = _s["seg"] = 0

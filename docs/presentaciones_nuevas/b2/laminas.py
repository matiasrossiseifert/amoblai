"""Las láminas, en orden: cada módulo las registra al importarse y acá se ordenan. Cada número sale
de datos.py. El hilo es el de la revisión del 2026-11-12 (docs/REVISION.md):

    el producto y por qué es un RAG · el recorrido por las once fases, con el mapa · los desafíos ·
    cómo evaluamos (los dos bancos, las métricas, las trampas) · los experimentos por su ranking
    (ocho con lámina propia, el camino incremental, siete de trámite) · el Ejercicio 4 (versión 1 y
    versión 2) · costo, limitaciones, trabajo futuro y conclusiones
"""

import laminas_intro  # noqa: F401  producto, por qué RAG, desafíos, datos para medir, métricas, trampas, mapa de experimentos
import laminas_recorrido  # noqa: F401  el recorrido por las once fases
import laminas_exp  # noqa: F401  los experimentos, por su ranking
import laminas_cierre  # noqa: F401  Ejercicio 4, costo, limitaciones, trabajo futuro, conclusiones

from registro import LAMINAS  # noqa: E402

ORDEN = [
    "portada", "problema", "producto", "rag",
    "rec-mapa", "rec-catalogo", "rec-descripcion", "rec-indice", "rec-plan", "rec-plan-prompt", "rec-busqueda",
    "rec-eleccion", "rec-escena", "rec-imagen", "rec-lista",
    "desafios",
    "gt", "vacios", "met-ret", "met-juez", "met-img", "trampas",
    "hiper", "e1", "e1r", "e2", "e2r", "e3", "e3r", "camino", "e4", "e5", "e5r", "e6", "e6r", "e7", "e7r", "e8",
    "tram1", "tram2",
    "ej4-v1", "ej4-v2", "ej4-res",
    "costo", "limites", "futuro", "conclusiones", "gracias",
]
_por_id = {s["id"]: s for s in LAMINAS}
assert set(ORDEN) == set(_por_id) and len(ORDEN) == len(LAMINAS), (set(ORDEN) ^ set(_por_id))
LAMINAS[:] = [_por_id[i] for i in ORDEN]

# Segundos por lámina: las palabras de sus notas a PPM palabras por minuto (con un piso para las
# láminas que se miran más de lo que se leen). 135 por minuto, el mismo ritmo que usa el guion de
# la presentación principal (las 155 de antes pedían hablar sin pausas). Se ajusta acá después de
# ensayar. "seg_real" es lo que se suma (sin redondear, para que el total no dependa de
# de qué lado de un redondeo cae cada lámina); "seg", lo que se muestra, de a 5 segundos.
PPM = 135
_MIN = {"portada": 25, "gracias": 5, "producto": 30, "conclusiones": 40, "camino": 30, "hiper": 30, "rec-mapa": 35, "rec-lista": 25}
for _s in LAMINAS:
    _n = _s["notas"]
    _s["palabras"] = len((" ".join(_n) if isinstance(_n, list) else _n).split())
    _s["seg_real"] = max(_MIN.get(_s["id"], 20), _s["palabras"] * 60 / PPM)
    _s["seg"] = round(_s["seg_real"] / 5) * 5

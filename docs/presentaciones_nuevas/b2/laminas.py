"""Las láminas, en orden: cada módulo las registra al importarse y acá se ordenan. Cada número sale
de datos.py.

    01 el producto · 02 arquitectura: v0 → v1, el recorrido por las once fases y el mapa de los
    experimentos · 03 los datos para medir · 04 las métricas · los trece experimentos · 05 cierre ·
    06 pasos a futuro
"""

import laminas_intro  # noqa: F401  producto, v0 → v1, mapa de experimentos, datos para medir, métricas
import laminas_recorrido  # noqa: F401  el recorrido por las once fases
import laminas_exp  # noqa: F401  los 13 experimentos
import laminas_cierre  # noqa: F401  cierre, pasos a futuro, conclusiones

from registro import LAMINAS  # noqa: E402

ORDEN = [
    "portada", "problema", "producto", "rag",
    "v0v1", "rec-mapa", "rec-catalogo", "rec-descripcion", "rec-indice", "rec-plan", "rec-plan-prompt", "rec-busqueda",
    "rec-eleccion", "rec-escena", "rec-imagen", "rec-lista", "hiper",
    "gt", "vacios", "met-ret", "met-juez", "met-img",
]
_por_id = {s["id"]: s for s in LAMINAS}
_resto = [s for s in LAMINAS if s["id"] not in ORDEN]
LAMINAS[:] = [_por_id[i] for i in ORDEN] + _resto  # los experimentos y el cierre, en el orden en que se registran

# Segundos por lámina, a unas 155 palabras por minuto de las notas (con un piso para las láminas
# que se miran más de lo que se leen). Se ajustan acá después de ensayar.
_MIN = {"portada": 25, "gracias": 5, "iteracion": 30, "producto": 40, "v0v1": 40, "conclusiones": 40,
        "camino": 30, "e10r1": 25, "hiper": 30, "rec-mapa": 35, "rec-lista": 30}
for _s in LAMINAS:
    _n = _s["notas"]
    _w = len((" ".join(_n) if isinstance(_n, list) else _n).split())
    _s["seg"] = max(_MIN.get(_s["id"], 20), round(_w * 60 / 155 / 5) * 5)

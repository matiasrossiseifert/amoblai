"""Las láminas, en orden: cada módulo las registra al importarse. Cada número sale de datos.py."""

import laminas_intro  # noqa: F401  1-14: producto, datos, arquitectura, métricas
import laminas_exp  # noqa: F401  los 13 experimentos
import laminas_cierre  # noqa: F401  cierre, pasos a futuro, conclusiones

# Segundos por lámina, a unas 155 palabras por minuto de las notas (con un piso para las láminas
# que se miran más de lo que se leen). Se ajustan acá después de ensayar.
from registro import LAMINAS  # noqa: E402

_MIN = {"portada": 25, "gracias": 5, "iteracion": 40, "e2e": 40, "producto": 40, "v0v1": 45, "conclusiones": 45,
        "camino": 35, "e10r1": 25, "flujo": 60, "hiper": 30, "como-leer": 20}
for _s in LAMINAS:
    _n = _s["notas"]
    _w = len((" ".join(_n) if isinstance(_n, list) else _n).split())
    _s["seg"] = max(_MIN.get(_s["id"], 20), round(_w * 60 / 155 / 5) * 5)

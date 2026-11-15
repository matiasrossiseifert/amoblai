"""El registro de láminas (lo comparten build.py y laminas.py)."""

LAMINAS: list[dict] = []


def lam(id_, titulo, seccion, cuerpo, notas, seg, clase="", focos=None):
    """notas: un texto, o una lista con lo que se dice en cada paso (el primero antes de avanzar)."""
    LAMINAS.append(dict(id=id_, titulo=titulo, seccion=seccion, html=cuerpo, notas=notas, seg=seg, clase=clase, focos=focos))

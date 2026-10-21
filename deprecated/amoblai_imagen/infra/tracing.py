"""Trazas opcionales con LangSmith (extra de la consigna: monitoreo y observabilidad).

Se activan con `LANGSMITH_TRACING=true` y `LANGSMITH_API_KEY` en `.env`. No
requieren LangChain: cada etapa del pipeline se decora con `@traced`. Las
imágenes no se suben: se reemplazan por un resumen (tamaño y modo) antes de
enviar la traza.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from typing import Any, TypeVar

import numpy as np
from PIL import Image

F = TypeVar("F", bound=Callable[..., Any])


def summarize(value: Any, depth: int = 0) -> Any:
    """Versión liviana y serializable de un valor para la traza."""
    if depth > 4:
        return "…"
    if isinstance(value, Image.Image):
        return f"<imagen {value.size[0]}x{value.size[1]} {value.mode}>"
    if isinstance(value, np.ndarray):
        return f"<array {value.shape} {value.dtype}>"
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        value = {f.name: getattr(value, f.name) for f in dataclasses.fields(value)}
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if isinstance(value, dict):
        return {str(k): summarize(v, depth + 1) for k, v in list(value.items())[:50]}
    if isinstance(value, list | tuple):
        items = [summarize(v, depth + 1) for v in value[:20]]
        return [*items, f"… (+{len(value) - 20})"] if len(value) > 20 else items
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return repr(value)[:200]


def _process(data: dict[str, Any]) -> dict[str, Any]:
    return {k: summarize(v) for k, v in data.items() if k != "self"}


def traced(name: str, run_type: str = "chain") -> Callable[[F], F]:
    """Decorador de etapa. Sin `langsmith` instalado o sin tracing activo, no hace nada."""
    try:
        from langsmith import traceable
    except ImportError:  # pragma: no cover
        return lambda fn: fn
    return traceable(
        name=name,
        run_type=run_type,
        process_inputs=_process,
        process_outputs=lambda out: {"output": summarize(out)},
    )

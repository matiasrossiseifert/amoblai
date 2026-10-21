"""Carga de pickles del dataset con un unpickler restringido.

`pickle.load` puede ejecutar código arbitrario. Los pickles del dataset solo
contienen diccionarios, listas y strings, así que se permiten únicamente esos
tipos builtin y cualquier otra clase hace fallar la carga.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

_BUILTINS = ("dict", "list", "set", "frozenset", "tuple", "str", "bytes", "int", "float", "bool")
_ALLOWED = (
    {("builtins", n) for n in _BUILTINS}
    | {("__builtin__", n) for n in (*_BUILTINS, "unicode", "long")}
    | {("collections", "OrderedDict"), ("collections", "defaultdict")}
)


class _RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str) -> Any:
        if (module, name) in _ALLOWED:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"Clase no permitida en el pickle: {module}.{name}")


def load_pickle(path: Path, encoding: str = "latin1") -> Any:
    """Carga un pickle (Python 2) con `encoding="latin1"`, como indica el dataset."""
    with Path(path).open("rb") as fh:
        return _RestrictedUnpickler(fh, encoding=encoding).load()

"""Post-retrieval: reranking de candidatos.

En la v1 el reranking está desactivado y el elegido es el top-1 del retriever.
La interfaz queda definida para la iteración del Ejercicio 4: un VLM que recibe
el recorte, las fotos de los top-k candidatos y el prompt del usuario, y devuelve
el SKU más adecuado (ver FUTURO.md).
"""

from __future__ import annotations

from typing import Protocol

from amoblai.retrieval.retriever import RetrievalResult
from amoblai.vision.crops import QueryCrop


class Reranker(Protocol):
    def rerank(
        self, crop: QueryCrop, result: RetrievalResult, user_prompt: str
    ) -> RetrievalResult: ...


class NoopReranker:
    """Deja el orden del retriever: el elegido es el top-1 si superó el umbral."""

    def rerank(self, crop: QueryCrop, result: RetrievalResult, user_prompt: str) -> RetrievalResult:
        return result

"""Text -> vector, for the descriptions and the queries.

- ``hashing`` (free): each word goes to one of `dim` slots by its hash, so two texts are near
  only when they share words. A baseline, and the tests' embedder.
- ``openai_embeddings``: ``POST /v1/embeddings`` with text-embedding-3-large or -small
  (developers.openai.com/api/docs/pricing.md, checked 2026-10-19). The same request goes to
  any OpenAI-compatible endpoint: fal's OpenRouter router serves OpenAI's models with the fal
  key (``Authorization: Key ...``, fal.ai/models/openrouter/router/openai/v1/embeddings,
  checked 2026-10-19), billed to fal.
- ``local`` (free): an open text-embedding model run here, on the CPU, with Hugging Face
  transformers (torch + transformers installed). Nothing leaves the machine.

Vectors come back as float32 rows of length 1, so a dot product is the cosine.
"""

from __future__ import annotations

import hashlib
import re
import threading
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Protocol

import httpx
import numpy as np

from amoblai.config import Config
from amoblai.infra.http import (
    ProviderError,
    check_response,
    client_scope,
    env_key,
    lookup_model,
    request_with_retries,
)

# importar transformers y cargar un modelo desde varios hilos a la vez falla (import parcial)
_LOAD_LOCK = threading.Lock()


@dataclass
class Embedding:
    vectors: np.ndarray  # (n, d) float32, rows of length 1
    model: str
    cost_usd: float
    cost_source: str  # "api" | "estimate" | "none"
    meta: dict = field(default_factory=dict)


class Embedder(Protocol):
    name: str
    paid: bool
    account: str | None  # the API account it spends from (budget.accounts); None when free

    def key(self) -> dict:
        """Everything besides the text that changes the vector."""
        ...

    def estimate_cost(self, texts: list[str]) -> float: ...

    def embed(self, texts: list[str]) -> Embedding: ...


def unit_rows(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=1, keepdims=True)
    return (v / np.maximum(n, 1e-12)).astype(np.float32)


STOPWORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "as",
        "at",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
        "de",
        "del",
        "el",
        "en",
        "la",
        "las",
        "los",
        "para",
        "por",
        "un",
        "una",
        "y",
        "con",
    ]
)


def words(text: str) -> list[str]:
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return [w for w in re.findall(r"[a-z0-9]+", t) if len(w) > 1 and w not in STOPWORDS]


class HashingEmbedder:
    paid = False
    account = None

    def __init__(self, params: dict, name: str = "hashing"):
        self.name = name
        self.dim = int(params.get("dim", 1024))

    def key(self) -> dict:
        return {"kind": "hashing", "dim": self.dim, "version": 1}

    def estimate_cost(self, texts: list[str]) -> float:
        return 0.0

    def embed(self, texts: list[str]) -> Embedding:
        v = np.zeros((len(texts), self.dim), np.float32)
        for i, t in enumerate(texts):
            for w in words(t):
                h = int.from_bytes(hashlib.blake2b(w.encode(), digest_size=8).digest(), "little")
                v[i, h % self.dim] += 1.0 if h >> 63 else -1.0
        return Embedding(unit_rows(v), f"hashing-{self.dim}", 0.0, "none")


class OpenAIEmbedder:
    paid = True
    BATCH = 256  # texts per request (the API takes up to 2048)

    def __init__(self, params: dict, name: str = "openai", client: httpx.Client | None = None):
        p = dict(params)
        if "model" not in p or "models" not in p:
            raise ValueError(f"{name}: embedder config needs `model` and a `models` table")
        self.name = name
        self.model = str(p["model"])
        self.rules = lookup_model(p["models"], self.model, name)
        self.dimensions = p.get("dimensions")  # None = the model's full size
        self.base_url = str(p.get("base_url", "https://api.openai.com/v1")).rstrip("/")
        self.timeout_s = float(p.get("timeout_s", 60))
        self.max_retries = int(p.get("max_retries", 2))
        self.backoff_s = float(p.get("backoff_s", 2.0))
        self.api_key_env = list(p.get("api_key_env", ["OPENAI_API_KEY"]))
        self.auth = str(p.get("auth", "bearer"))  # bearer: OpenAI; key: fal
        self.account = str(p.get("account", "openai"))
        self._client = client

    def key(self) -> dict:
        return {"kind": "openai_embeddings", "model": self.model, "dimensions": self.dimensions}

    def _auth_header(self, key: str) -> str:
        return f"Key {key}" if self.auth == "key" else f"Bearer {key}"

    def estimate_cost(self, texts: list[str]) -> float:
        tokens = sum(len(t) for t in texts) / 3  # generous: English runs ~4 characters a token
        return tokens * float(self.rules["usd_per_m"]) / 1e6

    def embed(self, texts: list[str]) -> Embedding:
        key = env_key(self.api_key_env, self.name)
        rows, tokens, billed, t0 = [], 0, None, time.perf_counter()
        with client_scope(self._client, self.timeout_s) as client:
            for s in range(0, len(texts), self.BATCH):
                body: dict = {"model": self.model, "input": texts[s : s + self.BATCH]}
                if self.dimensions:
                    body["dimensions"] = int(self.dimensions)
                resp = request_with_retries(
                    client,
                    "POST",
                    f"{self.base_url}/embeddings",
                    max_retries=self.max_retries,
                    backoff_s=self.backoff_s,
                    idempotent=False,
                    headers={"Authorization": self._auth_header(key)},
                    json=body,
                )
                check_response(resp, self.name)
                out = resp.json()
                usage = out.get("usage") or {}
                if usage.get("cost") is not None:  # what the router billed, in US$
                    billed = (billed or 0.0) + float(usage["cost"])
                data = sorted(out.get("data") or [], key=lambda d: d["index"])
                if len(data) != len(body["input"]):
                    raise ProviderError(
                        f"{self.name}: {len(data)} vectors for {len(body['input'])} texts"
                    )
                rows += [d["embedding"] for d in data]
                tokens += int(usage.get("total_tokens", 0))
        if billed is not None:
            cost, source = billed, "api"
        elif tokens:
            cost, source = tokens * float(self.rules["usd_per_m"]) / 1e6, "api_tokens"
        else:  # no usage in the reply
            cost, source = self.estimate_cost(texts), "estimate"
        meta = {"tokens": tokens, "latency_s": round(time.perf_counter() - t0, 2)}
        vectors = unit_rows(np.array(rows, np.float32))
        return Embedding(vectors, self.model, round(cost, 8), source, meta)


class LocalEmbedder:
    """`pooling`: how a text's token vectors become one: ``cls`` (the first token, BGE), ``mean``
    (E5, GTE) or ``last`` (the last token, Qwen3-Embedding). Queries and descriptions go in
    the same way: our query is written like a description, so no query instruction."""

    paid = False
    account = None

    def __init__(self, params: dict, name: str = "local"):
        self.name = name
        self.model_id = str(params["model"])
        self.revision = params.get("revision")
        self.pooling = str(params.get("pooling", "cls"))
        self.max_length = int(params.get("max_length", 512))
        self.batch = int(params.get("batch", 16))
        self._loaded = None

    def key(self) -> dict:
        return {
            "kind": "local",
            "model": self.model_id,
            "revision": self.revision,
            "pooling": self.pooling,
            "max_length": self.max_length,
        }

    def estimate_cost(self, texts: list[str]) -> float:
        return 0.0

    def _load(self):
        with _LOAD_LOCK:
            return self._load_locked()

    def _load_locked(self):
        if self._loaded is None:
            from transformers import AutoModel, AutoTokenizer

            side = "left" if self.pooling == "last" else "right"
            tok = AutoTokenizer.from_pretrained(
                self.model_id, revision=self.revision, padding_side=side
            )
            model = AutoModel.from_pretrained(self.model_id, revision=self.revision).eval()
            self._loaded = tok, model
        return self._loaded

    def embed(self, texts: list[str]) -> Embedding:
        import torch

        tok, model = self._load()
        t0 = time.perf_counter()
        rows = []
        with torch.inference_mode():
            for i in range(0, len(texts), self.batch):
                enc = tok(
                    texts[i : i + self.batch],
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt",
                )
                h = model(**enc).last_hidden_state
                if self.pooling == "cls":
                    v = h[:, 0]
                elif self.pooling == "last":  # left padding: the last position is the last token
                    v = h[:, -1]
                else:
                    m = enc["attention_mask"].unsqueeze(-1).to(h.dtype)
                    v = (h * m).sum(1) / m.sum(1).clamp(min=1)
                rows.append(v.float().numpy())
        meta = {"latency_s": round(time.perf_counter() - t0, 2)}
        return Embedding(unit_rows(np.concatenate(rows)), self.model_id, 0.0, "none", meta)


_LOCAL: dict[str, LocalEmbedder] = {}  # one model in memory per setup, not one per search


def get_embedder(name: str, cfg: Config) -> Embedder:
    params = dict(cfg.rag.embedders.get(name, {}))
    if not params:
        raise ValueError(
            f"rag: no embedder {name!r} in rag.embedders (datos/configs/amoblai.yaml); "
            f"known: {sorted(cfg.rag.embedders)}"
        )
    kind = params.pop("kind", name)
    if kind == "hashing":
        return HashingEmbedder(params, name)
    if kind == "openai_embeddings":
        return OpenAIEmbedder(params, name)
    if kind == "local":
        key = repr((name, sorted(params.items())))
        if key not in _LOCAL:
            _LOCAL[key] = LocalEmbedder(params, name)
        return _LOCAL[key]
    raise ValueError(f"rag: embedder {name!r} has an unknown kind {kind!r}")

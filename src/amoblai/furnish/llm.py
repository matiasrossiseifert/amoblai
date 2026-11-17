"""The LLM that looks at photos and writes: images and text in, text out.

Content is a list of blocks, `text_block(...)` and `image_block(path)`, the same for every kind:

- ``anthropic``: Claude, ``POST /v1/messages`` with ``x-api-key`` and ``anthropic-version``;
  ``output_config.effort``; thinking is billed as output; ``stop_reason`` "end_turn" is a full
  answer (platform.claude.com/docs, checked 2026-10-19).
- ``openai_chat``: any OpenAI-compatible Chat Completions API (OpenAI, and the compatible
  endpoints of Gemini, OpenRouter and others: set ``base_url`` and ``api_key_env``),
  ``POST {base_url}/chat/completions``; ``finish_reason`` "stop" is a full answer.

Models and prices live in the config (`models`: {model: {usd_per_m: {input, output},
estimate_usd}}); the cost of a call comes from the reply's token counts.

A text block can be marked as a cache breakpoint (`text_block(text, cache="5m" | "1h")`, Claude
only): everything up to it is stored for that long and read back at a fraction of the price by
the next calls that start with the same bytes. Its prices go in `usd_per_m` too (`cache_read`,
`cache_write_5m`, `cache_write_1h`).
"""

from __future__ import annotations

import base64
import io
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import httpx
from PIL import Image, ImageOps

from amoblai.infra.http import (
    ProviderError,
    check_response,
    client_scope,
    env_key,
    lookup_model,
    request_with_retries,
)

DONE = (
    "end_turn",
    "stop_sequence",
)  # Claude; anything else ("max_tokens", "refusal"...): cut short


@dataclass
class Answer:
    text: str
    model: str
    cost_usd: float
    cost_source: str  # "api" | "estimate"
    meta: dict = field(default_factory=dict)  # status, stop_reason, usage, latency_s

    @property
    def complete(self) -> bool:
        return self.meta.get("status") == "completed"


class LLM(Protocol):
    name: str
    model: str
    paid: bool
    account: str | None  # the API account it spends from (budget.accounts)

    def key(self) -> dict:
        """Everything besides the content that changes the answer."""
        ...

    def estimate_cost(self) -> float: ...

    def ask(self, content: list[dict]) -> Answer: ...


def jpeg_b64(path: Path, max_side: int) -> str:
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()


def image_block(path: Path, max_side: int = 1024) -> dict:
    data = jpeg_b64(path, max_side)
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}}


def text_block(text: str, cache: str | None = None) -> dict:
    """`cache` ("5m" or "1h"): the prompt up to the end of this block is cached for that long
    (Claude's prompt caching; other kinds ignore it)."""
    block: dict = {"type": "text", "text": text}
    if cache:
        block["cache_control"] = {"type": "ephemeral", **({"ttl": "1h"} if cache == "1h" else {})}
    return block


def parse_json(text: str) -> dict:
    """The JSON object in an answer: the first one, with or without a ```json fence around it
    and whatever the model wrote before or after (a note, a second block). If the first one is
    broken and the model wrote it again (a "correction"), the next one that starts a line."""
    starts = [text.find("{")]
    starts += [i + 1 for i in range(starts[0], len(text) - 1) if text[i : i + 2] == "\n{"]
    err: json.JSONDecodeError | None = None
    for start in starts:
        try:
            if start < 0:
                raise json.JSONDecodeError("no JSON object", text, 0)
            data, _ = json.JSONDecoder().raw_decode(text[start:])
            break
        except json.JSONDecodeError as e:
            err = err or e
    else:
        raise ProviderError(f"the answer is not the JSON asked for: {err}: {text[:300]!r}") from err
    if not isinstance(data, dict):
        raise ProviderError(f"the answer is not a JSON object: {text[:300]!r}")
    return data


def _token_cost(rules: dict, tokens_in: int, tokens_out: int) -> float:
    prices = rules["usd_per_m"]
    return (tokens_in * float(prices["input"]) + tokens_out * float(prices["output"])) / 1e6


def claude_cost(rules: dict, usage: dict) -> float:
    """The cost of one Claude answer from its `usage`. Input read from the cache or written to
    it has its own price (`cache_read`, `cache_write_5m`, `cache_write_1h` in `usd_per_m`);
    a model without those prices counts it as plain input, which overstates a cached call."""
    prices = rules["usd_per_m"]
    plain = float(prices["input"])
    written = usage.get("cache_creation_input_tokens") or 0
    for_1h = (usage.get("cache_creation") or {}).get("ephemeral_1h_input_tokens") or 0
    return (
        (usage.get("input_tokens") or 0) * plain
        + (written - for_1h) * float(prices.get("cache_write_5m", plain))
        + for_1h * float(prices.get("cache_write_1h", plain))
        + (usage.get("cache_read_input_tokens") or 0) * float(prices.get("cache_read", plain))
        + (usage.get("output_tokens") or 0) * float(prices["output"])
    ) / 1e6


class _Http:
    """What both kinds share: the model and its prices, the key, timeouts and retries."""

    paid = True

    def __init__(self, params: dict, name: str, client: httpx.Client | None, defaults: dict):
        p = {**defaults, **params}
        if "model" not in p or "models" not in p:
            raise ValueError(f"{name}: needs `model` and a `models` table")
        self.name = name
        self.model = str(p["model"])
        self.rules = lookup_model(p["models"], self.model, name)
        self.max_tokens = int(p.get("max_tokens", 4000))
        self.base_url = str(p["base_url"]).rstrip("/")
        self.timeout_s = float(p.get("timeout_s", 120))
        self.max_retries = int(p.get("max_retries", 2))
        self.backoff_s = float(p.get("backoff_s", 2.0))
        self.api_key_env = list(p["api_key_env"])
        self.account = p.get("account")
        self.params = p
        self._client = client

    def estimate_cost(self) -> float:
        return float(self.rules["estimate_usd"])

    def _post(self, path: str, headers: dict, body: dict) -> dict:
        with client_scope(self._client, self.timeout_s) as client:
            resp = request_with_retries(
                client,
                "POST",
                f"{self.base_url}/{path}",
                max_retries=self.max_retries,
                backoff_s=self.backoff_s,
                idempotent=False,
                headers=headers,
                json=body,
            )
            check_response(resp, self.name)
            return resp.json()


class Claude(_Http):
    def __init__(self, params: dict, name: str = "claude", client: httpx.Client | None = None):
        defaults = {
            "base_url": "https://api.anthropic.com/v1",
            "account": "anthropic",
            "api_key_env": ["ANTHROPIC_API_KEY"],
        }
        super().__init__(params, name, client, defaults)
        self.effort = self.params.get("effort")
        self.version = str(self.params.get("anthropic_version", "2023-06-01"))

    def key(self) -> dict:
        return {"model": self.model, "effort": self.effort}

    def body(self, content: list[dict]) -> dict:
        body: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": content}],
        }
        if self.effort:
            body["output_config"] = {"effort": self.effort}
        return body

    def ask(self, content: list[dict]) -> Answer:
        key = env_key(self.api_key_env, self.name)
        t0 = time.perf_counter()
        out = self._post(
            "messages", {"x-api-key": key, "anthropic-version": self.version}, self.body(content)
        )
        usage = out.get("usage") or {}
        if usage:
            cost, source = claude_cost(self.rules, usage), "api"
        else:
            cost, source = self.estimate_cost(), "estimate"
        stop = out.get("stop_reason")
        text = "".join(
            c.get("text", "") for c in out.get("content") or [] if c.get("type") == "text"
        )
        meta = {
            "status": "completed" if stop in DONE else str(stop),
            "stop_reason": stop,
            "usage": usage,
            "images": sum(1 for c in content if c.get("type") == "image"),
            "latency_s": round(time.perf_counter() - t0, 2),
        }
        return Answer(text.strip(), out.get("model", self.model), round(cost, 6), source, meta)


class OpenAIChat(_Http):
    def __init__(self, params: dict, name: str = "openai_chat", client: httpx.Client | None = None):
        defaults = {
            "base_url": "https://api.openai.com/v1",
            "account": "openai",
            "api_key_env": ["OPENAI_API_KEY"],
        }
        super().__init__(params, name, client, defaults)
        self.reasoning_effort = self.params.get("reasoning_effort")

    def key(self) -> dict:
        return {"model": self.model, "reasoning_effort": self.reasoning_effort}

    @staticmethod
    def part(block: dict) -> dict:
        if block["type"] == "image":
            src = block["source"]
            url = f"data:{src['media_type']};base64,{src['data']}"
            return {"type": "image_url", "image_url": {"url": url}}
        return {"type": "text", "text": block["text"]}

    def body(self, content: list[dict]) -> dict:
        body: dict = {
            "model": self.model,
            "max_completion_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": [self.part(b) for b in content]}],
        }
        if self.reasoning_effort:
            body["reasoning_effort"] = self.reasoning_effort
        return body

    def ask(self, content: list[dict]) -> Answer:
        key = env_key(self.api_key_env, self.name)
        t0 = time.perf_counter()
        out = self._post("chat/completions", {"Authorization": f"Bearer {key}"}, self.body(content))
        usage = out.get("usage") or {}
        if usage:
            tokens = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
            cost, source = _token_cost(self.rules, *tokens), "api"
        else:
            cost, source = self.estimate_cost(), "estimate"
        choice = (out.get("choices") or [{}])[0]
        stop = choice.get("finish_reason")
        meta = {
            "status": "completed" if stop == "stop" else str(stop),
            "stop_reason": stop,
            "usage": usage,
            "images": sum(1 for c in content if c.get("type") == "image"),
            "latency_s": round(time.perf_counter() - t0, 2),
        }
        text = (choice.get("message") or {}).get("content") or ""
        return Answer(text.strip(), out.get("model", self.model), round(cost, 6), source, meta)


KINDS = {"anthropic": Claude, "openai_chat": OpenAIChat}


def make_llm(params: dict, name: str = "llm", client: httpx.Client | None = None) -> LLM:
    p = dict(params)
    kind = p.pop("kind", "anthropic")
    if kind not in KINDS:
        raise ValueError(f"{name}: unknown LLM kind {kind!r}; known: {sorted(KINDS)}")
    return KINDS[kind](p, name, client)

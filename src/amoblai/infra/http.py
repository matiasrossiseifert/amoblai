"""Helpers shared by every paid HTTP API: the LLMs, the describers, the embedders and the image
generators.

Everything goes through plain httpx so tests can swap the network for an ``httpx.MockTransport``:
either pass ``client=`` to a provider, or set ``TRANSPORT`` (tests only) so that providers built
deep inside the pipeline use it too.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from email.utils import parsedate_to_datetime

import httpx

# Test hook: when set, clients created by providers use this transport instead of the network.
TRANSPORT: httpx.BaseTransport | None = None

RETRY_STATUS = frozenset({429, 500, 502, 503, 504})


class ProviderError(RuntimeError):
    pass


class ProviderUnavailable(ProviderError):
    """Missing API key / SDK; the batch runner skips such providers."""


@contextmanager
def client_scope(client: httpx.Client | None, timeout_s: float) -> Iterator[httpx.Client]:
    """Use the injected client as is, or create (and close) one for the duration of a call."""
    if client is not None:
        yield client
        return
    timeout = httpx.Timeout(timeout_s, connect=min(30.0, timeout_s))
    with httpx.Client(timeout=timeout, transport=TRANSPORT, follow_redirects=True) as c:
        yield c


def env_key(names: list[str] | tuple[str, ...], provider: str) -> str:
    """First non-empty environment variable of `names`, else ProviderUnavailable."""
    for n in names:
        v = os.environ.get(n, "").strip()
        if v:
            return v
    raise ProviderUnavailable(
        f"{provider}: no API key; set {' or '.join(names)} in the environment or .env"
    )


def _retry_after(resp: httpx.Response, cap_s: float) -> float | None:
    raw = resp.headers.get("retry-after")
    if not raw:
        return None
    try:
        return min(cap_s, max(0.0, float(raw)))
    except ValueError:
        pass
    try:
        return min(cap_s, max(0.0, parsedate_to_datetime(raw).timestamp() - time.time()))
    except (TypeError, ValueError):
        return None


def request_with_retries(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    max_retries: int,
    backoff_s: float,
    idempotent: bool,
    max_backoff_s: float = 60.0,
    sleep: Callable[[float], None] = time.sleep,
    **kwargs,
) -> httpx.Response:
    """Send a request, retrying 429/5xx (and connection failures) with exponential backoff.

    `max_retries` is the number of retries after the first attempt. Read timeouts are retried only
    for idempotent requests: a POST that timed out may still be running (and billed) upstream.
    The Retry-After header, when present, overrides the computed delay (capped).
    """
    attempt = 0
    while True:
        delay = min(max_backoff_s, backoff_s * (2**attempt))
        try:
            resp = client.request(method, url, **kwargs)
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            if attempt >= max_retries:
                raise ProviderError(f"{method} {url}: {e!r}") from e
        except httpx.TransportError as e:
            if not idempotent or attempt >= max_retries:
                raise ProviderError(f"{method} {url}: {e!r}") from e
        else:
            if resp.status_code not in RETRY_STATUS or attempt >= max_retries:
                return resp
            ra = _retry_after(resp, max_backoff_s)
            delay = delay if ra is None else ra
        sleep(delay)
        attempt += 1


def check_response(resp: httpx.Response, provider: str) -> None:
    """Raise a ProviderError (or ProviderUnavailable for auth problems) on HTTP errors."""
    if resp.status_code < 400:
        return
    try:
        body: object = resp.json()
    except ValueError:
        body = resp.text[:500]
    detail = body
    if isinstance(body, dict):
        # OpenAI: {"error": {message, type, code}}; Google: {"error": {code, message, status}};
        # fal: {"detail": ...}.
        err = body.get("error")
        if isinstance(err, dict):
            detail = {k: err[k] for k in ("type", "code", "status", "message") if err.get(k)}
        elif err is not None:
            detail = err
        elif "detail" in body:
            detail = body["detail"]
    msg = f"{provider}: HTTP {resp.status_code} from {resp.request.url}: {detail}"
    if resp.status_code in (401, 403):
        # Invalid key, or e.g. OpenAI organization not verified for GPT Image models.
        raise ProviderUnavailable(msg)
    raise ProviderError(msg)


def lookup_model(models: dict, model: str, provider: str) -> dict:
    """Rules/prices for `model` from a config table keyed by model id.

    An exact key wins; otherwise the longest key that is a dash-prefix of the id, so dated
    snapshots (``gpt-image-2.5-sunburst-2026-09-08``) inherit their family's entry.
    """
    if model in models:
        return dict(models[model])
    keys = sorted((k for k in models if model.startswith(k + "-")), key=len, reverse=True)
    if not keys:
        raise ValueError(
            f"{provider}: model {model!r} has no entry in the provider's `models` table "
            f"(configs/base/providers.yaml); known: {sorted(models)}"
        )
    return dict(models[keys[0]])

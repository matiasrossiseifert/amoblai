"""Modelos de imagen por API para el paso `generate` de roomrag (interfaz de roomrag/generate.py).

Reciben la foto del ambiente (primera) y las fotos de los productos elegidos, en ese orden, y el
prompt que escribió el paso `scene`; devuelven `final.png` en la carpeta de la corrida.

- `FalNanoBanana`: Nano Banana 2 (Gemini 3.1 Flash Image de Google) por la API de colas de fal.
  Documentación: fal.ai/models/fal-ai/nano-banana-2/edit/llms.txt; precio: US$0,08 la imagen 1K,
  x1,5 en 2K y x2 en 4K (consultado por YouSeeYouBuy el 2026-10-20). Con `aspect_ratio: auto`
  dibuja en la proporción de la foto. fal no devuelve el costo: se usa el precio configurado.
- `OpenAIImage`: gpt-image por `images.edit` (varias imágenes de entrada). El costo sale de los
  tokens de `usage` y los precios configurados.

Se configuran en `furnish.generators` con `kind: "amoblai.generacion:<Clase>"`. Las dos son
pagas: roomrag las frena salvo `budget.allow_paid` y descuenta del tope de su cuenta.
"""

from __future__ import annotations

import base64
import io
import time
from pathlib import Path

import httpx
from PIL import Image, ImageOps
from roomrag.generate import Generated
from roomrag.http import ProviderError, check_response, client_scope, env_key, request_with_retries


def data_uri(path: Path, max_side: int, fmt: str = "PNG") -> str:
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format=fmt, **({"quality": 95} if fmt == "JPEG" else {}))
    mime = "image/png" if fmt == "PNG" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(buf.getvalue()).decode()}"


class FalNanoBanana:
    paid = True
    account = "fal"

    def __init__(
        self, params: dict, cfg, name: str = "nano_banana_2", client: httpx.Client | None = None
    ):
        p = dict(params)
        self.name = name
        self.endpoint = str(p.get("endpoint", "fal-ai/nano-banana-2/edit"))
        self.resolution = str(p.get("resolution", "1K"))
        self.aspect_ratio = str(p.get("aspect_ratio", "auto"))
        self.prices = {
            str(k): float(v) for k, v in (p.get("usd_per_image") or {"1K": 0.08}).items()
        }
        if self.resolution not in self.prices:
            raise ValueError(f"{name}: no hay precio para la resolución {self.resolution!r}")
        self.room_max_side = int(p.get("room_max_side", 1536))
        self.ref_max_side = int(p.get("ref_max_side", 1024))
        self.queue_url = str(p.get("queue_url", "https://queue.fal.run")).rstrip("/")
        self.timeout_s = float(p.get("timeout_s", 600))
        self.poll_s = float(p.get("poll_s", 1.5))
        self.max_retries = int(p.get("max_retries", 3))
        self.api_key_env = list(p.get("api_key_env", ["FAL_KEY"]))
        self._client = client
        self._sleep = time.sleep

    def estimate_cost(self, images: list[Path]) -> float:
        return self.prices[self.resolution]

    def payload(self, prompt: str, images: list[Path]) -> dict:
        uris = [data_uri(images[0], self.room_max_side, "PNG")]
        uris += [data_uri(p, self.ref_max_side, "JPEG") for p in images[1:]]
        return {
            "prompt": prompt,
            "image_urls": uris,
            "num_images": 1,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "output_format": "png",
        }

    def _call(self, client: httpx.Client, method: str, url: str, **kw) -> httpx.Response:
        resp = request_with_retries(
            client, method, url, max_retries=self.max_retries, backoff_s=2.0,
            idempotent=method != "POST", sleep=self._sleep, **kw,
        )  # fmt: skip
        check_response(resp, self.name)
        return resp

    def generate(self, prompt: str, images: list[Path], out: Path) -> Generated:
        key = env_key(self.api_key_env, self.name)
        auth = {"Authorization": f"Key {key}"}
        t0 = time.perf_counter()
        with client_scope(self._client, 120.0) as client:
            sub = self._call(client, "POST", f"{self.queue_url}/{self.endpoint}", headers=auth,
                             json=self.payload(prompt, images)).json()  # fmt: skip
            rid = sub.get("request_id")
            base = f"{self.queue_url}/{self.endpoint}/requests/{rid}"
            status_url = sub.get("status_url") or f"{base}/status"
            response_url = sub.get("response_url") or base
            deadline = time.monotonic() + self.timeout_s
            while True:
                st = self._call(client, "GET", status_url, headers=auth).json()
                if st.get("status") == "COMPLETED":
                    if st.get("error"):
                        raise ProviderError(
                            f"{self.name}: el pedido {rid} falló: {st.get('error')}"
                        )
                    break
                if time.monotonic() > deadline:
                    raise ProviderError(f"{self.name}: el pedido {rid} no terminó a tiempo")
                self._sleep(self.poll_s)
            result = self._call(client, "GET", response_url, headers=auth).json()
            imgs = result.get("images") or []
            if not imgs or not imgs[0].get("url"):
                raise ProviderError(f"{self.name}: la respuesta no trae images[0].url")
            url = imgs[0]["url"]
            # La imagen está en el CDN público de fal: se baja sin la clave.
            data = (base64.b64decode(url.split(",", 1)[1]) if url.startswith("data:")
                    else self._call(client, "GET", url).content)  # fmt: skip
        dst = Path(out) / "final.png"
        Image.open(io.BytesIO(data)).convert("RGB").save(dst)
        meta = {
            "endpoint": self.endpoint,
            "request_id": rid,
            "resolution": self.resolution,
            "aspect_ratio": self.aspect_ratio,
            "images_in": len(images),
            "description": result.get("description"),
            "latency_s": round(time.perf_counter() - t0, 2),
            "cost_note": "precio configurado: fal no devuelve el costo",
        }
        return Generated(dst, self.endpoint, self.estimate_cost(images), "estimate", meta)


class OpenAIImage:
    paid = True
    account = "openai"

    def __init__(self, params: dict, cfg, name: str = "openai"):
        p = dict(params)
        self.name = name
        self.model = str(p.get("model", "gpt-image-2"))
        self.quality = str(p.get("quality", "medium"))
        self.size = str(p.get("size", "auto"))
        self.prices = p.get("usd_per_m") or {
            "text_input": 5.0,
            "image_input": 8.0,
            "image_output": 30.0,
        }
        self.estimate_usd = float(p.get("estimate_usd", 0.12))
        self.ref_max_side = int(p.get("ref_max_side", 1024))
        self.api_key_env = list(p.get("api_key_env", ["OPENAI_API_KEY"]))

    def estimate_cost(self, images: list[Path]) -> float:
        return self.estimate_usd

    def generate(self, prompt: str, images: list[Path], out: Path) -> Generated:
        from openai import OpenAI

        client = OpenAI(api_key=env_key(self.api_key_env, self.name), timeout=300, max_retries=1)
        files = []
        for i, p in enumerate(images):
            im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
            im.thumbnail((1536 if i == 0 else self.ref_max_side,) * 2, Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            files.append((f"image_{i + 1}.png", buf.getvalue(), "image/png"))
        t0 = time.perf_counter()
        resp = client.images.edit(
            model=self.model, image=files, prompt=prompt, size=self.size,
            quality=self.quality, output_format="png", n=1,
        )  # fmt: skip
        dst = Path(out) / "final.png"
        Image.open(io.BytesIO(base64.b64decode(resp.data[0].b64_json))).convert("RGB").save(dst)
        cost, source = self.estimate_usd, "estimate"
        u = resp.usage
        if u is not None:
            d_in = getattr(u, "input_tokens_details", None)
            text_in = int(getattr(d_in, "text_tokens", 0) or 0)
            image_in = int(getattr(d_in, "image_tokens", 0) or 0)
            cost = (
                text_in * self.prices["text_input"]
                + image_in * self.prices["image_input"]
                + int(u.output_tokens or 0) * self.prices["image_output"]
            ) / 1e6
            source = "api_tokens"
        meta = {"latency_s": round(time.perf_counter() - t0, 2), "quality": self.quality}
        return Generated(dst, self.model, round(cost, 6), source, meta)

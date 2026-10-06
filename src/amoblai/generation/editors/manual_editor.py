"""Editor manual: para experimentar barato con las suscripciones de ChatGPT o Gemini.

El pipeline prepara una carpeta de trabajo con las imágenes de entrada, el
prompt e instrucciones, y se pausa. Una persona genera la imagen a mano en la
web de ChatGPT o Gemini, la guarda en la carpeta como `resultado.png` (o .jpg /
.webp), completa `meta.yaml` con la app usada y el pipeline continúa.

Nunca se automatizan las interfaces web de chat: sus términos de uso lo prohíben.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

from amoblai.config import EditorConfig
from amoblai.generation.base import EditRequest, EditResult, ManualStepPendingError
from amoblai.infra.images import load_image, save_image
from amoblai.infra.usage import UsageRecord

log = logging.getLogger(__name__)

RESULT_NAMES = ("resultado.png", "resultado.jpg", "resultado.jpeg", "resultado.webp")
APPS = {
    "chatgpt": "https://chatgpt.com",
    "gemini": "https://gemini.google.com",
}

INSTRUCTIONS = """\
# Paso manual: {stage}

1. Abrí {app_url} ({app}) en el navegador.
2. Subí, en este orden, las imágenes de esta carpeta:
{image_list}
3. Pegá el contenido de `prompt.txt` y generá la imagen.{mask_note}
4. Descargá el resultado y guardalo en esta carpeta como **`resultado.png`**
   (también sirve .jpg o .webp).
5. Completá `meta.yaml`: qué app usaste (`chatgpt` o `gemini`), el modelo si se
   ve en la interfaz y cualquier nota (por ejemplo, si hubo que reintentar).

El pipeline detecta el archivo y sigue solo (o volvé a correr el mismo comando:
todo lo anterior está en caché).
"""

MASK_NOTE = """
   La zona a modificar está marcada en rojo en `zona_a_editar.png` (solo como
   referencia: si la app permite seleccionar una región, seleccioná esa)."""


def find_result(workdir: Path) -> Path | None:
    for name in RESULT_NAMES:
        if (workdir / name).exists():
            return workdir / name
    return None


def fit_to_aspect(img: Image.Image, size: tuple[int, int]) -> tuple[Image.Image, bool]:
    """Recorte centrado al aspecto de `size` y escala. Indica si hubo que recortar."""
    w, h = img.size
    target_ratio = size[0] / size[1]
    ratio = w / h
    adjusted = abs(np.log(ratio / target_ratio)) > 0.02
    if adjusted:
        if ratio > target_ratio:
            nw = round(h * target_ratio)
            img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
        else:
            nh = round(w / target_ratio)
            img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return img.resize(size, Image.Resampling.LANCZOS), adjusted


class ManualImageEditor:
    provider = "manual"

    def __init__(self, cfg: EditorConfig, root: Path, poll_s: float = 2.0):
        self.cfg = cfg
        self.model = f"manual:{cfg.manual_app}"
        self.root = Path(root)
        self.poll_s = poll_s

    def estimate_usd(self, request: EditRequest) -> float:
        return 0.0  # se paga con la suscripción de la app, no por llamada

    def workdir(self, request: EditRequest) -> Path:
        return self.root / request.cache_key

    def prepare(self, request: EditRequest) -> tuple[Path, str]:
        workdir = self.workdir(request)
        workdir.mkdir(parents=True, exist_ok=True)
        names = []
        for i, (img, label) in enumerate(
            zip(request.images, request.image_labels, strict=True), start=1
        ):
            name = f"entrada_{i}_{label}.png"
            save_image(img, workdir / name)
            names.append(name)
        if request.mask is not None:
            overlay = np.asarray(request.base.convert("RGB")).copy()
            red = np.array([230, 30, 30], dtype=np.uint8)
            overlay[request.mask] = (0.55 * overlay[request.mask] + 0.45 * red).astype(np.uint8)
            save_image(Image.fromarray(overlay), workdir / "zona_a_editar.png")
        (workdir / "prompt.txt").write_text(request.prompt)
        app = self.cfg.manual_app
        instructions = INSTRUCTIONS.format(
            stage=request.stage,
            app=app,
            app_url=APPS.get(app, app),
            image_list="\n".join(f"   {i}. `{n}`" for i, n in enumerate(names, start=1)),
            mask_note=MASK_NOTE if request.mask is not None else "",
        )
        (workdir / "INSTRUCCIONES.md").write_text(instructions)
        meta_path = workdir / "meta.yaml"
        if not meta_path.exists():
            meta_path.write_text(
                f"app: {app}        # chatgpt | gemini\nmodelo: ''\noperador: ''\nnotas: ''\n"
            )
        return workdir, instructions

    def edit(self, request: EditRequest) -> EditResult:
        workdir, instructions = self.prepare(request)
        result_path = find_result(workdir)
        waited = 0.0
        if result_path is None:
            if not self.cfg.manual_wait:
                raise ManualStepPendingError(workdir, instructions)
            log.warning("Paso manual pendiente. Instrucciones en %s/INSTRUCCIONES.md", workdir)
            print(
                f"\n{instructions}\nCarpeta: {workdir.resolve()}\nEsperando resultado…", flush=True
            )
            start = time.monotonic()
            while (result_path := find_result(workdir)) is None:
                if time.monotonic() - start > self.cfg.manual_timeout_s:
                    raise ManualStepPendingError(workdir, instructions)
                time.sleep(self.poll_s)
            time.sleep(0.5)  # por si el archivo se está terminando de escribir
            waited = time.monotonic() - start
        image, adjusted = fit_to_aspect(load_image(result_path), request.base.size)
        meta = yaml.safe_load((workdir / "meta.yaml").read_text()) or {}
        app = str(meta.get("app") or self.cfg.manual_app).split()[0]
        usage = UsageRecord(
            stage=request.stage,
            provider=self.provider,
            model=f"manual:{app}",
            images_out=1,
            latency_s=round(waited, 1),
            manual=True,
            extra={"app": app, "modelo": meta.get("modelo"), "operador": meta.get("operador")},
        )
        return EditResult(
            image=image,
            usage=usage,
            meta={
                "manual": True,
                "app": app,
                "workdir": str(workdir),
                "aspect_adjusted": adjusted,
                **meta,
            },
        )

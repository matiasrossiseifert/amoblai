"""Editor de prueba: no llama a ninguna API, devuelve la base marcada y estima el costo.

Permite probar el pipeline y las webapps de punta a punta sin gastar. Combinado
con `--image1` (una imagen 1 dada, por ejemplo una foto de ambiente de IKEA) sirve
para ver detección, recortes y retrieval reales sin generar nada.
"""

from __future__ import annotations

import numpy as np
from PIL import ImageDraw

from amoblai_imagen.generation.base import EditRequest, EditResult, ImageEditor
from amoblai_imagen.infra.usage import UsageRecord


class DryRunEditor:
    provider = "dry_run"

    def __init__(self, simulated: ImageEditor | None = None):
        self.simulated = simulated
        self.model = f"dry_run:{simulated.provider}:{simulated.model}" if simulated else "dry_run"

    def estimate_usd(self, request: EditRequest) -> float:
        return self.simulated.estimate_usd(request) if self.simulated else 0.0

    def edit(self, request: EditRequest) -> EditResult:
        img = request.base.convert("RGB").copy()
        draw = ImageDraw.Draw(img, "RGBA")
        if request.mask is not None:
            ys, xs = np.nonzero(request.mask)
            if len(xs):
                draw.rectangle(
                    [xs.min(), ys.min(), xs.max(), ys.max()], outline=(230, 30, 30, 255), width=4
                )
        w, _ = img.size
        draw.rectangle([0, 0, w, 36], fill=(0, 0, 0, 160))
        draw.text(
            (10, 10), f"DRY RUN · {request.stage} · sin llamada a la API", fill=(255, 255, 255, 255)
        )
        usage = UsageRecord(
            stage=request.stage,
            provider=self.provider,
            model=self.model,
            dry_run=True,
            cost_usd=round(self.estimate_usd(request), 6),
        )
        return EditResult(image=img, usage=usage, meta={"dry_run": True})

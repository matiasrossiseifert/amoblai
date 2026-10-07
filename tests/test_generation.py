import base64
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from amoblai.config import EditorConfig
from amoblai.generation.base import EditRequest, ManualStepPendingError
from amoblai.generation.editors.dry_run import DryRunEditor
from amoblai.generation.editors.manual_editor import ManualImageEditor, fit_to_aspect
from amoblai.generation.editors.openai_editor import OpenAIImageEditor
from amoblai.generation.geometry import (
    FitTransform,
    boxes_mask,
    closest_aspect,
    closest_fixed_size,
    composite,
    free_size,
    openai_mask,
)
from amoblai.generation.prompts import PlacedProduct, generator1_prompt, generator2_single_prompt
from amoblai.generation.service import EditorService
from amoblai.infra.budget import BudgetExceededError, BudgetGuard
from amoblai.infra.images import to_png_bytes
from amoblai.infra.usage import PricingTable, SpendLedger
from amoblai.vision.boxes import Box
from tests.conftest import ROOT


def _request(size=(64, 48), mask=False) -> EditRequest:
    base = Image.new("RGB", size, (100, 120, 140))
    m = boxes_mask(size, [Box(10, 10, 30, 30)]) if mask else None
    return EditRequest(
        "generator1",
        "amoblar",
        [base, Image.new("RGB", (20, 20), "red")],
        ["ambiente", "producto_x"],
        m,
    )


def test_sizes_and_aspects():
    assert free_size(1536, 1024) == (1536, 1024)
    w, h = free_size(1000, 333, max_side=1536)
    assert w % 16 == 0 and h % 16 == 0
    assert closest_fixed_size(1600, 1000) == (1536, 1024)
    assert closest_fixed_size(900, 1400) == (1024, 1536)
    assert closest_aspect(1920, 1080) == "16:9"


def test_fit_transform_roundtrip_preserves_geometry():
    img = Image.new("RGB", (300, 200), (0, 0, 0))
    img.paste((255, 0, 0), (0, 0, 150, 200))
    fit = FitTransform((300, 200), (256, 256))
    canvas = fit.apply(img)
    assert canvas.size == (256, 256)
    back = fit.invert(canvas)
    assert back.size == (300, 200)
    assert back.getpixel((10, 100))[0] > 200 and back.getpixel((290, 100))[0] < 50


def test_masks_and_composite():
    mask = boxes_mask((40, 40), [Box(10, 10, 20, 20)], dilation=0.0)
    assert mask.sum() == 100
    rgba = openai_mask(mask)
    assert rgba.mode == "RGBA"
    assert rgba.getpixel((15, 15))[3] == 0 and rgba.getpixel((0, 0))[3] == 255
    base = Image.new("RGB", (40, 40), "white")
    gen = Image.new("RGB", (40, 40), "black")
    out = composite(base, gen, mask, feather_px=0)
    assert out.getpixel((15, 15)) == (0, 0, 0) and out.getpixel((0, 0)) == (255, 255, 255)


def test_prompts_mention_scope_and_products():
    p1 = generator1_prompt("estilo nórdico", ["sofa", "rug"])
    assert "sofa, rug" in p1 and "estilo nórdico" in p1
    placed = [
        PlacedProduct("sofa", Box(0, 50, 50, 100), "1", "KIVIK", "Three-seat sofa", "200x90 cm")
    ]
    p2 = generator2_single_prompt(placed, (100, 100), "image1")
    assert "image 2" in p2 and "KIVIK" in p2 and "front left" in p2
    # Dos sillas iguales y una mesa: el producto repetido se adjunta una vez.
    chairs = [
        PlacedProduct("chair", Box(0, 0, 10, 10), "7", "INGOLF", "Chair", None),
        PlacedProduct("table", Box(20, 0, 40, 10), "8", "LISABO", "Table", None),
        PlacedProduct("chair", Box(50, 0, 60, 10), "7", "INGOLF", "Chair", None),
    ]
    p3 = generator2_single_prompt(chairs, (100, 100), "original")
    assert p3.count("product in image 2") == 2 and "product in image 3" in p3
    assert "image 4" not in p3


def test_manual_editor_pending_then_result(tmp_path):
    cfg = EditorConfig(provider="manual", manual_wait=False, manual_app="gemini")
    editor = ManualImageEditor(cfg, tmp_path)
    req = _request(mask=True)
    req.cache_key = "abc"
    with pytest.raises(ManualStepPendingError) as err:
        editor.edit(req)
    workdir = err.value.workdir
    assert (workdir / "prompt.txt").read_text() == "amoblar"
    assert (workdir / "entrada_1_ambiente.png").exists()
    assert (workdir / "zona_a_editar.png").exists()
    assert "gemini" in (workdir / "INSTRUCCIONES.md").read_text()
    # La persona deja el resultado (con otro aspecto) y completa la app usada.
    Image.new("RGB", (100, 100), "green").save(workdir / "resultado.png")
    (workdir / "meta.yaml").write_text("app: chatgpt\nmodelo: gpt-image\n")
    result = editor.edit(req)
    assert result.image.size == (64, 48)
    assert result.usage.manual and result.usage.model == "manual:chatgpt"
    assert result.meta["aspect_adjusted"]


def test_fit_to_aspect():
    img, adjusted = fit_to_aspect(Image.new("RGB", (100, 50)), (40, 40))
    assert img.size == (40, 40) and adjusted
    _, adjusted = fit_to_aspect(Image.new("RGB", (80, 60)), (40, 30))
    assert not adjusted


def test_service_caches_and_enforces_budget(tmp_path):
    calls = []

    class FakeEditor:
        provider = "openai"
        model = "gpt-image-2"

        def estimate_usd(self, request):
            return 0.05

        def edit(self, request):
            from amoblai.generation.base import EditResult
            from amoblai.infra.usage import UsageRecord

            calls.append(request.cache_key)
            usage = UsageRecord(
                stage=request.stage, provider="openai", model="gpt-image-2", cost_usd=0.05
            )
            return EditResult(request.base.copy(), usage)

    budget = BudgetGuard(max_calls=1)
    ledger = SpendLedger(tmp_path / "gastos.jsonl")
    service = EditorService(FakeEditor(), EditorConfig(), tmp_path / "gen", budget, ledger)
    r1 = service.edit(_request())
    r2 = service.edit(_request())  # misma entrada → caché, no paga
    assert len(calls) == 1
    assert r2.usage.cached and r2.usage.cost_usd == 0.0
    assert ledger.total_usd() == pytest.approx(0.05)
    assert r1.image.size == r2.image.size
    other = _request(size=(70, 40))
    with pytest.raises(BudgetExceededError):
        service.edit(other)  # tope de 1 llamada


def test_dry_run_editor_estimates_without_calling():
    pricing = PricingTable.load(ROOT / "configs" / "pricing.yaml")

    class Sim:
        provider, model = "openai", "gpt-image-2"

        def estimate_usd(self, request):
            return pricing.estimate("openai", "gpt-image-2", "medium", request.base.size, 2)

    result = DryRunEditor(Sim()).edit(_request(mask=True))
    assert result.usage.dry_run and result.usage.cost_usd > 0
    assert result.image.size == (64, 48)


def test_openai_editor_builds_request_and_parses_usage():
    pricing = PricingTable.load(ROOT / "configs" / "pricing.yaml")
    editor = OpenAIImageEditor.__new__(OpenAIImageEditor)
    editor.cfg = EditorConfig(
        provider="openai", model="gpt-image-2", quality="low", size_policy="fixed"
    )
    editor.model, editor.pricing = "gpt-image-2", pricing
    captured = {}

    def fake_edit(**kwargs):
        captured.update(kwargs)
        w, h = (int(v) for v in kwargs["size"].split("x"))
        out = Image.new("RGB", (w, h), "blue")
        usage = SimpleNamespace(
            input_tokens_details=SimpleNamespace(text_tokens=100, image_tokens=2000),
            output_tokens_details=SimpleNamespace(image_tokens=272, text_tokens=0),
            output_tokens=272,
        )
        return SimpleNamespace(
            data=[SimpleNamespace(b64_json=base64.b64encode(to_png_bytes(out)))], usage=usage
        )

    editor.client = SimpleNamespace(images=SimpleNamespace(edit=fake_edit))
    result = editor.edit(_request(size=(300, 200), mask=True))
    assert captured["size"] == "1536x1024"
    assert len(captured["image"]) == 2 and "mask" in captured
    assert result.image.size == (300, 200)
    assert result.usage.input_image_tokens == 2000
    expected = (100 * 5 + 2000 * 8 + 272 * 30) / 1e6
    assert result.usage.cost_usd == pytest.approx(expected, rel=1e-3)
    assert np.asarray(result.image)[100, 150, 2] > 200


def test_gemini_editor_parses_image_and_usage():
    from amoblai.generation.editors.gemini_editor import GeminiImageEditor

    pricing = PricingTable.load(ROOT / "configs" / "pricing.yaml")
    editor = GeminiImageEditor.__new__(GeminiImageEditor)
    editor.cfg = EditorConfig(provider="gemini", model="gemini-3.1-flash-image")
    editor.model, editor.pricing = "gemini-3.1-flash-image", pricing
    captured = {}

    def generate_content(model, contents, config):
        captured.update(model=model, contents=contents, config=config)
        out = Image.new("RGB", (1536, 1024), "green")
        part = SimpleNamespace(inline_data=SimpleNamespace(data=to_png_bytes(out)))
        cand = SimpleNamespace(content=SimpleNamespace(parts=[part]), finish_reason="STOP")
        usage = SimpleNamespace(prompt_token_count=1500, candidates_token_count=1120)
        return SimpleNamespace(candidates=[cand], usage_metadata=usage)

    editor.client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
    result = editor.edit(_request(size=(300, 200), mask=True))
    assert captured["config"].image_config.aspect_ratio == "3:2"
    assert isinstance(captured["contents"][0], str) and len(captured["contents"]) == 3
    assert result.image.size == (300, 200)
    assert result.meta["mask_ignored"]
    assert result.usage.cost_usd == pytest.approx((1500 * 0.5 + 1120 * 60) / 1e6, rel=1e-3)

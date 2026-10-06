import json

import pytest
from PIL import Image

from amoblai.eval.e2e_eval import aggregate_e2e, evaluate_result, ssim_outside
from amoblai.eval.retriever_eval import run_retriever_eval
from amoblai.eval.strict_eval import StrictLabel, append_label, load_labels, run_strict_eval
from amoblai.generation.editors.dry_run import DryRunEditor
from amoblai.generation.editors.manual_editor import ManualImageEditor
from amoblai.generation.service import EditorService
from amoblai.infra.budget import BudgetGuard
from amoblai.infra.runs import RunContext
from amoblai.pipeline.query import FurnishPipeline
from amoblai.report.report import build_report
from tests.conftest import ROOM_BOXES, ROOM_ID, make_room_image


def _pipeline(cfg, components, editor=None) -> FurnishPipeline:
    budget = BudgetGuard()
    gen = EditorService(
        editor or DryRunEditor(), cfg.generation.generator1, cfg.paths.generations_dir, budget
    )
    return FurnishPipeline(cfg, components, gen, gen)


def test_pipeline_with_given_image1_saves_every_stage(cfg, components):
    run = RunContext(cfg, "run", name="test")
    empty = Image.new("RGB", (320, 320), (180, 180, 170))
    result = _pipeline(cfg, components).run(
        empty, "living cálido", run=run, image1=make_room_image()
    )
    assert result.status == "ok"
    assert {it.product.sku for it in result.accepted} == set(ROOM_BOXES)
    assert result.final is not None and result.final.size == result.original.size
    for name in (
        "00_original.jpg",
        "01_imagen1.jpg",
        "02_detecciones.jpg",
        "05_mascara.png",
        "06_final.jpg",
    ):
        assert (run.dir / name).exists(), name
    assert len(list((run.dir / "03_recortes").glob("*_consulta.jpg"))) == 3
    shopping = json.loads((run.dir / "lista_compra.json").read_text())
    assert set(shopping["productos"]) == set(ROOM_BOXES)
    assert shopping["productos"]["100.000.01"]["categoria"] == "sofá"
    summary = json.loads((run.dir / "resultado.json").read_text())
    assert summary["image1_source"] == "provided" and len(summary["items"]) == 3


def test_pipeline_per_item_mode_from_original(cfg, components):
    cfg.generation.gen2_mode = "per_item"
    cfg.generation.gen2_base = "original"
    cfg.generation.composite = True
    result = _pipeline(cfg, components).run(make_room_image(), "", image1=make_room_image())
    assert len(result.gen2_steps) == 3
    assert result.usage and all(u.dry_run for u in result.usage)


def test_pipeline_pauses_on_manual_step_and_resumes(cfg, components):
    cfg.generation.generator1.manual_wait = False
    manual = ManualImageEditor(cfg.generation.generator1, cfg.paths.generations_dir / "manual")
    pipeline = _pipeline(cfg, components, manual)
    room = Image.new("RGB", (320, 320), (180, 180, 170))
    first = pipeline.run(room, "algo")
    assert first.status == "pending_manual"
    workdir = first.pending.workdir
    assert (workdir / "prompt.txt").exists()
    make_room_image().save(workdir / "resultado.png")
    # El generador 2 también es manual: queda pendiente en el paso siguiente.
    second = pipeline.run(room, "algo")
    assert second.image1 is not None and second.status == "pending_manual"
    assert second.pending.workdir != workdir
    second.pending.workdir.joinpath("resultado.png").parent.mkdir(exist_ok=True)
    make_room_image().save(second.pending.workdir / "resultado.png")
    third = pipeline.run(room, "algo")
    assert third.status == "ok"
    assert all(u.manual for u in third.usage)
    assert any(u.cached for u in third.usage)  # el paso 1 ya estaba en caché


def test_e2e_metrics_on_dry_run(cfg, components):
    result = _pipeline(cfg, components).run(make_room_image(), "", image1=make_room_image())
    metrics = evaluate_result(result, _pipeline(cfg, components))
    assert metrics["coverage"] == 1.0
    assert metrics["reid@1"] == 1.0  # dry-run devuelve la misma imagen
    # La imagen 1 dada es idéntica a la original; la final tiene la banda del dry-run.
    assert metrics["preservation_image1"]["ssim_outside"] == pytest.approx(1.0, abs=1e-3)
    assert metrics["preservation_final"]["ssim_outside"] < 1.0
    agg = aggregate_e2e({"a.jpg": metrics | {"usage": {"cost_usd": 0.0, "latency_s": 0.0}}}, cfg)
    assert agg["reid@1"] == 1.0 and agg["rooms_done"] == 1


def test_ssim_outside_detects_changes():
    a = Image.new("RGB", (64, 64), (120, 120, 120))
    b = a.copy()
    b.paste((255, 255, 255), (0, 0, 32, 64))
    import numpy as np

    exclude = np.zeros((64, 64), dtype=bool)
    assert ssim_outside(a, b, exclude)["mae_outside"] > 0
    exclude[:, :40] = True
    assert ssim_outside(a, b, exclude)["mae_outside"] == 0


def test_retriever_eval_strict_eval_and_report(cfg, components):
    run = RunContext(cfg, "retriever", name="eval")
    metrics = run_retriever_eval(cfg, run, components, calibrate=True)
    assert metrics["rooms"] == 1
    assert metrics["retrieval"]["hit@1"] == 1.0
    assert metrics["items"]["recall@1"] == 1.0
    assert metrics["random_baseline"]["hit@1"] < 1.0
    assert cfg.paths.thresholds_file.exists()
    append_label(
        cfg.paths.labels_file,
        StrictLabel(
            room_id=ROOM_ID,
            box=ROOM_BOXES["100.000.03"].as_list(),
            category="chair",
            sku="100.000.03",
        ),
    )
    assert len(load_labels(cfg.paths.labels_file)) == 1
    metrics |= run_strict_eval(cfg, run, components)
    assert metrics["strict"]["hit@1"] == 1.0
    run.finish(metrics)
    written = build_report(cfg.paths.runs_dir, cfg.paths.results_dir / "reporte")
    text = written["readme"].read_text()
    assert "Retriever" in text and "estricto" in text

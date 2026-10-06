"""Detección de muebles con detectores de vocabulario abierto (Grounding DINO u OWLv2).

El detector recibe las etiquetas en inglés de `configs/categories.yaml` y cada
detección se mapea a una de las categorías del alcance. Después se filtra por
tamaño y se aplica NMS dos veces: dentro de cada categoría (cajas repetidas) y
entre categorías (la misma pieza detectada como "chair" y como "armchair": se
queda la de mayor score).
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Protocol

from PIL import Image

from amoblai.config import DetectionConfig, stable_hash
from amoblai.infra.cache import ArtifactCache
from amoblai.infra.device import resolve_device
from amoblai.infra.images import image_digest
from amoblai.vision.boxes import Box

log = logging.getLogger(__name__)

DEFAULT_MODELS = {
    "grounding_dino": "IDEA-Research/grounding-dino-tiny",
    "owlv2": "google/owlv2-base-patch16-ensemble",
}


@dataclass(frozen=True)
class Detection:
    box: Box
    category: str
    label: str  # frase del detector que la originó
    score: float

    def to_dict(self) -> dict:
        d = asdict(self)
        d["box"] = self.box.as_list()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Detection:
        return cls(Box.from_list(d["box"]), d["category"], d["label"], float(d["score"]))


class Detector(Protocol):
    def detect(self, image: Image.Image) -> list[Detection]: ...


def match_label(text: str, label_to_category: dict[str, str]) -> tuple[str, str] | None:
    """Mapea la etiqueta devuelta por el detector a (frase, categoría).

    Grounding DINO a veces devuelve frases parciales o fusionadas ("coffee table",
    "table", "chair table"): se elige la frase configurada más larga contenida en
    el texto y, si ninguna está contenida, la primera que contenga al texto.
    """
    text = text.strip().lower()
    if not text:
        return None
    contained = [lbl for lbl in label_to_category if lbl in text]
    if contained:
        best = max(contained, key=len)
        return best, label_to_category[best]
    for lbl, cat in label_to_category.items():
        if text in lbl:
            return lbl, cat
    return None


def nms(dets: list[Detection], iou_threshold: float) -> list[Detection]:
    kept: list[Detection] = []
    for det in sorted(dets, key=lambda d: d.score, reverse=True):
        if all(det.box.iou(k.box) <= iou_threshold for k in kept):
            kept.append(det)
    return kept


def postprocess(
    dets: list[Detection], cfg: DetectionConfig, width: int, height: int
) -> list[Detection]:
    total = float(width * height)
    dets = [d for d in dets if cfg.min_area_frac * total <= d.box.area <= cfg.max_area_frac * total]
    per_category: list[Detection] = []
    for cat in sorted({d.category for d in dets}):
        per_category += nms([d for d in dets if d.category == cat], cfg.nms_iou)
    final = nms(per_category, cfg.cross_category_iou)
    return sorted(final, key=lambda d: d.score, reverse=True)[: cfg.max_detections]


class GroundingDinoDetector:
    def __init__(
        self, cfg: DetectionConfig, label_to_category: dict[str, str], device: str = "auto"
    ):
        import torch
        from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

        self.cfg = cfg
        self.label_to_category = label_to_category
        self.device = resolve_device(device)
        model_id = cfg.model_id or DEFAULT_MODELS["grounding_dino"]
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = (
            AutoModelForZeroShotObjectDetection.from_pretrained(model_id).to(self.device).eval()
        )
        # Formato que espera Grounding DINO: frases en minúscula separadas por punto.
        self.text = " ".join(f"{label}." for label in label_to_category)
        self._torch = torch

    def detect(self, image: Image.Image) -> list[Detection]:
        inputs = self.processor(images=image, text=self.text, return_tensors="pt").to(self.device)
        with self._torch.inference_mode():
            outputs = self.model(**inputs)
        res = self.processor.post_process_grounded_object_detection(
            outputs,
            inputs["input_ids"],
            threshold=self.cfg.box_threshold,
            text_threshold=self.cfg.text_threshold,
            target_sizes=[image.size[::-1]],
        )[0]
        labels = res.get("text_labels") or res.get("labels")
        dets = []
        for box, score, text in zip(
            res["boxes"].tolist(), res["scores"].tolist(), labels, strict=True
        ):
            matched = match_label(str(text), self.label_to_category)
            if matched:
                dets.append(Detection(Box.from_list(box), matched[1], matched[0], float(score)))
        return postprocess(dets, self.cfg, *image.size)


class Owlv2Detector:
    def __init__(
        self, cfg: DetectionConfig, label_to_category: dict[str, str], device: str = "auto"
    ):
        import torch
        from transformers import Owlv2ForObjectDetection, Owlv2Processor

        self.cfg = cfg
        self.label_to_category = label_to_category
        self.labels = list(label_to_category)
        self.device = resolve_device(device)
        model_id = cfg.model_id or DEFAULT_MODELS["owlv2"]
        self.processor = Owlv2Processor.from_pretrained(model_id)
        self.model = Owlv2ForObjectDetection.from_pretrained(model_id).to(self.device).eval()
        self._torch = torch

    def detect(self, image: Image.Image) -> list[Detection]:
        queries = [f"a photo of a {label}" for label in self.labels]
        inputs = self.processor(text=[queries], images=image, return_tensors="pt").to(self.device)
        with self._torch.inference_mode():
            outputs = self.model(**inputs)
        # OWLv2 rellena la imagen a un cuadrado (abajo y a la derecha): las cajas
        # quedan relativas a ese cuadrado, así que se escalan por el lado mayor.
        side = max(image.size)
        res = self.processor.post_process_grounded_object_detection(
            outputs, threshold=self.cfg.box_threshold, target_sizes=[(side, side)]
        )[0]
        dets = []
        for box, score, idx in zip(
            res["boxes"].tolist(), res["scores"].tolist(), res["labels"].tolist(), strict=True
        ):
            label = self.labels[int(idx)]
            box_obj = Box.from_list(box).clip(*image.size)
            dets.append(Detection(box_obj, self.label_to_category[label], label, float(score)))
        return postprocess(dets, self.cfg, *image.size)


class CachedDetector:
    """Reusa detecciones ya calculadas para la misma imagen y la misma config."""

    def __init__(
        self, detector: Detector, cfg: DetectionConfig, labels: list[str], cache: ArtifactCache
    ):
        self.detector = detector
        self.cache = cache
        self.config_key = stable_hash({"cfg": cfg.model_dump(mode="json"), "labels": labels})

    def detect(self, image: Image.Image) -> list[Detection]:
        key = self.cache.key({"image": image_digest(image), "detector": self.config_key})
        cached = self.cache.get_json(key, "detections.json")
        if cached is not None:
            return [Detection.from_dict(d) for d in cached]
        dets = self.detector.detect(image)
        self.cache.put_json(key, [d.to_dict() for d in dets], "detections.json")
        return dets


def build_detector(
    cfg: DetectionConfig,
    label_to_category: dict[str, str],
    device: str = "auto",
    cache: ArtifactCache | None = None,
) -> Detector:
    detector: Detector
    if cfg.provider == "grounding_dino":
        detector = GroundingDinoDetector(cfg, label_to_category, device)
    elif cfg.provider == "owlv2":
        detector = Owlv2Detector(cfg, label_to_category, device)
    else:  # pragma: no cover - lo impide la validación de la config
        raise ValueError(cfg.provider)
    if cache is not None:
        detector = CachedDetector(detector, cfg, list(label_to_category), cache)
    return detector

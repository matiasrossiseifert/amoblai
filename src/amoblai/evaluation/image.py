"""Métricas de la imagen que genera el flujo (gratis: modelos locales, ninguna API).

Para una corrida con imagen final (`datos/resultados/amoblar/<corrida>/`, la de 5_image.json):

- **fidelidad de producto** (la faithfulness de la clase 11 llevada a la imagen: ¿la imagen usa
  los productos que se recuperaron o dibuja otros?): Grounding DINO busca en la imagen final cada
  producto de la lista, con las frases del detector de su categoría (categories.yaml); el
  recorte se embebe con DINOv3, igual que la foto del producto en el catálogo. Por producto: el
  coseno con su foto y su puesto entre los productos del catálogo de su tipo, ordenados por
  parecido al recorte (1 = la imagen muestra ese producto y no otro parecido). La vara es la
  misma identificación con fotos reales (`reference`): los recortes de los productos anotados en
  los ambientes IKEA, fotografiados de verdad en un ambiente.
- **presencia y piezas inventadas**: qué productos de la lista se detectan, y qué detecciones de
  la imagen final no son de la lista ni estaban en la foto original.
- **ambiente preservado**: SSIM entre la foto original y la final fuera de las cajas de los
  muebles (paredes, piso, aberturas), y SIFT + RANSAC: de los puntos de la foto original, qué
  fracción se reencuentra en la final con una homografía, y cuánto se movieron (la cámara tiene
  que quedar quieta).
- **pedido ↔ imagen** (la answer relevance, en imagen): SigLIP 2, multilingüe, entre el pedido y
  la imagen final, contra la foto vacía y contra pedidos de contraste.

Las detecciones y los vectores de las fotos del catálogo quedan en datos/cache/imagen/.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

from amoblai import paths
from amoblai.catalog.loader import Product, load_catalog
from amoblai.config import Config

DETECTOR = "IDEA-Research/grounding-dino-tiny"
EMBEDDER = "facebook/dinov3-vitb16-pretrain-lvd1689m"  # el mejor de la v0 (retrieval por imagen)
ALIGNER = "google/siglip2-base-patch16-224"  # texto multilingüe: el pedido va en castellano
DETECTOR_VERSION = 1  # sube cuando cambia cómo se detecta (invalida la caché)

BOX_THRESHOLD = 0.30
NMS_IOU, CROSS_IOU = 0.5, 0.8  # dentro de una categoría y entre categorías (la v0)
MIN_AREA, MAX_AREA = 0.004, 0.9  # fracción de la imagen
CROP_MARGIN = 0.05  # alrededor de la caja, del lado mayor
PAD_MARGIN = 0.05  # blanco alrededor al cuadrar, como las fotos del catálogo
SIDE = 800  # ancho al que se comparan la foto original y la final

# Si el detector no ve un producto con las frases de su categoría, se busca en las vecinas
# (un sillón detectado como sofá sigue siendo el sillón).
FAMILY = {
    **dict.fromkeys(("sofa", "armchair", "chair", "ottoman", "stool", "bench"), "asiento"),
    **dict.fromkeys(("table", "desk"), "mesa"),
    **dict.fromkeys(("shelf", "cabinet", "dresser"), "guardado"),
}
# En lámparas y decoración el grupo de relevancia es el kind (retrieval.group_of): la frase
# del detector que lo dice. "lamp" sola no dice cuál, y no entra en la referencia.
PHRASE_GROUP = {
    "pendant lamp": "pendant lamp",
    "floor lamp": "floor lamp",
    "cushion": "cushion",
    "vase": "vase",
    "plant": "plant",
    "picture frame": "wall art",
    "mirror": "mirror",
    "curtains": "curtains",
}
# Pedidos que la imagen final no debería cumplir mejor que el suyo.
CONTRAST = (
    "un ambiente vacío, sin muebles",
    "un dormitorio infantil colorido",
    "una oficina industrial con muebles de metal negro",
    "un comedor rústico para ocho personas",
    "un living glam con terciopelo y dorados",
    "una cocina blanca moderna",
)


@dataclass(frozen=True)
class Det:
    box: tuple[float, float, float, float]  # x0, y0, x1, y1 en píxeles
    category: str
    label: str  # la frase del detector
    score: float


def detector_labels(categories_file: Path = paths.CATEGORIES) -> dict[str, str]:
    """{frase del detector: categoría}, de datos/configs/categories.yaml."""
    spec = yaml.safe_load(Path(categories_file).read_text())["categories"]
    out: dict[str, str] = {}
    for cat, c in spec.items():
        for label in c.get("detector_labels") or []:
            out.setdefault(label, cat)
    return out


def area(b: Sequence[float]) -> float:
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def inside(a: Sequence[float], b: Sequence[float]) -> float:
    """Qué fracción de la caja `a` cae dentro de `b`."""
    inter = area((max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])))
    return inter / area(a) if area(a) else 0.0


def iou(a: Sequence[float], b: Sequence[float]) -> float:
    inter = area((max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])))
    union = area(a) + area(b) - inter
    return inter / union if union else 0.0


def nms(dets: list[Det], threshold: float) -> list[Det]:
    kept: list[Det] = []
    for d in sorted(dets, key=lambda d: -d.score):
        if all(iou(d.box, k.box) <= threshold for k in kept):
            kept.append(d)
    return kept


def postprocess(dets: list[Det], width: int, height: int) -> list[Det]:
    """Por tamaño, NMS dentro de cada categoría y después entre categorías (la misma pieza vista
    como "chair" y como "armchair": queda la de más score)."""
    total = float(width * height)
    dets = [d for d in dets if MIN_AREA * total <= area(d.box) <= MAX_AREA * total]
    per_cat = [
        k
        for c in sorted({d.category for d in dets})
        for k in nms([d for d in dets if d.category == c], NMS_IOU)
    ]
    return nms(per_cat, CROSS_IOU)


def pad_square(img: Image.Image, margin: float = PAD_MARGIN) -> Image.Image:
    """Centrada en un cuadrado blanco: el procesador no le corta los extremos a un sofá."""
    img = img.convert("RGB")
    w, h = img.size
    side = round(max(w, h) * (1 + 2 * margin))
    canvas = Image.new("RGB", (side, side), "white")
    canvas.paste(img, ((side - w) // 2, (side - h) // 2))
    return canvas


def crop(image: Image.Image, box: Sequence[float], margin: float = CROP_MARGIN) -> Image.Image:
    w, h = image.size
    pad = margin * max(box[2] - box[0], box[3] - box[1])
    x0, y0 = max(0, box[0] - pad), max(0, box[1] - pad)
    x1, y1 = min(w, box[2] + pad), min(h, box[3] + pad)
    return image.crop((round(x0), round(y0), round(x1), round(y1)))


def _sha(data: bytes | str) -> str:
    raw = data.encode() if isinstance(data, str) else data
    return hashlib.sha256(raw).hexdigest()[:24]


class Models:
    """Los tres modelos locales, cargados la primera vez que se usan."""

    def __init__(self, cache_dir: Path = paths.CACHE / "imagen"):
        self.cache = Path(cache_dir)
        self._det = self._emb = self._align = None

    def detect(self, image_path: Path, labels: dict[str, str]) -> list[Det]:
        """Las detecciones de la foto con las frases `labels`, cada caja asignada a la frase de
        mayor probabilidad (clasificación por frase: el post-procesamiento estándar funde las
        frases, "armchair chair", y no distingue silla de sillón)."""
        key = _sha(
            json.dumps(
                [
                    _sha(Path(image_path).read_bytes()),
                    sorted(labels),
                    DETECTOR,
                    DETECTOR_VERSION,
                    BOX_THRESHOLD,
                ]
            )
        )
        f = self.cache / "detecciones" / f"{key}.json"
        if f.exists():
            return [
                Det(tuple(d["box"]), d["category"], d["label"], d["score"])
                for d in json.loads(f.read_text())
            ]
        import torch

        if self._det is None:
            from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

            proc = AutoProcessor.from_pretrained(DETECTOR)
            model = AutoModelForZeroShotObjectDetection.from_pretrained(DETECTOR).eval()
            self._det = proc, model
        proc, model = self._det
        phrases = list(labels)
        text, positions = _phrase_tokens(proc.tokenizer, phrases)
        image = Image.open(image_path).convert("RGB")
        inputs = proc(images=image, text=text, return_tensors="pt")
        with torch.inference_mode():
            out = model(**inputs)
        probs = out.logits[0].sigmoid().float()  # (consultas, tokens)
        per_phrase = torch.stack([probs[:, p].max(dim=1).values for p in positions], dim=1)
        scores, best = per_phrase.max(dim=1)
        keep = scores > BOX_THRESHOLD
        w, h = image.size
        dets = []
        for (cx, cy, bw, bh), s, i in zip(
            out.pred_boxes[0].float()[keep].tolist(),
            scores[keep].tolist(),
            best[keep].tolist(),
            strict=True,
        ):
            box = (
                max(0.0, (cx - bw / 2) * w),
                max(0.0, (cy - bh / 2) * h),
                min(float(w), (cx + bw / 2) * w),
                min(float(h), (cy + bh / 2) * h),
            )
            dets.append(Det(box, labels[phrases[i]], phrases[i], float(s)))
        dets = postprocess(dets, w, h)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps([asdict(d) for d in dets]))
        return dets

    def embed(self, images: list[Image.Image]) -> np.ndarray:
        """DINOv3: el token CLS (pooler_output) de cada imagen cuadrada, de largo 1."""
        import torch

        if self._emb is None:
            from transformers import AutoImageProcessor, AutoModel

            self._emb = (
                AutoImageProcessor.from_pretrained(EMBEDDER),
                AutoModel.from_pretrained(EMBEDDER).eval(),
            )
        proc, model = self._emb
        side = _input_side(proc)
        rows = []
        with torch.inference_mode():
            for i in range(0, len(images), 16):
                batch = [
                    pad_square(im).resize((side, side), Image.Resampling.BICUBIC)
                    for im in images[i : i + 16]
                ]
                pix = proc(
                    images=batch, return_tensors="pt", do_resize=False, do_center_crop=False
                )["pixel_values"]
                rows.append(model(pixel_values=pix).pooler_output.float().numpy())
        v = np.concatenate(rows) if rows else np.zeros((0, 0), np.float32)
        return v / np.linalg.norm(v, axis=1, keepdims=True).clip(min=1e-12)

    def photo_vectors(self, photos: list[Path]) -> np.ndarray:
        """Los vectores DINOv3 de fotos del catálogo (en caché: una por archivo)."""
        out: list[np.ndarray | None] = []
        todo = []
        for p in photos:
            f = self.cache / "vectores" / f"{_sha(EMBEDDER + _sha(Path(p).read_bytes()))}.npy"
            if f.exists():
                out.append(np.load(f))
            else:
                out.append(None)
                todo.append((len(out) - 1, p, f))
        if todo:
            vecs = self.embed([Image.open(p) for _, p, _ in todo])
            for (i, _, f), v in zip(todo, vecs, strict=True):
                f.parent.mkdir(parents=True, exist_ok=True)
                np.save(f, v)
                out[i] = v
        return np.stack(out)

    def align(self, texts: list[str], images: list[Image.Image]) -> np.ndarray:
        """(textos, imágenes): el coseno de SigLIP 2 entre cada texto y cada imagen."""
        import torch

        if self._align is None:
            from transformers import AutoModel, AutoProcessor

            self._align = (
                AutoProcessor.from_pretrained(ALIGNER),
                AutoModel.from_pretrained(ALIGNER).eval(),
            )
        proc, model = self._align
        with torch.inference_mode():
            t = proc(
                text=texts,
                padding="max_length",
                max_length=64,
                truncation=True,
                return_tensors="pt",
            )
            tv = _features(model.get_text_features(**t))
            i = proc(images=[im.convert("RGB") for im in images], return_tensors="pt")
            iv = _features(model.get_image_features(**i))
        tv = tv / np.linalg.norm(tv, axis=1, keepdims=True)
        iv = iv / np.linalg.norm(iv, axis=1, keepdims=True)
        return tv @ iv.T


def _features(out) -> np.ndarray:
    t = out if hasattr(out, "float") else out.pooler_output
    return t.float().numpy()


def _input_side(processor) -> int:
    for attr in ("crop_size", "size"):
        size = getattr(processor, attr, None)
        if not size:
            continue
        get = size.get if isinstance(size, dict) else lambda k, s=size: getattr(s, k, None)
        for key in ("height", "shortest_edge"):
            if get(key):
                return int(get(key))
    return 224


def _phrase_tokens(tokenizer, phrases: list[str]) -> tuple[str, list[list[int]]]:
    """El texto para Grounding DINO ("sofa. couch. ...") y los tokens de cada frase."""
    text, spans = "", []
    for ph in phrases:
        start = len(text)
        text += ph
        spans.append((start, len(text)))
        text += ". "
    text = text.strip()
    offsets = tokenizer(text, return_offsets_mapping=True)["offset_mapping"]
    positions: list[list[int]] = [[] for _ in phrases]
    for tok, (s, e) in enumerate(offsets):
        for i, (a, b) in enumerate(spans):
            if e > s and s >= a and e <= b:
                positions[i].append(tok)
    if any(not p for p in positions):
        missing = [ph for ph, p in zip(phrases, positions, strict=True) if not p]
        raise ValueError(f"frases sin tokens: {missing}")
    return text, positions


def rank_among(vec: np.ndarray, relevant: set[str], candidates: dict[str, np.ndarray]) -> dict:
    """El puesto del relevante más parecido a `vec` entre los candidatos: 1 + cuántos no
    relevantes se le parecen más (una foto repetida en otro SKU no lo baja: empata)."""
    ids = list(candidates)
    sims = np.stack([candidates[i] for i in ids]) @ vec
    rel = [s for i, s in zip(ids, sims, strict=True) if i in relevant]
    if not rel:
        return {"rank": None, "cos": None, "n": len(ids)}
    best = max(rel)
    worse_than = int(
        sum(1 for i, s in zip(ids, sims, strict=True) if i not in relevant and s > best)
    )
    top = ids[int(np.argmax(sims))]
    return {"rank": 1 + worse_than, "cos": round(float(best), 4), "n": len(ids), "top": top}


def assign(products: list[Product], dets: list[Det], score: Callable[[Product, Det], float]):
    """Cada producto con una detección de su categoría (o, si no hay, de su familia), sin
    repetir: entre las detecciones candidatas (las de más score, hasta el doble de productos),
    la asignación que maximiza el parecido con la foto de cada producto (Hungarian). Por score
    solo, un sillón se queda con la detección de unas mesitas que el detector vio como banqueta."""
    from scipy.optimize import linear_sum_assignment

    out: dict[str, int] = {}
    used: set[int] = set()
    for level in ("category", "family"):
        groups: dict[str, list[Product]] = {}
        for p in products:
            if p.id in out:
                continue
            key = (
                p.info["category_tp"]
                if level == "category"
                else FAMILY.get(p.info["category_tp"], p.info["category_tp"])
            )
            groups.setdefault(key, []).append(p)
        for key, ps in groups.items():
            cands = [
                i
                for i, d in enumerate(dets)
                if i not in used
                and (d.category if level == "category" else FAMILY.get(d.category, d.category))
                == key
            ]
            cands = sorted(cands, key=lambda i: -dets[i].score)[: max(len(ps), 1) * 2]
            if not cands:
                continue
            cost = np.array([[-score(p, dets[i]) for i in cands] for p in ps])
            rows, cols = linear_sum_assignment(cost)
            pick = {ps[r].id: cands[c] for r, c in zip(rows, cols, strict=True)}
            out.update(pick)
            used.update(pick.values())
    return out


def preservation(before: Image.Image, after: Image.Image, boxes: list[Sequence[float]]) -> dict:
    """¿Es el mismo ambiente? SSIM fuera de las cajas (las cajas en coordenadas de `after`) y
    SIFT + RANSAC entre las dos fotos."""
    from skimage.feature import SIFT, match_descriptors
    from skimage.measure import ransac
    from skimage.metrics import structural_similarity
    from skimage.transform import ProjectiveTransform

    w = SIDE
    h = round(before.height * SIDE / before.width)
    b = np.asarray(before.convert("L").resize((w, h)), float) / 255
    a = np.asarray(after.convert("L").resize((w, h)), float) / 255
    ssim, smap = structural_similarity(b, a, data_range=1.0, full=True)
    sx, sy = w / after.width, h / after.height
    free = np.ones((h, w), bool)
    for x0, y0, x1, y1 in boxes:
        pad = 0.03 * w
        free[
            max(0, int(y0 * sy - pad)) : min(h, int(y1 * sy + pad)),
            max(0, int(x0 * sx - pad)) : min(w, int(x1 * sx + pad)),
        ] = False
    out: dict[str, Any] = {
        "ssim": round(float(ssim), 4),
        "ssim_fuera_de_los_muebles": round(float(smap[free].mean()), 4) if free.any() else None,
        "fraccion_fuera_de_los_muebles": round(float(free.mean()), 4),
    }
    sift_b, sift_a = SIFT(), SIFT()
    sift_b.detect_and_extract(b)
    sift_a.detect_and_extract(a)
    matches = match_descriptors(
        sift_b.descriptors, sift_a.descriptors, max_ratio=0.8, cross_check=True
    )
    out["sift_puntos_original"] = len(sift_b.keypoints)
    out["sift_matches"] = len(matches)
    if len(matches) >= 8:
        src = sift_b.keypoints[matches[:, 0]][:, ::-1]  # (fila, col) -> (x, y)
        dst = sift_a.keypoints[matches[:, 1]][:, ::-1]
        _, inliers = ransac(
            (src, dst),
            ProjectiveTransform,
            min_samples=4,
            residual_threshold=3,
            max_trials=2000,
            rng=0,
        )
        n_in = int(inliers.sum()) if inliers is not None else 0
        out["sift_inliers"] = n_in
        out["sift_reencontrados"] = round(n_in / max(1, len(sift_b.keypoints)), 4)
        if n_in:
            moved = np.linalg.norm(dst[inliers] - src[inliers], axis=1)
            out["sift_desplazamiento_mediano"] = round(float(np.median(moved)) / w, 4)
    return out


def contact_sheet(rows: list[tuple[Image.Image, Image.Image | None, str]], out: Path) -> None:
    """Por producto: su foto del catálogo, el recorte de la imagen final y los números."""
    cell = 260
    sheet = Image.new("RGB", (2 * cell, len(rows) * (cell + 40)), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(13)
    for n, (photo, cropped, text) in enumerate(rows):
        y = n * (cell + 40)
        for col, im in enumerate((photo, cropped)):
            if im is not None:
                sq = pad_square(im, 0.02).resize((cell - 10, cell - 10))
                sheet.paste(sq, (col * cell + 5, y + 5))
        draw.text((6, y + cell + 2), text, fill="black", font=font)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=88)


def _catalog(cfg: Config) -> dict[str, Product]:
    return {p.id: p for p in load_catalog(cfg.rag.catalog, cfg.root).products}


def _candidates(models: Models, catalog: dict[str, Product], category: str) -> dict[str, Any]:
    """Los productos del catálogo de un tipo (el filtro `type` de la búsqueda) con su vector."""
    ps = [p for p in catalog.values() if p.category == category]
    vecs = models.photo_vectors([p.photos()[0] for p in ps])
    return dict(zip([p.id for p in ps], vecs, strict=True))


def evaluate_run(cfg: Config, run_dir: Path, models: Models | None = None) -> dict[str, Any]:
    """Las métricas de la imagen final de una corrida: escribe `6_metricas_imagen.json` y
    `6_recortes.jpg` (la foto de cada producto al lado de su recorte) en la carpeta."""
    run_dir = Path(run_dir)
    models = models or Models(Path(cfg.cache_dir) / "imagen")
    image_meta = json.loads((run_dir / "5_image.json").read_text())
    final = run_dir / image_meta["image"]
    before_path = run_dir / "room.jpg"
    request = json.loads((run_dir / "request.json").read_text())["request"]
    choices = json.loads((run_dir / "3_choice.json").read_text())["answer"]["choices"]
    catalog = _catalog(cfg)
    products = [catalog[c["id"]] for c in choices if c.get("id") in catalog]
    labels = detector_labels()
    after_dets = [d for d in models.detect(final, labels) if d.score >= BOX_THRESHOLD]
    before_dets = [d for d in models.detect(before_path, labels) if d.score >= BOX_THRESHOLD]
    after = Image.open(final).convert("RGB")
    before = Image.open(before_path).convert("RGB")
    crops = [crop(after, d.box) for d in after_dets]
    crop_vecs = models.embed(crops) if crops else np.zeros((0, 0))
    photo_vecs = dict(
        zip(
            [p.id for p in products],
            models.photo_vectors([p.photos()[0] for p in products]),
            strict=True,
        )
    )

    def similarity(p: Product, d: Det) -> float:
        return float(crop_vecs[after_dets.index(d)] @ photo_vecs[p.id])

    picked = assign(products, after_dets, similarity)
    per_product, sheet = [], []
    by_category: dict[str, dict] = {}
    for p in products:
        row: dict[str, Any] = {
            "id": p.id,
            "kind": p.kind,
            "categoria": p.info["category_tp"],
            "detectado": p.id in picked,
        }
        cropped = None
        if p.id in picked:
            d = after_dets[picked[p.id]]
            if p.category not in by_category:
                by_category[p.category] = _candidates(models, catalog, p.category)
            ident = rank_among(crop_vecs[picked[p.id]], {p.id}, by_category[p.category])
            row.update(
                detector=d.label,
                score_detector=round(d.score, 3),
                box=[round(v) for v in d.box],
                puesto=ident["rank"],
                entre=ident["n"],
                coseno=ident["cos"],
                mas_parecido=ident["top"],
            )
            cropped = crops[picked[p.id]]
        per_product.append(row)
        text = f"{p.id} {p.kind}: " + (
            f"coseno {row['coseno']:.2f}, puesto {row['puesto']}/{row['entre']}"
            if row["detectado"]
            else "no se detectó"
        )
        sheet.append((Image.open(p.photos()[0]), cropped, text))
    assigned = set(picked.values())
    listed = {p.info["category_tp"] for p in products}
    unassigned = [
        {
            "detector": d.label,
            "categoria": d.category,
            "score": round(d.score, 3),
            "box": [round(v) for v in d.box],
        }
        for i, d in enumerate(after_dets)
        if i not in assigned
        # una parte de un producto de la lista (los almohadones del sofá) no es inventada
        and not any(inside(d.box, after_dets[j].box) >= 0.6 for j in assigned)
        # ni lo que ya estaba en la foto original (un radiador, un placard)
        and not any(iou(_scaled(d.box, after, before), b.box) > 0.3 for b in before_dets)
    ]
    # Otra de una categoría de la lista puede ser el par de un producto (dos paños de cortina,
    # un juego de sillas): va aparte de las inventadas.
    extras = [e for e in unassigned if e["categoria"] not in listed]
    repeated = [e for e in unassigned if e["categoria"] in listed]
    found = [r for r in per_product if r["detectado"]]
    texts = [request, *CONTRAST]
    sims = models.align(texts, [after, before])
    rank_request = 1 + int((sims[1:, 0] > sims[0, 0]).sum())
    result = {
        "corrida": run_dir.name,
        "imagen": final.name,
        "generador": image_meta.get("generator"),
        "modelos": {"detector": DETECTOR, "embedder": EMBEDDER, "alineacion": ALIGNER},
        "productos": per_product,
        "fidelidad": {
            "productos": len(products),
            "detectados": len(found),
            "presencia": round(len(found) / len(products), 4) if products else None,
            "coseno_medio": round(float(np.mean([r["coseno"] for r in found])), 4)
            if found
            else None,
            "identificados@1": round(sum(r["puesto"] == 1 for r in found) / len(products), 4)
            if products
            else None,
            "mrr": round(
                float(np.mean([1 / r["puesto"] if r.get("puesto") else 0.0 for r in per_product])),
                4,
            )
            if products
            else None,
        },
        "inventadas": extras,
        "repetidas": repeated,
        "ambiente": preservation(
            before, after, [after_dets[i].box for i in assigned] + [e["box"] for e in unassigned]
        ),
        "pedido_imagen": {
            "pedido": request,
            "siglip_final": round(float(sims[0, 0]), 4),
            "siglip_vacia": round(float(sims[0, 1]), 4),
            "delta": round(float(sims[0, 0] - sims[0, 1]), 4),
            "puesto_entre_contrastes": rank_request,
            "contrastes": len(CONTRAST),
            "vacio_final_vs_original": round(float(sims[1, 0] - sims[1, 1]), 4),
        },
    }
    (run_dir / "6_metricas_imagen.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1)
    )
    contact_sheet(sheet, run_dir / "6_recortes.jpg")
    return result


def _scaled(box: Sequence[float], src: Image.Image, dst: Image.Image) -> tuple:
    sx, sy = dst.width / src.width, dst.height / src.height
    return (box[0] * sx, box[1] * sy, box[2] * sx, box[3] * sy)


def reference(
    cfg: Config, queries_path: Path, raw_dir: Path, out: Path, models: Models | None = None
) -> dict[str, Any]:
    """La vara de la fidelidad: la misma identificación (recorte → producto del catálogo de su
    tipo, DINOv3) con fotos reales, los ambientes IKEA de la evaluación. Cada recorte vale para
    los productos anotados en su ambiente de su grupo (el de la v0 y del retrieval por texto):
    hit@1 y MRR@10 sobre los recortes que tienen alguno."""
    from amoblai.dataset.ikea import IkeaDataset
    from amoblai.evaluation.metrics import bootstrap_ci
    from amoblai.evaluation.queries import load_queries
    from amoblai.evaluation.retrieval import product_group

    models = models or Models(Path(cfg.cache_dir) / "imagen")
    catalog = _catalog(cfg)
    groups = {pid: product_group(p) for pid, p in catalog.items()}
    labels = detector_labels()
    ds = IkeaDataset.load(raw_dir)
    rows, by_category = [], {}
    for room_id in load_queries(queries_path):
        room = ds.rooms[room_id]
        photo = Path(raw_dir) / room.path
        image = Image.open(photo).convert("RGB")
        dets = [d for d in models.detect(photo, labels) if d.score >= BOX_THRESHOLD]
        gt = [s for s in room.skus if s in catalog]
        if not dets:
            continue
        vecs = models.embed([crop(image, d.box) for d in dets])
        for d, v in zip(dets, vecs, strict=True):
            group = PHRASE_GROUP.get(d.label, d.category)
            if d.category in ("lamp", "deco") and d.label not in PHRASE_GROUP:
                continue
            relevant = {s for s in gt if groups[s] == group}
            if not relevant:
                continue
            category = catalog[next(iter(relevant))].category
            if category not in by_category:
                by_category[category] = _candidates(models, catalog, category)
            ident = rank_among(v, relevant, by_category[category])
            rows.append({"room_id": room_id, "detector": d.label, "grupo": group, **ident})
    hit1 = [float(r["rank"] == 1) for r in rows]
    rr = [1 / r["rank"] if r["rank"] and r["rank"] <= 10 else 0.0 for r in rows]
    rooms = [r["room_id"] for r in rows]
    per_group: dict[str, list[float]] = {}
    for r, h in zip(rows, hit1, strict=True):
        per_group.setdefault(r["grupo"], []).append(h)
    result = {
        "modelos": {"detector": DETECTOR, "embedder": EMBEDDER},
        "recortes": len(rows),
        "ambientes": len(set(rooms)),
        "hit@1": round(float(np.mean(hit1)), 4) if rows else None,
        "hit@1_ic95": [round(x, 4) for x in bootstrap_ci(hit1, rooms)] if rows else None,
        "mrr@10": round(float(np.mean(rr)), 4) if rows else None,
        "coseno_medio": round(float(np.mean([r["cos"] for r in rows])), 4) if rows else None,
        "hit@1_por_grupo": {
            g: [round(float(np.mean(v)), 4), len(v)] for g, v in sorted(per_group.items())
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({**result, "filas": rows}, ensure_ascii=False, indent=1))
    return result

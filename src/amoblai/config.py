"""Configuración del sistema: YAML validado con pydantic, más secretos desde `.env`.

Cada experimento es un YAML que puede heredar de otro con `extends:` y pisar
solo lo que cambia. Desde la CLI también se puede pisar cualquier campo con
`--set seccion.campo=valor`.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from amoblai.data.download import DEFAULT_COMMIT, DEFAULT_REPO

DEFAULT_CONFIG = Path("configs/base.yaml")


class _Section(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PathsConfig(_Section):
    raw_dir: Path = Path("data/raw/ikea")
    catalog_file: Path = Path("data/processed/catalog.json")
    chroma_dir: Path = Path("data/chroma")
    # Cachés locales y recomputables (detecciones, máscaras): no se commitean.
    cache_dir: Path = Path("data/cache")
    # Resultados que se commitean (el repo es privado).
    results_dir: Path = Path("resultados")
    runs_dir: Path = Path("resultados/corridas")
    # Imágenes generadas (API o a mano): cuestan plata o tiempo, se comparten por git.
    generations_dir: Path = Path("resultados/generaciones")
    spend_ledger: Path = Path("resultados/gastos.jsonl")
    empty_rooms_dir: Path = Path("ambientes_vacios")
    labels_file: Path = Path("anotaciones/estricto.jsonl")
    categories_file: Path = Path("configs/categories.yaml")
    pricing_file: Path = Path("configs/pricing.yaml")
    thresholds_file: Path = Path("configs/umbrales.yaml")


class DatasetConfig(_Section):
    repo: str = DEFAULT_REPO
    commit: str = DEFAULT_COMMIT
    # Tipos de ambiente (categories_dict.p) que entran en la evaluación del retriever.
    eval_room_types: list[str] = ["Living Room", "Dining"]


class EmbeddingConfig(_Section):
    # Alias de un preset (ver embeddings/registry.py) o "custom" con model_id.
    name: str = "dinov3"
    model_id: str | None = None
    batch_size: int = 16


class PreprocessConfig(_Section):
    """Preprocesamiento simétrico de imágenes de catálogo y recortes."""

    pad_to_square: bool = True
    # Margen blanco extra alrededor del objeto, como fracción del lado mayor.
    pad_margin: float = 0.05
    background_color: tuple[int, int, int] = (255, 255, 255)


class IndexConfig(_Section):
    # False: se indexa todo el catálogo con category="other" para lo que no está
    # en el alcance (ver docs/ARQUITECTURA.md, "Qué se indexa").
    scope_only: bool = False


class DetectionConfig(_Section):
    provider: Literal["grounding_dino", "owlv2"] = "grounding_dino"
    model_id: str | None = None
    box_threshold: float = 0.30
    # NMS dentro de la misma categoría y entre categorías (resuelve "chair" vs "armchair").
    nms_iou: float = 0.5
    cross_category_iou: float = 0.8
    min_area_frac: float = 0.004
    max_area_frac: float = 0.9
    max_detections: int = 12


class BackgroundConfig(_Section):
    method: Literal["none", "sam", "rembg"] = "none"
    sam_model_id: str = "facebook/sam-vit-base"
    rembg_model: str = "isnet-general-use"
    # Margen alrededor de la caja al recortar, como fracción del lado mayor de la caja.
    crop_margin: float = 0.04
    # Categorías a las que no se les quita el fondo (p. ej. alfombras tapadas por muebles).
    skip_categories: list[str] = []


class RetrievalConfig(_Section):
    top_k: int = 10
    category_filter: bool = True
    # "auto": umbral calibrado para la colección (configs/umbrales.yaml); None: sin umbral.
    threshold: float | Literal["auto"] | None = "auto"


class RerankConfig(_Section):
    # El reranking con un VLM queda para la iteración del Ejercicio 4.
    enabled: bool = False


class EditorConfig(_Section):
    provider: Literal["manual", "openai", "gemini", "dry_run"] = "manual"
    model: str = "gpt-image-2"
    quality: str = "medium"
    # "free": tamaño arbitrario múltiplo de 16 (gpt-image-2); "fixed": 1024², 1536x1024, 1024x1536.
    size_policy: Literal["free", "fixed"] = "free"
    input_fidelity: Literal["high", "low"] | None = None
    # Lado máximo de las fotos de producto que se mandan como referencia.
    reference_max_side: int = 768
    # Solo para el editor manual: app sugerida en las instrucciones (chatgpt | gemini).
    manual_app: str = "chatgpt"
    manual_wait: bool = True
    manual_timeout_s: float = 3600.0
    timeout_s: float = 300.0


class GenerationConfig(_Section):
    # Lado mayor de la imagen de trabajo (múltiplo de 16).
    working_max_side: int = 1536
    generator1: EditorConfig = Field(default_factory=EditorConfig)
    generator2: EditorConfig = Field(default_factory=EditorConfig)
    # Entrada del generador n.º 2: la imagen 1 o la foto original vacía.
    gen2_base: Literal["image1", "original"] = "image1"
    # "single": todos los muebles en una llamada; "per_item": uno por llamada con máscara.
    gen2_mode: Literal["single", "per_item"] = "single"
    mask_dilation: float = 0.10
    # Postprocesamiento: pegar solo lo de adentro de la máscara sobre la base.
    composite: bool = False
    feather_px: int = 12


class BudgetConfig(_Section):
    dry_run: bool = False
    max_calls_per_run: int | None = 20
    max_usd_per_run: float | None = 3.0
    # Tope acumulado sobre resultados/gastos.jsonl (todas las corridas).
    max_usd_total: float | None = 50.0


class EvalConfig(_Section):
    ks: list[int] = [1, 5, 10]
    bootstrap_samples: int = 1000
    seed: int = 0
    max_rooms: int | None = None
    # Guardar miniaturas de los recortes de cada corrida (para la app de flujo).
    save_crops: bool = True
    # Dilatación de las cajas que se excluyen del SSIM, como fracción del lado de la caja.
    ssim_box_dilation: float = 0.10


class AppConfig(_Section):
    name: str = "base"
    device: str = "auto"
    seed: int = 0
    paths: PathsConfig = Field(default_factory=PathsConfig)
    dataset: DatasetConfig = Field(default_factory=DatasetConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    preprocess: PreprocessConfig = Field(default_factory=PreprocessConfig)
    index: IndexConfig = Field(default_factory=IndexConfig)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    background: BackgroundConfig = Field(default_factory=BackgroundConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    rerank: RerankConfig = Field(default_factory=RerankConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    eval: EvalConfig = Field(default_factory=EvalConfig)


class Secrets(BaseSettings):
    """Claves de API. Se leen de variables de entorno o de `.env` (nunca se commitea)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    google_api_key: str | None = None
    hf_token: str | None = None

    @property
    def gemini_key(self) -> str | None:
        return self.gemini_api_key or self.google_api_key


def load_env(path: Path = Path(".env")) -> None:
    """Carga `.env` en `os.environ` (sin pisar lo que ya esté definido).

    LangSmith y Hugging Face leen sus variables directamente del entorno.
    """
    from dotenv import load_dotenv

    load_dotenv(path, override=False)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def _read_yaml_with_extends(path: Path, _seen: tuple[Path, ...] = ()) -> dict[str, Any]:
    path = path.resolve()
    if path in _seen:
        raise ValueError(f"Herencia circular de configs: {path}")
    data = yaml.safe_load(path.read_text()) or {}
    parent = data.pop("extends", None)
    if parent is None:
        return data
    parent_data = _read_yaml_with_extends(path.parent / parent, (*_seen, path))
    return deep_merge(parent_data, data)


def parse_override(expr: str) -> dict[str, Any]:
    """Convierte `a.b.c=valor` en `{"a": {"b": {"c": valor}}}` (valor parseado como YAML)."""
    if "=" not in expr:
        raise ValueError(f"Override inválido (se espera clave=valor): {expr!r}")
    key, raw = expr.split("=", 1)
    value: Any = yaml.safe_load(raw)
    for part in reversed(key.strip().split(".")):
        value = {part: value}
    return value


def load_config(path: Path | None = None, overrides: list[str] | None = None) -> AppConfig:
    data: dict[str, Any] = {}
    if path is None and DEFAULT_CONFIG.exists():
        path = DEFAULT_CONFIG
    if path is not None:
        data = _read_yaml_with_extends(Path(path))
    for expr in overrides or []:
        data = deep_merge(data, parse_override(expr))
    return AppConfig.model_validate(data)


def stable_hash(data: Any, length: int = 12) -> str:
    """Hash estable de estructuras JSON-serializables o modelos pydantic."""
    if isinstance(data, BaseModel):
        data = data.model_dump(mode="json")
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:length]

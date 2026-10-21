"""Hard limits a product must meet before the search ranks it: the type of product and that it
fits go as filters; style and taste go to the embeddings."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .kinds import KINDS


class Filters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # The products' `category` values (e.g. ["chair", "sofa"]); empty = any.
    categories: list[str] = Field(default_factory=list)
    # What it is for (rag/kinds.py, e.g. ["desk chair"]); empty = any. A product without a kind
    # passes when its type is one of those kinds' types.
    kinds: list[str] = Field(default_factory=list)
    # The most the product may measure, in centimetres; a product without its size passes.
    max_width_cm: float | None = None
    max_depth_cm: float | None = None
    max_height_cm: float | None = None

    def allows(self, item: dict) -> bool:
        if self.categories and item["category"] not in self.categories:
            return False
        if self.kinds:
            kind = item.get("kind")
            if kind is None and item["category"] not in {KINDS.get(k) for k in self.kinds}:
                return False
            if kind is not None and kind not in self.kinds:
                return False
        dims = item.get("dimensions_cm") or {}
        for axis in ("width", "depth", "height"):
            most = getattr(self, f"max_{axis}_cm")
            if most is not None and dims.get(axis) is not None and dims[axis] > most:
                return False
        return True

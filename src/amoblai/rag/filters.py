"""Hard limits a product must meet before the search ranks it: the type of product and that it
fits go as filters; style and taste go to the embeddings. `allows` checks one product (exact
search, whole_catalog mode); `where` says the same to ChromaDB (store.py)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from amoblai.catalog.kinds import KINDS


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

    def where(self) -> dict | None:
        """The same limits as a ChromaDB `where` (store.metadata_for: a missing kind is "", a
        missing size -1, so it passes any limit); None: no limit."""
        conds: list[dict] = []
        if self.categories:
            conds.append({"category": {"$in": list(self.categories)}})
        if self.kinds:
            by_kind = {"kind": {"$in": list(self.kinds)}}
            types = sorted({KINDS[k] for k in self.kinds if k in KINDS})
            no_kind = {"$and": [{"kind": ""}, {"category": {"$in": types}}]}
            conds.append({"$or": [by_kind, no_kind]} if types else by_kind)
        for axis in ("width", "depth", "height"):
            most = getattr(self, f"max_{axis}_cm")
            if most is not None:
                conds.append({axis: {"$lte": float(most)}})
        if not conds:
            return None
        return conds[0] if len(conds) == 1 else {"$and": conds}

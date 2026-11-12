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
    # The most the product may measure, in centimetres; a product without its size passes. With
    # both a width and a depth limit the product may be turned (a 200 x 300 rug fits a 300 x 220
    # spot): the catalogs don't agree on which side is the width (IKEA writes width x length as
    # the seller does, ABO puts the longer side first).
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

        def fits(axis: str, most: float | None) -> bool:
            return most is None or dims.get(axis) is None or dims[axis] <= most

        w, d = self.max_width_cm, self.max_depth_cm
        floor = fits("width", w) and fits("depth", d)
        if w is not None and d is not None:  # or turned a quarter
            floor = floor or (fits("width", d) and fits("depth", w))
        return floor and fits("height", self.max_height_cm)

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
        w, d = self.max_width_cm, self.max_depth_cm
        if w is not None and d is not None:  # as it is, or turned a quarter
            as_is = [{"width": {"$lte": float(w)}}, {"depth": {"$lte": float(d)}}]
            turned = [{"width": {"$lte": float(d)}}, {"depth": {"$lte": float(w)}}]
            conds.append({"$or": [{"$and": as_is}, {"$and": turned}]})
        else:
            conds += [
                {a: {"$lte": float(m)}} for a, m in (("width", w), ("depth", d)) if m is not None
            ]
        if self.max_height_cm is not None:
            conds.append({"height": {"$lte": float(self.max_height_cm)}})
        if not conds:
            return None
        return conds[0] if len(conds) == 1 else {"$and": conds}

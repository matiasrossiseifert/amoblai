"""Cajas delimitadoras y operaciones geométricas simples."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Box:
    """Caja en píxeles (x0, y0) arriba a la izquierda, (x1, y1) abajo a la derecha."""

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)

    def iou(self, other: Box) -> float:
        ix = max(0.0, min(self.x1, other.x1) - max(self.x0, other.x0))
        iy = max(0.0, min(self.y1, other.y1) - max(self.y0, other.y0))
        inter = ix * iy
        union = self.area + other.area - inter
        return inter / union if union > 0 else 0.0

    def clip(self, width: int, height: int) -> Box:
        return Box(
            max(0.0, min(self.x0, width)),
            max(0.0, min(self.y0, height)),
            max(0.0, min(self.x1, width)),
            max(0.0, min(self.y1, height)),
        )

    def expand(self, ratio: float, width: int | None = None, height: int | None = None) -> Box:
        """Agranda la caja `ratio` veces su lado mayor en cada dirección."""
        pad = ratio * max(self.width, self.height)
        box = Box(self.x0 - pad, self.y0 - pad, self.x1 + pad, self.y1 + pad)
        return box.clip(width, height) if width is not None and height is not None else box

    def scale(self, sx: float, sy: float) -> Box:
        return Box(self.x0 * sx, self.y0 * sy, self.x1 * sx, self.y1 * sy)

    def to_int(self) -> tuple[int, int, int, int]:
        return (int(self.x0), int(self.y0), round(self.x1), round(self.y1))

    def as_list(self) -> list[float]:
        return [round(self.x0, 1), round(self.y0, 1), round(self.x1, 1), round(self.y1, 1)]

    @classmethod
    def from_list(cls, values: list[float] | tuple[float, ...]) -> Box:
        x0, y0, x1, y1 = (float(v) for v in values)
        return cls(x0, y0, x1, y1)


def describe_location(box: Box, width: int, height: int) -> str:
    """Ubicación aproximada en palabras (en inglés, para los prompts del generador)."""
    cx, cy = box.center
    horiz = ["left", "center", "right"][min(2, int(3 * cx / max(width, 1)))]
    depth = ["back", "middle", "front"][min(2, int(3 * cy / max(height, 1)))]
    return f"{depth} {horiz}" if horiz != "center" else f"{depth} center"


def box_percent(box: Box, width: int, height: int) -> str:
    """Caja como porcentajes de la imagen, p. ej. 'x 10–45%, y 50–90%'."""
    return (
        f"x {100 * box.x0 / width:.0f}–{100 * box.x1 / width:.0f}%, "
        f"y {100 * box.y0 / height:.0f}–{100 * box.y1 / height:.0f}%"
    )

from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class Vector:
    x: float
    y: float

    def __add__(self, other: Vector) -> Vector:
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector) -> Vector:
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, other: int) -> Vector:
        return Vector(self.x * other, self.y * other)

    def __truediv__(self, other: int) -> Vector:
        return Vector(self.x / other, self.y / other)

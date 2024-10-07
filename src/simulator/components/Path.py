from simulator.typehints.component_types import Component, Point
import simulator.utils.helpers as helpers

from typing import List, Iterable


class Path(Component):
    def __init__(self, points: Iterable[Point], speed: float = 5):
        self.points: List[Point] = list(points)
        self.curr_point: int = 0
        self.speed: float = speed

    def __str__(self):
        return f"Path{self.points} at point {self.curr_point}"

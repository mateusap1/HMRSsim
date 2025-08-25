import esper
import logging

from simulator.components.Position import Position
from simulator.components.Velocity import Velocity

from simulator.typehints.dict_types import SystemArgs

from typing import Tuple, List


class MovementProcessor(esper.Processor):
    def __init__(
        self, minx: float, maxx: float, miny: float, maxy: float, sector_size: int = 50
    ):
        super().__init__()
        
        self.world: esper.World = self.world

        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy

        self.sector_size = sector_size
        self.logger = logging.getLogger(__name__)

        self.setup_ready = False

    def setup(self):
        # The Movement Processor is responsible for managing the tiling of the simulation
        # When it starts (which is after the simulation is loaded) it will initialize the sector
        # Of all entities that have a position
        # This is done just once in the first execution
        for _, (position,) in self.world.get_components(Position):
            position.sector = self.calculate_sector(position)

        self.setup_ready = True

    def get_move_ents(self) -> List[Tuple[int, Tuple[Position, Velocity]]]:
        # Returns every entity which has both of these components
        return self.world.get_components(Position, Velocity)

    def calculate_new_position(
        self, position: Position, velocity: Velocity, axis: int
    ) -> float:
        if not axis in [0, 1]:
            raise ValueError(
                f"Axis must be either 0 (x) or 1 (y), but received {axis}."
            )

        if axis == 0:
            return min(self.maxx - position.w, max(self.minx, position.x + velocity.x))
        else:
            return min(self.maxy - position.h, max(self.miny, position.y + velocity.y))

    def calculate_center(self, position: Position):
        return (position.x + position.w // 2, position.y + position.h // 2)

    def calculate_sector(self, position: Position):
        tiley = position.y // self.sector_size
        tilex = position.x // self.sector_size

        return (tiley * self.maxx) + tilex

    def calculate_adjacent_sectors(self, position: Position):
        return [
            (position.sector + dx + dy)
            for dx in [-1, -1, -1, 1, 1, 1, 0, 0, 0]
            for dy in [
                0,
                -self.maxx,
                +self.maxx,
                0,
                -self.maxx,
                +self.maxx,
                0,
                -self.maxx,
                +self.maxx,
            ]
        ]

    def update_position(self, position: Position, velocity: Velocity):
        posx = self.calculate_new_position(position, velocity, 0)
        posy = self.calculate_new_position(position, velocity, 1)

        moved_position = (posx, posy) != (position.x, position.y)
        moved_angle = velocity.alpha > 0.0

        position.changed = False

        if moved_position:
            position.changed = True
            position.x = posx
            position.y = posy
            position.center = self.calculate_center(position)
            position.sector = self.calculate_sector(position)
            position.adjacent_sectors = self.calculate_adjacent_sectors(position)

        if moved_angle:
            position.angle = (position.angle + velocity.alpha) % 360

    def process(self, _: SystemArgs):
        if not self.setup_ready:
            self.setup()

        for ent, (position, velocity) in self.get_move_ents():
            self.update_position(position, velocity)

    def add_sector_info(self, pos: Position):
        pos.sector = ((pos.y // self.sector_size) * self.maxx) + (
            pos.x // self.sector_size
        )

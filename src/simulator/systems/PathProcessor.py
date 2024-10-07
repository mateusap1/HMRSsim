import esper
import logging
from simulator.typehints.dict_types import SystemArgs

from simpy import FilterStore, Environment

from simulator.components.Path import Path
from simulator.components.Position import Position
from simulator.components.Velocity import Velocity
from simulator.components.ApproximationHistory import ApproximationHistory
from typing import List, Tuple, Dict
from simulator.typehints.component_types import (
    EVENT,
    EndOfPathPayload,
    EndOfPathTag,
    EndOfApproximationPayload,
    EndOfApproximationTag,
    Point,
)


class PathProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

        self.initial_velocity: Dict[int, Tuple[float, float]] = {}

        self.logger = logging.getLogger(__name__)

    def setup_initial_velocity(self, ent: int, velocity: Velocity):
        if ent not in self.initial_velocity:
            self.initial_velocity[ent] = (velocity.x, velocity.y)

    def get_event_store(self, kwargs: SystemArgs) -> FilterStore:
        event_store = kwargs.get("EVENT_STORE", None)
        if event_store is None:
            raise Exception("Can't find Event Store.")

        return event_store

    def get_environment(self, kwargs: SystemArgs) -> Environment:
        env = kwargs.get("ENV", None)
        if env is None:
            raise Exception("Can't find Environment.")

        return env

    def get_path_ents(self) -> List[Tuple[int, Tuple[Position, Velocity, Path]]]:
        return self.world.get_components(Position, Velocity, Path)

    def move_to_point(self, point: Point, pos: Position, vel: Velocity, path: Path):
        dx, dy = (point[0] - pos.center[0], point[1] - pos.center[1])

        vel.x = min(path.speed, dx) if dx > 0 else max(-path.speed, dx)
        vel.y = min(path.speed, dy) if dy > 0 else max(-path.speed, dy)

    def send_end_of_approximation_event(
        self, ent: int, position: Position, event_store: FilterStore, now: str
    ):
        history = self.world.component_for_entity(ent, ApproximationHistory)
        history.entity_final_approx_pos = position.center
        history.approximated = True

        end_of_approximation_event = EVENT(
            EndOfApproximationTag, EndOfApproximationPayload(ent, now)
        )
        event_store.put(end_of_approximation_event)

    def get_approximation_history(self, ent: int) -> ApproximationHistory:
        return self.world.component_for_entity(ent, ApproximationHistory)

    def handle_approximation_history(
        self, ent: int, position: Position, event_store: FilterStore, now: str
    ):
        if self.world.has_component(ent, ApproximationHistory):
            history = self.get_approximation_history(ent)
            if not history.approximated:
                history.entity_final_approx_pos = position.center
                history.approximated = True

                event_store.put(
                    EVENT(EndOfApproximationTag, EndOfApproximationPayload(ent, now))
                )

    def process(self, kwargs: SystemArgs):
        event_store = self.get_event_store(kwargs)
        env = self.get_environment(kwargs)

        for ent, (pos, vel, path) in self.get_path_ents():
            self.setup_initial_velocity(ent, vel)

            point = path.points[path.curr_point]
            at_point = point == pos.center

            if at_point:
                path.curr_point += 1

                reached_end = path.curr_point == len(path.points)
                if reached_end:
                    # Returns ent to velocity it had before path processor
                    vel.x, vel.y = self.initial_velocity[ent]

                    event_store.put(
                        EVENT(
                            EndOfPathTag,
                            EndOfPathPayload(ent, str(env.now), path=path.points),
                        )
                    )

                    self.world.remove_component(ent, Path)

                    # I don't think this should be handled here
                    # pos.changed = False

                    self.handle_approximation_history(
                        ent, pos, event_store, str(env.now)
                    )

                    self.logger.debug(
                        f"Removed Path component from {ent} (pos={pos.center}). Last point of path is {path.points[-1]}"
                    )
            else:
                self.move_to_point(point, pos, vel, path)

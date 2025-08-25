from simulator.typehints.dict_types import SystemArgs
from simulator.components.Position import Position
from simulator.components.Skeleton import Skeleton

from simpy import FilterStore, Environment
from typing import List, Callable
from esper import World

import json


class Seer:
    def __init__(self, consumers: List[Callable], scan_interval: float):
        self.consumers = consumers
        self.scan_interval = scan_interval
        self.msg_idx = 0

        self.event_store: FilterStore = None
        self.env: Environment = None

    def send_message(self, message: dict):
        for consumer in self.consumers:
            consumer(message, self.msg_idx)

        self.msg_idx += 1

    def start(self):
        simulation_skeleton = self.world.component_for_entity(1, Skeleton)
        self.send_message(
            {
                "timestamp": -1,
                "window_name": simulation_skeleton.id,
                "dimensions": json.loads(simulation_skeleton.style),
            }
        )

    def process(self, kwargs: SystemArgs):
        self.world = self._get_world(kwargs)
        self.event_store = self._get_event_store(kwargs)
        self.env = self._get_environment(kwargs)

        self.start()

        while True:
            message = {"timestamp": round(float(self.env.now), 3)}
            for ent, (skeleton, position) in self.world.get_components(Skeleton, Position):
                change_detected = skeleton.changed or position.changed
                if change_detected:
                    self._handle_object_change(skeleton, position, message)

            self.send_message(message)

            yield self.env.timeout(self.scan_interval)

    def _get_world(self, kwargs: SystemArgs) -> World:
        world = kwargs.get("WORLD")
        if world is None:
            raise ValueError("Can't find World.")
        return world

    def _get_event_store(self, kwargs: SystemArgs) -> FilterStore:
        event_store = kwargs.get("EVENT_STORE", None)
        if event_store is None:
            raise Exception("Can't find Event Store.")

        return event_store

    def _get_environment(self, kwargs: SystemArgs) -> Environment:
        env = kwargs.get("ENV", None)
        if env is None:
            raise Exception("Can't find Environment.")

        return env

    def _handle_object_change(
        self, skeleton: Skeleton, position: Position, message: dict
    ):
        message[skeleton.id] = {
            "value": skeleton.value,
            "x": position.x,
            "y": position.y,
            "width": position.w,
            "height": position.h,
            "style": skeleton.style,
        }

        skeleton.changed = False
        position.changed = False
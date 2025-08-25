from simulator.typehints.dict_types import SystemArgs
from simulator.typehints.component_types import (
    ObserverTag,
    ObserverPayload,
    ObserverChangeType,
    EVENT,
)
from simulator.components.Position import Position
from simulator.components.Skeleton import Skeleton

from simpy import FilterStore, Environment
from typing import List, Callable
from esper import World

import json


class WatcherDESProcessor:

    def __init__(self, consumers: List[Callable]):
        self.consumers = consumers
        self.msg_idx = 0

        self.event_store: FilterStore = None
        self.world: World = None
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
        self.event_store = self._get_event_store(kwargs)
        self.world = self._get_world(kwargs)
        self.env = self._get_environment(kwargs)

        self.start()

        while True:
            event = yield self.event_store.get(lambda e: e.type == ObserverTag)
            self._process_event(event)

    def _get_event_store(self, kwargs: SystemArgs) -> FilterStore:
        event_store = kwargs.get("EVENT_STORE", None)
        if event_store is None:
            raise Exception("Can't find Event Store.")

        return event_store

    def _get_world(self, kwargs: SystemArgs) -> World:
        world = kwargs.get("WORLD")
        if world is None:
            raise ValueError("Can't find World.")
        return world

    def _get_environment(self, kwargs: SystemArgs) -> Environment:
        env = kwargs.get("ENV", None)
        if env is None:
            raise Exception("Can't find Environment.")

        return env

    def _handle_object_change(self, ent: int, message: dict):
        if not self.world.has_components(ent, Position, Skeleton):
            return

        position: Position = self.world.component_for_entity(ent, Position)
        skeleton: Skeleton = self.world.component_for_entity(ent, Skeleton)

        message[skeleton.id] = {
            "value": skeleton.value,
            "x": position.x,
            "y": position.y,
            "width": position.w,
            "height": position.h,
            "style": skeleton.style,
        }

    def _process_event(self, event: EVENT):
        if event.type == ObserverTag:
            payload: ObserverPayload = event.payload

            message = {}
            for change in payload.changes:
                change_detected = False
                for c, t in change.changes:
                    if isinstance(c, Position) or isinstance(c, Skeleton):
                        # TODO: Handle deletes
                        if t in [ObserverChangeType.added, ObserverChangeType.modified]:
                            change_detected = True

                if change_detected:
                    self._handle_object_change(change.ent, message)

            if message != {}:
                message["timestamp"] = round(payload.timestamp, 3)
                self.send_message(message)

                # change_detected = any(
                #     [
                #         isinstance(c, Position) or isinstance(c, Skeleton)
                #         for (c, _) in change.changes
                #     ]
                # )
                # if change_detected:

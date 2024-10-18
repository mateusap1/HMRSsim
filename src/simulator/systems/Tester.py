from simulator.typehints.dict_types import SystemArgs
from simulator.typehints.component_types import (
    ObserverTag,
    ObserverPayload,
    EVENT,
    ObserverChangeType,
)

from simulator.components.Position import Position

from simpy import FilterStore, Environment

from typing import List, Tuple, Callable

from enum import Enum

import math


class TesterState(Enum):
    __test__ = False

    SUCCESS = 0
    FAILURE = 1
    RUNNING = 2


class RequireState(Enum):
    SUCCESS = 0
    FAILURE = 1
    CONTINUE = 2


class NearPosition:

    def __init__(self, ent: int, position: Tuple[float, float], tolerance: float):
        self.ent = ent
        self.position = position
        self.tolerance = tolerance

    def _near_position(self, actual: Tuple[float, float]):
        return (actual[0] - self.position[0]) ** 2 + (
            actual[1] - self.position[1]
        ) ** 2 <= self.tolerance**2

    def requirement(self, payload: ObserverPayload) -> RequireState:
        for ent, changes in payload.changes:
            if ent == self.ent:
                for component, change_type in changes:
                    if isinstance(component, Position) and change_type in [
                        ObserverChangeType.modified,
                        ObserverChangeType.added,
                    ]:
                        if self._near_position((component.x, component.y)):
                            return RequireState.SUCCESS

        return RequireState.CONTINUE


class TesterDESProcessor:
    __test__ = False

    def __init__(self, requirements: List[Callable[[ObserverPayload], RequireState]]):
        # A requirement is a function which expects ObserverPayload
        # and returns either SUCCESS, CONTINUE or FAIL.

        # Requirements are sequential, the next requirement will only
        # be verified if the last one returned SUCCESS.

        # A tester is successful, if all requirements return SUCCESS
        # A tester fails if any requirement returns FAIL or the
        # simulation ends without all requirements returning
        # SUCCESS

        self.requirements = requirements
        self.requirement_counter = 0
        self.state: TesterState = TesterState.RUNNING

    def finish(self):
        if self.state == TesterState.RUNNING:
            self.state = TesterState.FAILURE

    def process(self, kwargs: SystemArgs):
        event_store = self._get_event_store(kwargs)

        while True:
            if self.requirement_counter == len(self.requirements):
                self.state = TesterState.SUCCESS

            if self.state != TesterState.RUNNING:
                break

            event = yield event_store.get(lambda e: e.type == ObserverTag)
            self._process_event(event)

    def _process_event(self, event: EVENT):
        requirement_result = self.requirements[self.requirement_counter](event.payload)
        if requirement_result == RequireState.SUCCESS:
            self.requirement_counter += 1
        elif requirement_result == RequireState.FAILURE:
            self.state = TesterState.FAILURE

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

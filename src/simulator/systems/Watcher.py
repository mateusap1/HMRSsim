from simulator.typehints.dict_types import SystemArgs
from simulator.typehints.component_types import ObserverTag, EVENT

from simpy import FilterStore, Environment

from typing import List
from simulator.typehints.component_types import ObserverPayload


class WatcherDESProcessor:

    def __init__(self):
        self.observer_memory: List[ObserverPayload] = []

    def process(self, kwargs: SystemArgs):
        event_store = self._get_event_store(kwargs)

        while True:
            event = yield event_store.get(lambda e: e.type == ObserverTag)
            self._process_event(event)

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

    def _process_event(self, event: EVENT):
        self.observer_memory.append(event.payload)

    def _print_memory(self):
        print("Memory:", self.observer_memory)

from simulator.typehints.component_types import (
    Component,
    EVENT,
    ObserverTag,
    ObserverPayload,
    ObserverChange,
    ObserverChangeType,
)
from simulator.typehints.dict_types import SystemArgs

from typing import List, Dict, Type, Tuple
from collections import defaultdict

from simpy import FilterStore, Environment

import esper


class ObserverProcessor(esper.Processor):
    def __init__(self, components: List[Type[Component]]):
        super().__init__()  # Is this necessary?

        self.components = components
        self.previous_state = {}

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

    def _components_order(self) -> Dict[Type[Component], int]:
        components_order = {}
        for i, component in enumerate(self.components):
            components_order[component] = i

        return components_order

    def _get_ents(self) -> Dict[int, List[Component]]:
        # This must respect the self.components order.

        ents = defaultdict(list)
        for comptype in self.components:
            for ent, component in self.world.get_component(comptype):
                ents[ent].append(component)

        return dict(ents)

    def _get_components_change(
        self, old: List[Component], new: List[Component]
    ) -> List[Tuple[Component, ObserverChangeType]]:
        # This algorithm assumes that the lists respects the
        # order defined here. This assumption holds true
        # depending on _get_ents.

        components_order = self._components_order()

        old_count = 0
        old_terminated = len(old) == 0

        new_count = 0
        new_terminated = len(new) == 0

        changes: List[Tuple[Component, ObserverChangeType]] = []
        while (not old_terminated) or (not new_terminated):
            if old_terminated:
                changes.append((new[new_count], ObserverChangeType.added))
                new_count += 1
            elif new_terminated:
                changes.append((old[old_count], ObserverChangeType.removed))
                old_count += 1
            else:
                if (
                    components_order[type(old[old_count])]
                    == components_order[type(new[new_count])]
                ):
                    if old[old_count] != new[new_count]:
                        changes.append((new[new_count], ObserverChangeType.modified))

                    new_count += 1
                    old_count += 1
                else:
                    if (
                        components_order[type(old[old_count])]
                        < components_order[type(new[new_count])]
                    ):
                        changes.append((old[old_count], ObserverChangeType.removed))
                        old_count += 1
                    else:
                        changes.append((new[new_count], ObserverChangeType.added))
                        new_count += 1

            old_terminated = old_count == len(old)
            new_terminated = new_count == len(new)

        return changes

    def _get_state_change(
        self, new_state: Dict[int, List[Component]]
    ) -> Dict[int, List[Tuple[Component, ObserverChangeType]]]:
        # In cases where the entity dissapeared, we always assume
        # all of its components were removed. In reality, the
        # entity could have been destroyed instead.

        state_change = {}

        # This is so we entities which dissapeared or had their
        # components removed are also tracked.
        for ent in self.previous_state:
            if not ent in new_state:
                new_state[ent] = []

        for ent, components in new_state.items():
            if ent in self.previous_state:
                state_change[ent] = self._get_components_change(
                    self.previous_state[ent], components
                )
            else:
                state_change[ent] = components

        return state_change

    def process(self, kwargs: SystemArgs):
        # For improved performance, maybe make this a DES like the
        # Seer Plugin, maybe it is not necessary to check for changes
        # at every tick.

        # Also, create Observable component, and only look at entities
        # with Observable component instead of passing observed
        # components as an argument

        event_store = self._get_event_store(kwargs)
        env = self._get_environment(kwargs)

        new_state = self._get_ents()
        state_change = self._get_state_change(new_state)
        self.previous_state = new_state

        if len(state_change) > 0:
            event_store.put(
                EVENT(
                    ObserverTag,
                    ObserverPayload(
                        env.now,
                        [
                            ObserverChange(ent, change)
                            for ent, change in state_change.items()
                        ],
                    ),
                )
            )
        
        
        

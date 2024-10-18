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

import esper


class ObserverProcessor(esper.Processor):
    def __init__(self, components: List[Type[Component]]):
        self.components = components
        self.previous_state = {}

    def _components_order(self) -> Dict[Type[Component], int]:
        components_order = {}
        for i, component in enumerate(self.components):
            components_order[component] = i

        return components_order

    def _get_ents(self) -> Dict[int, List[Component]]:
        ents = {}
        for comptype in self.components:
            world_ents = self.world.get_component(comptype)
            for ent, component in world_ents:
                if ent in ents:
                    ents[ent].append(component)
                else:
                    ents[ent] = [component]

        return ents

    def _get_components_change(
        self, old: List[Component], new: List[Component]
    ) -> List[Tuple[Component, ObserverChangeType]]:
        components_order = self._components_order()

        old_count = 0
        old_terminated = False

        new_count = 0
        new_terminated = False

        changes: List[Tuple[Component, ObserverChangeType]] = []
        while not old_terminated or not new_terminated:
            if old_count == len(old):
                old_terminated = True
            if new_count == len(new):
                new_terminated = True

            if old_terminated and new_terminated:
                break

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

        return changes

    def _get_state_change(self) -> Dict[int, Tuple[List[Component], List[Component]]]:
        """Returns a dictionary mapping the entities which
        changed with a tuple containing the removed components
        and the added (or modified) components"""

        state_change = {}
        new_state = self._get_ents()
        for ent in self.previous_state:
            if not ent in new_state:
                new_state[ent] = []

        for ent, components in new_state.items():
            if ent in self.previous_state:
                removed, added = self._get_components_change(
                    self.previous_state[ent], components
                )
                state_change[ent] = (removed, added)
            else:
                state_change[ent] = ([], components)

        return state_change

    def process(self, kwargs: SystemArgs):
        event_store = self.get_event_store(kwargs)
        env = self.get_environment(kwargs)

        state_change = self._get_state_change()
        for ent, components in state_change.items():
            pass
            # event_store.put(
            #     EVENT(
            #         str(env.now),
            #         ObserverTag,
            #         ObserverPayload(ent, str(env.now), path=path.points),
            #     )
            # )

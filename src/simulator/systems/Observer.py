from simulator.typehints.component_types import Component
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
    ) -> Tuple[List[Component], List[Component]]:
        components_order = self._components_order()

        old_count = 0
        old_terminated = False

        new_count = 0
        new_terminated = False

        new_added = []
        old_removed = []
        while not old_terminated or not new_terminated:
            if old_count == len(old):
                old_terminated = True
            if new_count == len(new):
                new_terminated = True

            if old_terminated and new_terminated:
                break

            if old_terminated:
                new_added.append(new[new_count])
                new_count += 1
            elif new_terminated:
                old_removed.append(old[old_count])
                old_count += 1
            else:
                if (
                    components_order[type(old[old_count])]
                    == components_order[type(new[new_count])]
                ):
                    print(old[old_count], new[new_count])
                    print(old[old_count] == new[new_count])
                    if old[old_count] != new[new_count]:
                        old_removed.append(old[old_count])
                        new_added.append(new[new_count])

                    new_count += 1
                    old_count += 1
                else:
                    if (
                        components_order[type(old[old_count])]
                        < components_order[type(new[new_count])]
                    ):
                        old_removed.append(old[old_count])
                        old_count += 1
                    else:
                        new_added.append(new[new_count])
                        new_count += 1

        return old_removed, new_added

    def _get_state_change(self) -> Dict[int, List[Component]]:
        new_state = self._get_ents()
        for ent, components in new_state:
            if ent in self.previous_state:
                pass

    # event_store.put(
    #     EVENT(
    #         EndOfPathTag,
    #         EndOfPathPayload(ent, str(env.now), path=path.points),
    #     )
    # )

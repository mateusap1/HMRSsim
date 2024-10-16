from simulator.typehints.component_types import Component
from typing import List, Dict, Type

import esper


class ObserverProcessor(esper.Processor):
    def __init__(self, components: List[Type[Component]]):
        self.components = components

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

    # event_store.put(
    #     EVENT(
    #         EndOfPathTag,
    #         EndOfPathPayload(ent, str(env.now), path=path.points),
    #     )
    # )
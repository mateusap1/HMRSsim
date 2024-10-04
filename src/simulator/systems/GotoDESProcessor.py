import esper
import logging

from typing import NamedTuple, List, Union, Callable, Optional

from simulator.components.Map import Map
from simulator.typehints.component_types import Point
from simulator.typehints.dict_types import SystemArgs

from esper import World
from simpy import FilterStore

import simulator.components.Script as scriptComponent
from simulator.components.Path import Path
from simulator.components.Position import Position
from simulator.components.Script import Script

from simulator.systems.NavigationSystem import find_route

from simulator.typehints.component_types import (
    EVENT,
    ERROR,
    GotoPoiPayload,
    GotoPosPayload,
    GotoPoiEventTag,
    GotoPosEventTag,
)

from simulator.systems.PathProcessor import EndOfPathTag
from simulator.utils.Navigation import PathNotFound, add_nodes_from_points

GotoInstructionId = "Go"
NavigationFunction = Callable[[Map, Point, Point], Path]

PathErrorTag = "PathError"
PathErrorPayload = NamedTuple(
    "PathErrorPayload", [("error", str), ("entity", int), ("best_path", Path)]
)
PathNotFoundTag = "PathNotFound"
PoiNotFoundTag = "PoiNotFound"


class GotoDESProcessor:
    def __init__(self, navigation_function: NavigationFunction = find_route):
        self.logger = logging.getLogger(__name__)

        self.nav_function = navigation_function

    def get_event_store(self, kwargs: SystemArgs) -> FilterStore:
        event_store = kwargs.get("EVENT_STORE", None)
        if event_store is None:
            raise Exception("Can't find Event Store.")

        return event_store

    def get_world(self, kwargs: SystemArgs) -> World:
        world = kwargs.get("WORLD", None)
        if world is None:
            raise Exception("Can't find World.")

        return world

    def get_event_target(
        self,
        world_map: Map,
        event_type: str,
        event_payload: Union[GotoPoiPayload, GotoPosPayload],
    ) -> Optional[Point]:
        if event_type == GotoPoiEventTag:
            try:
                return world_map.pois[event_payload.target]
            except KeyError:
                return None

        return tuple(map(lambda p: float(p), event_payload.target))

    def add_path_to_ent(
        self, ent: int, world: World, world_map: Map, source: Point, target: Point
    ):
        path = self.nav_function(world_map, source, target)
        add_nodes_from_points(world_map, path.points)

        world.add_component(ent, path)

        self.logger.debug(f"Added Path component to entity {ent} - {path}")

    def handle_target_error(
        self, event_store: FilterStore, payload: Union[GotoPoiPayload, GotoPosPayload]
    ):
        self.logger.error(f"POI {payload.target} does not exist in map.")
        event_store.put(
            ERROR(
                PathErrorTag,
                payload.entity,
                PathErrorPayload(PoiNotFoundTag, payload.entity, payload.target),
            )
        )

    def handle_path_error(
        self,
        event_store: FilterStore,
        payload: Union[GotoPoiPayload, GotoPosPayload],
        error: PathNotFound,
    ):
        self.logger.warning(
            f"Failed to go to point (entity {payload.entity}) - {error.message}"
        )
        self.logger.warning(f"Best path - {error.partial_path}")

        event_store.put(
            ERROR(
                PathErrorTag,
                payload.entity,
                PathErrorPayload(PathNotFoundTag, payload.entity, error.partial_path),
            )
        )

    def process_event(
        self, world: World, world_map: Map, event_store: FilterStore, event: EVENT
    ):
        payload: Union[GotoPoiPayload, GotoPosPayload] = event.payload
        target = self.get_event_target(world_map, event.type, payload)
        if target is None:
            self.handle_target_error(event_store, payload)
            return

        # Position of entity
        entity_pos = world.component_for_entity(payload.entity, Position)
        source = entity_pos.center

        if target == source:
            self.logger.warning("Already at destination.")
            return

        try:
            self.add_path_to_ent(payload.entity, world, world_map, source, target)
        except PathNotFound as error:
            self.handle_path_error(event_store, payload, error)

    def process(self, kwargs: SystemArgs):
        event_store = self.get_event_store(kwargs)
        world = self.get_world(kwargs)
        world_map = world.component_for_entity(1, Map)

        while True:
            # Gets next goto event
            event = yield event_store.get(
                lambda ev: ev.type in [GotoPoiEventTag, GotoPosEventTag]
            )

            self.process_event(world, world_map, event_store, event)


# Functions that handle instructions
# A function returns the state of the Script component after executing
def goInstruction(
    ent: int, args: List[str], script: scriptComponent.Script, event_store: FilterStore
) -> scriptComponent.States:
    if len(args) == 1:
        payload = GotoPoiPayload(ent, args[0])
        new_event = EVENT(GotoPoiEventTag, payload)
    elif len(args) == 2:
        payload = GotoPosPayload(ent, [float(args[0]), float(args[1])])
        new_event = EVENT(GotoPosEventTag, payload)
    else:
        raise Exception("GO instruction failed. Go <poi> OR Go <x> <y>")
    event_store.put(new_event)
    # Needs to block the script
    if script:
        script.state = scriptComponent.States.BLOCKED
        script.expecting.append(EndOfPathTag)
        return script.state


def handle_PathError(payload: PathErrorPayload, kwargs: SystemArgs):
    logger = logging.getLogger(__name__)

    if payload.error == PathNotFoundTag:
        world: esper.World = kwargs.get("WORLD")
        logger.info(f"Add best path {payload.best_path} to entity {payload.entity}")
        world.add_component(payload.entity, payload.best_path)
        # Update the script
        script = world.component_for_entity(payload.entity, Script)
        script.logs.append(f"Add best path {payload.best_path}.")
    else:
        logger.error(f"Can't solve POI not found. Missing POI is {payload.best_path}")

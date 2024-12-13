import logging
from typing import NamedTuple, List, Union, Callable, Optional
from dataclasses import dataclass

import esper
from simpy import FilterStore

from simulator.components.Map import Map
from simulator.components.Path import Path
from simulator.components.Position import Position
from simulator.components.Script import Script, States as ScriptStates
from simulator.typehints.component_types import Point, EVENT, ERROR, GotoPoiPayload, GotoPosPayload, GotoPoiEventTag, GotoPosEventTag
from simulator.typehints.dict_types import SystemArgs
from simulator.systems.PathProcessor import EndOfPathTag
from simulator.systems.NavigationSystem import find_route
from simulator.utils.Navigation import PathNotFound, add_nodes_from_points

GotoInstructionId = "Go"
NavigationFunction = Callable[[Map, Point, Point], Path]

PathErrorTag = "PathError"
PathNotFoundTag = "PathNotFound"
PoiNotFoundTag = "PoiNotFound"

@dataclass
class PathErrorPayload:
    error: str
    entity: int
    best_path: Union[Path, str]

class GotoDESProcessor:
    def __init__(self, navigation_function: NavigationFunction = find_route):
        self.logger = logging.getLogger(__name__)
        self.nav_function = navigation_function

    def process(self, kwargs: SystemArgs):
        event_store = self._get_event_store(kwargs)
        world = self._get_world(kwargs)
        world_map = world.component_for_entity(1, Map)

        while True:
            event = yield event_store.get(lambda ev: ev.type in [GotoPoiEventTag, GotoPosEventTag])
            
            self.logger.debug("Received GoToPos event. Processing...")
            self._process_event(world, world_map, event_store, event)

    def _get_event_store(self, kwargs: SystemArgs) -> FilterStore:
        event_store = kwargs.get("EVENT_STORE")
        if event_store is None:
            raise ValueError("Can't find Event Store.")
        return event_store

    def _get_world(self, kwargs: SystemArgs) -> esper.World:
        world = kwargs.get("WORLD")
        if world is None:
            raise ValueError("Can't find World.")
        return world

    def _get_event_target(self, world_map: Map, event_type: str, event_payload: Union[GotoPoiPayload, GotoPosPayload]) -> Optional[Point]:
        if event_type == GotoPoiEventTag:
            return world_map.pois.get(event_payload.target)
        return tuple(map(float, event_payload.target))

    def _add_path_to_ent(self, ent: int, world: esper.World, world_map: Map, source: Point, target: Point):
        path = self.nav_function(world_map, source, target)
        add_nodes_from_points(world_map, path.points)
        world.add_component(ent, path)
        self.logger.debug(f"Added Path component to entity {ent} - {path}")

    def _handle_target_error(self, event_store: FilterStore, payload: Union[GotoPoiPayload, GotoPosPayload]):
        self.logger.error(f"POI {payload.target} does not exist in map.")
        event_store.put(ERROR(PathErrorTag, payload.entity, PathErrorPayload(PoiNotFoundTag, payload.entity, payload.target)))

    def _handle_path_error(self, event_store: FilterStore, payload: Union[GotoPoiPayload, GotoPosPayload], error: PathNotFound):
        self.logger.warning(f"Failed to go to point (entity {payload.entity}) - {error.message}")
        self.logger.warning(f"Best path - {error.partial_path}")
        event_store.put(ERROR(PathErrorTag, payload.entity, PathErrorPayload(PathNotFoundTag, payload.entity, error.partial_path)))

    def _process_event(self, world: esper.World, world_map: Map, event_store: FilterStore, event: EVENT):
        payload: Union[GotoPoiPayload, GotoPosPayload] = event.payload
        target = self._get_event_target(world_map, event.type, payload)
        
        if target is None:
            self._handle_target_error(event_store, payload)
            return

        entity_pos = world.component_for_entity(payload.entity, Position)
        source = entity_pos.center

        if target == source:
            self.logger.warning("Already at destination.")
            return

        try:
            self._add_path_to_ent(payload.entity, world, world_map, source, target)
        except PathNotFound as error:
            self._handle_path_error(event_store, payload, error)

def go_instruction(ent: int, args: List[str], script: Script, event_store: FilterStore) -> ScriptStates:
    if len(args) == 1:
        payload = GotoPoiPayload(ent, args[0])
        new_event = EVENT(GotoPoiEventTag, payload)
    elif len(args) == 2:
        payload = GotoPosPayload(ent, [float(args[0]), float(args[1])])
        new_event = EVENT(GotoPosEventTag, payload)
    else:
        raise ValueError("GO instruction failed. Usage: Go <poi> OR Go <x> <y>")
    
    event_store.put(new_event)
    
    if script:
        script.state = ScriptStates.BLOCKED
        script.expecting.append(EndOfPathTag)
    
    return script.state if script else None

def handle_path_error(payload: PathErrorPayload, kwargs: SystemArgs):
    logger = logging.getLogger(__name__)

    if payload.error == PathNotFoundTag:
        world: esper.World = kwargs.get("WORLD")
        logger.info(f"Add best path {payload.best_path} to entity {payload.entity}")
        world.add_component(payload.entity, payload.best_path)
        script = world.component_for_entity(payload.entity, Script)
        script.logs.append(f"Add best path {payload.best_path}.")
    else:
        logger.error(f"Can't solve POI not found. Missing POI is {payload.best_path}")
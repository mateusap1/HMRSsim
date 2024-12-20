from simulator.systems.GotoDESProcessor import GotoDESProcessor

from simulator.components.Map import Map
from simulator.components.Velocity import Velocity
from simulator.components.Position import Position

from simulator.typehints.component_types import (
    EVENT,
    GotoPoiEventTag,
    GotoPoiPayload,
    GotoPosEventTag,
    GotoPosPayload,
)

from simulator.utils.Navigation import POI, PathNotFound

from unittest.mock import MagicMock

import esper
import simpy


HOSPITAL_MAP = Map(
    nodes={
        (510.0, 90.0): [(490.0, 90.0)],
        (510.0, 230.0): [(510.0, 290.0)],
        (490.0, 90.0): [(370.0, 90.0), (50.0, 90.0), (510.0, 90.0)],
        (370.0, 90.0): [(490.0, 90.0), (370.0, 290.0)],
        (370.0, 290.0): [(370.0, 90.0), (510.0, 290.0), (90.0, 290.0)],
        (510.0, 290.0): [(370.0, 290.0), (90.0, 290.0), (510.0, 230.0)],
        (90.0, 230.0): [(90.0, 290.0)],
        (90.0, 290.0): [(510.0, 290.0), (370.0, 290.0), (90.0, 230.0)],
        (50.0, 90.0): [(490.0, 90.0)],
    },
    pois=[
        POI("medRoom", (519.5, 245.0)),
        POI("patientRoom", (75.0, 225.0)),
        POI("robotHome", (500.0, 80.0)),
    ],
)


def test_process_event():
    processor = GotoDESProcessor()

    world = esper.World()

    world.create_entity(HOSPITAL_MAP)
    robot = world.create_entity(Velocity(x=0.0, y=0.0), Position(x=0.0, y=0.0))

    event_store = simpy.FilterStore(simpy.Environment())
    event = EVENT(GotoPoiEventTag, GotoPoiPayload(robot, "patientRoom"))
    event_store.put(event)

    processor._get_event_target = MagicMock(return_value=(75.0, 225.0))
    processor._add_path_to_ent = MagicMock()

    processor._process_event(world, HOSPITAL_MAP, event_store, event)

    processor._get_event_target.assert_called_with(
        HOSPITAL_MAP, GotoPoiEventTag, GotoPoiPayload(robot, "patientRoom")
    )
    processor._add_path_to_ent.assert_called_with(
        robot, world, HOSPITAL_MAP, (0.0, 0.0), (75.0, 225.0)
    )


def test_process_event_no_target():
    processor = GotoDESProcessor()

    world = esper.World()

    world.create_entity(HOSPITAL_MAP)
    robot = world.create_entity(Velocity(x=0.0, y=0.0), Position(x=0.0, y=0.0))

    event_store = simpy.FilterStore(simpy.Environment())
    event = EVENT(GotoPoiEventTag, GotoPoiPayload(robot, "patientRoom"))
    event_store.put(event)

    processor._get_event_target = MagicMock(return_value=None)
    processor._handle_target_error = MagicMock()

    processor._process_event(world, HOSPITAL_MAP, event_store, event)

    processor._get_event_target.assert_called_with(
        HOSPITAL_MAP, GotoPoiEventTag, GotoPoiPayload(robot, "patientRoom")
    )
    processor._handle_target_error.assert_called_with(
        event_store, GotoPoiPayload(robot, "patientRoom")
    )


def test_process_event_path_not_found():
    processor = GotoDESProcessor()

    world = esper.World()

    world.create_entity(HOSPITAL_MAP)
    robot = world.create_entity(Velocity(x=0.0, y=0.0), Position(x=0.0, y=0.0))

    event_store = simpy.FilterStore(simpy.Environment())
    event = EVENT(GotoPoiEventTag, GotoPoiPayload(robot, "patientRoom"))
    event_store.put(event)

    path_error = PathNotFound((0.0, 0.0), (75.0, 225.0), None)

    processor._get_event_target = MagicMock(return_value=(75.0, 225.0))
    processor._add_path_to_ent = MagicMock(side_effect=path_error)
    processor._handle_path_error = MagicMock()

    processor._process_event(world, HOSPITAL_MAP, event_store, event)

    processor._get_event_target.assert_called_with(
        HOSPITAL_MAP, GotoPoiEventTag, GotoPoiPayload(robot, "patientRoom")
    )
    processor._handle_path_error.assert_called_with(
        event_store, GotoPoiPayload(robot, "patientRoom"), path_error
    )


def test_get_event_target():
    world = esper.World()

    wmap = HOSPITAL_MAP
    world.create_entity(wmap)

    processor = GotoDESProcessor()
    assert processor._get_event_target(
        wmap, GotoPoiEventTag, GotoPoiPayload(0, "patientRoom")
    ) == (75.0, 225.0)

    assert processor._get_event_target(
        wmap, GotoPoiEventTag, GotoPoiPayload(0, "robotHome")
    ) == (500.0, 80.0)

    assert (
        processor._get_event_target(
            wmap, GotoPoiEventTag, GotoPoiPayload(0, "nonexistent")
        )
        is None
    )

from simulator.systems.GotoDESProcessor import GotoDESProcessor
from simulator.components.Map import Map
from simulator.typehints.component_types import (
    EVENT,
    GotoPoiEventTag,
    GotoPoiPayload,
    GotoPosEventTag,
    GotoPosPayload,
)

from simulator.utils.Navigation import Node, POI

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

    wmap = HOSPITAL_MAP
    world.add_component(wmap)

    event_store = simpy.FilterStore(simpy.Environment())

    processor.process_event(
        world,
        wmap,
        event_store,
        EVENT(GotoPoiEventTag, GotoPoiPayload(0, "patientRoom")),
    )


def test_get_event_target():
    world = esper.World()

    wmap = HOSPITAL_MAP
    world.create_entity(wmap)

    processor = GotoDESProcessor()
    assert processor.get_event_target(
        wmap, GotoPoiEventTag, GotoPoiPayload(0, "patientRoom")
    ) == (75.0, 225.0)

    assert processor.get_event_target(
        wmap, GotoPoiEventTag, GotoPoiPayload(0, "robotHome")
    ) == (500.0, 80.0)

    assert processor.get_event_target(
        wmap, GotoPoiEventTag, GotoPoiPayload(0, "nonexistent")
    ) is None

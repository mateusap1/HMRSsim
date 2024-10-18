from simulator.systems.Observer import ObserverProcessor

from simulator.components.Velocity import Velocity
from simulator.components.Position import Position
from simulator.components.Path import Path
from simulator.components.Map import Map

from simulator.typehints.component_types import (
    EVENT,
    ObserverPayload,
    ObserverChange,
    ObserverTag,
    ObserverChangeType,
)

from unittest.mock import MagicMock, PropertyMock


import esper
import simpy


def test_observer_get_ents():
    world = esper.World()

    vel1 = Velocity(x=0.0, y=0.0)
    vel2 = Velocity(x=1.0, y=1.0)
    position = Position(x=0.0, y=0.0)

    ent1 = world.create_entity(vel1, position)
    ent2 = world.create_entity(vel2)

    obs = ObserverProcessor([Velocity])
    world.add_processor(obs)
    assert obs._get_ents() == {ent1: [vel1], ent2: [vel2]}
    world.remove_processor(obs)

    obs = ObserverProcessor([Position])
    world.add_processor(obs)
    assert obs._get_ents() == {ent1: [position]}
    world.remove_processor(obs)

    obs = ObserverProcessor([Velocity, Position])
    world.add_processor(obs)
    assert obs._get_ents() == {ent1: [vel1, position], ent2: [vel2]}


def test_get_components_change():
    obs = ObserverProcessor([Velocity, Position, Path, Map])

    vel1 = Velocity(x=0.0, y=0.0)
    vel12 = Velocity(x=0.0, y=0.0)
    vel2 = Velocity(x=1.0, y=1.0)

    pos1 = Position(x=0.0, y=0.0)
    pos12 = Position(x=0.0, y=0.0)
    pos2 = Position(x=1.0, y=1.0)

    path1 = Path([])
    path12 = Path([])

    map12 = Map()

    old, new = [], []
    changes = obs._get_components_change(old, new)
    assert changes == []

    components = [vel1, pos1]
    changes = obs._get_components_change(components, components)
    assert changes == []

    old, new = [vel1, pos1], [vel12, pos12]
    changes = obs._get_components_change(old, new)
    assert changes == []

    old, new = [vel1, pos1], [vel2, pos2]
    changes = obs._get_components_change(old, new)
    assert changes == [
        (vel2, ObserverChangeType.modified),
        (pos2, ObserverChangeType.modified),
    ]

    old, new = [], [vel1, pos1]
    changes = obs._get_components_change(old, new)
    assert changes == [
        (vel1, ObserverChangeType.added),
        (pos1, ObserverChangeType.added),
    ]

    old, new = [vel1, pos1], []
    changes = obs._get_components_change(old, new)
    assert changes == [
        (vel1, ObserverChangeType.removed),
        (pos1, ObserverChangeType.removed),
    ]

    old, new = [pos1], [vel1, pos2]
    changes = obs._get_components_change(old, new)
    assert changes == [
        (vel1, ObserverChangeType.added),
        (pos2, ObserverChangeType.modified),
    ]

    old = [vel1, pos1, path1]
    new = [pos12, path12, map12]
    changes = obs._get_components_change(old, new)
    assert changes == [
        (vel1, ObserverChangeType.removed),
        (map12, ObserverChangeType.added),
    ]

    old = [vel1, pos1]
    new = [vel12, pos2]
    changes = obs._get_components_change(old, new)
    assert changes == [(pos2, ObserverChangeType.modified)]


def test_get_state_change():
    obs = ObserverProcessor([Velocity, Position, Path, Map])

    vel1 = Velocity(x=0.0, y=0.0)
    vel2 = Velocity(x=1.0, y=1.0)

    pos1 = Position(x=0.0, y=0.0)
    pos2 = Position(x=1.0, y=1.0)

    # Case 1: Empty changes
    obs.previous_state = {0: []}
    obs._get_ents = MagicMock(return_value={0: []})
    assert obs._get_state_change() == {0: []}
    obs._get_ents.assert_called()

    # Case 2: One entity modified
    obs.previous_state = {0: [vel1, pos1]}
    obs._get_ents = MagicMock(return_value={0: [vel2, pos2]})
    obs._get_components_change = MagicMock(
        return_value=[
            (vel2, ObserverChangeType.modified),
            (pos2, ObserverChangeType.modified),
        ]
    )

    assert obs._get_state_change() == {
        0: [
            (vel2, ObserverChangeType.modified),
            (pos2, ObserverChangeType.modified),
        ]
    }
    obs._get_ents.assert_called_once()
    obs._get_components_change.assert_called_with([vel1, pos1], [vel2, pos2])

    # Case 3: Entity Removed
    obs.previous_state = {0: [vel1, pos1]}
    obs._get_ents = MagicMock(return_value={})
    obs._get_components_change = MagicMock(
        return_value=[
            (vel1, ObserverChangeType.removed),
            (pos1, ObserverChangeType.removed),
        ]
    )

    assert obs._get_state_change() == {
        0: [
            (vel1, ObserverChangeType.removed),
            (pos1, ObserverChangeType.removed),
        ]
    }
    obs._get_ents.assert_called_once()
    obs._get_components_change.assert_called_once_with([vel1, pos1], [])

    # Case 4: New entity
    obs.previous_state = {0: []}
    obs._get_ents = MagicMock(return_value={0: [], 1: []})
    obs._get_components_change = MagicMock(return_value=[])

    assert obs._get_state_change() == {0: [], 1: []}
    obs._get_ents.assert_called_once()
    obs._get_components_change.assert_called()

    # Case 5: Two entities modified
    obs.previous_state = {0: [pos1], 1: [vel1, pos1]}
    obs._get_ents = MagicMock(return_value={0: [], 1: [vel2, pos1]})
    obs._get_components_change = MagicMock(
        side_effect=lambda old, new: (
            [(pos1, ObserverChangeType.removed)]
            if new == []
            else [(vel2, ObserverChangeType.modified)]
        )
    )

    assert obs._get_state_change() == {
        0: [(pos1, ObserverChangeType.removed)],
        1: [(vel2, ObserverChangeType.modified)],
    }
    obs._get_ents.assert_called_once()
    obs._get_components_change.assert_called()


def test_process():
    env = simpy.Environment()
    event_store = simpy.FilterStore(env)

    obs = ObserverProcessor([Velocity, Position, Path, Map])

    vel1 = Velocity(x=0.0, y=0.0)
    vel2 = Velocity(x=1.0, y=1.0)

    pos1 = Position(x=0.0, y=0.0)
    pos2 = Position(x=1.0, y=1.0)

    kwargs = {"foo": "bar"}
    obs._get_event_store = MagicMock(return_value=event_store)
    obs._get_environment = MagicMock(return_value=env)

    # Case 1: No changes
    # entity = world.create_entity(velocity, position, path)
    obs._get_state_change = MagicMock(return_value={})

    obs.process(kwargs)

    obs._get_event_store.assert_called_once_with(kwargs)
    obs._get_environment.assert_called_once_with(kwargs)
    obs._get_state_change.assert_called_once()
    assert len(event_store.items) == 0

    # Case 2: Two entities added
    obs._get_state_change = MagicMock(return_value={0: [], 1: []})
    type(env).now = PropertyMock(return_value=42)

    obs.process(kwargs)

    obs._get_state_change.assert_called_once()
    assert len(event_store.items) == 1
    assert event_store.items[0] == EVENT(
        ObserverTag,
        ObserverPayload(
            timestamp=42, changes=[ObserverChange(0, []), ObserverChange(1, [])]
        ),
    )

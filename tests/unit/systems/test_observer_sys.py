from simulator.systems.Observer import ObserverProcessor

from simulator.components.Velocity import Velocity
from simulator.components.Position import Position
from simulator.components.Path import Path
from simulator.components.Map import Map


import esper


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

    map1 = Map()
    map12 = Map()

    old, new = [], []
    removed, added = obs._get_components_change(old, new)
    assert removed == []
    assert added == []

    old, new = [], [vel1, pos1]
    removed, added = obs._get_components_change(old, new)
    assert removed == []
    assert added == new

    old, new = [vel1, pos1], []
    removed, added = obs._get_components_change(old, new)
    assert removed == old
    assert added == []

    components = [vel1, pos1]
    removed, added = obs._get_components_change(components, components)
    assert removed == []
    assert added == []

    removed, added = obs._get_components_change([vel1, pos1], [vel12, pos12])
    assert removed == []
    assert added == []

    old = [vel1, pos1, path1]
    new = [pos12, path12, map12]
    removed, added = obs._get_components_change(old, new)
    assert removed == [vel1]
    assert added == [map12]

    old = [vel1, pos1]
    new = [vel12, pos2]
    removed, added = obs._get_components_change(old, new)
    assert removed == [pos1]
    assert added == [pos2]
    assert removed[0].x == 0.0
    assert added[0].x == 1.0
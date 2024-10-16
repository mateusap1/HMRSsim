from simulator.systems.Observer import ObserverProcessor

from simulator.components.Velocity import Velocity
from simulator.components.Position import Position


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

from simulator.systems.MovementProcessor import MovementProcessor
from simulator.components.Velocity import Velocity
from simulator.components.Position import Position


import esper


# TODO: Add tests for sector and adjacent sector
# Hopefully should be more modularized in order to do this test easier


def test_movement_process_idle():
    world = esper.World()

    entity = world.create_entity(Velocity(x=0.0, y=0.0), Position(x=0.0, y=0.0))
    world.add_processor(MovementProcessor(-500, 500, -500, 500))

    velocity: Velocity = world.component_for_entity(entity, Velocity)
    position: Position = world.component_for_entity(entity, Position)

    world.process({})

    assert (velocity.x, velocity.y) == (0.0, 0.0)
    assert (position.x, position.y) == (0.0, 0.0)
    assert position.changed is False


def test_movement_process():
    world = esper.World()

    entity = world.create_entity(Velocity(x=5.0, y=0.0), Position(x=0.0, y=0.0))
    world.add_processor(MovementProcessor(-500, 500, -500, 500))

    velocity: Velocity = world.component_for_entity(entity, Velocity)
    position: Position = world.component_for_entity(entity, Position)

    world.process({})
    assert (position.x, position.y) == (5.0, 0.0)
    assert position.sector == 0
    assert position.changed is True

    velocity.y = 5.0
    position.x = 0.0

    world.process({})
    assert (position.x, position.y) == (5.0, 5.0)
    assert position.sector == 0
    assert position.changed is True

    world.process({})
    assert (position.x, position.y) == (10.0, 10.0)
    assert position.sector == 0
    assert position.changed is True

    velocity.x = 50.0
    velocity.y = 0.0
    position.x = 0.0
    position.y = 0.0

    world.process({})
    assert (position.x, position.y) == (50.0, 0.0)
    assert position.changed is True

    velocity.y = 50.0

    world.process({})
    assert (position.x, position.y) == (100.0, 50.0)
    assert position.changed is True

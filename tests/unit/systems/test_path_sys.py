from simulator.systems.PathProcessor import PathProcessor

from simulator.components.Velocity import Velocity
from simulator.components.Position import Position
from simulator.components.Path import Path


import esper
import simpy


def test_path_process():
    world = esper.World()
    env = simpy.Environment()
    event_store = simpy.FilterStore(env)

    velocity = Velocity(x=5.0, y=5.0)
    position = Position(x=0.0, y=0.0)
    path = Path([(0.0, 0.0), (5.0, 0.0), (5.0, 5.0), (0.0, 5.0), (0.0, 0.0)], 1.0)

    entity = world.create_entity(velocity, position, path)
    world.add_processor(PathProcessor())

    world.process({"ENV": env, "EVENT_STORE": event_store})

    assert (velocity.x, velocity.y) == (5.0, 5.0)
    assert (position.x, position.y) == (0.0, 0.0)
    assert path.curr_point == 1

    world.process({"ENV": env, "EVENT_STORE": event_store})

    assert (velocity.x, velocity.y) == (1.0, 0.0)
    assert (position.x, position.y) == (0.0, 0.0)
    assert path.curr_point == 1

    position.x = 5.0
    position.center = (5.0, 0.0)

    velocity.x = 0.0

    world.process({"ENV": env, "EVENT_STORE": event_store})

    assert (velocity.x, velocity.y) == (0.0, 0.0)
    assert (position.x, position.y) == (5.0, 0.0)
    assert path.curr_point == 2

    position.x, position.y = (0.0, 0.0)
    position.center = (0.0, 0.0)
    path.curr_point = 4

    world.process({"ENV": env, "EVENT_STORE": event_store})

    assert not world.has_component(entity, Path)
    assert len(event_store.items) == 1
    assert (velocity.x, velocity.y) == (5.0, 5.0)

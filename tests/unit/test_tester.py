from simulator.systems.Tester import (
    TesterDESProcessor,
    RequireState,
    TesterState,
    NearPosition,
)

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


def always_succeed_requirment(_):
    return RequireState.SUCCESS


def always_fail_requirment(_):
    return RequireState.FAILURE


def always_continue_requirment(_):
    return RequireState.CONTINUE


def test_process_event():
    event = EVENT(ObserverTag, ObserverPayload(timestamp=0, changes=[]))

    tester = TesterDESProcessor([always_succeed_requirment])
    tester._process_event(event)
    assert tester.requirement_counter == 1
    assert tester.state == TesterState.RUNNING

    tester = TesterDESProcessor([always_fail_requirment])
    tester._process_event(event)
    assert tester.requirement_counter == 0
    assert tester.state == TesterState.FAILURE

    tester = TesterDESProcessor([always_continue_requirment])
    tester._process_event(event)
    assert tester.requirement_counter == 0
    assert tester.state == TesterState.RUNNING


def test_near_position():
    pos = NearPosition(0, (0.0, 0.0), 5.0)
    assert pos._near_position((3.0, 4.0))  # Boundary
    assert pos._near_position((5.0, 0.0))  # Boundary
    assert pos._near_position((0.0, 0.0))  # Middle

    assert not pos._near_position((6.0, 8.0))  # Outside

    pos = NearPosition(0, (2.0, 2.0), 0.0)
    assert pos._near_position((2.0, 2.0))  # Same position
    assert not pos._near_position((2.1, 2.1))  # Any other position should be False


def test_near_position_requirement():
    # Case 1: No changes
    req = NearPosition(0, (5.0, 5.0), 5.0)
    req._near_position = MagicMock(return_value=True)
    payload = ObserverPayload(timestamp=0, changes=[])
    assert req.requirement(payload) == RequireState.CONTINUE
    req._near_position.assert_not_called()

    # Case 2: Success, change position to near
    req = NearPosition(0, (5.0, 5.0), 5.0)
    req._near_position = MagicMock(return_value=True)
    payload = ObserverPayload(
        timestamp=0,
        changes=[
            ObserverChange(
                ent=0, changes=[(Position(0.0, 0.0), ObserverChangeType.modified)]
            )
        ],
    )
    assert req.requirement(payload) == RequireState.SUCCESS
    req._near_position.assert_called_once_with((0.0, 0.0))

    # Case 3: Change to position far
    req = NearPosition(0, (5.0, 5.0), 5.0)
    req._near_position = MagicMock(return_value=False)
    payload = ObserverPayload(
        timestamp=0,
        changes=[
            ObserverChange(
                ent=0, changes=[(Position(0.0, 0.0), ObserverChangeType.modified)]
            )
        ],
    )
    assert req.requirement(payload) == RequireState.CONTINUE
    req._near_position.assert_called_once_with((0.0, 0.0))

    # Case 4: Change to position added
    req = NearPosition(0, (5.0, 5.0), 5.0)
    req._near_position = MagicMock(return_value=True)
    payload = ObserverPayload(
        timestamp=0,
        changes=[
            ObserverChange(
                ent=0, changes=[(Position(0.0, 0.0), ObserverChangeType.added)]
            )
        ],
    )
    assert req.requirement(payload) == RequireState.SUCCESS
    req._near_position.assert_called_once_with((0.0, 0.0))

    # Case 5: Change to position removed
    req = NearPosition(0, (5.0, 5.0), 5.0)
    req._near_position = MagicMock(return_value=True)
    payload = ObserverPayload(
        timestamp=0,
        changes=[
            ObserverChange(
                ent=0, changes=[(Position(0.0, 0.0), ObserverChangeType.removed)]
            )
        ],
    )
    assert req.requirement(payload) == RequireState.CONTINUE
    req._near_position.assert_not_called()


    # Case 6: Changes in other entity
    req = NearPosition(0, (5.0, 5.0), 5.0)
    req._near_position = MagicMock(return_value=True)
    payload = ObserverPayload(
        timestamp=0,
        changes=[
            ObserverChange(
                ent=1, changes=[(Position(0.0, 0.0), ObserverChangeType.modified)]
            )
        ],
    )
    assert req.requirement(payload) == RequireState.CONTINUE
    req._near_position.assert_not_called()

    # Case 7: Changes same entity, but not position component
    req = NearPosition(0, (5.0, 5.0), 5.0)
    req._near_position = MagicMock(return_value=True)
    payload = ObserverPayload(
        timestamp=0,
        changes=[
            ObserverChange(
                ent=0, changes=[(Velocity(0.0, 0.0), ObserverChangeType.modified)]
            )
        ],
    )
    assert req.requirement(payload) == RequireState.CONTINUE
    req._near_position.assert_not_called()

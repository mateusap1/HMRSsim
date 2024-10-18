from typing import Tuple, Union, List, NamedTuple
from dataclasses import dataclass
from enum import Enum

Point = Tuple[Union[float, int], Union[float, int]]
ShapeDefinition = Tuple[Point, List[Point]]

EVENT = NamedTuple("Event", [("type", str), ("payload", NamedTuple)])
ERROR = NamedTuple("ErrorEvent", [("type", str), ("ent", int), ("payload", NamedTuple)])


class Component:
    def __eq__(self, other: "Component"):
        return vars(self) == vars(other)


# Payloads and tags convention related to Goto events
GotoPoiPayload = NamedTuple("GotoPoiPayload", [("entity", int), ("target", str)])
GotoPosPayload = NamedTuple("GotoPosPayload", [("entity", int), ("target", list)])
GotoPoiEventTag = "GoToPoiEvent"
GotoPosEventTag = "GoToPosEvent"

# Payloads and tags convention related to Path events
EndOfPathPayload = NamedTuple(
    "EndOfPathPayload", [("ent", int), ("timestamp", str), ("path", List[Point])]
)
EndOfPathTag = "EndOfPath"
EndOfApproximationPayload = NamedTuple(
    "EndOfApproximation",
    [
        ("ent", int),
        ("timestamp", str),
    ],
)
EndOfApproximationTag = "EndOfApproximation"


class ObserverChangeType(Enum):
    added = 1
    modified = 2
    removed = 3


ObserverTag = "Observer"
ObserverChange = NamedTuple(
    "ObserverChange",
    [("ent", int), ("changes", List[Tuple[Component, ObserverChangeType]])],
)
ObserverPayload = NamedTuple(
    "ObserverPayload", [("timestamp", int), ("changes", List[ObserverChange])]
)

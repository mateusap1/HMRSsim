from typing import Tuple, Union, List, NamedTuple

Point = Tuple[Union[float, int], Union[float, int]]
ShapeDefinition = Tuple[Point, List[Point]]

EVENT = NamedTuple('Event', [('type', str), ('payload', NamedTuple)])
ERROR = NamedTuple('ErrorEvent', [('type', str), ('ent', int), ('payload', NamedTuple)])

class Component:
    pass

# Payloads and tags convention related to Goto events
GotoPoiPayload = NamedTuple('GotoPoiPayload', [('entity', int), ('target', str)])
GotoPosPayload = NamedTuple('GotoPosPayload', [('entity', int), ('target', list)])
GotoPoiEventTag = 'GoToPoiEvent'
GotoPosEventTag = 'GoToPosEvent'

# Payloads and tags convention related to Path events
EndOfPathPayload = NamedTuple('EndOfPathPayload', [('ent', int), ('timestamp', str), ('path', List[Point])])
EndOfPathTag = 'EndOfPath'
EndOfApproximationPayload = NamedTuple('EndOfApproximation', [('ent', int), ('timestamp', str),])
EndOfApproximationTag = 'EndOfApproximation'

ObserverTag = 'Observer'
ObserverChange = NamedTuple('ObserverChange', [('ent', int), ('components', List[Component])])
ObserverPayload = NamedTuple('ObserverPayload', [('timestamp', str), ('changes', List[ObserverChange])])
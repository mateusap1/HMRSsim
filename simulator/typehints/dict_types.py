import typing
import esper
import simpy


class SystemArgs(typing.TypedDict):
    """Type of Keyword Arguments passed to systems in the process method."""
    ENV: simpy.Environment
    WORLD: esper.World
    _KILLSWITCH: typing.Union[simpy.Event, None]
    EVENT_STORE: simpy.FilterStore


class Config(typing.TypedDict):
    """Options for the Simulation config

        Arguments:
            context: str -- Change the base directory for simulation assets. Default is .
            map: str -- Name of simulation map file. Must be under assets folder. Default is 'map.drawio'
    """
    context: str
    map: str
    FPS: typing.Optional[int]
    DLW: typing.Optional[int]
    duration: typing.Optional[int]
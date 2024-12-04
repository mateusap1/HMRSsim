import sys

from simulator.systems.MovementProcessor import MovementProcessor
from simulator.systems.CollisionProcessor import CollisionProcessor
from simulator.systems.PathProcessor import PathProcessor
from simulator.systems.GotoDESProcessor import GotoDESProcessor
from simulator.systems.BridgePlugin import BridgeProcessor
from simulator.systems import SeerPlugin

from simulator.main import Simulator

from simulator.utils.Firebase import Firebase_conn


def setup():
    # Create a simulation with config
    simulator = Simulator(sys.argv[1])

    # Some simulator objects
    width, height = simulator.window_dimensions

    firebase = Firebase_conn("bt")
    firebase.clean_old_simulation()

    build_report = simulator.build_report
    firebase.send_build_report(build_report)

    NavigationSystemProcess = GotoDESProcessor().process

    # Defines and initializes esper.Processor for the simulation
    normal_processors = [
        MovementProcessor(minx=0, miny=0, maxx=width, maxy=height),
        CollisionProcessor(),
        PathProcessor(),
        BridgeProcessor()
    ]

    # Defines DES processors
    des_processors = [
        SeerPlugin.init([firebase.seer_consumer], 0.05, False),
        (NavigationSystemProcess,),
    ]

    # Add processors to the simulation, according to processor type
    for p in normal_processors:
        simulator.add_system(p)
    for p in des_processors:
        simulator.add_des_system(p)

    return simulator


if __name__ == "__main__":
    simulator = setup()
    simulator.run()
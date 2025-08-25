import pytest
import json
import math
import sys
import re

from typing import List, Tuple

from simulator.main import Simulator, ConfigFormat

from simulator.systems.MovementProcessor import MovementProcessor
from simulator.systems.CollisionProcessor import CollisionProcessor
from simulator.systems.PathProcessor import PathProcessor

import simulator.systems.EnergyConsumptionDESProcessor as energySystem
import simulator.systems.ManageObjects as ObjectManager
import simulator.systems.ClawDESProcessor as ClawProcessor
import simulator.systems.ScriptEventsDES as ScriptSystem
import simulator.systems.GotoDESProcessor as NavigationSystem
from simulator.systems.Observer import ObserverProcessor
from simulator.systems.Tester import (
    TesterDESProcessor,
    NearPosition,
    ChangedInventory,
    TesterState,
)
from simulator.components.Script import Script, States
from simulator.components.Inventory import Inventory
from simulator.components.Position import Position

from simulator.typehints.component_types import Component


def setup_simulation(config: ConfigFormat, observer_components: List[Component]):
    # Create a simulation with config
    simulator = Simulator(config)

    robot_ent = None
    for ent, ent_type in simulator.entities:
        if ent_type == "robot":
            robot_ent = ent

    if robot_ent is None:
        raise ValueError("Could not find robot entity.")

    # Some simulator objects
    width, height = simulator.window_dimensions

    extra_instructions = [
        (NavigationSystem.GotoInstructionId, NavigationSystem.go_instruction),
        (ClawProcessor.GrabInstructionTag, ClawProcessor.grabInstruction),
        (ClawProcessor.DropInstructionTag, ClawProcessor.dropInstrution),
    ]
    ScriptProcessor = ScriptSystem.init(extra_instructions, [ClawProcessor.ClawDoneTag])
    NavigationSystemProcess = NavigationSystem.GotoDESProcessor().process

    # Defines and initializes esper.Processor for the simulation
    normal_processors = [
        ObserverProcessor(observer_components),
        MovementProcessor(minx=0, miny=0, maxx=width, maxy=height),
        CollisionProcessor(),
        PathProcessor(),
    ]

    med_room = (514.5, 240.0)
    patient_room = (70.0, 220.0)
    robot_home = (495.0, 75.0)

    tester = TesterDESProcessor(
        [
            (
                "Start at robot home",
                NearPosition(robot_ent, robot_home, 15.0).requirement,
            ),
            ("Go to med room", NearPosition(robot_ent, med_room, 15.0).requirement),
            (
                "Grab claw",
                ChangedInventory(1, "medicine").removed_object_requirement,
            ),
            (
                "Go to patient room",
                NearPosition(robot_ent, patient_room, 15.0).requirement,
            ),
            (
                "Drop claw",
                ChangedInventory(1, "medicine").added_object_requirement,
            ),
            (
                "Return to robot home",
                NearPosition(robot_ent, robot_home, 15.0).requirement,
            ),
        ]
    )

    # Defines DES processors
    des_processors = [
        (tester.process,),
        (ClawProcessor.process,),
        (ObjectManager.process,),
        (energySystem.process,),
        (NavigationSystemProcess,),
        (ScriptProcessor,),
    ]

    # Add processors to the simulation, according to processor type
    for p in normal_processors:
        simulator.add_system(p)

    for p in des_processors:
        simulator.add_des_system(p)

    # Create the error handlers dict
    error_handlers = {NavigationSystem.PathErrorTag: NavigationSystem.handle_path_error}

    # Adding error handlers to the robot
    robot = simulator.objects[0][0]
    script = simulator.world.component_for_entity(robot, Script)
    script.error_handlers = error_handlers

    return simulator, tester


@pytest.fixture
def config_path(tmp_path):
    # Create a temporary config file
    config = {
        "context": ".",
        "map": str(tmp_path / "hospital_map.xml"),
        "FPS": 60,
        "DLW": 10,
        "duration": 10,
        "verbose": 20,
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    return str(config_file)


@pytest.fixture(params=[
    (["Go medRoom", "Grab medicine", "Go patientRoom", "Drop medicine", "Go robotHome"], True),
    (["Grab medicine", "Go patientRoom", "Drop medicine", "Go robotHome"], False),
    (["Go medRoom", "Go patientRoom", "Go robotHome"], False),
    (["Go medRoom", "Grab medicine", "Drop medicine", "Go robotHome"], False),
    (["Go medRoom", "Grab medicine", "Go patientRoom", "Go robotHome"], False),
    (["Go medRoom", "Grab medicine", "Go patientRoom", "Drop medicine"], False),
])
def mock_map(request, tmp_path):
    steps, state = request.param
    steps_str = ", ".join([f"&quot;{step}&quot;" for step in steps])
    component_script = f"[[{steps_str}], 0]"
    
    map_content = f"""
    <mxfile host="" modified="2021-03-05T12:07:23.856Z"
    agent="5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
    etag="4gopTQFj9oIBlTbiy7g3" version="13.7.9" type="embed">
    <diagram id="Yp99EcE86TbjtTeTYBdj" name="Hospital Scenario 0">
        <mxGraphModel dx="749" dy="567" grid="1" gridSize="10" guides="1" tooltips="1" connect="1"
            arrows="1" fold="1" page="1" pageScale="1" pageWidth="583" pageHeight="413"
            background="#F1FAEE" math="0" shadow="0">
            <root>
                <mxCell id="0" />
                <mxCell id="1" parent="0" />
                <object label="&lt;font color=&quot;#000000&quot;&gt;Robot&lt;/font&gt;"
                    type="robot" collision_tag="stopEvent" component_Claw="[80, 1]"
                    component_Script="{component_script}"
                    id="XaaZAw79OCWD7nJUf5TW-4">
                    <mxCell
                        style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;strokeColor=#B09500;fontColor=#ffffff;fillColor=#e3c800;"
                        parent="1" vertex="1">
                        <mxGeometry x="500" y="65" width="30" height="30" as="geometry" />
                    </mxCell>
                </object>
                <mxCell id="XaaZAw79OCWD7nJUf5TW-5" value=""
                    style="verticalLabelPosition=bottom;html=1;verticalAlign=top;align=center;shape=mxgraph.floorplan.wall;fillColor=#A8DADC;direction=south;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry x="400" y="120" width="10" height="120" as="geometry" />
                </mxCell>
                <mxCell id="XaaZAw79OCWD7nJUf5TW-6" value=""
                    style="verticalLabelPosition=bottom;html=1;verticalAlign=top;align=center;shape=mxgraph.floorplan.wall;fillColor=#A8DADC;direction=west;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry y="30" width="560" height="10" as="geometry" />
                </mxCell>
                <mxCell id="XaaZAw79OCWD7nJUf5TW-7" value=""
                    style="verticalLabelPosition=bottom;html=1;verticalAlign=top;align=center;shape=mxgraph.floorplan.wall;fillColor=#A8DADC;direction=south;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry x="310" y="120" width="10" height="120" as="geometry" />
                </mxCell>
                <mxCell id="XaaZAw79OCWD7nJUf5TW-8" value=""
                    style="verticalLabelPosition=bottom;html=1;verticalAlign=top;align=center;shape=mxgraph.floorplan.wall;fillColor=#A8DADC;direction=west;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry x="10" y="120" width="310" height="10" as="geometry" />
                </mxCell>
                <mxCell id="XaaZAw79OCWD7nJUf5TW-9" value=""
                    style="verticalLabelPosition=bottom;html=1;verticalAlign=top;align=center;shape=mxgraph.floorplan.wall;fillColor=#A8DADC;direction=west;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry x="140" y="230" width="170" height="10" as="geometry" />
                </mxCell>
                <mxCell id="XaaZAw79OCWD7nJUf5TW-10" value=""
                    style="verticalLabelPosition=bottom;html=1;verticalAlign=top;align=center;shape=mxgraph.floorplan.wall;fillColor=#A8DADC;direction=south;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry x="130" y="170" width="10" height="70" as="geometry" />
                </mxCell>
                <mxCell id="XaaZAw79OCWD7nJUf5TW-11" value=""
                    style="verticalLabelPosition=bottom;html=1;verticalAlign=top;align=center;shape=mxgraph.floorplan.wall;fillColor=#A8DADC;direction=south;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry x="470" y="170" width="10" height="70" as="geometry" />
                </mxCell>
                <mxCell id="XaaZAw79OCWD7nJUf5TW-12" value=""
                    style="verticalLabelPosition=bottom;html=1;verticalAlign=top;align=center;shape=mxgraph.floorplan.wall;fillColor=#A8DADC;direction=west;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry x="410" y="230" width="60" height="10" as="geometry" />
                </mxCell>
                <mxCell id="XaaZAw79OCWD7nJUf5TW-13" value=""
                    style="verticalLabelPosition=bottom;html=1;verticalAlign=top;align=center;shape=mxgraph.floorplan.wall;fillColor=#A8DADC;direction=west;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry x="140" y="320" width="340" height="10" as="geometry" />
                </mxCell>
                <object label="" type="map-path" id="Y7Bzf0jI6VJ8z7jc9NQ7-1">
                    <mxCell
                        style="endArrow=classic;html=1;exitX=0;exitY=0.5;exitDx=0;exitDy=0;labelBackgroundColor=#F1FAEE;fontColor=#1D3557;strokeColor=#000000;"
                        parent="1" source="XaaZAw79OCWD7nJUf5TW-4" edge="1">
                        <mxGeometry width="50" height="50" relative="1" as="geometry">
                            <mxPoint x="490" y="80" as="sourcePoint" />
                            <mxPoint x="518" y="230" as="targetPoint" />
                            <Array as="points">
                                <mxPoint x="360" y="80" />
                                <mxPoint x="360" y="280" />
                                <mxPoint x="518" y="280" />
                            </Array>
                        </mxGeometry>
                    </mxCell>
                </object>
                <mxCell id="Y7Bzf0jI6VJ8z7jc9NQ7-2" value=""
                    style="rounded=0;whiteSpace=wrap;html=1;fillColor=#A8DADC;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry x="480" y="180" width="77" height="25" as="geometry" />
                </mxCell>
                <object label="" type="map-path" id="CDSX7yOxOUjXz9ZWq8lS-1">
                    <mxCell
                        style="endArrow=classic;html=1;labelBackgroundColor=#F1FAEE;fontColor=#1D3557;strokeColor=#000000;"
                        parent="1" edge="1">
                        <mxGeometry width="50" height="50" relative="1" as="geometry">
                            <mxPoint x="500" y="280" as="sourcePoint" />
                            <mxPoint x="80" y="230" as="targetPoint" />
                            <Array as="points">
                                <mxPoint x="80" y="280" />
                            </Array>
                        </mxGeometry>
                    </mxCell>
                </object>
                <mxCell id="CDSX7yOxOUjXz9ZWq8lS-2" value=""
                    style="verticalLabelPosition=bottom;html=1;verticalAlign=top;align=center;shape=mxgraph.floorplan.wall;fillColor=#A8DADC;direction=south;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry x="260" y="40" width="10" height="80" as="geometry" />
                </mxCell>
                <object label="" type="map-path" id="CDSX7yOxOUjXz9ZWq8lS-3">
                    <mxCell
                        style="endArrow=classic;html=1;labelBackgroundColor=#F1FAEE;fontColor=#1D3557;strokeColor=#000000;"
                        parent="1" edge="1">
                        <mxGeometry width="50" height="50" relative="1" as="geometry">
                            <mxPoint x="490" y="80" as="sourcePoint" />
                            <mxPoint x="40" y="80" as="targetPoint" />
                        </mxGeometry>
                    </mxCell>
                </object>
                <object label="" type="pickable" name="medicine" weight="0.2"
                    id="CDSX7yOxOUjXz9ZWq8lS-4">
                    <mxCell
                        style="rounded=0;whiteSpace=wrap;html=1;fillColor=#e51400;strokeColor=#B20000;fontColor=#ffffff;"
                        parent="1" vertex="1">
                        <mxGeometry x="512.5" y="193" width="12" height="12" as="geometry" />
                    </mxCell>
                </object>
                <mxCell id="eMFEXRY4Y2-7gtaYJtUj-1"
                    value="&lt;font style=&quot;font-size: 14px&quot;&gt;Patient Room&lt;/font&gt;"
                    style="verticalLabelPosition=middle;html=1;verticalAlign=middle;align=center;shape=mxgraph.floorplan.wallU;fillColor=#A8DADC;rotation=-90;labelPosition=center;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry x="1" y="190.94" width="170" height="108.12" as="geometry" />
                </mxCell>
                <mxCell id="eMFEXRY4Y2-7gtaYJtUj-2" value="Medicine Room"
                    style="verticalLabelPosition=middle;html=1;verticalAlign=middle;align=center;shape=mxgraph.floorplan.wallU;fillColor=#A8DADC;rotation=90;labelPosition=center;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry x="438.5" y="191.5" width="170" height="107" as="geometry" />
                </mxCell>
                <mxCell id="eMFEXRY4Y2-7gtaYJtUj-3" value=""
                    style="verticalLabelPosition=bottom;html=1;verticalAlign=top;align=center;shape=mxgraph.floorplan.wall;fillColor=#A8DADC;direction=south;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry x="550" y="40" width="10" height="90" as="geometry" />
                </mxCell>
                <mxCell id="eMFEXRY4Y2-7gtaYJtUj-4" value=""
                    style="verticalLabelPosition=bottom;html=1;verticalAlign=top;align=center;shape=mxgraph.floorplan.wall;fillColor=#A8DADC;strokeColor=#457B9D;fontColor=#1D3557;"
                    parent="1" vertex="1">
                    <mxGeometry x="410" y="120" width="140" height="10" as="geometry" />
                </mxCell>
                <object label="" type="map-path" id="MtlUYL0zB10NUilJHkJb-1">
                    <mxCell
                        style="endArrow=classic;html=1;labelBackgroundColor=#F1FAEE;fontColor=#1D3557;strokeColor=#000000;"
                        parent="1" edge="1">
                        <mxGeometry width="50" height="50" relative="1" as="geometry">
                            <mxPoint x="80" y="280" as="sourcePoint" />
                            <mxPoint x="490" y="80" as="targetPoint" />
                            <Array as="points">
                                <mxPoint x="360" y="280" />
                                <mxPoint x="360" y="80" />
                            </Array>
                        </mxGeometry>
                    </mxCell>
                </object>
                <object label="" type="POI" tag="medRoom" id="2">
                    <mxCell
                        style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#e3c800;strokeColor=#B09500;fontColor=#ffffff;"
                        parent="1" vertex="1">
                        <mxGeometry x="514.5" y="240" width="10" height="10" as="geometry" />
                    </mxCell>
                </object>
                <object label="" type="POI" tag="patientRoom" id="10">
                    <mxCell
                        style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#e3c800;strokeColor=#B09500;fontColor=#ffffff;"
                        parent="1" vertex="1">
                        <mxGeometry x="70" y="220" width="10" height="10" as="geometry" />
                    </mxCell>
                </object>
                <object label="" type="POI" tag="robotHome" id="14">
                    <mxCell
                        style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#e3c800;strokeColor=#B09500;fontColor=#ffffff;"
                        parent="1" vertex="1">
                        <mxGeometry x="495" y="75" width="10" height="10" as="geometry" />
                    </mxCell>
                </object>
            </root>
        </mxGraphModel>
    </diagram>
</mxfile>
    """
    map_file = tmp_path / "hospital_map.xml"
    map_file.write_text(map_content)

    return TesterState.SUCCESS if state else TesterState.FAILURE


def test_hospital_simulation_integration(tmp_path, mock_map):
    state = mock_map
    sim, tester = setup_simulation(
        {
            "context": ".",
            "map": str(tmp_path / "hospital_map.xml"),
            "FPS": 60,
            "DLW": 10,
            "duration": 10,
            "verbose": 20,
        },
        [Position, Inventory],
    )

    # Run the simulation with a timeout
    sim.run()
    tester.finish()
    tester.print_state()

    assert tester.state == state


if __name__ == "__main__":
    pytest.main([__file__])

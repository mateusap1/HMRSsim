import pytest
import json
import math
import time
import sys
import re

from pathlib import Path
from simulator.main import Simulator
from simulator.components.Script import Script, States
from simulator.components.Inventory import Inventory
from simulator.components.Position import Position

from examples.hospitalSimulation.run import setup


class SimulationComplete(Exception):
    pass


def run_simulation_with_timeout(simulator, timeout=300):
    def signal_completion(env):
        yield env.timeout(timeout)
        raise SimulationComplete()

    simulator.ENV.process(signal_completion(simulator.ENV))

    try:
        simulator.run()
    except SimulationComplete:
        pass


def is_close_enough(actual, expected, tolerance=15):
    return (
        math.sqrt((actual[0] - expected[0]) ** 2 + (actual[1] - expected[1]) ** 2)
        <= tolerance
    )


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


@pytest.fixture
def mock_map(tmp_path):
    map_content = """
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
                    component_Script="[[&quot;Go medRoom&quot;, &quot;Grab medicine&quot;, &quot;Go patientRoom&quot;, &quot;Drop medicine&quot;, &quot;Go robotHome&quot;], 0]"
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


@pytest.fixture
def simulator(config_path, mock_map):
    sys.argv = [sys.argv[0], config_path]
    simulator, objects = setup()
    return simulator, objects


def parse_script_logs(logs):
    parsed_logs = []
    for log in logs:
        match = re.match(
            r"\[(\d+(?:\.\d+)?)\] Execute instruction (\w+) (\[.*?\])\. Current state (States\.\w+)",
            log,
        )
        if match:
            time, instruction, args, state = match.groups()
            parsed_logs.append(
                {
                    "time": float(time),
                    "instruction": instruction,
                    "args": eval(args),
                    "state": getattr(States, state.split(".")[1]),
                }
            )
    return parsed_logs


def test_hospital_simulation_integration(simulator, caplog):
    sim, objects = simulator
    script = objects[0]

    # Run the simulation with a timeout
    # run_simulation_with_timeout(sim)
    sim.run()

    # Verify that the simulation completed
    assert sim.ENV.now > 0, "Simulation did not run"

    # Parse and check robot's script logs
    parsed_logs = parse_script_logs(script.logs)

    expected_instructions = [
        ("Go", ["medRoom"]),
        ("Grab", ["medicine"]),
        ("Go", ["patientRoom"]),
        ("Drop", ["medicine"]),
        ("Go", ["robotHome"]),
    ]

    # Print detailed information about executed instructions
    print("Executed instructions:")
    for log in parsed_logs:
        print(
            f"Time: {log['time']}, Instruction: {log['instruction']}, Args: {log['args']}, State: {log['state']}"
        )

    assert len(parsed_logs) == len(
        expected_instructions
    ), f"Expected {len(expected_instructions)} instructions, got {len(parsed_logs)}"

    for i, (expected_instruction, expected_args) in enumerate(expected_instructions):
        if i < len(parsed_logs):
            assert (
                parsed_logs[i]["instruction"] == expected_instruction
            ), f"Instruction {i} should be {expected_instruction}, got {parsed_logs[i]['instruction']}"
            assert (
                parsed_logs[i]["args"] == expected_args
            ), f"Arguments for instruction {i} should be {expected_args}, got {parsed_logs[i]['args']}"
            assert (
                parsed_logs[i]["state"] == States.BLOCKED
            ), f"State for instruction {i} should be BLOCKED, got {parsed_logs[i]['state']}"
        else:
            pytest.fail(
                f"Instruction {i} ({expected_instruction} {expected_args}) was not executed"
            )

    # Check that times are increasing
    times = [log["time"] for log in parsed_logs]
    assert times == sorted(
        times
    ), "Instructions were not executed in order of increasing time"

    # Verify that the script completed successfully
    assert (
        script.state == States.DONE
    ), f"Script did not complete successfully. Final state: {script.state}"

    # Verify robot's final position
    robot_entity = sim.objects[0][0]
    robot_position = sim.world.component_for_entity(robot_entity, Position)
    robot_home = (
        500.0,
        80.0,
    )  # Updated based on the POI in the simulation loading output

    assert is_close_enough(
        robot_position.center, robot_home
    ), f"Robot did not return close enough to its home position. Expected: {robot_home}, Actual: {robot_position.center}"

    # Print final simulation time
    print(f"Final simulation time: {sim.ENV.now}")


if __name__ == "__main__":
    pytest.main([__file__])
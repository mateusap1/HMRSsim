#!/bin/bash
set -e

# setup ros2 environment
echo "source \"/opt/ros/$ROS_DISTRO/setup.bash\"" >> /root/.bashrc
echo "source \"/opt/ros/$ROS_DISTRO/setup.bash\"" >> /root/.profile

source /root/.bashrc
source /root/.profile

# run rosbridge server
poetry run python examples/hospitalSimulationRos/hospital_ros_run.py examples/hospitalSimulationRos/simulation.json

exec "$@"

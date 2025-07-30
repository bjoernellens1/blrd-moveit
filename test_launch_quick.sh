#!/bin/bash

# Quick launch test to check if MoveIt starts properly

echo "=== Quick MoveIt2 Launch Test ==="

# Set up environment
source /opt/ros/jazzy/setup.bash
source /workspace/install/setup.bash

# Try to launch MoveIt for a few seconds to check for immediate errors
echo "Testing MoveIt launch (will run for 10 seconds)..."

timeout 10s ros2 launch abb_bringup abb_moveit.launch.py \
  robot_xacro_file:=crb15000_5_95.xacro \
  support_package:=abb_crb15000_support \
  moveit_config_package:=abb_crb15000_5_95_moveit_config \
  moveit_config_file:=abb_crb15000_5_95.srdf.xacro || echo "Launch test completed (or timed out)"

echo -e "\n=== Launch test finished ==="

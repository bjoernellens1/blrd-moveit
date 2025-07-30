#!/bin/bash

# Test script to verify MoveIt launch with CRB15000

echo "=== Testing MoveIt2 CRB15000 Launch Configuration ==="

# Test 1: Check if the packages exist
echo -e "\n1. Verifying required packages exist..."
ros2 pkg list | grep -E "abb_crb15000|abb_bringup"

# Test 2: Check the launch file exists
echo -e "\n2. Checking abb_moveit.launch.py exists..."
ros2 pkg prefix abb_bringup
find $(ros2 pkg prefix abb_bringup) -name "abb_moveit.launch.py" -type f

# Test 3: Verify robot XACRO file exists
echo -e "\n3. Checking CRB15000 XACRO file..."
find $(ros2 pkg prefix abb_crb15000_support) -name "crb15000_5_95.xacro" -type f

# Test 4: Verify MoveIt config file exists
echo -e "\n4. Checking CRB15000 MoveIt SRDF file..."
find $(ros2 pkg prefix abb_crb15000_5_95_moveit_config) -name "abb_crb15000_5_95.srdf.xacro" -type f

# Test 5: Test the launch command syntax
echo -e "\n5. Testing launch command syntax (dry run)..."
ros2 launch abb_bringup abb_moveit.launch.py \
  robot_xacro_file:=crb15000_5_95.xacro \
  support_package:=abb_crb15000_support \
  moveit_config_package:=abb_crb15000_5_95_moveit_config \
  moveit_config_file:=abb_crb15000_5_95.srdf.xacro \
  --help 2>/dev/null | head -10

echo -e "\n6. Checking MoveIt dependency packages..."
ros2 pkg list | grep -E "moveit|rviz"

echo -e "\n=== Test complete ==="

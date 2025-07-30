#!/bin/bash

# Script to check available robot packages in the abb_ros2 workspace

echo "=== Checking available robot packages in abb_ros2 ==="

# Check robot_specific_config directory
echo -e "\n1. Available robot packages in robot_specific_config:"
find /workspace/src/abb_ros2/robot_specific_config -name "*support" -o -name "*moveit_config" | sort

# Check for CRB15000 specific files
echo -e "\n2. Searching for CRB15000 related files:"
find /workspace/src/abb_ros2 -name "*crb15000*" -o -name "*CRB15000*" | sort

echo -e "\n3. Searching for available robot XACRO files:"
find /workspace/src/abb_ros2 -name "*.xacro" | grep -E "urdf|robot" | sort

echo -e "\n4. Available SRDF files:"
find /workspace/src/abb_ros2 -name "*.srdf*" | sort

echo -e "\n5. List all robot support packages:"
ls -la /workspace/src/abb_ros2/robot_specific_config/

echo -e "\n6. Check package.xml files to understand robot types:"
find /workspace/src/abb_ros2/robot_specific_config -name "package.xml" -exec echo -n "Package: " \; -exec dirname {} \; -exec grep -h "<name>" {} \;

echo -e "\n=== End of package check ==="

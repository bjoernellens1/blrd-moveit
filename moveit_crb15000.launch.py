#!/usr/bin/env python3
"""
moveit_crb15000.launch.py
========================

MoveIt2-only launch file for the ABB CRB 15000 robot.
This file launches only the MoveIt2 components for motion planning
without robot control or hardware interface.

NOTE: Currently using IRB1200 configuration as CRB15000 packages are not yet 
available in the abb_ros2 repository. This will need to be updated once 
CRB15000 support packages are created.

Usage:
  ros2 launch . moveit_crb15000.launch.py
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution, FindExecutable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """Generate the launch description for CRB15000 MoveIt2."""
    
    # Declare launch arguments
    declared_arguments = []
    
    declared_arguments.append(
        DeclareLaunchArgument(
            "launch_rviz",
            default_value="true",
            description="Launch RViz2 with MoveIt2 plugins.",
        )
    )

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])


def launch_setup(context, *args, **kwargs):
    """Setup function called with evaluated launch arguments."""
    
    # Get launch arguments
    launch_rviz = LaunchConfiguration("launch_rviz")
    
    # Robot description for MoveIt2
    # NOTE: Using IRB1200 as CRB15000 support packages are not yet available
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]),
        " ",
        PathJoinSubstitution([
            FindPackageShare("abb_irb1200_support"),
            "urdf",
            "irb1200_5_90.xacro"
        ]),
        " use_fake_hardware:=true",
    ])
    
    robot_description = {"robot_description": robot_description_content}
    
    # MoveIt2 configuration
    # NOTE: Using IRB1200 MoveIt config as CRB15000 config is not yet available
    moveit_config = (
        MoveItConfigsBuilder("abb_irb1200", package_name="abb_irb1200_5_90_moveit_config")
        .robot_description(robot_description_content.perform(context))
        .robot_description_semantic(
            file_path=os.path.join(
                get_package_share_directory("abb_irb1200_5_90_moveit_config"),
                "config",
                "abb_irb1200_5_90.srdf.xacro",
            )
        )
        .robot_description_kinematics(
            file_path=os.path.join(
                get_package_share_directory("abb_irb1200_5_90_moveit_config"),
                "config",
                "kinematics.yaml",
            )
        )
        .trajectory_execution(
            file_path=os.path.join(
                get_package_share_directory("abb_irb1200_5_90_moveit_config"),
                "config", 
                "moveit_controllers.yaml",
            ),
            moveit_manage_controllers=False,
        )
        .planning_pipelines(
            pipelines=["ompl"]
        )
        .planning_scene_monitor(
            publish_planning_scene=True,
            publish_geometry_updates=True,
            publish_state_updates=True,
            publish_transforms_updates=True,
        )
        .joint_limits(
            file_path=os.path.join(
                get_package_share_directory("abb_irb1200_5_90_moveit_config"),
                "config",
                "joint_limits.yaml",
            )
        )
        .to_moveit_configs()
    )
    
    # Robot state publisher (for MoveIt2)
    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="both",
        parameters=[moveit_config.robot_description],
    )
    
    # MoveIt2 move_group node
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": False},
        ],
        arguments=["--log-level", "info"],
    )
    
    # RViz2 with MoveIt2 plugins
    # NOTE: Using IRB1200 RViz config as CRB15000 config is not yet available
    rviz_config = os.path.join(
        get_package_share_directory("abb_irb1200_5_90_moveit_config"),
        "rviz",
        "moveit.rviz",
    )
    
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2_moveit",
        output="log",
        arguments=["-d", rviz_config],
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": False},
        ],
        condition=IfCondition(launch_rviz),
    )
    
    # Static TF from world to base_link
    static_tf_node = Node(
        package="tf2_ros", 
        executable="static_transform_publisher",
        name="static_transform_publisher",
        output="log",
        arguments=["0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "world", "base_link"],
    )
    
    nodes_to_start = [
        robot_state_pub_node, 
        static_tf_node,
        move_group_node,
        rviz_node,
    ]
    
    return nodes_to_start
            package="moveit_ros_move_group",
            executable="move_group",
            output="screen",
            parameters=[
                moveit_config.to_dict(),
                {"use_sim_time": False},
            ],
        )
        nodes_to_start.append(move_group_node)

        # RViz Node
        rviz_config_file = os.path.join(
            get_package_share_directory("abb_irb1200_5_90_moveit_config"),
            "rviz",
            "moveit.rviz"
        )
        
        rviz_node = Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            output="log",
            arguments=["-d", rviz_config_file],
            parameters=[
                moveit_config.to_dict(),
                {"use_sim_time": False},
            ],
        )
        nodes_to_start.append(rviz_node)

        # Static TF
        static_tf_node = Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="static_transform_publisher",
            output="log",
            arguments=["0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "world", "base_link"],
        )
        nodes_to_start.append(static_tf_node)

        # Robot State Publisher
        robot_state_pub_node = Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            output="both",
            parameters=[moveit_config.robot_description],
        )
        nodes_to_start.append(robot_state_pub_node)
    
    return nodes_to_start


def generate_launch_description():
    declared_arguments = []
    
    declared_arguments.append(
        DeclareLaunchArgument(
            "robot_xacro_file",
            default_value="crb15000_5_95.xacro",
            description="Xacro describing the robot.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "support_package",
            default_value="abb_crb15000_support",
            description="Name of the support package",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "moveit_config_package",
            default_value="abb_crb15000_5_95_moveit_config",
            description="Name of the MoveIt config package",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "moveit_config_file",
            default_value="crb15000_5_95.srdf.xacro",
            description="Name of the SRDF file",
        )
    )

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )

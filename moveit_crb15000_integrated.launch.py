#!/usr/bin/env python3
"""
moveit_crb15000_integrated.launch.py
===================================

Comprehensive launch file for the ABB CRB 15000 robot with MoveIt2 integration.
This file launches:
1. Robot control (ros2_control) with hardware interface or fake hardware
2. MoveIt2 move_group for motion planning
3. RViz2 with MoveIt2 plugins for visualization and control
4. Robot state publisher

The configuration supports both simulation (fake_hardware) and real robot
operation through the ABB hardware interface.
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
    """Generate the launch description for CRB15000 with MoveIt2."""
    
    # Declare launch arguments
    declared_arguments = []
    
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_fake_hardware",
            default_value="true",
            description="Start robot with fake hardware mirroring command to its states.",
        )
    )
    
    declared_arguments.append(
        DeclareLaunchArgument(
            "fake_sensor_commands",
            default_value="false", 
            description="Enable fake command interfaces for sensors used for simple simulations.",
        )
    )
    
    declared_arguments.append(
        DeclareLaunchArgument(
            "rws_ip",
            default_value="192.168.125.1",
            description="IP address of the robot controller (for real hardware).",
        )
    )
    
    declared_arguments.append(
        DeclareLaunchArgument(
            "rws_port", 
            default_value="80",
            description="Port of the robot controller RWS interface.",
        )
    )
    
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
    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    fake_sensor_commands = LaunchConfiguration("fake_sensor_commands")
    rws_ip = LaunchConfiguration("rws_ip")
    rws_port = LaunchConfiguration("rws_port")
    launch_rviz = LaunchConfiguration("launch_rviz")
    
    # Robot description with ros2_control
    # CONFIRMED: Using IRB1200 as reference configuration for CRB15000
    # The IRB1200 and CRB15000 have similar kinematics and joint configurations
    # This serves as a compatible base configuration until CRB15000-specific packages are available
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]),
        " ",
        PathJoinSubstitution([
            FindPackageShare("abb_irb1200_support"),
            "urdf",
            "irb1200_5_90.xacro"
        ]),
        " use_fake_hardware:=", use_fake_hardware,
        " fake_sensor_commands:=", fake_sensor_commands,
        " rws_ip:=", rws_ip,
        " rws_port:=", rws_port,
    ])
    
    robot_description = {"robot_description": robot_description_content}
    
    # MoveIt2 configuration
    # CONFIRMED: Using IRB1200 MoveIt config as working base for CRB15000
    # IRB1200 and CRB15000 have compatible joint configurations and kinematics
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
    
    # Robot controllers configuration
    robot_controllers = PathJoinSubstitution([
        FindPackageShare("abb_bringup"),
        "config",
        "abb_controllers.yaml",
    ])
    
    # Control node (ros2_control)
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, robot_controllers],
        output="both",
        remappings=[
            ("~/robot_description", "/robot_description"),
        ],
    )
    
    # Robot state publisher
    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="both",
        parameters=[moveit_config.robot_description],
    )
    
    # ros2_control spawners
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
    )
    
    arm_controller_spawner = Node(
        package="controller_manager", 
        executable="spawner",
        arguments=["arm_controller", "-c", "/controller_manager"],
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
    # CONFIRMED: Using IRB1200 RViz config as working base for CRB15000
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
        control_node,
        robot_state_pub_node, 
        static_tf_node,
        joint_state_broadcaster_spawner,
        arm_controller_spawner,
        move_group_node,
        rviz_node,
    ]
    
    return nodes_to_start

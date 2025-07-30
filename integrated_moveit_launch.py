# Integrated Launch File for CRB15000 with MoveIt2
# This launch file starts both the robot control and MoveIt2 motion planning

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    declared_arguments = []
    
    # Robot Configuration Arguments
    declared_arguments.append(
        DeclareLaunchArgument(
            "description_package",
            default_value="abb_crb15000_support",
            description="Description package with robot URDF/XACRO files.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "description_file",
            default_value="crb15000_5_95.xacro",
            description="URDF/XACRO description file with the robot.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "moveit_config_package", 
            default_value="abb_crb15000_5_95_moveit_config",
            description="MoveIt configuration package for the robot.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_fake_hardware",
            default_value="true",
            description="Start robot with fake hardware mirroring command to its states.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "rws_ip",
            default_value="None",
            description="IP of RWS computer. Used only if 'use_fake_hardware' parameter is false.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "launch_rviz",
            default_value="true",
            description="Launch RViz with MoveIt plugin?",
        )
    )
    
    # Initialize Arguments
    description_package = LaunchConfiguration("description_package")
    description_file = LaunchConfiguration("description_file")
    moveit_config_package = LaunchConfiguration("moveit_config_package")
    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    rws_ip = LaunchConfiguration("rws_ip")
    launch_rviz = LaunchConfiguration("launch_rviz")
    
    # Robot Control Launch - using abb_bringup package patterns
    robot_control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("abb_bringup"),
                "launch",
                "abb_control.launch.py"
            ])
        ]),
        launch_arguments={
            "description_package": description_package,
            "description_file": description_file,
            "moveit_config_package": moveit_config_package,
            "use_fake_hardware": use_fake_hardware,
            "rws_ip": rws_ip,
            "launch_rviz": "false",  # We'll launch RViz with MoveIt separately
        }.items(),
    )
    
    # MoveIt Launch - using abb_bringup package patterns
    moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("abb_bringup"),
                "launch", 
                "abb_moveit.launch.py"
            ])
        ]),
        launch_arguments={
            "robot_xacro_file": description_file,
            "support_package": description_package,
            "moveit_config_package": moveit_config_package,
            "moveit_config_file": "crb15000_5_95.srdf.xacro",
        }.items(),
    )
    
    # Motion Planning Interface Node
    # This node will provide high-level motion planning services
    motion_planning_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        name="move_group",
        output="screen",
        parameters=[
            {"use_sim_time": False},
            {"publish_planning_scene": True},
            {"publish_geometry_updates": True},
            {"publish_state_updates": True},
            {"publish_transforms_updates": True},
        ],
    )
    
    nodes_to_start = [
        robot_control_launch,
        moveit_launch,
    ]
    
    return LaunchDescription(declared_arguments + nodes_to_start)

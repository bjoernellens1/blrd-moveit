#!/usr/bin/env python3
"""
launch_moveit_crb15000.py
=========================

Launch script for MoveIt2 with ABB CRB15000 robot configuration.

This script sets up and launches the complete MoveIt2 stack for the ABB CRB15000 
collaborative robot, including:
- MoveIt motion planning framework  
- Robot state publisher
- Joint state broadcaster
- Planning scene monitor
- Move group interface

The script uses the abb_ros2 packages in the testing branch which includes
support for the CRB15000 robot model.
"""

import os
import sys
import time
import rclpy
from rclpy.node import Node
import subprocess


class MoveItLauncher(Node):
    """Node to launch and monitor MoveIt2 services for CRB15000."""
    
    def __init__(self):
        super().__init__('moveit_crb15000_launcher')
        self.get_logger().info("Initializing MoveIt2 launcher for ABB CRB15000")
        
        # Robot configuration parameters (verified against abb_ros2 testing branch)
        self.robot_config = {
            'robot_xacro_file': 'crb15000_5_95.xacro',
            'support_package': 'abb_crb15000_support', 
            'moveit_config_package': 'abb_crb15000_5_95_moveit_config',
            'moveit_config_file': 'abb_crb15000_5_95.srdf.xacro'
        }
        
    def launch_moveit(self):
        """Launch the MoveIt2 stack with CRB15000 configuration."""
        self.get_logger().info("Launching MoveIt2 for ABB CRB15000...")
        
        # Build the launch command
        cmd = [
            'ros2', 'launch', 'abb_bringup', 'abb_moveit.launch.py',
            f"robot_xacro_file:={self.robot_config['robot_xacro_file']}",
            f"support_package:={self.robot_config['support_package']}",
            f"moveit_config_package:={self.robot_config['moveit_config_package']}", 
            f"moveit_config_file:={self.robot_config['moveit_config_file']}"
        ]
        
        self.get_logger().info(f"Executing command: {' '.join(cmd)}")
        
        try:
            # Launch MoveIt as a subprocess
            self.moveit_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.get_logger().info("MoveIt2 launch initiated successfully")
            
            # Monitor the process output
            while self.moveit_process.poll() is None:
                output = self.moveit_process.stdout.readline()
                if output:
                    self.get_logger().info(f"MoveIt: {output.strip()}")
                time.sleep(0.1)
                    
        except Exception as e:
            self.get_logger().error(f"Failed to launch MoveIt2: {str(e)}")
            return False
            
        return True


def main():
    """Main entry point for the MoveIt launcher."""
    try:
        rclpy.init()
        
        launcher = MoveItLauncher()
        
        # Launch MoveIt in a separate thread so we can keep the node spinning
        import threading
        moveit_thread = threading.Thread(target=launcher.launch_moveit, daemon=True)
        moveit_thread.start()
        
        # Keep the node spinning
        try:
            rclpy.spin(launcher)
        except KeyboardInterrupt:
            launcher.get_logger().info("Shutting down MoveIt launcher...")
            
    except Exception as e:
        print(f"Error in main: {str(e)}")
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
ros_moveit_service.py
====================

Complete ROS2/MoveIt2 service for ABB CRB15000 robot integration.

This service combines:
1. MoveIt2 motion planning and execution stack
2. ROS interface for Streamlit integration  
3. Robot state monitoring and control
4. WebSocket communication for real-time updates

The service launches MoveIt2 with the CRB15000 configuration and provides
a simple API interface for external applications (like Streamlit) to 
interact with the robot through motion planning and execution.
"""

import os
import sys
import time
import json
import threading
import subprocess
import asyncio
import websockets
from typing import Dict, List, Optional

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

# Import our existing ROS interface
try:
    from ros_interface import RosInterface
except ImportError:
    # If running in different directory structure
    sys.path.append('/app')
    from ros_interface import RosInterface


class MoveItCRB15000Service(Node):
    """
    Complete service for MoveIt2 + CRB15000 robot integration.
    
    This service:
    - Launches MoveIt2 with CRB15000 configuration
    - Provides ROS interface for joint state monitoring
    - Exposes WebSocket API for real-time communication
    - Handles motion planning and execution requests
    """
    
    def __init__(self):
        super().__init__('moveit_crb15000_service')
        self.get_logger().info("Starting MoveIt2 CRB15000 service...")
        
        # Robot configuration for CRB15000 (verified against abb_ros2 testing branch)
        self.robot_config = {
            'robot_xacro_file': 'crb15000_5_95.xacro',
            'support_package': 'abb_crb15000_support',
            'moveit_config_package': 'abb_crb15000_5_95_moveit_config', 
            'moveit_config_file': 'abb_crb15000_5_95.srdf.xacro'
        }
        
        # Initialize ROS interface for joint monitoring
        self.ros_interface = RosInterface()
        
        # MoveIt process handle
        self.moveit_process = None
        
        # WebSocket connections
        self.websocket_clients = set()
        
        # Service state
        self.service_ready = False
        
    def launch_moveit(self):
        """Launch MoveIt2 stack for CRB15000."""
        self.get_logger().info("Launching MoveIt2 for ABB CRB15000...")
        
        # Build launch command
        cmd = [
            'ros2', 'launch', 'abb_bringup', 'abb_moveit.launch.py',
            f"robot_xacro_file:={self.robot_config['robot_xacro_file']}",
            f"support_package:={self.robot_config['support_package']}", 
            f"moveit_config_package:={self.robot_config['moveit_config_package']}",
            f"moveit_config_file:={self.robot_config['moveit_config_file']}"
        ]
        
        self.get_logger().info(f"Launch command: {' '.join(cmd)}")
        
        try:
            # Start MoveIt process
            self.moveit_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.get_logger().info("MoveIt2 process started")
            
            # Monitor MoveIt startup
            startup_timeout = 30  # seconds
            start_time = time.time()
            
            while time.time() - start_time < startup_timeout:
                if self.moveit_process.poll() is not None:
                    self.get_logger().error("MoveIt process exited unexpectedly")
                    return False
                    
                # Check if MoveIt services are available
                result = subprocess.run(
                    ['ros2', 'service', 'list'], 
                    capture_output=True, 
                    text=True
                )
                
                if '/move_group/plan_kinematic_path' in result.stdout:
                    self.get_logger().info("MoveIt2 services detected - startup complete")
                    self.service_ready = True
                    return True
                    
                time.sleep(2)
                
            self.get_logger().warn("MoveIt startup timeout - continuing anyway")
            self.service_ready = True
            return True
            
        except Exception as e:
            self.get_logger().error(f"Failed to launch MoveIt2: {str(e)}")
            return False
    
    def start_ros_interface(self):
        """Start the ROS interface for joint state monitoring."""
        try:
            self.ros_interface.start()
            self.get_logger().info("ROS interface started - monitoring joint states")
        except Exception as e:
            self.get_logger().error(f"Failed to start ROS interface: {str(e)}")
    
    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections for real-time communication."""
        self.websocket_clients.add(websocket)
        self.get_logger().info(f"WebSocket client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = await self.handle_websocket_message(data)
                    await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'error': 'Invalid JSON format'
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        'error': f'Message handling error: {str(e)}'
                    }))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.websocket_clients.discard(websocket)
            self.get_logger().info("WebSocket client disconnected")
    
    async def handle_websocket_message(self, data: Dict) -> Dict:
        """Process WebSocket messages and return responses."""
        try:
            msg_type = data.get('type', '')
            
            if msg_type == 'get_joint_state':
                positions = self.ros_interface.get_current_joint_positions()
                return {
                    'type': 'joint_state_response',
                    'joint_positions': positions,
                    'timestamp': time.time()
                }
                
            elif msg_type == 'plan_motion':
                target_positions = data.get('target_positions', {})
                trajectory = self.ros_interface.plan_to_joint_positions(target_positions)
                
                return {
                    'type': 'motion_plan_response',
                    'success': trajectory is not None,
                    'trajectory': list(trajectory) if trajectory else None
                }
                
            elif msg_type == 'execute_motion':
                trajectory_points = data.get('trajectory_points', [])
                success = self.ros_interface.execute_trajectory(trajectory_points)
                
                return {
                    'type': 'motion_execution_response', 
                    'success': success
                }
                
            elif msg_type == 'get_service_status':
                return {
                    'type': 'service_status_response',
                    'moveit_ready': self.service_ready,
                    'ros_interface_active': self.ros_interface.node is not None,
                    'connected_clients': len(self.websocket_clients)
                }
                
            else:
                return {
                    'type': 'error',
                    'message': f'Unknown message type: {msg_type}'
                }
                
        except Exception as e:
            return {
                'type': 'error',
                'message': f'Error processing message: {str(e)}'
            }
    
    async def broadcast_joint_updates(self):
        """Periodically broadcast joint state updates to all WebSocket clients."""
        while True:
            try:
                if self.websocket_clients and self.ros_interface.node:
                    positions = self.ros_interface.get_current_joint_positions()
                    
                    if positions:  # Only broadcast if we have joint data
                        message = json.dumps({
                            'type': 'joint_state_update',
                            'joint_positions': positions,
                            'timestamp': time.time()
                        })
                        
                        # Send to all connected clients
                        disconnected = set()
                        for client in self.websocket_clients:
                            try:
                                await client.send(message)
                            except websockets.exceptions.ConnectionClosed:
                                disconnected.add(client)
                        
                        # Remove disconnected clients
                        self.websocket_clients -= disconnected
                        
                await asyncio.sleep(0.1)  # 10Hz update rate
                
            except Exception as e:
                self.get_logger().error(f"Error broadcasting joint updates: {str(e)}")
                await asyncio.sleep(1)
    
    async def start_websocket_server(self, host='0.0.0.0', port=8766):
        """Start the WebSocket server for real-time communication."""
        self.get_logger().info(f"Starting WebSocket server on {host}:{port}")
        
        # Start the server
        server = await websockets.serve(self.websocket_handler, host, port)
        
        # Start broadcasting task
        broadcast_task = asyncio.create_task(self.broadcast_joint_updates())
        
        self.get_logger().info("WebSocket server ready")
        
        # Keep server running
        await server.wait_closed()
    
    def start_service(self):
        """Start the complete MoveIt2 CRB15000 service."""
        self.get_logger().info("Initializing MoveIt2 CRB15000 service...")
        
        # Start MoveIt in background thread
        moveit_thread = threading.Thread(target=self.launch_moveit, daemon=True)
        moveit_thread.start()
        
        # Wait a bit for MoveIt to start
        time.sleep(5)
        
        # Start ROS interface
        self.start_ros_interface()
        
        # Start WebSocket server in asyncio event loop
        asyncio.run(self.start_websocket_server())


def main():
    """Main entry point for the MoveIt CRB15000 service."""
    try:
        rclpy.init()
        
        service = MoveItCRB15000Service()
        
        # Start the service (this will block)
        service.start_service()
        
    except KeyboardInterrupt:
        print("Service interrupted by user")
    except Exception as e:
        print(f"Service error: {str(e)}")
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

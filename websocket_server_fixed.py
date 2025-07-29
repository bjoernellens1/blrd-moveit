"""
WebSocket server for real-time robot joint position updates.
Bridges ROS 2 joint states with Three.js visualization.
"""

import asyncio
import websockets
import json
import threading
import time
from typing import Dict, Optional
import numpy as np

class RobotWebSocketServer:
    """WebSocket server that streams robot joint positions to Three.js client."""
    
    def __init__(self, ros_interface, port: int = 8765):
        """
        Initialize WebSocket server.
        
        Parameters
        ----------
        ros_interface : ROSInterface
            ROS interface for getting joint positions
        port : int
            WebSocket server port
        """
        self.ros_interface = ros_interface
        self.port = port
        self.clients = set()
        self.running = False
        self.server = None
        
    async def register_client(self, websocket, path):
        """Register a new WebSocket client."""
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            print(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast_joint_positions(self):
        """Continuously broadcast joint positions to all clients."""
        while self.running:
            if self.clients:
                try:
                    # Get current joint positions
                    joint_positions = self.ros_interface.get_current_joint_positions()
                    
                    if joint_positions:
                        # Create message
                        message = {
                            'type': 'joint_update',
                            'timestamp': time.time(),
                            'joint_positions': joint_positions
                        }
                        
                        # Broadcast to all clients
                        disconnected = set()
                        for client in self.clients:
                            try:
                                await client.send(json.dumps(message))
                            except websockets.exceptions.ConnectionClosed:
                                disconnected.add(client)
                        
                        # Remove disconnected clients
                        self.clients -= disconnected
                        
                except Exception as e:
                    print(f"Error broadcasting joint positions: {e}")
            
            await asyncio.sleep(0.1)  # 10 Hz update rate
    
    async def start_server(self):
        """Start the WebSocket server."""
        print(f"Starting WebSocket server on port {self.port}")
        self.running = True
        
        try:
            # Start server - bind to all interfaces for Docker compatibility
            self.server = await websockets.serve(
                self.register_client, 
                "0.0.0.0",  # Bind to all interfaces instead of localhost
                self.port
            )
            print(f"WebSocket server successfully started on 0.0.0.0:{self.port}")
            
            # Start broadcasting task
            broadcast_task = asyncio.create_task(self.broadcast_joint_positions())
            
            # Wait for the server to close
            await self.server.wait_closed()
            
        except OSError as e:
            if e.errno == 98:  # Address already in use
                print(f"Port {self.port} is already in use. Trying alternative ports...")
                for alt_port in range(self.port + 1, self.port + 10):
                    try:
                        self.server = await websockets.serve(
                            self.register_client,
                            "0.0.0.0",
                            alt_port
                        )
                        self.port = alt_port
                        print(f"WebSocket server started on alternative port: {alt_port}")
                        broadcast_task = asyncio.create_task(self.broadcast_joint_positions())
                        await self.server.wait_closed()
                        break
                    except OSError:
                        continue
                else:
                    print(f"Could not find available port in range {self.port}-{self.port + 9}")
                    raise
            else:
                raise
    
    def start_in_thread(self):
        """Start the WebSocket server in a separate thread."""
        def run_server():
            asyncio.run(self.start_server())
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        return thread
    
    async def stop_server(self):
        """Stop the WebSocket server."""
        if self.server:
            self.running = False
            self.server.close()
            await self.server.wait_closed()
    
    def get_active_port(self) -> int:
        """Get the actual port the server is running on."""
        return self.port


def start_websocket_server(ros_interface, port: int = 8765) -> RobotWebSocketServer:
    """
    Start a WebSocket server for real-time robot updates.
    
    Parameters
    ----------
    ros_interface : ROSInterface
        ROS interface for getting joint positions
    port : int
        WebSocket server port
        
    Returns
    -------
    RobotWebSocketServer
        The running server instance
    """
    server = RobotWebSocketServer(ros_interface, port)
    server.start_in_thread()
    return server

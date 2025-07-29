#!/usr/bin/env python3
"""
Quick test script to verify WebSocket server functionality.
"""

import asyncio
import websockets
import json

class MockRosInterface:
    """Mock ROS interface for testing."""
    def get_current_joint_positions(self):
        return {
            "joint_1": 0.1,
            "joint_2": 0.2,
            "joint_3": 0.3,
            "joint_4": 0.4,
            "joint_5": 0.5,
            "joint_6": 0.6
        }

async def test_websocket_handler():
    """Test the WebSocket handler function."""
    from websocket_server import RobotWebSocketServer
    
    mock_ros = MockRosInterface()
    server = RobotWebSocketServer(mock_ros, port=8766)
    
    # Test the handler function directly
    class MockWebSocket:
        def __init__(self):
            self.closed = False
        
        async def wait_closed(self):
            await asyncio.sleep(0.1)  # Simulate brief connection
            self.closed = True
    
    mock_ws = MockWebSocket()
    
    try:
        # This should not raise an error if the handler is correct
        await server.handle_client(mock_ws, "/test")
        print("✅ WebSocket handler test passed!")
        return True
    except Exception as e:
        print(f"❌ WebSocket handler test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_websocket_handler())

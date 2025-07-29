#!/usr/bin/env python3
"""
Minimal WebSocket server test to verify the handler approach.
"""

import asyncio
import json

# Mock websockets module structure for testing
class MockWebSocket:
    def __init__(self):
        self.clients = set()
    
    async def serve(self, handler, host, port):
        """Mock websockets.serve function"""
        print(f"Mock server starting on {host}:{port}")
        # Simulate calling the handler
        mock_websocket = MockConnection()
        try:
            await handler(mock_websocket, "/test")
            print("✅ Handler called successfully")
        except Exception as e:
            print(f"❌ Handler failed: {e}")
            raise

class MockConnection:
    async def wait_closed(self):
        await asyncio.sleep(0.1)

class TestWebSocketServer:
    def __init__(self):
        self.clients = set()
        self.running = True
    
    async def _websocket_handler(self, websocket, path):
        """Internal websocket handler that properly handles the connection."""
        await self.handle_client(websocket, path)
    
    async def handle_client(self, websocket, path):
        """Handle a new WebSocket client connection."""
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            print(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def test_handler(self):
        mock_ws = MockWebSocket()
        await mock_ws.serve(self._websocket_handler, "0.0.0.0", 8765)

async def main():
    server = TestWebSocketServer()
    await server.test_handler()

if __name__ == "__main__":
    asyncio.run(main())

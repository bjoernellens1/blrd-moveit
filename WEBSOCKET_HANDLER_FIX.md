# WebSocket Handler Fix

## The Problem
The error `TypeError: RobotWebSocketServer.register_client() missing 1 required positional argument: 'path'` was occurring because the `websockets.serve()` function was trying to call `self.register_client` as a standalone function, but it's a method that requires `self` as the first parameter.

## The Solution
Changed the handler from a direct method reference to a lambda function that properly binds `self`:

### Before (Broken):
```python
self.server = await websockets.serve(
    self.register_client,  # ❌ This doesn't work - missing 'self'
    "0.0.0.0",
    self.port
)
```

### After (Fixed):
```python
self.server = await websockets.serve(
    lambda ws, path: self.handle_client(ws, path),  # ✅ Properly binds 'self'
    "0.0.0.0",
    self.port
)
```

## Changes Made to `websocket_server.py`:

1. **Added proper handler method**:
   ```python
   async def handle_client(self, websocket, path):
       """Handle a new WebSocket client connection."""
       # ... implementation
   ```

2. **Updated websockets.serve calls** (both primary and fallback):
   ```python
   lambda ws, path: self.handle_client(ws, path)
   ```

3. **Kept register_client as alias** for backward compatibility.

## Why This Fixes the Issue
- The lambda function creates a proper closure that captures `self`
- When websockets library calls the handler, it gets the correct signature
- The `self` parameter is properly passed to the method

## Test the Fix
Run `docker compose up --build` and check for the absence of the TypeError in the logs.

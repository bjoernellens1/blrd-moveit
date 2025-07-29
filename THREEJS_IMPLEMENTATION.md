# Three.js Implementation for Real-time Robot Visualization

## Overview

This implementation adds real-time robot visualization using Three.js and WebSocket, eliminating the need for constant page reloads in Streamlit.

## New Files

### 1. `threejs_robot_viewer.py`
- **Purpose**: Creates a Three.js-based 3D robot viewer as a Streamlit component
- **Key Features**:
  - Extracts mesh data from URDF robot models
  - Generates HTML with embedded Three.js visualization
  - WebSocket connectivity for real-time updates
  - Orbit controls for user interaction
  - Connection status indicator

### 2. `websocket_server.py`
- **Purpose**: WebSocket server that bridges ROS 2 joint states with the Three.js client
- **Key Features**:
  - Asynchronous WebSocket server using `websockets` library
  - Continuously broadcasts joint positions to connected clients
  - Automatic client management
  - Threaded execution to run alongside Streamlit

## Modified Files

### 1. `streamlit_app.py`
- **Added**: Visualization mode selector (Plotly vs Three.js)
- **Added**: WebSocket server initialization
- **Added**: Conditional auto-refresh (only for Plotly mode)
- **Improved**: UI with metrics and optional debug information

### 2. `Dockerfile.streamlit`
- **Added**: `websockets` dependency
- **Added**: Copy of new Python files

### 3. `docker-compose.yaml`
- **Added**: Port 8765 exposure for WebSocket server
- **Added**: Mount points for new Python files

## Usage

### Plotly Mode (Static)
- Traditional approach with manual refresh
- Page reloads every `POLL_INTERVAL` seconds
- Debug output available
- Good for development and troubleshooting

### Three.js Mode (Real-time)
- Real-time updates via WebSocket
- No page reloads
- Smooth 3D interaction with orbit controls
- Connection status indicator
- Better performance for continuous monitoring

## Architecture

```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   Streamlit     │◄──────────────►│  Three.js       │
│   Application   │     Port 8765   │  Viewer         │
└─────────────────┘                 └─────────────────┘
         │                                   ▲
         │ ROS Interface                     │
         ▼                                   │
┌─────────────────┐                         │
│   ROS 2         │                         │
│   Joint States  │─────────────────────────┘
└─────────────────┘    Real-time Updates
```

## Key Benefits

1. **Performance**: No page reloads in Three.js mode
2. **Real-time**: Smooth updates as robot moves
3. **Interactive**: 3D navigation with mouse controls
4. **Fallback**: Plotly mode available for debugging
5. **Status**: Connection monitoring and auto-reconnect

## Technical Details

### WebSocket Message Format
```json
{
  "link_frames": {
    "base_link": [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1],
    "link_1": [...]
  }
}
```

### Three.js Transform Updates
- Transforms are applied directly to mesh objects
- Position extracted from translation components (transform[12-14])
- Rotation extracted from rotation matrix components
- Real-time updates without DOM reconstruction

### Connection Handling
- Automatic reconnection on WebSocket disconnect
- Visual status indicator in top-left corner
- Graceful fallback during connection issues

## Testing

To test the implementation:

1. **Build and run**: `docker-compose up --build`
2. **Access**: http://localhost:8501
3. **Switch modes**: Use sidebar selector
4. **Monitor**: Check WebSocket status in Three.js mode
5. **Interact**: Use mouse to orbit, zoom, pan in 3D view

## Future Enhancements

- [ ] Mesh material and color customization
- [ ] Joint limit visualization
- [ ] Trajectory planning overlay
- [ ] Multiple robot support
- [ ] Performance metrics display
- [ ] Mobile-responsive controls

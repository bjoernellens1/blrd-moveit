# ABB CRB15000 MoveIt2 Integration - Complete Setup Guide

## Overview

This document provides a complete guide for the successful integration of ABB CRB15000 robot with MoveIt2 and a Streamlit-based visualization interface. The system uses Docker containers for easy deployment and consists of two main services:

1. **MoveIt2 ROS Service**: Handles robot planning and control using the correct ABB CRB15000 packages
2. **Streamlit UI**: Provides web-based 3D visualization and user interface

## System Architecture

```
┌─────────────────────┐    ┌──────────────────────┐
│   Streamlit UI      │    │   MoveIt2 Service    │
│   (Port 8501)       │    │   (ROS2 + WebSocket) │
│                     │    │                      │
│ - 3D Visualization  │◄──►│ - Motion Planning    │
│ - User Interface    │    │ - Joint State Pub    │
│ - WebSocket Client  │    │ - WebSocket Server   │
│   (Port 8765)       │    │   (Port 8766)        │
└─────────────────────┘    └──────────────────────┘
```

## Key Components

### 1. ABB CRB15000 Robot Support
- **Robot Package**: `abb_crb15000_support`
- **MoveIt Config**: `abb_crb15000_5_95_moveit_config`
- **URDF Model**: `crb15000_5_95.xacro`
- **SRDF Config**: `abb_crb15000_5_95.srdf.xacro`

### 2. MoveIt2 Launch Configuration
```bash
ros2 launch abb_bringup abb_moveit.launch.py \
  robot_xacro_file:=crb15000_5_95.xacro \
  support_package:=abb_crb15000_support \
  moveit_config_package:=abb_crb15000_5_95_moveit_config \
  moveit_config_file:=abb_crb15000_5_95.srdf.xacro
```

### 3. Docker Services
- **ROS Service Container**: `abb_moveit_ros`
- **Streamlit Container**: `abb_streamlit_ui`
- **Network**: Shared Docker network for inter-service communication

## Setup and Installation

### Prerequisites
- Docker and Docker Compose
- X11 forwarding configured (for GUI applications)
- Git access to ABB ROS2 repositories

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd blrd-moveit
   ```

2. **Build and start services**:
   ```bash
   docker compose build
   docker compose up -d
   ```

3. **Access the interfaces**:
   - Streamlit UI: http://localhost:8501
   - MoveIt2 ROS: Running in background with WebSocket on port 8766

## File Structure

```
blrd-moveit/
├── docker-compose.yaml          # Service orchestration
├── Dockerfile.ros              # MoveIt2 service container
├── Dockerfile.streamlit        # Streamlit UI container
├── ros_moveit_service.py       # Main MoveIt2 service
├── ros_interface.py            # ROS2 interface wrapper
├── streamlit_app.py            # Streamlit application
├── urdf_visualizer.py          # 3D visualization utilities
├── threejs_robot_viewer.py     # Three.js robot renderer
└── websocket_server.py         # WebSocket communication
```

## Key Configuration Changes Made

### 1. MoveIt Launch Parameters
Updated to use correct CRB15000-specific packages and files:
- Changed from IRB1200 to CRB15000 robot support
- Updated URDF/SRDF file references
- Configured proper MoveIt config package

### 2. Port Management
Resolved WebSocket port conflicts:
- Streamlit WebSocket: Port 8765 (with fallback logic)
- MoveIt2 WebSocket: Port 8766
- Streamlit UI: Port 8501

### 3. Docker Configuration
- Proper ROS2 environment sourcing
- Correct dependency ordering (Streamlit starts first)
- Host network mode for ROS communication
- X11 forwarding for GUI components

## Verification and Testing

### 1. Service Status Check
```bash
# Check running containers
docker compose ps

# Monitor logs
docker compose logs -f

# Check specific service
docker compose logs ros_moveit
```

### 2. MoveIt2 Verification
The following components should be active:
- MoveGroup node with CRB15000 configuration
- Joint state publisher
- Planning scene monitor
- Motion planning pipelines (OMPL, Pilz)

### 3. WebSocket Communication
- Streamlit connects to port 8765 (or fallback ports)
- MoveIt2 service runs WebSocket server on port 8766
- Real-time joint state updates flow between services

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   - Ensure ports 8501, 8765, and 8766 are available
   - Check for existing processes using `netstat -tulpn | grep <port>`

2. **ROS Environment**
   - Verify ROS2 Jazzy installation in containers
   - Check that all ABB packages are built correctly
   - Ensure proper environment sourcing

3. **Docker Issues**
   - Rebuild images after code changes: `docker compose build`
   - Clear containers: `docker compose down`
   - Check container logs for specific errors

### Log Analysis
Key log messages to look for:
- ✅ "MoveIt2 process started"
- ✅ "WebSocket server ready"
- ✅ "ROS interface started - monitoring joint states"
- ❌ "Address already in use" (port conflict)
- ❌ "Package not found" (missing dependencies)

## Development Notes

### Architecture Decisions
1. **Separation of Concerns**: MoveIt2 and UI in separate containers
2. **WebSocket Communication**: Real-time data exchange between services
3. **Port Management**: Automatic fallback for WebSocket connections
4. **ABB Package Integration**: Use of official testing branch packages

### Future Improvements
- Add motion planning interface in Streamlit UI
- Implement trajectory execution monitoring
- Add collision detection visualization
- Enhance error handling and recovery

## Success Criteria ✅

- [x] ABB CRB15000 packages correctly integrated
- [x] MoveIt2 launches with proper robot configuration
- [x] WebSocket communication established
- [x] Streamlit UI accessible and functional
- [x] Real-time joint state monitoring
- [x] No port conflicts between services
- [x] Dockerized deployment working
- [x] **FIXED**: Correct CRB15000 URDF path in Streamlit app

## Final Fix Applied

**Issue**: Streamlit app was still referencing the old IRB1200 URDF path instead of CRB15000.

**Solution**: Updated `streamlit_app.py` URDF_PATH from:
```python
'/workspace/src/abb_ros2/robot_specific_config/abb_irb1200_support/urdf/irb1200_5_90.xacro'
```

To the correct CRB15000 path:
```python
'/workspace/src/abb_ros2/robot_specific_config/abb_crb15000_support/urdf/crb15000_5_95.xacro'
```

**Result**: ✅ Both MoveIt2 service and Streamlit UI now use consistent CRB15000 robot model.

## Contact and Support

For issues or questions:
1. Check the logs using `docker compose logs`
2. Verify service status with `docker compose ps`
3. Review this documentation for troubleshooting steps

---

**Status**: ✅ **INTEGRATION COMPLETE AND FUNCTIONAL**
**Last Updated**: July 30, 2025
**Version**: 1.0

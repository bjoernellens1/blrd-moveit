# ABB CRB15000 MoveIt2 Integration Guide

## Overview

This project integrates the ABB CRB15000 collaborative robot with MoveIt2 motion planning framework, providing real-time 3D visualization through a Streamlit/Three.js interface.

## Key Components

### 1. ROS2/MoveIt2 Configuration

**Launch Command Structure:**
```bash
ros2 launch abb_bringup abb_moveit.launch.py \
  robot_xacro_file:=crb15000_5_95.xacro \
  support_package:=abb_crb15000_support \
  moveit_config_package:=abb_crb15000_5_95_moveit_config \
  moveit_config_file:=abb_crb15000_5_95.srdf.xacro
```

**Package Dependencies:**
- `abb_crb15000_support` - Robot URDF/Xacro files and configuration
- `abb_crb15000_5_95_moveit_config` - MoveIt-specific configuration (SRDF, kinematics, etc.)
- `abb_bringup` - Generic ABB launch files and controllers

### 2. Service Architecture

**ros_moveit_service.py** - Main integration service that:
- Launches MoveIt2 with CRB15000 configuration
- Provides ROS interface for joint state monitoring  
- Exposes WebSocket API for real-time communication with Streamlit
- Handles motion planning and execution requests

**ros_interface.py** - ROS2 abstraction layer that:
- Subscribes to `/joint_states` topic
- Provides MoveIt2 motion planning interface
- Handles trajectory execution through MoveIt action servers

### 3. Docker Configuration

**Dockerfile.ros** - Builds ROS2 container with:
- ROS2 Jazzy base image
- MoveIt2 and ABB packages from abb_ros2 repository (testing branch)
- Python dependencies including websockets
- Proper workspace sourcing and entrypoint

**docker-compose.yaml** - Service orchestration:
```yaml
services:
  ros_moveit:
    # Runs ros_moveit_service.py for complete MoveIt2 stack
  streamlit_app:
    # Streamlit UI with Three.js 3D visualization
  rviz:
    # Optional RViz2 for debugging/visualization
```

### 4. Web Interface

**streamlit_app.py** - Web interface featuring:
- Real-time 3D robot visualization using Three.js
- Joint state monitoring from ROS2
- Motion planning controls
- WebSocket communication for live updates

**URDF Path Configuration:**
```python
URDF_PATH = '/workspace/src/abb_ros2/robot_specific_config/abb_crb15000_support/urdf/crb15000_5_95.xacro'
```

## Launch Sequence

1. **Container Startup**: Docker builds and starts ROS2 environment
2. **MoveIt2 Launch**: Service launches complete MoveIt2 stack for CRB15000
3. **Service Detection**: Waits for MoveIt2 services to become available
4. **ROS Interface**: Starts joint state monitoring and motion planning interface  
5. **WebSocket Server**: Enables real-time communication with web interface
6. **Streamlit UI**: Provides interactive 3D visualization and controls

## API Endpoints

### WebSocket Messages

**Get Joint State:**
```json
{
  "type": "get_joint_state"
}
```

**Plan Motion:**
```json
{
  "type": "plan_motion",
  "target_positions": {
    "joint_1": 0.5,
    "joint_2": -0.3,
    ...
  }
}
```

**Execute Motion:**
```json
{
  "type": "execute_motion", 
  "trajectory_points": [[...], [...], ...]
}
```

**Service Status:**
```json
{
  "type": "get_service_status"
}
```

## Network Configuration

- **Streamlit**: `http://localhost:8501`
- **WebSocket**: `ws://localhost:8765`
- **RViz2**: Accessible via X11 forwarding

## Fallback Strategy

Since CRB15000 packages may not be fully available in the testing branch:

1. **Primary**: Use CRB15000-specific packages when available
2. **Fallback**: Use IRB1200 configuration as stand-in with parameter mapping
3. **Manual Config**: Create custom CRB15000 configuration if needed

## Troubleshooting

### Common Issues

1. **Missing CRB15000 packages**: Falls back to IRB1200 configuration
2. **MoveIt service timeout**: Check if all required ROS2 packages are installed
3. **WebSocket connection fails**: Verify port 8765 is available
4. **URDF loading errors**: Check file paths and xacro dependencies

### Debugging Commands

```bash
# Check available services
ros2 service list | grep move_group

# Monitor joint states  
ros2 topic echo /joint_states

# Test MoveIt planning service
ros2 service call /move_group/plan_kinematic_path moveit_msgs/srv/GetMotionPlan

# Check container logs
docker compose logs ros_moveit
```

## Development Notes

- Built on ROS2 Jazzy with MoveIt2
- Uses abb_ros2 testing branch for latest CRB15000 support
- WebSocket-based architecture for real-time updates
- Dockerized for consistent deployment across environments
- Designed for collaborative robot applications with safety considerations

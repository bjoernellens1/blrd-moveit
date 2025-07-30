# ABB CRB15000/IRB1200 MoveIt2 Integration - Quick Start Guide

## Overview
This guide helps you run the complete ABB robot MoveIt2 integration with Streamlit UI and real-time 3D visualization.

## System Architecture
- **ROS Service**: MoveIt2 motion planning and execution with IRB1200 config (CRB15000 stand-in)
- **Streamlit Service**: Web UI for robot control and trajectory planning
- **RViz Service**: Traditional ROS visualization (optional)
- **WebSocket Server**: Real-time data streaming between ROS and Streamlit

## Prerequisites
1. Docker and Docker Compose installed
2. X11 forwarding enabled for GUI applications
3. NVIDIA Docker runtime (if using GPU acceleration)

## Quick Start

### 1. Start the Complete System
```bash
# Build and start all services
docker compose up --build

# Or start in background
docker compose up -d --build
```

### 2. Access the Interfaces
- **Streamlit UI**: http://localhost:8501
- **WebSocket Server**: ws://localhost:8765
- **RViz** (optional): `docker compose --profile rviz up rviz`

### 3. Development Access
```bash
# Interactive shell with ROS environment
docker compose --profile dev run dev

# Inside the container, you can:
source /opt/ros/humble/setup.bash
source /workspace/abb_ros2/install/setup.bash
ros2 launch moveit_crb15000_integrated.launch.py
```

## Service Details

### Main Services (Always Running)
- `ros_moveit`: Core ROS2/MoveIt2 service with robot planning
- `streamlit_app`: Web UI and WebSocket server

### Optional Services (Use Profiles)
- `rviz`: ROS visualization (`--profile rviz`)
- `dev`: Development shell (`--profile dev`)

## Common Commands

### Start Specific Services
```bash
# Only Streamlit UI
docker compose up streamlit_app

# Only ROS/MoveIt2
docker compose up ros_moveit

# Add RViz for visualization
docker compose --profile rviz up rviz
```

### Build and Development
```bash
# Rebuild containers
docker compose build

# View logs
docker compose logs -f ros_moveit
docker compose logs -f streamlit_app

# Stop all services
docker compose down
```

### Testing Individual Components
```bash
# Test ROS interface directly
docker compose --profile dev run dev python3 ros_interface.py

# Test Streamlit app
docker compose run streamlit_app streamlit run streamlit_app.py

# Test WebSocket server
docker compose run streamlit_app python3 websocket_server.py
```

## Troubleshooting

### X11/Display Issues
```bash
# Allow X11 forwarding
xhost +local:docker

# Check DISPLAY variable
echo $DISPLAY
```

### ROS Communication Issues
```bash
# Check ROS domain
export ROS_DOMAIN_ID=0

# List ROS topics
docker compose --profile dev run dev ros2 topic list

# Check robot state
docker compose --profile dev run dev ros2 topic echo /joint_states
```

### Container Access
```bash
# Access running container
docker exec -it abb_moveit_ros bash
docker exec -it abb_streamlit_ui bash

# Check container status
docker compose ps
```

## Configuration Files
- `docker-compose.yaml`: Service orchestration
- `Dockerfile.ros`: ROS2/MoveIt2 environment
- `Dockerfile.streamlit`: Python/Streamlit environment
- `moveit_crb15000_integrated.launch.py`: MoveIt2 launch configuration
- `ros_interface.py`: ROS2/MoveIt2 Python interface
- `streamlit_app.py`: Web UI application

## Known Issues & Workarounds
1. **CRB15000 Config Missing**: Using IRB1200 as compatible stand-in
2. **Package Dependencies**: Some ABB packages may need manual installation
3. **GPU Support**: Ensure NVIDIA Docker runtime is properly configured

## Next Steps
1. Test motion planning in Streamlit UI
2. Verify RViz2 visualization
3. Test real robot connection (if available)
4. Customize planning parameters as needed

For detailed status and implementation notes, see `MOVEIT_STATUS_REPORT.md`.

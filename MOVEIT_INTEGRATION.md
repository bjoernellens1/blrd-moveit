# ABB CRB15000 MoveIt2 Integration

This project integrates MoveIt2 motion planning with the ABB CRB15000 robot, providing real-time 3D visualization through both RViz2 and a custom Streamlit/Three.js interface.

## Features

### 🤖 MoveIt2 Integration
- **Motion Planning**: Full MoveIt2 integration with OMPL planners
- **Trajectory Execution**: Real trajectory execution through ros2_control
- **Planning Groups**: Pre-configured planning groups for the CRB15000 manipulator
- **Collision Detection**: Built-in collision checking and avoidance

### 🎮 Dual Visualization
- **RViz2**: Professional robotics visualization with MoveIt2 plugins
  - Interactive markers for end-effector control
  - Trajectory visualization and editing
  - Planning scene management
  - Real-time joint state display

- **Streamlit/Three.js**: Web-based real-time visualization
  - Live WebSocket updates
  - Interactive joint sliders for planning
  - Mesh-based robot rendering
  - Motion planning and execution controls

### 🔌 Hardware Support
- **Simulation Mode**: Fake hardware for development and testing
- **Real Hardware**: Direct connection to ABB robot controllers via RWS
- **Hybrid Operation**: Switch between modes without code changes

## Quick Start

### Prerequisites
- Docker and Docker Compose
- X11 forwarding for GUI applications (Linux) or XQuartz (macOS)
- ABB robot controller with RWS enabled (for real hardware)

### 1. Launch in Simulation Mode
```bash
# Simple simulation startup
./launch_moveit.sh sim

# Simulation without RViz (lighter resource usage)
./launch_moveit.sh sim --no-rviz
```

### 2. Connect to Real Hardware
```bash
# Connect to robot controller at default IP
./launch_moveit.sh real

# Connect to robot at custom IP
./launch_moveit.sh real --rws-ip 192.168.1.100
```

### 3. Access the Interfaces
- **Streamlit Web UI**: http://localhost:8501
- **RViz2**: Launches automatically in the Docker container
- **WebSocket Server**: Port 8765 (for Three.js real-time updates)

## Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    ROS 2 Core    │    │   ABB Robot     │
│   Web UI        │◄───┤                  │◄───┤   Controller    │
│                 │    │  • ros2_control   │    │   (RWS/EGM)     │
└─────────────────┘    │  • MoveIt2        │    └─────────────────┘
                       │  • Joint States   │
┌─────────────────┐    │  • TF Tree        │    ┌─────────────────┐
│     RViz2       │◄───┤                  │    │   Simulation    │
│   Visualization │    └──────────────────┘    │  (fake_hardware) │
└─────────────────┘                            └─────────────────┘
```

### MoveIt2 Configuration
- **Planning Pipeline**: OMPL with RRTConnect, RRTstar, PRM
- **Kinematics**: KDL kinematics solver for CRB15000
- **Controllers**: Joint trajectory controller for smooth motion
- **Planning Groups**: "manipulator" group for the 6-DOF arm

### File Structure
```
.
├── docker-compose.yaml              # Multi-container orchestration
├── Dockerfile.ros                   # ROS 2 + MoveIt2 environment
├── Dockerfile.streamlit             # Streamlit web interface
├── moveit_crb15000_integrated.launch.py  # Main MoveIt2 launch file
├── launch_moveit.sh                 # Convenient launch script
├── ros_interface.py                 # Python ROS 2 interface with MoveIt2
├── streamlit_app.py                 # Web UI with planning controls
├── websocket_server.py              # Real-time data streaming
└── urdf_visualizer.py               # 3D rendering utilities
```

## Usage Guide

### Motion Planning with Streamlit UI

1. **Open the Web Interface**: Navigate to http://localhost:8501
2. **Set Target Positions**: Use the joint sliders in the sidebar to set target positions
3. **Plan Motion**: Click "Plan Motion" to compute a trajectory
4. **Execute**: Click "Execute" to send the planned trajectory to the robot
5. **Monitor**: Watch real-time execution in both RViz2 and the web interface

### Advanced RViz2 Controls

1. **Interactive Markers**: Drag the end-effector to set goals
2. **Planning**: Use the MoveIt2 Motion Planning panel
3. **Scene Objects**: Add collision objects for advanced planning
4. **Trajectory Editing**: Modify planned trajectories before execution

### Configuration Options

#### Environment Variables (docker-compose.yaml)
```yaml
environment:
  USE_FAKE_HARDWARE: "true"     # true for simulation, false for real robot
  RWS_IP: "192.168.125.1"       # Robot controller IP address
  RWS_PORT: "80"                # Robot controller RWS port
```

#### Launch Parameters
```bash
# All available parameters
ros2 launch moveit_crb15000_integrated.launch.py \
    use_fake_hardware:=true \
    rws_ip:=192.168.125.1 \
    rws_port:=80 \
    launch_rviz:=true
```

## Development

### Building and Testing

```bash
# Build Docker images
./launch_moveit.sh build

# Rebuild from scratch
./launch_moveit.sh build --rebuild

# View logs
./launch_moveit.sh logs

# Open development shell
./launch_moveit.sh shell
```

### Customization

#### Adding New Planning Groups
Edit the SRDF file in the MoveIt2 configuration package:
```xml
<!-- In abb_crb15000_5_95_moveit_config/config/abb_crb15000_5_95.srdf.xacro -->
<group name="manipulator">
    <joint name="joint_1" />
    <joint name="joint_2" />
    <!-- ... -->
</group>
```

#### Modifying Planning Algorithms
Update the OMPL planning configuration:
```yaml
# In abb_crb15000_5_95_moveit_config/config/ompl_planning.yaml
manipulator:
  default_planner_config: RRTConnect
  planner_configs:
    - RRTConnect
    - RRTstar
    - PRM
```

#### Custom Joint Limits
Modify joint limits in the configuration:
```yaml
# In abb_crb15000_5_95_moveit_config/config/joint_limits.yaml
joint_limits:
  joint_1:
    max_velocity: 2.618
    max_acceleration: 8.727
```

## Troubleshooting

### Common Issues

#### 1. RViz2 Not Displaying
- **Symptom**: RViz2 window appears but is blank
- **Solution**: Check X11 forwarding setup
```bash
# Test X11 forwarding
xhost +local:docker
echo $DISPLAY
```

#### 2. Planning Fails
- **Symptom**: "Planning failed!" message in Streamlit
- **Solution**: Check MoveIt2 services are running
```bash
# In the ROS container
ros2 service list | grep moveit
ros2 topic echo /joint_states
```

#### 3. Robot Connection Failed
- **Symptom**: No joint states received
- **Solution**: Verify robot controller connectivity
```bash
# Test RWS connection
curl http://192.168.125.1/rw/system
```

#### 4. WebSocket Connection Issues
- **Symptom**: Three.js visualization not updating
- **Solution**: Check WebSocket server status
```bash
# Check if WebSocket server is running
docker-compose logs streamlit | grep websocket
```

### Performance Optimization

#### For Better Performance
- Use `--no-rviz` flag if you don't need RViz2
- Reduce planning time in MoveIt2 configuration
- Limit WebSocket update frequency

#### Resource Usage
- **Full setup**: ~4GB RAM, moderate CPU
- **No RViz**: ~2GB RAM, light CPU
- **Real hardware**: Additional network I/O

## API Reference

### RosInterface Class
```python
from ros_interface import RosInterface

ros = RosInterface()
ros.start()

# Get current joint positions
positions = ros.get_current_joint_positions()

# Plan motion to target
target = {"joint_1": 0.5, "joint_2": -0.3, ...}
trajectory = ros.plan_to_joint_positions(target)

# Execute planned trajectory
success = ros.execute_trajectory(trajectory_points)
```

### WebSocket API
Real-time robot data is streamed via WebSocket on port 8765:
```javascript
const ws = new WebSocket('ws://localhost:8765');
ws.onmessage = (event) => {
    const robotData = JSON.parse(event.data);
    // robotData contains joint positions and transforms
};
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test with both simulation and real hardware (if available)
4. Submit a pull request with detailed description

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review Docker and ROS 2 logs
- Ensure all dependencies are properly installed
- Verify network connectivity for real hardware setups

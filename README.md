# ABB CRB15000 MoveIt2 Integration with Streamlit Visualization

A comprehensive ROS2/MoveIt2 integration for ABB industrial robots with real-time web-based 3D visualization using Streamlit and Three.js.

## 🎯 Project Goals

- **Motion Planning**: Integrate MoveIt2 for ABB CRB15000 robot motion planning and execution
- **Real-time Visualization**: Stream joint states and planned trajectories to a web-based 3D viewer
- **Web Interface**: Provide an intuitive Streamlit UI for robot control and monitoring
- **ROS2 Integration**: Utilize real joint state data from ROS2/MoveIt for accurate visualization

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   WebSocket      │    │   ROS2/MoveIt2  │
│   (Port 8501)   │◄──►│   Server         │◄──►│   Planning      │
│                 │    │   (Port 8765)    │    │   & Execution   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Three.js      │    │   Joint State    │    │   RViz2         │
│   3D Viewer     │    │   Streaming      │    │   Visualization │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

1. **Prerequisites**
   ```bash
   # Install Docker and Docker Compose
   sudo apt install docker.io docker-compose-plugin
   
   # Enable X11 forwarding for GUI apps
   xhost +local:docker
   ```

2. **Launch the System**
   ```bash
   # Clone and navigate to project
   cd /path/to/blrd-moveit
   
   # Build and start all services
   docker compose up --build
   ```

3. **Access Interfaces**
   - **Streamlit UI**: http://localhost:8501
   - **RViz2**: `docker compose --profile rviz up rviz`
   - **Development Shell**: `docker compose --profile dev run dev`

## 📁 Project Structure

```
blrd-moveit/
├── docker-compose.yaml              # Service orchestration
├── Dockerfile.ros                   # ROS2/MoveIt2 environment
├── Dockerfile.streamlit             # Streamlit/Python environment
├── ros_interface.py                 # ROS2/MoveIt2 Python interface
├── streamlit_app.py                 # Main Streamlit application
├── websocket_server.py              # Real-time data streaming
├── urdf_visualizer.py               # URDF parsing and processing
├── threejs_robot_viewer.py          # Three.js 3D visualization
├── moveit_crb15000_integrated.launch.py  # MoveIt2 launch file
├── launch_moveit.sh                 # Launch script
├── abb_ros2/                        # ABB robot packages (submodule)
├── QUICK_START_GUIDE.md             # Detailed usage instructions
├── MOVEIT_STATUS_REPORT.md          # Implementation status and issues
└── MOVEIT_INTEGRATION.md            # Technical integration details
```

## 🔧 Key Features

### MoveIt2 Integration
- Motion planning using MoveIt2 planning framework
- Support for multiple planning algorithms (RRTConnect, OMPL, etc.)
- Joint state monitoring and trajectory execution
- Collision detection and avoidance

### Web-based Visualization
- Real-time 3D robot visualization using Three.js
- Interactive joint position controls
- Trajectory playback and monitoring
- WebSocket-based data streaming

### Docker Containerization
- Multi-service Docker Compose setup
- Isolated ROS2 and Streamlit environments
- X11 forwarding for GUI applications
- Development and production configurations

## ⚠️ Important Notes

### CRB15000 Configuration Status
**Current Workaround**: The project uses IRB1200 MoveIt2 configuration as a stand-in for CRB15000, as the specific CRB15000 packages are not available in the abb_ros2 repository.

- **IRB1200 Config**: Fully functional as reference implementation
- **CRB15000 Support**: Requires custom URDF and MoveIt2 configuration
- **Migration Path**: IRB1200 → CRB15000 when packages become available

### Known Limitations
1. CRB15000-specific MoveIt2 packages missing from abb_ros2 repo
2. Some advanced MoveIt2 features may require additional configuration
3. Real robot connection requires proper network setup and safety protocols

## 🛠️ Development

### Service Management
```bash
# Start specific services
docker compose up ros_moveit streamlit_app

# View logs
docker compose logs -f ros_moveit

# Interactive development
docker compose --profile dev run dev
```

### Testing Components
```bash
# Test ROS interface
python3 ros_interface.py

# Test WebSocket server
python3 websocket_server.py

# Test Streamlit app
streamlit run streamlit_app.py
```

### Configuration Updates
- **Robot Config**: Edit `moveit_crb15000_integrated.launch.py`
- **UI Settings**: Modify `streamlit_app.py`
- **Docker Services**: Update `docker-compose.yaml`

## 📚 Documentation

- **[Quick Start Guide](QUICK_START_GUIDE.md)**: Step-by-step usage instructions
- **[Status Report](MOVEIT_STATUS_REPORT.md)**: Current implementation status
- **[Integration Details](MOVEIT_INTEGRATION.md)**: Technical implementation notes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes using the Docker environment
4. Submit a pull request with detailed description

## 📄 License

[Add your license information here]

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section in `QUICK_START_GUIDE.md`
2. Review known issues in `MOVEIT_STATUS_REPORT.md`
3. Open an issue with detailed problem description and logs
#!/bin/bash
#
# launch_moveit.sh
# ================
#
# Convenient script to launch the ABB CRB15000 robot with MoveIt2 in different modes.
# This script provides options for simulation and real hardware operation.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage function
usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  sim               Start in simulation mode (fake hardware)"
    echo "  real              Start with real hardware connection"
    echo "  rviz              Launch only RViz2 with MoveIt2 plugins"
    echo "  build             Build the Docker images"
    echo "  clean             Clean Docker images and containers"
    echo "  logs              Show container logs"
    echo "  shell             Open shell in ROS container"
    echo ""
    echo "Options:"
    echo "  -h, --help        Show this help message"
    echo "  --rws-ip IP       Set robot controller IP (default: 192.168.125.1)"
    echo "  --rws-port PORT   Set robot controller port (default: 80)"
    echo "  --no-rviz         Don't launch RViz2"
    echo "  --rebuild         Force rebuild Docker images"
    echo ""
    echo "Examples:"
    echo "  $0 sim                                   # Start simulation mode"
    echo "  $0 real --rws-ip 192.168.1.100          # Connect to real robot"
    echo "  $0 sim --no-rviz                        # Simulation without RViz"
    echo "  $0 build --rebuild                      # Force rebuild images"
}

# Default values
COMMAND=""
RWS_IP="192.168.125.1"
RWS_PORT="80"
LAUNCH_RVIZ="true"
REBUILD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        sim|real|rviz|build|clean|logs|shell)
            COMMAND="$1"
            shift
            ;;
        --rws-ip)
            RWS_IP="$2"
            shift 2
            ;;
        --rws-port)
            RWS_PORT="$2"
            shift 2
            ;;
        --no-rviz)
            LAUNCH_RVIZ="false"
            shift
            ;;
        --rebuild)
            REBUILD=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Check if command is provided
if [[ -z "$COMMAND" ]]; then
    print_error "No command provided."
    usage
    exit 1
fi

# Ensure we're in the correct directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker compose &> /dev/null; then
    print_error "Docker Compose is not installed or not in PATH."
    exit 1
fi

# Function to check X11 forwarding setup
check_x11() {
    if [[ -z "$DISPLAY" ]]; then
        print_warning "DISPLAY environment variable is not set."
        print_info "X11 forwarding may not work properly."
    fi
    
    if [[ ! -f "$HOME/.Xauthority" ]]; then
        print_warning "X11 authority file not found at $HOME/.Xauthority"
        print_info "You may need to run 'xauth generate :0 . trusted' or similar."
    fi
}

# Function to build images
build_images() {
    print_info "Building Docker images..."
    
    if [[ "$REBUILD" == "true" ]]; then
        print_info "Forcing rebuild (--no-cache)..."
        docker compose build --no-cache
    else
        docker compose build
    fi
    
    print_success "Docker images built successfully."
}

# Function to clean up
cleanup() {
    print_info "Cleaning up Docker containers and images..."
    docker compose down --remove-orphans
    docker system prune -f
    print_success "Cleanup completed."
}

# Function to show logs
show_logs() {
    print_info "Showing container logs..."
    docker compose logs -f
}

# Function to open shell
open_shell() {
    print_info "Opening shell in ROS container..."
    docker compose exec ros bash
}

# Main execution based on command
case $COMMAND in
    sim)
        print_info "Starting ABB CRB15000 in simulation mode..."
        check_x11
        
        # Set environment variables for simulation
        export USE_FAKE_HARDWARE="true"
        export RWS_IP="$RWS_IP"
        export RWS_PORT="$RWS_PORT"
        
        # Update launch command for simulation
        export MOVEIT_LAUNCH_CMD="ros2 launch /workspace/moveit_crb15000_integrated.launch.py use_fake_hardware:=true rws_ip:=${RWS_IP} rws_port:=${RWS_PORT} launch_rviz:=${LAUNCH_RVIZ}"
        
        print_info "Launching with settings:"
        print_info "  - Fake hardware: enabled"
        print_info "  - RWS IP: $RWS_IP"
        print_info "  - RWS Port: $RWS_PORT"
        print_info "  - RViz: $LAUNCH_RVIZ"
        
        docker compose up
        ;;
        
    real)
        print_info "Starting ABB CRB15000 with real hardware connection..."
        check_x11
        
        # Set environment variables for real hardware
        export USE_FAKE_HARDWARE="false"
        export RWS_IP="$RWS_IP"
        export RWS_PORT="$RWS_PORT"
        
        # Update launch command for real hardware
        export MOVEIT_LAUNCH_CMD="ros2 launch /workspace/moveit_crb15000_integrated.launch.py use_fake_hardware:=false rws_ip:=${RWS_IP} rws_port:=${RWS_PORT} launch_rviz:=${LAUNCH_RVIZ}"
        
        print_info "Launching with settings:"
        print_info "  - Fake hardware: disabled"
        print_info "  - RWS IP: $RWS_IP"
        print_info "  - RWS Port: $RWS_PORT" 
        print_info "  - RViz: $LAUNCH_RVIZ"
        print_warning "Make sure the robot controller is accessible at $RWS_IP:$RWS_PORT"
        
        docker compose up
        ;;
        
    rviz)
        print_info "Launching only RViz2 with MoveIt2 plugins..."
        check_x11
        
        # Set environment variables for RViz-only mode
        export MOVEIT_LAUNCH_CMD="ros2 launch abb_bringup abb_moveit.launch.py robot_xacro_file:=crb15000_5_95.xacro support_package:=abb_crb15000_support moveit_config_package:=abb_crb15000_5_95_moveit_config moveit_config_file:=abb_crb15000_5_95.srdf.xacro"
        
        docker compose up ros
        ;;
        
    build)
        build_images
        ;;
        
    clean)
        cleanup
        ;;
        
    logs)
        show_logs
        ;;
        
    shell)
        open_shell
        ;;
        
    *)
        print_error "Unknown command: $COMMAND"
        usage
        exit 1
        ;;
esac

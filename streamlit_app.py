"""
streamlit_app.py
=================

This file defines a Streamlit web applicati# Path to the URDF or Xacro description of the ABB robot.  Adjust this
# path to point to your local installation of the ABB CRB 1500/15000
# support package.  In the ABB MoveIt configuration, the URDF is
# located in the ``abb_crb15000_support/urdf`` directory, e.g.,
# ``crb15000_5_95.xacro``. Currently using IRB1200 as CRB15000 stand-in.
URDF_PATH = os.environ.get('ABB_URDF_PATH', '/workspace/src/abb_ros2/robot_specific_config/abb_irb1200_support/urdf/irb1200_5_90.xacro')t visualises the
ABB CRB 1500/15000 robot in 3D using real joint state data from
ROS 2. The app depends on the ``RosInterface`` class to subscribe_app.py
=================

This file defines a Streamlit web application that visualises the
ABB CRB 1500/15000 robot in 3D using real joint state data from
RO        if joint_positions:
            link_frames = compute_link_frames(robot, joint_positions)
            fig = create_figure(robot, link_frames)
            fig_placeholder.plotly_chart(fig, use_container_width=True)
            # Display current joint positions as a table
            table_data = {name: [pos] for name, pos in joint_positions.items()}
            table_placeholder.table(table_data)he app depends on the ``RosInterface`` class to subscribe
to the ``/joint_states`` topic and the ``urdf_visualizer`` module to
compute link transforms from a URDF model.  The 3D rendering is
implemented with Plotly, which integrates seamlessly with Streamlit.

How it works
------------

1. On startup, the app creates a ``RosInterface`` instance and
   launches it in a background thread.  This begins listening for
   joint state messages from the ROS 2 system.
2. The URDF model is loaded once at startup using the path
   specified in ``URDF_PATH``.  If you are using a `.xacro` file,
   ensure that the `xacro` executable is installed (see the
   documentation for :func:`urdf_visualizer.load_robot`).
3. A Streamlit timer callback periodically reads the latest joint
   positions, computes forward kinematics and updates a Plotly figure.
4. The current joint positions are displayed in a table.  Future
   iterations could include controls for sending new target positions
   back to ROS 2 via the ``RosInterface.plan_to_joint_positions``
   method.

Setup
-----

Before running this application you must ensure that your ROS 2
environment is set up and that the ABB robot is being published via
``joint_state_publisher_gui`` or the actual hardware driver.  One way
to do this with the configuration from the ``abb_ros2`` repository is
to run the provided launch file:

::

    ros2 launch abb_crb15000_support view_crb15000_5_95.launch.py

This starts a ``robot_state_publisher`` and an interactive GUI for
sliding joint angles, as shown in the ABB launch file【955574263095724†L30-L67】.

You should also install the Python dependencies listed in the
``setup_guide.md`` accompanying this project (see the end of this
file for a brief summary).

Run the app with::

    streamlit run streamlit_app.py

"""

import os
import time
from typing import Dict

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from ros_interface import RosInterface
from urdf_visualizer import load_robot, compute_link_frames
from threejs_robot_viewer import create_threejs_robot_viewer
from websocket_server import start_websocket_server


###############################################################################
# Configuration
###############################################################################

# Path to the URDF or Xacro description of the ABB robot.  Adjust this
# path to point to your local installation of the ABB CRB 1500/15000
# support package.  In the ABB MoveIt configuration, the URDF is
# located in the ``abb_crb15000_support/urdf`` directory, e.g.,
# ``crb15000_5_95.xacro``【955574263095724†L30-L40】.
URDF_PATH = os.environ.get('ABB_URDF_PATH', '/workspace/src/abb_ros2/robot_specific_config/abb_irb1200_support/urdf/irb1200_5_90.xacro')

# Polling interval (seconds) for updating the plot.
POLL_INTERVAL = 0.2


###############################################################################
# Helper functions
###############################################################################

def create_figure(robot, link_frames: Dict[str, np.ndarray], enable_debug: bool = False) -> go.Figure:
    """Build a Plotly figure representing the robot with meshes and coordinate frames in 3D.

    This function displays both the visual meshes of the robot and coordinate 
    frames for each link to provide a comprehensive visualization.

    Parameters
    ----------
    robot : urdfpy.URDF
        The robot model with loaded meshes.
    link_frames : Dict[str, numpy.ndarray]
        Mapping from link names to 4×4 transforms.
    enable_debug : bool, optional
        Whether to enable debug output and test objects.

    Returns
    -------
    plotly.graph_objects.Figure
        A Plotly figure containing mesh and coordinate frame visualizations.
    """
    fig = go.Figure()
    
    # Colors for X, Y, Z axes
    axis_colors = ['red', 'green', 'blue']
    axis_names = ['X', 'Y', 'Z']
    
    # Scale factor for axis length
    axis_length = 0.05  # Smaller axes so they don't interfere with meshes
    
    # Add meshes for each link
    meshes_processed = 0
    if enable_debug:
        print(f"Starting mesh processing for {len(robot.links)} links")
        print(f"Available link_frames keys: {list(link_frames.keys())}")
    
    for link in robot.links:
        link_name = link.name
        if enable_debug:
            print(f"Processing link: {link_name}")
        
        if link_name not in link_frames:
            if enable_debug:
                print(f"ERROR: Link {link_name} not found in link_frames")
                print(f"Available keys: {list(link_frames.keys())}")
            continue
            
        transform = link_frames[link_name]
        
        # Process visual elements
        if hasattr(link, 'visuals') and link.visuals:
            for visual_idx, visual in enumerate(link.visuals):
                if hasattr(visual, 'geometry') and visual.geometry:
                    geometry = visual.geometry
                    
                    # Handle mesh geometry
                    if hasattr(geometry, 'mesh') and geometry.mesh:
                        mesh = geometry.mesh
                        
                        # Get the trimesh objects
                        if hasattr(mesh, 'meshes') and mesh.meshes:
                            for i, trimesh_obj in enumerate(mesh.meshes):
                                # Apply transform to mesh vertices
                                vertices = trimesh_obj.vertices
                                if vertices is not None and len(vertices) > 0:
                                    # Transform vertices to world coordinates
                                    homogeneous_verts = np.column_stack([vertices, np.ones(len(vertices))])
                                    transformed_verts = (transform @ homogeneous_verts.T).T[:, :3]
                                    
                                    # Get faces
                                    faces = trimesh_obj.faces
                                    if faces is not None and len(faces) > 0:
                                        # Create mesh3d trace
                                        fig.add_trace(go.Mesh3d(
                                            x=transformed_verts[:, 0],
                                            y=transformed_verts[:, 1],
                                            z=transformed_verts[:, 2],
                                            i=faces[:, 0],
                                            j=faces[:, 1],
                                            k=faces[:, 2],
                                            color='lightblue',
                                            opacity=0.7,
                                            name=f'{link_name}_mesh_{i}',
                                            showlegend=False,
                                            hovertemplate=f'{link_name} mesh {i}<extra></extra>'
                                        ))
                                        meshes_processed += 1
    
    if enable_debug:
        print(f"Total meshes processed: {meshes_processed}")
    
    # Add a test cube to verify Plotly mesh rendering works (only in debug mode)
    if enable_debug:
        test_vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],  # bottom face
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]   # top face
        ]) * 0.1  # Scale down to 10cm
        
        test_faces = np.array([
            [0, 1, 2], [0, 2, 3],  # bottom
            [4, 7, 6], [4, 6, 5],  # top
            [0, 4, 5], [0, 5, 1],  # front
            [2, 6, 7], [2, 7, 3],  # back
            [0, 3, 7], [0, 7, 4],  # left
            [1, 5, 6], [1, 6, 2]   # right
        ])
        
        # Add test cube at origin
        fig.add_trace(go.Mesh3d(
            x=test_vertices[:, 0],
            y=test_vertices[:, 1],
            z=test_vertices[:, 2],
            i=test_faces[:, 0],
            j=test_faces[:, 1],
            k=test_faces[:, 2],
            color='red',
            opacity=0.8,
            name='test_cube',
            showlegend=False,
            hovertemplate='Test cube<extra></extra>'
        ))
        print("Added test cube to figure")
    
    # Add coordinate frames (smaller now that we have meshes)
    for link_name, transform in link_frames.items():
        # Extract position and rotation matrix
        position = transform[:3, 3]
        rotation = transform[:3, :3]
        
        # link_name is already a string since compute_link_frames returns string keys
        link_name_str = link_name
        
        # Draw coordinate axes for this link (smaller)
        for i, (color, name) in enumerate(zip(axis_colors, axis_names)):
            # Create axis vector
            axis_vector = rotation[:, i] * axis_length
            end_point = position + axis_vector
            
            # Add line trace for this axis
            fig.add_trace(go.Scatter3d(
                x=[position[0], end_point[0]],
                y=[position[1], end_point[1]],
                z=[position[2], end_point[2]],
                mode='lines',
                line=dict(width=4, color=color),
                name=f'{link_name_str}_{name}',
                showlegend=False,
                hovertemplate=f'{link_name_str} {name}-axis<extra></extra>'
            ))
        
        # Add a small sphere at the origin of each coordinate frame
        fig.add_trace(go.Scatter3d(
            x=[position[0]],
            y=[position[1]],
            z=[position[2]],
            mode='markers',
            marker=dict(size=2, color='white', opacity=0.9),
            name=link_name_str,
            showlegend=False,
            hovertemplate=f'{link_name_str}<br>X: {position[0]:.3f}<br>Y: {position[1]:.3f}<br>Z: {position[2]:.3f}<extra></extra>'
        ))
    
    # Also draw connections between coordinate frames to show robot structure
    xs, ys, zs = [], [], []
    for joint in robot.joints:
        parent = joint.parent
        child = joint.child
        
        # Convert parent and child names to strings if needed
        parent_name = parent.name if hasattr(parent, 'name') else str(parent)
        child_name = child.name if hasattr(child, 'name') else str(child)
        
        if parent_name in link_frames and child_name in link_frames:
            p_pos = link_frames[parent_name][:3, 3]
            c_pos = link_frames[child_name][:3, 3]
            # Add line segment
            xs.extend([p_pos[0], c_pos[0], None])
            ys.extend([p_pos[1], c_pos[1], None])
            zs.extend([p_pos[2], c_pos[2], None])
    
    # Add robot structure as thin gray lines
    if xs:  # Only add if we have connections
        fig.add_trace(go.Scatter3d(
            x=xs,
            y=ys,
            z=zs,
            mode='lines',
            line=dict(width=1, color='gray', dash='dot'),
            name='robot_structure',
            showlegend=False,
            hovertemplate='Robot structure<extra></extra>'
        ))
    
    # Adjust layout for better viewing
    fig.update_layout(
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Z (m)',
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        title="Robot Visualization with Meshes (Red=X, Green=Y, Blue=Z)"
    )
    return fig


###############################################################################
# Streamlit app
###############################################################################

def main() -> None:
    st.set_page_config(page_title='ABB CRB Robot Visualisation', layout='wide')
    st.title('ABB CRB Robot Visualisation (ROS 2/MoveIt)')

    # Sidebar controls
    st.sidebar.header("Visualization Settings")
    
    # Visualization mode selector
    viz_mode = st.sidebar.selectbox(
        "Visualization Mode",
        ["Plotly (Static)", "Three.js (Real-time)"],
        index=1,  # Default to Three.js
        help="Choose between static Plotly updates or real-time Three.js rendering"
    )
    
    # Debug toggle (only for Plotly mode)
    enable_debug = False
    if viz_mode == "Plotly (Static)":
        enable_debug = st.sidebar.checkbox("Enable debug output", value=False)
    
    # Initialize ROS interface in session state to persist across reruns
    if 'ros' not in st.session_state:
        st.session_state.ros = RosInterface()
        st.session_state.ros.start()
    
    # Load robot model in session state to avoid reloading
    if 'robot' not in st.session_state:
        try:
            st.session_state.robot = load_robot(URDF_PATH)
        except Exception as exc:
            st.error(f'Failed to load URDF: {exc}')
            return

    # Initialize WebSocket server for Three.js mode (after robot is loaded)
    if (viz_mode == "Three.js (Real-time)" and 
        'websocket_server' not in st.session_state and 
        'robot' in st.session_state):
        print("Starting WebSocket server for Three.js mode...")
        try:
            st.session_state.websocket_server = start_websocket_server(st.session_state.ros, st.session_state.robot)
            print("WebSocket server created, waiting for startup...")
            # Give the server a moment to start and determine its port
            time.sleep(0.5)
            actual_port = st.session_state.websocket_server.get_active_port()
            print(f"WebSocket server started on port {actual_port}")
            st.sidebar.success(f"WebSocket server started on port {actual_port}")
        except Exception as e:
            print(f"Failed to start WebSocket server: {e}")
            st.sidebar.error(f"Failed to start WebSocket server: {e}")
            st.session_state.websocket_server = None

    # Get current joint positions
    joint_positions = st.session_state.ros.get_current_joint_positions()
    
    # MoveIt2 Planning Controls (needs joint_positions to be defined)
    st.sidebar.header("MoveIt2 Planning")
    
    # Joint target controls
    target_positions = {}
    if joint_positions:
        st.sidebar.subheader("Joint Targets")
        # Add joint sliders for planning targets
        for joint_name, current_pos in joint_positions.items():
            target_positions[joint_name] = st.sidebar.slider(
                f"{joint_name} target",
                min_value=-3.14159,
                max_value=3.14159,
                value=float(current_pos),
                step=0.01,
                format="%.2f",
                help=f"Target position for {joint_name} (radians)"
            )
        
        # Planning and execution buttons
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("Plan Motion", type="primary", help="Plan trajectory to target joint positions"):
                with st.spinner("Planning trajectory..."):
                    planned_path = st.session_state.ros.plan_to_joint_positions(target_positions)
                    if planned_path:
                        st.session_state.planned_trajectory = planned_path
                        st.sidebar.success("Planning successful!")
                    else:
                        st.sidebar.error("Planning failed!")
        
        with col2:
            if st.button("Execute", type="secondary", help="Execute the planned trajectory"):
                if hasattr(st.session_state, 'planned_trajectory'):
                    with st.spinner("Executing trajectory..."):
                        # For execution, we need trajectory points, not just final position
                        # This is a simplified version - in practice, you'd want full trajectory
                        trajectory_points = [list(st.session_state.planned_trajectory)]
                        success = st.session_state.ros.execute_trajectory(trajectory_points)
                        if success:
                            st.sidebar.success("Execution successful!")
                        else:
                            st.sidebar.error("Execution failed!")
                else:
                    st.sidebar.warning("No trajectory planned!")
        
        # Display planned trajectory info
        if hasattr(st.session_state, 'planned_trajectory'):
            st.sidebar.subheader("Planned Trajectory")
            st.sidebar.text(f"Target positions: {len(st.session_state.planned_trajectory)} joints")
            
            # Show planned vs current positions
            for i, (joint_name, current_pos) in enumerate(joint_positions.items()):
                if i < len(st.session_state.planned_trajectory):
                    planned_pos = st.session_state.planned_trajectory[i]
                    diff = abs(planned_pos - current_pos)
                    st.sidebar.text(f"{joint_name}: {planned_pos:.3f} (Δ{diff:.3f})")
        
        # Current joint positions display
        st.sidebar.subheader("Current Joint Positions")
        for joint_name, position in joint_positions.items():
            st.sidebar.text(f"{joint_name}: {position:.3f} rad")
    
    # Robot status info
    st.sidebar.header("Robot Status")
    st.sidebar.text(f"Connected: {'Yes' if joint_positions else 'No'}")
    if joint_positions:
        st.sidebar.text(f"Active joints: {len(joint_positions)}")
    else:
        st.sidebar.warning("Waiting for robot connection...")
        st.sidebar.text("Make sure ROS 2 is running and joint_state_publisher is active")
    
    if joint_positions:
        # Compute link frames for visualization
        link_frames = compute_link_frames(st.session_state.robot, joint_positions)
        
        # Basic information
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Link Frames", len(link_frames))
        with col2:
            st.metric("Joints", len(st.session_state.robot.joints))
        with col3:
            st.metric("Links", len(st.session_state.robot.links))
        with col4:
            st.metric("Mode", viz_mode.split(" ")[0])
        
        # Choose visualization based on selected mode
        if viz_mode == "Three.js (Real-time)":
            st.subheader("Real-time 3D Robot Visualization")
            st.info("🚀 Real-time mode: Robot updates automatically without page refreshes!")
            
            # Create Three.js viewer
            create_threejs_robot_viewer(
                st.session_state.robot, 
                link_frames,
                width=1000,
                height=600
            )
            
        else:  # Plotly mode
            st.subheader("Static 3D Robot Visualization")
            if st.button("🔄 Refresh Visualization"):
                st.rerun()
        
        # Debug information (only shown when enabled for Plotly mode)
        if viz_mode == "Plotly (Static)" and enable_debug:
            # Check for meshes
            mesh_count = 0
            for link in st.session_state.robot.links:
                if hasattr(link, 'visuals') and link.visuals:
                    for visual in link.visuals:
                        if hasattr(visual, 'geometry') and visual.geometry and hasattr(visual.geometry, 'mesh'):
                            mesh_count += 1
            st.write(f"Number of visual meshes found: {mesh_count}")
            
            # Additional mesh debugging
            with st.expander("Mesh Debug Details"):
                for link in st.session_state.robot.links:
                    if hasattr(link, 'visuals') and link.visuals:
                        for i, visual in enumerate(link.visuals):
                            if hasattr(visual, 'geometry') and visual.geometry:
                                if hasattr(visual.geometry, 'mesh') and visual.geometry.mesh:
                                    mesh = visual.geometry.mesh
                                    st.write(f"Link {link.name}: mesh filename = {getattr(mesh, 'filename', 'No filename')}")
                                    if hasattr(mesh, 'meshes') and mesh.meshes:
                                        st.write(f"  - Has {len(mesh.meshes)} trimesh objects")
                                        for j, tmesh in enumerate(mesh.meshes):
                                            if hasattr(tmesh, 'vertices') and hasattr(tmesh, 'faces'):
                                                st.write(f"    Trimesh {j}: {len(tmesh.vertices)} vertices, {len(tmesh.faces)} faces")
                                    else:
                                        st.write(f"  - No trimesh objects loaded")
        
        # Only show Plotly visualization in Plotly mode
        if viz_mode == "Plotly (Static)":
            fig = create_figure(st.session_state.robot, link_frames, enable_debug=enable_debug)
            
            if enable_debug:
                # Debug: Check how many traces were added to the figure
                total_traces = len(fig.data)
                mesh_traces = sum(1 for trace in fig.data if hasattr(trace, 'type') and trace.type == 'mesh3d')
                st.write(f"Total traces in figure: {total_traces}")
                st.write(f"Mesh traces: {mesh_traces}")
            
            # Display the robot visualization
            st.plotly_chart(fig, use_container_width=True)
        
        # Display current joint positions as a table
        st.subheader("Current Joint Positions")
        table_data = {name: [f"{pos:.3f}"] for name, pos in joint_positions.items()}
        st.table(table_data)
    else:
        st.info('Waiting for joint states...')
    
    # Auto-refresh only for Plotly mode (Three.js updates via WebSocket)
    if viz_mode == "Plotly (Static)":
        time.sleep(POLL_INTERVAL)
        st.rerun()


if __name__ == '__main__':
    main()

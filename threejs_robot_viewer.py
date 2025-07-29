"""
Three.js-based robot viewer component for Streamlit.
Provides real-time 3D visualization without page reloads.
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import numpy as np
from typing import Dict, List, Any
import tempfile
import os

def create_threejs_robot_viewer(robot, link_frames: Dict[str, np.ndarray], 
                               width: int = 800, height: int = 600) -> None:
    """
    Create a Three.js-based robot viewer that can update in real-time.
    
    Parameters
    ----------
    robot : URDF
        The robot model with meshes
    link_frames : Dict[str, np.ndarray]
        Current link transforms
    width : int
        Viewer width in pixels
    height : int
        Viewer height in pixels
    """
    
    # Extract mesh data for Three.js
    mesh_data = extract_mesh_data(robot, link_frames)
    
    # Create the HTML/JavaScript component
    html_content = create_threejs_html(mesh_data, width, height)
    
    # Render the component
    components.html(html_content, width=width, height=height)

def extract_mesh_data(robot, link_frames: Dict[str, np.ndarray]) -> List[Dict[str, Any]]:
    """
    Extract mesh data from URDF robot for Three.js rendering.
    
    Returns
    -------
    List[Dict]
        List of mesh objects with vertices, faces, and transforms
    """
    mesh_objects = []
    
    for link in robot.links:
        link_name = link.name
        
        if link_name not in link_frames:
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
                                vertices = trimesh_obj.vertices
                                faces = trimesh_obj.faces
                                
                                if vertices is not None and len(vertices) > 0 and faces is not None and len(faces) > 0:
                                    # Store vertices in their local coordinates
                                    # Transform will be applied to the entire mesh
                                    
                                    mesh_obj = {
                                        'id': f'{link_name}_mesh_{i}',
                                        'linkName': link_name,
                                        'vertices': vertices.flatten().tolist(),
                                        'faces': faces.flatten().tolist(),
                                        'color': '#87CEEB',  # Light blue
                                        'initialTransform': transform.flatten().tolist()
                                    }
                                    mesh_objects.append(mesh_obj)
    
    return mesh_objects

def create_threejs_html(mesh_data: List[Dict], width: int, height: int) -> str:
    """
    Create HTML content with Three.js visualization.
    
    Parameters
    ----------
    mesh_data : List[Dict]
        Mesh data for rendering
    width : int
        Canvas width
    height : int
        Canvas height
        
    Returns
    -------
    str
        HTML content with embedded Three.js code
    """
    
    mesh_data_json = json.dumps(mesh_data)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; }}
            #robot-container {{ width: {width}px; height: {height}px; }}
            #controls {{
                position: absolute;
                top: 10px;
                left: 10px;
                background: rgba(0,0,0,0.7);
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-family: Arial, sans-serif;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div id="robot-container"></div>
        <div id="controls">
            <div>Left mouse: Rotate</div>
            <div>Right mouse: Pan</div>
            <div>Wheel: Zoom</div>
            <div id="fps">FPS: --</div>
        </div>
        
        <script>
            // Global variables
            let scene, camera, renderer, controls;
            let robotMeshes = [];
            let frameCount = 0;
            let lastTime = performance.now();
            
            // Initialize Three.js scene
            function init() {{
                // Scene setup
                scene = new THREE.Scene();
                scene.background = new THREE.Color(0xf0f0f0);
                
                // Camera setup - position to view upright robot
                camera = new THREE.PerspectiveCamera(75, {width}/{height}, 0.01, 1000);
                camera.position.set(2, 1, 2);  // View from front-right angle
                camera.lookAt(0, 0.5, 0);  // Look at robot mid-height
                
                // Renderer setup
                renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize({width}, {height});
                renderer.shadowMap.enabled = true;
                renderer.shadowMap.type = THREE.PCFSoftShadowMap;
                
                document.getElementById('robot-container').appendChild(renderer.domElement);
                
                // Controls
                controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.1;
                
                // Lighting
                setupLighting();
                
                // Load robot meshes
                loadRobotMeshes();
                
                // Add coordinate system
                addCoordinateSystem();
                
                // Start render loop
                animate();
            }}
            
            function setupLighting() {{
                // Ambient light
                const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
                scene.add(ambientLight);
                
                // Directional light
                const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
                directionalLight.position.set(5, 5, 5);
                directionalLight.castShadow = true;
                directionalLight.shadow.mapSize.width = 2048;
                directionalLight.shadow.mapSize.height = 2048;
                scene.add(directionalLight);
                
                // Additional fill light
                const fillLight = new THREE.DirectionalLight(0x8080ff, 0.3);
                fillLight.position.set(-5, 2, -5);
                scene.add(fillLight);
            }}
            
            function loadRobotMeshes() {{
                const meshData = {mesh_data_json};
                
                meshData.forEach(meshInfo => {{
                    const geometry = new THREE.BufferGeometry();
                    
                    // Convert flat arrays back to Vector3 arrays
                    const vertices = new Float32Array(meshInfo.vertices);
                    const indices = new Uint32Array(meshInfo.faces);
                    
                    geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
                    geometry.setIndex(new THREE.BufferAttribute(indices, 1));
                    geometry.computeVertexNormals();
                    
                    // Material
                    const material = new THREE.MeshLambertMaterial({{
                        color: meshInfo.color,
                        transparent: true,
                        opacity: 0.8
                    }});
                    
                    // Create mesh
                    const mesh = new THREE.Mesh(geometry, material);
                    mesh.castShadow = true;
                    mesh.receiveShadow = true;
                    mesh.userData = {{
                        id: meshInfo.id,
                        linkName: meshInfo.linkName
                    }};
                    
                    // Apply initial transformation
                    if (meshInfo.initialTransform) {{
                        const initialMatrix = new THREE.Matrix4();
                        initialMatrix.fromArray(meshInfo.initialTransform);
                        
                        // Apply coordinate system transformation: ROS to Three.js
                        // ROS: X-forward, Y-left, Z-up  
                        // Three.js: X-right, Y-up, Z-forward
                        // We want ROS Z-up to become Three.js Y-up (robot standing upright)
                        const coordinateTransform = new THREE.Matrix4();
                        coordinateTransform.set(
                            1, 0, 0, 0,   // ROS X -> Three.js X
                            0, 0, 1, 0,   // ROS Z -> Three.js Y (up)
                            0, -1, 0, 0,  // ROS -Y -> Three.js Z (forward)
                            0, 0, 0, 1
                        );
                        
                        // Apply coordinate transformation
                        initialMatrix.premultiply(coordinateTransform);
                        
                        mesh.matrix.copy(initialMatrix);
                        mesh.matrixAutoUpdate = false;
                    }}
                    
                    scene.add(mesh);
                    robotMeshes.push(mesh);
                }});
                
                console.log(`Loaded ${{robotMeshes.length}} robot meshes`);
            }}
            
            function addCoordinateSystem() {{
                // Add world coordinate axes
                const axesHelper = new THREE.AxesHelper(0.5);
                scene.add(axesHelper);
                
                // Add grid
                const gridHelper = new THREE.GridHelper(2, 20, 0x888888, 0xcccccc);
                scene.add(gridHelper);
            }}
            
            function updateFPS() {{
                frameCount++;
                const currentTime = performance.now();
                if (currentTime >= lastTime + 1000) {{
                    const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
                    document.getElementById('fps').textContent = `FPS: ${{fps}}`;
                    frameCount = 0;
                    lastTime = currentTime;
                }}
            }}
            
            function animate() {{
                requestAnimationFrame(animate);
                
                controls.update();
                renderer.render(scene, camera);
                updateFPS();
            }}
            
            // Function to update robot configuration (called from WebSocket)
            window.updateRobotConfiguration = function(newLinkFrames) {{
                // Update robot meshes with new link frames
                robotMeshes.forEach((mesh, index) => {{
                    const linkName = mesh.userData.linkName;
                    if (newLinkFrames[linkName]) {{
                        const transform = newLinkFrames[linkName];
                        
                        // Create Three.js Matrix4 from the 4x4 transformation matrix
                        // Three.js matrices are column-major, so we need to transpose
                        const matrix4 = new THREE.Matrix4();
                        matrix4.fromArray([
                            transform[0][0], transform[1][0], transform[2][0], transform[3][0],
                            transform[0][1], transform[1][1], transform[2][1], transform[3][1],
                            transform[0][2], transform[1][2], transform[2][2], transform[3][2],
                            transform[0][3], transform[1][3], transform[2][3], transform[3][3]
                        ]);
                        
                        // Apply coordinate system transformation: ROS to Three.js
                        // ROS: X-forward, Y-left, Z-up  
                        // Three.js: X-right, Y-up, Z-forward
                        // We want ROS Z-up to become Three.js Y-up (robot standing upright)
                        const coordinateTransform = new THREE.Matrix4();
                        coordinateTransform.set(
                            1, 0, 0, 0,   // ROS X -> Three.js X
                            0, 0, 1, 0,   // ROS Z -> Three.js Y (up)
                            0, -1, 0, 0,  // ROS -Y -> Three.js Z (forward)
                            0, 0, 0, 1
                        );
                        
                        // Apply coordinate transformation
                        matrix4.premultiply(coordinateTransform);
                        
                        // Reset mesh transformation and apply new one
                        mesh.matrix.copy(matrix4);
                        mesh.matrixAutoUpdate = false;
                        
                        // Debug first few meshes
                        if (index < 3) {{
                            const pos = new THREE.Vector3();
                            const quat = new THREE.Quaternion();
                            const scale = new THREE.Vector3();
                            matrix4.decompose(pos, quat, scale);
                            console.log(`Updated ${{linkName}}: pos(${{pos.x.toFixed(3)}}, ${{pos.y.toFixed(3)}}, ${{pos.z.toFixed(3)}})`);
                        }}
                    }}
                }});
            }};
            
            // WebSocket connection for real-time updates
            function connectWebSocket() {{
                // Try multiple ports in case the default is occupied
                const ports = [8765, 8766, 8767, 8768, 8769];
                let currentPortIndex = 0;
                
                function tryConnect() {{
                    if (currentPortIndex >= ports.length) {{
                        console.error('Could not connect to WebSocket server on any port');
                        document.getElementById('connection-status').textContent = 'Failed - No server found';
                        document.getElementById('connection-status').style.color = 'red';
                        return;
                    }}
                    
                    const port = ports[currentPortIndex];
                    const wsUrl = `ws://localhost:${{port}}`;
                    console.log(`Trying WebSocket connection on port:`, port);
                    
                    const ws = new WebSocket(wsUrl);
                    
                    ws.onopen = function(event) {{
                        console.log(`WebSocket connected on port ${{port}}`);
                        document.getElementById('connection-status').textContent = `Connected (port ${{port}})`;
                        document.getElementById('connection-status').style.color = 'green';
                    }};
                    
                    ws.onmessage = function(event) {{
                        try {{
                            const data = JSON.parse(event.data);
                            if (data.link_frames) {{
                                console.log('Received link frames update');
                                
                                // Convert flat arrays back to 4x4 matrices
                                const linkFrames = {{}};
                                for (const [linkName, flatMatrix] of Object.entries(data.link_frames)) {{
                                    // Reshape flat array to 4x4 matrix (row-major order)
                                    const matrix = [];
                                    for (let i = 0; i < 16; i += 4) {{
                                        matrix.push(flatMatrix.slice(i, i + 4));
                                    }}
                                    linkFrames[linkName] = matrix;
                                    
                                    // Debug: log first matrix to see the format
                                    if (linkName === 'base_link') {{
                                        console.log('base_link matrix:', matrix);
                                        console.log('Position:', matrix[0][3], matrix[1][3], matrix[2][3]);
                                    }}
                                }}
                                
                                // Update robot configuration with link frames
                                window.updateRobotConfiguration(linkFrames);
                            }}
                        }} catch (e) {{
                            console.error('Error parsing WebSocket message:', e);
                        }}
                    }};
                    
                    ws.onerror = function(error) {{
                        console.error(`WebSocket error on port ${{port}}:`, error);
                        currentPortIndex++;
                        setTimeout(tryConnect, 1000); // Try next port after 1 second
                    }};
                    
                    ws.onclose = function(event) {{
                        console.log(`WebSocket disconnected from port ${{port}}`);
                        document.getElementById('connection-status').textContent = 'Disconnected';
                        document.getElementById('connection-status').style.color = 'orange';
                        
                        // Attempt to reconnect after 3 seconds
                        setTimeout(connectWebSocket, 3000);
                    }};
                    
                    return ws;
                }}
                
                return tryConnect();
            }}
            
            // Add connection status display
            function addConnectionStatus() {{
                const statusDiv = document.createElement('div');
                statusDiv.style.position = 'absolute';
                statusDiv.style.top = '10px';
                statusDiv.style.left = '10px';
                statusDiv.style.color = 'white';
                statusDiv.style.fontFamily = 'Arial, sans-serif';
                statusDiv.style.fontSize = '12px';
                statusDiv.style.backgroundColor = 'rgba(0,0,0,0.5)';
                statusDiv.style.padding = '5px 10px';
                statusDiv.style.borderRadius = '3px';
                statusDiv.innerHTML = 'WebSocket: <span id="connection-status">Connecting...</span>';
                document.body.appendChild(statusDiv);
            }}
            
            // Handle window resize
            window.addEventListener('resize', function() {{
                camera.aspect = {width} / {height};
                camera.updateProjectionMatrix();
                renderer.setSize({width}, {height});
            }});
            
            // Initialize when page loads
            init();
            addConnectionStatus();
            connectWebSocket();
        </script>
    </body>
    </html>
    """
    
    return html_content

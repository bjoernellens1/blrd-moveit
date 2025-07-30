"""
ros_interface.py
=================

This module provides a simple interface between a ROS 2/MoveIt setup and
a higher‑level application (e.g. a Streamlit UI).  It encapsulates
initialising a ROS 2 node, subscribing to the joint state topic and
exposing the latest joint positions.  The code is written to be as
framework‑agnostic as possible: it does not depend on any Streamlit
components and can therefore be reused in other applications.

Key features
------------

* Lazy initialisation of a ROS 2 node: the node is only created when
  required, and subsequent calls will reuse the same context.
* Background thread for spinning the node: ROS 2 requires the node to
  spin continuously to process incoming messages.  This implementation
  spawns a daemon thread so that the main application (e.g. Streamlit)
  remains responsive.
* Thread‑safe storage of the latest joint state: received joint
  positions are stored in a dictionary and protected by a lock.

To use this module:

>>> from ros_interface import RosInterface
>>> ros = RosInterface()
>>> ros.start()  # starts the node and subscriber in the background
>>> # later, read the latest joint state
>>> positions = ros.get_current_joint_positions()

Dependencies
------------

This code relies on `rclpy` (ROS 2 Python client library).  It also
imports message definitions from the `sensor_msgs` package.  Ensure
these packages are installed in your ROS 2 environment.  The code does
not require MoveIt directly but can be extended to integrate with
MoveIt’s Python API (see the `plan_to_joint_positions` stub).
"""

import threading
import time
from typing import Dict, Optional, Sequence

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class RosInterface:
    """A helper class that wraps ROS 2 initialisation and joint state subscription.

    The interface maintains an internal dictionary mapping joint names to
    their most recently received positions.  It exposes a simple API to
    start/stop the ROS 2 node and to retrieve the latest joint state.

    Attributes
    ----------
    node : Optional[Node]
        The underlying ROS 2 node.  Will be created on first call to
        :meth:`start`.
    latest_joint_positions : Dict[str, float]
        Thread‑safe store of the latest joint positions keyed by joint
        name.
    _spin_thread : Optional[threading.Thread]
        Background thread that runs the ROS 2 executor.  Marked as
        daemon so it will exit when the main program terminates.
    _lock : threading.Lock
        Protects access to ``latest_joint_positions``.
    """

    def __init__(self) -> None:
        self.node: Optional[Node] = None
        self.latest_joint_positions: Dict[str, float] = {}
        self._spin_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def _joint_state_callback(self, msg: JointState) -> None:
        """Callback invoked whenever a new JointState message is received.

        Parameters
        ----------
        msg : sensor_msgs.msg.JointState
            The incoming joint state message.
        """
        with self._lock:
            for name, position in zip(msg.name, msg.position):
                self.latest_joint_positions[name] = position

    def _create_node(self) -> Node:
        """Initialise rclpy and create the underlying node.

        Returns
        -------
        Node
            A new ROS 2 node.
        """
        if not rclpy.ok():
            rclpy.init()
        node = rclpy.create_node('streamlit_ros_interface')
        # Subscribe to the joint_states topic.  This topic is published by
        # the robot_state_publisher or joint_state_publisher GUI launched
        # via the abb_ros2 launch files【955574263095724†L30-L67】.
        node.create_subscription(
            JointState,
            '/joint_states',
            self._joint_state_callback,
            10,
        )
        return node

    def _spin(self) -> None:
        """Spin the ROS 2 node in a background thread.

        This function runs until ROS 2 is shut down.  It should not be
        called directly; instead, it is used as the target of
        ``_spin_thread``.
        """
        assert self.node is not None, 'Node must be created before spinning'
        executor = rclpy.executors.SingleThreadedExecutor()
        executor.add_node(self.node)
        try:
            executor.spin()
        finally:
            executor.shutdown()

    def start(self) -> None:
        """Start the ROS 2 node and subscriber.

        This method is idempotent: calling it multiple times has no
        effect after the first call.
        """
        if self.node is None:
            self.node = self._create_node()
        if self._spin_thread is None:
            self._spin_thread = threading.Thread(target=self._spin, daemon=True)
            self._spin_thread.start()

    def stop(self) -> None:
        """Shut down the ROS 2 context gracefully.

        This method stops the executor and shuts down rclpy.  It should
        be called when the application is terminating.
        """
        if self.node is not None:
            self.node.destroy_node()
            self.node = None
        if rclpy.ok():
            rclpy.shutdown()

    def get_current_joint_positions(self) -> Dict[str, float]:
        """Return a copy of the latest joint positions.

        Returns
        -------
        Dict[str, float]
            Mapping from joint name to position (in radians).
        """
        with self._lock:
            return dict(self.latest_joint_positions)

    def plan_to_joint_positions(self, target_positions: Dict[str, float]) -> Optional[Sequence[float]]:
        """Plan a trajectory to a desired joint configuration using MoveIt.

        Parameters
        ----------
        target_positions : Dict[str, float]
            The desired joint positions keyed by joint name.

        Returns
        -------
        Optional[Sequence[float]]
            A list of joint positions representing the planned path.  If
            planning fails, return ``None``.
        """
        try:
            from moveit_msgs.msg import MoveItErrorCodes, MotionPlanRequest
            from moveit_msgs.srv import GetMotionPlan
            from sensor_msgs.msg import JointState
            import rclpy
            
            if self.node is None:
                return None
                
            # Create a service client for motion planning
            plan_client = self.node.create_client(GetMotionPlan, '/plan_kinematic_path')
            
            if not plan_client.wait_for_service(timeout_sec=2.0):
                self.node.get_logger().warn("Motion planning service not available")
                return None
            
            # Create motion plan request
            req = GetMotionPlan.Request()
            req.motion_plan_request.group_name = "manipulator"  # or appropriate group name
            req.motion_plan_request.num_planning_attempts = 10
            req.motion_plan_request.allowed_planning_time = 5.0
            
            # Set start state to current joint positions
            start_state = req.motion_plan_request.start_state
            start_state.joint_state.name = list(self.latest_joint_positions.keys())
            start_state.joint_state.position = list(self.latest_joint_positions.values())
            
            # Set goal constraints for joint positions
            from moveit_msgs.msg import Constraints, JointConstraint
            goal_constraints = Constraints()
            
            for joint_name, target_pos in target_positions.items():
                joint_constraint = JointConstraint()
                joint_constraint.joint_name = joint_name
                joint_constraint.position = target_pos
                joint_constraint.tolerance_above = 0.01
                joint_constraint.tolerance_below = 0.01
                joint_constraint.weight = 1.0
                goal_constraints.joint_constraints.append(joint_constraint)
            
            req.motion_plan_request.goal_constraints = [goal_constraints]
            
            # Call the planning service
            future = plan_client.call_async(req)
            rclpy.spin_until_future_complete(self.node, future, timeout_sec=10.0)
            
            if future.done():
                response = future.result()
                if response.motion_plan_response.error_code.val == MoveItErrorCodes.SUCCESS:
                    # Extract trajectory points
                    trajectory = response.motion_plan_response.trajectory.joint_trajectory
                    if trajectory.points:
                        # Return the final joint positions
                        return trajectory.points[-1].positions
                    
            return None
            
        except ImportError:
            if self.node:
                self.node.get_logger().warn("MoveIt Python packages not available")
            return None
        except Exception as e:
            if self.node:
                self.node.get_logger().error(f"Motion planning failed: {str(e)}")
            return None

    def execute_trajectory(self, trajectory_points: Sequence[Sequence[float]]) -> bool:
        """Execute a planned trajectory using MoveIt.

        Parameters
        ----------
        trajectory_points : Sequence[Sequence[float]]
            A sequence of joint position vectors representing the trajectory.

        Returns
        -------
        bool
            True if execution was successful, False otherwise.
        """
        try:
            from moveit_msgs.action import ExecuteTrajectory
            from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
            import rclpy
            from rclpy.action import ActionClient
            from builtin_interfaces.msg import Duration
            
            if self.node is None:
                return False
                
            # Create action client for trajectory execution
            execute_client = ActionClient(self.node, ExecuteTrajectory, '/execute_trajectory')
            
            if not execute_client.wait_for_server(timeout_sec=2.0):
                self.node.get_logger().warn("Trajectory execution action server not available")
                return False
            
            # Create trajectory message
            goal_msg = ExecuteTrajectory.Goal()
            trajectory = JointTrajectory()
            trajectory.joint_names = list(self.latest_joint_positions.keys())
            
            # Add trajectory points
            for i, positions in enumerate(trajectory_points):
                point = JointTrajectoryPoint()
                point.positions = list(positions)
                point.time_from_start = Duration(sec=i, nanosec=0)  # 1 second per point
                trajectory.points.append(point)
            
            goal_msg.trajectory.joint_trajectory = trajectory
            
            # Send goal and wait for result
            future = execute_client.send_goal_async(goal_msg)
            rclpy.spin_until_future_complete(self.node, future, timeout_sec=5.0)
            
            if future.done():
                goal_handle = future.result()
                if goal_handle.accepted:
                    result_future = goal_handle.get_result_async()
                    rclpy.spin_until_future_complete(self.node, result_future, timeout_sec=30.0)
                    if result_future.done():
                        return result_future.result().result.error_code.val == 1  # SUCCESS
                        
            return False
            
        except ImportError:
            if self.node:
                self.node.get_logger().warn("MoveIt action packages not available")
            return False
        except Exception as e:
            if self.node:
                self.node.get_logger().error(f"Trajectory execution failed: {str(e)}")
            return False

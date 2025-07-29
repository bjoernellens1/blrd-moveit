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

    # The following method is a stub demonstrating how you might
    # integrate MoveIt’s planning capabilities.  Implementations will
    # vary depending on the chosen Python API (e.g. moveit2_python,
    # moveit_msgs service calls, or direct integration with moveit_commander).
    def plan_to_joint_positions(self, target_positions: Dict[str, float]) -> Optional[Sequence[float]]:
        """Plan a trajectory to a desired joint configuration.

        Parameters
        ----------
        target_positions : Dict[str, float]
            The desired joint positions keyed by joint name.

        Returns
        -------
        Optional[Sequence[float]]
            A list of joint positions representing the planned path.  If
            planning fails, return ``None``.  For now, this method is a
            placeholder and returns ``None``.
        """
        # TODO: Integrate with MoveIt’s Python API here.
        # For example, using moveit2_python you would create a
        # MoveGroupInterface for the manipulator, set the target joint
        # positions, and call plan().  The result’s trajectory could
        # then be returned or executed via MoveIt’s action server.
        return None

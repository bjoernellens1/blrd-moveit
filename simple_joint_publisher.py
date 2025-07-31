#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import math
import time

class SimpleJointPublisher(Node):
    def __init__(self):
        super().__init__('simple_joint_publisher')
        
        # Create joint state publisher
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)
        
        # Define joint names for CRB15000
        self.joint_names = [
            'joint_1',
            'joint_2', 
            'joint_3',
            'joint_4',
            'joint_5',
            'joint_6'
        ]
        
        # Create timer to publish joint states at 10 Hz
        self.timer = self.create_timer(0.1, self.publish_joint_states)
        
        self.time_offset = 0.0
        
        self.get_logger().info('Simple Joint Publisher started')
        
    def publish_joint_states(self):
        """Publish joint states with simple sinusoidal motion"""
        
        # Create joint state message
        joint_state = JointState()
        joint_state.header.stamp = self.get_clock().now().to_msg()
        joint_state.name = self.joint_names
        
        # Generate simple sinusoidal motion for visualization
        self.time_offset += 0.1
        
        # Create position values (in radians)
        positions = [
            0.5 * math.sin(self.time_offset * 0.5),     # joint_1: slow rotation
            0.3 * math.sin(self.time_offset * 0.7),     # joint_2: medium motion
            0.4 * math.sin(self.time_offset * 0.4),     # joint_3: slow motion
            0.6 * math.sin(self.time_offset * 0.9),     # joint_4: fast motion
            0.2 * math.sin(self.time_offset * 0.6),     # joint_5: medium motion
            0.8 * math.sin(self.time_offset * 1.0)      # joint_6: fastest motion
        ]
        
        joint_state.position = positions
        joint_state.velocity = []  # Empty for now
        joint_state.effort = []    # Empty for now
        
        # Publish the joint state
        self.joint_pub.publish(joint_state)

def main(args=None):
    rclpy.init(args=args)
    
    joint_publisher = SimpleJointPublisher()
    
    try:
        rclpy.spin(joint_publisher)
    except KeyboardInterrupt:
        pass
    finally:
        joint_publisher.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

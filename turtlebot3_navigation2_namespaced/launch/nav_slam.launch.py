# Copyright 2019 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Darby Lim

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

TURTLEBOT3_MODEL = os.environ['TURTLEBOT3_MODEL']
ROS_DISTRO = os.environ.get('ROS_DISTRO')


def generate_launch_description():
    namespace = LaunchConfiguration('namespace', default='tb3_1')
    use_sim_time = LaunchConfiguration('use_sim_time', default='True')
    map_dir = LaunchConfiguration(
        'map',
        default=os.path.join(
            get_package_share_directory('turtlebot3_navigation2_tb3_1'),
            'map',
            'map.yaml'))


        
    param_dir = LaunchConfiguration(
        'params_file',
        default=os.path.join(
            get_package_share_directory('turtlebot3_navigation2_tb3_1'),
            "param",
            "burger3310.yaml"
        )
    )

    launch_dir = os.path.join(get_package_share_directory('turtlebot3_navigation2_tb3_1'), 'launch')

    rviz_config_dir = os.path.join(
        get_package_share_directory('turtlebot3_navigation2_tb3_1'),
        'rviz',
        'tb3_navigation2.rviz')

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace',
            default_value='tb3_1',
            description='Top-level namespace'),

        DeclareLaunchArgument(
            'map',
            default_value=map_dir,
            description='Full path to map file to load'),

        DeclareLaunchArgument(
            'params_file',
            default_value=param_dir,
            description='Full path to param file to load'),

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='True',
            description='Use simulation (Gazebo) clock if true'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([launch_dir, '/bringup_launch.py']),
            launch_arguments={
                'namespace': namespace,
                'use_namespace': 'True',
                'slam':"True",
                'map': map_dir,
                'use_sim_time': use_sim_time,
                'params_file': param_dir}.items(),
        ),

        # RViz runs INSIDE the namespace so the Nav2/Docking panels + GoalTool create their
        # action clients as /<namespace>/navigate_to_pose, /follow_waypoints, /dock_robot, etc.
        # (an un-namespaced RViz makes global /navigate_to_pose clients with no matching server).
        # The .rviz display topics are already absolute /tb3_1/... so the namespace doesn't touch
        # them; the /tf remaps force RViz's TF listener onto the namespaced /tb3_1/tf topics.
        #
        # Delayed by TimerAction: RViz is graphics-heavy at startup and, if it races the nav2
        # lifecycle bringup, it can starve the controller_server 'configure' transition, timing
        # out its change_state response and stalling the whole nav stack (seen as controller_server
        # stuck 'inactive', everything downstream 'unconfigured'). Starting RViz after bringup
        # settles avoids that contention.
        TimerAction(
            period=12.0,
            actions=[
                Node(
                    package='rviz2',
                    executable='rviz2',
                    name='rviz2',
                    namespace=namespace,
                    arguments=['-d', rviz_config_dir],
                    parameters=[{'use_sim_time': use_sim_time}],
                    remappings=[
                        ('/tf', ['/', namespace, '/tf']),
                        ('/tf_static', ['/', namespace, '/tf_static']),
                    ],
                    output='screen'),
            ]),
    ])

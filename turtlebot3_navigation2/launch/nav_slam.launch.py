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
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from nav2_common.launch import ReplaceString

TURTLEBOT3_MODEL = os.environ['TURTLEBOT3_MODEL']
ROS_DISTRO = os.environ.get('ROS_DISTRO')


def generate_launch_description():
    namespace = LaunchConfiguration('namespace', default='')
    # Skip PushROSNamespace (via use_namespace=false) when the namespace is empty.
    use_namespace = PythonExpression(["'false' if '", namespace, "' == '' else 'true'"])
    # '/tb3_1' (or '') for absolute topic/tf names.
    topic_prefix = PythonExpression(["'' if '", namespace, "' == '' else '/", namespace, "'"])
    use_sim_time = LaunchConfiguration('use_sim_time', default='True')
    map_dir = LaunchConfiguration(
        'map',
        default=os.path.join(
            get_package_share_directory('turtlebot3_navigation2'),
            'map',
            'map.yaml'))


        
    param_dir = LaunchConfiguration(
        'params_file',
        default=os.path.join(
            get_package_share_directory('turtlebot3_navigation2'),
            "param",
            "burger3310.yaml"
        )
    )

    launch_dir = os.path.join(get_package_share_directory('turtlebot3_navigation2'), 'launch')

    rviz_config_dir = os.path.join(
        get_package_share_directory('turtlebot3_navigation2'),
        'rviz',
        'tb3_navigation2.rviz')

    # Substitute the '<frame_ns>' (frames) and '<topic_ns>' (topics) placeholders in the
    # RViz config so it follows the launch namespace.
    frame_prefix = PythonExpression(["'' if '", namespace, "' == '' else '", namespace, "/'"])
    namespaced_rviz_config = ReplaceString(
        source_file=rviz_config_dir,
        replacements={'<frame_ns>': frame_prefix, '<topic_ns>': topic_prefix},
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace',
            default_value='',
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
                'use_namespace': use_namespace,
                'slam':"True",
                'map': map_dir,
                'use_sim_time': use_sim_time,
                'params_file': param_dir}.items(),
        ),

        # RViz runs INSIDE the namespace so the Nav2/Docking panels + GoalTool create their
        # action clients as /<namespace>/navigate_to_pose, /follow_waypoints, /dock_robot, etc.
        # (an un-namespaced RViz makes global /navigate_to_pose clients with no matching server).
        # The .rviz display topics carry the '<topic_ns>' placeholder, substituted to the active
        # namespace above; the /tf remaps force RViz's TF listener onto the namespaced tf topics.
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
                    arguments=['-d', namespaced_rviz_config],
                    parameters=[{'use_sim_time': use_sim_time}],
                    remappings=[
                        ('/tf', [topic_prefix, '/tf']),
                        ('/tf_static', [topic_prefix, '/tf_static']),
                    ],
                    output='screen'),
            ]),
    ])

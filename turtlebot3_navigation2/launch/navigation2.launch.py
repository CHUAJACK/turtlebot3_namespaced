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
    # 'tb3_1/' (or '') for frames; '/tb3_1' (or '') for absolute topic/tf names.
    frame_prefix = PythonExpression(["'' if '", namespace, "' == '' else '", namespace, "/'"])
    topic_prefix = PythonExpression(["'' if '", namespace, "' == '' else '/", namespace, "'"])
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    package_dir = get_package_share_directory('turtlebot3_navigation2')
    map_dir = LaunchConfiguration(
        'map',
        default=os.path.join(
            get_package_share_directory('turtlebot3_navigation2'),
            'map',
            'map.yaml'))

    # burger3310.yaml is the namespace-aware param file (frames carry the '<frame_ns>'
    # placeholder); use it for all models so the namespace argument works uniformly.
    param_dir = LaunchConfiguration(
        'params_file',
        default=os.path.join(
            package_dir,
            'param',
            'burger3310.yaml'))

    launch_dir = os.path.join(package_dir, 'launch')

    rviz_config_dir = os.path.join(
        package_dir,
        'rviz',
        'tb3_navigation2.rviz')

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
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([launch_dir, '/bringup_launch.py']),
            launch_arguments={
                'namespace': namespace,
                'use_namespace': use_namespace,
                'map': map_dir,
                'use_sim_time': use_sim_time,
                'params_file': param_dir}.items(),
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', namespaced_rviz_config],
            parameters=[{'use_sim_time': use_sim_time}],
            remappings=[
                ('/tf', [topic_prefix, '/tf']),
                ('/tf_static', [topic_prefix, '/tf_static']),
            ],
            output='screen'),
    ])

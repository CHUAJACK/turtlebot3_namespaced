#!/usr/bin/env python3
#
# Copyright 2019 ROBOTIS CO., LTD.
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
# Authors: Darby Lim

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from nav2_common.launch import ReplaceString


def generate_launch_description():
    namespace = LaunchConfiguration('namespace', default='')
    # Frames are BARE (base_link, odom, map ...) on every robot: multi-robot
    # isolation comes from the namespaced /tf topics, not from frame names.
    # '/tb3_1' (or '') still prefixes absolute topic names.
    frame_prefix = ''
    topic_prefix = PythonExpression(["'' if '", namespace, "' == '' else '/", namespace, "'"])

    rviz_config_dir = os.path.join(
        get_package_share_directory('turtlebot3_description'),
        'rviz',
        'model.rviz')

    namespaced_rviz_config = ReplaceString(
        source_file=rviz_config_dir,
        replacements={'<frame_ns>': frame_prefix, '<topic_ns>': topic_prefix},
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace',
            default_value='',
            description='Top-level namespace'),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', namespaced_rviz_config],
            remappings=[
                ('/tf', [topic_prefix, '/tf']),
                ('/tf_static', [topic_prefix, '/tf_static']),
            ],
            output='screen'),
    ])

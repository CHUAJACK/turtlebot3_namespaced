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
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    namespace = LaunchConfiguration('namespace', default='tb3_1')
    rviz_config_dir = os.path.join(
        get_package_share_directory('turtlebot3_description_tb3_1'),
        'rviz',
        'model.rviz')

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace',
            default_value='tb3_1',
            description='Top-level namespace'),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_dir],
            remappings=[
                ('/tf', ['/', namespace, '/tf']),
                ('/tf_static', ['/', namespace, '/tf_static']),
            ],
            output='screen'),
    ])

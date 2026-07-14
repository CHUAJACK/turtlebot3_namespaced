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
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PythonExpression
from launch.substitutions import ThisLaunchFileDir
from launch_ros.actions import Node
from nav2_common.launch import ReplaceString


def launch_cartographer_node(context, *args, **kwargs):
    # cartographer_node needs a config *directory* + *basename* and reads the .lua off
    # disk, so ReplaceString (which yields a single temp file path) can't feed it directly.
    # Instead, render the .lua here: substitute the '<frame_ns>' placeholder with
    # '<namespace>/' (or '' when empty) and write the result to a temp dir cartographer reads.
    namespace = LaunchConfiguration('namespace').perform(context)
    config_dir = LaunchConfiguration('cartographer_config_dir').perform(context)
    basename = LaunchConfiguration('configuration_basename').perform(context)

    frame_prefix = '' if namespace == '' else namespace + '/'
    with open(os.path.join(config_dir, basename), 'r') as source:
        rendered = source.read().replace('<frame_ns>', frame_prefix)

    rendered_dir = tempfile.mkdtemp(prefix='cartographer_cfg_')
    with open(os.path.join(rendered_dir, basename), 'w') as dest:
        dest.write(rendered)

    return [
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            namespace=namespace,
            output='screen',
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
            remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
            arguments=['-configuration_directory', rendered_dir,
                       '-configuration_basename', basename]),
    ]


def generate_launch_description():
    namespace = LaunchConfiguration('namespace', default='')
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    turtlebot3_cartographer_prefix = get_package_share_directory('turtlebot3_cartographer')
    cartographer_config_dir = LaunchConfiguration('cartographer_config_dir', default=os.path.join(
                                                  turtlebot3_cartographer_prefix, 'config'))
    configuration_basename = LaunchConfiguration('configuration_basename',
                                                 default='turtlebot3_lds_2d.lua')

    resolution = LaunchConfiguration('resolution', default='0.05')
    publish_period_sec = LaunchConfiguration('publish_period_sec', default='1.0')

    # 'tb3_1/' (or '') for frame IDs. The cartographer .rviz only namespaces frames
    # (its display topics are intentionally left un-prefixed, as before).
    frame_prefix = PythonExpression(["'' if '", namespace, "' == '' else '", namespace, "/'"])

    rviz_config_dir = os.path.join(get_package_share_directory('turtlebot3_cartographer'),
                                   'rviz', 'tb3_cartographer.rviz')

    namespaced_rviz_config = ReplaceString(
        source_file=rviz_config_dir,
        replacements={'<frame_ns>': frame_prefix},
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace',
            default_value='',
            description='Namespace to apply to all cartographer nodes'),

        DeclareLaunchArgument(
            'cartographer_config_dir',
            default_value=cartographer_config_dir,
            description='Full path to config file to load'),
        DeclareLaunchArgument(
            'configuration_basename',
            default_value=configuration_basename,
            description='Name of lua file for cartographer'),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),

        OpaqueFunction(function=launch_cartographer_node),

        DeclareLaunchArgument(
            'resolution',
            default_value=resolution,
            description='Resolution of a grid cell in the published occupancy grid'),

        DeclareLaunchArgument(
            'publish_period_sec',
            default_value=publish_period_sec,
            description='OccupancyGrid publishing period'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([ThisLaunchFileDir(), '/occupancy_grid.launch.py']),
            launch_arguments={'namespace': namespace, 'use_sim_time': use_sim_time,
                              'resolution': resolution,
                              'publish_period_sec': publish_period_sec}.items(),
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            namespace=namespace,
            arguments=['-d', namespaced_rviz_config],
            parameters=[{'use_sim_time': use_sim_time}],
            remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
            condition=IfCondition(use_rviz),
            output='screen'),
    ])

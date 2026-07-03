# TurtleBot3
<img src="https://raw.githubusercontent.com/ROBOTIS-GIT/emanual/master/assets/images/platform/turtlebot3/logo_turtlebot3.png" width="300">

- Active Branches: humble, jazzy, main(rolling)
- Legacy Branches: *-devel, noetic

---

# 🏷️ Namespacing (this fork): Structure & How to Change the Namespace
# CLONE THIS ALONGSIDE THE ROBOTIS turtlebot3 repo
This fork wraps the stock TurtleBot3 stack so every node, topic, action and TF frame
lives under a per-robot namespace. **The default namespace is `tb3_1`.** This section
explains where `tb3_1` lives and exactly what to edit to rename it (e.g. `tb3_1` → `robot_a`).

## 1. Package layout

Each source directory `*_namespaced/` builds a package **named** `*_tb3_1`
(the directory name is generic; the package name carries the robot label):

| Source directory | Package name | Build type | What it provides |
|---|---|---|---|
| `turtlebot3_namespaced/`             | `turtlebot3_tb3_1`             | ament_cmake  | metapackage |
| `turtlebot3_bringup_namespaced/`     | `turtlebot3_bringup_tb3_1`     | ament_cmake  | robot / rviz / camera / state-publisher launch |
| `turtlebot3_description_namespaced/` | `turtlebot3_description_tb3_1` | ament_cmake  | URDF + meshes + `model.rviz` |
| `turtlebot3_node_namespaced/`        | `turtlebot3_node_tb3_1`        | ament_cmake  | robot node params |
| `turtlebot3_cartographer_namespaced/`| `turtlebot3_cartographer_tb3_1`| ament_cmake  | Cartographer SLAM + `tb3_cartographer.rviz` |
| `turtlebot3_navigation2_namespaced/` | `turtlebot3_navigation2_tb3_1` | ament_cmake  | Nav2 + slam_toolbox + `tb3_navigation2.rviz` |
| `turtlebot3_example_namespaced/`     | `turtlebot3_example_tb3_1`     | ament_python | example nodes |
| `turtlebot3_teleop_namespaced/`      | `turtlebot3_teleop_tb3_1`      | ament_python | teleop |

## 2. Where the string `tb3_1` lives (3 independent levels)

`tb3_1` is reused for three *different* purposes. Understanding which is which is the key
to changing it safely — you almost always want to change **Levels 2 & 3 only** and leave
Level 1 (package names) alone.

| Level | Meaning | Follows the `namespace:=` launch arg? | Where it lives |
|---|---|---|---|
| **1. Package identity** — `*_tb3_1` | Build-system labels. A cosmetic tag; it does **not** have to equal the ROS namespace. | ❌ No (build-time) | `package.xml` `<name>`, `CMakeLists.txt` `project(...)`, `setup.py` `package_name`/entry-points, the Python module dirs `turtlebot3_example_tb3_1/` & `turtlebot3_teleop_tb3_1/`, every `get_package_share_directory('..._tb3_1')` call, and `package://turtlebot3_description_tb3_1/meshes/...` in the URDFs |
| **2. ROS namespace token** — `tb3_1` | The actual graph namespace: `/tb3_1/...` topics, actions, node names. | ⚠️ Partially | Launch defaults `LaunchConfiguration('namespace', default='tb3_1')` / `DeclareLaunchArgument('namespace', default_value='tb3_1')` **(these you can override with `namespace:=robot_a` at launch, no edit needed)**. Hardcoded `namespace='tb3_1'` that you **must** edit: `turtlebot3_bringup_namespaced/launch/camera.launch.py`, and the ament_python node scripts (`turtlebot3_teleop_.../teleop_keyboard.py`, all 6 `turtlebot3_example_...` nodes) |
| **3. Frame IDs & config strings** — `tb3_1/…`, `/tb3_1/…` | Literal frame/topic strings that consumers must match to the running robot. **Do not auto-follow anything.** | ❌ No (hardcoded) | Nav2 params `param/burger3310.yaml`, `param/burger.yaml`, `param/burger_cam.yaml` (`tb3_1/map`, `tb3_1/odom`, `tb3_1/base_link`, `tb3_1/base_footprint`, `tb3_1/scan`); `map/map.yaml` `frame_id:`; all three `rviz/*.rviz` (`Fixed Frame:` + every display/tool `Value: /tb3_1/...`) |

### Why the robot's own TF frames are *not* in the manual-edit list
The published TF frames (`tb3_1/base_link`, …) come from the URDF, which prefixes every
link/joint with `${namespace}`:
```xml
<xacro:arg name="namespace" default="tb3_1/"/>          <!-- fallback only -->
<xacro:property name="namespace" value="$(arg namespace)"/>
<link name="${namespace}base_link"/>
```
`turtlebot3_state_publisher.launch.py` passes `namespace:=<namespace>/` into that arg, so
**the robot's frames automatically follow the launch namespace.** Level 3 above is only the
*other* places (Nav2 params, RViz, saved map) that have to be told to match those frames.

## 3. How to change the namespace (keep package names)

Rename the runtime namespace only — this is what you want 95% of the time. Example
`tb3_1` → `robot_a`, run from `src/TB3/turtlebot3_namespaced/`:

```bash
NEW=robot_a

# (a) See every occurrence first, so you know what you're touching:
grep -rn "tb3_1" . --include="*.py" --include="*.yaml" --include="*.rviz" --include="*.urdf"

# (b) Level 3 — frame IDs + topic strings (word boundary \b protects package paths like
#     ".../turtlebot3_description_tb3_1/meshes"):
grep -rlE "\btb3_1/" . --include="*.yaml" --include="*.rviz" --include="*.urdf" \
  | xargs sed -i -E "s#\btb3_1/#${NEW}/#g"

# (c) Level 2 — namespace literals in launch files + python node scripts (the quotes keep
#     it from matching package names like 'turtlebot3_example_tb3_1'):
grep -rl "'tb3_1'" . --include="*.py" | xargs sed -i "s#'tb3_1'#'${NEW}'#g"

# (d) Review, then rebuild (install is a plain copy — edits don't take effect until built):
git diff
cd /home/jp16/colcon_ws && colcon build && source install/setup.bash
```

> **GNU sed** is assumed for `\b`. Review `git diff` before building — the `\b` rule is what
> keeps `*_tb3_1` package names intact while changing `tb3_1/` frames.

Prefer editing by hand? Change the same three levels in the files listed in the table above.
You can also skip the Level-2 launch-default edits and just launch with the argument:
`ros2 launch turtlebot3_navigation2_tb3_1 nav_slam.launch.py namespace:=robot_a` — but Level 3
(params/RViz/map) still must be edited to match, and the hardcoded node namespaces still won't move.

## 4. Verify

```bash
ros2 node list        | grep robot_a     # nodes now under /robot_a/...
ros2 action list      | grep -v '/robot_a/'   # should print nothing (all namespaced)
ros2 run tf2_ros tf2_echo robot_a/map robot_a/odom \
  --ros-args -r /tf:=/robot_a/tf -r /tf_static:=/robot_a/tf_static   # SLAM's map->odom
```

## 5. (Advanced) Also rename the packages — Level 1

Only needed if you want package *names* to match the robot (e.g. maintaining several robots'
package sets side by side). Heavier: rename the module dirs `turtlebot3_example_tb3_1/` and
`turtlebot3_teleop_tb3_1/`, then replace `_tb3_1` → `_robot_a` across `package.xml`,
`CMakeLists.txt` (`project()`), `setup.py`, every `get_package_share_directory('..._tb3_1')`
call, and `package://..._tb3_1/` mesh paths in the URDFs. Do this **in addition to** section 3.

## 6. (Recommended) Make future renames a one-flag change

`bringup_launch.py` already supports a `<robot_namespace>` placeholder
(`ReplaceString(replacements={'<robot_namespace>': ('/', namespace)})`), but the param files
currently hardcode `tb3_1/` instead of using it. If you replace the hardcoded `tb3_1/` frame
prefixes in `param/*.yaml` with `<robot_namespace>/`, Level 3 will follow the `namespace:=`
launch argument automatically and you'll only ever set the namespace in one place.

## Open Source Projects Related to TurtleBot3
- [turtlebot3](https://github.com/ROBOTIS-GIT/turtlebot3)
- [turtlebot3_msgs](https://github.com/ROBOTIS-GIT/turtlebot3_msgs)
- [turtlebot3_simulations](https://github.com/ROBOTIS-GIT/turtlebot3_simulations)
- [turtlebot3_manipulation](https://github.com/ROBOTIS-GIT/turtlebot3_manipulation)
- [turtlebot3_manipulation_simulations](https://github.com/ROBOTIS-GIT/turtlebot3_manipulation_simulations)
- [turtlebot3_applications](https://github.com/ROBOTIS-GIT/turtlebot3_applications)
- [turtlebot3_applications_msgs](https://github.com/ROBOTIS-GIT/turtlebot3_applications_msgs)
- [turtlebot3_machine_learning](https://github.com/ROBOTIS-GIT/turtlebot3_machine_learning)
- [turtlebot3_autorace](https://github.com/ROBOTIS-GIT/turtlebot3_autorace)
- [turtlebot3_home_service_challenge](https://github.com/ROBOTIS-GIT/turtlebot3_home_service_challenge)
- [hls_lfcd_lds_driver](https://github.com/ROBOTIS-GIT/hls_lfcd_lds_driver)
- [ld08_driver](https://github.com/ROBOTIS-GIT/ld08_driver)
- [coin_d4_driver](https://github.com/ROBOTIS-GIT/coin_d4_driver)
- [open_manipulator](https://github.com/ROBOTIS-GIT/open_manipulator)
- [dynamixel_sdk](https://github.com/ROBOTIS-GIT/DynamixelSDK)
- [OpenCR-Hardware](https://github.com/ROBOTIS-GIT/OpenCR-Hardware)
- [OpenCR](https://github.com/ROBOTIS-GIT/OpenCR)

## Documentation, Videos, and Community

### Official Documentation
- ⚙️ **[ROBOTIS DYNAMIXEL](https://dynamixel.com/)**
- 📚 **[ROBOTIS e-Manual for Dynamixel SDK](http://emanual.robotis.com/docs/en/software/dynamixel/dynamixel_sdk/overview/)**
- 📚 **[ROBOTIS e-Manual for TurtleBot3](http://turtlebot3.robotis.com/)**
- 📚 **[ROBOTIS e-Manual for OpenMANIPULATOR-X](https://emanual.robotis.com/docs/en/platform/openmanipulator_x/overview/)**

### Learning Resources
- 🎥 **[ROBOTIS YouTube Channel](https://www.youtube.com/@ROBOTISCHANNEL)**
- 🎥 **[ROBOTIS Open Source YouTube Channel](https://www.youtube.com/@ROBOTISOpenSourceTeam)**
- 🎥 **[ROBOTIS TurtleBot3 YouTube Playlist](https://www.youtube.com/playlist?list=PLRG6WP3c31_XI3wlvHlx2Mp8BYqgqDURU)**
- 🎥 **[ROBOTIS OpenMANIPULATOR YouTube Playlist](https://www.youtube.com/playlist?list=PLRG6WP3c31_WpEsB6_Rdt3KhiopXQlUkb)**

### Community & Support
- 💬 **[ROBOTIS Community Forum](https://forum.robotis.com/)**
- 💬 **[TurtleBot category from ROS Community](https://discourse.ros.org/c/turtlebot/)**

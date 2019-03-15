cmake_minimum_required(VERSION 2.8.3)
project(rsync_ros)


find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  genmsg
  actionlib_msgs
  actionlib
)


################################################
## Declare ROS messages, services and actions ##
################################################

add_action_files(
    FILES
    Rsync.action
)

add_service_files(
    FILES
    RsyncService.srv
)

generate_messages(
 DEPENDENCIES
 std_msgs
 actionlib_msgs
)

###################################
## catkin specific configuration ##
###################################

catkin_package(
 #INCLUDE_DIRS include
 LIBRARIES image_to_file
 CATKIN_DEPENDS rospy std_msgs message_runtime
 DEPENDS system_lib
)

###########
## Build ##
###########

include_directories(
  ${catkin_INCLUDE_DIRS}
)

#############
## Install ##
#############

catkin_install_python(PROGRAMS src/rsync_server_node.py DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

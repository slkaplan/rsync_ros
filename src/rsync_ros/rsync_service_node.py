#!/usr/bin/env python

# Software License Agreement (BSD License)
#
# Copyright (c) 2019, Thomas Kostas
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of the author may be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import rospy
from .rsync import Rsync
from rsync_ros.srv import RsyncService, RsyncServiceResponse


class RsyncServiceServer:
    def __init__(self, service_path='/rsync_ros/run', spin_freq=1):
        self.rsync_service_proxy = None
        self.service_path = service_path
        self.dispatch_services()
        self.refresh_rate = rospy.Rate(spin_freq)

    def dispatch_services(self):
        self.rsync_service_proxy = rospy.Service(self.service_path, RsyncService, self.rsync_service_callback)
        rospy.loginfo("Successfully dispatched " + self.service_path)

    @staticmethod
    def rsync_service_callback(request):
        ip = request.target_ip
        username = request.target_user
        if request.local_path is not None:
            local_path = os.path.abspath(os.path.expanduser(request.local_path))
        options = request.options
        target_path = request.target_path

        rospy.loginfo("Attempting to sync " + local_path + " to machine " + ip + " in location " + target_path +
                      " with user " + username + " using following options [" + options + "]")

        dest = username + "@" + ip + ":" + target_path
        rospy.loginfo(dest)
        a = list()
        a.append(options)
        rsync = Rsync(a, local_path, dest)
        success = rsync.sync()

        if success is True:
            rospy.loginfo("Successfully synced " + local_path + " to machine " + ip + " in location " + target_path)
        else:
            rospy.loginfo("Failed to sync " + local_path + " to machine " + ip + " in location " + target_path)
        resp = RsyncServiceResponse()
        resp.success = success
        return resp

    def shutdown_services(self, reason):
        try:
            self.rsync_service_proxy.shutdown(reason)
        except AttributeError:
            rospy.logerr("Fail to shutdown rsync_service Service")

    def spin(self):
        """
        Spinning method avoiding the object instance to be garbage collected when running as a node.
        """
        while not rospy.is_shutdown():
            self.refresh_rate.sleep()
        self.shutdown_services("ROS shutdown")

if __name__ == "__main__":
    try:
        rospy.init_node('rsync_ros')
        RsyncServiceServer(rospy.get_name())
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
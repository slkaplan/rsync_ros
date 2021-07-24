#!/usr/bin/env python

# Software License Agreement (BSD License)
#
# Copyright (c) 2016, Alex McClung
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

import rospy
import roslib
import actionlib
import os
import sys

# from .rsync import Rsync
from rsync import Rsync
from rsync_ros.msg import RsyncAction, RsyncResult, RsyncFeedback

roslib.load_manifest('rsync_ros')


class RsyncActionServer:
    def __init__(self, name):
        self.result = None
        self.rsync = None
        self.feedback = None
        self._action_name = name
        self.server = actionlib.SimpleActionServer(self._action_name, RsyncAction, self.execute, False)
        self.server.start()
        rospy.loginfo("Ready to sync files.")

    def progress_update_cb(self, line, percent_complete, transfer_rate):
        # This is run every time the progress is published to stdout
        # rospy.loginfo('Total transfer percentage: {}'.format(percent_complete))

        self.feedback.percent_complete = percent_complete
        self.feedback.transfer_rate = transfer_rate
        self.server.publish_feedback(self.feedback)

        if line:
            rospy.loginfo(line)
        # Check if preempt (cancel action) has been requested by the client
        if self.server.is_preempt_requested():
            # Get the process id & try to terminate it gracefuly
            pid = self.rsync.p.pid
            self.rsync.p.terminate()
            # Check if the process has really terminated & force kill if not.
            try:
                os.kill(pid, 0)
                self.rsync.p.kill()
                print("Forced kill")
            except OSError:
                print("Terminated gracefully")

            rospy.loginfo('%s: Preempted' % self._action_name)
            self.server.set_preempted()
            # TO-DO, fix logic error changing states upon preempt request

    def execute(self, goal):
        self.result = RsyncResult()
        self.feedback = RsyncFeedback()

        rospy.loginfo("Executing rsync command '%s %s %s'", 'rsync ' + ' '.join(goal.rsync_args) +
                      ' --progress --outbuf=L', goal.source_path, goal.destination_path)
        self.rsync = Rsync(goal.rsync_args, goal.source_path, goal.destination_path,
                           progress_callback=self.progress_update_cb)
        self.result.sync_success = self.rsync.sync()

        if not self.server.is_preempt_requested():
            if self.rsync.stderr_block:
                rospy.logerr('\n{}'.format(self.rsync.stderr_block))
            rospy.loginfo("Rsync command result '%s'", self.result.sync_success)
            self.server.set_succeeded(self.result)


if __name__ == "__main__":
    try:
        rospy.init_node('rsync_ros')
        RsyncActionServer(rospy.get_name())
        rospy.spin()
    except rospy.ROSInterruptException:
        pass

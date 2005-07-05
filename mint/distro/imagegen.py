#
# Copyright (c) 2004-2005 Specifix, Inc.
#
# All Rights Reserved
#

import os
import sys

from mint import jobstatus

class ImageGenerator:
    def __init__(self, client, cfg, job, profileId):
        self.client = client
        self.cfg = cfg
        self.job = job
        self.profileId = profileId

    def write(self):
        raise NotImplementedError

    def status(self, msg):
        self.job.setStatus(jobstatus.RUNNING, msg)

    def grabOutput(self, logFile):
        """Redirect stdout and stderr to a file"""
        self.logfd = os.open(logFile, os.O_TRUNC | os.O_WRONLY | os.O_CREAT)
        sys.stdout.flush()
        sys.stderr.flush()

        self.stdout = os.dup(sys.stdout.fileno())
        self.stderr = os.dup(sys.stderr.fileno())
        os.dup2(self.logfd, sys.stdout.fileno())
        os.dup2(self.logfd, sys.stderr.fileno())

    def releaseOutput(self):
        """Restore stdout and stderr to the original state before grabOutput"""
        sys.stdout.flush()
        sys.stderr.flush()

        os.dup2(self.stdout, sys.stdout.fileno())
        os.dup2(self.stderr, sys.stderr.fileno())
        os.close(self.stdout)
        os.close(self.stderr)

        os.close(self.logfd)

#
# Copyright (c) 2004-2005 Specifix, Inc.
#
# All Rights Reserved
#

import os
import sys

class ImageGenerator:
    def __init__(self, client, cfg, job, profileId):
        self.client = client
        self.cfg = cfg
        self.job = job
        self.profileId = profileId

    def write(self):
        raise NotImplementedError

    def grabOutput(self, logFile):
        logfd = os.open(logFile, os.O_TRUNC | os.O_WRONLY | os.O_CREAT)
        self.stdout = os.dup(sys.stdout.fileno())
        self.stderr = os.dup(sys.stderr.fileno())
        os.dup2(logfd, sys.stdout.fileno())
        os.dup2(logfd, sys.stderr.fileno())
        os.close(logfd)

    def releaseOutput(self):
        os.dup2(self.stdout, sys.stdout.fileno())
        os.dup2(self.stderr, sys.stderr.fileno())

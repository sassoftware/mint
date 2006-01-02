#
# Copyright (c) 2004-2005 rPath, Inc.
#
# All Rights Reserved
#

import os
import sys

from mint import jobstatus

from threading import currentThread

class NoConfigFile(Exception):
    def __init__(self, path = ""):
        self._path = path

    def __str__(self):
        return "Unable to access configuration file: %s" % self._path

class ImageGenerator:
    configObject = None

    def __init__(self, client, cfg, job, profileId):
        self.client = client
        self.cfg = cfg
        self.job = job
        self.profileId = profileId

    def getConfig(self):
        assert(self.configObject)
        imageCfg = self.configObject()

        cfgFile = os.path.join(self.cfg.configPath, imageCfg.filename)
        if os.access(cfgFile, os.R_OK):
            imageCfg.read(cfgFile)
        else:
            raise NoConfigFile(cfgFile)
        return imageCfg

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

def getParentThread():
    # parentThread is defined in the JobRunner class
    # we use this to check if the main thread is still alive, so we
    # can abort if it's not...
    try:
        r = currentThread().parentThread
    except (NameError, AttributeError):
        # we'll get here if getParentThread was used outside of a
        # JobRunner thread. oh well, we won't be able to abort cleanly.
        r = currentThread()
    return r

def getJobId(parentThread = None):
    if not parentThread:
        parentThread = getParentThread
    try:
        job = parentThread.job
    except AttributeError:
        # we'll get here if current thread is not a JobRunner thread.
        return None
    return job.jobId

def assertParentAlive():
    parentThread = getParentThread()
    if not parentThread.isAlive():
        jobId = getJobId(parentThread)
        raise RuntimeError("Job %d aborted." %jobId)

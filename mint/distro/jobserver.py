#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#
import errno
import threading
import socket
import time
import random
import traceback
import os
import sys
from xmlrpclib import ProtocolError

# conary imports
from conary import conaryclient
from conary.conarycfg import ConfigFile, ConaryConfiguration
from conary.conarycfg import CfgList, CfgString, CfgBool, CfgInt, CfgEnum, CfgDict
from conary.lib import log 

# mint imports
from mint import cooktypes
from mint import jobstatus
from mint import releasetypes
from mint.mint import MintClient

# image generators
from mint.distro.installable_iso import InstallableIso
from mint.distro.live_iso import LiveIso
from mint.distro.live_cf_image import LiveCFImage
from mint.distro.stub_image import StubImage
from mint.distro.netboot_image import NetbootImage
from mint.distro.group_trove import GroupTroveCook
from mint.distro.bootable_image import BootableImage

generators = {
    releasetypes.INSTALLABLE_ISO:   InstallableIso,
    releasetypes.STUB_IMAGE:        StubImage,
}

SUPPORTED_ARCHS = ('x86', 'x86_64')


class JobRunner(threading.Thread):
    def __init__(self, cfg, client, job):
        threading.Thread.__init__(self)
        self.cfg = cfg
        self.client = client
        self.job = job
        # still in parent thread when init gets called.
        self.parentThread = threading.currentThread()

    def run(self):
        # ensure each job thread has it's own process space
        pid = os.fork()
        if not pid:
            self.doWork()
            os._exit(0)
        else:
            try:
                os.waitpid(pid, 0)
            except OSError, e:
                if e.errno != errno.ECHILD:
                    raise

    def doWork(self):
        ret = None
        error = None
        jobId = self.job.getId()
        self.job.setStatus(jobstatus.RUNNING, 'Running')

        if self.job.releaseId:
            release = self.client.getRelease(self.job.releaseId)
            project = self.client.getProject(release.getProjectId())

            # save the current working directory in case the generator
            # (or scripts that change the wd)
            cwd = os.getcwd()
            try:
                #Iterate through the different jobs
                imageTypes = release.getImageTypes()
                imageFilenames = []
                if releasetypes.INSTALLABLE_ISO in imageTypes:
                    generator = generators[releasetypes.INSTALLABLE_ISO]
                    log.info("%s job for %s started (id %d)" % \
                             (generator.__name__,
                              project.getHostname(), jobId))
                    imageFilenames.extend(generator(self.client,
                                                    self.cfg, self.job,
                                                    release, project).write())
                    os.chdir(cwd)
                #Now for the bootable images
                imagegen = BootableImage(self.client, self.cfg, self.job, release, project)
                imagegen.setImageTypes(imageTypes)
                if imagegen.workToDo():
                    log.info("%s job for %s started (id %d)" % \
                             (BootableImage.__name__,
                              project.getHostname(), jobId))

                    imageFilenames.extend(imagegen.write())
                else:
                    log.info("job %s:%d did not have a bootable image"
                             " generation request" % (project.getHostname(),
                                                      jobId))
                # and stub images
                if releasetypes.STUB_IMAGE in imageTypes:
                    generator = generators[releasetypes.STUB_IMAGE]
                    log.info("stub image for %s started (id %d)" % (project.getHostname(), jobId))
                    imageFilenames.extend(generator(self.client,
                        self.cfg, self.job, release, project).write())

            except Exception, e:
                traceback.print_exc()
                sys.stdout.flush()
                error = e
                self.job.setStatus(jobstatus.ERROR, str(e))
            else:
                release.setFiles(imageFilenames)
                log.info("job %d finished: %s", jobId, str(imageFilenames))
            os.chdir(cwd)
        elif self.job.getGroupTroveId():
            try:
                log.info("GroupTroveCook job started (id %d)" % (jobId))
                ret = GroupTroveCook(self.client, self.cfg, self.job).write()
            except Exception, e:
                traceback.print_exc()
                sys.stdout.flush()
                error = e
                self.job.setStatus(jobstatus.ERROR, str(e))
            else:
                log.info("job %d succeeded: %s" % (jobId, str(ret)))

        if error:
            log.info(error)
        else:
            self.job.setStatus(jobstatus.FINISHED, "Finished")

def updateWaitStatus(client):
    joblist = client.getJobs()
    for job in joblist:
        if job.getStatus() == jobstatus.WAITING:
            job.setStatus(jobstatus.WAITING,
                          client.server.getJobWaitMessage(job.getId()))


class JobDaemon:
    def __init__(self, cfg):
        client = MintClient(cfg.serverUrl)

        confirmedAlive = False

        try:
            os.makedirs(cfg.logPath)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise

        # normalize the job daemon machine's architecture
        # right now we only handle x86 and x86_64 images
        log.info("handling jobs of architecture: %s", cfg.supportedArch)

        runningJobs = []

        errors = 0
        while(True):
            for jobThread in runningJobs[:]:
                if not jobThread.isAlive():
                    jobThread.join()
                    runningJobs.remove(jobThread)

            if len(runningJobs) < cfg.maxThreads:
                try:
                    job = client.startNextJob(["1#" + x for x in \
                                               cfg.supportedArch],
                                              cfg.jobTypes)
                    if errors and not confirmedAlive:
                        log.warning("rBuilder server reached after %d attempt(s), resuming normal operation" % errors)
                        errors = 0
                    confirmedAlive = True

                    if not job:
                        # sleeping for a random interval helps prevent
                        # concurrency issues with multiple instances of
                        # this code
                        time.sleep(random.uniform(3, 5))
                        continue

                    if job.releaseId:
                        release = client.getRelease(job.releaseId)
                        if release.getArch() not in cfg.supportedArch:
                            continue

                    job.setStatus(jobstatus.RUNNING, 'Starting')
                    th = JobRunner(cfg, client, job)
                    th.start()
                    updateWaitStatus(client)

                    # queue this thread and move on
                    runningJobs.append(th)

                # if the rBuilder Online server is down, we will get either a
                # ProtocolError or a socket error depending on what xmlrpc lib
                # was doing when the server went down. simply wait for it.
                except (ProtocolError, socket.error), e:
                    if not confirmedAlive:
                        errors += 1
                        if errors > 5:
                            log.error("rBuilder Server Unreachable after 5 attempts; exiting")
                            return
                        else:
                            log.error("rBuilder Server Unreachable: trying again (attempt %d/5)" % errors)

                    log.warning("Error retrieving job list:" + str(e))
                    time.sleep(5)
            else:
                # we get here if we already have (maxThreads) jobs running
                time.sleep(5)


class CfgCookType(CfgEnum):
    validValues = cooktypes.validCookTypes

class CfgImageType(CfgEnum):
    validValues = releasetypes.validImageTypes

class IsoGenConfig(ConfigFile):
    supportedArch   = CfgList(CfgString)
    cookTypes       = CfgList(CfgCookType)
    imageTypes      = CfgList(CfgImageType)
    serverUrl       = None
    SSL             = (CfgBool, False)
    logPath         = '/srv/mint/logs'
    imagesPath      = '/srv/mint/images/'
    finishedPath    = '/srv/mint/finished-images/'
    lockFile        = '/var/run/mint-jobdaemon.pid'
    maxThreads      = (CfgInt, 5)

    def read(cfg, path, exception = False):
        ConfigFile.read(cfg, path, exception)
        for arch in cfg.supportedArch:
            if arch not in SUPPORTED_ARCHS:
                log.error("unsupported architecture: %s", arch)
                sys.exit(1)
        cfg.jobTypes = {}
        if 'cookTypes' in cfg.__dict__:
            cfg.jobTypes['cookTypes'] = cfg.cookTypes
            del cfg.cookTypes
        if 'imageTypes' in cfg.__dict__:
            cfg.jobTypes['imageTypes'] = cfg.imageTypes
            del cfg.imageTypes
        if cfg.serverUrl is None:
            log.error("a server URL must be specified in the config file,"
            " for example:")
            log.error("serverUrl http://username:userpass@"
                      "www.example.com/xmlrpc-private/")
            sys.exit(1)


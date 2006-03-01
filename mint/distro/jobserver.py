#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#
import errno
import socket
import time
import random
import traceback
import os
import sys
from xmlrpclib import ProtocolError
import signal

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
# JOB_IDLE_INTERVAL: interval is in seconds. format is (min, max)
JOB_IDLE_INTERVAL = (5, 10)

class JobRunner:
    def __init__(self, cfg, client, job):
        self.cfg = cfg
        self.client = client
        self.job = job

    def run(self):
        # ensure each job thread has it's own process space
        pid = os.fork()
        if not pid:
            self.doWork()
            os._exit(0)
        else:
            return pid

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
                    log.info("(%d) %s job for %s started (id %d)" % \
                             (os.getpid(), generator.__name__,
                              project.getHostname(), jobId))
                    imageFilenames.extend(generator(self.client,
                                                    self.cfg, self.job,
                                                    release, project).write())
                    os.chdir(cwd)
                #Now for the bootable images
                imagegen = BootableImage(self.client, self.cfg, self.job, release, project)
                imagegen.setImageTypes(imageTypes)
                if imagegen.workToDo():
                    log.info("(%d) %s job for %s started (id %d)" % \
                             (os.getpid(), BootableImage.__name__,
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
                log.info("(%d) job %d finished: %s", os.getpid(), jobId, str(imageFilenames))
            os.chdir(cwd)
        elif self.job.getGroupTroveId():
            try:
                log.info("(%d) GroupTroveCook job started (id %d)" % (os.getpid(), jobId))
                ret = GroupTroveCook(self.client, self.cfg, self.job).write()
            except Exception, e:
                traceback.print_exc()
                sys.stdout.flush()
                error = e
                self.job.setStatus(jobstatus.ERROR, str(e))
            else:
                log.info("(%d) job %d succeeded: %s" % (os.getpid(), jobId, str(ret)))

        if error:
            log.info(error)
        else:
            self.job.setStatus(jobstatus.FINISHED, "Finished")


class JobDaemon:
    def __init__(self, cfg):
        client = MintClient(cfg.serverUrl)

        confirmedAlive = False

        self.takingJobs = True

        def stopJobs(signalNum, frame):
            self.takingJobs = False
            if signalNum == signal.SIGTERM:
                signalName = 'SIGTERM'
            elif signalNum == signal.SIGINT:
                signalName = 'SIGINT'
            else:
                signalName = 'UNKNOWN'
            log.info("Caught %s signal. No more jobs will be requested." % \
                     signalName)
            signal.signal(signal.SIGTERM, self.origTerm)
            signal.signal(signal.SIGINT, self.origInt)
            # alter the lock file
            try:
                stats = os.stat(cfg.lockfile)
            except:
                exc, e, bt = sys.exc_info()
                log.error("got %s while trying to stat lockfile" % str(e))
            else:
                # ensure we don't write to an empty file
                if stats[7]:
                    lockFile = open(cfg.lockFile, 'a')
                    lockFile.write('\nSHUTTING_DOWN')
                    lockFile.close()

        self.origTerm = signal.signal(signal.SIGTERM, stopJobs)
        self.origInt = signal.signal(signal.SIGINT, stopJobs)

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
        while(self.takingJobs or runningJobs):
            for jobPid in runningJobs[:]:
                try:
                    os.waitpid(jobPid, os.WNOHANG)
                except OSError:
                    runningJobs.remove(jobPid)

            if len(runningJobs) < cfg.maxThreads:
                try:
                    if self.takingJobs:
                        job = client.startNextJob(["1#" + x for x in \
                                                   cfg.supportedArch],
                                                  cfg.jobTypes)
                    else:
                        job = None
                    if errors and not confirmedAlive:
                        log.warning("rBuilder server reached after %d attempt(s), resuming normal operation" % errors)
                        errors = 0
                    confirmedAlive = True

                    if not job:
                        # sleeping for a random interval helps prevent
                        # concurrency issues with multiple instances of
                        # this code
                        time.sleep(random.uniform(*JOB_IDLE_INTERVAL))
                        continue

                    log.info("(%d) TOOK A JOB: jobId %d" % (os.getpid(), job.id))
                    if job.releaseId:
                        release = client.getRelease(job.releaseId)
                        if release.getArch() not in cfg.supportedArch:
                            continue

                    job.setStatus(jobstatus.RUNNING, 'Starting')
                    th = JobRunner(cfg, client, job)
                    jobPid = th.run()

                    # queue this thread and move on
                    runningJobs.append(jobPid)

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
            # sleep at the end of every run, no matter what the outcome was
            time.sleep(random.uniform(*JOB_IDLE_INTERVAL))
        log.info("Job server daemon is exiting.")


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
    configPath       = '/srv/mint/'

    def read(cfg, path, exception = False):
        ConfigFile.read(cfg, path, exception)
        cfg.configPath = os.path.dirname(path)
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


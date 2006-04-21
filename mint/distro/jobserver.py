#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#
import errno
import random
import os
import signal
import socket
import sys
import time
import traceback
from xmlrpclib import ProtocolError

# conary imports
from conary import conaryclient
from conary.conarycfg import ConfigFile, ConaryConfiguration
from conary.conarycfg import CfgList, CfgString, CfgBool, CfgInt, CfgDict, \
     CfgEnum

# mint imports
from mint import cooktypes
from mint import jobstatus
from mint import releasetypes
from mint import scriptlibrary
from mint.client import MintClient
from mint.config import CfgImageEnum
from mint.constants import mintVersion

# image generators
from mint.distro.installable_iso import InstallableIso
from mint.distro.live_iso import LiveIso
from mint.distro.raw_hd_image import RawHdImage
from mint.distro.vmware_image import VMwareImage
from mint.distro.stub_image import StubImage
from mint.distro.netboot_image import NetbootImage
from mint.distro.group_trove import GroupTroveCook
from mint.distro.bootable_image import BootableImage
from mint.distro.raw_fs_image import RawFsImage
from mint.distro.tarball import Tarball

generators = {
    releasetypes.INSTALLABLE_ISO:   InstallableIso,
    releasetypes.STUB_IMAGE:        StubImage,
    releasetypes.LIVE_ISO:          LiveIso,
    releasetypes.RAW_HD_IMAGE:      RawHdImage,
    releasetypes.VMWARE_IMAGE:      VMwareImage,
    releasetypes.RAW_FS_IMAGE:      RawFsImage,
    releasetypes.TARBALL:           Tarball,
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
            try:
                self.doWork()
            finally:
                # always die here, no matter what.
                os._exit(0)
        else:
            return pid

    def doWork(self):
        ret = None
        error = None
        jobId = self.job.getId()
        slog = scriptlibrary.getScriptLogger()

        self.job.setStatus(jobstatus.RUNNING, 'Running')

        if self.cfg.saveChildOutput:
            joboutputPath = os.path.join(self.cfg.logPath, 'joboutput')
            if not os.path.exists(joboutputPath):
                os.mkdir(joboutputPath)
            logFile = os.path.join(self.cfg.logPath, "joboutput",
                    "%s_%d.out" % (time.strftime('%Y%m%d%H%M%S'), jobId))
            slog.debug("Output logged to %s" % logFile)

            sys.stdout.flush()
            sys.stderr.flush()

            logfd = os.open(logFile, os.O_WRONLY | os.O_CREAT, 0664)

            os.dup2(logfd, sys.stdout.fileno())
            os.dup2(logfd, sys.stderr.fileno())

            sys.stdout.flush()

        # make sure conary's logger instance is logging (almost) all output
        # N.B. debug is probably *too* verbose, really
        from conary.lib import log
        from logging import INFO
        log.setVerbosity(INFO)

        if self.job.releaseId:
            release = self.client.getRelease(self.job.releaseId)
            project = self.client.getProject(release.getProjectId())

            # save the current working directory in case the generator
            # (or scripts that change the wd)
            cwd = os.getcwd()
            try:
                # this line assumes that there's only one image per job.
                generator = generators[release.getImageTypes()[0]]
                slog.info("%s job for %s started (id %d)" % \
                         (generator.__name__, project.getHostname(), jobId))
                imageFilenames = generator(self.client, self.cfg, self.job,
                                           release, project).write()
            except Exception, e:
                traceback.print_exc()
                sys.stdout.flush()
                error = e
            else:
                release.setFiles(imageFilenames)
                slog.info("Job %d finished: %s", jobId, str(imageFilenames))

            try:
                os.chdir(cwd)
            except:
                pass

        elif self.job.getGroupTroveId():
            try:
                slog.info("Group trove cook job started (id %d)" % jobId)
                ret = GroupTroveCook(self.client, self.cfg, self.job).write()
            except Exception, e:
                traceback.print_exc()
                sys.stdout.flush()
                error = e
            else:
                slog.info("Job %d succeeded: %s" % (jobId, str(ret)))

        if error:
            slog.error("Job %d failed: %s", jobId, str(error))
            self.job.setStatus(jobstatus.ERROR, str(e))
            raise error
        else:
            self.job.setStatus(jobstatus.FINISHED, "Finished")


class JobDaemon:
    def __init__(self, cfg):
        client = MintClient(cfg.serverUrl)

        confirmedAlive = False

        self.takingJobs = True

        slog = scriptlibrary.getScriptLogger()

        def stopJobs(signalNum, frame):
            slog = scriptlibrary.getScriptLogger()
            self.takingJobs = False
            if signalNum == signal.SIGTERM:
                signalName = 'SIGTERM'
            elif signalNum == signal.SIGINT:
                signalName = 'SIGINT'
            else:
                signalName = 'UNKNOWN'
            slog.info("Caught %s signal. No more jobs will be requested." % \
                     signalName)
            signal.signal(signal.SIGTERM, self.origTerm)
            signal.signal(signal.SIGINT, self.origInt)
            # alter the lock file
            try:
                stats = os.stat(cfg.lockFile)
            except:
                exc, e, bt = sys.exc_info()
                slog.error("Got %s while trying to stat lockfile" % str(e))
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
        slog.info("rBuilder ISOgen Version: %s" % mintVersion)
        slog.info("handling jobs of architecture: %s", cfg.supportedArch)
        if 'imageTypes' in cfg.jobTypes:
            slog.info("handling images: %s" \
                     % str([releasetypes.typeNamesShort[x] \
                            for x in cfg.jobTypes['imageTypes']]))
        if 'cookTypes' in cfg.jobTypes:
            slog.info("handling cooks: %s" \
                     % str([cooktypes.typeNames[x] \
                            for x in cfg.jobTypes['cookTypes']]))

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
                                                  cfg.jobTypes,
                                                  mintVersion)
                    else:
                        job = None
                    if errors and not confirmedAlive:
                        slog.info("rBuilder server reached after %d attempt(s), resuming normal operation" % errors)
                        errors = 0
                    confirmedAlive = True

                    if not job:
                        # sleeping for a random interval helps prevent
                        # concurrency issues with multiple instances of
                        # this code
                        time.sleep(random.uniform(*JOB_IDLE_INTERVAL))
                        continue

                    if job.releaseId:
                        release = client.getRelease(job.releaseId)
                        if release.getArch() not in cfg.supportedArch:
                            continue

                    job.setStatus(jobstatus.RUNNING, 'Starting')
                    slog.info("Took ownership of jobId %d" % job.id)
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
                            slog.error("rBuilder Server Unreachable after 5 attempts; exiting")
                            return
                        else:
                            slog.error("rBuilder Server Unreachable: trying again (attempt %d/5)" % errors)

                    slog.warning("Error retrieving job list: " + str(e))
                except Exception, e:
                    slog.error("Fatal exception caught: " + str(e))
                    break
            # sleep at the end of every run, no matter what the outcome was
            time.sleep(random.uniform(*JOB_IDLE_INTERVAL))
        slog.info("Job server daemon is exiting.")


class CfgCookEnum(CfgEnum):
    validValues = cooktypes.validCookTypes

class IsoGenConfig(ConfigFile):
    supportedArch   = CfgList(CfgString)
    cookTypes       = CfgList(CfgCookEnum)
    imageTypes      = CfgList(CfgImageEnum)
    serverUrl       = None
    SSL             = (CfgBool, False)
    logPath         = '/srv/mint/logs'
    imagesPath      = '/srv/mint/images/'
    finishedPath    = '/srv/mint/finished-images/'
    lockFile        = '/var/run/mint-jobdaemon.pid'
    maxThreads      = (CfgInt, 5)
    configPath      = '/srv/mint/'

    def read(cfg, path, exception = False):
        slog = scriptlibrary.getScriptLogger()
        ConfigFile.read(cfg, path, exception)
        cfg.configPath = os.path.dirname(path)
        for arch in cfg.supportedArch:
            if arch not in SUPPORTED_ARCHS:
                slog.error("unsupported architecture: %s", arch)
                sys.exit(1)
        cfg.jobTypes = {}
        if 'cookTypes' in cfg.__dict__:
            cfg.jobTypes['cookTypes'] = cfg.cookTypes
        if 'imageTypes' in cfg.__dict__:
            cfg.jobTypes['imageTypes'] = cfg.imageTypes
        if cfg.serverUrl is None:
            slog.error("A server URL must be specified in the config file. For example:")
            slog.error("    serverUrl http://username:userpass@www.example.com/xmlrpc-private/")
            sys.exit(1)

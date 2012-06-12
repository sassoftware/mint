#
# Copyright (c) 2011 rPath, Inc.
#

import re
import StringIO

from conary.lib import util

from rmake.cmdline import helper as rmakeHelper
from rmake.cmdline import query as rmakeQuery
from rmake import errors as rmakeErrors

from mint.rmake3_package_creator import rmakecfg

class Constants(object):
    BUILD_STATUS_FAILED = 0
    BUILD_STATUS_COMMITTING = 1
    BUILD_STATUS_COMMITTED = 2
    BUILD_STATUS_QUEUED = 3
    BUILD_STATUS_RUNNING = 4
    BUILD_STATUS_BUILT = 5
    BUILD_STATUS_BUILDING = 6
    BUILD_STATUS_FINISHED = 7

    BUILD_STATUS_STRINGS = {
        BUILD_STATUS_FAILED : "failed",
        BUILD_STATUS_COMMITTING : "committing",
        BUILD_STATUS_COMMITTED : "committed",
        BUILD_STATUS_QUEUED : "queued",
        BUILD_STATUS_RUNNING : "running",
        BUILD_STATUS_BUILT : "built",
        BUILD_STATUS_BUILDING : "building",
        BUILD_STATUS_FINISHED : "finished",
    }

    isDone = set([BUILD_STATUS_COMMITTED])

class Callback(object):
    def notify_error(self, builder, job):
        pass

    def notify_built(self, builder, job):
        pass

    def notify_committed(self, builder, job):
        pass

class Errors(object):
    class PackageCreatorError(Exception):
        msg = "An unknown error occured in Package Creator"
        def __init__(self, msg = None, *args):
            if msg is not None:
                if not isinstance(msg, basestring):
                    msg = str(msg)
                if args:
                    self.msg = msg % args
                else:
                    self.msg = msg
            else:
                # Use the class object instead of the instance so __init__ does
                # not depend on the object's state; e.g. the default thaw
                # method calls __init__ on an already instantiated object.
                cls = self.__class__
                if cls.__doc__ is not None:
                    self.msg = cls.__doc__
                else:
                    self.msg = cls.msg

        def __str__(self):
            return self.msg

    class InvalidJobHandleError(PackageCreatorError):
        """Raised when the job handle is invalid"""

    class BuildFailedError(PackageCreatorError):
        """Raised when the build failed"""

class TroveBuilder(object):
    """
    The class that handles the build of a trove.
    """

    _build_status_map = [
        (Constants.BUILD_STATUS_FAILED, "isFailed"),
        (Constants.BUILD_STATUS_COMMITTING, "isCommitting"),
        (Constants.BUILD_STATUS_COMMITTED, "isCommitted"),
        (Constants.BUILD_STATUS_QUEUED, "isQueued"),
        (Constants.BUILD_STATUS_RUNNING, "isRunning"),
        (Constants.BUILD_STATUS_BUILT, "isBuilt"),
        (Constants.BUILD_STATUS_BUILDING, "isBuilding"),
        (Constants.BUILD_STATUS_FINISHED, "isFinished"),
    ]

    msgRegexps = [re.compile('(umount|find).*: (Invalid argument|Permission denied|No such file or directory)'), re.compile('.*\[.*root\].*-.*Shutting down server'), re.compile('.*SocketAuth')]

    def __init__(self, rmakeCfg, callback = None):
        rmakecfg.RmakeConfiguration.loadPlugins()
        self.callback = callback
        self.buildConfig = rmakecfg.RmakeConfiguration.loadFromString(rmakeCfg)
        self.helper = self._createRmakeHelper()
        self.jobId = None

    def build(self, troveSpecs, commit = False):
        """
        Start a build.
        @param troveSpecs: A list of troves to build.
        @type troveSpecs: C{list} of (name, version, flavor) tuples
        @param commit: A flag that forces a commit at the end of the build
        (off by default)
        @type commit: C{bool}
        """
        assert(self.buildConfig.buildLabel)
        job = self.createBuildJob(troveSpecs)
        self.jobId = self.helper.buildJob(job, quiet = True)
        self.callback.notify_built(self, self.retrieveJob())
        if commit:
            self.commit()
        return self.jobId

    def createBuildJob(self, troveSpecs):
        return self.helper.createBuildJob(troveSpecs)

    def commit(self):
        """
        Commit a build
        """
        self._commit()
        return self.jobId

    def getBuildStatus(self):
        """Get build status.
        @return: one of the BUILD_STATUS_ constants
        @rtype: int
        @raise BuildFailedError: if the build failed
        """
        job = self.retrieveJob()
        return self.getBuildStatusForJob(job)

    def getBuildStatusForJob(self, job):
        statusCode, methodName = self._getJobStatus(job)
        if statusCode is None:
            raise Exception("Unknown status code")
        if statusCode == Constants.BUILD_STATUS_FAILED:
            errorMessage = job.failureReason.getShortError()
            raise Errors.BuildFailedError(errorMessage)

        rmkClient = self.helper.client

        message = rmkClient.getJobLogs(job.jobId)[-1][1]
        if methodName != 'isRunning':
            return self._returnStatus(statusCode, message)

        maxTimeStamp = ''
        maxMark = 0
        troves = list(job.iterTroves())
        for trove in troves:
            # From the trove log (dep resolver, installing chroot)
            troveLog = self.getTroveLog(job, trove)
            if troveLog:
                lastLog = troveLog[-1]
                if lastLog[0] > maxTimeStamp:
                    maxTimeStamp = lastLog[0]
                    message = lastLog[1]

            building = False
            mark = 0
            # From the build log
            try:
                building, logMessage, mark = rmkClient.getTroveBuildLog(
                    job.jobId, trove.getNameVersionFlavor())
            except (ValueError, RuntimeError):
                # HACK: rMake periodically crashes here, then
                # crashes again trying to serialize the exception,
                # so who knows what the error is -- but it is
                # apparently harmless.
                pass
            if not building or mark <= maxMark:
                continue
            # Found a newer message
            maxMark = mark
            if "subscribeToBuild" in logMessage:
                logLines = logMessage.splitlines()
                # only filter lines that we might actually
                # display
                message = logLines.pop()
                # this assumes there's at least 1 good line
                # but the odds that every line in the log is
                # going to be a bogus message is nil
                while self._badMessage(message):
                    message = logLines.pop()
            # XXX misa when moving to rmake3: we found a trove with a message
            # that is newer than what we had. The previous generation of this
            # code was moving on, possibly finding other messages in other
            # troves, but that seems pointless.
            break
        return self._returnStatus(statusCode, message)

    def getBuildLogs(self):
        job = self.retrieveJob()
        out = StringIO()
        # just ask rMake. this output is subject to change at rMake's whim
        # XXX the rmake query module is not public, so this must be changed
        rmakeQuery.displayJobInfo(self.helper, jobId = job.jobId,
                displayTroves = True, displayDetails = True, showLogs = True,
                showBuildLogs = True, showTracebacks = True, out = out)
        return out.getvalue()

    def getTroveLog(self, job, trove):
        troveTup = trove.getNameVersionFlavor(True)
        mark = 0
        numFailures = 0
        log = []
        while True:
            try:
                new = self.helper.client.getTroveLogs(job.jobId, troveTup, mark)
            except (KeyError, RuntimeError):
                # HACK: rMake sometimes decides the trove doesn't exist, which
                # throws KeyError, which doesn't get marshalled properly and
                # thus appears as a RuntimeError.
                numFailures += 1
                if numFailures > 10:
                    # Maybe something is actually wrong.
                    raise
                break
            numFailures = 0
            if not new:
                break

            log += new
            mark += len(new)

        return log

    def retrieveJob(self):
        assert(self.jobId is not None)
        try:
            job = self.helper.getJob(self.jobId)
        except rmakeErrors.JobNotFound:
            util.rethrow(Errors.InvalidJobHandleError)
        return job

    @classmethod
    def _badMessage(klass, msg):
        for regexp in klass.msgRegexps:
            if regexp.match(msg):
                return True
        return False

    @classmethod
    def _returnStatus(cls, statusCode, message):
        isDone = statusCode in Constants.isDone
        return (isDone, statusCode, "%s: %s" %
            (Constants.BUILD_STATUS_STRINGS[statusCode], message))

    @classmethod
    def _getJobStatus(cls, job):
        for statusCode, methodName in cls._build_status_map:
            method = getattr(job, methodName)
            if method():
                return statusCode, methodName
        return None, None

    def _createRmakeHelper(self):
        return rmakeHelper.rMakeHelper(buildConfig = self.buildConfig,
            configureClient = True)

    def _commit(self):
        job = self.retrieveJob()
        self._commit_action(job)
        self.callback.notify_committed(self, self.retrieveJob())

    def _commit_action(self, job):
        self.helper.commitJobs([ job.jobId ], waitForJob = True)


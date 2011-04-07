#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

import logging
log = logging.getLogger('rmake3.handler')

import os
import time

from mint.rmake3_package_creator import constants
from rmake3.core import handler as rmk_handler

from twisted.internet import defer, protocol, reactor
from twisted.web import client as tw_client

from rpath_repeater.utils.reporting import ReportingMixIn
from rpath_repeater.utils.xmlutils import XML

class BaseHandler(rmk_handler.JobHandler, ReportingMixIn):
    firstState = 'run'
    ReportingXmlTag = "system"

    def setup(self):
        self.data = self.getData()
        self.resultsLocation = self.data.thaw().resultsLocation

    def jobUpdateCallback(self, task):
        status = task.status.thaw()
        if status.final:
            return
        self.setStatus(status)

    def _handleTask(self, task):
        """
        Handle responses for a task execution
        """
        d = self.waitForTask(task)
        d.addCallbacks(self._handleTaskCallback, self._handleTaskError)
        return d

    def _handleTaskCallback(self, task):
        if task.status.failed:
            self.setStatus(task.status.thaw())
            self.postFailure()
        else:
            self._handleTaskComplete(task)
        return 'done'

    def _handleTaskComplete(self, task):
        response = task.task_data.getObject()
        self.job.data = response.thaw().data
        self.setStatus(constants.Codes.OK, "Done")
        self.postResults()

    def _handleTaskError(self, reason):
        """
        Error callback that gets invoked if rmake failed to handle the job.
        Clean errors from the repeater do not see this function.
        """
        d = self.failJob(reason)
        self.postFailure()
        return d

    def getResultsLocation(self):
        return (self.resultsLocation.host or 'localhost',
            int(self.resultsLocation.port or 80),
            self.resultsLocation.path)

class HandlerCommitSource(BaseHandler):
    jobType = constants.NS_JOB_COMMIT_SOURCE

    def run(self):
        self.setStatus(constants.Codes.MSG_START, "Waiting for processing")
        task = self.newTask(constants.NS_TASK_COMMIT_SOURCE,
            constants.NS_TASK_COMMIT_SOURCE, self.data)
        self.watchTask(task, self.jobUpdateCallback)
        return self._handleTask(task)

    def postResults(self, *args, **kwargs):
        return ReportingMixIn.postResults(self, method="POST")

class HandlerBuildSource(BaseHandler):
    jobType = constants.NS_JOB_BUILD_SOURCE

    def run(self):
        self.setStatus(constants.Codes.MSG_START, "Waiting for processing")
        task = self.newTask(constants.NS_TASK_BUILD_SOURCE,
            constants.NS_TASK_BUILD_SOURCE, self.data)
        self.watchTask(task, self.jobUpdateCallback)
        return self._handleTask(task)

    def postResults(self, *args, **kwargs):
        return # XXX until we figure out the results reporting
        return ReportingMixIn.postResults(self, method="POST")

class HandlerDownloadFiles(BaseHandler):
    jobType = constants.NS_JOB_DOWNLOAD_FILES
    ReportingXmlTag = 'package_version_url'

    def run(self):
        self.setStatus(constants.Codes.MSG_START, "Waiting for processing")
        self.params = self.getData().thaw()
        self.resultsLocation = self.params.resultsLocation

        def downloadCallback(ignored):
            pass

        data = self.data.thaw()
        dlist = []
        for downloadFile in data.urlList:
            deferred = defer.Deferred()
            deferred.addBoth(downloadCallback)
            url = downloadFile.url
            DownloadAgent(url, downloadFile.path,
                self.progressCallbackFactory(os.path.basename(url)), deferred)
            dlist.append(deferred)
        deferred = defer.DeferredList(dlist)
        @deferred.addBoth
        def cb(resultList):
            self.job.data = "Blah"
            self.setStatus(constants.Codes.OK, "Download finished")
            urls = [
                XML.Element('package_version_url',
                    XML.Text('url', x.url),
                    XML.Text('file_path', x.path),
                    XML.Text('file_size', os.stat(x.path).st_size)
                ) for x in data.urlList ]
            elt = XML.Element('package_version_urls', *urls)
            self.postResults(elt)
        return deferred

    def progressCallbackFactory(self, fileName):
        def cb(code, msg):
            msg = "%s: %s" % (fileName, msg)
            self.setStatus(constants.Codes.MSG_STATUS, msg)
        return cb

class DownloadAgent(object):
    USER_AGENT = "Downloader/1.0"
    def __init__(self, url, destination, progressCallback, finished):
        agent = tw_client.Agent(reactor)
        defr = agent.request("GET",
            url,
            tw_client.Headers({
                'User-Agent' : [ self.USER_AGENT ],
            }),
            None)

        @defr.addCallback
        def cb(response):
            response.deliverBody(BodyConsumer(file(destination, "w"),
                response.length, finished, progressCallback))
            return finished

class BodyConsumer(protocol.Protocol):
    PROGRESS_TIMEOUT = 2 # Do not send progress more often than this timeout
    def __init__(self, result, length, finished, progressCallback):
        self.finished = finished
        self.bytesTotal = length
        self.bytesDownloaded = 0
        self.result = result
        self.nextProgressCall = 0
        self.progressCallback = progressCallback

    def dataReceived(self, bytes):
        if self.bytesDownloaded >= self.bytesTotal:
            return
        self.result.write(bytes)
        self.bytesDownloaded += len(bytes)

        now = time.time()
        if now > self.nextProgressCall:
            self.nextProgressCall = now + self.PROGRESS_TIMEOUT
            msg = "Downloaded %s/%s" % (self.bytesDownloaded, self.bytesTotal)
            self.progressCallback(constants.Codes.MSG_STATUS, msg)

    def connectionLost(self, reason):
        self.result.close()
        if reason.type == tw_client.ResponseDone:
            code = constants.Codes.OK
            msg = "Download done"
        else:
            code = constants.Codes.ERR_GENERIC
            msg = "Download failed: %s" % (reason.getErrorMessage(), )
        self.progressCallback(code, msg)
        self.finished.callback(None)

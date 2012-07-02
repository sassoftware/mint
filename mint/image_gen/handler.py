#
# Copyright (c) rPath, Inc.
#

import logging
import tempfile
from conary.lib import timeutil
from lxml import builder
from lxml import etree
from rmake3.core import handler as rmk_handler
from rmake3.core import types as rmk_types
from rmake3.lib import logger
from rmake3.lib import structlog
from twisted.internet import defer
from twisted.web import client as tw_web_client
from twisted.web import http_headers

from mint import jobstatus

log = logging.getLogger(__name__)


class BaseImageHandler(rmk_handler.JobHandler):

    imageBase = None
    imageToken = None
    log = None
    slotType = 'image_gen'

    def _mirrorTaskStatus(self, task):
        """Copy task status to job status when task is updated."""
        if task.status.final:
            level = logging.ERROR if task.status.failed else logging.INFO
            detail = '\n' + task.status.detail if task.status.detail else ''
            self.log.log(level, "Job result: %s %s%s", task.status.code,
                    task.status.text, detail)
            path = self.dispatcher.getLogPath(task.job_uuid, task.task_uuid)
            try:
                fobj = open(path, 'rb')
            except IOError, err:
                pass
            else:
                self._reformatLog(fobj)
        self.setStatus(task.status)

    def setStatus(self, codeOrStatus, text=None, detail=None):
        """Set job status, and upload same to mint database."""
        if isinstance(codeOrStatus, rmk_types.FrozenJobStatus):
            status = codeOrStatus.thaw()
        elif isinstance(codeOrStatus, rmk_types.JobStatus):
            status = codeOrStatus.freeze().thaw()
        else:
            assert text is not None
            status = rmk_types.JobStatus(codeOrStatus, text, detail)
        if self.log:
            self.log.info("Status: %s %s%s", status.code, status.text,
                    ('\n' + status.detail if status.detail else ''))
        # Always send status to mint before updating rMake's own database. This
        # prevents a race with job-cleanup, which will shoot any builds which
        # rMake thinks are done but mint thinks are still running.
        self._uploadStatus(status)
        return rmk_handler.JobHandler.setStatus(self, status)

    def _translateCode(self, rmakeCode):
        return jobstatus.FAILED

    def _uploadStatus(self, status):
        E = builder.ElementMaker()
        code = self._translateCode(status.code)
        root = E.imageStatus(
                E.code(str(code)),
                E.message(status.text),
                )
        self._upload('PUT', 'status', etree.tostring(root))

    def _uploadLog(self, data):
        self._upload('POST', 'buildLog', data, 'text/plain')

    def _upload(self, method, path, body, contentType='application/xml'):
        url = self.imageBase + path
        headers = http_headers.Headers()
        headers.addRawHeader('Content-Type', contentType)
        headers.addRawHeader('X-Rbuilder-Outputtoken', self.imageToken)
        client = tw_web_client.Agent(self.clock)
        if hasattr(body, 'read'):
            producer = FileBodyProducer(body)
        else:
            producer = StringProducer(body)
        d = client.request(method, url, headers, producer)
        def cb_result(result):
            if 200 <= result.code < 300:
                log.debug("Status upload successful: %s %s",
                        result.code, result.phrase)
            else:
                log.error("Status upload failed: %s %s",
                        result.code, result.phrase)
        def eb_unwrap_error(result):
            # Unwrap some failure types that Agent might throw to get the
            # original traceback.
            if (not hasattr(result.value, 'reasons')
                    or not result.value.reasons):
                return result
            for reason in result.value.reasons:
                logger.logFailure(reason, "Error uploading job status:")
        d.addCallbacks(cb_result, eb_unwrap_error)
        d.addErrback(logger.logFailure, "Error uploading job status:")

    def _reformatLog(self, inFile):
        outFile = tempfile.NamedTemporaryFile()
        formatter = timeutil.ISOFormatter(
                '[%(asctime)s] [%(levelname)s] (%(name)s) %(message)s')
        handler = logging.StreamHandler(outFile)
        handler.setFormatter(formatter)
        parser = structlog.StructuredLogParser(inFile, asRecords=True)
        for record in parser:
            handler.emit(record)
        handler.close()
        outFile.flush()
        outFile.seek(0)
        self._uploadLog(outFile)


class StringProducer(object):

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

    def stopProducing(self):
        pass


# Copied from Twisted; replace me after next Twisted upgrade
from zope.interface import implements
from twisted.web.iweb import UNKNOWN_LENGTH, IBodyProducer
import os
from twisted.internet import task
class FileBodyProducer(object):
    """
    L{FileBodyProducer} produces bytes from an input file object incrementally
    and writes them to a consumer.

    Since file-like objects cannot be read from in an event-driven manner,
    L{FileBodyProducer} uses a L{Cooperator} instance to schedule reads from
    the file.  This process is also paused and resumed based on notifications
    from the L{IConsumer} provider being written to.

    The file is closed after it has been read, or if the producer is stopped
    early.

    @ivar _inputFile: Any file-like object, bytes read from which will be
        written to a consumer.

    @ivar _cooperate: A method like L{Cooperator.cooperate} which is used to
        schedule all reads.

    @ivar _readSize: The number of bytes to read from C{_inputFile} at a time.
    """
    implements(IBodyProducer)

    # Python 2.4 doesn't have these symbolic constants
    _SEEK_SET = getattr(os, 'SEEK_SET', 0)
    _SEEK_END = getattr(os, 'SEEK_END', 2)

    def __init__(self, inputFile, cooperator=task, readSize=2 ** 16):
        self._inputFile = inputFile
        self._cooperate = cooperator.cooperate
        self._readSize = readSize
        self.length = self._determineLength(inputFile)


    def _determineLength(self, fObj):
        """
        Determine how many bytes can be read out of C{fObj} (assuming it is not
        modified from this point on).  If the determination cannot be made,
        return C{UNKNOWN_LENGTH}.
        """
        try:
            seek = fObj.seek
            tell = fObj.tell
        except AttributeError:
            return UNKNOWN_LENGTH
        originalPosition = tell()
        seek(0, self._SEEK_END)
        end = tell()
        seek(originalPosition, self._SEEK_SET)
        return end - originalPosition


    def stopProducing(self):
        """
        Permanently stop writing bytes from the file to the consumer by
        stopping the underlying L{CooperativeTask}.
        """
        self._inputFile.close()
        self._task.stop()


    def startProducing(self, consumer):
        """
        Start a cooperative task which will read bytes from the input file and
        write them to C{consumer}.  Return a L{Deferred} which fires after all
        bytes have been written.

        @param consumer: Any L{IConsumer} provider
        """
        self._task = self._cooperate(self._writeloop(consumer))
        d = self._task.whenDone()
        def maybeStopped(reason):
            # IBodyProducer.startProducing's Deferred isn't support to fire if
            # stopProducing is called.
            reason.trap(task.TaskStopped)
            return defer.Deferred()
        d.addCallbacks(lambda ignored: None, maybeStopped)
        return d


    def _writeloop(self, consumer):
        """
        Return an iterator which reads one chunk of bytes from the input file
        and writes them to the consumer for each time it is iterated.
        """
        while True:
            bytes = self._inputFile.read(self._readSize)
            if not bytes:
                self._inputFile.close()
                break
            consumer.write(bytes)
            yield None


    def pauseProducing(self):
        """
        Temporarily suspend copying bytes from the input file to the consumer
        by pausing the L{CooperativeTask} which drives that activity.
        """
        self._task.pause()


    def resumeProducing(self):
        """
        Undo the effects of a previous C{pauseProducing} and resume copying
        bytes to the consumer by resuming the L{CooperativeTask} which drives
        the write activity.
        """
        self._task.resume()

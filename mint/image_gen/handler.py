#
# Copyright (c) 2011 rPath, Inc.
#

import logging
from lxml import builder
from lxml import etree
from rmake3.core import handler as rmk_handler
from rmake3.core import types as rmk_types
from rmake3.lib import logger
from twisted.internet import defer
from twisted.web import client as tw_web_client
from twisted.web import http_headers

from mint import jobstatus

log = logging.getLogger(__name__)


class BaseImageHandler(rmk_handler.JobHandler):

    imageBase = None
    imageToken = None
    log = None

    def _mirrorTaskStatus(self, task):
        """Copy task status to job status when task is updated."""
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


class StringProducer(object):

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

    def stopProducing(self):
        pass

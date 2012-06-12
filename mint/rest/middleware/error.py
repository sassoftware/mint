#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import logging
import traceback

from restlib import response

from mint import logerror
from mint import mint_error
from mint.rest.api import models
from mint.rest.modellib import converter

log = logging.getLogger(__name__)


class ErrorCallback(object):
    def __init__(self, controller):
        self.controller = controller
        
    def processException(self, request, excClass, exception, tb):
        message = '%s: %s' % (excClass.__name__, exception)

        if hasattr(exception, 'status'):
            status = exception.status
        else:
            status = 500
            self.logError(request, excClass, exception, tb, doEmail=True)

        # Only send the traceback information if it's an unintentional
        # exception (i.e. a 500)
        if status == 500:
            tbString = 'Traceback:\n' + ''.join(traceback.format_tb(tb))
            text = [message + '\n', tbString]
        else:
            tbString = None
            text = [message + '\n']
        isFlash = 'HTTP_X_FLASH_VERSION' in request.headers
        if not getattr(request, 'contentType', None):
            request.contentType = 'text/xml'
            request.responseType = 'xml'
        if isFlash or request.contentType != 'text/plain':
        # for text/plain, just print out the traceback in the easiest to read
        # format.
            code = status
            if isFlash:
                # flash ignores all data sent with a non-200 error
                status = 200
            error = models.Fault(code=code, message=message, 
                                 traceback=tbString)
            text = converter.toText(request.responseType, error,
                                    self.controller, request)
        return response.Response(text, content_type=request.contentType,
                                 status=status)

    def logError(self, request, e_type, e_value, e_tb, doEmail=True):
        info = {
                'uri'               : request.thisUrl,
                'path'              : request.path,
                'method'            : request.method,
                'headers_in'        : request.headers,
                'request_params'    : request.GET,
                'post_params'       : request.POST,
                'remote'            : '[%s]:%d' % request.remote[:2],
                }
        try:
            logerror.logErrorAndEmail(self.controller.cfg, e_type, e_value,
                    e_tb, 'API call', info, doEmail=doEmail)
        except mint_error.MailError, err:
            log.error("Error sending mail: %s", str(err))

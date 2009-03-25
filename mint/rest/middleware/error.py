#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import traceback

from restlib import response

from mint import logerror
from mint.rest.api import models
from mint.rest.modellib import converter

class ErrorCallback(object):
    def __init__(self, controller):
        self.controller = controller
        
    def processException(self, request, excClass, exception, tb):
        message = '%s: %s' % (excClass.__name__, exception)
        if hasattr(exception, 'status'):
            status = exception.status
        else:
            status = 500
            # TODO: Pass contextual info like request params
            logerror.logErrorAndEmail(self.controller.cfg,
                    excClass, exception, tb, 'API call', {})

        # Only send the traceback information if it's an unintentional
        # exception (i.e. a 500)
        if status == 500:
            tbString = 'Traceback:\n' + ''.join(traceback.format_tb(tb))
            text = [message + '\n', tbString]
        else:
            tbString = None
            text = [message + '\n']
        isFlash = 'HTTP_X_FLASH_VERSION' in request.headers
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
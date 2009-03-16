#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import traceback

from restlib import response

from mint.rest.api import models
from mint.rest.modellib import converter

class ErrorCallback(object):
    def __init__(self, controller):
        self.controller = controller
        
    def processException(self, request, excClass, exception, tb):
        message = '%s: %s' % (excClass.__name__, exception)
        tbString = 'Traceback:\n' + ''.join(traceback.format_tb(tb))
        if hasattr(exception, 'status'):
            status = exception.status
        else:
            status = 500
        if request.contentType == 'text/plain':
            # just print out the traceback in the easiest to read
            # format.
            text = [message, tbString]
        else:
            code = status
            if 'HTTP_X_FLASH_VERSION' in request.headers:
                status = 200
            error = models.Error(code=code, message=message, 
                                 traceback=tbString)
            text = converter.toText(request.responseType, error,
                                    self.controller, request)
        return response.Response(text, content_type=request.contentType,
                                 status=status)

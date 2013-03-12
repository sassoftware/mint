#
# Copyright (c) 2011 rPath, Inc.
#

try:
    # The mod_python version is more efficient, so try importing it first.
    from mod_python.util import parse_qsl # pyflakes=ignore
except ImportError:
    from cgi import parse_qsl # pyflakes=ignore

import logging
import sys
import time
import traceback

from django import http
from django.http import HttpResponse

from mint import logerror
from mint import mint_error
from mint.django_rest.rbuilder import models


def handler404(request, **kwargs):
    fault = models.Fault()
    fault.code = 404
    fault.message = "URL %s not found." % request.path
    fault.traceback = None
    response = HttpResponse(status=404, content_type='text/xml')
    response.content = fault.to_xml(request)
    return response

def handler500(request, **kwargs):
    return handleException(request)

def handleException(request, exception=None, doEmail=True, doTraceback=True):
    ei = sys.exc_info()
    if doTraceback:
        tb = ''.join(traceback.format_tb(ei[2]))
    else:
        tb = None
    msg = str(ei[1])
    logError(request, ei[0], ei[1], ei[2], doEmail=doEmail)

    code = getattr(ei[1], 'status', 500)
    fault = models.Fault(code=code, message=msg, traceback=tb)
    response = HttpResponse(status=code, content_type='text/xml')
    response.content = fault.to_xml(request)

    return response

log = logging.getLogger(__name__)

def logError(request, e_type, e_value, e_tb, doEmail=True):
    info = {
            'path'              : request.path,
            'method'            : request.method,
            'headers_in'        : request.META,
            'request_params'    : request.GET,
            'is_secure'         : request.is_secure,
            }
    if request.raw_post_data:
        info.update(raw_post_data = request.raw_post_data)
    try:
        cfg = getattr(request, "cfg", None)
        logerror.logErrorAndEmail(cfg, e_type, e_value,
                e_tb, 'API call (django handler)', info, doEmail=doEmail)
    except mint_error.MailError, err:
        log.error("Error sending mail: %s", str(err))



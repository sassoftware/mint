#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

try:
    # The mod_python version is more efficient, so try importing it first.
    from mod_python.util import parse_qsl # pyflakes=ignore
except ImportError:
    from cgi import parse_qsl # pyflakes=ignore

import logging
import sys
import traceback

from django import http
from django.core.handlers import modpython
from django.http import HttpResponse

from mint import logerror
from mint import mint_error
from mint.django_rest.rbuilder import models


class MintDjangoRequest(modpython.ModPythonRequest):

    def __init__(self, req):
        modpython.ModPythonRequest.__init__(self, req)

        if req.args:
            args = req.args
        else:
            args = ''
        questionParams = parse_qsl(args)

        if ';' in self.path:
            self.path, semiColonParams = self.path.split(';', 1)
            self.path_info = self.path
            semiColonParams = parse_qsl(semiColonParams)
        else:
            semiColonParams = []

        params = questionParams + semiColonParams
        self.params = ['%s=%s' % (k, v) for k, v in params]
        self.params = ';' + ';'.join(self.params)

    def _get_get(self):
        if not hasattr(self, '_get'):
            self._get = http.QueryDict(self.params, encoding=self._encoding)
        return self._get

    def _set_get(self, *args, **kwargs):
        return modpython.ModPythonRequest._set_get(self, *args, **kwargs)

    GET = property(_get_get, _set_get)

class MintDjangoHandler(modpython.ModPythonHandler):
    request_class = MintDjangoRequest

def handler(req):
    # mod_python hooks into this function.
    return MintDjangoHandler()(req)    

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

def handleException(request, exception=None):
    ei = sys.exc_info()
    tb = ''.join(traceback.format_tb(ei[2]))
    msg = str(ei[1])
    logError(request, ei[0], ei[1], ei[2])

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
        logerror.logErrorAndEmail(request.cfg, e_type, e_value,
                e_tb, 'API call (django handler)', info, doEmail=doEmail)
    except mint_error.MailError, err:
        log.error("Error sending mail: %s", str(err))



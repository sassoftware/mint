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

from django import http
from django.core.handlers import modpython

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
        self.params = ';'.join(self.params)

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

#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django import http
from django.core.handlers import modpython

class MintDjangoRequest(modpython.ModPythonRequest):

    def __init__(self, req):
        modpython.ModPythonRequest.__init__(self, req)
        if ':' in self.path:
            self.path, self.params = self.path.split(':')
            self.path_info = self.path
        else:
            self.params = None


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

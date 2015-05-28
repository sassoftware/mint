#!/usr/bin/python
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import __builtin__
import sys
import os
from testrunner import suite

os.environ['DJANGO_SETTINGS_MODULE'] = 'mint.django_rest.settings_local'

from django import http
# Django will mistakengly set this to None when running under mod_python as we
# do in our testsuite.
if http.parse_qsl is None:
    from cgi import parse_qsl
    http.parse_qsl = parse_qsl

def enforceBuiltin(result):
    failure = False
    if isinstance(result, (list, tuple)):
        for item in result:
            failure = failure or enforceBuiltin(item)
    elif isinstance(result, dict):
        for item in result.items():
            failure = failure or enforceBuiltin(item)
    failure =  failure or (result.__class__.__name__ \
                           not in __builtin__.__dict__)
    return failure


def filteredCall(self, *args, **kwargs):
    from mint.client import VERSION_STRING
    args = [VERSION_STRING] + list(args)
    isException, result = self._server.callWrapper(self._name,
                                                   self._authToken, args)

    if not isException:
        if enforceBuiltin(result):
            # if the return type appears to be correct, check the types
            # some items get cast to look like built-ins for str()
            # an extremely common example is sql result rows.
            raise AssertionError('XML cannot marshall return value: %s '
                                 'for method %s' % (str(result), self._name))
        return result
    else:
        self.handleError(result)

# ensure shim client errors on types that can't be sent over xml-rpc
from mint import shimclient
shimclient._ShimMethod.__call__ = filteredCall

class Suite(suite.TestSuite):
    testsuite_module = sys.modules[__name__]

    def getCoverageDirs(self, handler, environ):
        import mint
        return [mint]

    def main(self, *args, **kwargs):
        from django.test import utils
        utils.setup_test_environment()
        try:
            return super(Suite, self).main(*args, **kwargs)
        finally:
            # Need to delete the database used by django tests.
            from django.conf import settings
            if settings.DATABASE_ENGINE == 'sqlite3':
                try:
                    os.unlink(settings.TEST_DATABASE_NAME)
                except OSError:
                    pass


if __name__ == '__main__':
    Suite().run()

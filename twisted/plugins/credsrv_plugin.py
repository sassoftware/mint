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


import errno
import os
from twisted.application import internet as ta_internet
from twisted.application import service
from twisted.plugin import IPlugin
from twisted.python import usage
from zope.interface import implements

from mint.scripts.cred_server import CredServerFactory


class Options(usage.Options):
    optParameters = [
            ('keydir', 'k', '/srv/rbuilder/data/credstore', 'Path to credential keystore', str),
            ('socket', 's', '/tmp/mintcred.sock', 'Path to UNIX socket', str),
            ]


class ServiceMaker(object):
    implements(service.IServiceMaker, IPlugin)
    tapname = 'credsrv'
    description = "Performs authentication checks for local services."
    options = Options

    def makeService(self, options):
        path = options['socket']
        try:
            os.unlink(path)
        except OSError, err:
            if err.errno != errno.ENOENT:
                raise
        factory = CredServerFactory(options['keydir'], init=True)
        return ta_internet.UNIXServer(path, factory, mode=0660)


serviceMaker = ServiceMaker()

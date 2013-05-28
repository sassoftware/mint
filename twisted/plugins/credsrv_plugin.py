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
import grp
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
            ('gid', 'g', None, 'Group that should own the UNIX socket', str),
            ]


class UNIXServer(ta_internet.UNIXServer):

    def __init__(self, *args, **kwargs):
        self.gid = kwargs.pop('gid', None)
        ta_internet.UNIXServer.__init__(self, *args, **kwargs)

    def _getPort(self):
        port = ta_internet.UNIXServer._getPort(self)
        if self.gid is not None:
            try:
                gid = int(self.gid)
            except ValueError:
                gid = grp.getgrnam(self.gid).gr_gid
            os.chown(port.port, os.getuid(), gid)
        return port


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
        return UNIXServer(path, factory, mode=0660, gid=options['gid'])


serviceMaker = ServiceMaker()

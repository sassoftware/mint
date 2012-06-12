#
# Copyright (c) 2011 rPath, Inc.
#


import errno
import os
from twisted.application import internet as ta_internet
from twisted.application import service
from twisted.plugin import IPlugin
from twisted.python import usage
from zope.interface import implements

from mint.scripts.auth_server import AuthServerFactory


class Options(usage.Options):
    optParameters = [
            ('socket', 's', '/tmp/mintauth.sock', 'Path to UNIX socket', str),
            ]


class ServiceMaker(object):
    implements(service.IServiceMaker, IPlugin)
    tapname = 'authsrv'
    description = "Performs authentication checks for local services."
    options = Options

    def makeService(self, options):
        path = options['socket']
        try:
            os.unlink(path)
        except OSError, err:
            if err.errno != errno.ENOENT:
                raise
        factory = AuthServerFactory()
        return ta_internet.UNIXServer(path, factory)


serviceMaker = ServiceMaker()

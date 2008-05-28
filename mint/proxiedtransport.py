#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#

import httplib
import urllib
import xmlrpclib

class ProxiedTransport(xmlrpclib.Transport):
    """
    Transport class for contacting rUS through a proxy
    """
    def __init__(self, proxy):
        splitUrl = urllib.splittype(proxy)
        self.protocol = splitUrl[0]
        self.proxy = splitUrl[1].lstrip('/')

    def make_connection(self, host):
        self.realHost = host
        if self.protocol == 'https':
            h = httplib.HTTPS(self.proxy)
        else:
            h = httplib.HTTP(self.proxy)
        return h

    def send_request(self, connection, handler, request_body):
        connection.putrequest('POST', 'https://%s%s' % (self.realHost,
                                                         handler))

    def send_host(self, connection, host):
        connection.putheader('Host', self.realHost)

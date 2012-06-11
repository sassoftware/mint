#
# Copyright (c) 2005-2009 rPath, Inc.
#
# All rights reserved
#

import urllib
from conary.repository import transport

class ProxiedTransport(transport.Transport):
    """
    Transport class for contacting rUS through a proxy
    """
    def __init__(self, *args, **kw):
        # Override transport.XMLOpener with our own that does the right thing
        # with the selector.
        transport.XMLOpener = ProxiedXMLOpener
        return transport.Transport.__init__(self, *args, **kw)

    def parse_response(self, *args, **kw):
        resp = transport.Transport.parse_response(self, *args, **kw)
        # The request method on transport.Transport expects this return
        # result.
        return [[resp,]]

    def request(self, *args, **kw):
        resp = transport.Transport.request(self, *args, **kw)
        # Return just the value.
        return resp[0][1]

class ProxiedXMLOpener(transport.XMLOpener):
    def createConnection(self, *args, **kw):
        h, urlstr, selector, headers = transport.URLOpener.createConnection(self, *args, **kw)
        # transport.URLOpener.createConnection leaves selector as the full
        # protocol, host, path string.  That does not always work with proxy,
        # so parse out just the path.
        proto, rest = urllib.splittype(selector)
        host, rest = urllib.splithost(rest)
        return h, urlstr, rest, headers

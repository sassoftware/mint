#
# Copyright (c) 2011 rPath, Inc.
#

import urllib
from conary.repository import transport

class ProxiedTransport(transport.Transport):
    """
    Transport class for contacting rUS through a proxy
    """

    def request(self, *args, **kw):
        resp = transport.Transport.request(self, *args, **kw)
        # Return just the value.
        return resp[0]

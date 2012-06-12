#
# Copyright (c) rPath, Inc.
#

from conary.lib.http import opener
from conary.repository import transport


# conary.repository.transport.XMLOpener is not suitable because it will try to
# use conary:// proxies.

class VanillaXmlrpcOpener(opener.URLOpener):
    contentType = 'text/xml'


class ProxiedTransport(transport.Transport):
    """
    Transport class for contacting rUS through a proxy
    """

    openerFactory = VanillaXmlrpcOpener

    def request(self, *args, **kw):
        resp = transport.Transport.request(self, *args, **kw)
        # Return just the value.
        return resp[0]

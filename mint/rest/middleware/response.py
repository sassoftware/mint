#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import os
from restlib import response

from conary.lib import util

class XmlStringResponse(response.Response):
    def __init__(self, *args, **kw):
        response.Response.__init__(self, *args, **kw)
        self.headers['content-type'] = 'application/xml'
        self.headers['Cache-Control'] = 'no-store'

class SeekableStreamResponse(response.Response):
    """
    Stream a (seekable) file back
    """
    def __init__(self, content, content_type="application/octet-stream", **kw):
        response.Response.__init__(self, content=content,
            content_type=content_type, **kw)

    class ChunkedStream(object):
        CHUNK_SIZE = 16384
        def __init__(self, stream):
            self.stream = stream

        def __iter__(self):
            while 1:
                buf = self.stream.read(self.CHUNK_SIZE)
                if not buf:
                    break
                yield buf

    def get(self):
        return self.ChunkedStream(self.response)
    content = property(get)

    def getLength(self):
        self.response.seek(0, 2)
        contentLength = self.response.tell()
        self.response.seek(0, 0)
        return contentLength

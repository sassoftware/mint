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

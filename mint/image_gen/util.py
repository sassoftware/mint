#
# Copyright (c) 2011 rPath, Inc.
#

import time


class FileWithProgress(object):

    interval = 2

    def __init__(self, fobj, callback):
        self.fobj = fobj
        self.callback = callback
        self.total = 0
        self.last = 0

    _SIGIL = object()
    def read(self, size=_SIGIL):
        if size is self._SIGIL:
            data = self.fobj.read()
        else:
            data = self.fobj.read(size)
        self.total += len(data)

        now = time.time()
        if now - self.last >= self.interval:
            self.last = now
            self.callback(self.total)

        return data

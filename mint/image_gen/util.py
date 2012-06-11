#
# Copyright (c) 2011 rPath, Inc.
#

import logging
import time
from conary.lib.log import FORMATS


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


class Accumulator(object):

    maxBytes = 4096
    maxTime = 4

    def __init__(self, clock, callback):
        self.clock = clock
        self.callback = callback
        self.buffer = ''
        self.timeoutCall = None

    def append(self, data):
        assert isinstance(data, bytes)
        self.buffer += data
        if len(self.buffer) > self.maxBytes:
            self.flush()
        elif not self.timeoutCall:
            self.timeoutCall = self.clock.callLater(self.maxTime, self.flush)

    def flush(self):
        if self.timeoutCall:
            if self.timeoutCall.active():
                self.timeoutCall.cancel()
            self.timeoutCall = None
        data, self.buffer = self.buffer, ''
        self.callback(data)


class LogSender(logging.Handler):

    def __init__(self, clock, callback):
        logging.Handler.__init__(self)
        self.accumulator = Accumulator(clock, callback)

    def close(self):
        self.flush()

    def flush(self):
        self.accumulator.flush()

    def emit(self, record):
        data = self.format(record)
        if isinstance(data, unicode):
            data = data.encode('utf8')
        self.append(data + '\n')

    def append(self, data):
        self.accumulator.append(data)


def getLogSender(clock, callback, name, level=logging.NOTSET):
    formatter = FORMATS['apache']
    handler = LogSender(clock, callback)
    handler.setFormatter(formatter)
    log = logging.Logger(name)
    log.addHandler(handler)
    log.setLevel(level)
    return log

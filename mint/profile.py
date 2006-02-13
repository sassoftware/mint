#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#

import os
import time

START_MARKER = '>>'
STOP_MARKER  = '<<'

HTML_TAG = 'HTML'
RPC_TAG = 'RPC'

class Profile(object):
    def __init__(self, logFile = None):
        self.times = {}
        if logFile:
            self.logFile = open(logFile, "a")

        self.nestcount = 0

    def __del__(self):
        self.logFile.close()

    def write(self, formatString, *args):
        if not self.logFile:
            return
        if not formatString.endswith('\n'):
            formatString += '\n'
        self.logFile.write('%.3f|%.2f|%d|%d|' % (time.time(), os.getloadavg()[0],\
            os.getpid(), self.nestcount) + (formatString % args))
        self.logFile.flush()

    def start(self, type, tag):
        self.nestcount += 1
        if tag:
            self.times[tag] = time.time()
            self.write('%s|%s' % ((START_MARKER + type), tag))

    def stop(self, type, tag):
        if tag and self.times[tag]:
            elapsed = ((time.time() - self.times[tag]) * 1000)
            self.write('%s|%s|%d' % ((STOP_MARKER + type), tag, elapsed))
        self.nestcount -= 1
        del self.times[tag]

    def startXml(self, method):
        self.start(RPC_TAG, method)

    def stopXml(self, method):
        self.stop(RPC_TAG, method)

    def startHtml(self, uri):
        self.start(HTML_TAG, uri)

    def stopHtml(self, uri):
        self.stop(HTML_TAG, uri)


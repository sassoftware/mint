#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#

import os
import time

class Profile(object):
    def __init__(self, logFile = None):
        if logFile:
            self.logFile = open(logFile, "a")

    def __del__(self):
        self.logFile.close()

    def write(self, formatString, *args):
        if not self.logFile:
            return
        if not formatString.endswith('\n'):
            formatString += '\n'
        self.logFile.write(time.ctime(time.time()) + " (pid: %d): " % \
                           os.getpid() + formatString % args)
        self.logFile.flush()

    def startXml(self, method):
        self.xmlStartTime = time.time()
        self.write("Starting XMLRPC request: %s", method)

    def stopXml(self, method):
        self.write("Ending XMLRPC request: %-s %.2f", method,
                    (time.time() - self.xmlStartTime) * 1000)

    def startHtml(self, uri):
        self.htmlStartTime = time.time()
        self.write("Starting HTML request: %s", uri)

    def stopHtml(self, uri):
        self.write("Ending HTML request: %-s %.2f", uri,
                   (time.time() - self.htmlStartTime) * 1000)

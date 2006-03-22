#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#

import os
import types
import sys
import syslog
import config
import time

# Markers used in the data output
START_MARKER = '>>'
STOP_MARKER  = '<<'
COMMENT_MARKER = '#'

# Common request types and their tags
HTTP_TAG = 'HTTP'
RPC_TAG = 'RPC'
KID_TAG = 'KID'

class AbstractProfile(object):
    """
    Profile is a singleton object to be used to profile calling times within
    the Mint codebase. It currently saves its state in a stack (thus
    ensuring that no data is lost).

    Some things to be aware of:

    * start/stop calls may be nested, but must be symmetric
    * this class is not reentrant (thread safe)

    Additionally, if the system is in debug mode (cfg.debugMode = True)
    then we will count the number of total references to all objects in
    the system after each request.
    """

    _stack = []

    def __new__(cls, *p, **kwargs):
        """
        Ensures that there is one and only one profile object in
        the system at a time (i.e. singleton dp).
        """
        if not '_it' in cls.__dict__:
            cls._it = object.__new__(cls)
        return cls._it

    def __init__(self, cfg = None):
        """
        Initialize the profile object based on the cfg object passed in.
        If cfg is None or cfg.profiling is False, then a skeleton object
        is created and all start/stop calls will be no-ops.
        @param cfg: the Mint configuration object
        """
        if not cfg:
            self.profiling = False
            self.cfg = None
        else:
            self.profiling = cfg.profiling
            self.cfg = cfg

    def _writeData(self, formatString, *args):
        """
        Write a line of profiling data to the logfile. Currently outputs
        the following data:

        seconds_since_epoch|loadavg|pid|nest_level| ...

        The caller is expected to give us the remainder of the fields,
        separated by '|'s.

        @param formatString: a format string to write
        @param *args: arguments to the format string
        """
        self._write('%.3f|%.2f|%d|%d|' % (time.time(), os.getloadavg()[0],\
            os.getpid(), len(Profile._stack)) + (formatString % args))

    def _writeComment(self, s):
        """
        Write a comment to the profiling file. This comment could be useful
        for human readability.
        @param s: comment to write to the file
        """
        self._write(COMMENT_MARKER + s)

    def _write(self, s):
        raise NotImplementedError

    def _get_refcounts(self):
        """
        Count all of the references to every object in the system.
        This is a blunt tool, but should allow us to see if there
        are long term trends in the system towards leaking.
        Returns the total number of references in the system.
        (code from http://www.nightmare.com/medusa/memory-leaks.html)
        """
        refcounts = 0
        sys.modules
        for m in sys.modules.values():
            for sym in dir(m):
                o = getattr(m, sym)
                if type(o) is types.ClassType:
                    refcounts += sys.getrefcount(o)
        return refcounts

    def start(self, tag, name):
        """
        Called at the start of tracking an event.
        Does nothing if cfg.profiling is False.
        @param tag: the type of event (e.g. KID uses KID_TAG)
        @param name: a string that iDENTIFIES the event
        """
        if self.profiling:
            Profile._stack.append( ( tag, name, time.time() ) )
            self._writeData('%s|%s' % ((START_MARKER + tag), name))

    def stop(self, tag, name):
        """
        Called at the end of tracking an event.
        Does nothing if cfg.profiling is False.
        @param tag: the type of event (e.g. KID uses KID_TAG)
        @param name: a string that identifies the event.
        """
        if self.profiling:
            p = Profile._stack.pop()
            elapsed = ((time.time() - p[2]) * 1000)
            self._writeData('%s|%s|%d' % \
                    ((STOP_MARKER + tag), name, elapsed))

            # Stuff to do at the end of the request
            if (len(Profile._stack) == 0):
                if self.cfg.debugMode:
                    self._writeComment(' total refcounts (pid %d): %d' %\
                            (os.getpid(), self._get_refcounts()))


    # Convenience methods below -------------------------------------------

    def startXml(self, method):
        """
        Call at the start of an RPC (XML, JSON) method.
        @param method: the method name
        """
        self.start(RPC_TAG, method)

    def stopXml(self, method):
        """
        Call at the end of an RPC (XML, JSON) method.
        @param method: the method name
        """
        self.stop(RPC_TAG, method)

    def startHttp(self, uri):
        """
        Call at the start of an HTTP request.
        @param uri: the URI of the request
        """
        self.start(HTTP_TAG, uri)

    def stopHttp(self, uri):
        """
        Call at the end of an HTTP request.
        @param uri: the URI of the request
        """
        self.stop(HTTP_TAG, uri)

    def startKid(self, templateName):
        """
        Call at the start of Kid template loading and rendering.
        @param uri: the URI of the request
        """
        self.start(KID_TAG, templateName)

    def stopKid(self, templateName, wasCacheHit):
        """
        Call at the start of Kid template loading and rendering.
        @param templateName: the name of the template file
        @param wasCacheHit: was the Kid cache used during loading?
        """
        logText = (wasCacheHit and "+" or "-") + templateName
        self.stop(KID_TAG, logText)


class SyslogProfile(AbstractProfile):
    """Log profiling data to syslog."""
    def __new__(cls, *p, **kwargs):
        ret = AbstractProfile.__new__(cls, *p, **kwargs)
        syslog.openlog('rbuilder', 0, syslog.LOG_LOCAL0)
        return ret

    def _write(self, s):
        syslog.syslog(syslog.LOG_INFO, s)


class Profile(AbstractProfile):
    """Log profiling data to an arbitrary file."""
    _logfile = None

    def _openLog(self):
        """
        Opens the log file if it isn't already open.
        """
        if not Profile._logfile:
            if 'logs' not in os.listdir(self.cfg.dataPath):
                os.mkdir(self._logPath())
            Profile._logfile = open(self._logfileName(), 'a')

    def _closeLog(self):
        """
        Closes the log file and resets it to None.
        """
        if Profile._logfile:
            Profile._logfile.close()
            Profile._logfile = None

    def _write(self, s):
        """
        Writes and flushes the data to the currently open logfile, if any.
        @param s: the string to write to the file
        """
        # Tack on a line separator
        if not s.endswith('\n'):
            s += '\n'

        # Write the string and flush buffers
        #
        # XXX: Yes, I know that this is ugly; but it assures that logrotate
        # doesn't lose data.
        self._openLog()
        Profile._logfile.write(s)
        self._closeLog()

    def _logPath(self):
        """
        Returns the current log path to be used by profiling.
        """
        return os.path.join(self.cfg.dataPath, 'logs')

    def _logfileName(self):
        """
        Returns the current log file name (with path) to be used by profiling.
        """
        return os.path.join(self._logPath(), 'profiling')

    def _logExists(self):
        """
        Returns whether the current log file exists or not.
        Useful to handle log rotation.
        """
        return os.path.exists(self._logfileName())



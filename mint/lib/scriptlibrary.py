#
# Copyright (c) 2005-2009 rPath, Inc.
#
# All rights reserved
#

import fcntl
import logging
import os
import os.path
import signal
import sys
import traceback
from conary.lib.log import logger
from mint import config
from mint.lib import mintutils

log = logging.getLogger(__name__)


class GenericScript(object):
    """ 
    Class used for a script which has an action phase and an optional
    cleanup phase.
    """

    cfg = None
    logFileName = None
    logPath = None
    newLogger = False
    timeout = None

    def __init__(self):
        self.name = os.path.basename(sys.argv[0])
        self.resetLogging()

    def resetLogging(self, quiet=False, verbose=False, fileLevel=logging.DEBUG):
        if self.newLogger:
            if verbose:
                level = logging.DEBUG
            elif quiet:
                level = logging.ERROR
            else:
                level = logging.INFO
            mintutils.setupLogging(self.logPath, consoleLevel=level,
                    fileLevel=fileLevel)
            # Set the conary logger to not eat messages
            logger.setLevel(logging.NOTSET)
        else:
            self._resetLogging()

    def _resetLogging(self):
        """
        You can override the logPath after __init__ by calling this method.
        """
        oldLogPath = None
        # Check if the log path is writable before opening the logger
        if self.logPath:
            try:
                open(self.logPath, 'a').close()
            except (OSError, IOError):
                # If it is not, then fall back to having no file
                oldLogPath = self.logPath
                self.logPath = None

        setupScriptLogger(self.logPath)
        self.log = getScriptLogger()

        if oldLogPath:
            self.log.warning("Unable to write to log file: %s" % oldLogPath)

    def setConfig(self, cfg):
        self.cfg = cfg
        if self.logFileName and not self.logPath:
            self.logPath = os.path.join(cfg.logPath, self.logFileName)
            self.resetLogging()

    def loadConfig(self, cfgPath=config.RBUILDER_CONFIG):
        self.setConfig(config.getConfig(cfgPath))

    def run(self):
        """ 
        Call this to run the script action. 
        """
        try:
            return self._run()
        except KeyboardInterrupt:
            print
            print 'interrupted'
            return 1
        except SystemExit, err:
            return err.code
        except:
            log.exception("Unhandled exception in script:")
            return 1

    def action(self):
        """ 
        Classes inheriting from SingletonScript should implement this
        method. This is where the script's behavior should go. Must return
        an integer status code (0 is OK, anything else is considered a 
        failure code. 
        """
        raise NotImplementedError
    
    def cleanup(self):
        """ 
        This is called unconditionally before the script exits.
        """
        pass

    def usage(self):
        """ 
        Print a usage statement; should be overridden by the caller.
        """
        pass

    def handle_args(self):
        """
        Override if you wish to handle command-line arguments. 
        Return True if args were OK; false otherwise.
        """
        return True

    def _run(self):
        if not self.handle_args():
            self.usage()
            return 1
        else:
            return self._runAction()

    def _runAction(self):
        if self.timeout:
            signal.signal(signal.SIGALRM, self._onTimeout)
            signal.alarm(self.timeout)

        exitcode = 1
        try:
            exitcode = self.action()
        except SystemExit, error:
            exitcode = error.code
        except KeyboardInterrupt:
            log.error("Interrupted by user")
        except:
            log.exception("Unhandled exception in script action:")
        self.cleanup()
        return exitcode

    def _onTimeout(self, signum, sigtb):
        raise RuntimeError("script %s timed out" % (self.name,))


# XXX: this should probably be /var/lock, but we need a properly setgid()
# wrapper that will make the script setgid to the 'lock' group.
DEFAULT_LOCKPATH = '/var/tmp'

class SingletonScript(GenericScript):
    """
    Class for scripts which need to run serially.
    """

    def __init__(self, aLockpath = DEFAULT_LOCKPATH):
        GenericScript.__init__(self)
        self.lockFileName = '%s/%s.lck' % (aLockpath, self.name)
        self.lockFile = None

    def _lock(self):
        """
        Attempts to control a lockfile via fcntl. If the lock can be obtained,
        the current PID will be written into the file. If another script holds
        the fcntl lock, the script will abort with a message warning the user;
        if this instance of the script obtains the fcntl lock, then the
        lockfile is created/overritten with new information and the script's
        action() method will be called.
        """
        self.lockFile = open(self.lockFileName, "w+")
        try:
            fcntl.lockf(self.lockFile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError, e:
            if e.errno == 11:
                print >> sys.stderr, \
                      "Looks like we're already running; exiting"
                sys.stderr.flush()
                return False
            raise
        # placing the PID into this file is simply for readability since the
        # fcntl is absolute proof of ownership.
        self.lockFile.write(str(os.getpid()))
        self.lockFile.flush()
        return True

    def _unlock(self):
        """
        Unlocks the lockfile if it exists.
        """
        if self.lockFile:
            self.lockFile.close()
            self.lockFile = None

    def _run(self):
        exitcode = -1
        # check args
        if not self.handle_args():
            self.usage()
            return exitcode

        # create lockfile
        try:
            if not self._lock():
                return exitcode
        except:
            print >> sys.stderr, "Failed to create lockfile %s" % \
                    self.lockFileName
            sys.stderr.flush()
            return exitcode

        try:
            # run action, always running cleanup at the end
            exitcode = self._runAction()
        finally:
            self._unlock()
            return exitcode


LOGGER_ID_SCRIPT = 'scriptlogger'

class ScriptLogger(object):
    """
    Singleton class for handling log output in scripts.
    """

    setup = False

    def __new__(cls, *p, **kwargs):
        """
        Ensures that there is one and only one scriptlogger object in
        the system at a time (i.e. singleton dp).
        """
        if not '_it' in cls.__dict__:
            cls._it = object.__new__(cls)
        return cls._it

    def __init__(self):
        """
        This should not be called by the public; use setupScriptLogger
        and getScriptLogger instead.
        """

        # get our instance of slogger
        self.slogger = logging.getLogger(LOGGER_ID_SCRIPT)

    def error(self, *args):
        "Log an error"
        self.slogger.error(*args)

    def warning(self, *args):
        "Log a warning"
        self.slogger.warning(*args)

    def info(self, *args):
        "Log an informative message"
        self.slogger.info(*args)

    def debug(self, *args):
        "Log a debugging message"
        self.slogger.debug(*args)

    def flush(self):
        for handler in self.slogger.handlers:
            handler.flush()

_scriptLogger = ScriptLogger()

def setupScriptLogger(logfile = None, consoleLevel = logging.WARNING,
        logfileLevel = logging.INFO):
    """
    Sets up the script logger instance for the process. If aLogfile
    is given, will log output to the given logfile in addition to 
    sys.stderr. Defaults to logging WARNING level messages to sys.stderr,
    and INFO level messages to the logfile (if aLogfile is specified).
    By default, output is sent to sys.stderr ONLY.

    While setupScriptLogger may be called more than once to reconfigure
    the script logger, it is better practice to call it before calling
    getScriptLogger (unless you want the script logger's default behavior).
    """
    assert(_scriptLogger)

    # clear the handlers before proceeding
    while _scriptLogger.slogger.handlers:
        _scriptLogger.slogger.removeHandler(_scriptLogger.slogger.handlers[0])

    # set up a console handler
    consoleFormatter = logging.Formatter('%(levelname)s: %(message)s')
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(consoleFormatter)
    consoleHandler.setLevel(consoleLevel)
    _scriptLogger.slogger.addHandler(consoleHandler)

    # if a logfile was specified, create a handler for it, too
    if logfile:
        logfileFormatter = mintutils.ISOFormatter('%(asctime)s [%(process)d] '
                '%(levelname)s %(name)s : %(message)s')
        logfileHandler = logging.FileHandler(logfile)
        logfileHandler.setFormatter(logfileFormatter)
        logfileHandler.setLevel(logfileLevel)
        _scriptLogger.slogger.addHandler(logfileHandler)

        # also, let's log conary messages that would normally go to standard out
        # into our log files
        if globals().has_key("logger"):
            conaryLogfileFormatter = mintutils.ISOFormatter(
                    '%(asctime)s [%(process)d] CONARY: %(message)s')
            conaryLogfileHandler = logging.FileHandler(logfile)
            conaryLogfileHandler.setFormatter(conaryLogfileFormatter)
            # always use debug level here no matter what
            conaryLogfileHandler.setLevel(logging.DEBUG)
            logger.addHandler(conaryLogfileHandler)

    # make sure the slogger handles all of the messages we want
    _scriptLogger.slogger.setLevel(min(consoleLevel, logfileLevel))

    # The root logger also needs to go somewhere, if it has no handlers
    # then point it our way.
    rootLogger = logging.getLogger()
    if not rootLogger.handlers:
        rootLogger.handlers = _scriptLogger.slogger.handlers[:]
        rootLogger.setLevel(min(consoleLevel, logfileLevel))

    _scriptLogger.setup = True

def getScriptLogger():
    "Returns the singleton instance of the script logger."

    assert(_scriptLogger)

    if not _scriptLogger.setup:
        setupScriptLogger()

    return _scriptLogger


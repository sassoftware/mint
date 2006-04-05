#
# Copyright (c) 2006 rPath, Inc.
#
# All rights reserved
#
import os
import os.path
import sys
import traceback
import logging


class GenericScript:
    """ 
    Class used for a script which has an action phase and an optional
    cleanup phase.
    """

    def __init__(self):
        self.name = os.path.basename(sys.argv[0])

    def run(self):
        """ 
        Call this to run the script action. 
        """
        return self._run()

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
        Classes inheriting from SingletonScript may implement this 
        method to run finalizers, etc. 
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
        exitcode = 1

        if not self.handle_args():
            self.usage()
        else:
            try:
                exitcode = self.action()
            finally:
                self.cleanup()
                logging.shutdown()

        return exitcode


# XXX: this should probably be /var/lock, but we need a properly setgid()
# wrapper that will make the script setgid to the 'lock' group for rPL.
DEFAULT_LOCKPATH = '/var/tmp'

class SingletonScript(GenericScript):
    """ 
    Class for scripts which need to run serially.
    """

    def __init__(self, aLockpath = DEFAULT_LOCKPATH):
        GenericScript.__init__(self)
        self.lockFileName = '%s/%s.lck' % (aLockpath, self.name)

    def _lock(self):
        """ 
        Checks for the existence of a lockfile. If it exists, will 
        make an effort to see if the PID in the lockfile is still running.
        If it is, the script will abort with a message warning the user;
        otherwise, the lock will be considered to be stale.
        If no lockfile exists, or if a stale lockfile is found, then
        the lockfile is created/overritten with new information and
        the script's action() method will be called.
        """

        # Check for a lockfile here
        if os.path.exists(self.lockFileName):
            lockFile = open(self.lockFileName,"r")
            lockPid = int(lockFile.readline().strip())
            procFilePath = '/proc/%d/cmdline' % (lockPid, )
            if os.path.exists(procFilePath):
                procFile = open(procFilePath,"r")
                if procFile.readline().find(self.name) < 0:
                    print >> sys.stderr, "Deleting stale lockfile"
                    lockFile.close()
                    os.unlink(self.lockFileName)
                else:
                    print >> sys.stderr, "Looks like we're already running; exiting"
                    return 1
                procFile.close()

        # Create the lock file
        newLockFile = open(self.lockFileName, "w+")
        newLockFile.write(str(os.getpid()))
        newLockFile.close()

    def _unlock(self):
        """
        Unlocks the lockfile if it exists.
        """
        if os.path.exists(self.lockFileName):
            os.unlink(self.lockFileName)

    def _run(self):
        exitcode = -1
        try:
            # check args
            if not self.handle_args():
                self.usage()
                raise

            # lockfile
            try:
                self._lock()
            except:
                print >> sys.stderr, "Failed to create lockfile %s" % \
                        self.lockFileName
                raise

            # run action, always running cleanup at the end
            try:
                try:
                    exitcode = self.action()
                # handle KeyboardInterrupt
                except KeyboardInterrupt:
                    print >> sys.stderr, "Interrupted by user"
                except Exception, e:
                    exc = traceback.format_exc()
                    print >> sys.stderr, exc
            finally:
                self.cleanup()

        finally:
            self._unlock()
            logging.shutdown()
            return exitcode

LOGGER_ID_SCRIPT = 'scriptlogger'

class ScriptLogger(object):
    """
    Class for handling log output in scripts.
    """
    
    logger = None

    def __new__(cls, *p, **kwargs):
        """
        Ensures that there is one and only one scriptlogger object in
        the system at a time (i.e. singleton dp).
        """
        if not '_it' in cls.__dict__:
            cls._it = object.__new__(cls)
        return cls._it

    def __init__(self, aLogfile = None, aConsoleLevel = logging.INFO, aLogfileLevel = logging.INFO):

        if not self.logger:
            # get our instance of logger
            self.logger = logging.getLogger(LOGGER_ID_SCRIPT)

            # set up a console handler
            consoleFormatter = logging.Formatter('%(levelname)s: %(message)s')
            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(consoleFormatter)
            consoleHandler.setLevel(aConsoleLevel)
            self.logger.addHandler(consoleHandler)

            # if a logfile was specified, create a handler for it, too
            if aLogfile:
                logfileFormatter = logging.Formatter('%(asctime)s [%(process)d] %(levelname)s: %(message)s', '%Y-%b-%d %H:%M:%S')
                logfileHandler = logging.FileHandler(aLogfile)
                logfileHandler.setFormatter(logfileFormatter)
                logfileHandler.setLevel(aLogfileLevel)
                self.logger.addHandler(logfileHandler)

    def error(self, *args):
        "Log an error"
        self.logger.error(*args)

    def warning(self, *args):
        "Log a warning"
        self.logger.warning(*args)

    def info(self, *args):
        "Log an informative message"
        self.logger.info(*args)

    def debug(self, *args):
        "Log a debugging message"
        self.logger.debug(*args)


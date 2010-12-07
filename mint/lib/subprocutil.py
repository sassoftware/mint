#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

import epdb
import errno
import fcntl
import logging
import os
import random
import select
import signal
import subprocess
import sys
import time

log = logging.getLogger(__name__)


class LockError(RuntimeError):
    pass


class LockTimeoutError(LockError):
    pass


class Lockable(object):
    _lockFile = None
    _lockLevel = fcntl.LOCK_UN
    _lockPath = None

    @staticmethod
    def _sleep():
        time.sleep(random.uniform(0.1, 0.5))

    def _lock(self, mode=fcntl.LOCK_SH):
        assert self._lockPath

        # Short-circuit if we already have the lock
        if mode == self._lockLevel:
            return True

        if self._lockFile:
            lockFile = self._lockFile
        else:
            lockFile = self._lockFile = open(self._lockPath, 'w')

        try:
            try:
                fcntl.flock(self._lockFile.fileno(), mode | fcntl.LOCK_NB)
            except IOError, err:
                if err.errno in (errno.EACCES, errno.EAGAIN):
                    # Already locked, retry later.
                    raise LockError('Could not acquire lock')
                raise
            else:
                self._lockFile = lockFile
                self._lockLevel = mode

        finally:
            if mode == fcntl.LOCK_UN:
                # If we don't have any lock at the moment then close the file
                # so that if another process deletes the lockfile we don't end
                # up locking the now-nameless file. The other process *must*
                # hold an exclusive lock to delete the lockfile, so this
                # assures lock safety.
                self._lockFile.close()
                self._lockFile = None

        return True

    def _lockWait(self, mode=fcntl.LOCK_SH, timeout=600.0, breakIf=None):
        logged = False
        runUntil = time.time() + timeout
        while True:
            # First, try to lock.
            try:
                return self._lock(mode)
            except LockError:
                pass

            if breakIf and breakIf():
                return False

            if time.time() > runUntil:
                raise LockTimeoutError('Timed out waiting for lock')

            if not logged:
                logged = True
                log.debug("Waiting for lock")

            self._sleep()

    def _deleteLock(self):
        self._lock(fcntl.LOCK_EX)
        os.unlink(self._lockPath)
        self._lock(fcntl.LOCK_UN)

    def _close(self):
        if self._lockFile:
            self._lockFile.close()
        self._lockFile = None
        self._lockLevel = fcntl.LOCK_UN


class Pipe(object):
    def __init__(self):
        readFD, writeFD = os.pipe()
        self.reader = os.fdopen(readFD, 'rb')
        self.writer = os.fdopen(writeFD, 'wb')

    def closeReader(self):
        self.reader.close()

    def closeWriter(self):
        self.writer.close()

    def close(self):
        self.closeReader()
        self.closeWriter()

    def read(self):
        self.reader.read()

    def write(self, data):
        self.writer.write(data)


class Subprocess(object):
    # Class settings
    procName = "subprocess"
    setsid = False

    # Runtime variables
    pid = None
    exitStatus = exitPid = None

    @property
    def exitCode(self):
        if self.exitStatus is None:
            return -2
        elif self.exitStatus < 0:
            return self.exitStatus
        elif os.WIFEXITED(self.exitStatus):
            return os.WEXITSTATUS(self.exitStatus)
        else:
            return -2

    def start(self):
        self.exitStatus = self.exitPid = None
        self.pid = os.fork()
        if not self.pid:
            #pylint: disable-msg=W0702,W0212
            try:
                try:
                    if self.setsid:
                        os.setsid()
                    ret = self.run()
                    if not isinstance(ret, (int, long)):
                        ret = bool(ret)
                    os._exit(ret)
                except SystemExit, err:
                    os._exit(err.code)
                except:
                    log.exception("Unhandled exception in %s:", self.procName)
            finally:
                os._exit(70)
        return self.pid

    def run(self):
        raise NotImplementedError

    def _subproc_wait(self, flags):
        if not self.pid:
            return False
        while True:
            try:
                pid, status = os.waitpid(self.pid, flags)
            except OSError, err:
                if err.errno == errno.EINTR:
                    # Interrupted by signal so wait again.
                    continue
                elif err.errno == errno.ECHILD:
                    # Process doesn't exist.
                    log.debug("Lost track of subprocess %d (%s)", self.pid,
                            self.procName)
                    self.exitPid, self.pid = self.pid, None
                    self.exitStatus = -1
                    return False
                else:
                    raise
            else:
                if pid:
                    # Process exists and is no longer running.
                    log.debug("Reaped subprocess %d (%s) with status %s",
                            self.pid, self.procName, status)
                    self.exitPid, self.pid = self.pid, None
                    self.exitStatus = status
                    return False
                else:
                    # Process exists and is still running.
                    return True

    def check(self):
        """
        Return C{True} if the subprocess is running.
        """
        return self._subproc_wait(os.WNOHANG)

    def wait(self):
        """
        Wait for the process to exit, then return. Returns the exit code if the
        process exited normally, -2 if the process exited abnormally, or -1 if
        the process does not exist.
        """
        self._subproc_wait(0)
        return self.exitCode

    def kill(self, signum=signal.SIGTERM, timeout=5):
        """
        Kill the subprocess and wait for it to exit.
        """
        if not self.pid:
            return

        try:
            os.kill(self.pid, signum)
        except OSError, err:
            if err.errno != errno.ESRCH:
                raise
            # Process doesn't exist (or is a zombie)

        if timeout:
            # If a timeout is given, wait that long for the process to
            # terminate, then send a SIGKILL.
            start = time.time()
            while time.time() - start < timeout:
                if not self.check():
                    break
                time.sleep(0.1)
            else:
                # If it's still going, use SIGKILL and wait indefinitely.
                os.kill(self.pid, signal.SIGKILL)
                self.wait()


def debugHook(signum, sigtb):
    port = 8080
    try:
        log.error("Starting epdb session on port %d", port)
        debugger = epdb.Epdb()
        debugger._server = epdb.telnetserver.InvertedTelnetServer(('', port))
        debugger._server.handle_request()
        debugger._port = port
    except:
        log.exception("epdb session failed to start")
    else:
        debugger.set_trace(skip=1)


def setDebugHook():
    signal.signal(signal.SIGUSR1, debugHook)


def call(cmd, ignoreErrors=False, logCmd=True, logLevel=logging.INFO,
        captureOutput=True, wait=True, **kw):
    """
    Run command C{cmd}, optionally logging the invocation and output.

    If C{cmd} is a string, it will be interpreted as a shell command.
    Otherwise, it should be a list where the first item is the program name and
    subsequent items are arguments to the program.

    @param cmd: Program or shell command to run.
    @type  cmd: C{basestring or list}
    @param ignoreErrors: If C{False}, a L{CommandError} will be raised if the
            program exits with a non-zero return code.
    @type  ignoreErrors: C{bool}
    @param logCmd: If C{True}, log the invocation and its output.
    @type  logCmd: C{bool}
    @param captureOutput: If C{True}, standard output and standard error are
            captured as strings and returned.
    @type  captureOutput: C{bool}
    @param kw: All other keyword arguments are passed to L{subprocess.Popen}
    @type  kw: C{dict}
    """
    logger = _getLogger(kw.pop('_levels', 2))

    if logCmd:
        if isinstance(cmd, basestring):
            niceString = cmd
        else:
            niceString = ' '.join(repr(x) for x in cmd)
        env = kw.get('env', {})
        env = ''.join(['%s="%s" ' % (k,v) for k,v in env.iteritems()])
        logger.log(logLevel, "+ %s%s", env, niceString)

    kw.setdefault('close_fds', True)
    kw.setdefault('shell', isinstance(cmd, basestring))
    if 'stdin' not in kw:
        kw['stdin'] = devNull()

    pipe = captureOutput and subprocess.PIPE or None
    kw.setdefault('stdout', pipe)
    kw.setdefault('stderr', pipe)
    p = subprocess.Popen(cmd, **kw)

    if not p.stdout and not p.stderr:
        # Can't grab output if we don't have any pipes.
        captureOutput = False

    stdout = stderr = ''
    if captureOutput:
        while p.poll() is None:
            rList = [x for x in (p.stdout, p.stderr) if x]
            rList, _, _ = tryInterruptable(select.select, rList, [], [])
            for rdPipe in rList:
                line = rdPipe.readline()
                if rdPipe is p.stdout:
                    which = 'stdout'
                    stdout += line
                else:
                    which = 'stderr'
                    stderr += line
                if logCmd and line.strip():
                    logger.log(logLevel, "++ (%s) %s", which, line.rstrip())

        # pylint: disable-msg=E1103
        stdout_, stderr_ = p.communicate()
        if stderr_ is not None:
            stderr += stderr_
            if logCmd:
                for x in stderr_.splitlines():
                    logger.log(logLevel, "++ (stderr) %s", x)
        if stdout_ is not None:
            stdout += stdout_
            if logCmd:
                for x in stdout_.splitlines():
                    logger.log(logLevel, "++ (stdout) %s", x)
    elif wait:
        tryInterruptable(p.wait)

    if not wait:
        return p
    elif p.returncode and not ignoreErrors:
        raise CommandError(cmd, p.returncode, stdout, stderr)
    else:
        return p.returncode, stdout, stderr


def logCall(cmd, **kw):
    # This function logs by default.
    kw.setdefault('logCmd', True)

    # _getLogger() will need to go out an extra frame to get the original
    # caller's module name.
    kw['_levels'] = 3

    return call(cmd, **kw)


def _getLogger(levels=2):
    """
    Get a logger for the function two stack frames up, e.g. the caller of the
    function calling this one.
    """
    caller = sys._getframe(levels)
    name = caller.f_globals['__name__']
    return logging.getLogger(name)


def devNull():
    return open('/dev/null', 'w+')


def tryInterruptable(func, *args, **kwargs):
    while True:
        try:
            return func(*args, **kwargs)
        except Exception, err:
            if getattr(err, 'errno', None) == errno.EINTR:
                continue
            else:
                raise


class CommandError(RuntimeError):
    def __init__(self, cmd, rv, stdout, stderr):
        self.cmd = cmd
        self.rv = rv
        self.stdout = stdout
        self.stderr = stderr
        self.args = (cmd, rv, stdout, stderr)

    def __str__(self):
        return "Error executing command: %s (return code %d)" % (
                self.cmd, self.rv)

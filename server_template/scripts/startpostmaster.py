#!/usr/bin/python
import os

pgdata='@SERVER_PATH@/postgresql'
pgport='5439'
pid = os.fork()
if pid:
    pid, status = os.waitpid(pid, 0)
    if status:
        print 'Failed to start postmaster'
        os._exit(1)
else:
    try:
        logFile = open('@SERVER_PATH@/postgresql/postmaster.log', 'w')
        devNull = open('/dev/null', 'r')
        os.dup2(devNull.fileno(), 0)
        os.dup2(logFile.fileno(), 1)
        os.dup2(logFile.fileno(), 2)
        devNull.close()
        logFile.close()
        pid = os.fork()
        if pid:
            os._exit(0)
        else:
            os.setsid()
            os.execl("/usr/bin/postmaster", "/usr/bin/postmaster", "-p", pgport,                     '-D', pgdata)
    finally:
        os._exit(1)

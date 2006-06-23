#!/usr/bin/python
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved.
#

import os, sys, time
import traceback
import xmlrpclib

from conary import versions
from conary.lib import options
from conary.lib import coveragehook

class UnknownException(Exception):
    def __str__(self):
        return "%s %s" % (self.eName, self.eArgs)

    def __init__(self, eName, eArgs):
        self.eName = eName
        self.eArgs = eArgs

def usage():
    return "\n".join((
     "Usage: commitaction [commitaction args] ",
     "         --module '/path/to/statsaction --user <user>' --url <xmlrpc url>",
     ""
    ))

class _Method(xmlrpclib._Method):
    def __repr__(self):
        return "<rBuilderAction._Method(%s, %r)>" %(self._Method__send, self._Method__name)

    def __str__(self):
        return self.__repr__()

    def __call__(self, *args):
        return self.doCall(*args)

    def doCall(self, *args):
        isException, result = self.__send(self.__name, args)
        if not isException:
            return result
        else:
            self.handleError(result)

    def handleError(self, result):
        exceptionName = result[0]
        exceptionArgs = result[1:]

        if exceptionName == "CommitError":
            raise Exception(result)
        else:
            raise UnknownException(exceptionName, exceptionArgs)

class ServerProxy(xmlrpclib.ServerProxy):
    def __getattr__(self, name):
        return _Method(self.__request, name)

def process(repos, cfg, commitList, srcMap, pkgMap, grpMap, argv, otherArgs):
    coveragehook.install()
    if not len(argv) and not len(otherArgs):
        usage()
        return 1
    
    argDef = {
        'url' : options.ONE_PARAM,
        'user': options.ONE_PARAM,
        'hostname': options.ONE_PARAM,
    }

    # create an argv[0] for processArgs to ignore
    argv[0:0] = ['']
    argSet, someArgs = options.processArgs(argDef, {}, cfg, usage, argv=argv)
    # and now remove argv[0] again
    argv.pop(0)
    if len(someArgs):
        someArgs.pop(0)
    otherArgs.extend(someArgs)

    pid = os.fork()
    if not pid:
        #child
        #Double fork we want the parent to return immediately so that there's no delay
        pid2 = os.fork()
        if not pid2:
            #child2
            user = argSet['user']
            url  = argSet['url']

            overrideHostname = None
            if 'hostname' in argSet:
                overrideHostname = argSet['hostname']

            for commit in commitList:
                t, vStr, f = commit

                v = versions.VersionFromString(vStr)

                if overrideHostname:
                    hostname = overrideHostname
                else:
                    hostname = v.getHost()

                rBuilderServer = ServerProxy(url)

                try:
                    rBuilderServer.registerCommit(hostname, user, t, vStr)
                except Exception, e:
                    traceback.print_exc(file = sys.stderr)
                    os._exit(1)
            os._exit(0)
        else:
            #parent 2
            pid2, status = os.waitpid(pid2, 0)
            if status:
                sys.stderr.write("rBuilderAction failed with code %d" % status)
            os._exit(0)


    #parent 1
    #drive on oblivious

    return 0

if __name__ == "__main__":
    print usage()
    sys.exit(1)

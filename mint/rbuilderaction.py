#!/usr/bin/python
#
# Copyright (c) 2005 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.opensource.org/licenses/cpl.php.
#
# This program is distributed in the hope that it will be useful, but
# without any waranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

import os, sys, time
import xmlrpclib

import conary
from lib import options
import versions

def usage(exitcode=1):
    sys.stderr.write("\n".join((
     "Usage: commitaction [commitaction args] ",
     "         --module '/path/to/statsaction --user <user>' --url <xmlrpc url>",
     ""
    )))
    return exitcode

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
    if not len(argv) and not len(otherArgs):
        return usage()
    
    argDef = {
        'url' : options.ONE_PARAM,
        'user': options.ONE_PARAM,
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

            for commit in commitList:
                t, vStr, f = commit

                v = versions.VersionFromString(vStr)
                hostname = v.branch().label().getHost()

                rBuilderServer = ServerProxy(url)

                try:
                    rBuilderServer.registerCommit(hostname, user, t, vStr)
                except Exception, e:
                    sys.stderr.write(e)
                    sys.exit(1)
            sys.exit(0)
        else:
            #parent 2
            pid2, status = os.waitpid(pid2, 0)
            if status:
                sys.stderr.write("rBuilderAction failed with code %d" % status)
            else:
                sys.stdout.write("rBuilderAction completed successfully")
            sys.exit(0)


    #parent 1
    #drive on oblivious

    return 0

if __name__ == "__main__":
    sys.exit(usage())

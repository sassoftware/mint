#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#
import time
import os
import sys

from mint import buildtypes
from mint import userlevels
from mint import jobstatus
from mint.cmdline import commands

from conary import versions, conarycfg
from conary.lib import options, log
from conary import conaryclient
from conary.deps import deps

class FindRefsCommand(commands.RBuilderCommand):
    commands = ['find-refs']
    paramHelp = "<trove spec>"

    docs = {'flat-list': 'show results in a flat list suitable for scripting.'}

    def addParameters(self, argDef):
        commands.RBuilderCommand.addParameters(self, argDef)
        argDef["flat-list"] = options.NO_PARAM

    def findTrove(self, nc, cc, n, v, f):
        return nc.findTrove(None, (n, v, f), cc.cfg.flavor)[0]

    def runCommand(self, client, cfg, argSet, args):
        args = args[1:]
        if len(args) < 1:
            return self.usage()

        flatList = argSet.pop('flat-list', False)

        cfg = conarycfg.ConaryConfiguration(True)
        cfg.initializeFlavors()

        cc = conaryclient.ConaryClient(cfg)
        nc = cc.getRepos()

        n, v, f = conaryclient.cmdline.parseTroveSpec(args[0])
        nvf = self.findTrove(nc, cc, n, v, f)

        queryFlavor = deps.flavorDifferences(cfg.flavor + [nvf[2]], strict = False)[nvf[2]]

        if not flatList:
            print "Projects that include a reference to %s=%s[%s]:" % (str(nvf[0]), str(nvf[1]), str(queryFlavor))
            print

        r = client.getTroveReferences(nvf[0], str(nvf[1]), nvf[2].freeze())
        for projectId, refs in r.items():
            p = client.getProject(int(projectId))
            if refs and not flatList:
                print "%s (%s):" % (p.getName(), p.getFQDN())
            for ref in refs:
                if ref:
                    flavor = deps.ThawFlavor(ref[2])
                    flavorDiffs = deps.flavorDifferences([nvf[2], flavor], strict = False)

                    if flatList:
                        print "%s=%s[%s]" % (ref[0], ref[1], flavor)
                    else:
                        diff = flavorDiffs[flavor].isEmpty() and ("[%s]" % flavorDiffs[flavor]) or ""
                        print "\t%s=%s%s" % (ref[0], ref[1], diff)


commands.register(FindRefsCommand)

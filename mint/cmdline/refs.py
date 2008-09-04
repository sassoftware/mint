#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#

from mint.cmdline import commands

from conary import conarycfg
from conary.lib import options
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

    def _output(self, nvf, flatList, client, data):
        for projectId, refs in data.items():
            p = client.getProject(int(projectId))
            if refs and not flatList:
                print "%s (%s):" % (p.getName(), p.getFQDN())
            for ref in refs:
                if ref:
                    # handle data from both References and Descendants
                    if len(ref) == 2:
                        ref = (nvf[0], ref[0], ref[1])

                    flavor = deps.ThawFlavor(ref[2])
                    flavorDiffs = deps.flavorDifferences([nvf[2], flavor], strict = False)

                    if flatList:
                        print "%s=%s[%s]" % (ref[0], ref[1], flavor)
                    else:
                        diff = (not flavorDiffs[flavor].isEmpty()) and ("[%s]" % flavorDiffs[flavor]) or ""
                        print "\t%s=%s%s" % (ref[0], ref[1], diff)

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
        if not v:
            raise RuntimeError, "You must specify at least a label to query. Eg., package=conary.example.com@rpl:1"

        nvf = self.findTrove(nc, cc, n, v, f)

        queryFlavor = deps.flavorDifferences(cfg.flavor + [nvf[2]], strict = False)[nvf[2]]

        if not flatList:
            print "Projects that include a reference to %s=%s[%s]:\n" % (str(nvf[0]), str(nvf[1]), str(queryFlavor))
        r = client.getTroveReferences(nvf[0], str(nvf[1]), [nvf[2].freeze()])
        self._output(nvf, flatList, client, r)

        if not flatList:
            print "\nProjects that derive %s=%s[%s]:\n" % (str(nvf[0]), str(nvf[1]), str(queryFlavor))
        d = client.getTroveDescendants(nvf[0], str(nvf[1].branch()), nvf[2].freeze())
        self._output(nvf, flatList, client, d)
        return 0

commands.register(FindRefsCommand)

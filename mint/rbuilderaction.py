#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

import time

import stats
import mint_server
import config

import conary
from lib import options
import versions

def usage(exitcode=1):
    sys.stderr.write("\n".join((
     "Usage: commitaction [commitaction args] ",
     "         --module '/path/to/statsaction --mintconf <mint config file> --user <user>'",
     ""
    )))
    return exitcode

def process(repos, cfg, commitList, srcMap, pkgMap, grpMap, argv, otherArgs):
    if not len(argv) and not len(otherArgs):
        return usage()
    
    argDef = {
        'user': options.ONE_PARAM,
        'mintconf' : options.ONE_PARAM,
    }

    # create an argv[0] for processArgs to ignore
    argv[0:0] = ['']
    argSet, someArgs = options.processArgs(argDef, {}, cfg, usage, argv=argv)
    # and now remove argv[0] again
    argv.pop(0)
    if len(someArgs):
        someArgs.pop(0)
    otherArgs.extend(someArgs)

    cfg = config.MintConfig()
    cfg.read(argSet['mintconf'])
    user = argSet['user']

    mint = mint_server.MintServer(cfg, allowPrivate = True)
    commitsTable = stats.CommitsTable(mint.db)
    
    for commit in commitList:
        t, vStr, f = commit

        v = versions.VersionFromString(vStr)
        hostname = v.branch().label().getHost()

        projectId = mint.getProjectIdByHostname(hostname)
        userId = mint.getUserIdByName(user)
        commitsTable.new(projectId, time.time(), t, vStr, userId)

    return 0

#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#
"""A handful of functions useful inside kid templates."""

import time
from mint import userlevels
from mint.client import extractIs

from conary.conaryclient.cmdline import parseTroveSpec
from conary import versions

def downloadTracker(cfg, url):
    if cfg.googleAnalyticsTracker:
        return {"onclick": "javascript:urchinTracker('%s');" % url}
    else:
        return {}

def injectVersion(version):
    parts = version.split('/')
    parts[-1] = str(time.time()) + ':' + parts[-1]
    return '/'.join(parts)

def isrMakeLegal(rMakeBuild, userLevel, trvName):
    """Returns True if 'trv' is legal to add to an rMake build."""
    # FIXME: the final condition currently removes group troves--but should
    # be re-enabled once rMake properly handles them.
    return rMakeBuild and not rMakeBuild.status and userLevel in userlevels.WRITERS and (':' not in trvName or trvName.endswith(':source')) and not trvName.startswith('group-')

def isGroupBuilderLegal(groupTrove, trv):
    """Returns True if 'trv' is legal to add to a group builder project."""
    return groupTrove and not groupTrove.troveInGroup(trv.getName())

def dictToJS(d):
    """Returns dict as a str with keys converted to str as well"""
    return str(dict([(str(x[0]), x[1]) for x in d.iteritems()]))

def shortTroveSpec(spec):
    n, v, f = parseTroveSpec(spec)
    return "%s=%s (%s)" % (n, str(versions.ThawVersion(v).trailingRevision()), extractIs(f))

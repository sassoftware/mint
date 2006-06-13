#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#
"""A handful of functions useful inside kid templates."""

import time
from mint import userlevels

def downloadTracker(cfg, url):
    if cfg.googleAnalyticsTracker:
        return {"onclick": "javascript:urchinTracker('%s');" % url}
    else:
        return {}

def injectVersion(version):
    parts = version.split('/')
    parts[-1] = str(time.time()) + ':' + parts[-1]
    return '/'.join(parts)

def isRMakeLegal(rMakeBuild, userLevel, trove):
    """Returns True if 'trove' is legal to add to an rMake build."""
    return rMakeBuild and not rMakeBuild.status and userLevel in userlevels.WRITERS and ':' not in trove.getName()

def isGroupBuilderLegal(groupTrove, trove):
    """Returns True if 'trove' is legal to add to a group builder project."""
    return groupTrove and not groupTrove.troveInGroup(trove.getName())

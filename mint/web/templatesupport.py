#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#
"""A handful of functions useful inside kid templates."""

import time
from mint.helperfuncs import getArchFromFlavor, getProjectText

import conary
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

def isGroupBuilderLegal(groupTrove, trv):
    """Returns True if 'trv' is legal to add to a group builder project."""
    return groupTrove and not groupTrove.troveInGroup(trv.getName())

def dictToJS(d):
    """Returns dict as a str with keys converted to str as well"""
    return str(dict([(str(x[0]), x[1]) for x in d.iteritems()]))

def shortTroveSpec(spec):
    n, v, f = parseTroveSpec(spec)
    try:
        v = versions.VersionFromString(v)
    except conary.errors.ParseError: # we got a frozen version string
        v = versions.ThawVersion(v)
    return "%s=%s (%s)" % (n, str(v.trailingRevision()), getArchFromFlavor(f))

def projectText():
    return getProjectText()

#!/usr/bin/env python2.4
# -*- python -*-
#
# Copyright (c) 2004-2005 rPath, Inc.
# All rights reserved
#

import base64
import errno
import os
import shutil
import string
import sys
import tempfile

import conary

from deps import deps
from lib import util, sha1helper
from repository import changeset, trovesource
import conarycfg
import conaryclient
import files
import trove
import updatecmd

def usage():
    print "usage: %s group /path/to/changesets/" %sys.argv[0]
    sys.exit(1)

def _getTrove(cs, name, version, flavor):
    troveCs = cs.getNewTroveVersion(name, version, flavor)
    t = trove.Trove(troveCs.getName(), troveCs.getOldVersion(),
                    troveCs.getNewFlavor(), troveCs.getChangeLog())
    t.applyChangeSet(troveCs)
    return t

def _handleKernelPackage(cs, name, version, flavor):
    # pull the kernel version string out of the trove Provides on
    # kernel:runtime
    #
    # FIXME: we assume that the kernel package will have a kernel:runtime
    # component.  Hopefully this will continue to be true.
    compName = name + ':runtime'
    compCs = cs.getNewTroveVersion(compName, version, flavor)
    provides = compCs.provides()
    if deps.DEP_CLASS_TROVES in provides.members:
        kernelProv = provides.members[deps.DEP_CLASS_TROVES].members.values()[0]
        kernelStr = kernelProv.flags.keys()[0]

    # other kernel types should be handled here, such as numa.
    if 'smp' in kernelStr:
        name = name + '-smp'
    return name, kernelStr

def _findValidTroves(cs, groupName, groupVersion, groupFlavor):
    # start the set of valid troves with the group itself
    valid = set()
    valid.add((groupName, groupVersion, groupFlavor))

    # iterate through the trove, recording all troves refrerenced by
    # it with byDetault=True
    t = _getTrove(cs, groupName, groupVersion, groupFlavor)
    for name, version, flavor in t.iterTroveList():
        if t.includeTroveByDefault(name, version, flavor):
            valid.add((name, version, flavor))
            if name.startswith('group-'):
                # recurse into included groups
                valid.update(_findValidTroves(cs, name, version, flavor))

    return valid

def _removeInvalidTroves(changeSetList, valid):
    finalCsList = []
    handled = set()
    for chunk in changeSetList:
        for csInfo in chunk:
            (name, (oldVersion, oldFlavor),
                   (newVersion, newFlavor), absolute) = csInfo
            entry = (name, newVersion, newFlavor)
            if entry in handled:
                continue
            if entry in valid:
                finalCsList.append(entry)
            # try to see if the package is included.  if so, go ahead
            # and add it to the finalCsList and mark it as included
            # already.  This makes the whole package get installed at
            # the first mention of a component, instead of the final
            # mention of the package.
            if ':' in name:
                entry = (name.split(':')[0], entry[1], entry[2])
                if entry in valid and not entry in handled:
                    finalCsList.append(entry)
                    handled.add(entry)

    return finalCsList

def _makeEntry(groupCs, name, version, flavor):
    # set up the base name, version, release that we'll use for anaconda
    dispName = name
    trailing = version.trailingRevision().asString()
    ver = trailing.split('-')
    verStr = '-'.join(ver[:-2])
    release = '-'.join(ver[-2:])

    # handle kernel as a special case, so that anaconda can set up grub
    # entries and so on
    if name == 'kernel':
        dispName, kernelVer = _handleKernelPackage(groupCs, name, version,
                                                   flavor)
        verStr, release = kernelVer.split('-')

    # grab the arch out of the flavor, this isn't perfect.
    if deps.DEP_CLASS_IS in flavor.members:
        pkgarch = flavor.members[deps.DEP_CLASS_IS].members.keys()[0]
    else:
        pkgarch = 'none';

    csfile = "%s-%s-%s.ccs" % (dispName, trailing, pkgarch)

    # instantiate the trove so we canget the size out of it
    t = _getTrove(groupCs, name, version, flavor)
    size = t.getSize() or 0
    # we don't want to double count the space that the group trove reports
    if name.startswith('group-'):
        size = 0
    # filename, trove name, version, release, size, discnum
    entry = "%s %s %s %s %s %s" %(csfile, dispName, verStr, release, size, 1)

    return csfile, entry


def _getCacheFilename(name, version, flavor):
    # hash the version and flavor to give a unique filename
    versionFlavor = '%s %s' %(version.asString(), flavor.freeze())
    h = sha1helper.md5ToString(sha1helper.md5String(versionFlavor))
    return '%s-%s.ccs' %(name, h)

def _linkOrCopyFile(src, dest):
    try:
        os.link(src, dest)
    except OSError, msg:
        if msg.errno != errno.EXDEV:
            raise
        fd, fn = tempfile.mkstemp(dir=os.path.dirname(dest))
        destf = os.fdopen(fd, 'w')
        srcf = open(src, 'r')
        shutil.copyfileobj(srcf, destf)
        destf.close()
        srcf.close()
        os.rename(fn, dest)
        os.chmod(dest, 0644)

def extractChangeSets(client, cfg, csdir, groupName, groupVer, groupFlavor,
                      oldFiles = None, cacheDir = None):
    """
    extractChangesets extracts changesets from a group and creates
    cslist entries as it does so.

    @param client: ConaryClient instance used to communicate with the
    repository servers
    @type client: ConaryClient instance
    @param cfg: configuration settings to use
    @type cfg: ConaryConfiguration instance
    @param csdir: the final location for the changesets
    @type csdir: str
    @param groupName: name of group to extract changesets from
    @type groupName: str
    @param groupVer: version of group to extract changesets from
    @type groupVer: Version instance
    @param groupFlavor: flavor of group to extract changesets from
    @type groupFlavor: DependencySet instance

    @param oldFiles: a set of changeset filenames that already exist
    in the csdir.  Any valid changeset that is included in the group
    specified will be removed from the set.  This allows the caller
    to clean up unused changesets.  This is an optional parameter.
    @type oldFiles: set
    @param cacheDir: a directory to write all changeset files.  This
    allows the caller to maintain a global changeset cache.  Files
    will be hardlinked between the cachedir and the csdir if possible.
    This is an optional parameter.

    @returns cslist
    """
    assert(os.path.isdir(csdir))
    if cacheDir:
        assert(os.path.isdir(cacheDir))

    cslist = []

    cl = [ (groupName, (None, None), (groupVer, groupFlavor), 0) ]
    print >> sys.stderr, 'requesting changeset', groupName, groupVer
    group = client.createChangeSet(cl, withFiles=False, withFileContents=False)
    print >> sys.stderr, 'done!'

    # find the order that we should install things in
    jobSet = group.getJobSet()
    trvSrc = trovesource.ChangesetFilesTroveSource(client.db)
    trvSrc.addChangeSet(group, includesFileContents = False)
    failedDeps = client.db.depCheck(jobSet, trvSrc)[0]

    rc = client.db.depCheck(jobSet, trvSrc, findOrdering=True)
    failedList, unresolveableList, changeSetList = rc
    if failedList:
        print >> sys.stderr, 'WARNING: unresolved dependencies:', failedList

    # instantiate all the trove objects in the group, make a set
    # of the changesets we should extract
    valid = _findValidTroves(group, groupName, groupVer, groupFlavor)
    # filter the change set list given by the dep solver
    finalList = _removeInvalidTroves(changeSetList, valid)

    # use the order to extract changesets from the repository
    for name, version, flavor in finalList:
        csfile, entry = _makeEntry(group, name, version, flavor)
        path = '%s/%s' %(csdir, csfile)

        copyToCache = False
        keep = False

        # check to see if we already have the changeset in the changeset
        # directory
        if oldFiles and path in oldFiles:
            # make a note that we already have this cs
            keep = True
        elif cacheDir:
            # check for the cs in the cacheDir
            cacheName = _getCacheFilename(name, version, flavor)
            cachedPath = os.path.join(cacheDir, cacheName)
            if os.path.exists(cachedPath):
                _linkOrCopyFile(cachedPath, path)
                # make a note that we already have this cs
                keep = True

        if keep:
            # we either pulled the changeset from the cache
            # or we already have it in the changeset directory
            try:
                print >> sys.stderr, 'keeping', path
                oldFiles.remove(path)
                keep = True
            except:
                pass
        else:
            print >> sys.stderr, "creating", path
            csRequest = [(name, (None, None), (version, flavor), True)]
            # if we're extracting a group, don't recurse
            recurse = not name.startswith('group-')

            # create the cs to a temp file
            fd, fn = tempfile.mkstemp(prefix=csfile, dir=csdir)
            os.close(fd)
            client.createChangeSetFile(fn, csRequest, recurse = recurse)
            # rename to final path and change permissions
            os.rename(fn, path)
            os.chmod(path, 0644)

            # link this into the cache dir if we need to
            if cacheDir:
                # cachedPath is calculated above
                _linkOrCopyFile(path, cachedPath)

        cslist.append(entry)

    return cslist

if __name__ == '__main__':
    sys.excepthook = util.genExcepthook()

    if len(sys.argv) != 3:
        usage()

    topGroup = sys.argv[1]
    csdir = sys.argv[2]
    util.mkdirChain(csdir)

    cfg = conarycfg.ConaryConfiguration()
    cfg.dbPath = ':memory:'
    cfg.root = ':memory:'
    cfg.initializeFlavors()
    client = conaryclient.ConaryClient(cfg)

    existingChangesets = set()
    for path in [ "%s/%s" % (csdir, x) for x in os.listdir(csdir) ]:
        existingChangesets.add(path)

    name, ver, flv = updatecmd.parseTroveSpec(topGroup)
    trvList = client.repos.findTrove(cfg.installLabelPath[0],\
                                     (name, ver, flv),
                                     defaultFlavor = cfg.flavor)

    if not trvList:
        print >> sys.stderr, "no match for", groupName
        raise RuntimeException
    elif len(trvList) > 1:
        print >> sys.stderr, "multiple matches for", groupName
        raise RuntimeException

    groupName, groupVer, groupFlavor = trvList[0]
    cslist = extractChangeSets(client, cfg, csdir, groupName,
                               groupVer, groupFlavor,
                               oldFiles = existingChangesets,
                               cacheDir = '/tmp/cscache')
    print '\n'.join(cslist)

    # delete any changesets that should not be around anymore
    for path in existingChangesets:
        print >> sys.stderr, 'removing unused', path
        os.unlink(path)

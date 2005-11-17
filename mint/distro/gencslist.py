#!/usr/bin/env python2.4
# -*- python -*-
#
# Copyright (c) 2004-2005 rPath, Inc.
# All rights reserved
#

import errno
import os
import shutil
import string
import sys
import tempfile

from conary.deps import deps
from conary.lib import util, sha1helper
from conary.repository import changeset, trovesource, netclient, shimclient
from conary.repository.netrepos import netserver
from conary import conarycfg
from conary import conaryclient
from conary import files
from conary import trove
from conary import updatecmd
from conary import versions

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
    if not name.endswith(':runtime'):
        compName = name + ':runtime'
    else:
        compName = name
    compCs = cs.getNewTroveVersion(compName, version, flavor)
    provides = compCs.provides()
    if deps.DEP_CLASS_TROVES in provides.members:
        kernelProv = provides.members[deps.DEP_CLASS_TROVES].members.values()[0]
        kernelStr = kernelProv.flags.keys()[0]

    name = name.split(':')[0]
    # other kernel types should be handled here, such as numa.
    if 'smp' in kernelStr:
        name = name + '-smp'
    return name, kernelStr

def _findValidTroves(cs, groupName, groupVersion, groupFlavor,
                     skipNotByDefault=False):
    # start the set of valid troves with the group itself
    valid = set()
    valid.add((groupName, groupVersion, groupFlavor))

    # iterate through the trove, recording all troves refrerenced by
    # it with byDetault=True
    t = _getTrove(cs, groupName, groupVersion, groupFlavor)
    for name, version, flavor in t.iterTroveList():
        if not skipNotByDefault or t.includeTroveByDefault(name, version, flavor):
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
            if ':' in name:
                # see if the package is included too.  If it is
                # go ahead and handle it now.
                pkgname = name.split(':')[0]
                pkgentry = (pkgname, entry[1], entry[2])
                if pkgentry in valid:
                    if not pkgentry in handled:
                        finalCsList.append(pkgentry)
                        # mark the package as handled so we don't do it
                        # again later.
                        handled.add(pkgentry)
                    # already (or just) handled, carry on
                    continue

            if entry in valid and not entry in handled:
                finalCsList.append(entry)
                handled.add(pkgentry)

    return finalCsList

def _makeEntry(groupCs, name, version, flavor):
    # set up the base name, version, release that we'll use for anaconda
    base = name
    trailing = version.trailingRevision().asString()
    ver = trailing.split('-')
    verStr = '-'.join(ver[:-2])
    release = '-'.join(ver[-2:])

    # handle kernel as a special case, so that anaconda can set up grub
    # entries and so on
    kernelSpec = "none"
    if name == 'kernel' or name == 'kernel:runtime':
        base, kernelVer = _handleKernelPackage(groupCs, name, version,
                                                     flavor)
        kernelSpec = '='.join((base, kernelVer))

    if deps.DEP_CLASS_IS in flavor.members:
        pkgarch = flavor.members[deps.DEP_CLASS_IS].members.keys()[0]
    else:
        pkgarch = 'none';

    csfile = "%s-%s-%s.ccs" % (base, trailing, pkgarch)

    # instantiate the trove so we canget the size out of it
    t = _getTrove(groupCs, name, version, flavor)
    size = t.getSize() or 0
    # we don't want to double count the space that the group trove reports
    if name.startswith('group-'):
        size = 0
    # filename, trove name, version, flavor, kernel=version, size, discnum
    frozenFlavor = flavor.freeze() or 'none'
    entry = "%s %s %s %s %s" %(csfile, name, version.asString(),
                               frozenFlavor, 1)

    return csfile, entry


def _getCacheFilename(name, version, flavor):
    # hash the version and flavor to give a unique filename
    versionFlavor = '%s %s' %(version.asString(), flavor.freeze())
    h = sha1helper.md5ToString(sha1helper.md5String(versionFlavor))
    return '%s-%s.ccs' %(name, h)

def _validateTrove(newCs, cachedCs, name, version, flavor):
    try:
        cachedTrove = _getTrove(cachedCs, name, version, flavor)
    except KeyError:
        # the cached cs doesn't know anything about the trove we
        # want, it's definitely not the trove we're looking for.
        # move along.
        return False
    newTrove = _getTrove(newCs, name, version, flavor)
    cachedTrove.idMap.clear()
    if cachedTrove.freeze() != newTrove.freeze():
        return False
    return True

def _validateChangeSet(path, cs, name, version, flavor):
    # check to make sure that a cached change set matches the version
    # from the repository
    cachedCs = changeset.ChangeSetFromFile(path)

    # first check the top level trove
    if not _validateTrove(cs, cachedCs, name, version, flavor):
        return False

    if name.startswith('group-'):
        # groups are extracted with recurse=False, so we are done with
        # validataion
        return True

    # then iterate over any included troves (if any)
    topTrove = _getTrove(cs, name, version, flavor)
    for name, version, flavor in topTrove.iterTroveList():
        # skip not byDefault troves
        try:
            if not topTrove.includeTroveByDefault(name, version, flavor):
                continue
        except KeyError:
            # missing byDefault infor for this trove, so it's bad
            return False
        if not _validateTrove(cs, cachedCs, name, version, flavor):
            return False

    return True

def _linkOrCopyFile(src, dest):
    while 1:
        try:
            os.link(src, dest)
        except OSError, msg:
            if msg.errno == errno.EEXIST:
                # if the file already exists, unlink and try again
                os.unlink(dest)
                continue
            # if we're attempting to make a cross-device link,
            # fall back to copy.
            if msg.errno != errno.EXDEV:
                # otherwise re-raise the unhandled exception, something
                # else went wrong.
                raise
            fd, fn = tempfile.mkstemp(dir=os.path.dirname(dest))
            destf = os.fdopen(fd, 'w')
            srcf = open(src, 'r')
            shutil.copyfileobj(srcf, destf)
            destf.close()
            srcf.close()
            os.rename(fn, dest)
            os.chmod(dest, 0644)
        break

def extractChangeSets(client, cfg, csdir, groupName, groupVer, groupFlavor,
                      oldFiles = None, cacheDir = None, callback = None):
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
    @param callback: Callback instance for progress.

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
    group = client.createChangeSet(cl, withFiles=False, withFileContents=False,
                                   skipNotByDefault = False)
    print >> sys.stderr, 'done!'
    # find the order that we should install things in
    jobSet = group.getJobSet()
    trvSrc = trovesource.ChangesetFilesTroveSource(client.db)
    trvSrc.addChangeSet(group, includesFileContents = False)

    rc = client.db.depCheck(jobSet, trvSrc, findOrdering=True)
    failedList, unresolveableList, changeSetList = rc
    if failedList:
        print >> sys.stderr, 'WARNING: unresolved dependencies:', failedList

    # instantiate all the trove objects in the group, make a set
    # of the changesets we should extract
    valid = _findValidTroves(group, groupName, groupVer, groupFlavor)
    # filter the change set list given by the dep solver
    finalList = _removeInvalidTroves(changeSetList, valid)

    total = len(finalList)
    # use the order to extract changesets from the repository
    for num, (name, version, flavor) in enumerate(finalList):
        csfile, entry = _makeEntry(group, name, version, flavor)
        path = '%s/%s' %(csdir, csfile)
        keep = False

        if cacheDir:
            cacheName = _getCacheFilename(name, version, flavor)
            cachedPath = os.path.join(cacheDir, cacheName)

        # check to see if we already have the changeset in the changeset
        # directory
        if oldFiles and path in oldFiles:
            # make a note that we already have this cs
            keep = True
        elif cacheDir:
            # check for the cs in the cacheDir
            if os.path.exists(cachedPath):
                _linkOrCopyFile(cachedPath, path)
                # make a note that we already have this cs
                keep = True

        # make sure that the existing changeset is not stale
        if keep:
            if not _validateChangeSet(path, group, name, version, flavor):
                # the existing changeset does not check out, toss it.
                keep = False

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
            if callback:
                callback.setPrefix('changeset %d of %d: ' %(num, total))
                callback.setChangeSet(name)
            client.createChangeSetFile(fn, csRequest, recurse = recurse,
                                       callback = callback)
            # rename to final path and change permissions
            os.rename(fn, path)
            os.chmod(path, 0644)

            # link this into the cache dir if we need to
            if cacheDir:
                # cachedPath is calculated above
                _linkOrCopyFile(path, cachedPath)

        cslist.append(entry)

    return cslist, group


class LocalRepository(netserver.NetworkRepositoryServer):
    """
    this is a small shim that set up a local NetworkRepositoryServer
    and provides a modified getChangeSet() method that works over local
    storage
    """
    def getChangeSet(self, authToken, clientVersin, chgSetList, recurse,
                     withFiles, withFileContents, excludeAutoSource):
        paths = []
        csList = []
	for (name, (old, oldFlavor), (new, newFlavor), absolute) in chgSetList:
	    newVer = self.toVersion(new)
	    if old == 0:
		l = (name, (None, None),
			   (self.toVersion(new), self.toFlavor(newFlavor)),
			   absolute)
	    else:
		l = (name, (self.toVersion(old), self.toFlavor(oldFlavor)),
			   (self.toVersion(new), self.toFlavor(newFlavor)),
			   absolute)
            csList.append(l)

        ret = self.repos.createChangeSet(csList,
                                recurse = recurse,
                                withFiles = withFiles,
                                withFileContents = withFileContents,
                                excludeAutoSource = excludeAutoSource)

        (cs, trovesNeeded, filesNeeded) = ret
        tmpFile = tempfile.mktemp(suffix = '.ccs')
        cs.writeToFile(tmpFile)
        size = os.stat(tmpFile).st_size
        return (tmpFile, [size], [], [])

    def commitChangeSet(self, cs):
        self.repos.commitChangeSet(cs, self.name)

    def __init__(self, serverName, dbpath):
        util.mkdirChain(dbpath)
        self.serverName = serverName
        netserver.NetworkRepositoryServer.__init__(self, dbpath, '/tmp',
                                                   '/tmp', serverName,
                                                   {})
        user = 'anonymous'
        try:
            self.auth.addUser(user, user)
            self.auth.addAcl(user, None, None, True, False, True)
        except:
            self.repos.troveStore.db.rollback()
            pass

    def __del__(self):
        self.db.close()
        del self.db


class LocalServerCache:
    # build a local repository on the fly for whatever we're asked for
    def __getitem__(self, item):
	if isinstance(item, versions.Label):
	    serverName = item.getHost()
	elif isinstance(item, str):
	    serverName = item
	else:
            if isinstance(item, versions.Branch):
		serverName = item.label().getHost()
	    else:
		serverName = item.branch().label().getHost()

	server = self.cache.get(serverName, None)
	if server is None:
            repos = LocalRepository(serverName, self.path)
            server = shimclient.ShimServerProxy(repos, 'http', 80,
                                                ('anonymous', 'anonymous'))
            self.cache[item] = server
	return server

    def __init__(self, path):
        """
        initializes the LocalServerCache
        @param path: path to the local repository
        """
	self.cache = {}
	self.path = path


class LocalNetClient(netclient.NetworkRepositoryClient):
    def __init__(self, path):
        self.c = LocalServerCache(path)
        self.localRep = None


def _getTrove(cs, name, version, flavor):
    pkgCs = cs.getNewTroveVersion(name, version, flavor)
    t = trove.Trove(pkgCs.getName(), pkgCs.getOldVersion(),
                    pkgCs.getNewFlavor(), pkgCs.getChangeLog())
    t.applyChangeSet(pkgCs)
    return t

def _getSourceBranches(cs, name, version, flavor):
    rc = set()
    metadataToName = {}

    # start with ourselves
    col = _getTrove(cs, name, version, flavor)
    key = (col.getSourceName(), col.getVersion().branch())
    rc.add(key)
    metadataToName[key] = name
    for (n, v, f) in col.iterTroveList():
        t = _getTrove(cs, n, v, f)
        key = (t.getSourceName(), t.getVersion().branch())
        rc.add(key)
        metadataToName[key] = n
        # recurse into things that are not components
        if ':' not in n:
            d, sources = _getSourceBranches(cs, n, v, f)
            metadataToName.update(d)
            rc.update(sources)
    return metadataToName, rc

def _getDescriptions(client, cs, name, version, flavor):
    byLabel = {}

    metadataToName, sources = _getSourceBranches(cs, name, version, flavor)
    for name, branch in sources:
        label = branch.label()
        if label in byLabel:
            byLabel[label].add((name, branch))
        else:
            byLabel[label] = set(((name, branch),))

    metadata = {}
    for label, trvlist in byLabel.iteritems():
        metadata.update(client.getMetadata(list(trvlist), label))
    sources = dict(sources)
    return sources, metadataToName, metadata

def writeSqldb(cs, path):
    tmpdir = tempfile.mkdtemp()

    if len(cs.primaryTroveList) != 1:
        raise RuntimeError, 'more than one top-level group is not supported'
    name, version, flavor = cs.primaryTroveList[0]
    # grab the server name from the version of the changeset
    for v in reversed(version.versions):
        if isinstance(v, versions.Label):
            serverName = v.getHost()
    assert(serverName is not None)
    # set up a local repository where we can commit the changeset
    localRepos = LocalRepository(serverName, tmpdir)
    localRepos.commitChangeSet(cs)

    # set up a conaryclient to get descriptions
    cfg = conarycfg.ConaryConfiguration()
    cfg.dbPath = ':memory:'
    cfg.root = ':memory:'
    cfg.initializeFlavors()
    client = conaryclient.ConaryClient(cfg)

    sources, metadataToName, metadata = _getDescriptions(client, cs, name, version, flavor)

    # set up a local net client to commit the descriptions
    repos = LocalNetClient(tmpdir)
    client.repos = repos

    for srcname, data in metadata.iteritems():
        branch = sources[srcname]
        name = metadataToName[(srcname, branch)]
        repos.updateMetadata(name, branch,
                             data.shortDesc, '', [], [], [],
                             data.source, data.language)

    # copy the file to the final location
    shutil.copyfile(tmpdir + '/sqldb', path)
    shutil.rmtree(tmpdir)

def usage():
    print "usage: %s group /path/to/changesets/ [sqldb]" %sys.argv[0]
    sys.exit(1)

if __name__ == '__main__':
    sys.excepthook = util.genExcepthook()

    if len(sys.argv) < 3 or len(sys.argv) > 4:
        usage()

    topGroup = sys.argv[1]
    csdir = sys.argv[2]
    sqldbpath = None
    if len(sys.argv) == 4:
        sqldbpath = sys.argv[3]

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
    cslist, groupcs = extractChangeSets(client, cfg, csdir, groupName,
                                        groupVer, groupFlavor,
                                        oldFiles = existingChangesets,
                                        cacheDir = '/tmp/cscache')
    print '\n'.join(cslist)

    # delete any changesets that should not be around anymore
    for path in existingChangesets:
        print >> sys.stderr, 'removing unused', path
        os.unlink(path)

    if sqldbpath:
        writeSqldb(groupcs, sqldbpath)

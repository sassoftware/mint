#
# Copyright (c) 2004-2005 rPath, Inc.
#
# This file is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.opensource.org/licenses/cpl.php.
#
# This program is distributed in the hope that it will be useful, but
# without any waranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

from flags import flags
from installmethod import FileCopyException
from rhpl.log import log
from rhpl.translate import _
from syslogd import syslog
from constants import *
import copy
import iutil
import packages
import rpm
import timer
import time
import os

import conarymethods

from conary import conaryclient, conarycfg
from conary.repository import changeset, netclient, repository, trovesource
from conary.callbacks import UpdateCallback, ChangesetCallback
from conary.lib import util
from conary.local import database
from conary.deps import deps

class ProgressHeader:
    # this is an awful thunk so we can get progress updates.  The data
    # for progress updates only get to the interfaces through rpm header
    # objects.
    def __init__(self, csnum, cscount, size):
        self.name = 'changeset %s' %csnum
        self.version = 'of'
        self.release = '%s' %cscount
        self.arch = ''
        self.size = size
        self.summary = ''

    def __getitem__(self, key):
        if key in (rpm.RPMTAG_NAME, 'name'):
            return self.name
        if key in (rpm.RPMTAG_VERSION, 'version'):
            return self.version
        if key in (rpm.RPMTAG_RELEASE, 'release'):
            return self.release
        if key in (rpm.RPMTAG_ARCH, 'arch'):
            return self.arch
        if key in (rpm.RPMTAG_SIZE, 'size'):
            return self.size
        if key in (rpm.RPMTAG_SUMMARY, 'summary'):
            return self.summary
        if key in (rpm.RPMTAG_BASENAMES, 'basenames'):
            return []

class InstallCallback(UpdateCallback, ChangesetCallback):
    def preparingChangeSet(self):
        self.status = 'preparing'
        self.progress.setPackageStatus("Building changeset request...", None)

    def resolvingDependencies(self):
        self.status = 'resolving'
        self.progress.setPackageStatus("Resolving dependencies...", None)

    def requestingChangeSet(self):
        self.timer.start()
        self.status = 'downloading'
        self.progress.setPackageStatus("Requesting changeset...", None)

    def downloadingChangeSet(self, got, need):
        self.status = 'downloading'
        if need != 0:
            self.progress.setPackageStatus(self.status, "(%d%% of %dk)"
                                           % ((got * 100) / need, need / 1024))

    def restoreFiles(self, size, totalSize):
        if self.status != 'install':
            self.progress.setPackageStatus(_("Installing..."), None)
            self.status = 'install'
        self.restored += size
        if totalSize != 0:
            self.progress.setPackageScale(self.restored, totalSize)

    def setUpdateHunk(self, num, total):
        if not total:
            return
        if num:
            # mark the last hunk complete
            h = ProgressHeader((num-1), total, self.restored)
            self.progress.completePackage(h, self.timer)
        self.restored = 0
        self.updateHunk = (num, total)
        h = ProgressHeader(num, total, 0)
        self.progress.setPackage(h)
        self.progress.setPackageScale(0, 1)

    def __init__(self, progress, timer):
        UpdateCallback.__init__(self)
        ChangesetCallback.__init__(self)
        self.timer = timer
        self.progress = progress
        self.restored = 0
        self.status = None
        self.updateHunk = None

def conaryInstallPost(id, intf, instPath):
    for x in ('/tmp/product/conaryrc',
              '/tmp/updates/conaryrc',
              '/mnt/source/RHupdates/conaryrc',
              '/etc/conaryrc'):
        if os.access(x, os.R_OK):
            iutil.copyFile(x, instPath + '/etc/conaryrc')
            break

    # run the tag scripts (if they exist)
    if os.path.exists(instPath + '/root/conary-tag-script'):
        win = intf.waitWindow(_("Running"),
                              _("Running post installation scripts"))
        old = open(instPath + '/root/conary-tag-script', 'r')
        new = open(instPath + '/root/conary-tag-script.new', 'w')
        # put ldconfig at the top of the script, kill all the others
        new.write('/sbin/ldconfig\n')
        for line in old:
            if not line.startswith('/sbin/ldconfig'):
                new.write(line)
        new.close()
        old.close()
        os.rename(instPath + '/root/conary-tag-script.new',
                  instPath + '/root/conary-tag-script')
        iutil.execWithRedirect('/bin/sh',
                               ('/bin/sh', '-x', '/root/conary-tag-script'),
                               stdout='/root/conary-tag-script.output',
                               stderr='/root/conary-tag-script.output',
                               root=instPath)
        win.pop()

    for (n, tag) in id.grpset.kernelVersionList():
        log('making initrd for %s', n)
        packages.recreateInitrd(n, instPath)

def doConaryRepositoryInstall(method, id, intf, instPath):
    # set up install.log
    instLogName = instPath + '/root/install.log'
    try:
	iutil.rmrf(instLogName)
    except OSError:
	pass
    instLog = open(instLogName, "w+")
    instLogFd = instLog.fileno()

    # set up our syslogd
    if flags.setupFilesystems:
        # dont start syslogd if we arent creating filesystems
	syslogname = instLogName + '.syslog'
	try:
	    iutil.rmrf (syslogname)
	except OSError:
	    pass
	syslog.start(instPath, syslogname)
    else:
	syslogname = None

    pkgTimer = timer.Timer(start = 0)

    total = 0
    l = []
    for p in id.grpset.hdrlist.values():
        if p.isSelected():
            instLog.write('installing %s %s-%s.\n' %(p.hdr['name'],
                                                     p.hdr['version'],
                                                     p.hdr['release']))
            n, v, f = p.hdr.nvf
            job = (n, (None, None), (v, f), False)
            l.append(job)
            total += (p[rpm.RPMTAG_SIZE] / 1024)

    id.instProgress.setSizes(len(l), total, 0)
    id.instProgress.processEvents()
    cfg = method.cfg
    cfg.root = instPath
    cfg.threaded = False
    cfg.tempDir = instPath + '/var/tmp'

    util.settempdir(cfg.tempDir)

    client = conaryclient.ConaryClient(cfg)

    callback = InstallCallback(id.instProgress, pkgTimer)

    updJob = client.updateChangeSet(l, resolveDeps = False,
                                    keepExisting = True,
                                    callback = callback,
                                    recurse = True,
                                    split = True)[0]
    client.applyUpdate(updJob, replaceFiles = True,
                       tagScript = instPath + '/root/conary-tag-script',
                       localRollbacks = cfg.localRollbacks,
                       autoPinList = cfg.pinTroves,
                       callback = callback)
    id.instProgress.setPackageScale(1, 1)
    id.instProgress = None

    conaryInstallPost(id, intf, instPath)

    method.filesDone()

def _collapseJobs(l):
    # take all the jobs in the job list, collect up all the job
    # entries that use one changeset file and batch them up
    jobList = []
    lastCsfile = None

    for p in l:
        h = p.hdr
        csfile = h[1000000]
        if lastCsfile is None:
            lastCsfile = csfile

        if lastCsfile == csfile:
            # if this thing uses the same file as the last header,
            # adding the n,v,f to the job list is fine.
            jobList.append(h)
            continue
        else:
            lastCsfile = csfile
        yield jobList
        jobList = [h]
    if jobList:
        yield jobList

def doConaryInstall(method, id, intf, instPath):
    if flags.test:
	return

    if isinstance(method, conarymethods.ConaryRepositoryInstallMethod):
        # we handle conary repository installs differently
        return doConaryRepositoryInstall(method, id, intf, instPath)

    # set up install.log
    instLogName = instPath + '/root/install.log'
    try:
	iutil.rmrf (instLogName)
    except OSError:
	pass
    instLog = open(instLogName, "w+")
    instLogFd = instLog.fileno()

    # set up our syslogd
    if flags.setupFilesystems:
        # dont start syslogd if we arent creating filesystems
	syslogname = instLogName + '.syslog'
	try:
	    iutil.rmrf (syslogname)
	except OSError:
	    pass
	syslog.start(instPath, syslogname)
    else:
	syslogname = None

    pkgTimer = timer.Timer(start = 0)

    total = 0
    l = []
    csFiles = set()
    for p in id.grpset.hdrlist.values():
        if p.isSelected():
            l.append(p)
            total += (p[rpm.RPMTAG_SIZE] / 1024)
            csFiles.add(p.hdr[1000000])
    l.sort(packages.sortPackages)

    id.instProgress.setSizes(len(csFiles), total, 0)
    del csFiles
    id.instProgress.processEvents()

    cfg = method.cfg
    cfg.root = instPath
    cfg.threaded = False
    cfg.tempDir = instPath + '/var/tmp'
    util.settempdir(cfg.tempDir)

    client = conaryclient.ConaryClient(cfg)

    for jobList in _collapseJobs(l):
        # pick the package in the the jobList (if any)
        h = jobList[0]
        for j in jobList:
            flavorStr = deps.formatFlavor(j.nvf[2])
            if flavorStr:
                flavorStr = '[%s]' %flavorStr
            instLog.write('installing %s=%s%s\n'
                          %(j.nvf[0],
                            j.nvf[1].asString(),
                            flavorStr))
            if ':' in j.nvf[0]:
                continue
            h = j

        instLog.flush()
        # add in any sub-component sizes
        size = 0
        for j in jobList:
            size += j[rpm.RPMTAG_SIZE]
        h[rpm.RPMTAG_SIZE] = size

        id.instProgress.setPackage(h)
        id.instProgress.setPackageScale(0, 1)
        # do the install
        pkgTimer.start()
        downloadCb = id.instProgress.setPackageStatus
        while True:
            try:
                fn = method.getPackageFilename(h, pkgTimer,
                                               callback=downloadCb)
                break
            except FileCopyException:
                method.unmountCD()
                intf.messageWindow(_("Error"),
                    _("The package %s-%s-%s cannot be opened. This is due "
                      "to a missing file or perhaps a corrupt package.  "
                      "If you are installing from CD media this usually "
                      "means the CD media is corrupt, or the CD drive is "
                      "unable to read the media.\n\n"
                      "Press <return> to try again.") % (h['name'],
                                                         h['version'],
                                                         h['release']))

        cs = changeset.ChangeSetFromFile(fn)
        callback = InstallCallback(id.instProgress, pkgTimer)
        job = []
        for hdr in jobList:
            job.append((hdr.nvf[0], (None, None),
                                    (hdr.nvf[1], hdr.nvf[2]), False))

        # set up an update job by hand (this skips dep resolution)
        uJob = database.UpdateJob(client.db)
        csSource = trovesource.ChangesetFilesTroveSource(client.db)
        csSource.addChangeSet(cs, includesFileContents = True)
        uJob.getTroveSource().addChangeSet(cs, includesFileContents = True)
        uJob.setSearchSource(csSource)
        uJob.addJob(job)

        client.applyUpdate(uJob, replaceFiles = True,
                           tagScript = instPath + '/root/conary-tag-script',
                           localRollbacks = cfg.localRollbacks,
                           autoPinList = cfg.pinTroves,
                           callback = callback)
        method.unlinkFilename(fn)
        id.instProgress.setPackageScale(1, 1)
        id.instProgress.completePackage(h, pkgTimer)

        # explicitly delete the changeset so that the underlying file
        # will be closed.
        del cs
        del uJob
        del csSource

    id.instProgress = None
    conaryInstallPost(id, intf, instPath)
    method.filesDone()

# override packages.doInstall
packages.doInstall = doConaryInstall

# FIXME: this class exists simply to hold the info that is needed
# for the dep solver.  The repository, changeset, and conarycfg needed
# are stored in the install method, which isn't available to the
# checkDependencies function as called by dispatch.
class DepChecker:
    def __init__(self):
        self.cfg = None
        self.repos = None

    def setCfg(self, cfg):
        self.cfg = cfg

    def setRepos(self, repos):
        self.repos = repos

    def checkDependencies(self, dir, intf, disp, id, instPath):
        if dir == DISPATCH_BACK:
            return

        win = intf.waitWindow(_("Dependency Check"),
          _("Checking dependencies in packages selected for installation..."))

        l = []
        for p in id.grpset.hdrlist.pkgs.values():
            if not p.isSelected():
                continue
            n, v, f = p.hdr.nvf
            job = (n, (None, None), (v, f), False)
            l.append(job)

        cfg = copy.copy(self.cfg)
        cfg.root = ':memory:'
        cfg.dbPath = ':memory:'
        cfg.autoResolve = True
        client = conaryclient.ConaryClient(cfg)

        # use the (potentially local) repository from the instmethod
        client.repos = self.repos
        # FIXME: this should not be necessary -- conaryclient.resolve needs
        # to use the repos from the client, instead of caching it.  Once
        # the change is made in conary, this can be removed.
        client.resolver.repos = self.repos
        try:
            (updJob, suggMap) = client.updateChangeSet(l, resolveDeps = True,
                                                       recurse = False)
        except conaryclient.DepResolutionFailure, e:
            win.pop()
            log(str(e))
            intf.messageWindow('Unresolvable Dependencies',
                               str(e),
                               custom_icon = "error")
            return
        win.pop()

        if not suggMap:
            return

        win = intf.waitWindow(_("Dependency Check"),
                         _("Selecting dependencies to solve requirements..."))
        time.sleep(.5)
        for what, need in suggMap.iteritems():
            for item in need:
                for p in id.grpset.hdrlist.pkgs.values():
                    if p.hdr.nvf == item:
                        log('using %s to satisfy %s',
                            str(p.hdr.nvf), str(what))
                        p.select(isDep = 1)
        win.pop()

depchecker = DepChecker()

def checkDependencies(*args):
    global depchecker
    return depchecker.checkDependencies(*args)

packages.checkDependencies = checkDependencies

if __name__ == '__main__':
    import versions
    from deps import deps
    import conarycomps
    # test suite
    v = versions.VersionFromString('/local@rpl:test/1.0-1-1')
    f = deps.ThawDependencySet('')
    l = []
    hl = []
    hl.append(rpm.Header('foo', 'foo', v, f, 0, 0))
    hl.append(rpm.Header('foo', 'foo:runtime', v, f, 0, 0))
    hl.append(rpm.Header('foo', 'foo:lib', v, f, 0, 0))
    hl.append(rpm.Header('bar', 'bar', v, f, 0, 0))
    hl.append(rpm.Header('bar', 'bar:runtime', v, f, 0, 0))
    hl.append(rpm.Header('baz', 'baz:runtime', v, f, 0, 0))
    l = [ conarycomps.Package(h) for h in hl ]
    jobList = list(_collapseJobs(l))
    assert (len(jobList) == 3)
    assert (jobList == [ hl[0:3], hl[3:5], hl[5:6] ])

#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from datetime import datetime

from conary import conaryclient
from conary import versions

from mint.django_rest.rbuilder.inventory import models

import base

class VersionManager(base.BaseManager):
    """
    Class encapsulating all logic around versions, available updates, etc.
    """
    def get_software_versions(self, system):
        pass

    def delete_installed_software(self, system):
        system.installed_software.all().delete()

    @base.exposed
    def setInstalledSoftware(self, system, installed_versions):
        oldInstalled = dict((x.getNVF(), x)
            for x in system.installed_software.all())

        # Do the delta
        toAdd = []
        for installed_version in installed_versions:
            if isinstance(installed_version, basestring):
                trove = self.trove_from_nvf(installed_version)
            else:
                trove = installed_version
            nvf = trove.getNVF()
            isInst = oldInstalled.pop(nvf, None)
            if isInst is None:
                toAdd.append(trove)
        for trove in oldInstalled.itervalues():
            system.installed_software.remove(trove)
        for trove in toAdd:
            system.installed_software.add(self._trove(trove))
        system.save()

    def trove_from_nvf(self, nvf):
        n, v, f = conaryclient.cmdline.parseTroveSpec(nvf)
        f = str(f)

        thawed_v = versions.ThawVersion(v)
        version = models.Version()
        version.fromConaryVersion(thawed_v)
        version.flavor = f

        trove = models.Trove()
        trove.name = n
        trove.version = version
        trove.flavor = f
        return trove

    @classmethod
    def _trove(cls, trove):
        """
        If the trove is new, save it to the db, otherwise return the existing
        one
        """
        # First, make sure the flavor is part of the version object
        if not trove.version.flavor:
            trove.version.flavor = trove.flavor
        created, version = models.Version.objects.load_or_create(trove.version)
        trove.version = version
        created, trove = models.Trove.objects.load_or_create(trove)
        return trove

    def cache_available_update(self, nvf, update_nvf):
        trove = self.trove_from_nvf(nvf)
        update_trove = self.trove_from_nvf(update_nvf)
        available_update, created = models.AvailableUpdate.get_or_create(
            trove=trove, trove_available_update=update_trove)
        available_update.save()

    def clear_cached_updates(self, nvf):
        trove = self.trove_from_nvf(nvf)
        trove.available_updates.all().delete()

    def _get_conary_client(self):
        if self._cclient is None:
            self._cclient = self.rest_db.productMgr.reposMgr.getUserClient()
        return self._cclient
    cclient = property(_get_conary_client)

    def get_available_updates(self, nvf, force=False):
        one_day = datetime.timedelta(1)
        trove = self.trove_from_nvf(nvf)

        if trove.last_available_update_refresh > one_day or force:
            self.refresh_updates(nvf)

        return trove.available_updates.all()

    def refresh_updates(self, softwareVersions):
        content = []

        for trvName, trvVersion, trvFlavor in softwareVersions:
            nvfStrs = self._nvfToString((trvName, trvVersion, trvFlavor))
            cachedUpdates = self.systemMgr.getCachedUpdates(nvfStrs)

            if cachedUpdates is not None:
                for cachedUpdate in cachedUpdates:
                    content.append(self._availableUpdateModelFactory(
                                   (trvName, trvVersion, trvFlavor),
                                   cachedUpdate))
                    instance.setOutOfDate(True)
                # Add the current version as well.
                content.append(self._availableUpdateModelFactory(
                               (trvName, trvVersion, trvFlavor),
                               (trvName, trvVersion, trvFlavor)))
                continue

            # trvName and trvVersion are str's, trvFlavor is a
            # conary.deps.deps.Flavor.
            label = trvVersion.trailingLabel()

            # Search the label for the trove of the top level item.  It should
            # only (hopefully) return 1 result.
            troves = self.cclient.repos.findTroves(label,
                [(trvName, trvVersion, trvFlavor)])
            assert(len(troves) == 1)

            # findTroves returns a {} with keys of (name, version, flavor), values
            # of [(name, repoVersion, repoFlavor)], where repoVersion and
            # repoFlavor are rich objects with the repository metadata.
            repoVersion = troves[(trvName, trvVersion, trvFlavor)][0][1]
            repoFlavors = [f[0][2] for f in troves.values()]
            # We only asked for 1 flavor, only 1 should be returned.
            assert(len(repoFlavors) == 1)

            # getTroveVersionList searches a repository (NOT by label), for a
            # given name/flavor combination.
            allVersions = self.cclient.repos.getTroveVersionList(
                trvVersion.getHost(), {trvName:repoFlavors})
            # We only asked for 1 name/flavor, so we should have only gotten 1
            # back.
            assert(len(allVersions) == 1)
            # getTroveVersionList returns a dict with keys of name, values of
            # (version, [flavors]).
            allVersions = allVersions[trvName]

            newerVersions = {}
            for v, fs in allVersions.iteritems():
                # getTroveVersionList doesn't search by label, so we need to
                # compare the results to the label we're interested in, and make
                # sure the version is newer.
                if v.trailingLabel() == label and v > repoVersion:

                    # Check that at least one of the flavors found satisfies the
                    # flavor we're interested in.
                    satisfiedFlavors = []
                    for f in fs:
                        # XXX: do we want to use flavor or repoFlavor here?
                        # XXX: do we want to use stronglySatisfies here?
                        if f.satisfies(trvFlavor):
                            satisfiedFlavors.append(f)
                    if satisfiedFlavors:
                        newerVersions[v] = satisfiedFlavors

            if newerVersions:
                for ver, fs in newerVersions.iteritems():
                    for flv in fs:
                        content.append(self._availableUpdateModelFactory(
                                        (trvName, trvVersion, trvFlavor),
                                        (trvName, ver, flv)))
                        self.systemMgr.cacheUpdate(nvfStrs, self._nvfToString(
                                (trvName, ver, f)))
                instance.setOutOfDate(True)
            else:
                # Cache that no update was available
                self.systemMgr.cacheUpdate(nvfStrs, None)
                

            # Add the current version as well.
            content.append(self._availableUpdateModelFactory(
                            (trvName, trvVersion, trvFlavor),
                            (trvName, repoVersion, trvFlavor)))

            # Can only have one repositoryUrl set on the instance, so set it
            # if this is a top level group.
            if self._isTopLevelGroup([trvName,]):
                instance.setRepositoryUrl(
                    self._getRepositoryUrl(repoVersion.getHost()))

        instance.setAvailableUpdate(content)

        return instance

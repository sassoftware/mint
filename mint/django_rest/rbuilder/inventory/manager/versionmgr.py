#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import datetime
from dateutil import tz

from conary import conaryclient
from conary import versions

from mint.django_rest.rbuilder.inventory import models

import base

class VersionManager(base.BaseManager):
    """
    Class encapsulating all logic around versions, available updates, etc.
    """
    
    def __init__(self, *args, **kwargs):
        base.BaseManager.__init__(self, *args, **kwargs)
        self._cclient = None

    def get_software_versions(self, system):
        pass

    def delete_installed_software(self, system):
        system.installed_software.all().delete()

    def _diffVersions(self, system, new_versions):
        oldInstalled = dict((x.getNVF(), x)
            for x in system.installed_software.all())

        # Do the delta
        toAdd = []
        for new_version in new_versions:
            if isinstance(new_version, basestring):
                trove = self.trove_from_nvf(new_version)
            else:
                trove = new_version
            nvf = trove.getNVF()
            isInst = oldInstalled.pop(nvf, None)
            if isInst is None:
                toAdd.append(trove)

        return oldInstalled, toAdd

    @base.exposed
    def setInstalledSoftware(self, system, new_versions):
        oldInstalled, toAdd = self._diffVersions(system, new_versions)
        for trove in oldInstalled.itervalues():
            system.installed_software.remove(trove)
        for trove in toAdd:
            system.installed_software.add(trove)
            self.set_available_updates(trove)
        system.save()

    @base.exposed
    def updateInstalledSoftware(self, system, new_versions):
        oldInstalled, toAdd = self._diffVersions(system, new_versions)
        sources = []
        for nvf in oldInstalled.keys():
            n, v, f = nvf
            sources.append("%s=%s[%s]" % (n, str(v), str(f)))
        for new_version in new_versions:
            n, v, f = new_version.getNVF()
            sources.append("%s=%s[%s]" % (n, str(v), str(f)))
        self.mgr.scheduleSystemApplyUpdateEvent(system, sources)

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
        # XXX unused
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

    def get_conary_client(self):
        if self._cclient is None:
            self._cclient = self.rest_db.productMgr.reposMgr.getUserClient()
        return self._cclient

    @base.exposed
    def set_available_updates(self, trove, force=False):
        one_day = datetime.timedelta(1)

        # Hack to make sure utc is set as the timezone on
        # last_available_update_refresh.
        if trove.last_available_update_refresh is not None:
            trove.last_available_update_refresh = \
                trove.last_available_update_refresh.replace(tzinfo=tz.tzutc())

        if force or trove.last_available_update_refresh is None:
            self.refresh_available_updates(trove)
            trove.last_available_update_refresh = \
                datetime.datetime.now(tz.tzutc())
            trove.save()
            return

        if (trove.last_available_update_refresh + one_day) < \
            datetime.datetime.now(tz.tzutc()):
            self.refresh_available_updates(trove)
            trove.last_available_update_refresh = \
                datetime.datetime.now(tz.tzutc())
            trove.save()

    def refresh_available_updates(self, trove):
        self.cclient = self.get_conary_client()
        # trvName and trvVersion are str's, trvFlavor is a
        # conary.deps.deps.Flavor.
        trvName = trove.name
        trvVersion = trove.version.conaryVersion
        trvFlavor = trove.getFlavor()
        trvLabel = trove.getLabel()

        # Search the label for the trove of the top level item.  It should
        # only (hopefully) return 1 result.
        troves = self.cclient.repos.findTroves(trvLabel,
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
        # {version: [flavors]}.
        allVersions = allVersions[trvName]

        newerVersions = {}
        for v, fs in allVersions.iteritems():
            # getTroveVersionList doesn't search by label, so we need to
            # compare the results to the label we're interested in, and make
            # sure the version is newer.
            if v.trailingLabel() == trvLabel and v > repoVersion:

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
                    new_version = models.Version()
                    new_version.fromConaryVersion(ver)
                    new_version.flavor = str(flv)
                    new_version = models.Version.objects.load(new_version)
                    new_version.save()
                    trove.available_updates.add(new_version)

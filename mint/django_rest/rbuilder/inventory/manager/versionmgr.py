#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging
from StringIO import StringIO

from smartform import descriptor
from smartform import descriptor_errors

from conary import conaryclient, versions
from conary import trove as conarytrove
from conary.errors import RepositoryError

from django.core.exceptions import ObjectDoesNotExist

from mint.django_rest import timeutils
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.projects.models import Project, ProjectVersion
from mint.rest.errors import ProductNotFound, ProductVersionNotFound

log = logging.getLogger(__name__)
exposed = basemanager.exposed

class VersionManager(basemanager.BaseManager):
    """
    Class encapsulating all logic around versions, available updates, etc.
    """
    
    def __init__(self, *args, **kwargs):
        basemanager.BaseManager.__init__(self, *args, **kwargs)
        self._cclient = None

    def get_software_versions(self, system):
        pass

    @classmethod
    def _flavor(cls, flavor):
        if flavor is None:
            return ''
        return str(flavor)

    def getStages(self, hostname, majorVersionName):
        stages = self.restDb.getProductVersionStages(hostname,
            majorVersionName)
        return stages.stages

    def setStage(self, system, trove):
        if not trove.is_top_level:
            return

        hostname = trove.getHost()

        label = trove.version.conaryVersion.trailingLabel()
        tag = label.getLabel()

        # NOTE: This assumes that repoName and the tag always match.
        repoName = hostname.split('.')[0]
        rparts = repoName.split('-')
        tparts = tag.split('-')
        majorVersionName = tparts[len(rparts)]

        stages = self.getStages(hostname,
            majorVersionName)
        stage = [s for s in stages \
            if s.label == trove.version.label]
        if not stage:
            return

        stage = stage[0]
        try:
            project = Project.objects.get(repository_hostname=hostname)
            majorVersion = ProjectVersion.objects.get(project=project,
                name=majorVersionName)
        except ObjectDoesNotExist:
            return

        stage, created = models.Stage.objects.get_or_create(project_branch=majorVersion,
            label=trove.version.label, name=stage.name, project=project)

        system.project_branch_stage = stage
        system.project_branch = majorVersion
        system.project = project

    def trove_from_nvf(self, nvf):
        n, v, f = conaryclient.cmdline.parseTroveSpec(nvf)
        f = self._flavor(f)
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
        # Need to call save again so that is_top_level gets reset
        trove.save()
        return trove

    def cache_available_update(self, nvf, update_nvf):
        trove = self.trove_from_nvf(nvf)
        update_trove = self.trove_from_nvf(update_nvf)
        available_update, created = models.AvailableUpdate.get_or_create(
            trove=trove, trove_available_update=update_trove)
        available_update.save()

    def get_conary_client(self):
        if self._cclient is None:
            self._cclient = self.restDb.productMgr.reposMgr.getUserClient()
        return self._cclient

    def _checkCacheExpired(self, trove):
        one_day = timeutils.timedelta(1)
        return (trove.last_available_update_refresh + one_day) < timeutils.now()

    # FIXME: is this still used?  -- MPD
    def set_available_updates(self, trove, force=False):

        # Hack to make sure utc is set as the timezone on
        # last_available_update_refresh.
        if trove.last_available_update_refresh is not None:
            trove.last_available_update_refresh = \
                trove.last_available_update_refresh.replace(tzinfo=timeutils.TZUTC)

        if force or \
           trove.last_available_update_refresh is None or \
           self._checkCacheExpired(trove):

            refreshed = self.refresh_available_updates(trove)
            if refreshed:
                trove.last_available_update_refresh = timeutils.now()
                trove.save()

    # NOTE: this system should no longer be used, but not positive -- MPD
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
        try:
            troves = self.cclient.repos.findTroves(trvLabel,
                [(trvName, trvVersion, trvFlavor)])
        except RepositoryError, e:
            log.error("Error contacting repository to look for available " + \
                "updates for %s=%s[%s]" % (trvName, trvLabel, trvFlavor))
            log.error(e)
            return False
        except ProductNotFound, e:
            log.error("Permission error querying repository for %s=%s[%s]" \
                % (trvName, trvLabel, trvFlavor))
            log.error(e)
            return False
        assert(len(troves) == 1)

        trove.available_updates.clear()
        trove.out_of_date = False

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

        availableVersions = {}
        for v, fs in allVersions.iteritems():
            # getTroveVersionList doesn't search by label, so we need to
            # compare the results to the label we're interested in.
            if v.trailingLabel() == trvLabel:

                # Check that at least one of the flavors found satisfies the
                # flavor we're interested in.
                satisfiedFlavors = []
                for f in fs:
                    # XXX: do we want to use flavor or repoFlavor here?
                    # XXX: do we want to use stronglySatisfies here?
                    if f.satisfies(trvFlavor):
                        satisfiedFlavors.append(f)
                if satisfiedFlavors:
                    availableVersions[v] = satisfiedFlavors

        if availableVersions:
            for ver, fs in availableVersions.iteritems():
                for flv in fs:
                    new_version = models.Version()
                    new_version.fromConaryVersion(ver)
                    new_version.flavor = str(flv)
                    created, new_version = \
                        models.Version.objects.load_or_create(new_version)
                    new_version.save()
                    trove.available_updates.add(new_version)

                    # Set out of date flag on True if there are newer versions
                    # available.
                    if ver > repoVersion:
                        trove.out_of_date = True

        # Always add the current version as an available update, this is so
        # that remediation will work.
        trove.available_updates.add(trove.version)

        return True


    # FIMXE: this from old mint/rest/api
    def _getTroveConfigDescriptor(self, name, version, flavor):

        repos = self.get_conary_client().repos
        trvList = repos.getTroves([(name, version, flavor)])

        referencedByDefault = []
        for trv in trvList:
            referencedByDefault += [ nvf for nvf, byDefault, strongRef in
                trv.iterTroveListInfo() if byDefault ]

        # Get properties sorted by package name.
        properties = repos.getTroveInfo(conarytrove._TROVEINFO_TAG_PROPERTIES,
            sorted(referencedByDefault, cmp=lambda x, y: cmp(x[0], y[0])))

        configFields = []
        for propSet in properties:
            if propSet is None:
                continue
            for property in propSet.iter():
                xml = property.definition()
                desc = descriptor.BaseDescriptor()

                try:
                    desc.parseStream(StringIO(xml))

                # Ignore any descriptors that don't parse.
                except descriptor_errors.Error:
                    continue

                configFields.extend(desc.getDataFields())

        return configFields

    # this code originally from mint/rest/api
    def _getConfigDescriptor(self, name, version, flavor):

        # FIXME: import descriptor
        desc = descriptor.ConfigurationDescriptor()
        desc.setDisplayName('Configuration Descriptor')
        desc.addDescription('Configuration Descriptor')

        newFields = self._getTroveConfigDescriptor(name, version, flavor)
        if not newFields:
            return ''

        fields = desc.getDataFields()
        fields.extend(newFields)

        out = StringIO()
        desc.serialize(out, validate=False)
        out.seek(0)

        return out.read()
   
    @exposed
    def getConfigurationDescriptor(self, system):
        """
        Generate config descriptor for all top level items on a system.
        """

        if system.latest_survey is None:
            return '<configuration></configuration>'
    
        # find the appliance group from the survey
        # what if multiple top levels with config descriptors?
        # UI doesn't support, so not worrying about it for now
        packages = system.latest_survey.conary_packages
        for conary_package in packages.all():
            info = conary_package.conary_package_info
            name = info.name
            if name.startswith("group-") and name.find("-appliance") != -1:
                res = self._getConfigDescriptor(info.name, info.version, info.flavor)
                return res
              
        # shouldn't ever get here unless you migrated to something weird, in which 
        # case (FIXME) just present the empty one and maybe log?
        raise Exception("could not find group-X-appliance")                               


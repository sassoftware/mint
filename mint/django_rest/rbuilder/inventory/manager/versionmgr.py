#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import datetime
import itertools
import logging
import xml
from dateutil import tz
from xml.dom import minidom

from conary import conaryclient, versions
from conary import trove as conarytrove
from conary.errors import RepositoryError

from django.core.exceptions import ObjectDoesNotExist

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

    def delete_installed_software(self, system):
        system.installed_software.all().delete()

    def _diffVersions(self, system, new_versions):
        oldInstalled = dict((x.getNVF(), x)
            for x in system.installed_software.all())

        # Do the delta
        toAdd = []
        newInstalled = []
        for new_version in new_versions:
            if isinstance(new_version, basestring):
                trove = self.trove_from_nvf(new_version)
            else:
                trove = new_version
            nvf = trove.getNVF()
            isInst = oldInstalled.pop(nvf, None)
            if isInst is None:
                toAdd.append(self._trove(trove))
            newInstalled.append(nvf)

        return oldInstalled, newInstalled, toAdd

    @exposed
    def setInstalledSoftware(self, system, new_versions):
        oldInstalled, newInstalled, toAdd = \
            self._diffVersions(system, new_versions)
        for trove in oldInstalled.itervalues():
            system.installed_software.remove(trove)
        for trove in toAdd:
            system.installed_software.add(trove)
            try:
                self.setStage(system, trove)
            except ProductVersionNotFound:
                system.project = None
        for trove in system.installed_software.all():
            self.set_available_updates(trove, force=True)
        system.save()

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

        system.stage = stage
        system.project_branch = majorVersion
        system.project = project

    @exposed
    def updateInstalledSoftware(self, system_id, new_versions):
        system = models.System.objects.get(pk=system_id)
        troveSpecs = ["%s=%s[%s]" % x.getNVF()
            for x in new_versions ]
        if troveSpecs:
            msg = "Initiating software update to: %s" % (
                ', '.join(troveSpecs), )
        else:
            msg = "Initiating software update, deleting everything"
        self.mgr.log_system(system, msg)
        oldInstalled, newInstalled, toAdd = \
            self._diffVersions(system, new_versions)
        sources = []
        for nvf in newInstalled:
            n, v, f = nvf
            sources.append("%s=%s[%s]" % (n, str(v), self._flavor(f)))
        self.mgr.scheduleSystemApplyUpdateEvent(system, sources)

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

    @exposed
    def refreshCachedUpdates(self, name, label):
        troves = models.Trove.objects.filter(name=name, 
            version__label=label)
        for trove in troves:
            self.set_available_updates(trove, force=True)

    def get_conary_client(self):
        if self._cclient is None:
            self._cclient = self.restDb.productMgr.reposMgr.getUserClient()
        return self._cclient

    def _checkCacheExpired(self, trove):
        one_day = datetime.timedelta(1)
        return (trove.last_available_update_refresh + one_day) < \
            datetime.datetime.now(tz.tzutc())

    @exposed
    def set_available_updates(self, trove, force=False):

        # Hack to make sure utc is set as the timezone on
        # last_available_update_refresh.
        if trove.last_available_update_refresh is not None:
            trove.last_available_update_refresh = \
                trove.last_available_update_refresh.replace(tzinfo=tz.tzutc())

        if force or \
           trove.last_available_update_refresh is None or \
           self._checkCacheExpired(trove):

            refreshed = self.refresh_available_updates(trove)
            if refreshed:
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

    @exposed
    def getConfigurationDescriptor(self, system):
        
        # remove this when you want it to work for real
        #return open('/srv/www/html/config/config_pony.xml').read()
        
        # Create master configuration DOM and add configDicts to dataFields
        impl = minidom.getDOMImplementation()
        newdoc = impl.createDocument(None, 'configuration_descriptor', None)
        top = newdoc.documentElement
        metadata = newdoc.createElement('metadata')
        descriptor = newdoc.createElement('descriptor')
        dataFields = newdoc.createElement('dataFields')
        top.appendChild(descriptor)
        descriptor.appendChild(dataFields)
        descriptor.appendChild(metadata)
        # We are just adding all 
        confDict = {}
        # WARNING: No control over ordering! Last to iterate will override prior field keys
        for trove in system.installed_software.all():
            confDict.update(self._getTroveConfigDescriptor(trove))
        #trove = None
        #confDict.update(self._getTroveConfigDescriptor(trove))
        for x in confDict:
            dataFields.appendChild(confDict[x])
        # WARNING: If we reconcile provides/requires here, then we can easily get to
        #          unresolved state if user adds a trove with configuration descriptor
        #          with unresolved config deps
        # Should we only provide config for the group or all troves returned?
        # Where should the config dep resolution happen, here or in the _getTroveConfigDescriptor?
        
        # (03:07:56 PM) slagle: but, if you wanted to tack on an id attribute, you would do it in InventorySystemConfigurationDescriptorServices in views.py
        return top.toxml()

    def _getTroveConfigDescriptor(self, trove):
        client = self.get_conary_client()
        repos = client.getRepos()
        n, v, f = trove.getNVF()

        trvList = repos.getTroves([(n, v, f)])

        referencedByDefault = []
        for trv in trvList:
            referencedByDefault += [ nvf for nvf, byDefault, strongRef in
                trv.iterTroveListInfo() if byDefault ]

        properties = repos.getTroveInfo(conarytrove._TROVEINFO_TAG_PROPERTIES,
            referencedByDefault)

        configDict = {}
        for propSet in properties:
            if propSet is None:
                continue
            for singleProperty in propSet.iter():
                troveXml = singleProperty.definition()
                try: 
                    doc = minidom.parseString(troveXml)
                except xml.parsers.expat.ExpatError:
                    continue

                for field in doc.getElementsByTagName('field'):
                    name = field.getElementsByTagName('name')[0].lastChild.data
                    configDict[name] = field

        return configDict

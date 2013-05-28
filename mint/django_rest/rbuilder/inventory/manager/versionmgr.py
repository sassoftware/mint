#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging

from conary import trovetup
from conary.errors import ParseError

from rpath_tools.client.utils.config_descriptor_cache import ConfigDescriptorCache

from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.manager import basemanager

log = logging.getLogger(__name__)
exposed = basemanager.exposed

class VersionManager(basemanager.BaseManager):
    """
    Class encapsulating all logic around versions, available updates, etc.
    """

    def __init__(self, *args, **kwargs):
        basemanager.BaseManager.__init__(self, *args, **kwargs)
        self._cclient = None

    def get_conary_client(self):
        if self._cclient is None:
            try:
                self._cclient = self.restDb.productMgr.reposMgr.getUserClient()
            except:
                # needs to be mocked in tests
                return None
        return self._cclient

    @exposed
    def getSystemConfigurationDescriptor(self, system):
        """
        Generate config descriptor for all top level items on a system.
        """

        descr = self.getSystemConfigurationDescriptorObject(system)
        if descr is None:
            return '<configuration/>'
        return descr.toxml()

    @exposed
    def troveTupleFactory(self, *args, **kwargs):
        # Eek. One class doesn't parse the flavor, the other doesn't
        # parse the version
        return trovetup.TroveTuple(trovetup.TroveSpec(*args, **kwargs))

    @exposed
    def getSystemConfigurationDescriptorObject(self, system):
        if isinstance(system, (int, basestring)):
            system = models.System.objects.get(system_id=system)
        # what if multiple top levels with config descriptors?
        # UI doesn't support, so not worrying about it for now
        items = system.observed_top_level_items.all()
        for item in items:

            try:
                truple = trovetup.TroveTuple(item.trove_spec)
            except ParseError:
                continue

            cclient = self.get_conary_client()
            if not cclient:
                break

            desc = self.getConfigurationDescriptorFromTrove(truple,
                conaryClient=cclient)
            if desc is not None:
                return desc

        log.warn('could not find configuration descriptor for %s' % system.name)
        return None

    @exposed
    def getConfigurationDescriptorFromTrove(self, trvTup, conaryClient=None):
        if conaryClient is None:
            conaryClient = self.get_conary_client()
            if conaryClient is None:
                return None

        repos = conaryClient.getRepos()
        desc = ConfigDescriptorCache(repos).getDescriptor(trvTup)
        if desc is None or desc == '':
            return None

        desc.setDisplayName('Configuration Descriptor')
        desc.addDescription('Configuration Descriptor')
        desc.setRootElement('configuration')

        return desc

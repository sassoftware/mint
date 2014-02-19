#
# Copyright (c) SAS Institute Inc.
#

import logging

from conary import trovetup

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
        return None

    @exposed
    def getConfigurationDescriptorFromTrove(self, trvTup, conaryClient=None):
        return None

#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import os
import sys
import weakref

from conary import versions

from rpath_common.proddef import api1 as proddef

from mint.rest import errors
from mint.rest.api import models
from mint.lib import persistentcache


class PlatformManager(object):
    def __init__(self, cfg, db):
        self.cfg = cfg
        self.db = db
        cacheFile = os.path.join(self.cfg.dataPath, 'data', 
                                 'platformName.cache')
        self.platformCache = PlatformNameCache(cacheFile, 
                                               db.productMgr.reposMgr)

    def _iterPlatforms(self):
        apnLength = len(self.cfg.availablePlatformNames)
        for i, platformLabel in enumerate(self.cfg.availablePlatforms):
            platformName = self.platformCache.get(platformLabel)
            enabled = bool(platformName)
            if not enabled:
                # Fall back to the platform label, if
                # self.cfg.availablePlatformNames is incomplete
                platformName = platformLabel
                if i < apnLength:
                    platformName = self.cfg.availablePlatformNames[i]
            yield platformLabel, platformName, enabled

    def listPlatforms(self):
        availablePlatforms = []
        for platformLabel, platformName, enabled in self._iterPlatforms():
            plat = models.Platform(label = platformLabel,
                                   platformName = platformName,
                                   enabled = enabled)
            availablePlatforms.append(plat)
        return models.Platforms(availablePlatforms)

class PlatformNameCache(persistentcache.PersistentCache):

    def __init__(self, cacheFile, reposMgr):
        persistentcache.PersistentCache.__init__(self, cacheFile)
        self._reposMgr = weakref.ref(reposMgr)
        self._cclient = reposMgr.getGenericConaryClient()

    def _refresh(self, labelStr):
        try:
            hostname = versions.Label(labelStr).getHost()
            # we require that the first section of the label be unique
            # across all repositories we access.
            hostname = hostname.split('.')[0]
            client = self._cclient
            try:
                isExternal = self._reposMgr()._isProductExternal(hostname)
                if not isExternal:
                    client = self._reposMgr().getInternalConaryClient(hostname)
            except errors.ProductNotFound:
                pass
            platDef = proddef.PlatformDefinition()
            platDef.loadFromRepository(client, labelStr)
            return platDef.getPlatformName()
        except Exception, e:
            # Swallowing this exception allows us to have a negative
            # cache entries.  Of course this comes at the cost
            # of swallowing exceptions...
            print >> sys.stderr, "failed to lookup platform definition on label %s: %s" % (labelStr, str(e))
            sys.stderr.flush()
            return None

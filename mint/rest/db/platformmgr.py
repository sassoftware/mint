#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import os
import sys
import weakref

from conary import versions

from rpath_proddef import api1 as proddef

from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import manager
from mint.lib import persistentcache

class PlatformManager(manager.Manager):
    def __init__(self, cfg, db, auth):
        manager.Manager.__init__(self, cfg, db, auth)
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

    def _platformModelFactory(self, *args, **kw):
        return models.Platform(platformId=kw['platformId'],
                               label=kw['label'],
                               platformName=kw['platformName'],
                               hostname=kw['hostname'],
                               enabled=kw['enabled'],
                               configurable=kw['configurable'])


    def listPlatforms(self, filterPlatformId=None):
        availablePlatforms = []
        dbPlatforms = self._listPlatformsFromDB(filterPlatformId)
        for platformLabel, platformName, enabled in self._iterPlatforms():
            if dbPlatforms.has_key(platformLabel):
                platformId = dbPlatforms[platformLabel]['platformId']
                configurable = dbPlatforms[platformLabel]['configurable']
            else:
                # TODO: Something meaningful.
                platformId = '0'
                configurable = 0
                pass
            plat = self._platformModelFactory(platformId=platformId,
                        label=platformLabel, platformName=platformName,
                        hostname=platformLabel.split('.')[0],
                        enabled=enabled, configurable=configurable)
            plat.sources = self.listPlatformSources(platformId)                        

            if filterPlatformId and \
                filterPlatformId == platformId:
                return plat
                
            availablePlatforms.append(plat)
        return models.Platforms(availablePlatforms)

    def getPlatform(self, platformId):
        return self.listPlatforms(platformId)

    def getSourceDescriptorConfig(self, platformId):
        plat = self.getPlatform(platformId)

        desc = models.Description(desc='Configure %s' % plat.platformName)
        metadata = models.Metadata(displayName=plat.platformName,
                    descriptions=[desc])

        dFields = []
        p0 = models.Prompt(desc='Your RHN Username')
        f0 = models.DescriptorField(name='username',
                                   required=True,
                                   descriptions=[models.Description(desc='Username')],
                                   prompt=p0,
                                   type='str')
        dFields.append(f0)                                   
        p1 = models.Prompt(desc='Your RHN Password')
        f1 = models.DescriptorField(name='password',
                                   required=True,
                                   descriptions=[models.Description(desc='Password')],
                                   prompt=p1,
                                   type='str',
                                   password=True)
        dFields.append(f1)                                   
        dataFields = models.DataFields(dFields)

        descriptor = models.descriptorFactory(metadata=metadata,
                        dataFields=dataFields)

        return descriptor
           
    def _listPlatformsFromDB(self, platformId=None):
        cu = self.db.cursor()
        sql = """
            SELECT
                platforms.platformId,
                platforms.platformLabel,
                platforms.configurable
            FROM
                platforms
        """

        if platformId:
            sql += ' WHERE platforms.platformId = %s' % platformId

        cu.execute(sql)

        results = {}
        for row in cu:
            results[row['platformLabel']] = \
                dict(platformId=str(row['platformId']),
                     configurable=row['configurable'])

        return results
    
    def _getPlatformSourceData(self, platformSourceId):
        sql = """
            SELECT
                platformSourceData.name,
                platformSourceData.value
            FROM
                platformSourceData
            WHERE
                platformSourceData.platformSourceId = ?
        """
        cu = self.db.cursor()
        cu.execute(sql, platformSourceId)
        return cu

    def _platformSourceModelFactory(self, row):
        plat = models.Source(
                        platformSourceId=str(row['platformSourceId']),
                        platformSourceName=row['platformSourceName'],
                        platformId=str(row['platformId']))

        data = self._getPlatformSourceData(row['platformSourceId'])

        for row in data:
            setattr(plat, row['name'], row['value'])

        return plat

    def listPlatformSources(self, platformId, filterPlatformSourceId=None):
        cu = self.db.cursor()

        sql = """
            SELECT
                platformSources.platformSourceId,
                platformSources.platformSourceName,
                platforms.platformId
            FROM
                platforms,
                platformSources
            WHERE
                platformSources.platformId = platforms.platformId
                and platforms.platformId = ?
        """

        if filterPlatformSourceId:
            sql = sql + ' AND platformSources.platformSourceId = %s' % \
                filterPlatformSourceId

        cu.execute(sql, platformId)

        ret = []
        for row in cu:
            plat = self._platformSourceModelFactory(row)
            ret.append(plat)

        if filterPlatformSourceId:
            return ret[0]
        else:
            platformSources = models.Sources()
            platformSources.sources = ret
            return platformSources


class PlatformNameCache(persistentcache.PersistentCache):
    def __init__(self, cacheFile, reposMgr):
        persistentcache.PersistentCache.__init__(self, cacheFile)
        self._reposMgr = weakref.ref(reposMgr)

    def _refresh(self, labelStr):
        try:
            client = self._reposMgr().getAdminClient()
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

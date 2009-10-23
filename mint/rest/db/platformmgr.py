#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import os
import sys
import weakref
import xmlrpclib

from conary import versions
from conary.lib import util

from mint import mint_error
from mint.lib import persistentcache
from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import manager

from rpath_proddef import api1 as proddef

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
                               configurable=kw['configurable'],
                               platformMode=kw['mode'])

    def _createPlatformInDB(self, platformLabel, configurable, mode):
        platformId = self.db.db.platforms.new(label=platformLabel,
                                        configurable=configurable, mode=mode)
        return str(platformId)                                        

    def listPlatforms(self, filterPlatformId=None):
        availablePlatforms = []
        dbPlatforms = self._listPlatformsFromDB()
        for platformLabel, platformName, enabled in self._iterPlatforms():
            if dbPlatforms.has_key(platformLabel):
                platformId = dbPlatforms[platformLabel]['platformId']
                configurable = dbPlatforms[platformLabel]['configurable']
                mode = dbPlatforms[platformLabel]['mode']
            else:
                # Create the platform in the db
                # Configurable by default.
                configurable = 1
                # Proxied by default.
                mode = 'proxied'
                platformId = self._createPlatformInDB(platformLabel, 
                                configurable, mode)

            # TODO: remove this once platforms are not tightly tied to sources
            # just here now to trigger a create of the configured sources
            if platformLabel in self.cfg.platformSourceLabels:
                self.listPlatformSources()

            plat = self._platformModelFactory(platformId=platformId,
                        label=platformLabel, platformName=platformName,
                        hostname=platformLabel.split('.')[0],
                        enabled=enabled, configurable=configurable, mode=mode)
            plat.sources = self.listPlatformSources(platformId)                        

            if filterPlatformId and \
                filterPlatformId == platformId:
                return plat
                
            availablePlatforms.append(plat)
        return models.Platforms(availablePlatforms)

    def getPlatform(self, platformId):
        return self.listPlatforms(platformId)

    def getConfigDescriptor(self, platformSourceShortName):
        sourceId = \
            self.db.db.platformSources.getIdFromShortName(platformSourceShortName)
        source = self.db.db.platformSources.get(sourceId)            
        desc = models.Description(desc='Configure %s' % source['name'])
        metadata = models.Metadata(displayName=source['name'],
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
                platforms.label,
                platforms.configurable,
                platforms.mode
            FROM
                platforms
        """

        if platformId:
            sql += ' WHERE platforms.platformId = %s' % platformId

        cu.execute(sql)

        results = {}
        for row in cu:
            results[row['label']] = \
                dict(platformId=str(row['platformId']),
                     configurable=row['configurable'],
                     mode=row['mode'])

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
        plat = models.PlatformSource(
                        platformSourceId=str(row['platformSourceId']),
                        name=row['name'],
                        platformId=str(row['platformId']),
                        shortName=row['shortName'],
                        defaultSource=row['defaultSource'],
                        orderIndex=row['orderIndex'])

        data = self._getPlatformSourceData(row['platformSourceId'])

        for row in data:
            setattr(plat, row['name'], row['value'])

        return plat

    def _createConfiguredSources(self, sources):
        shortNames = [source['shortname'] for source in sources]
        for i, configShortName in enumerate(self.cfg.platformSources):
            if configShortName not in shortNames:
                # TODO: create sources independent of platforms
                source = models.PlatformSource(shortName=configShortName,
                                       sourceUrl=self.cfg.platformSourceUrls[i],
                                       name=self.cfg.platformSourceNames[i],
                                       defaultSource='1',
                                       orderIndex='0')
                # TODO: fix once we have platform types
                try:
                    platformId = self.db.db.platforms.getIdByColumn('label',
                                    self.cfg.platformSourceLabels[i])
                except mint_error.ItemNotFound:
                    return

                self.createPlatformSource(platformId, source)

    def listPlatformSources(self, platformId=None, filterPlatformSourceShortName=None):

        if filterPlatformSourceShortName:
            filterPlatformSourceId = \
                self.db.db.platformSources.getIdFromShortName(filterPlatformSourceShortName)
        else:
            filterPlatformSourceId = None

        cu = self.db.cursor()

        sql = """
            SELECT
                platformSources.platformSourceId,
                platformSources.name,
                platformSources.shortName,
                platformSources.defaultSource,
                platformSources.orderIndex,
                platforms.platformId
            FROM
                platforms,
                platformSources
            WHERE
                platformSources.platformId = platforms.platformId
        """

        if platformId:
            sql = sql + ' AND platforms.platformId = %s' % platformId

        if filterPlatformSourceId:
            sql = sql + ' AND platformSources.platformSourceId = %s' % \
                filterPlatformSourceId

        cu.execute(sql)

        if not platformId and not filterPlatformSourceId:
            self._createConfiguredSources(cu)
            cu.execute(sql)

        ret = []
        for row in cu:
            plat = self._platformSourceModelFactory(row)
            ret.append(plat)

        if filterPlatformSourceId:
            return ret[0]
        else:
            platformSources = models.Sources()
            platformSources.platformSource = ret
            return platformSources

    def getPlatformSource(self, platformSourceShortName):
        return self.listPlatformSources(None, platformSourceShortName)

    def getPlatformStatus(self, platformId):
        pass

    def getPlatformSourceStatus(self, platformSourceShortName):
        platformSourceId = \
            self.db.db.platformSources.getIdFromShortName(platformSourceShortName)
        platformSource = self.getPlatformSource(platformSourceShortName)
        if not platformSource.username or \
           not platformSource.password or \
           not platformSource.sourceUrl:
            status = models.PlatformSourceStatus(connected=False, valid=False, 
                message="Username, password, and source url must be provided to check a source's status.")
        else:
            ret = self._checkRHNSourceStatus(platformSource.sourceUrl,
                        platformSource.username, platformSource.password)
            status = models.PlatformSourceStatus(connected=ret[0],
                                valid=ret[1], message=ret[2])

        return status

    def _checkRHNSourceStatus(self, url, username, password):
        if url.endswith('/'):
            url = url[:-1]
        url = "%s/rpc/api" % url
        s = util.ServerProxy(url)
        try:
            s.auth.login(username, password)
            return (True, True, 'Validated Successfully.')
        except xmlrpclib.Fault, e:
            return (True, False, e.faultString)

    def updatePlatformSource(self, platformId, platformSourceShortName, source):
        platformSourceId = \
            self.db.db.platformSources.getIdFromShortName(platformSourceShortName)
        cu = self.db.cursor()
        updSql = """
        UPDATE platformSourceData
        SET value='%s'
        WHERE 
            name='%s'
            and platformSourceId = ?
        """
        insSql = """
        INSERT INTO platformSourceData
        VALUES (?, '%s', '%s', 3)
        """

        oldSource = self.getPlatformSource(platformSourceShortName)

        for field in ['username', 'password', 'sourceUrl']:
            newVal = getattr(source, field)
            if getattr(oldSource, field) != newVal:
                row = cu.execute(updSql % (newVal, field), platformSourceId)
                if not row:
                    cu.execute(insSql % (field, newVal), platformSourceId)

        return self.getPlatformSource(platformSourceShortName)                    

    def updatePlatform(self, platformId, platform):
        cu = self.db.cursor()
        sql = """
        UPDATE platforms
        SET mode='%s'
        WHERE
            platformId=?
        """

        cu.execute(sql % platform.platformMode, platformId)
        return self.getPlatform(platformId)

    def createPlatformSource(self, platformId, source):
        try:
            platformSourceId = self.db.db.platformSources.new(
                    platformId=platformId, name=source.name,
                    shortName=source.shortName,
                    defaultSource=source.defaultSource,
                    orderIndex=source.orderIndex)
        except mint_error.DuplicateItem, e:
            raise e

        cu = self.db.cursor()
        sql = """
        INSERT INTO platformSourceData
        VALUES (%s, '%s', '%s', 3)
        """

        for field in ['username', 'password', 'sourceUrl']:
            value = getattr(source, field, None)
            if value:
                cu.execute(sql % (platformSourceId, field, value))

        return self.getPlatformSource(source.shortName)            

    def deletePlatformSource(self, platformShortName):
        platformSourceId = \
            self.db.db.platformSources.getIdFromShortName(platformSourceShortName)
        self.db.db.platformSources.delete(platformSourceId)

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

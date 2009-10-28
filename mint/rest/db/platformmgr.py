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

    def _iterConfigPlatforms(self):
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
            
            # TODO: remove this, just for testing until types are in platform
            # defn.
            # if i == 1:
                # types = ['blue',]
            # else:
                # types = ['red',]
            if 'pnalv' in platformLabel or 'localhost' in platformLabel or 'rhelrepo' in platformLabel:
                types = ['rhn',]
            else:
                types = []

            yield platformLabel, platformName, enabled, types

    def _getConfigPlatforms(self, platformLabel=None):
        plats = {}
        for pLabel, pName, enabled, sourceTypes in self._iterConfigPlatforms():
            if pLabel == platformLabel:
                plats = {}
                plats[pLabel] = dict(name=pName, enabled=enabled,
                                     sourceTypes=sourceTypes)
                return plats
            else:
                plats[pLabel] = dict(name=pName, enabled=enabled,
                                     sourceTypes=sourceTypes)

        return plats

    def _getPlatformsFromDB(self, platformId=None):
        cu = self.db.cursor()
        sql = """
            SELECT
                platforms.platformId,
                platforms.label,
                platforms.configurable
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
                     configurable=row['configurable'])

        return results

    def _platformModelFactory(self, *args, **kw):
        return models.Platform(platformId=kw['platformId'],
                               label=kw['label'],
                               platformName=kw['platformName'],
                               hostname=kw['hostname'],
                               enabled=kw['enabled'],
                               configurable=kw['configurable'])

    def _createContentSourceType(self, name):
        try:
            typeId = self.db.db.contentSourceTypes.getByName(name)
        except mint_error.ItemNotFound, e:
            typeId = self.db.db.contentSourceTypes.new(name=name)

        return typeId            

    def _createPlatformInDB(self, platformLabel, configurable, sourceTypes):
        configurable = int(configurable)
        platformId = self.db.db.platforms.new(label=platformLabel,
                                        configurable=configurable)

        for sourceType in sourceTypes:
            typeId = self._createContentSourceType(sourceType)
            self.db.db.platformsContentSourceTypes.new(platformId=platformId,
                            contentSourceTypeId=typeId)

        return str(platformId)                                        

    def _createPlatformsInDB(self, dbPlatforms, cfgPlatforms):
        changed = False
        for label in cfgPlatforms:
            if not dbPlatforms.has_key(label):
                # TODO: set configurable correctly
                self._createPlatformInDB(label, cfgPlatforms[label]['enabled'],
                        cfgPlatforms[label]['sourceTypes'])
                changed = True
        return changed                

    def getPlatforms(self, platformId=None):
        availablePlatforms = []
        if platformId:
            platformLabel = self.db.db.platforms.get(platformId)['label']
        else:
            platformLabel = None

        dbPlatforms = self._getPlatformsFromDB(platformId)
        cfgPlatforms = self._getConfigPlatforms(platformLabel)
        changed = self._createPlatformsInDB(dbPlatforms, cfgPlatforms)

        # If we created platforms in db, need to refresh dbPlatforms
        if changed:
            dbPlatforms = self._getPlatformsFromDB(platformId)
            
        for platformLabel in dbPlatforms:
            platId = dbPlatforms[platformLabel]['platformId']
            configurable = dbPlatforms[platformLabel]['configurable']
            platformName = cfgPlatforms[platformLabel]['name']
            enabled = cfgPlatforms[platformLabel]['enabled']
            
            plat = self._platformModelFactory(platformId=platId,
                        label=platformLabel, platformName=platformName,
                        hostname=platformLabel.split('.')[0],
                        enabled=enabled, configurable=configurable)
            # sources = self.getSourceInstances(platformId=platId)
            # sourceRefs = []
            # for src in sources.instance:
                # sourceRef = models.SourceRef()
                # sourceRef._contentSourceType = src.contentSourceType
                # sourceRef._shortName = src.shortName
                # sourceRefs.append(sourceRef)
            # plat.contentSources = models.SourceRefs(sourceRefs)

            availablePlatforms.append(plat)

        if platformId:
            return availablePlatforms[0]
        else:
            return models.Platforms(availablePlatforms)
        
    def getPlatform(self, platformId):
        return self.getPlatforms(platformId)

    def getSourceDescriptor(self, source):
        # TODO remove later
        source = 'Red Hat Network'
        desc = models.Description(desc='Configure %s' % source)
        metadata = models.Metadata(displayName=source,
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
        plat = models.SourceInstance(
                        contentSourceId=str(row['platformSourceId']),
                        name=row['name'],
                        shortName=row['shortName'],
                        defaultSource=row['defaultSource'],
                        orderIndex=row['orderIndex'],
                        contentSourceType=row['contentSourceType'])

        data = self._getPlatformSourceData(row['platformSourceId'])

        for row in data:
            setattr(plat, row['name'], row['value'])

        return plat

    def _getSourcesFromDB(self, source, platformId, sourceShortName):
        cu = self.db.cursor()
        sql = """
            SELECT
                platformSources.platformSourceId,
                platformSources.name,
                platformSources.shortName,
                platformSources.defaultSource,
                platformSources.orderIndex,
                (SELECT contentSourceTypes.name
                 FROM contentSourceTypes
                 WHERE platformSources.contentSourceTypeId =
                       contentSourceTypes.contentSourceTypeId) AS contentSourceType
            FROM
                platformSources
        """

        if source:
            sourceId = self.db.db.contentSourceTypes.getByName(source)

        if platformId: 
            sql = sql + ', platformsPlatformSources '
            sql = sql + """
                WHERE 
                    platformsPlatformSources.platformSourceId =
                    platformSources.platformSourceId 
                AND platformsPlatformSources.platformId = ?
            """
            cu.execute(sql, platformId)
        elif sourceShortName:
            sql = sql + 'WHERE platformSources.shortName = ?'
            cu.execute(sql, sourceShortName)
        elif source:
            sql = sql + """WHERE platformSources.contentSourceTypeId = ?""" 
            cu.execute(sql, sourceId)
        else:
            cu.execute(sql)
            
        sources = {}
        for row in cu:
            source = self._platformSourceModelFactory(row)
            sources[source.shortName] = source

        return sources            

    def _getCfgSources(self, source=None, sourceShortName=None):        
        sources = {}
        for i, cfgShortName in enumerate(self.cfg.platformSources):
            source = models.PlatformSource(shortName=cfgShortName,
                                   sourceUrl=self.cfg.platformSourceUrls[i],
                                   name=self.cfg.platformSourceNames[i],
                                   contentSourceType=self.cfg.platformSourceTypes[i],
                                   defaultSource='1',
                                   orderIndex='0')
            if sourceShortName and sourceShortName == cfgShortName:
                sources = {}
                sources[source.shortName] = source
                return sources
            elif source and source == self.cfg.platformSourceTypes[i]:
                sources[source.shortName] = source
            else:                
                sources[source.shortName] = source

        return sources            

    def _linkPlatformPlatformSource(self, platformId, platformSourceId):
        self.db.db.platformsPlatformSources.new(platformId=platformId,
                    platformSourceId=platformSourceId)

    def _linkToPlatforms(self, source):
        platformIds = self.db.db.platforms.getAllByType(source.contentSourceType)
        for platformId in platformIds:
            try:
                platId = platformId[0]
            except TypeError, e:
                platId = platformId

            self._linkPlatformPlatformSource(platId,
                    source.contentSourceId)

    def _createSourcesInDB(self, dbSources, cfgSources):
        changed = False
        for cfgSource in cfgSources:
            if not dbSources.has_key(cfgSource):
                sourceId = self._createPlatformSource(cfgSources[cfgSource])
                cfgSources[cfgSource].contentSourceId = sourceId
                self._linkToPlatforms(cfgSources[cfgSource])
                changed = True

        return changed                

    def getSourcesByPlatform(self, platformId):
        platformLabel = self.db.db.platforms.get(platformId)['label']
        platform = self._getConfigPlatforms(platformLabel).values()[0]

        types = []
        for sourceType in platform['sourceTypes']:
            types.append(models.SourceType(contentSourceType=sourceType))
        
        return models.SourceTypes(types)

    def getSources(self, source=None):
        plats = self._getConfigPlatforms()
        types = []
        strTypes = []
        for p in plats:
            tList = plats[p]['sourceTypes']
            for t in tList:
                if t not in strTypes:
                    if source and source == t:
                        return models.SourceType(contentSourceType=t)
                    strTypes.append(t)
                    types.append(models.SourceType(contentSourceType=t))

        return models.ContentSources(types)

    def getSource(self, source):
        return self.getSources(source)

    def getSourceInstances(self, source=None, shortName=None, platformId=None):
        sources = []
        dbSources = self._getSourcesFromDB(None, None, shortName)
        cfgSources = self._getCfgSources(source, shortName)
        changed = self._createSourcesInDB(dbSources, cfgSources)

        dbSources = self._getSourcesFromDB(source, platformId, shortName)
        
        if shortName:
            return dbSources[shortName]
        elif platformId:
            return models.ContentSourceInstances(dbSources.values())
        else:
            return models.SourceInstances(dbSources.values())

    def getSourceInstance(self, source=None, shortName=None):
        return self.getSourceInstances(source, shortName)

    def getSourceInstanceStatus(self, shortName):
        source = self.getSourceInstance(shortName=shortName)
        return self.getPlatformSourceStatus(source)

    def getPlatformStatus(self, platformId):
        pass

    def getPlatformSourceStatus(self, source):
        if not source.username or \
           not source.password or \
           not source.sourceUrl:
            status = models.PlatformSourceStatus(connected=False, valid=False, 
                message="Username, password, and source url must be provided to check a source's status.")
        else:
            ret = self._checkRHNSourceStatus(source.sourceUrl,
                        source.username, source.password)
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

    def updateSourceInstance(self, shortName, sourceInstance):
        cu = self.db.cursor()
        updSql = """
        UPDATE platformSourceData
        SET value = ?
        WHERE 
            name = ?
            AND platformSourceId = ?
        """
        insSql = """
        INSERT INTO platformSourceData
        VALUES (?, '%s', '%s', 3)
        """
        selSql = """
        SELECT value
        FROM platformSourceData
        WHERE 
            name = ?
            AND platformSourceId = ?
        """

        oldSource = self.getSourceInstance(shortName=shortName)

        for field in ['username', 'password', 'sourceUrl']:
            newVal = getattr(sourceInstance, field)
            if getattr(oldSource, field) != newVal:
                row = cu.execute(selSql, field, sourceInstance.contentSourceId)
                if row.fetchall():
                    cu.execute(updSql, newVal, field, sourceInstance.contentSourceId)
                else:
                    cu.execute(insSql % (field, newVal), sourceInstance.contentSourceId)

        return self.getSourceInstance(shortName=shortName)

    def updatePlatform(self, platformId, platform):
        cu = self.db.cursor()
        sql = """
        """
        cu.execute(sql, platformId)
        return self.getPlatform(platformId)

    def _createPlatformSource(self, source):
        try:
            typeId = self._createContentSourceType(source.contentSourceType)
            platformSourceId = self.db.db.platformSources.new(
                    name=source.name,
                    shortName=source.shortName,
                    defaultSource=source.defaultSource,
                    contentSourceTypeId=typeId,
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

        return platformSourceId          

    def createPlatformSource(self, source):
        self._createPlatformSource(source)
        return self.getSourceInstance(shortName=source.shortName)

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

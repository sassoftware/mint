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
from conary.dbstore import sqllib
from conary.lib import util

from mint import mint_error
from mint.lib import persistentcache
from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import contentsources
from mint.rest.db import manager

from rpath_proddef import api1 as proddef

class PlatformManager(manager.Manager):
    def __init__(self, cfg, db, auth):
        manager.Manager.__init__(self, cfg, db, auth)
        cacheFile = os.path.join(self.cfg.dataPath, 'data', 
                                 'platformName.cache')
        self.platformCache = PlatformDefCache(cacheFile, 
                                               db.productMgr.reposMgr)

    def _iterConfigPlatforms(self):
        apnLength = len(self.cfg.availablePlatformNames)
        for i, platformLabel in enumerate(self.cfg.availablePlatforms):
            platDef = self.platformCache.get(platformLabel)
            enabled = bool(platDef)
            if not enabled:
                # Fall back to the platform label, if
                # self.cfg.availablePlatformNames is incomplete
                platformName = platformLabel
                if i < apnLength:
                    platformName = self.cfg.availablePlatformNames[i]
            
            if platDef:
                platformName = platDef.getPlatformName()
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

    def _createSourceType(self, name):
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
            typeId = self._createSourceType(sourceType)
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

            availablePlatforms.append(plat)

        if platformId:
            return availablePlatforms[0]
        else:
            return models.Platforms(availablePlatforms)
        
    def getPlatform(self, platformId):
        return self.getPlatforms(platformId)

    def _getSourceInstance(self, source):
        sourceClass = contentsources.contentSourceTypes[source.contentSourceType]
        sourceInst = sourceClass()
        for field in sourceInst.getFieldNames():
            if hasattr(source, field):
                val = str(getattr(source, field))
                setattr(sourceInst, field, val)

        return sourceInst                

    def getSourceDescriptor(self, source):
        source = self.getSourceType(source)
        sourceInst = self._getSourceInstance(source)

        desc = models.Description(desc='Configure %s' % sourceInst.name)
        metadata = models.Metadata(displayName=sourceInst.name,
                    descriptions=[desc])

        dFields = []
        for field in sourceInst.fields:
            p = models.Prompt(desc=field.prompt)
            f = models.DescriptorField(name=field.name,
                           required=field.required,
                           descriptions=[models.Description(desc=field.description)],
                           prompt=p,
                           type=field.type,
                           password=field.password)
            dFields.append(f)                                   

        dataFields = models.DataFields(dFields)
        descriptor = models.descriptorFactory(metadata=metadata,
                        dataFields=dataFields)

        return descriptor

    def _getSourceData(self, sourceId):
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
        cu.execute(sql, sourceId)
        return cu

    def _sourceModelFactory(self, **kw):
        kw = sqllib.CaselessDict(kw)
        sourceId = kw.get('platformSourceId', None)
        contentSourceType = kw['contentSourceType']
        sourceTypeClass = contentsources.contentSourceTypes[contentSourceType]
        sourceType = sourceTypeClass()
        model = sourceType.model()
        
        for k, v in kw.items():
            if type(v) == type(int):
                val = str(v)
            else:
                val = v 
            setattr(model, k, val)

        if sourceId:
            model.contentSourceId = sourceId
            data = self._getSourceData(sourceId)
            for d in data:
                setattr(model, d['name'], d['value'])

        return model

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
            source = self._sourceModelFactory(**dict(row))
            sources[source.shortName] = source

        return sources            

    def _getCfgSources(self, sourceType=None, sourceShortName=None):        
        sources = {}
        for i, cfgShortName in enumerate(self.cfg.platformSources):
            source = self._sourceModelFactory(
                                shortName=cfgShortName,
                                sourceUrl=self.cfg.platformSourceUrls[i],
                                name=self.cfg.platformSourceNames[i],
                                contentSourceType=self.cfg.platformSourceTypes[i],
                                defaultSource='1',
                                orderIndex='0')
            if sourceShortName and sourceShortName == cfgShortName:
                sources = {}
                sources[source.shortName] = source
                return sources
            elif sourceType and sourceType == self.cfg.platformSourceTypes[i]:
                sources[source.shortName] = source
            else:                
                sources[source.shortName] = source

        return sources            

    def _linkPlatformContentSource(self, platformId, sourceId):
        self.db.db.platformsPlatformSources.new(platformId=platformId,
                    platformSourceId=sourceId)

    def _linkToPlatforms(self, source):
        platformIds = self.db.db.platforms.getAllByType(source.contentSourceType)
        for platformId in platformIds:
            try:
                platId = platformId[0]
            except TypeError, e:
                platId = platformId

            self._linkPlatformContentSource(platId,
                    source.contentSourceId)

    def _createSourcesInDB(self, dbSources, cfgSources):
        changed = False
        for cfgSource in cfgSources:
            if not dbSources.has_key(cfgSource):
                sourceId = self._createSource(cfgSources[cfgSource])
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

    def getSourceTypes(self, source=None):
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

        if source:
            raise mint_error.ItemNotFound(
                    'Content source type not found: %s' % source)

        return models.ContentSources(types)

    def getSourceType(self, source):
        return self.getSourceTypes(source)

    def getSources(self, source=None, shortName=None, platformId=None):
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

    def getSource(self, source=None, shortName=None):
        return self.getSources(source, shortName)

    def getPlatformStatus(self, platformId):
        pass

    def getSourceStatusByName(self, shortName):
        source = self.getSource(shortName=shortName)
        return self.getSourceStatus(source)

    def getSourceStatus(self, source):
        sourceInst = self._getSourceInstance(source)

        missing = []
        for field in sourceInst.fields:
            if field.required:
                val = getattr(source, field.name, None)
                if not val:
                    missing.append(field.name)

        if missing:
            message = "The following fields must be provided to check a source's status: %s." % str(missing)
            status = models.SourceStatus(connected=False, valid=False,
                                message=message)
        else:
            ret = sourceInst.status()
            status = models.SourceStatus(connected=ret[0],
                                valid=ret[1], message=ret[2])

        return status

    def updateSource(self, shortName, source):
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

        oldSource = self.getSource(shortName=shortName)

        sourceClass = contentsources.contentSourceTypes[source.contentSourceType]
        sourceInst = sourceClass()

        for field in sourceInst.getFieldNames():
            newVal = getattr(source, field)
            if getattr(oldSource, field) != newVal:
                row = cu.execute(selSql, field, source.contentSourceId)
                if row.fetchall():
                    cu.execute(updSql, newVal, field, source.contentSourceId)
                else:
                    cu.execute(insSql % (field, newVal), source.contentSourceId)

        return self.getSource(shortName=shortName)

    def updatePlatform(self, platformId, platform):
        cu = self.db.cursor()
        sql = """
        """
        cu.execute(sql, platformId)
        return self.getPlatform(platformId)

    def _createSource(self, source):
        try:
            typeId = self._createSourceType(source.contentSourceType)
            sourceId = self.db.db.platformSources.new(
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
                cu.execute(sql % (sourceId, field, value))

        return sourceId          

    def createSource(self, source):
        self._createSource(source)
        return self.getSource(shortName=source.shortName)

    def deleteSource(self, shortName):
        sourceId = self.db.db.platformSources.getIdFromShortName(shortName)
        self.db.db.platformSources.delete(sourceId)

class PlatformDefCache(persistentcache.PersistentCache):
    def __init__(self, cacheFile, reposMgr):
        persistentcache.PersistentCache.__init__(self, cacheFile)
        self._reposMgr = weakref.ref(reposMgr)

    def _refresh(self, labelStr):
        try:
            client = self._reposMgr().getAdminClient()
            platDef = proddef.PlatformDefinition()
            platDef.loadFromRepository(client, labelStr)
            return platDef
        except Exception, e:
            # Swallowing this exception allows us to have a negative
            # cache entries.  Of course this comes at the cost
            # of swallowing exceptions...
            print >> sys.stderr, "failed to lookup platform definition on label %s: %s" % (labelStr, str(e))
            sys.stderr.flush()
            return None

#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import os
import sys
import tempfile
import weakref
import xmlrpclib

from conary import conarycfg
from conary import errors as conaryErrors
from conary import versions
from conary.conaryclient import callbacks
from conary.dbstore import sqlerrors
from conary.dbstore import sqllib
from conary.build import lookaside
from conary.lib import util
from conary.repository import changeset

from mint import config
from mint import jobstatus
from mint import mint_error
from mint.lib import persistentcache
from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import contentsources
from mint.rest.db import manager

from rpath_proddef import api1 as proddef

class PlatformLoadCallback(callbacks.ChangesetCallback):
    def __init__(self, db, platformId, loadJobId, totalKB, *args, **kw):
        self.db = db
        self.platformId = platformId
        self.loadJobId = loadJobId
        self.totalKB = totalKB
        callbacks.ChangesetCallback.__init__(self, *args, **kw)
        
    def _message(self, txt, usePrefix=True):
        if usePrefix:
            message = self.prefix + txt
        else:
            message = txt

        try:
            self.db.db.platformLoadJobs.update(self.loadJobId, platformId=self.platformId, message=message)
        except sqlerrors.CursorError, e:
            reopened = self.db.db.reopen()
            if reopened:
                self.db.db.platformLoadJobs.update(self.loadJobId, platformId=self.platformId, message=message)

    def done(self):
        self.db.db.platformLoadJobs.update(self.loadJobId, done=1)

    def downloading(self, got, rate):
        self._downloading('Downloading', got, rate, self.totalKB)

    def _downloading(self, msg, got, rate, total):
        self.csMsg("%s %dMB of %dMB (%d%%) at %dKB/sec"
                   % (msg, got/1024/1024, total/1024/1024, (got*100)/total, 
                      rate/1024))
        self.update()                      

    def sendingChangeset(self, got, need):
        if need != 0:
            self._message("Committing changeset "
                          "(%dKB (%d%%) of %dKB at %dKB/sec)..."
                          % (got/1024/1024, (got*100)/need, need/1024/1024, self.rate/1024))
        else:
            self._message("Committing changeset "
                          "(%dKB at %dKB/sec)..." % (got/1024/1024, self.rate/1024))

class ContentSourceTypes(object):
    def __init__(self, db, cfg, platforms):
        self.db = db
        self.cfg = cfg
        self.platforms = platforms

    def _contentSourceTypeModelFactory(self, name):
        return models.SourceType(contentSourceType=name)

    def _listFromDb(self):
        dbTypes = self.db.db.contentSourceTypes.getAll()
        types = []
        for dbType in dbTypes:  
            type = self._contentSourceTypeModelFactory(name=dbType['name'])
            types.append(type)

        return types            
    
    def _listFromCfg(self):
        allTypes = []
        for label, name, enabled, types, configurable in self.platforms._iterConfigPlatforms():
            for t in types:
                if t not in allTypes:
                    allTypes.append(t)

        types = []
        for type in allTypes:
            type = self._contentSourceTypeModelFactory(name=type)
            types.append(type)

        return types

    def _create(self, sourceType):
        sourceTypeId = self.db.db.contentSourceTypes.new(name=sourceType.contentSourceType)
        return sourceTypeId

    def _syncDb(self, dbTypes, cfgTypes):
        changed = False
        dbNames = [t.contentSourceType for t in dbTypes]
        for cfgType in cfgTypes:
            if cfgType.contentSourceType not in dbNames:
                changed = True
                self._create(cfgType)

        return changed                

    def listByName(self, sourceTypeName):
        types = self.list()
        type = [t for t in types.contentSourceTypes \
                if t.contentSourceType == \
                   sourceTypeName]

        return type[0]

    def getIdByName(self, sourceTypeName):
        types = self.list()
        return self.db.db.contentSourceTypes.getByName(sourceTypeName)

    def list(self):
        dbTypes = self._listFromDb()
        cfgTypes = self._listFromCfg()
        changed = self._syncDb(dbTypes, cfgTypes)
        if changed:
            dbTypes = self._listFromDb()

        return models.SourceTypes(dbTypes)            

    def _getSourceTypeInstance(self, source):
        sourceClass = contentsources.contentSourceTypes[source.contentSourceType]
        sourceInst = sourceClass()
        for field in sourceInst.getFieldNames():
            if hasattr(source, field):
                val = str(getattr(source, field))
                setattr(sourceInst, field, val)

        return sourceInst   

    def _getSourceTypeInstanceByName(self, sourceType):
        sourceClass = contentsources.contentSourceTypes[sourceType]
        return sourceClass()

    def getDescriptor(self, sourceType):
        sourceTypeInst = self._getSourceTypeInstanceByName(sourceType)

        desc = models.Description(desc='%s Configuration' % sourceTypeInst.name)
        metadata = models.Metadata(displayName=sourceTypeInst.name,
                    descriptions=[desc])

        dFields = []
        for field in sourceTypeInst.fields:
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

class Platforms(object):

    def __init__(self, db, cfg, mgr):
        self.platforms = []
        self.db = db
        self.cfg = cfg
        self._reposMgr = db.productMgr.reposMgr
        cacheFile = os.path.join(self.cfg.dataPath, 'data', 
                                 'platformName.cache')
        self.platformCache = PlatformDefCache(cacheFile, 
                                              self._reposMgr)
        self.contentSourceTypes = ContentSourceTypes(db, cfg, self)
        self.mgr = mgr

    def _listFromDb(self):
        platforms = []
        dbPlatforms = self.db.db.platforms.getAll()
        for platform in dbPlatforms:
            platforms.append(self._platformModelFactory(**dict(platform)))

        return platforms            

    def _iterConfigPlatforms(self):
        apnLength = len(self.cfg.availablePlatformNames)
        for i, platformLabel in enumerate(self.cfg.availablePlatforms):
            platDef = self.platformCache.get(platformLabel)
            if not platDef:
                # Fall back to the platform label, if
                # self.cfg.availablePlatformNames is incomplete
                platformName = platformLabel
                if i < apnLength:
                    platformName = self.cfg.availablePlatformNames[i]

            if platDef:
                platformName = platDef.getPlatformName()
                platformProv = platDef.getContentProvider()
                if platformProv:
                    types = [t.name for t in platformProv.contentSourceTypes]
                else:
                    types = []
            else:
                types = []

            
            # Platforms are not enabled by default, they have to be
            # explicitly enabled in the db.
            enabled = 0

            configurable = platformLabel in self.cfg.configurablePlatforms

            yield platformLabel, platformName, enabled, types, configurable

    def _platformModelFactory(self, *args, **kw):
        kw = sqllib.CaselessDict(kw)
        platformId = kw.get('platformId', None)
        if platformId:
            platformId = str(platformId)
        label = kw.get('label', None)
        platformName = kw.get('platformName', None)
        hostname = kw.get('hostname', None)
        enabled = kw.get('enabled', None)
        configurable = kw.get('configurable', None)
        sourceTypes = kw.get('sourceTypes', [])
        mode = kw.get('mode', 'manual')
        platform = models.Platform(platformId=platformId,
                               label=label,
                               platformName=platformName,
                               hostname=hostname,
                               enabled=enabled,
                               configurable=configurable,
                               mode=mode)
        platform._sourceTypes = sourceTypes                               
        return platform

    def _create(self, platform):
        # If this is a new install of rba, we want to create platforms as
        # disabled.  If it was an upgrade, we want to create them as enabled.
        # There's no great way to tell this, but if there are projects
        # already created, they must have used a platform already, and
        # therefore they should be enabled.
        projects = self.db.db.projects.getProjectsList()
        # Remove rmake-repository from the list, we don't want to count that.
        rmakeRepoName = 'rmake-repository - rMake Repository'
        projects = [p for p in projects if p[2] != rmakeRepoName]
        enabled = projects and 1 or 0

        platformId = self.db.db.platforms.new(label=platform.label,
                                              enabled=enabled)

        for sourceType in platform._sourceTypes:
            typeId = self.contentSourceTypes.getIdByName(sourceType)
            self.db.db.platformsContentSourceTypes.new(platformId=platformId,
                            contentSourceTypeId=typeId)

        return platform

    def _syncDb(self, dbPlatforms, cfgPlatforms):
        changed = False
        dbPlatformLabels = [d.label for d in dbPlatforms]

        for cfgPlatform in cfgPlatforms:
            if cfgPlatform.label not in dbPlatformLabels:
                changed = True
                self._create(cfgPlatform)

        return changed                

    def _linkToSourceType(self, platformId, contentSourceTypeId):
        platformId = int(platformId)
        contentSourceTypeId = int(contentSourceTypeId)

        # If the link is already there, do nothing
        types = self.db.db.platformsContentSourceTypes.getAllByPlatformId(platformId)
        for t in types:
            if t[1] == contentSourceTypeId:
                return

        self.db.db.platformsContentSourceTypes.new(platformId=platformId,
            contentSourceTypeId=contentSourceTypeId)

    def _populateFromCfg(self, dbPlatforms, cfgPlatforms):
        dbLabels = [p.label for p in dbPlatforms]
        cfgLabels = [p.label for p in cfgPlatforms]

        fields = ['platformName', 'hostname',
                  '_sourceTypes', 'configurable']

        platforms = []

        # For each platform in cfgPlatform, populate any of it's attributes
        # onto the models that were loaded from the db.
        for i, c in enumerate(cfgLabels):
            if c in dbLabels:
                for f in fields:
                    dIndex = dbLabels.index(c)
                    setattr(dbPlatforms[dIndex], f,
                            getattr(cfgPlatforms[i], f, None))
                platforms.append(dbPlatforms[dIndex])                            

        # Link the platforms to all of it's source types.
        for p in platforms:
            for sourceType in p._sourceTypes:
                id = self.mgr.contentSourceTypes.getIdByName(sourceType)
                self._linkToSourceType(p.platformId, id)

        # Append any other platforms not found in the cfg onto our new list.
        for i, d in enumerate(dbLabels):
            if d not in cfgLabels:
                platforms.append(dbPlatforms[i])

        return platforms

    def _listFromCfg(self):
        platforms = []
        for label, name, enabled, sourceTypes, configurable in self._iterConfigPlatforms():
            platform = self._platformModelFactory(label=label,
                                platformName=name, 
                                hostname=label.split('.')[0],
                                enabled=enabled, configurable=configurable,
                                sourceTypes=sourceTypes)
            platforms.append(platform)
        return platforms

    def backgroundRun(self, function, *args, **kw):
        pid = os.fork()
        if pid:
            os.waitpid(pid, 0)
            return
        try:
            try:
                pid = os.fork()
                if pid:
                    # The first child exits and is waited by the parent
                    # the finally part will do the os._exit
                    return
                # Redirect stdin, stdout, stderr
                fd = os.open(os.devnull, os.O_RDWR)
                #os.dup2(fd, 0)
                #os.dup2(fd, 1)
                #os.dup2(fd, 2)
                os.close(fd)
                # Create new process group
                #os.setsid()

                os.chdir('/')
                function(*args, **kw)
            except Exception:
                try:
                    ei = sys.exc_info()
                    # TODO log error
                    # self.log_error('Daemonized process exception',
                                   # exc_info = ei)
                finally:
                    os._exit(1)
        finally:
            os._exit(0)

    def load(self, platformId, platformLoad):
        platform = self.getById(platformId)
        host = platform.label.split('@')[:1][0]
        repos = self.db.productMgr.reposMgr.getRepositoryClientForProduct(host)
        uri = platformLoad.uri
        headers = {}
        fd, outFilePath = tempfile.mkstemp('.ccs', 'platform-load-')

        finder = lookaside.FileFinder(None, None)
        inFile = finder._fetchUrl(uri, headers)

        jobId = self.db.db.platformLoadJobs.new(platformId=platformId, message='')
        platLoad = models.PlatformLoad()
        platLoad.jobId = jobId
        platLoad.platformId = platformId
        platLoad.uri = platformLoad.uri

        self.backgroundRun(self._load, platformId, jobId, inFile, outFilePath,
                           repos)
        # self._load(platformId, jobId, inFile, outFilePath, repos)

        return platLoad

    def _load(self, platformId, jobId, inFile, outFilePath, repos):
        totalKB = int(inFile.headers['content-length'])
        callback = PlatformLoadCallback(self.db, platformId, jobId, totalKB)

        outFile = open(outFilePath, 'w')
        total = util.copyfileobj(inFile, outFile,
                                 callback=callback.downloading)
        outFile.close()

        callback._message('Download Complete. Figuring out what to commit..')
        cs = changeset.ChangeSetFromFile(outFilePath) 
        needsCommit = cs.removeCommitted(repos)
        if needsCommit:
            repos.commitChangeSet(cs, callback=callback, mirror=True)
            callback._message('Commit completed.')
        else:
            callback._message('Nothing needs to be committed. Local Repository '
                              'is up to date.')
        callback.done()            

        return 

    def _getProjectId(self, platformId):
        return self.db.db.platforms.get(platformId)['projectId']

    def _getUsableProject(self, platformId, hostname):
        # See if there is project already setup that shares
        # the fqdn of the platform.
        try:
            projectId = self.db.db.projects.getProjectIdByFQDN(hostname)
        except mint_error.ItemNotFound, e:
            projectId = None

        if projectId:
            # Check if the project is external.
            project = self.db.db.projects.get(projectId)
            external = project['external'] == 1 and True or False

            if external:
                # Look up any repo maps from the labels table.
                labelIdMap, repoMap, userMap, entMap = \
                    self.db.db.labels.getLabelsForProject(projectId) 
                url = repoMap.get(hostname, url)

                # Check if there is a mirror set up.
                try:
                    mirrorId = self.db.db.inboundMirrors.getIdByColumn(
                                'targetProjectId', projectId)
                    # Just add the project to our platform
                    self.db.db.platforms.update(platformId, projectId=projectId)
                except mint_error.ItemNotFound, e:
                    # Add an inboud mirror for this external project.
                    self.db.productMgr.reposMgr.addIncomingMirror(
                        projectId, host, domainname, url, authInfo, True)
            else:
                # Not an external Project, fail.
                raise errors.InvalidProjectForPlatform()

        return projectId

    def _setupPlatform(self, platform):
        platformId = int(platform.platformId)
        platformName = str(platform.platformName)
        platformLabel = str(platform.label)
        hostname = str(platform.hostname)
        label = versions.Label(platform.label)
        host = str(label.getHost())
        url = 'http://%s/conary/' % (host)
        domainname = '.'.join(host.split('.')[1:])

        # Use the entitlement from /srv/rbuilder/data/authorization.xml
        entitlement = self.db.siteAuth.entitlementKey
        authInfo = models.AuthInfo(authType='entitlement',
                                   entitlement=entitlement)

        # Get the productId to see if this platform has already been
        # associated with an external product.
        projectId = self._getProjectId(platformId, hostname)

        if not projectId:
            projectId = self._getUsableProject(platformId)

        if not projectId:            
            # Still no project, we need to create a new one.
            try:
                mirror = platformLabel in self.cfg.configurablePlatforms
                projectId = self.db.productMgr.createExternalProduct(platformName, hostname, 
                                domainname, url, authInfo, mirror=mirror)
            except mint_error.RepositoryAlreadyExists, e:
                projectId = self.db.productMgr.getProjectIdByFQDN(hostname)

        return projectId

    def update(self, platformId, platform):
        self.db.db.platforms.update(platformId, enabled=int(platform.enabled))
        self.db.db.platforms.update(platformId, mode=platform.mode)

        if platform.enabled:
            self._setupPlatform(platform)

        return self.getById(platformId)

    def list(self):
        dbPlatforms = self._listFromDb()
        cfgPlatforms = self._listFromCfg()
        changed = self._syncDb(dbPlatforms, cfgPlatforms)
        if changed:
            dbPlatforms = self._listFromDb()

        dbPlatforms = self._populateFromCfg(dbPlatforms, cfgPlatforms)            
            
        return models.Platforms(dbPlatforms)

    def getStatus(self, platformId):
        platform = self.getById(platformId)
        client = self._reposMgr.getAdminClient()
        platDef = proddef.PlatformDefinition()
        platStatus = models.PlatformSourceStatus()
        try:
            platDef.loadFromRepository(client, platform.label)
        except conaryErrors.ConaryError, e:
            platStatus.valid = False
            platStatus.connected = True
            platStatus.message = str(e)
        except Exception, e:
            platStatus.valid = False
            platStatus.connected = False
            platStatus.message = str(e)
            # Hard code a helpful message for the sle platform.
            if 'sle.rpath.com' in platform.label:
                platStatus.message = "This platform requires a " + \
                    "commercial license.  You are either missing the " + \
                    "entitlement for this platform or it is no longer valid"
        else:            
            platStatus.valid = True
            platStatus.connected = True
            platStatus.message = '%s is online.' % platform.platformName

        return platStatus

    def getLoadStatus(self, platformId, jobId):
        status = models.PlatformLoadStatus()
        message = self.db.db.platformLoadJobs.get(jobId)['message']
        done = self.db.db.platformLoadJobs.get(jobId)['done']
        if bool(done):
            code = jobstatus.FINISHED
        else:
            code = jobstatus.RUNNING

        status.set_status(code, message)
        return status

    def getById(self, platformId):
        platform = self.db.db.platforms.get(platformId)
        platform = self._platformModelFactory(**dict(platform))
        platforms = self._populateFromCfg([platform], self._listFromCfg())

        return platforms[0]

    def getByName(self, platformName):
        platforms = self.list()
        platform = [p for p in platforms.platforms \
                    if p.platformName == platformName][0]
        return platform                    

    def getSources(self, platformId):
        return self.mgr.contentSources.listByPlatformId(platformId)

class ContentSources(object):

    def __init__(self, db, cfg, platforms, contentSourceTypes):
        self._sources = []
        self.db = db
        self.cfg = cfg
        self.platforms = platforms
        self.contentSourceTypes = contentSourceTypes

    def _contentSourceModelFactory(self, *args, **kw):

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

    def _create(self, source):
        typeId = self.contentSourceTypes.getIdByName(source.contentSourceType)
        sourceId = self.db.db.platformSources.new(
                name=source.name,
                shortName=source.shortName,
                defaultSource=int(source.defaultSource),
                contentSourceTypeId=typeId,
                orderIndex=source.orderIndex)

        cu = self.db.cursor()
        sql = """
        INSERT INTO platformSourceData
        VALUES (%s, '%s', '%s', 3)
        """

        for field in ['username', 'password', 'sourceUrl']:
            value = getattr(source, field, None)
            if value:
                cu.execute(sql % (sourceId, field, value))

        source.contentSourceId = sourceId
        self._linkToPlatforms(source)

        return sourceId      

    def _syncDb(self, dbSources, cfgSources):
        changed = False
        dbNames = [s.shortName for s in dbSources]

        createdPlatforms = False
        for cfgSource in cfgSources:
            if cfgSource.shortName not in dbNames:

                # Before creating a source (which links sources to platforms),
                # we need to make sure all platforms exist in the db (by
                # calling list()).  Save a flag so we only do it once.
                if not createdPlatforms:
                    self.platforms.list()
                    createdPlatforms = True

                self._create(cfgSource)
                changed = True

        return changed                

    def _listFromDb(self):
        sources = []
        dbSources = self.db.db.platformSources.getAll()
        for dbSource in dbSources:
            source = self._contentSourceModelFactory(**dict(dbSource))
            sources.append(source)

        return sources            
        
    def _listFromCfg(self):
        sources = []
        for i, cfgShortName in enumerate(self.cfg.platformSources):
            source = self._contentSourceModelFactory(
                                shortName=cfgShortName,
                                sourceUrl=self.cfg.platformSourceUrls[i],
                                name=self.cfg.platformSourceNames[i],
                                contentSourceType=self.cfg.platformSourceTypes[i],
                                defaultSource='1',
                                orderIndex='0')
            sources.append(source)

        return sources

    def list(self):
        dbSources = self._listFromDb()
        cfgSources = self._listFromCfg()
        changed = self._syncDb(dbSources, cfgSources)
        if changed:
            dbSources = self._listFromDb()

        return models.SourceInstances(dbSources)            

    def _linkPlatformToContentSource(self, platformId, sourceId):
        self.db.db.platformsPlatformSources.new(platformId=platformId,
                    platformSourceId=sourceId)

    def _linkToPlatforms(self, source):
        platforms = self.db.db.platforms.getAllByType(source.contentSourceType)

        for platform in platforms:
            self._linkPlatformToContentSource(platform['platformId'],
                    source.contentSourceId)

    def delete(self, shortName):
        sourceId = self.db.db.platformSources.getIdFromShortName(shortName)
        self.db.db.platformSources.delete(sourceId)

    def create(self, source):
        if not source.contentSourceType:
            raise Exception('Content Source Type must be specified.')

        sourceId = self._create(source)

        return self.getByShortName(source.shortName)

    def update(self, source):
        cu = self.db.cursor()
        updSql = """
        UPDATE platformSourceData
        SET value = ?
        WHERE 
            name = ?
            AND platformSourceId = ?
        """
        selSql = """
        SELECT value
        FROM platformSourceData
        WHERE 
            name = ?
            AND platformSourceId = ?
        """

        oldSource = self.getByShortName(source.shortName)

        sourceClass = contentsources.contentSourceTypes[source.contentSourceType]
        sourceInst = sourceClass()

        for field in sourceInst.getFieldNames():
            newVal = getattr(source, field)
            if getattr(oldSource, field) != newVal:
                row = cu.execute(selSql, field, source.contentSourceId)
                if row.fetchall():
                    cu.execute(updSql, newVal, field, source.contentSourceId)
                else:
                    self.db.db.platformSourceData.new(
                                platformSourceId=source.contentSourceId,
                                name=str(field),
                                value=str(newVal),
                                dataType=3)

        return self.getByShortName(source.shortName)

    def getByShortName(self, shortName):
        sources = self.list()
        sources = [s for s in sources.instance \
                   if s.shortName == shortName]
        return sources[0]

    def listByType(self, sourceType):
        sources = self.list()
        sources = [s for s in sources.instance \
                   if s.contentSourceType == sourceType]
        return models.SourceInstances(sources)                   

    def listByPlatformId(self, platformId):
        sources = self.list()
        dbSources = self.db.db.platformSources.getByPlatformId(platformId)
        sources = []
        for dbSource in dbSources:
            source = self.getByShortName(dbSource['shortName'])
            sources.append(source)

        return models.ContentSourceInstances(sources)            

    def getStatus(self, source):        
        sourceInst = self.contentSourceTypes._getSourceTypeInstance(source)

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

class PlatformManager(manager.Manager):
    def __init__(self, cfg, db, auth):
        manager.Manager.__init__(self, cfg, db, auth)
        self._reposMgr = db.productMgr.reposMgr
        cacheFile = os.path.join(self.cfg.dataPath, 'data', 
                                 'platformName.cache')
        self.platformCache = PlatformDefCache(cacheFile, 
                                              self._reposMgr)
        self.platforms = Platforms(db, cfg, self)
        self.contentSourceTypes = ContentSourceTypes(db, cfg, self.platforms)
        self.contentSources = ContentSources(db, cfg, self.platforms,
                                self.contentSourceTypes)

    def getPlatforms(self, platformId=None):
        return self.platforms.list()
        
    def getPlatform(self, platformId):
        return self.platforms.getById(platformId)

    def getPlatformByName(self, platformName):
        return self.platforms.getByName(platformName)

    def loadPlatform(self, platformId, platformLoad):
        return self.platforms.load(platformId, platformLoad)

    def getPlatformStatus(self, platformId):
        return self.platforms.getStatus(platformId)

    def getPlatformLoadStatus(self, platformId, jobId):
        return self.platforms.getLoadStatus(platformId, jobId)

    def getSourceTypeDescriptor(self, sourceType):
        return self.contentSourceTypes.getDescriptor(sourceType)

    def getSourceTypesByPlatform(self, platformId):
        platform = self.platforms.getById(platformId)
        types = []
        for sourceType in platform._sourceTypes:
            types.append(models.SourceType(contentSourceType=sourceType))
        
        return models.SourceTypes(types)

    def getSourceTypes(self, sourceType=None):
        return self.contentSourceTypes.list()

    def getSourceType(self, sourceType):
        return self.contentSourceTypes.listByName(sourceType)

    def getSources(self, sourceType=None):
        if sourceType:
            return self.contentSources.listByType(sourceType)
        else:
            return self.contentSources.list()

    def getSource(self, shortName):
        return self.contentSources.getByShortName(shortName)

    def getSourcesByPlatform(self, platformId):
        return self.platforms.getSources(platformId)

    def getSourceStatusByName(self, shortName):
        source = self.getSource(shortName=shortName)
        return self.getSourceStatus(source)

    def getSourceStatus(self, source):
        return self.contentSources.getStatus(source)

    def updateSource(self, source):
        return self.contentSources.update(source)

    def updatePlatform(self, platformId, platform):
        return self.platforms.update(platformId, platform)

    def createSource(self, source):
        return self.contentSources.create(source)

    def deleteSource(self, shortName):
        return self.contentSources.delete(shortName)

    def getContentEnabledPlatformLabels(self):
        sql = """
            SELECT DISTINCT Platforms.label
                       FROM Platforms
                       JOIN PlatformsContentSourceTypes USING (platformId)
                       JOIN ContentSourceTypes USING (contentSourceTypeId)
                      WHERE Platforms.enabled != 0
        """
        cu = self.db.cursor()
        cu.execute(sql)
        return [ x[0] for x in cu ]

class PlatformDefCache(persistentcache.PersistentCache):
    def __init__(self, cacheFile, reposMgr):
        persistentcache.PersistentCache.__init__(self, cacheFile)
        self._reposMgr = weakref.ref(reposMgr)

    def _refresh(self, labelStr):
        try:
            reposMgr = self._reposMgr()
            client = reposMgr.getAdminClient()

            # TODO: figure out the right thing to do here.
            # Need to look at inboundmirrors table to get the sourceurl from
            # the platform in order to read the platdef, so that we bypass the
            # local repo already setup for the platform.
            sourceUrl = reposMgr.getIncomingMirrorUrlByLabel(labelStr)
            if sourceUrl:
                from mint.db import repository as reposdb
                host = labelStr.split('@')[0]
                entitlement = reposMgr.db.siteAuth.entitlementKey
                serverProxy = reposMgr.reposManager.getServerProxy(host,
                    sourceUrl, None, [entitlement])
                client.repos.c.cache[host] = serverProxy

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

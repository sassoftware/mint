#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import base64
import logging
import os
import sys
import tempfile
import weakref

from conary import errors as conaryErrors
from conary import versions
from conary.conaryclient import callbacks
from conary.dbstore import sqlerrors
from conary.dbstore import sqllib
from conary.build import lookaside
from conary.lib import util
from conary.repository import errors as reposErrors
from conary.repository import changeset
from conary.repository import filecontainer

from mint import jobstatus
from mint import mint_error
from mint.lib import persistentcache
from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import contentsources
from mint.rest.db import manager

from rpath_proddef import api1 as proddef

log = logging.getLogger(__name__)


class PlatformLoadCallback(callbacks.ChangesetCallback):
    def __init__(self, db, platformId, loadJobId, totalKB, *args, **kw):
        self.db = db
        self.platformId = platformId
        self.loadJobId = loadJobId
        self.totalKB = totalKB
        self.prefix = ''
        callbacks.ChangesetCallback.__init__(self, *args, **kw)
        
    def _message(self, txt, usePrefix=True):
        if usePrefix:
            message = self.prefix + txt
        else:
            message = txt

        try:
            self.db.db.platformLoadJobs.update(self.loadJobId, 
                platformId=self.platformId, message=message)
        except sqlerrors.CursorError, e:
            reopened = self.db.db.reopen()
            if reopened:
                self.db.db.platformLoadJobs.update(self.loadJobId, 
                    platformId=self.platformId, message=message)

    def done(self):
        self.db.db.platformLoadJobs.update(self.loadJobId, done=1)

    def error(self, e):
        self.db.db.platformLoadJobs.update(self.loadJobId, error=1)
        self._message("Load failed: %s" % e)

    def downloading(self, got, rate):
        self._downloading('Downloading', got, rate, self.totalKB)

    def _downloading(self, msg, got, rate, total):
        if not total:
            totalMsg = ''
            totalPct = ''
        else:
            totalMsg = 'of %dMB ' % (total / 1024 / 1024)
            totalPct = '(%d%%) ' % ((got * 100) / total)

        self.csMsg("%s %dMB %s%sat %dKB/sec"
                   % (msg, got/1024/1024, totalMsg, totalPct, rate/1024))
        self.update()                      

    def sendingChangeset(self, got, need):
        if need != 0:
            self._message("Committing changeset "
                          "(%dMB (%d%%) of %dMB at %dKB/sec)..."
                          % (got/1024/1024, (got*100)/need, need/1024/1024, self.rate/1024))
        else:
            self._message("Committing changeset "
                          "(%dKB at %dKB/sec)..." % (got/1024/1024, self.rate/1024))

    def creatingDatabaseTransaction(self, troveNum, troveCount):
        """
        @see: callbacks.UpdateCallback.creatingDatabaseTransaction
        """
        self._message("Creating database transaction (%d of %d)" %
		      (troveNum, troveCount))

    def committingTransaction(self):
        self._message("Committing database transaction")

class ContentSourceTypes(object):
    def __init__(self, db, cfg, platforms):
        self.db = db
        self.cfg = cfg
        self.platforms = platforms

    def _contentSourceTypeModelFactory(self, name, singleton = None, id = None):
        if id is None:
            id = name
        return models.SourceType(contentSourceType=name, singleton=singleton,
            id = name)

    def _listFromCfg(self):
        allTypesMap = dict()
        allTypes = []
        for label, name, usageTerms, buildTypes, enabled, sourceTypes, configurable in self.platforms._iterConfigPlatforms():
            for t, isSingleton in sourceTypes:
                if t not in allTypes:
                    allTypes.append(t)
                    allTypesMap[t] = isSingleton

        stypes = []
        for stype in allTypes:
            isSingleton = allTypesMap[stype]
            stype = self._contentSourceTypeModelFactory(name=stype,
                singleton=isSingleton)
            stypes.append(stype)

        return stypes

    def listByName(self, sourceTypeName):
        stypes = self.list()
        stype = [t for t in stypes.contentSourceTypes
                 if t.contentSourceType == sourceTypeName]

        return stype[0]

    def getIdByName(self, sourceTypeName):
        s = self.listByName(sourceTypeName)
        return s.id

    def list(self):
        cfgTypes = self._listFromCfg()
        return models.SourceTypes(cfgTypes)

    def _getSourceTypeInstance(self, source):
        sourceClass = contentsources.contentSourceTypes[source.contentSourceType]
        sourceInst = sourceClass(proxies = self.db.cfg.proxy)
        for field in sourceInst.getFieldNames():
            if hasattr(source, field):
                val = str(getattr(source, field))
                setattr(sourceInst, field, val)

        return sourceInst   

    def _getSourceTypeInstanceByName(self, sourceType):
        sourceClass = contentsources.contentSourceTypes[sourceType]
        return sourceClass(proxies = self.db.cfg.proxy)

    def getDescriptor(self, sourceType):
        sourceTypeInst = self._getSourceTypeInstanceByName(sourceType)

        contentSourceTypeName = sourceTypeInst.getContentSourceTypeName()
        desc = models.Description(desc='%s Configuration' %
            contentSourceTypeName)
        metadata = models.Metadata(displayName=contentSourceTypeName,
                    descriptions=[desc])

        dFields = []
        for field in sourceTypeInst.fields:
            p = models.Prompt(desc=field.prompt)

            c = None
            if hasattr(field, 'regexp'):
                c = models.Constraints(regexp=field.regexp,
                            descriptions=[models.Description(desc=field.regexpDescription)])

            f = models.DescriptorField(name=field.name, required=field.required,
                        descriptions=[models.Description(desc=field.description)],
                        prompt=p, type=field.type, password=field.password,
                        constraints=c)
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

            platformUsageTerms = None
            if platDef:
                platformName = platDef.getPlatformName()
                platformUsageTerms = platDef.getPlatformUsageTerms()
                platformProv = platDef.getContentProvider()
                if platformProv:
                    types = [(t.name, t.isSingleton)
                        for t in platformProv.contentSourceTypes]
                else:
                    types = []
                platformBuildTypes = platDef.getBuildTemplates()
            else:
                types = []
                platformBuildTypes = []
            
            # Platforms are not enabled by default, they have to be
            # explicitly enabled in the db.
            enabled = 0

            configurable = platformLabel in self.cfg.configurablePlatforms

            yield (platformLabel, platformName, platformUsageTerms,
                platformBuildTypes, enabled, types, configurable)

    def _platformModelFactory(self, *args, **kw):
        kw = sqllib.CaselessDict(kw)
        platformId = kw.get('platformId', None)
        if platformId:
            platformId = str(platformId)
        label = kw.get('label', None)
        fqdn = label.split('@')[0]
        platformName = kw.get('platformName', None)
        platformBuildTypes = kw.get('platformBuildTypes', [])
        enabled = kw.get('enabled', None)
        configurable = kw.get('configurable', None)
        sourceTypes = kw.get('sourceTypes', [])
        mode = kw.get('mode', 'manual')
        platformUsageTerms = kw.get('platformUsageTerms')
        platform = models.Platform(platformId=platformId, label=label,
                platformName=platformName, enabled=enabled,
                platformUsageTerms=platformUsageTerms,
                configurable=configurable, mode=mode,
                repositoryHostname=fqdn)
        platform._sourceTypes = sourceTypes
        platform._buildTypes = platformBuildTypes
        return platform

    def _create(self, platform):
        try:
            platformId = self.db.db.platforms.new(label=platform.label,
                                                  enabled=0)
        except mint_error.DuplicateItem, e:
            platformId = self.db.db.platforms.getIdByColumn('label',
                            platform.label)
            log.error("Error creating platform %s, it must already "
                      "exist: %s" % (platform.label, e))

        for sourceType, isSingleton in platform._sourceTypes:
            typeName = self.contentSourceTypes.getIdByName(sourceType)
            try:
                self.db.db.platformsContentSourceTypes.new(platformId=platformId,
                                contentSourceType=typeName)
            except mint_error.DuplicateItem, e:
                # No need to raise this, the data is already created.
                pass

        return platform

    def _syncDb(self, dbPlatforms, cfgPlatforms):
        changed = False
        dbPlatformLabels = [d.label for d in dbPlatforms]

        for cfgPlatform in cfgPlatforms:
            if cfgPlatform.label not in dbPlatformLabels:
                changed = True
                self._create(cfgPlatform)

        return changed                

    def _linkToSource(self, platformId, contentSourceId):
        platformId = int(platformId)

        # Do nothing if the source is already there.
        sources = self.db.db.platformsPlatformSources.getAllByPlatformId(platformId)
        sources = [s for s in sources if s[1] == contentSourceId]
        if sources:
            return

        self.db.db.platformsPlatformSources.new(platformId=platformId,
            platformSourceId=contentSourceId)

    def _linkToSourceType(self, platformId, contentSourceType):
        platformId = int(platformId)

        # Do nothing if the source is already there.
        types = self.db.db.platformsContentSourceTypes.getAllByPlatformId(platformId)
        for t in types:
            if t[1] == contentSourceType:
                return

        self.db.db.platformsContentSourceTypes.new(platformId=platformId,
            contentSourceType=contentSourceType)

    def _populateFromCfg(self, dbPlatforms, cfgPlatforms):
        dbLabels = [p.label for p in dbPlatforms]
        cfgLabels = [p.label for p in cfgPlatforms]

        fields = ['platformName', 'platformUsageTerms', 'hostname',
                  '_sourceTypes', '_buildTypes', 'configurable']

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

        # Append any other platforms not found in the cfg onto our new list.
        for i, d in enumerate(dbLabels):
            if d not in cfgLabels:
                platforms.append(dbPlatforms[i])

        # Link the platforms to all of it's source types and sources.
        for p in platforms:
            for sourceType, isSingleton in p._sourceTypes:
                contentSourceType = self.mgr.contentSourceTypes.getIdByName(sourceType)
                self._linkToSourceType(p.platformId, contentSourceType)
                contentSources = self.mgr.contentSources.listByType(
                                    contentSourceType, createPlatforms=False)
                for s in contentSources.instance:
                    self._linkToSource(p.platformId, s.contentSourceId)

        # Also check for mirroring permissions for configurable platforms.
        # This is the best place to do this, since this method always gets
        # called when fetching a platform.
        if self.db.siteAuth:
            for p in platforms:
                if p.label in self.cfg.configurablePlatforms:
                    p.mirrorPermission = self._checkMirrorPermissions(p)
                else:
                    p.mirrorPermission = False

        return platforms

    def _checkMirrorPermissions(self, platform):
        try:
            self.db.productMgr.reposMgr.checkExternalRepositoryAccess(
                self._getHost(platform), 
                self._getDomainname(platform), 
                self._getUrl(platform), 
                self._getAuthInfo())
        except errors.ExternalRepositoryMirrorError, e:
            return False
        else:
            return True

    def _listFromCfg(self):
        platforms = []
        for label, name, usageTerms, buildTypes, enabled, sourceTypes, configurable in self._iterConfigPlatforms():
            platform = self._platformModelFactory(label=label,
                                platformName=name,
                                platformUsageTerms=usageTerms,
                                platformBuildTypes=buildTypes,
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

                os.chdir('/')
                self.db.db.reopen_fork()
                function(*args, **kw)
            except:
                try:
                    exc_info = sys.exc_info()
                    if hasattr(function, 'error'):
                        function.error(self, exc_info)
                    else:
                        log.error("Unhandled error in background operation:",
                                exc_info=exc_info)
                finally:
                    os._exit(1)
        finally:
            os._exit(0)

    def load(self, platformId, platformLoad):
        platform = self.getById(platformId)
        host = platform.label.split('@')[:1][0]
        repos = self.db.productMgr.reposMgr.getRepositoryClientForProduct(host)
        uri = platformLoad.uri.encode('utf-8')
        headers = {}
        fd, outFilePath = tempfile.mkstemp('.ccs', 'platform-load-')

        finder = lookaside.FileFinder(None, None, cfg = self.cfg)
        inFile = finder._fetchUrl(uri, headers)

        if not inFile:
            raise errors.PlatformLoadFileNotFound(uri)

        jobId = self.db.db.platformLoadJobs.new(platformId=platformId, message='')
        platLoad = models.PlatformLoad()
        platLoad.jobId = jobId
        platLoad.platformId = platformId
        platLoad.uri = platformLoad.uri

        self.backgroundRun(self._load, platform, jobId, inFile, outFilePath,
                           uri, repos)

        return platLoad

    def _load(self, platform, jobId, inFile, outFilePath, uri, repos):
        platformId = platform.platformId
        callback = PlatformLoadCallback(self.db, platformId, jobId, None)
        # Save a reference to the callback so that we have access to it in the
        # _load_error method.
        self.callback = callback


        if inFile.headers.has_key('content-length'):
            totalKB = int(inFile.headers['content-length'])
            callback.totalKB = totalKB
        
        outFile = open(outFilePath, 'w')
        total = util.copyfileobj(inFile, outFile,
                                 callback=callback.downloading)
        outFile.close()

        callback._message('Download Complete. Figuring out what to commit..')
        try:
            cs = changeset.ChangeSetFromFile(outFilePath) 
        except filecontainer.BadContainer:
            raise Exception("%s is not a valid conary changeset." % uri)
        removedTroves = self._filterChangeSet(cs, platform.label)
        needsCommit = cs.removeCommitted(repos)

        if needsCommit:
            repos.commitChangeSet(cs, callback=callback, mirror=True)
            callback._message('Commit completed.')
        else:
            callback._message('Nothing needs to be committed. Local Repository '
                              'is up to date.')
        callback.done()            

        return 

    def _filterChangeSet(self, cs, label):
        fqdn = label.split('@')[0]
        removedTroves = []
        for trove in cs.iterNewTroveList():
            if trove.getNewVersion().getHost() != fqdn:
                removedTroves.append(trove.getNewNameVersionFlavor())

        for tup in removedTroves:
            cs.delNewTrove(*tup)

        return removedTroves

    def _load_error(self, exc_info):
        log.error("Unhandled error in platform slice manual load:",
                exc_info=exc_info)
        self.callback.error(exc_info[1])
    _load.error = _load_error

    def _getProjectId(self, platformId):
        plat = self.db.db.platforms.get(platformId)
        return plat.get('projectId', None)

    def _getUsableProject(self, platformId, hostname, domainname, url,
                          authInfo, mirror):
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

                if mirror:
                    # Check if there is a mirror set up.
                    try:
                        mirrorId = self.db.db.inboundMirrors.getIdByColumn(
                                    'targetProjectId', projectId)
                    except mint_error.ItemNotFound, e:
                        # Add an inboud mirror for this external project.
                        self.db.productMgr.reposMgr.addIncomingMirror(
                            projectId, hostname, domainname, url, authInfo, True)

            # Add the project to our platform
            self.db.db.platforms.update(platformId, projectId=projectId)

        return projectId

    def _getHostname(self, platform):
        label = versions.Label(platform.label)
        return str(label.getHost())

    def _getHost(self, platform):
        hostname = self._getHostname(platform)
        parts = hostname.split('.', 1)
        return parts[0]

    def _getDomainname(self, platform):
        hostname = self._getHostname(platform)
        parts = hostname.split('.', 1)
        host = parts[0]
        if len(parts) == 1:
            domainname = ''
        else:
            domainname = ''.join(parts[1:])

        return domainname

    def _getUrl(self, platform):
        hostname = self._getHostname(platform)
        return 'https://%s/conary/' % (hostname)

    def _getAuthInfo(self):
        # Use the entitlement from /srv/rbuilder/data/authorization.xml
        if self.db.siteAuth:
            entitlement = self.db.siteAuth.entitlementKey
            return models.AuthInfo(authType='entitlement',
                    entitlement=entitlement)
        else:
            return models.AuthInfo(authType='none')

    def _setupPlatform(self, platform):
        platformId = int(platform.platformId)
        platformName = str(platform.platformName)
        hostname = self._getHostname(platform)
        host = self._getHost(platform)
        url = self._getUrl(platform)
        domainname = self._getDomainname(platform)
        mirror = platform.label in self.cfg.configurablePlatforms

        authInfo = self._getAuthInfo()

        # Get the productId to see if this platform has already been
        # associated with an external product.
        projectId = self._getProjectId(platformId)

        if not projectId:
            projectId = self._getUsableProject(platformId, hostname,
                            domainname, url, authInfo, mirror)

        if not projectId:            
            # Still no project, we need to create a new one.
            try:
                projectId = self.db.productMgr.createExternalProduct(platformName, host, 
                                domainname, url, authInfo, mirror=mirror)
            except mint_error.RepositoryAlreadyExists, e:
                projectId = self.db.db.projects.getProjectIdByFQDN(hostname)

            self.db.db.platforms.update(platformId, projectId=projectId)

        return projectId

    def update(self, platformId, platform):
        if platform.enabled:
            self._setupPlatform(platform)

        self.db.db.platforms.update(platformId, enabled=int(platform.enabled))
        self.db.db.platforms.update(platformId, mode=platform.mode)

        return self.getById(platformId)

    def list(self):
        dbPlatforms = self._listFromDb()
        cfgPlatforms = self._listFromCfg()
        changed = self._syncDb(dbPlatforms, cfgPlatforms)
        if changed:
            dbPlatforms = self._listFromDb()

        dbPlatforms = self._populateFromCfg(dbPlatforms, cfgPlatforms)            
            
        return models.Platforms(dbPlatforms)

    def _getStatus(self, platform):
        platStatus = models.PlatformSourceStatus()
        remote = True
        remoteMessage = ''
        remoteConnected = True
        local = False
        localMessage = ''
        localConnected = False

        if not platform.enabled:
           platStatus.valid = False
           platStatus.connected = False
           platStatus.message = "Platform must be enabled to check its status."
           return platStatus

        openMsg = "Repository not responding: %s."
        connectMsg = "Error connecting to repository %s: %s."
        pDefNotFoundMsg = "Platform definition not found in repository %s."
        sliceUrl = "http://docs.rpath.com/platforms/platform_repositories.html"
        pDefNotFoundMsgLocal = "Repository is empty, please manually load " + \
            "the base slice for this platform available from %s."
        successMsg = "Available."

        if platform.mode == 'auto':
            client = self._reposMgr.getAdminClient()
            from mint.db import repository as reposdb
            host = platform.label.split('@')[0]
            entitlement = self.db.productMgr.reposMgr.db.siteAuth.entitlementKey
            # Go straight to the host as defined by the platform, bypassing
            # any local repo map.
            sourceUrl = self._getUrl(platform)
            try:
                serverProxy = self.db.productMgr.reposMgr.reposManager.getServerProxy(host,
                    sourceUrl, None, [entitlement])
                client.repos.c.cache[host] = serverProxy
                platDef = proddef.PlatformDefinition()
                platDef.loadFromRepository(client, platform.label)
            except reposErrors.OpenError, e:
                remote = False
                remoteConnected = False
                remoteMessage = openMsg % sourceUrl
            except conaryErrors.ConaryError, e:
                remote = False
                remoteConnected = True
                remoteMessage = connectMsg % (sourceUrl, e)
            except proddef.ProductDefinitionTroveNotFoundError, e:
                remote = False
                remoteConnected = True
                remoteMessage = pDefNotFoundMsg % sourceUrl
            except Exception, e:
                remote = False
                remoteConnected = False
                # Hard code a helpful message for the sle platform.
                if 'sle.rpath.com' in platform.label:
                    remoteMessage = "This platform requires a " + \
                        "commercial license.  You are either missing the " + \
                        "entitlement for this platform or it is no longer valid"
                else:
                    remoteMessage = connectMsg % (sourceUrl, e)

        client = self._reposMgr.getAdminClient()
        platDef = proddef.PlatformDefinition()
        url = self._reposMgr._getFullRepositoryMap().get(
                platform.repositoryHostname, self._getUrl(platform))

        try:
            platDef.loadFromRepository(client, platform.label)
        except reposErrors.OpenError, e:
            local = False
            localConnected = False
            localMessage = openMsg % url 
        except conaryErrors.ConaryError, e:
            local = False
            localConnected = True
            localMessage = connectMsg % (url, e)
        except proddef.ProductDefinitionTroveNotFoundError, e:
            local = False
            localConnected = True
            localMessage = pDefNotFoundMsgLocal % sliceUrl
        except Exception, e:
            local = False
            localConnected = False
            localMessage = connectMsg % (url, e)
        else:            
            local = True
            localConnected = True

        platStatus.valid = local and remote
        platStatus.connected = localConnected and remoteConnected
        if platStatus.valid:
            platStatus.message = successMsg
        else:
            platStatus.message = ' '.join([remoteMessage, localMessage])

        return platStatus

    def getStatusTest(self, platform):
        return self._getStatus(platform)

    def getStatus(self, platformId):
        platform = self.getById(platformId)
        return self._getStatus(platform)

    def getLoadStatus(self, platformId, jobId):
        status = models.PlatformLoadStatus()
        message = self.db.db.platformLoadJobs.get(jobId)['message']
        done = self.db.db.platformLoadJobs.get(jobId)['done']
        error = self.db.db.platformLoadJobs.get(jobId)['error']
        if bool(done):
            code = jobstatus.FINISHED
        elif bool(error):
            code = jobstatus.ERROR
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

    def getByLabel(self, platformLabel):
        if platformLabel is None:
            return None
        # XXX Surely we can do this without enumerating all platforms first
        platforms = self.list()
        platforms = [p for p in platforms.platforms \
                    if p.label == platformLabel]
        if not platforms:
            return None
        return platforms[0]

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
        encFields = sourceType.getEncryptedFieldNames()
        
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
                if d['name'] in encFields:
                    value = base64.decodestring(d['value'])
                else:
                    value = d['value']
                setattr(model, d['name'], value)

        model.enabled = True
        for field in sourceType.fields:
            if field.required:
                val = getattr(model, field.name, None)
                if not val:
                    model.enabled = False

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
        typeName = self.contentSourceTypes.getIdByName(source.contentSourceType)
        try:
            sourceId = self.db.db.platformSources.new(
                    name=source.name,
                    shortName=source.shortName,
                    defaultSource=int(source.defaultSource),
                    contentSourceType=typeName,
                    orderIndex=source.orderIndex)
        except mint_error.DuplicateItem, e:
            log.error("Error creating content source %s, it must already "
                      "exist: %s" % (source.shortName, e))
            return self.db.db.platformSources.getIdFromShortName(source.shortName)

        cu = self.db.cursor()
        sql = """
        INSERT INTO platformSourceData
        VALUES (%s, '%s', '%s', 3)
        """

        sourceClass = contentsources.contentSourceTypes[source.contentSourceType]
        sourceInst = sourceClass()
        encFields = sourceInst.getEncryptedFieldNames()

        for field in ['username', 'password', 'sourceUrl']:
            value = getattr(source, field, None)

            if value:
                if field in encFields :
                    value = base64.encodestring(value)

                cu.execute(sql % (sourceId, field, value))

        source.contentSourceId = sourceId
        self._linkToPlatforms(source)

        return sourceId      

    def _syncDb(self, dbSources, cfgSources, createPlatforms):
        changed = False
        dbNames = [s.shortName for s in dbSources]

        createdPlatforms = False or not createPlatforms
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

    def list(self, createPlatforms=True):
        dbSources = self._listFromDb()
        cfgSources = self._listFromCfg()
        changed = self._syncDb(dbSources, cfgSources, createPlatforms)
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
        encFields = sourceInst.getEncryptedFieldNames()

        for field in sourceInst.getFieldNames():
            newVal = str(getattr(source, field))

            if field in encFields:
                newVal = base64.encodestring(newVal)

            if getattr(oldSource, field) != newVal:
                row = cu.execute(selSql, field, source.contentSourceId)
                if row.fetchall():
                    cu.execute(updSql, newVal, field, 
                        source.contentSourceId)
                else:
                    self.db.db.platformSourceData.new(
                                platformSourceId=source.contentSourceId,
                                name=str(field),
                                value=newVal,
                                dataType=3)

        return self.getByShortName(source.shortName)

    def getByShortName(self, shortName):
        sources = self.list()
        sources = [s for s in sources.instance \
                   if s.shortName == shortName]
        return sources[0]

    def listByType(self, sourceType, createPlatforms=True):
        sources = self.list(createPlatforms)
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
                    missing.append(field.prompt)

        if missing:
            message = "The following fields must be provided to check " + \
                      "a source's status: %s." % ', '.join(missing)
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

    def getPlatformImageTypeDefs(self, request, platformId):
        platform = self.platforms.getById(platformId)
        templates = models.PlatformBuildTemplates()
        platDef = self.platformCache.get(platform.label)
        from mint import buildtypes
        from mint.rest.api import productversion
        buildDefModels = []
        for buildDef in platform._buildTypes:
            kw = {'platform':platformId}
            buildDefId = productversion.BuildDefinitionMixIn.getBuildDefId(buildDef)
            extra = {'platform':platformId, 'imageTypeDefinitions': buildDefId}
            displayName = getattr(buildDef, "displayName", buildDef.name)
            kw.update(dict(name = buildDef.name,
                displayName = displayName,
                id = buildDefId))
            
            if buildDef.flavorSetRef:
                fset = buildDef.flavorSetRef
                fset = platDef.getFlavorSet(fset)
                if fset:
                    kw['flavorSet'] = models.PlatformFlavorSet(id = fset.name,
                                                        name = fset.name,
                                                        displayName = fset.displayName, **extra)

            if buildDef.architectureRef:
                arch = buildDef.architectureRef
                arch = platDef.getArchitecture(arch)
                if arch:
                    kw['architecture'] = models.PlatformArchitecture(id = arch.name,
                                                            name = arch.name,
                                                            displayName = arch.displayName, **extra)

            if buildDef.containerTemplateRef:
                ctemplRef = buildDef.containerTemplateRef
                ctempl = platDef.getContainerTemplate(ctemplRef)
                if ctempl and ctemplRef in buildtypes.xmlTagNameImageTypeMap:
                    displayName = buildtypes.xmlTagNameImageTypeMap[ctemplRef]
                    displayName = buildtypes.typeNamesMarketing[displayName]
                    if hasattr(buildDef, 'getBuildImage'):
                    # This is a build
                        imageField = buildDef.getBuildImage()
                    else:
                    # This is a build template
                        imageField = ctempl
                    imageParams = models.ImageParams(**imageField.fields)
                    kw['container'] = models.PlatformContainerFormat(
                        id = ctemplRef,
                        name = ctemplRef,
                        displayName = displayName,
                        options = imageParams, **extra)

            model = models.PlatformBuildTemplate(**kw)
            buildDefModels.append(model)
        bdefs = models.BuildTemplates(buildTemplates = buildDefModels)
        return bdefs

    def getPlatformByLabel(self, platformLabel):
        return self.platforms.getByLabel(platformLabel)

    def loadPlatform(self, platformId, platformLoad):
        return self.platforms.load(platformId, platformLoad)

    def getPlatformStatus(self, platformId):
        return self.platforms.getStatus(platformId)

    def getPlatformStatusTest(self, platform):
        return self.platforms.getStatusTest(platform)

    def getPlatformLoadStatus(self, platformId, jobId):
        return self.platforms.getLoadStatus(platformId, jobId)

    def getSourceTypeDescriptor(self, sourceType):
        return self.contentSourceTypes.getDescriptor(sourceType)

    def getSourceTypesByPlatform(self, platformId):
        platform = self.platforms.getById(platformId)
        types = []
        for sourceType, isSingleton in platform._sourceTypes:
            types.append(models.SourceType(contentSourceType=sourceType,
                singleton=isSingleton))

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
                      WHERE Platforms.enabled != 0
        """
        cu = self.db.cursor()
        cu.execute(sql)
        return [ x[0] for x in cu ]

class PlatformDefCache(persistentcache.PersistentCache):
    def __init__(self, cacheFile, reposMgr):
        persistentcache.PersistentCache.__init__(self, cacheFile)
        self._reposMgr = weakref.ref(reposMgr)

    def _getPlatDef(self, client, labelStr):
        try:
            platDef = proddef.PlatformDefinition()
            platDef.loadFromRepository(client, labelStr)
        except reposErrors.InsufficientPermission, err:
            log.error("Failed to lookup platform definition on label %s: %s",
                    labelStr, str(err))
            return None
        except proddef.ProductDefinitionTroveNotFoundError, e:
            # Re-raise so this can be handled by the _refresh method.
            raise e
        except:
            log.exception("Failed to lookup platform definition on label %s:",
                    labelStr)
            return None

        return platDef            

    def _refresh(self, labelStr):
        reposMgr = self._reposMgr()
        try:
            client = reposMgr.getAdminClient()
            platDef = self._getPlatDef(client, labelStr)
            return platDef
        except proddef.ProductDefinitionTroveNotFoundError, e:
            log.error("Failed to find product definition  for platform.  Will "
                      "try looking on platform source label.")

            # Need to look at inboundmirrors table to get the sourceurl 
            # for the platform so that we bypass the local repo.
            sourceUrl = reposMgr.getIncomingMirrorUrlByLabel(labelStr)
            host = labelStr.split('@')[0]

            if not sourceUrl:
                # Try going straight to the platform label
                sourceUrl = "https://%s/conary/" % host

            try:
                from mint.db import repository as reposdb
                entitlement = reposMgr.db.siteAuth.entitlementKey
                serverProxy = reposMgr.reposManager.getServerProxy(host,
                    sourceUrl, None, [entitlement])
                client.repos.c.cache[host] = serverProxy
                platDef = self._getPlatDef(client, labelStr)
                return platDef
            except Exception, e:
                log.error("Platform Definition not found for %s: %s" % (labelStr, e))
                return None


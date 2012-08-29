#
# Copyright (c) rPath, Inc.
#

import base64
import logging
import os
import sys
import tempfile
import time
import traceback
import weakref

from conary import errors as conaryErrors
from conary import versions
from conary.dbstore import sqllib
from conary.build import lookaside
from conary.lib import util
from conary.repository import errors as reposErrors

from mint import jobstatus
from mint import mint_error
from mint.db import repository
from mint.lib import persistentcache
from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import contentsources
from mint.rest.db import manager
from mint.scripts import pkgindexer

from rpath_proddef import api1 as proddef
from rpath_job import api1 as rpath_job

log = logging.getLogger(__name__)


class PlatformLoadCallback(repository.DatabaseRestoreCallback):
    def __init__(self, db, job, totalKB):
        self.db = db
        self.job = job
        self.totalKB = totalKB
        self.last = 0
        repository.DatabaseRestoreCallback.__init__(self)
        
    def _message(self, txt):
        log.info(txt)
        self.job.message = txt

    def done(self):
        self.job.status = self.job.STATUS_COMPLETED

    def error(self, txt):
        txt = "Load Failed: %s" % txt
        log.error(txt)
        self.job.status = self.job.STATUS_FAILED
        self.job.message = txt

    def downloading(self, got, rate):
        if time.time() - self.last < 1:
            return
        self.last = time.time()
        self._downloading('Downloading', got, rate, self.totalKB)

    def _downloading(self, msg, got, rate, total):
        if not total:
            totalMsg = ''
            totalPct = ''
        else:
            totalMsg = 'of %dMB ' % (total / 1024 / 1024)
            totalPct = '(%d%%) ' % ((got * 100) / total)

        self._message("%s %dMB %s%sat %dKB/sec"
                   % (msg, got/1024/1024, totalMsg, totalPct, rate/1024))

    def _info(self, message, *args):
        self._message(message % args)

    def _error(self, message, *args):
        self.error(message % args)


class ContentSourceTypes(object):
    def __init__(self, db, cfg, mgr):
        self.db = db
        self.cfg = cfg
        self.mgr = weakref.ref(mgr)

    @classmethod
    def contentSourceTypeModelFactory(cls, name, singleton = None, id = None,
            required=False):
        if id is None:
            id = name
        return models.SourceType(contentSourceType=name, singleton=singleton,
            id = name, required=required)

    def _listFromCfg(self):
        allTypesMap = dict()
        allTypes = []
        pIter = self.mgr().platforms.iterPlatforms(withRepositoryLookups=True)
        isOffline = self.db.siteAuth.isOffline()
        for platform in pIter:
            sourceTypes = platform._sourceTypes
            for t, isSingleton in sourceTypes or []:
                if t not in allTypes:
                    cst = contentsources.contentSourceTypes[t]
                    if isOffline and not cst.enabledInOfflineMode:
                        continue
                    allTypes.append(t)
                    allTypesMap[t] = (isSingleton, cst.isRequired)

        stypes = []
        for stype in allTypes:
            isSingleton, isRequired = allTypesMap[stype]
            stype = self.contentSourceTypeModelFactory(name=stype,
                singleton=isSingleton, required=isRequired)
            stypes.append(stype)

        return stypes

    def listByName(self, sourceTypeName):
        stypes = self.list()
        stype = [t for t in stypes.contentSourceTypes
                 if t.contentSourceType == sourceTypeName]

        if not stype:
            # A content source type defined in the config, could not be found
            # in the platform definitions.
            raise errors.ContentSourceTypeNotDefined(sourceTypeName)

        return stype[0]

    def getIdByName(self, sourceTypeName):
        s = self.listByName(sourceTypeName)
        return s.id

    def list(self):
        cfgTypes = self._listFromCfg()
        return models.SourceTypes(cfgTypes)

    def _getSourceTypeInstance(self, source):
        sourceClass = contentsources.contentSourceTypes[source.contentSourceType]
        sourceInst = sourceClass(proxyMap=self.db.cfg.getProxyMap())
        for field in sourceInst.getFieldNames():
            if hasattr(source, field):
                val = str(getattr(source, field))
                setattr(sourceInst, field, val)

        return sourceInst   

    def _getSourceTypeInstanceByName(self, sourceType):
        sourceClass = contentsources.contentSourceTypes[sourceType]
        return sourceClass(proxyMap=self.db.cfg.getProxyMap())

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

class PlatformJobStore(rpath_job.SqlJobStore):
    jobType = 'platform-load'

class LoadRunner(rpath_job.BackgroundRunner):

    def __init__(self, func, db):
        rpath_job.BackgroundRunner.__init__(self, func)
        self.db = db

    def postFork(self):
        """Unshare database connection with parent process."""
        self.db.reopen_fork()

    def handleError(self, exc_info):
        log.error("Unhandled error in platform slice manual load:",
                exc_info=exc_info)
        self.callback.error(exc_info[1])

class Platforms(object):

    def __init__(self, db, cfg, mgr):
        self.platforms = []
        self.db = db
        self.cfg = cfg
        self.mgr = weakref.ref(mgr)
        cacheFile = os.path.join(self.cfg.dataPath, 'data', 
                                 'platformName.cache')
        self.platformCache = PlatformDefCache(cacheFile, mgr)
        self.jobStore = PlatformJobStore(self.db)
        self.loader = LoadRunner(self._load, self.db)

    def iterPlatforms(self, withRepositoryLookups=True):
        platforms = []
        dbPlatforms = self.db.db.platforms.getAll()
        for platform in dbPlatforms:
            platforms.append(self.getPlatformModelFromRow(platform,
                withRepositoryLookups=withRepositoryLookups))
        return platforms

    def getPlatformModelFromRow(self, platformRow, withRepositoryLookups=True,
            withComputedFields=True):
        platform = self._platformModelFactory(**dict(platformRow))
        return self.getPlatformModel(platform,
            withRepositoryLookups=withRepositoryLookups,
            withComputedFields=withComputedFields)

    def getPlatformModel(self, platform, withRepositoryLookups=True,
            withComputedFields=True):
        if withRepositoryLookups:
            platformDef = self.platformCache.get(str(platform.label))
        else:
            platformDef = None
        self._updatePlatformFromPlatformDefinition(platform, platformDef)
        if withComputedFields:
            self._addComputedFields(platform)
        return platform

    def _getPlatformTroveName(self, platform):
        platformDef = self.platformCache.get(str(platform.label))
        if not platformDef:
            return None
        srcTroves = [s for s in platformDef.getSearchPaths() \
            if s.isPlatformTrove]
        if srcTroves:
            return srcTroves[0].troveName
        else:
            return None

    def getPlatformVersions(self, platformId, platformVersionId=None):
        platform = self.getById(platformId)

        if platformVersionId:
            platformTroveName, revision = platformVersionId.split('=')
        else:
            platformTroveName = self._getPlatformTroveName(platform)
            if not platformTroveName:
                platformVersions = models.PlatformVersions()
                platformVersions.platformVersion = []
                return platformVersions
            revision = None

        host = platform.label.split('@')[:1][0]
        label = platform.label
        if not label.startswith('/'):
            label = '/%s' % label
        conaryLabel = versions.VersionFromString(label).label()
        repos = self.db.productMgr.reposMgr.getRepositoryClientForProduct(host)
        repoTroves = repos.findTroves(conaryLabel, 
            [(platformTroveName, None, None)], getLeaves=False)

        try:
            platformTroves = repoTroves[(platformTroveName, None, None)]
        except KeyError, e:
            # TODO: something else?
            raise e

        _platformVersions = []
        seenRevisions = []
        for platformTrove in platformTroves:
            version = platformTrove[1]
            versionRevision = version.trailingRevision()
            strRevision = versionRevision.asString()

            # Because of flavors, there may be multiples of the same revision.
            # We don't need to worry about flavors when rebasing.
            if strRevision in seenRevisions:
                continue

            seenRevisions.append(strRevision)
            timeStamp = versionRevision.timeStamp
                
            platformVersion = models.PlatformVersion(
                name=platformTroveName, version=version.asString(),
                revision=strRevision, label=label,
                ordering=timeStamp)
            platformVersion._platformId = platformId

            if revision is not None and revision == strRevision:
                return platformVersion

            _platformVersions.append(platformVersion)

        platformVersions = models.PlatformVersions()
        platformVersions.platformVersion = _platformVersions

        return platformVersions

    def getPlatformVersion(self, platformId, platformVersionId):
        return self.getPlatformVersions(platformId, platformVersionId)

    def _updatePlatformFromPlatformDefinition(self, platformModel, platformDef):
        if platformDef is None:
            platformName = platformModel.platformName
            platformUsageTerms = None
            platformBuildTypes = []
            types = None
        else:
            platformName = platformDef.getPlatformName()
            platformUsageTerms = platformDef.getPlatformUsageTerms()
            platformProv = platformDef.getContentProvider()
            if platformProv:
                types = [(t.name, t.isSingleton)
                    for t in platformProv.contentSourceTypes]
            else:
                types = []
            platformBuildTypes = platformDef.getBuildTemplates()
        platformModel.updateFields(
            platformName=platformName,
            platformUsageTerms=platformUsageTerms,
            _sourceTypes=types,
            _buildTypes=platformBuildTypes,
        )
        return platformModel

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
        abstract = kw.get('abstract', None)
        sourceTypes = kw.get('sourceTypes', [])
        mode = kw.get('mode', 'manual')
        hidden = kw.get('hidden', None)
        platformUsageTerms = kw.get('platformUsageTerms')
        platform = models.Platform(platformId=platformId, label=label,
                platformName=platformName, enabled=enabled,
                platformUsageTerms=platformUsageTerms,
                configurable=configurable, mode=mode,
                repositoryHostname=fqdn, abstract=abstract,
                hidden=hidden)
        platform._sourceTypes = sourceTypes
        platform._buildTypes = platformBuildTypes
        return platform

    def _create(self, platformModel, platformDef, projectId=None):
        platformLabel = str(platformModel.label)
        params = dict(
            platformName=platformModel.platformName,
            abstract=bool(platformModel.abstract),
            configurable=bool(platformModel.configurable),
            label=platformLabel,
            enabled=int(platformModel.enabled or 0),
            projectId=projectId,
        )

        # isFromDisk is a field that's not exposed in the API, so treat it
        # differently
        params.update(isFromDisk=getattr(platformModel, 'isFromDisk', False))

        try:
            platformId = self.db.db.platforms.new(**params)
            log.info("Created platform %s with id %s", platformLabel,
                    platformId)
        except mint_error.DuplicateItem, e:
            platformId = self.db.db.platforms.getIdByColumn('label',
                platformLabel)
            log.error("Error creating platform %s, it must already "
                      "exist: %s" % (platformLabel, e))

        platformModel.platformId = platformId
        self._updateDatabasePlatformSources(platformModel, platformDef)
        return platformId

    def _update(self, platformModel, platformDef):
        platformId = platformModel.platformId
        platformName = platformModel.platformName
        abstract = bool(platformModel.abstract)
        configurable = bool(platformModel.configurable)
        cu = self.db.db.cursor()
        sql = """UPDATE Platforms
            SET platformName = ?,
                abstract = ?,
                configurable = ?,
                time_refreshed = current_timestamp
            WHERE platformId = ?"""
        cu.execute(sql, platformName, abstract, configurable, platformId)
        self._updateDatabasePlatformSources(platformModel, platformDef)
        return platformId

    def _addComputedFields(self, platformModel):
        # Also check for mirroring permissions for configurable platforms.
        # This is the best place to do this, since this method always gets
        # called when fetching a platform.
        if self.db.siteAuth:
            if platformModel.configurable:
                # XXX this is a hack, we need the platform model passed to the
                # platform cache somehow
                self._platformModel = platformModel
                mirrorPermission = self.platformCache.getMirrorPermission(platformModel.label)
                del self._platformModel
            else:
                mirrorPermission = False
            platformModel.mirrorPermission = mirrorPermission

    def _updateDatabasePlatformSources(self, platformModel, platformDef):
        platformId = platformModel.platformId
        self._linkPlatformToSourceTypes(platformModel, platformDef)
        contentSourceIds = set()
        for contentSourceType, isSingleton in (platformModel._sourceTypes or []):
            contentSources = self.mgr().contentSources.listByType(contentSourceType)
            contentSourceIds.update(x.contentSourceId for x in contentSources.instance)
        self.db.db.platformsPlatformSources.sync(platformId=platformId,
            platformSourceIds=contentSourceIds)

    def _linkPlatformToSourceTypes(self, platformModel, platformDef):
        self._updatePlatformFromPlatformDefinition(platformModel, platformDef)
        if platformModel._sourceTypes is not None:
            cst = [ x[0] for x in platformModel._sourceTypes ]
            self._linkToSourceTypes(platformModel.platformId, cst)

    def _linkToSourceTypes(self, platformId, contentSourceTypes):
        platformId = int(platformId)
        self.db.db.platformsContentSourceTypes.sync(platformId,
            contentSourceTypes)

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

    def load(self, platformId, platformLoad):
        platform = self.getById(platformId)
        host = platform.label.split('@')[:1][0]
        repos = self.db.productMgr.reposMgr.getRepositoryClientForProduct(host)
        loadUri = platformLoad.loadUri.encode('utf-8')
        headers = {}
        fd, outFilePath = tempfile.mkstemp('.tar', 'platform-load-')

        finder = lookaside.FileFinder(None, None, cfg = self.cfg)
        inFile = finder._fetchUrl(loadUri, headers)

        if not inFile:
            raise errors.PlatformLoadFileNotFound(loadUri)

        job = self.jobStore.create()

        platLoad = models.PlatformLoad()
        platLoad.jobId = job.id
        platLoad.platformId = platformId
        platLoad.loadUri = platformLoad.loadUri

        self.loader(platform, job.id, inFile, outFilePath, loadUri, repos)

        return platLoad

    def _load(self, platform, jobId, inFile, outFilePath, uri, repos):
        # Open the job and commit after each state change
        job = self.jobStore.get(jobId, commitAfterChange = True)
        job.setFields([('pid', os.getpid()), ('status', job.STATUS_RUNNING) ])

        try:
            if inFile.headers.has_key('content-length'):
                totalKB = int(inFile.headers['content-length'])
            else:
                totalKB = None

            callback = PlatformLoadCallback(self.db, job, totalKB)
            # Save a reference to the callback so that we have access to it in the
            # _load_error method.
            self.callback = callback
            
            outFile = open(outFilePath, 'w')
            total = util.copyfileobj(inFile, outFile,
                                     callback=callback.downloading)
            outFile.close()

            callback._message('Download Complete. Loading preload...')
            reposManager = self.db.reposShim
            repoHandle = reposManager.getRepositoryFromFQDN(
                    platform.repositoryHostname)
            repoHandle.restoreBundle(outFilePath, replaceExisting=True,
                callback=callback)

            # Recreate anonymous and mintauth users.
            self.db.productMgr.reposMgr.populateUsers(repoHandle)

            # Clear the cache of status information
            self.platformCache.clearPlatformData(platform.label)

            callback._message('Load completed.')
            callback.done()
            os.unlink(outFilePath)
        except:
            log.exception("Unhandled exception loading platform repository:")
            exc_info = sys.exc_info()
            lines = traceback.format_exception_only(exc_info[0], exc_info[1])
            callback.error('\n'.join(lines))

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


    def _getProjectId(self, platformId):
        plat = self.db.db.platforms.get(platformId)
        return plat.get('projectId', None)

    def _getUsableProject(self, platformId, hostname):
        projectId = self._getProjectId(platformId)
        if projectId:
            return projectId

        # See if there is project already setup that shares
        # the fqdn of the platform.
        try:
            projectId = self.db.db.projects.getProjectIdByFQDN(hostname)
        except mint_error.ItemNotFound, e:
            projectId = None

        return projectId

    def _setupExternalProject(self, hostname, domainname, authInfo, 
                              url, projectId, mirror):
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
        projectId = self._getUsableProject(platform.platformId, hostname)
        if projectId:
            project = self.db.db.projects.get(projectId)
            local = not(project['external'] == 1)
        else:
            local = False

        if local:
            return 'https://%s/repos/%s/' % \
                (self.cfg.secureHost, hostname)
        else:
            # XXX Don't leave this hard-coded forever
            if hostname == 'centos.rpath.com':
                return 'https://centos.rpath.com/nocapsules/'
            elif hostname == 'centos6.rpath.com':
                return 'https://centos6.rpath.com/nocapsules/'
            return 'https://%s/conary/' % (hostname)

    def _getAuthInfo(self):
        # Use the entitlement from /srv/rbuilder/data/authorization.xml
        if self.db.siteAuth:
            entitlement = self.db.siteAuth.entitlementKey
            return models.AuthInfo(authType='entitlement',
                    entitlement=entitlement)
        else:
            return models.AuthInfo(authType='none')

    def _updateInternalPackageIndex(self):
        """
        Update the internal package index
        """
        upi = pkgindexer.UpdatePackageIndex()
        return upi.run()

    def _updateExternalPackageIndex(self):
        """
        Update the external package index.
        """
        upie = pkgindexer.UpdatePackageIndexExternal()
        return upie.run()

    def _setupPlatform(self, platform):
        platformId = int(platform.platformId)
        platformName = str(platform.platformName)
        hostname = self._getHostname(platform)
        host = self._getHost(platform)
        url = self._getUrl(platform)
        domainname = self._getDomainname(platform)
        mirror = platform.configurable

        authInfo = self._getAuthInfo()

        # Get the projectId to see if this platform has already been
        # associated with an external project.
        projectId = self._getProjectId(platformId)

        if not projectId:
            projectId = self._getUsableProject(platformId, hostname)
            if projectId:
                # Add the project to our platform
                self.db.db.platforms.update(platformId, 
                    projectId=projectId)
                project = self.db.db.projects.get(projectId)
                if project['external'] == 1:
                    self._setupExternalProject(hostname, domainname, 
                        authInfo, url, projectId, mirror)
                    self._updateExternalPackageIndex()
                else:
                    self._updateInternalPackageIndex()

        if not projectId:
            # Still no project, we need to create a new one.
            try:
                projectId = self.db.productMgr.createExternalProduct(
                    platformName, host, domainname, url, authInfo,
                    mirror=mirror)
            except mint_error.RepositoryAlreadyExists, e:
                projectId = self.db.db.projects.getProjectIdByFQDN(hostname)

            self.db.db.platforms.update(platformId, projectId=projectId)

            # Update package index if the project is in proxy mode. In mirror
            # mode there's no content yet.
            if not mirror:
                self._updateExternalPackageIndex()

        return projectId

    def update(self, platformId, platform):
        if platform.enabled:
            self._setupPlatform(platform)

        self.db.db.platforms.update(platformId, enabled=int(platform.enabled),
            mode=platform.mode, configurable=bool(platform.configurable),
            hidden=bool(platform.hidden))

        # Clear the cache of status information
        self.platformCache.clearPlatformData(platform.label)

        return self.getById(platformId)

    def list(self):
        return models.Platforms(self.iterPlatforms())

    def _getPlatformSourceStatus(self, platform):
        platStatus = models.PlatformSourceStatus()
        # XXX this is a hack, we need the platform model passed to the
        # platform cache somehow
        self._platformModel = platform
        valid, connected, message = self.platformCache.getStatus(platform.label)
        del self._platformModel
        platStatus.valid = valid
        platStatus.connected = connected
        platStatus.message = message
        return platStatus

    def _getPlatformStatus(self, platform):
        """
        Return (valid, connected, message)
        """
        reposMgr = self.db.productMgr.reposMgr
        remote = True
        remoteMessage = ''
        remoteConnected = True
        local = False
        localMessage = ''
        localConnected = False

        if not platform.enabled:
            return (False, False,
                "Platform must be enabled to check its status.")

        openMsg = "Repository not responding: %s."
        connectMsg = "Error connecting to repository %s: %s."
        pDefNotFoundMsg = "Platform definition not found in repository %s."
        preloadUrl = "http://docs.rpath.com/platforms/platform_repositories.html"
        pDefNotFoundMsgLocal = "Repository is empty, please manually load " + \
            "the preload for this platform available from %s."
        successMsg = "Available."

        if platform.mode == 'auto':
            client = reposMgr.getAdminClient()
            host = platform.label.split('@')[0]
            entitlement = self.db.productMgr.reposMgr.db.siteAuth.entitlementKey
            # Go straight to the host as defined by the platform, bypassing
            # any local repo map.
            sourceUrl = self._getUrl(platform)
            try:
                serverProxy = self.db.reposShim.getServerProxy(host,
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

        client = reposMgr.getAdminClient()
        platDef = proddef.PlatformDefinition()
        url = reposMgr._getFullRepositoryMap().get(
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
            localMessage = pDefNotFoundMsgLocal % preloadUrl
        except Exception, e:
            local = False
            localConnected = False
            localMessage = connectMsg % (url, e)
        else:            
            local = True
            localConnected = True

        valid = local and remote
        connected = localConnected and remoteConnected
        if valid:
            message = successMsg
        else:
            message = ' '.join([remoteMessage, localMessage])
        return (valid, connected, message)

    def getStatusTest(self, platform):
        return self._getPlatformSourceStatus(platform)

    def getStatus(self, platformId):
        platform = self.getById(platformId)
        return self._getPlatformSourceStatus(platform)

    def getLoadStatus(self, platformId, jobId):
        job = self.jobStore.get(jobId)
        status = models.PlatformLoadStatus()
        message = job.message
        done = True and job.status == job.STATUS_COMPLETED or False
        error = True and job.status == job.STATUS_FAILED or False

        if bool(done):
            code = jobstatus.FINISHED
        elif bool(error):
            code = jobstatus.ERROR
        else:
            code = jobstatus.RUNNING

        status.set_status(code, message)
        return status

    def getById(self, platformId, withComputedFields=True):
        platform = self.db.db.platforms.get(platformId)
        return self.getPlatformModelFromRow(platform,
            withComputedFields=withComputedFields)

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
        return self.mgr().contentSources.listByPlatformId(platformId)

class ContentSources(object):

    def __init__(self, db, cfg, mgr):
        self._sources = []
        self.db = db
        self.cfg = cfg
        self.mgr = weakref.ref(mgr)

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
        try:
            typeName = self.mgr().contentSourceTypes.getIdByName(source.contentSourceType)
        except errors.ContentSourceTypeNotDefined, e:
            log.error("Failed to create content source %s defined in the config "
                "file.  The content source type was not defined by any platforms. "
                "This usually means a platform definition could not be read." % source.name)
            log.error(str(e))
            return False
            
        try:
            sourceId = self.db.db.platformSources.new(
                    name=source.name,
                    shortName=source.shortName,
                    defaultSource=int(source.defaultSource),
                    contentSourceType=typeName,
                    orderIndex=source.orderIndex)
            log.info("Created platform source %s with type %s and id %s",
                    source.name, typeName, sourceId)
        except mint_error.DuplicateItem, e:
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

        for cfgSource in cfgSources:
            if cfgSource.shortName not in dbNames:
                self._create(cfgSource)
                changed = True

        return changed

    def _wrapFromDb(self, dbSources):
        sources = []
        for dbSource in dbSources:
            source = self._contentSourceModelFactory(**dict(dbSource))
            sources.append(source)
        return sources

    def _listFromDb(self):
        dbSources = self.db.db.platformSources.getAll()
        return self._wrapFromDb(dbSources)

    def _listFromCfg(self):
        sources = []
        for i, cfgShortName in enumerate(self.cfg.platformSources):
            source = self._contentSourceModelFactory(
                                shortName=cfgShortName,
                                sourceUrl=self.cfg.platformSourceUrls[i],
                                name=self.cfg.platformSourceNames[i],
                                contentSourceType=self.cfg.platformSourceTypes[i],
                                defaultSource='1',
                                orderIndex=i)
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
        log.info("Adding platform source %s to platform %s",
                sourceId, platformId)
        self.db.db.platformsPlatformSources.new(platformId=platformId,
                    platformSourceId=sourceId)

    def _linkToPlatforms(self, source):
        platforms = self.db.db.platforms.getAllByType(source.contentSourceType)

        for platform in platforms:
            self._linkPlatformToContentSource(platform['platformId'],
                    source.contentSourceId)

    def delete(self, shortName):
        sourceId = self.db.db.platformSources.getIdFromShortName(shortName)
        log.info("Deleting platform source %s", sourceId)
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
        dbSources = self.db.db.platformSources.getByPlatformId(platformId)
        sources = self._wrapFromDb(dbSources)
        return models.ContentSourceInstances(sources)

    def listByRepository(self, reposHost):
        dbSources = self.db.db.platformSources.getByRepository(reposHost)
        sources = self._wrapFromDb(dbSources)
        return models.ContentSourceInstances(sources)

    def getStatus(self, source):        
        pmgr = self.mgr()
        sourceInst = pmgr.contentSourceTypes._getSourceTypeInstance(source)
        dataSources = pmgr.getDataSourcesForContentSourceType(source.contentSourceType)

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
            sourceInst.setDataSources(dataSources)
            ret = sourceInst.status()
            status = models.SourceStatus(connected=ret[0],
                                valid=ret[1], message=ret[2])

        return status

class PlatformManager(manager.Manager):
    def __init__(self, cfg, db, auth):
        manager.Manager.__init__(self, cfg, db, auth)
        cacheFile = os.path.join(self.cfg.dataPath, 'data', 
                                 'platformName.cache')
        self.platforms = Platforms(db, cfg, self)
        self.contentSourceTypes = ContentSourceTypes(db, cfg, self)
        self.contentSources = ContentSources(db, cfg, self)
        self.platformCache = self.platforms.platformCache

    def getPlatforms(self, platformId=None):
        return self.platforms.list()

    def getPlatform(self, platformId):
        return self.platforms.getById(platformId)

    def getPlatformVersion(self, platformId, platformVersionId):
        return self.platforms.getPlatformVersion(platformId, platformVersionId)

    def getPlatformVersions(self, platformId):
        return self.platforms.getPlatformVersions(platformId)

    def isOffline(self, label):
        if not self.db.siteAuth or not self.db.siteAuth.isOffline():
            # Site is online so remote repos are reachable
            return False
        # Site is offline, check if there is a local mirror
        host = label.split('@')[0]
        try:
            handle = self.db.reposShim.getRepositoryFromFQDN(host)
        except errors.ProductNotFound:
            # No project at all, so it's offline
            return True
        if not handle.hasDatabase:
            # There is a project but it is remote
            return True
        # Local or mirrored project is accessible
        return False

    def _lookupFromRepository(self, platformLabel, createPlatDef):
        if self.isOffline(platformLabel):
            return None

        # If there is a product definition, this call will publish it as a
        # platform
        pd = proddef.ProductDefinition()
        pd.setBaseLabel(platformLabel)

        client = self.db.productMgr.reposMgr.getAdminClient(write=True)
        if createPlatDef:
            try:
                pd.loadFromRepository(client)
                pl = pd.toPlatformDefinition()
                pl.saveToRepository(client, platformLabel,
                    message="rBuilder generated\n")
                pl.loadFromRepository(client, platformLabel)
                log.info("Platform definition created for %s during platform "
                    "enablement." % platformLabel)
                # Invalidate the platform cache, we know we need to reload this
                # platform
                self.platforms.platformCache.clear()
            except proddef.ProductDefinitionError:
                # Could not find a product. Look for the platform
                pl = proddef.PlatformDefinition()
                try:
                    pl.loadFromRepository(client, platformLabel)
                except proddef.ProductDefinitionError:
                    pl = None
                    log.warning("Platform definition not found for %s during "
                        "platform enablement." % platformLabel)
        else:
            pl = proddef.PlatformDefinition()
            try:
                pl.loadFromRepository(client, platformLabel)
            except proddef.ProductDefinitionError:
                log.warning("Platform definition not found for %s during "
                    "platform enablement." % platformLabel)
                pl = None
           
        return pl

    def getDataSourcesForContentSourceType(self, contentSourceType):
        pcache = self.platformCache
        sql = """
            SELECT DISTINCT platforms.label
              FROM platformsContentSourceTypes
              JOIN platforms USING (platformid)
             WHERE contentSourceType = ?
        """
        cu = self.db.db.cursor()
        cu.execute(sql, (contentSourceType, ))
        dsset = set()
        for row in cu:
            pdef = pcache.get(row[0])
            if pdef is None:
                continue
            contentProvider = pdef.getContentProvider()
            if contentProvider is None:
                continue
            dsset.update(ds.name for ds in contentProvider.dataSources)
        return dsset

    def createPlatform(self, platform, createPlatDef=True, overwrite=False):
        platformLabel = platform.label

        # If the platform is already a platform, we want to make sure we
        # aren't trying to create a platform definition.
        # This is the case where you adding a label as a platform where it is
        # already a platform.
        if platform.isPlatform and createPlatDef:
            createPlatDef = False

        pl = self._lookupFromRepository(platformLabel, createPlatDef)

        # Now save the platform
        cu = self.db.db.cursor()
        cu.execute("SELECT platformId FROM Platforms WHERE label = ?", (platformLabel, ))
        row = cu.fetchone()
        if row and not overwrite:
            raise mint_error.PlatformAlreadyExists
        if not row:
            platId = self.platforms._create(platform, pl)
        else:
            platId = row[0]
            platformModel = self.platforms.getById(platId,
                withComputedFields=False)
            platformFieldVals = ((x, getattr(platform, x))
                for x in platform._fields)
            platformModel.updateFields(**dict((fname, fval)
                for (fname, fval) in platformFieldVals
                    if fval is not None))
            # Make sure the XML can't override internal fields
            platformModel.platformId = platId
            self.platforms._update(platformModel, pl)
        return platId

    def getPlatformByName(self, platformName):
        return self.platforms.getByName(platformName)

    def getPlatformImageTypeDefs(self, request, platformId):
        platform = self.platforms.getById(platformId)
        platDef = self.platforms.platformCache.get(platform.label)
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
                        **extra)
                    kw.update(options=imageParams)

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
        sourceTypes = platform._sourceTypes
        isOffline = self.db.siteAuth.isOffline()
        if sourceTypes is not None:
            for sourceType, isSingleton in sourceTypes:
                cst = contentsources.contentSourceTypes[sourceType]
                if isOffline and not cst.enabledInOfflineMode:
                    continue
                types.append(ContentSourceTypes.contentSourceTypeModelFactory(
                    name=sourceType, singleton=isSingleton,
                    required=cst.isRequired))

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

    def getSourcesByRepository(self, reposHost):
        return self.contentSources.listByRepository(reposHost)

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

    def getContentEnabledPlatformLabels(self, reposHost=None):
        cu = self.db.cursor()
        sql = """
            SELECT DISTINCT pl.label
            FROM Platforms pl
            JOIN Projects p ON p.projectId = pl.projectId
            JOIN PlatformsContentSourceTypes pcst ON pcst.platformId = pl.platformId
            WHERE pl.enabled != 0
            """
        if reposHost:
            cu.execute(sql + "AND p.fqdn = ?", (reposHost,))
        else:
            cu.execute(sql)
        return [ x[0] for x in cu ]


class PlatformDefCache(persistentcache.PersistentCache):
    def __init__(self, cacheFile, mgr):
        persistentcache.PersistentCache.__init__(self, cacheFile)
        self.mgr = weakref.ref(mgr)

    def getReposMgr(self):
        return self.mgr().db.productMgr.reposMgr

    def _getPlatDef(self, client, labelStr):
        try:
            platDef = proddef.PlatformDefinition()
            platDef.loadFromRepository(client, labelStr)
            self.clearPlatformData(labelStr)
        except proddef.ProductDefinitionTroveNotFoundError:
            raise
        except reposErrors.InsufficientPermission, err:
            log.info("Platform %s is not accessible because "
                    "it is not entitled.", labelStr)
            self.clearPlatformData(labelStr)
            return None
        except:
            log.exception("Failed to lookup platform definition on label %s:",
                    labelStr)
            self.clearPlatformData(labelStr)
            return None

        platDef.label = labelStr
        return platDef

    def _refresh(self, labelStr):
        if isinstance(labelStr, tuple):
            if labelStr == self._mirrorKey(labelStr[1]):
                return self._refreshMirrorPermission(labelStr[1], platform=None)
            if labelStr == self._statusKey(labelStr[1]):
                return self._refreshStatus(labelStr[1], platform=None)
            raise Exception("XXX")
        if self.mgr().isOffline(labelStr):
            # Don't refresh if we're offline and would need to talk to a remote
            # repository.
            return None
        reposMgr = self.getReposMgr()
        try:
            client = reposMgr.getAdminClient()
            platDef = self._getPlatDef(client, labelStr)
            return platDef
        except proddef.ProductDefinitionTroveNotFoundError, e:
            # Need to look at inboundmirrors table to get the sourceurl 
            # for the platform so that we bypass the local repo.
            sourceUrl = reposMgr.getIncomingMirrorUrlByLabel(labelStr)
            host = labelStr.split('@')[0]

            if not sourceUrl:
                # Try going straight to the platform label
                sourceUrl = "https://%s/conary/" % host

            try:
                if reposMgr.db.siteAuth:
                    entitlement = reposMgr.db.siteAuth.entitlementKey
                    if reposMgr.db.siteAuth.isOffline():
                        # Remote will not be reachable
                        return None
                else:
                    entitlement = None
                serverProxy = reposMgr.db.reposShim.getServerProxy(host,
                    sourceUrl, None, [entitlement])
                client.repos.c.cache[host] = serverProxy
                platDef = self._getPlatDef(client, labelStr)
                return platDef
            except (proddef.ProductDefinitionTroveNotFoundError,
                    reposErrors.InsufficientPermission):
                log.info("Platform %s is not accessible because "
                        "it is not entitled.", labelStr)
                return None
            except:
                log.exception("Failed to lookup platform definition "
                        "on label %s:", labelStr)
                return None

    def _getPlatform(self, labelStr, platform, commit=True):
        # Helper function to reduce code duplication - if a platform is not
        # presented, attempt to fetch it from the cache; if not available,
        # clear the caches
        if platform is not None:
            return platform
        platform = self.get(labelStr)
        if platform is None:
            self.clearPlatformData(labelStr, commit=commit)
            return None
        return platform

    @classmethod
    def _mirrorKey(cls, labelStr):
        return ('mirrorPermission', labelStr)

    @classmethod
    def _statusKey(cls, labelStr):
        return ('status', labelStr)

    def _refreshMirrorPermission(self, labelStr, platform=None, commit=True):
        platformMgr = self.mgr()
        platformModel = platformMgr.platforms._platformModel
        mirrorPermission = platformMgr.platforms._checkMirrorPermissions(platformModel)
        self._update(self._mirrorKey(labelStr), mirrorPermission,
            commit=commit)
        return mirrorPermission

    def _refreshStatus(self, labelStr, platform=None, commit=True):
        platformMgr = self.mgr()
        platformModel = platformMgr.platforms._platformModel
        (valid, connected, message) = platformMgr.platforms._getPlatformStatus(
            platformModel)
        self._update(self._mirrorKey(labelStr), (valid, connected, message),
            commit=commit)
        return (valid, connected, message)

    def _clearMirrorPermission(self, labelStr, commit=True):
        self.clearKey(self._mirrorKey(labelStr), commit=commit)

    def _clearStatus(self, labelStr, commit=True):
        self.clearKey(self._statusKey(labelStr), commit=commit)

    def getMirrorPermission(self, labelStr):
        return self.get(self._mirrorKey(labelStr))

    def getStatus(self, labelStr):
        return self.get(self._statusKey(labelStr))

    def clearPlatformData(self, labelStr, commit=True):
        self._clearMirrorPermission(labelStr, commit=commit)
        self._clearStatus(labelStr, commit=commit)
        self.clearKey(labelStr, commit)

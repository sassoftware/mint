#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import logging
import os
import weakref

from conary import errors as conaryErrors
from conary import versions
from conary.dbstore import sqllib
from conary.repository import errors as reposErrors

from mint import mint_error
from mint.lib import persistentcache
from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import manager
from mint.scripts import pkgindexer

from rpath_proddef import api1 as proddef

log = logging.getLogger(__name__)


class Platforms(object):

    def __init__(self, db, cfg, mgr):
        self.platforms = []
        self.db = db
        self.cfg = cfg
        self.mgr = weakref.ref(mgr)
        cacheFile = os.path.join(self.cfg.dataPath, 'data', 
                                 'platformName.cache')
        self.platformCache = PlatformDefCache(cacheFile, mgr)

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
            platformDef = self.platformCache.get(str(platform.label),
                    platform=platform)
        else:
            platformDef = None
        self._updatePlatformFromPlatformDefinition(platform, platformDef)
        if withComputedFields:
            self._addComputedFields(platform)
        return platform

    def _getPlatformTroveName(self, platform):
        platformDef = self.platformCache.get(str(platform.label),
                platform=platform)
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

        label = platform.label
        if not label.startswith('/'):
            label = '/%s' % label
        conaryLabel = versions.VersionFromString(label).label()
        cli = self.db.productMgr.reposMgr.getUserClient()
        repoTroves = cli.repos.findTroves(conaryLabel,
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
        mode = kw.get('mode', 'manual')
        hidden = kw.get('hidden', None)
        upstream_url = kw.get('upstream_url', None)
        platformUsageTerms = kw.get('platformUsageTerms')
        platform = models.Platform(platformId=platformId, label=label,
                platformName=platformName, enabled=enabled,
                platformUsageTerms=platformUsageTerms,
                configurable=configurable, mode=mode,
                repositoryHostname=fqdn, abstract=abstract,
                hidden=hidden, upstream_url=upstream_url)
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
            upstream_url=platformModel.upstream_url,
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
                upstream_url = ?,
                time_refreshed = current_timestamp
            WHERE platformId = ?"""
        cu.execute(sql, platformName, abstract, configurable, platformModel.upstream_url, platformId)
        return platformId

    def _addComputedFields(self, platformModel):
        # Also check for mirroring permissions for configurable platforms.
        # This is the best place to do this, since this method always gets
        # called when fetching a platform.
        if platformModel.configurable:
            mirrorPermission = self.platformCache.getMirrorPermission(
                    platformModel.label, platform=platformModel)
        else:
            mirrorPermission = False
        platformModel.mirrorPermission = mirrorPermission

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
        elif platform.upstream_url:
            return platform.upstream_url
        else:
            return 'https://%s/conary/' % (hostname)

    def _getAuthInfo(self):
        return models.AuthInfo(authType='none')

    def _updateInternalPackageIndex(self):
        """
        Update the internal package index
        """
        upi = pkgindexer.UpdatePackageIndex()
        return upi.run()

    def _updateExternalPackageIndex(self, fqdn):
        """
        Update the external package index.
        """
        # Disabled for now
        return
        upie = pkgindexer.UpdatePackageIndexExternal()
        upie.log = logging.getLogger('pkgindexer')
        return upie.action(fqdn=fqdn)

    def _setupPlatform(self, platform):
        platformId = int(platform.platformId)
        platformName = str(platform.platformName)
        hostname = self._getHostname(platform)
        host = self._getHost(platform)
        url = self._getUrl(platform)
        domainname = self._getDomainname(platform)
        mirror = platform.configurable
        if self.db.isOffline():
            # Proxying is prohibited in offline mode so always create a mirror
            mirror = True

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
                    self._updateExternalPackageIndex(project['fqdn'])
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
                project = self.db.db.projects.get(projectId)
                self._updateExternalPackageIndex(fqdn=project['fqdn'])

        return projectId

    def update(self, platformId, platform):
        if platform.enabled:
            self._setupPlatform(platform)

        self.db.db.platforms.update(platformId, enabled=int(platform.enabled),
            mode=platform.mode, configurable=bool(platform.configurable),
            hidden=bool(platform.hidden), upstream_url=platform.upstream_url)

        # Clear the cache of status information
        self.platformCache.clearPlatformData(platform.label)

        return self.getById(platformId)

    def list(self):
        return models.Platforms(self.iterPlatforms())

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
        url = self._getUrl(platform)

        if platform.mode == 'auto':
            client = reposMgr.getAdminClient()
            host = platform.label.split('@')[0]
            # Go straight to the host as defined by the platform, bypassing
            # any local repo map.
            try:
                serverProxy = self.db.reposShim.getServerProxy(host,
                    url, None, [])
                client.repos.c.cache[host] = serverProxy
                platDef = proddef.PlatformDefinition()
                platDef.loadFromRepository(client, platform.label)
            except reposErrors.OpenError, e:
                remote = False
                remoteConnected = False
                remoteMessage = openMsg % url
            except conaryErrors.ConaryError, e:
                remote = False
                remoteConnected = True
                remoteMessage = connectMsg % (url, e)
            except proddef.ProductDefinitionTroveNotFoundError, e:
                remote = False
                remoteConnected = True
                remoteMessage = pDefNotFoundMsg % url
            except Exception, e:
                remote = False
                remoteConnected = False
                # Hard code a helpful message for the sle platform.
                if 'sle.rpath.com' in platform.label:
                    remoteMessage = "This platform requires a " + \
                        "commercial license.  You are either missing the " + \
                        "entitlement for this platform or it is no longer valid"
                else:
                    remoteMessage = connectMsg % (url, e)

        client = reposMgr.getAdminClient()
        platDef = proddef.PlatformDefinition()

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


class PlatformManager(manager.Manager):
    def __init__(self, cfg, db, auth):
        manager.Manager.__init__(self, cfg, db, auth)
        self.platforms = Platforms(db, cfg, self)
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
        if not self.db.isOffline():
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

    def createPlatform(self, platform, createPlatDef=True, overwrite=False):
        platformLabel = platform.label

        # If the platform is already a platform, we want to make sure we
        # aren't trying to create a platform definition.
        # This is the case where you adding a label as a platform where it is
        # already a platform.
        if platform.isPlatform and createPlatDef:
            createPlatDef = False

        if createPlatDef:
            pl = self._lookupFromRepository(platform.label, createPlatDef)
        else:
            pl = None

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
        platDef = self.platforms.platformCache.get(platform.label,
                platform=platform)
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

    def updatePlatform(self, platformId, platform):
        return self.platforms.update(platformId, platform)


class PlatformDefCache(persistentcache.PersistentCache):
    def __init__(self, cacheFile, mgr):
        persistentcache.PersistentCache.__init__(self, cacheFile)
        self.mgr = weakref.ref(mgr)

    def getReposMgr(self):
        return self.mgr().db.productMgr.reposMgr

    def _getPlatDef(self, labelStr, url=None):
        reposMgr = self.getReposMgr()
        client = reposMgr.getAdminClient()
        try:
            if url:
                fqdn = labelStr.split('@')[0]
                serverProxy = reposMgr.db.reposShim.getServerProxy(fqdn, url,
                        None, [])
                client.repos.c.cache[fqdn] = serverProxy

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

    def _refresh(self, labelStr, platform=None):
        if isinstance(labelStr, tuple):
            if labelStr == self._mirrorKey(labelStr[1]):
                return self._refreshMirrorPermission(labelStr[1],
                        platform=platform)
            if labelStr == self._statusKey(labelStr[1]):
                return self._refreshStatus(labelStr[1], platform=platform)
            raise Exception("XXX")
        reposMgr = self.getReposMgr()
        fqdn = labelStr.split('@')[0]
        try:
            handle = reposMgr.db.reposShim.getRepositoryFromFQDN(fqdn)
        except errors.ProductNotFound:
            handle = None
        # If there's a project already configured then use that first.
        if handle:
            try:
                platDef = self._getPlatDef(labelStr)
                return platDef
            except proddef.ProductDefinitionTroveNotFoundError, err:
                pass
        # Bail out now if the project is local, because there is no upstream.
        if handle and not handle.isExternal:
            log.error("No platform definition found on label %s", labelStr)
            return None
        # Don't refresh if we're offline and would need to talk to a remote
        # repository.
        if reposMgr.db.isOffline():
            return None
        # Use inbound mirror URL if available, or the platform stub's upstream
        # URL otherwise.
        sourceUrl = reposMgr.getIncomingMirrorUrlByLabel(labelStr)
        if not sourceUrl and platform:
            sourceUrl = platform.upstream_url
        if not sourceUrl:
            sourceUrl = "https://%s/conary/" % fqdn
        try:
            platDef = self._getPlatDef(labelStr, sourceUrl)
            return platDef
        except (proddef.ProductDefinitionTroveNotFoundError,
                reposErrors.InsufficientPermission):
            log.info("Platform %s is not accessible because "
                    "it is not entitled.", labelStr)
            return None
        return None

    @classmethod
    def _mirrorKey(cls, labelStr):
        return ('mirrorPermission', labelStr)

    @classmethod
    def _statusKey(cls, labelStr):
        return ('status', labelStr)

    def _refreshMirrorPermission(self, labelStr, platform=None, commit=True):
        platformMgr = self.mgr()
        mirrorPermission = platformMgr.platforms._checkMirrorPermissions(platform)
        self._update(self._mirrorKey(labelStr), mirrorPermission,
            commit=commit)
        return mirrorPermission

    def _refreshStatus(self, labelStr, platform=None, commit=True):
        platformMgr = self.mgr()
        (valid, connected, message) = platformMgr.platforms._getPlatformStatus(
                platform)
        self._update(self._mirrorKey(labelStr), (valid, connected, message),
            commit=commit)
        return (valid, connected, message)

    def _clearMirrorPermission(self, labelStr, commit=True):
        self.clearKey(self._mirrorKey(labelStr), commit=commit)

    def _clearStatus(self, labelStr, commit=True):
        self.clearKey(self._statusKey(labelStr), commit=commit)

    def getMirrorPermission(self, labelStr, platform=None):
        return self.get(self._mirrorKey(labelStr), platform=platform)

    def getStatus(self, labelStr, platform=None):
        return self.get(self._statusKey(labelStr), platform=platform)

    def clearPlatformData(self, labelStr, commit=True):
        self._clearMirrorPermission(labelStr, commit=commit)
        self._clearStatus(labelStr, commit=commit)
        self.clearKey(labelStr, commit)

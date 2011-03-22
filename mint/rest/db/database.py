#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import decorator
import logging

from conary import versions
from conary.conaryclient import cmdline
from conary.dbstore import sqllib
from conary.deps import deps

from mint import jobstatus
from mint import mint_error
from mint import projects
from mint import userlevels
from mint.lib import siteauth
from mint.rest.api import models
from mint.rest import errors
from mint.rest.db import authmgr
from mint.rest.db import awshandler
from mint.rest.db import capsulemgr
from mint.rest.db import emailnotifier
from mint.rest.db import filemgr
from mint.rest.db import imagemgr
from mint.rest.db import pkimgr
from mint.rest.db import platformmgr
from mint.rest.db import productmgr
from mint.rest.db import publisher
from mint.rest.db import releasemgr
from mint.rest.db import systemmgr
from mint.rest.db import targetmgr
from mint.rest.db import usermgr

reservedHosts = ['admin', 'mail', 'mint', 'www', 'web', 'rpath', 'wiki', 'conary', 'lists']

class DBInterface(object):
    _logFormat = "%(asctime)s %(levelname)s - %(message)s"
    def __init__(self, db):
        self._holdCommits = False
        self.db = db

    def _getOne(self, cu, exception, key):
        res = cu.fetchone()
        if res is None:
            raise exception(key)

        # Make sure only one row was returned. If there are more, it is
        # a programming error, not a user error.
        assert cu.fetchone() is None

        return sqllib.Row(res, cu.fields())

    def cursor(self):
        return self.db.cursor()

    def _commitAfter(self, fn, *args, **kw):
        """
            Commits after running a function
        """
        self._holdCommits = True
        self.db.transaction()
        try:
            rv = fn(*args, **kw)
            self._holdCommits = False
            self.commit()
            return rv
        except:
            self.rollback()
            self._holdCommits = False
            raise

    def commit(self):
        if not self._holdCommits:
            return self.db.commit()
        else:
            return True

    def rollback(self):
        return self.db.rollback()

    def inTransaction(self, default=None):
        return self.db.db.inTransaction(default)

    def open(self):
        raise NotImplementedError

    def reopen(self):
        self._holdCommits = False
        self.db = self.open()

    def reopen_fork(self):
        self._holdCommits = False
        if self.db:
            self.db.reopen_fork()

    def close(self):
        self.db.close()
        self.db = None

@decorator.decorator
def commitafter(fn, self, *args, **kw):
    return self._commitAfter(fn, self, *args, **kw)

@decorator.decorator
def commitmaybe(fn, self, *args, **kw):
    inTransaction = self.inTransaction(default=False)
    rv = fn(self, *args, **kw)
    if not inTransaction and self.inTransaction(default=True):
        self.commit()
    return rv

@decorator.decorator
def readonly(fn, self, *args, **kw):
    inTransaction = self.inTransaction(default=False)
    rv = fn(self, *args, **kw)
    if not inTransaction and self.inTransaction(default=False):
        #raise RuntimeError('Database modified unexpectedly after %s.' % fn.func_name)
        # We used to complain loudly if the state had modified, until we
        # started to use temporary tables. So now we just roll back.
        # RBL-8111
        self.rollback()
    return rv

class Database(DBInterface):
    def __init__(self, cfg, db, auth=None, subscribers=None, dbOnly=False):
        DBInterface.__init__(self, db)
        self.cfg = cfg

        if auth is None:
            auth = authmgr.AuthenticationManager(cfg, self)
        self.auth = auth
        self.publisher = publisher.EventPublisher()
        self.productMgr = productmgr.ProductManager(cfg, self, auth,
                                                    self.publisher)
        self.fileMgr = filemgr.FileManager(cfg, self, auth)
        self.imageMgr = imagemgr.ImageManager(cfg, self, auth, self.publisher)
        self.releaseMgr = releasemgr.ReleaseManager(cfg, self,
                                                    auth, self.publisher)
        self.userMgr = usermgr.UserManager(cfg, self, auth, self.publisher)
        self.platformMgr = platformmgr.PlatformManager(cfg, self, auth)
        self.capsuleMgr = capsulemgr.CapsuleManager(cfg, self, auth)
        self.targetMgr = targetmgr.TargetManager(cfg, self, auth)
        self.awsMgr = awshandler.AWSHandler(cfg, self, auth)
        self.pkiMgr = pkimgr.PKIManager(cfg, self, auth)
        self.systemMgr = systemmgr.SystemManager(cfg, self, auth)
        if subscribers is None:
            subscribers = []
            subscribers.append(emailnotifier.EmailNotifier(cfg, self,
                                                           auth))
            subscribers.append(self.awsMgr)
        for subscriber in subscribers:
            self.publisher.subscribe(subscriber)

        # Don't instantiate things that go outside the core database
        # connection if dbOnly is set.
        self.siteAuth = None
        if not dbOnly:
            self.siteAuth = siteauth.getSiteAuth(cfg.siteAuthCfgPath)

    def close(self):
        #DBInterface.close(self)
        self.productMgr.reposMgr.close()

    def reopen_fork(self):
        DBInterface.reopen_fork(self)
        self.productMgr.reposMgr.reopen_fork()

    def setAuth(self, auth, authToken):
        self.auth.setAuth(auth, authToken)

    def setProfiler(self, profile):
        #profile.attachDb(self.db.db)
        #profile.attachRepos(self.productMgr.reposMgr)
        pass

    @readonly
    def getUsername(self, userId):
        cu = self.db.cursor()
        cu.execute('SELECT username from Users where userId=?', userId)
        return self._getOne(cu, errors.UserNotFound, userId)[0]

    @readonly
    def listProducts(self, start=0, limit=None, search=None, roles=None,
                     prodtype=None):
        return self.productMgr.listProducts(start=start, limit=limit,
                search=search, roles=roles, prodtype=prodtype)

    @readonly
    def getProductFQDNFromId(self, productId):
        cu = self.db.cursor()
        cu.execute('SELECT hostname, domainname from Projects where projectId=?', productId)
        hostname, domainname = self._getOne(cu, errors.ProductNotFound, 
                                            productId)
        return hostname + '.' + domainname

    @readonly
    def getProduct(self, hostname):
        self.auth.requireProductReadAccess(hostname=hostname)
        return self.productMgr.getProduct(hostname)

    @readonly
    def listProductVersions(self, hostname):
        self.auth.requireProductReadAccess(hostname=hostname)
        if '.' in hostname:
            hostname, domainname = hostname.split('.', 1)
        cu = self.db.cursor()
        cu.execute('''SELECT productVersionId as versionId, 
                          PVTable.namespace, PVTable.name, PVTable.description,
                          PVTable.timeCreated, Projects.hostname
                      FROM Projects 
                      JOIN ProductVersions as PVTable USING (projectId)
                      WHERE Projects.hostname=?''', hostname)

        pvl = models.ProductVersionList()
        for row in cu:
            pvl.addProductVersion(row)
            pv = pvl.versions[-1]
            pd = self.productMgr.getProductVersionDefinitionByProductVersion(pv)
            # Use sourceGroup here since this is really the name of the source
            # trove that needs to be cooked.
            pv.sourceGroup = pd.getImageGroup()

        return pvl

    @readonly
    def listProductMembers(self, hostname):
        self.auth.requireProductReadAccess(hostname=hostname)
        if '.' in hostname:
            hostname, domainname = hostname.split('.', 1)
        cu = self.db.cursor()
        cu.execute('''SELECT username, level
                      FROM Projects
                      JOIN ProjectUsers USING(projectId)
                      JOIN Users USING(userId)
                      WHERE hostname=?''', hostname)
        memberList = models.MemberList()
        for username, level in cu:
            member = models.Membership(hostname=hostname,
                                       username=username,
                                       level=userlevels.names[level])
            memberList.members.append(member)
        return memberList

    @readonly
    def getProductMembership(self, hostname, username):
        self.auth.requireProductReadAccess(hostname=hostname)
        if '.' in hostname:
            hostname, domainname = hostname.split('.', 1)
        cu = self.db.cursor()
        cu.execute('''SELECT level
                      FROM Projects
                      JOIN ProjectUsers USING(projectId)
                      JOIN Users USING(userId)
                      WHERE hostname=? AND username=?''', 
                      hostname, username)
        level, = self._getOne(cu, errors.MemberNotFound, (hostname, username))
        return models.Membership(hostname=hostname, username=username, 
                                 level=level)

    @readonly
    def getProductVersion(self, hostname, versionName):
        self.auth.requireProductReadAccess(hostname=hostname)
        return self.productMgr.getProductVersion(hostname, versionName)

    @readonly
    def getUserId(self, username):
        return self.userMgr.getUserId(username)

    @readonly
    def getProductId(self, fqdn):
        cu = self.db.cursor()
        hostname = fqdn.split('.', 1)[0]
        cu.execute("""SELECT projectId FROM Projects WHERE hostname=?""", hostname)
        projectId, = self._getOne(cu, errors.ProductNotFound, fqdn)
        return projectId

    @readonly
    def getUser(self, username):
        self.auth.requireLogin()
        if self.auth.hasUserReadAccess(username):
            return self._getUser(username, includePrivateInfo=True)
        else:
            return self._getUser(username, includePrivateInfo=False)

    def _getUser(self, username, includePrivateInfo=True):
        if includePrivateInfo:
            cu = self.db.cursor()
            cu.execute("""SELECT userId, username, fullName,
                                 email, displayEmail, timeCreated, timeAccessed,
                                 active, blurb 
                           FROM Users WHERE username=?""", username)
        else:
            cu = self.db.cursor()
            cu.execute("""SELECT userId, username, fullName,
                                 displayEmail, blurb 
                           FROM Users WHERE username=? AND active=1""", 
                           username)
        d = self._getOne(cu, errors.UserNotFound, username)
        return models.User(d)

    @readonly
    def listMembershipsForUser(self, username):
        self.auth.requireUserReadAccess(username)
        cu = self.db.cursor()
        cu.execute('''SELECT hostname, level
                      FROM Users
                      JOIN ProjectUsers USING(userId)
                      JOIN Projects USING(projectId)
                      WHERE username=?''', username)
        memberList = models.MemberList()
        for hostname, level in cu:
            member = models.Membership(hostname=hostname,
                                       username=username,
                                       level=userlevels.names[level])
            memberList.members.append(member)
        return memberList

    @readonly    
    def listUsers(self):
        self.auth.requireAdmin()
        cu = self.db.cursor()
        cu.execute("""SELECT userId, username, fullName,
                             email, displayEmail, timeCreated, timeAccessed,
                             active, blurb FROM Users""")
        userList = models.UserList()
        for d in cu:
            userList.users.append(models.User(d))
        return userList

    @readonly    
    def listUserGroupsForUser(self, username):
        self.auth.requireAdmin()
        cu = self.db.cursor()
        cu.execute('''SELECT userGroup 
                      FROM Users
                      JOIN UserGroupMembers  USING(userId)
                      JOIN UserGroups  USING(userGroupId)
                      WHERE Users.username=?''', username)
        groupList = models.UserGroupMemberList()
        for userGroup, in cu:
            group = models.UserGroupMember(userGroup, username)
        groupList.groups.append(group)
        return groupList

    @commitafter
    def createProduct(self, product):
        self.auth.requireProductCreationRights()
        if not product.name:
            raise errors.InvalidItem("Product name must be specified")
        if self.cfg.rBuilderOnline or not product.domainname:
            product.domainname = self.cfg.projectDomainName.split(':')[0]
        projects._validateShortname(product.shortname, product.domainname, 
                                    reservedHosts)
        projects._validateHostname(product.hostname, product.domainname, 
                                   reservedHosts)
        if product.namespace:
            projects._validateNamespace(product.namespace)
        else:
            #If none was set use the default namespace set in config
            product.namespace = self.cfg.namespace
        # validate the label, which will be added later.  This is done
        # here so the project is not created before this error occurs
        if product.version is None:
            product.version = '1'
        projects._validateProductVersion(product.version)
        label = '%s.%s@%s:%s-%s-devel' % (product.hostname, product.domainname,
                                          product.namespace, product.hostname,
                                          product.version)
        if projects.validLabel.match(label) == None:
            raise mint_error.InvalidLabel(label)

        prodtype = product.prodtype
        if not prodtype:
            prodtype = 'Appliance'
        elif prodtype not in ('Appliance', 'Component', 'Platform', 'Repository', 'PlatformFoundation'):
            raise mint_error.InvalidProdType

        fqdn = ".".join((product.hostname, product.domainname))
        projecturl = product.projecturl
        if (projecturl and not (projecturl.startswith('https://') 
            or projecturl.startswith('http://'))):
            product.projecturl = "http://" + projecturl
        for attr in ('projecturl', 'description', 'commitEmail'):
            if getattr(product, attr) is None:
                setattr(product, attr, '')

        if self.cfg.hideNewProjects:
            product.hidden = True
        elif product.hidden is None:
            product.hidden = False

        productId = self.productMgr.createProduct(product.name, 
                                      product.description, product.hostname,
                                      product.domainname, product.namespace,
                                      product.projecturl,
                                      product.shortname, product.prodtype,
                                      product.version,
                                      product.commitEmail, 
                                      isPrivate=product.hidden)
        product.productId = productId
        return product

    @commitafter
    def updateProduct(self, hostname, product):
        self.auth.requireProductOwner(hostname)
        self.productMgr.updateProduct(hostname, name=product.name,
                                      namespace=product.namespace,
                                      description=product.description,
                                      projecturl=product.projecturl,
                                      prodtype=product.prodtype,
                                      commitEmail=product.commitEmail,
                                      hidden=product.hidden)

    @commitafter
    def setMemberLevel(self, hostname, username, level):
        self.auth.requireProductOwner(hostname)
        level = userlevels.idsByName[level]
        product = self.getProduct(hostname)
        userId = self.getUserId(username)
        self.productMgr.setMemberLevel(product.productId, userId, level)

    @commitafter
    def deleteMember(self, hostname, username):
        if self.auth.username != username:
            self.auth.requireProductOwner(hostname)
        product = self.getProduct(hostname)
        userId = self.getUserId(username)
        self.productMgr.deleteMember(product.productId, userId)

    @commitafter
    def cancelUserAccount(self, username):
        self.auth.requireUserAdmin(username)
        self.userMgr.cancelUserAccount(username)

    @commitafter
    def createProductVersion(self, fqdn, productVersion):
        self.auth.requireProductOwner(fqdn)
        versionId = self.productMgr.createProductVersion(
                                                fqdn,
                                                productVersion.name,
                                                productVersion.namespace,
                                                productVersion.description,
                                                productVersion.platformLabel)
        productVersion.id = versionId
        return productVersion

    @commitafter
    def updateProductVersion(self, hostname, version, productVersion):
        self.auth.requireProductOwner(hostname)
        self.productMgr.updateProductVersion(hostname,
                                             version, productVersion.description)


    def getProductVersionPlatform(self, hostname, version):
        self.auth.requireProductReadAccess(hostname)
        pd = self.productMgr.getProductVersionDefinition(hostname, version)
        platformName = pd.getPlatformName()
        sourceTrove = pd.getPlatformSourceTrove()
        if not sourceTrove:
            return models.ProductPlatform(platformTroveName='',
                platformVersion='', label='', platformName=platformName,
                hostname=hostname, productVersion=version)
        n,v,f = cmdline.parseTroveSpec(sourceTrove)
        v = versions.VersionFromString(v)
        # convert trove name from unicode
        platformLabel = str(v.trailingLabel())
        localPlatform = self.platformMgr.getPlatformByLabel(platformLabel)
        platformId = None
        platformEnabled = None
        if localPlatform:
            platformId = localPlatform.platformId
            platformEnabled = bool(localPlatform.enabled)
        return models.ProductPlatform(platformTroveName=str(n),
            platformVersion=str(v.trailingRevision()),
            label=platformLabel,
            platformName=platformName,
            hostname=hostname,
            productVersion=version,
            enabled=platformEnabled,
            platformId = platformId)

    def updateProductVersionStage(self, hostname, version, stageName, trove):
        return self.productMgr.updateProductVersionStage(hostname, version, stageName, trove)

    def getGroupPromoteJobStatus(self, hostname, version, stage, jobId):
        return self.productMgr.getGroupPromoteJobStatus(hostname, version, stage, jobId)

    @readonly    
    def getProductVersionStage(self, hostname, version, stageName):
        self.auth.requireProductReadAccess(hostname)
        pd = self.productMgr.getProductVersionDefinition(hostname, version)
        stages = pd.getStages()
        for stage in stages:
            if str(stage.name) == stageName:
                promotable = ((stage.name != stages[-1].name and True) or False) 
                return models.Stage(name=str(stage.name),
                                    label=str(pd.getLabelForStage(stage.name)),
                                    hostname=hostname,
                                    version=version,
                                    isPromotable=promotable)
        raise errors.StageNotFound(stageName)

    @readonly    
    def getProductVersionStages(self, hostname, version):
        self.auth.requireProductReadAccess(hostname)
        pd = self.productMgr.getProductVersionDefinition(hostname, version)
        stageList = models.Stages()
        stages = pd.getStages()
        for stage in stages:
            promotable = ((stage.name != stages[-1].name and True) or False)
            stageList.stages.append(models.Stage(name=str(stage.name),
                                 label=str(pd.getLabelForStage(stage.name)),
                                 hostname=hostname,
                                 version=version,
                                 isPromotable=promotable))
        return stageList

    def listImagesForProductVersion(self, hostname, version):
        self.auth.requireProductReadAccess(hostname)
        return self.imageMgr.listImagesForProductVersion(hostname, version)

    def listImagesForProductVersionStage(self, hostname, version, stageName):
        self.auth.requireProductReadAccess(hostname)
        return self.imageMgr.listImagesForProductVersionStage(hostname,
                                                        version, stageName)

    @readonly
    def getProductVersionStageBuildDefinitions(self, hostname, version,
                                               stageName):
        self.auth.requireProductReadAccess(hostname)
        return self.productMgr.getProductVersionStageBuildDefinitions(
            hostname, version, stageName)

    @readonly
    def getProductVersionDefinition(self, hostname, version):
        self.auth.requireProductReadAccess(hostname)
        return self.productMgr.getProductVersionDefinition(hostname, version)

    @commitafter
    def setProductVersionDefinition(self, hostname, version, pd):
        self.auth.requireProductDeveloper(hostname)
        return self.productMgr.setProductVersionDefinition(hostname, version, pd)

    @commitafter
    def rebaseProductVersionPlatform(self, hostname, version,
                                     platformLabel=None):
        self.auth.requireProductDeveloper(hostname)
        self.productMgr.rebaseProductVersionPlatform(hostname, version,
                                                     platformLabel)

    @commitafter
    def setProductVersionBuildDefinitions(self, hostname, version, model):
        self.auth.requireProductDeveloper(hostname)
        return self.productMgr.setProductVersionBuildDefinitions(hostname, version, model)

    def stopImageJob(self, hostname, imageId):
        self.auth.requireBuildsOnHost(hostname, [imageId])
        return self.imageMgr.stopImageJob(imageId)

    @readonly    
    def listReleasesForProduct(self, hostname, limit=None):
        self.auth.requireProductReadAccess(hostname)
        return self.releaseMgr.listReleasesForProduct(hostname, limit=limit)

    @readonly    
    def getReleaseForProduct(self, hostname, releaseId):
        self.auth.requireProductReadAccess(hostname)
        return self.releaseMgr.getReleaseForProduct(hostname, releaseId)

    @commitafter
    def createRelease(self, hostname, name, description, version, imageIds):
        self.auth.requireProductDeveloper(hostname)
        self.auth.requireBuildsOnHost(hostname, imageIds)
        releaseId = self.releaseMgr.createRelease(hostname, name, description,
                                                  version, imageIds)
        return releaseId

    @commitafter
    def deleteRelease(self, hostname, releaseId):
        self.auth.requireProductDeveloper(hostname)
        self.auth.requireReleaseOnHost(hostname, releaseId)
        self.releaseMgr.deleteRelease(releaseId)

    @commitafter
    def updateRelease(self, hostname, releaseId, name, description, version,
                      published, shouldMirror, imageIds):
        self.auth.requireProductDeveloper(hostname)
        self.auth.requireReleaseOnHost(hostname, releaseId)
	if imageIds:
            self.auth.requireBuildsOnHost(hostname, imageIds)
        self.releaseMgr.updateRelease(hostname, releaseId,
                                      name, description, version,
                                      published, shouldMirror, imageIds)

    @commitafter
    def updateImagesForRelease(self, hostname, releaseId, imageIds):
        self.auth.requireProductDeveloper(hostname)
        self.auth.requireReleaseOnHost(hostname, releaseId)
        self.auth.requireBuildsOnHost(hostname, imageIds)
        self.releaseMgr.updateImagesForRelease(hostname, releaseId, imageIds)

    @commitafter
    def addImageToRelease(self, hostname, releaseId, imageId):
        self.auth.requireProductDeveloper(hostname)
        self.auth.requireReleaseOnHost(hostname, releaseId)
        self.auth.requireBuildsOnHost(hostname, [imageId])
        self.releaseMgr.addImageToRelease(hostname, releaseId, imageId)

    @commitafter
    def publishRelease(self, hostname, releaseId, shouldMirror):
        self.auth.requireReleaseOnHost(hostname, releaseId)
        self.auth.requireProductOwner(hostname)
        self.releaseMgr.publishRelease(releaseId, shouldMirror)

    @commitafter
    def unpublishRelease(self, hostname, releaseId):
        self.auth.requireReleaseOnHost(hostname, releaseId)
        self.auth.requireProductOwner(hostname)
        self.releaseMgr.unpublishRelease(releaseId)

    @readonly
    def listImagesForTrove(self, hostname, name, version, flavor):
        self.auth.requireProductReadAccess(hostname)
        return self.imageMgr.listImagesForTrove(hostname, name, version,
                flavor)

    @readonly
    def listImagesForRelease(self, hostname, releaseId):
        self.auth.requireProductReadAccess(hostname)
        return self.imageMgr.listImagesForRelease(hostname, releaseId)

    @readonly
    def listImagesForProduct(self, hostname):
        self.auth.requireProductReadAccess(hostname)
        return self.imageMgr.listImagesForProduct(hostname)

    @readonly
    def getImageForProduct(self, hostname, imageId):
        self.auth.requireProductReadAccess(hostname)
        return self.imageMgr.getImageForProduct(hostname, imageId)

    @readonly
    def getImageStatus(self, hostname, imageId):
        self.auth.requireProductReadAccess(hostname)
        return self.imageMgr.getImageStatus(imageId)

    def setImageStatus(self, hostname, imageId, imageToken, status):
        self.auth.requireImageToken(hostname, imageId, imageToken)
        if status.isFinal:
            try:
                # This method is not running in a single transaction, since it
                # may want to update the status
                self._finalImageProcessing(imageId, status)
            except:
                self.rollback()
                self._holdCommits = False
                self.cancelImageBuild(imageId)
                raise
        return self.setVisibleImageStatus(imageId, status)

    def _finalImageProcessing(self, imageId, status):
        self.imageMgr.finalImageProcessing(imageId, status)

    @commitafter
    def setVisibleImageStatus(self, imageId, status):
        return self.imageMgr.setImageStatus(imageId, status)

    @commitafter
    def cancelImageBuild(self, imageId):
        """Only set the status if it's a non-terminal state"""
        status = self.imageMgr.getImageStatus(imageId)
        if status.isFinal:
            return
        status.set_status(jobstatus.FAILED, message = "Unknown error")
        return self.imageMgr.setImageStatus(imageId, status)

    @readonly
    def getImageFile(self, hostname, imageId, fileName, asResponse=False):
        self.auth.requireBuildsOnHost(hostname, [imageId])
        return self.fileMgr.getImageFile(hostname, imageId, fileName,
                asResponse)

    @readonly
    def appendImageFile(self, hostname, imageId, fileName, imageToken, data):
        self.auth.requireImageToken(hostname, imageId, imageToken)
        return self.fileMgr.appendImageFile(hostname, imageId, fileName,
                data)

    @commitafter
    def deleteImageForProduct(self, hostname, imageId):
        self.auth.requireProductDeveloper(hostname)
        return self.imageMgr.deleteImageForProduct(hostname, imageId)

    @commitafter
    def deleteImageFilesForProduct(self, hostname, imageId):
        self.auth.requireProductDeveloper(hostname)
        return self.imageMgr.deleteImageFilesForProduct(hostname, imageId)

    @readonly
    def listFilesForImage(self, hostname, imageId):
        self.auth.requireBuildsOnHost(hostname, [imageId])
        return self.imageMgr.listFilesForImage(hostname, imageId)

    @commitafter
    def setFilesForImage(self, hostname, imageId, imageToken, files):
        self.auth.requireImageToken(hostname, imageId, imageToken)
        return self.imageMgr.setFilesForImage(hostname, imageId, files)

    def getPlatformContentErrors(self, contentSourceName, instanceName):
        return self.capsuleMgr.getIndexerErrors(contentSourceName, instanceName)

    def getPlatformContentError(self, contentSourceName, instanceName, errorId):
        return self.capsuleMgr.getIndexerError(contentSourceName, instanceName,
            errorId)

    def updatePlatformContentError(self, contentSourceName, instanceName,
            errorId, resourceError):
        return self.capsuleMgr.updateIndexerError(contentSourceName,
            instanceName, errorId, resourceError)

    @commitafter
    def createImage(self, hostname, image, buildData=None):
        self.auth.requireProductDeveloper(hostname)
        imageId =  self.imageMgr.createImage(hostname, image, buildData)
        image.imageId = imageId
        return imageId

    @commitafter
    def uploadImageFiles(self, hostname, image, outputToken=None):
        self.auth.requireProductDeveloper(hostname)
        self.imageMgr.uploadImageFiles(hostname, image,
            outputToken=outputToken)
        return image

    @commitafter
    def createUser(self, username, password, fullName, email, 
                   displayEmail, blurb, admin=False):
        self.auth.requireAdmin()
        self.userMgr.createUser(username, password, fullName, email, 
                                displayEmail, blurb, admin=admin)


    @readonly    
    def getIdentity(self):
        if self.siteAuth:
            return self.siteAuth.getIdentityModel()
        raise RuntimeError("Identity information is not loaded.")

    @commitafter
    def getPlatforms(self):
        return self.platformMgr.getPlatforms()

    @commitafter
    def getPlatform(self, platformId):
        return self.platformMgr.getPlatform(platformId)

    @commitafter
    def createPlatform(self, platform, createPlatDef=True):
        return self.platformMgr.createPlatform(platform, createPlatDef)

    @readonly
    def getPlatformImageTypeDefs(self, request, platformId):
        return self.platformMgr.getPlatformImageTypeDefs(request, platformId)

    @readonly
    def getSourceTypes(self):
        return self.platformMgr.getSourceTypes()

    @readonly
    def getSourceType(self, sourceType):
        return self.platformMgr.getSourceType(sourceType)

    @readonly
    def getSourceTypeDescriptor(self, sourceType):
        return self.platformMgr.getSourceTypeDescriptor(sourceType)

    @commitafter
    def getSources(self, sourceType):
        return self.platformMgr.getSources(sourceType)

    @commitafter
    def getSourcesByPlatform(self, platformId):
        return self.platformMgr.getSourcesByPlatform(platformId)

    @commitafter
    def getSource(self, shortName):
        return self.platformMgr.getSource(shortName)

    @readonly
    def getSourceTypesByPlatform(self, platformId):
        return self.platformMgr.getSourceTypesByPlatform(platformId)

    @readonly
    def getPlatformStatus(self, platformId):
        return self.platformMgr.getPlatformStatus(platformId)

    @readonly
    def getPlatformStatusTest(self, platform):
        return self.platformMgr.getPlatformStatusTest(platform)

    @readonly
    def getPlatformLoadStatus(self, platformId, jobId):
        return self.platformMgr.getPlatformLoadStatus(platformId, jobId)

    @commitafter
    def getSourceStatusByName(self, sourceType, shortName):
        return self.platformMgr.getSourceStatusByName(shortName)

    @commitafter
    def getSourceStatus(self, source):
        return self.platformMgr.getSourceStatus(source)

    @commitafter
    def updateSource(self, shortName, sourceInstance):
        return self.platformMgr.updateSource(sourceInstance)

    @commitafter
    def updatePlatform(self, platformId, platform):
        return self.platformMgr.updatePlatform(platformId, platform)

    @commitafter
    def loadPlatform(self, platformId, platformLoad):
        return self.platformMgr.loadPlatform(platformId, platformLoad)

    @commitafter
    def createSource(self, source):
        return self.platformMgr.createSource(source)

    @commitafter
    def deleteSource(self, shortName):
        return self.platformMgr.deleteSource(shortName)

    # doesn't actually commit anything to the database, instead
    # it pushes to the entitlement server.
    @readonly
    def setRegistration(self, registrationData):
        assert self.siteAuth
        if self.siteAuth.isValid():
            # only require admin if we've got a valid setup.
            # If our setup is already invalid then allow anyone to
            # set the registration, as most of the interface (including 
            # logging in) is disabled.
            self.auth.requireAdmin()
        self.siteAuth.register(registrationData)

    @readonly
    def getRegistrationForm(self):
        assert self.siteAuth
        if self.siteAuth.isValid():
            self.auth.requireAdmin()
        return self.siteAuth.getForm()

    @readonly
    def getCACertificates(self):
        return self.pkiMgr.getCACertificates()

    @commitafter
    def createCertificate(self, purpose, desc, issuer=None, common=None,
            conditional=False):
        if conditional:
            x509_pem, pkey_pem = self.pkiMgr.getCertificatePair(purpose)
            if x509_pem:
                return x509_pem, pkey_pem
        return self.pkiMgr.createCertificate(purpose, desc, issuer, common)

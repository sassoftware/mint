#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import decorator

from conary import versions
from conary.conaryclient import cmdline
from conary.dbstore import sqllib

from mint import mint_error
from mint import projects
from mint import userlevels
from mint.lib import siteauth
from mint.rest.api import models
from mint.rest import errors
from mint.rest.db import authmgr
from mint.rest.db import awshandler
from mint.rest.db import emailnotifier
from mint.rest.db import imagemgr
from mint.rest.db import platformmgr
from mint.rest.db import productmgr
from mint.rest.db import publisher
from mint.rest.db import releasemgr
from mint.rest.db import usermgr


reservedHosts = ['admin', 'mail', 'mint', 'www', 'web', 'rpath', 'wiki', 'conary', 'lists']

class DBInterface(object):
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
        self.db = self.open()

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
        raise RuntimeError('Database modified unexpectedly after %s.' % fn.func_name)
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
        self.imageMgr = imagemgr.ImageManager(cfg, self, auth, self.publisher)
        self.releaseMgr = releasemgr.ReleaseManager(cfg, self,
                                                    auth, self.publisher)
        self.userMgr = usermgr.UserManager(cfg, self, auth, self.publisher)
        self.platformMgr = platformmgr.PlatformManager(cfg, self, auth)
        if subscribers is None:
            subscribers = []
            subscribers.append(emailnotifier.EmailNotifier(cfg, self,
                                                           auth))
            subscribers.append(awshandler.AWSHandler(cfg, self, auth))
        for subscriber in subscribers:
            self.publisher.subscribe(subscriber)

        # Don't instantiate things that go outside the core database
        # connection if dbOnly is set.
        self.siteAuth = None
        if not dbOnly:
            self.siteAuth = siteauth.SiteAuthorization(
                    cfgPath=cfg.siteAuthCfgPath)

    def close(self):
        #DBInterface.close(self)
        self.productMgr.reposMgr.close()

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
    def listProducts(self, start=0, limit=None, search=None, roles=None):
        return self.productMgr.listProducts(start=start, limit=limit,
                search=search, roles=roles)

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
        elif prodtype not in ('Appliance', 'Component', 'Platform', 'Repository'):
            raise mint_error.InvalidProdType

        fqdn = ".".join((product.hostname, product.domainname))
        projecturl = product.projecturl
        if (projecturl and not (projecturl.startswith('https://') 
            or projecturl.startswith('http://'))):
            product.projecturl = "http://" + projecturl
        for attr in ('projecturl', 'description', 'commitEmail'):
            if getattr(product, attr) is None:
                setattr(product, attr, '')

        if product.prodtype == 'Appliance':
            applianceValue = 1
        else:
            applianceValue = 0

        if self.cfg.hideNewProjects:
            product.hidden = True
        elif product.hidden is None:
            product.hidden = False

        productId = self.productMgr.createProduct(product.name, 
                                      product.description, product.hostname,
                                      product.domainname, product.namespace,
                                      applianceValue, product.projecturl,
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
                                      description=product.description,
                                      projecturl=product.projecturl,
                                      prodtype=product.prodtype,
                                      commitEmail=product.commitEmail)

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
            return models.Platform(platformTroveName='', platformVersion='',
                                   label='', platformName='',
                                   hostname=hostname, 
                                   productVersion=version)
        n,v,f = cmdline.parseTroveSpec(pd.getPlatformSourceTrove())
        v = versions.VersionFromString(v)
        return models.Platform(platformTroveName=str(n), # convert from unicode
                               platformVersion=str(v.trailingRevision()), 
                               label=str(v.trailingLabel()),
                               platformName=platformName,
                               hostname=hostname,
                               productVersion=version)

    @readonly    
    def getProductVersionStage(self, hostname, version, stageName):
        self.auth.requireProductReadAccess(hostname)
        pd = self.productMgr.getProductVersionDefinition(hostname, version)
        for stage in pd.getStages():
            if str(stage.name) == stageName:
                return models.Stage(name=str(stage.name),
                                    label=str(pd.getLabelForStage(stage.name)),
                                    hostname=hostname,
                                    version=version)
        raise errors.StageNotFound(stageName)

    @readonly    
    def getProductVersionStages(self, hostname, version):
        self.auth.requireProductReadAccess(hostname)
        pd = self.productMgr.getProductVersionDefinition(hostname, version)
        stageList = models.Stages()
        for stage in pd.getStages():
            stageList.stages.append(models.Stage(name=str(stage.name),
                                 label=str(pd.getLabelForStage(stage.name)),
                                 hostname=hostname,
                                 version=version))
        return stageList

    def listImagesForProductVersion(self, hostname, version, update=False):
        self.auth.requireProductReadAccess(hostname)
        return self.imageMgr.listImagesForProductVersion(hostname, version)

    def listImagesForProductVersionStage(self, hostname, version, stageName,
                                         update=False):
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


    @commitmaybe
    def listImagesForTrove(self, hostname, name, version, flavor, update=False):
        self.auth.requireProductReadAccess(hostname)
        return self.imageMgr.listImagesForTrove(hostname, name, version,
                flavor, update=update)

    @commitmaybe
    def listImagesForRelease(self, hostname, releaseId, update=False):
        self.auth.requireProductReadAccess(hostname)
        return self.imageMgr.listImagesForRelease(hostname, releaseId,
                update=update)

    @commitmaybe
    def listImagesForProduct(self, hostname, update=False):
        self.auth.requireProductReadAccess(hostname)
        return self.imageMgr.listImagesForProduct(hostname, update=update)

    @commitmaybe
    def getImageForProduct(self, hostname, imageId, update=False):
        self.auth.requireProductReadAccess(hostname)
        return self.imageMgr.getImageForProduct(hostname, imageId,
                update=update)

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
        self.auth.requireProductReadAccess(hostname)
        return self.imageMgr.listFilesForImage(hostname, imageId)

    @commitafter
    def createImage(self, hostname, image, buildData=None):
        self.auth.requireProductDeveloper(hostname)
        imageId =  self.imageMgr.createImage(hostname, image.imageType, 
                                            image.name,  
                                            image.getNameVersionFlavor(), 
                                            buildData)
        image.imageId = imageId
        return imageId
    
    @commitafter
    def setImageFiles(self, hostname, imageId, imageFiles):
        self.auth.requireAdmin()
        self.imageMgr.setImageFiles(hostname, imageId, imageFiles)

        

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

    @readonly    
    def listPlatforms(self):
        return self.platformMgr.listPlatforms()

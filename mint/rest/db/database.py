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


import decorator

from conary import versions
from conary.conaryclient import cmdline
from conary.dbstore import sqllib

from mint import jobstatus
from mint import mint_error
from mint import projects
from mint import userlevels
from mint.db import repository as reposdb
from mint.rest.api import models
from mint.rest import errors
from mint.rest.db import authmgr
from mint.rest.db import filemgr
from mint.rest.db import imagemgr
from mint.rest.db import pkimgr
from mint.rest.db import platformmgr
from mint.rest.db import productmgr
from mint.rest.db import publisher
from mint.rest.db import systemmgr
from mint.rest.db import targetmgr
from mint.rest.db import usermgr

reservedHosts = ['admin', 'mail', 'mint', 'www', 'web', 'rpath', 'wiki', 'lists']

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
        self.userMgr = usermgr.UserManager(cfg, self, auth, self.publisher)
        self.platformMgr = platformmgr.PlatformManager(cfg, self, auth)
        self.targetMgr = targetmgr.TargetManager(cfg, self, auth)
        self.pkiMgr = pkimgr.PKIManager(cfg, self, auth)
        self.systemMgr = systemmgr.SystemManager(cfg, self, auth)
        self.reposShim = reposdb.RepositoryManager(cfg, db._db)
        if subscribers is None:
            subscribers = []
        for subscriber in subscribers:
            self.publisher.subscribe(subscriber)
        self._djMgr = None

    @property
    def djMgr(self):
        if self._djMgr is None:
            from mint.django_rest.rbuilder.manager import rbuildermanager
            self._djMgr = rbuildermanager.RbuilderManager()
        return self._djMgr

    def close(self):
        DBInterface.close(self)
        self.reposShim.close()

    def reopen_fork(self):
        DBInterface.reopen_fork(self)
        self.reposShim.close_fork()
        self.reposShim = reposdb.RepositoryManager(self.cfg, self.db._db)

    def reset(self):
        self.reposShim.reset()

    def setAuth(self, auth, authToken):
        self.auth.setAuth(auth, authToken)

    def setProfiler(self, profile):
        #profile.attachDb(self.db.db)
        #profile.attachRepos(self.productMgr.reposMgr)
        pass

    def isOffline(self):
        return False

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
        cu.execute('SELECT fqdn FROM Projects where projectId=?', productId)
        return self._getOne(cu, errors.ProductNotFound, productId)[0]

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
            pd = self.productMgr.getProductVersionDefinitionByProductVersion(hostname, pv)
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

    def getProductVersionPlatformVersion(self, hostname, version):
        self.auth.requireProductReadAccess(hostname)
        pd = self.productMgr.getProductVersionDefinition(hostname, version)
        platformName = pd.getPlatformName()
        sourceTrove = pd.getPlatformSourceTrove()
        if not sourceTrove:
            return models.EmptyPlatformVersion()
        n,v,f = cmdline.parseTroveSpec(sourceTrove)
        v = versions.VersionFromString(v)
        # convert trove name from unicode
        platformLabel = str(v.trailingLabel())
        localPlatform = self.platformMgr.getPlatformByLabel(platformLabel)
        if localPlatform:
            platformTroves = [pt for pt in pd.getPlatformSearchPaths() \
                if pt.isPlatformTrove]
            if not platformTroves:
                return models.EmptyPlatformVersion()
            platformTrove = platformTroves[0]
            name = str(platformTrove.troveName)
            revision = str(platformTrove.version)
            return self.platformMgr.getPlatformVersion(
                localPlatform.platformId, 
                "%s=%s" % (name, revision))
        else:
            return models.EmptyPlatformVersion()

    @readonly    
    def getProductVersionStage(self, hostname, version, stageName):
        self.auth.requireProductReadAccess(hostname)
        pd = self.productMgr.getProductVersionDefinition(hostname, version)
        stages = pd.getStages()
        for stage in stages:
            if str(stage.name) == stageName:
                return models.Stage(name=str(stage.name),
                                    label=str(pd.getLabelForStage(stage.name)),
                                    hostname=hostname,
                                    version=version,
                                    isPromotable=False)
        raise errors.StageNotFound(stageName)

    @readonly    
    def getProductVersionStages(self, hostname, version):
        self.auth.requireProductReadAccess(hostname)
        pd = self.productMgr.getProductVersionDefinition(hostname, version)
        stageList = models.Stages()
        stages = pd.getStages()
        for stage in stages:
            stageList.stages.append(models.Stage(name=str(stage.name),
                                 label=str(pd.getLabelForStage(stage.name)),
                                 hostname=hostname,
                                 version=version,
                                 isPromotable=False))
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
    
    def getProductVersionDefinitionFromVersion(self, hostname, version):
        self.auth.requireProductReadAccess(hostname)
        return self.productMgr.getProductVersionDefinitionByProductVersion(hostname, version)

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
    def listImagesForTrove(self, hostname, name, version, flavor):
        self.auth.requireProductReadAccess(hostname)
        return self.imageMgr.listImagesForTrove(hostname, name, version,
                flavor)

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
    def listFilesForImage(self, hostname, imageId):
        self.auth.requireBuildsOnHost(hostname, [imageId])
        return self.imageMgr.listFilesForImage(hostname, imageId)

    @commitafter
    def createUser(self, username, password, fullName, email, 
                   displayEmail, blurb, admin=False):
        self.auth.requireAdmin()
        self.userMgr.createUser(username, password, fullName, email, 
                                displayEmail, blurb, admin=admin)

    @commitafter
    def getPlatforms(self):
        return self.platformMgr.getPlatforms()

    @commitafter
    def getPlatform(self, platformId):
        return self.platformMgr.getPlatform(platformId)

    @commitafter
    def getPlatformVersion(self, platformId, platformVersionId):
        return self.platformMgr.getPlatformVersion(platformId, platformVersionId)

    @commitafter
    def getPlatformVersions(self, platformId):
        return self.platformMgr.getPlatformVersions(platformId)

    @commitafter
    def createPlatform(self, platform, createPlatDef=True, overwrite=False):
        return self.platformMgr.createPlatform(platform, createPlatDef, overwrite)

    @readonly
    def getPlatformImageTypeDefs(self, request, platformId):
        return self.platformMgr.getPlatformImageTypeDefs(request, platformId)

    @commitafter
    def updatePlatform(self, platformId, platform):
        return self.platformMgr.updatePlatform(platformId, platform)

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

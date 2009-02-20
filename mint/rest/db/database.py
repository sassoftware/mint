from conary import versions
from conary.conaryclient import cmdline

from mint import projects
from mint import userlevels
from mint.rest.api import models
from mint.rest import errors
from mint.rest.db import authmgr
from mint.rest.db import productmgr
from mint.rest.db import publisher
from mint.rest.db import emailnotifier
from mint.rest.db import awshandler


reservedHosts = ['admin', 'mail', 'mint', 'www', 'web', 'rpath', 'wiki', 'conary', 'lists']

class Database(object):
    def __init__(self, cfg, db, auth=None):
        self.cfg = cfg
        self.db = db
        self.userId = -1
        self.isAdmin = False
        if auth is None:
            auth = authmgr.AuthenticationManager(cfg, self)
        self.auth = auth
        self.publisher = publisher.EventPublisher()
        self.publisher.subscribe(emailnotifier.EmailNotifier(self.cfg, self))
        #self.publisher.subscribe(awshandler.AWSHandler(self.cfg, self.db, self))
        self.productMgr = productmgr.ProductManager(self.cfg, self.db, 
                                                    self.auth, self.publisher)

    def setAuth(self, auth, authToken):
        self.auth.setAuth(auth, authToken)
        self.userId = auth.userId
        self.username = auth.username
        self.isAdmin = auth.admin

    def _getOne(self, cu, exception, key):
        try:
            cu = iter(cu)
            res = cu.next()
            assert (not(list(cu))), key # make sure that we really only
                                        # got one entry
            return res
        except:
            raise exception(key)

    def getUsername(self, userId):
        cu = self.db.cursor()
        cu.execute('SELECT username from Users where userId=?', userId)
        return self._getOne(cu, errors.UserNotFound, userId)[0]

    def listProducts(self):
        cu = self.db.cursor()
        if self.isAdmin:
            cu.execute('''
                SELECT projectId, hostname, name 
                FROM Projects ORDER BY hostname''')
        else:
            cu.execute('''
                SELECT Projects.projectId, hostname, name
                FROM Projects 
                LEFT JOIN ProjectUsers ON (
                    ProjectUsers.projectId=Projects.projectId 
                    AND userId=?)
                WHERE NOT Projects.hidden OR 
                      ProjectUsers.level IS NOT NULL
                ORDER BY hostname
               ''', self.userId)
        results = models.ProductSearchResultList()
        for id, hostname, name in cu:
            results.addProduct(id, hostname, name)
        return results

    def getProductFQDNFromId(self, productId):
        cu = self.db.cursor()
        cu.execute('SELECT hostname, domainname from Projects where projectId=?', productId)
        hostname, domainname = self._getOne(cu, errors.ProductNotFound, 
                                            productId)
        return hostname + '.' + domainname

    def getProduct(self, hostname):
        self.auth.requireProductReadAccess(hostname=hostname)
        return self.productMgr.getProduct(hostname)

    def listProductVersions(self, hostname):
        self.auth.requireProductReadAccess(hostname=hostname)
        if '.' in hostname:
            hostname, domainname = hostname.split('.', 1)
        cu = self.db.cursor()
        cu.execute('''SELECT productVersionId as id, 
                          PVTable.namespace, PVTable.name, PVTable.description  
                      FROM Projects 
                      JOIN ProductVersions as PVTable USING (projectId)
                      WHERE Projects.hostname=?''', hostname)
        pvl = models.ProductVersionList()
        for id, namespace, name, description in cu:
            pvl.addProductVersion(id, namespace, name, description,
                                  hostname)
        return pvl

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

    def getProductVersion(self, hostname, versionName):
        self.auth.requireProductReadAccess(hostname=hostname)
        return self.productMgr.getProductVersion(hostname, versionName)

    def getUserId(self, username):
        cu = self.db.cursor()
        cu.execute("""SELECT userId FROM Users WHERE username=?""", username)
        userId, = self._getOne(cu, errors.UserNotFound, username)
        return userId

    def getProductId(self, fqdn):
        cu = self.db.cursor()
        hostname = fqdn.split('.', 1)[0]
        cu.execute("""SELECT projectId FROM Users WHERE hostname=?""", hostname)
        projectId, = self._getOne(cu, errors.ProductNotFound, fqdn)
        return projectId


    def getUser(self, username):
        self.auth.requireLogin()
        if self.hasUserReadAccess(username):
            self._getUser(username, includePrivateInfo=True)
        else:
            self._getUser(username, includePrivateInfo=False)

    def _getUser(self, username, includePrivateInfo=True):
        if includePrivateInfo:
            cu = self.db.cursor()
            cu.execute("""SELECT userId as id, username, fullName,
                                 email, displayEmail, timeCreated, timeAccessed,
                                 active, blurb 
                           FROM Users WHERE username=?""", username)
        else:
            cu = self.db.cursor()
            cu.execute("""SELECT userId as id, username, fullName,
                                 displayEmail, blurb 
                           FROM Users WHERE username=? AND active=1""", 
                           username)
        d = dict(self._getOne(cu, errors.UserNotFound, username))
        return models.User(**d)

        
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

    def listUsers(self):
        self.auth.requireAdmin()
        cu = self.db.cursor()
        cu.execute("""SELECT userId as id, username, fullName,
                             email, displayEmail, timeCreated, timeAccessed,
                             active, blurb FROM Users""")
        userList = models.UserList()
        for d in cu:
            userList.users.append(models.User(**d))
        return userList

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

    def createProduct(self, product):
        self.auth.requireProductCreationRights()
        if self.cfg.rBuilderOnline or not product.domainname:
            product.domainname = self.cfg.projectDomainName.split(':')[0]
        projects._validateShortname(product.shortname, product.domainname, reservedHosts)
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
        elif prodtype not in ('Appliance', 'Component'):
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
        product.id = productId
        return product

    def setMemberLevel(self, hostname, username, level):
        self.auth.requireProductOwner(hostname)
        level = userlevels.idsByName[level]
        product = self.getProduct(hostname)
        userId = self.getUserId(username)
        self.productMgr.setMemberLevel(product.id, userId, level)

    def deleteMember(self, hostname, username):
        self.auth.requireProductOwner(hostname)
        product = self.getProduct(hostname)
        userId = self.getUserId(username)
        self.productMgr.removeMember(product.id, userId)

    def cancelUserAccount(self, username):
        self.userMgr.cancelUserAccount(userId)

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

    def updateProductVersion(self, hostname, version, productVersion):
        self.auth.requireProductOwner(hostname)
        self.productMgr.updateProductVersion(hostname,
                                             version, productVersion.description)

    def getProductVersionPlatform(self, hostname, version):
        pd = self.getProductVersionDefinition(hostname, version)
        n,v,f = cmdline.parseTroveSpec(pd.getPlatformSourceTrove())
        v = versions.VersionFromString(v)
        return models.Platform(name=str(n), # convert from unicode
                               version=str(v.trailingRevision()), 
                               label=str(v.trailingLabel()))

    def getProductVersionStages(self, hostname, version):
        pd = self.getProductVersionDefinition(hostname, version)
        stageList = models.Stages()
        for stage in pd.getStages():
            stageList.stages.append(models.Stage(name=str(stage.name),
                                                 label=str(pd.getLabelForStage(stage.name))))
        return stageList

    def getProductVersionDefinition(self, hostname, version):
        self.auth.requireProductReadAccess(hostname)
        return self.productMgr.getProductVersionDefinition(hostname, version)

    def setProductVersionDefinition(self, hostname, version, pd):
        self.auth.requireProductDeveloper(hostname)
        return self.productMgr.setProductVersionDefinition(hostname, version, pd)

    def rebaseProductVersionPlatform(self, hostname, version, platformLabel=None):
        self.auth.requireProductDeveloper(hostname)
        self.productMgr.rebaseProductVersionDefinition(hostname, version, platformLabel)

    def cursor(self):
        return self.db.cursor()

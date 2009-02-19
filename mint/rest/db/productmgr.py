import time

from mint import userlevels
from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import reposmgr

from rpath_common.proddef import api1 as proddef

# FIXME - really shouldn't be any SQL in this file.

class ProductManager(object):
    def __init__(self, cfg, db, auth, publisher=None):
        self.cfg = cfg
        self.db = db
        self.auth = auth
        self.reposMgr = reposmgr.RepositoryManager(cfg, db, self.db.projects.reposDB,
                                                   auth)
        self.publisher = publisher

    def getProduct(self, hostname):
        # accept fqdn.
        hostname = hostname.split('.')[0]
        cu = self.db.cursor()
        sql = '''
            SELECT Projects.projectId,hostname,name,shortname,
                   domainname, description, Users.username as creator, projectUrl,
                   isAppliance, Projects.timeCreated, Projects.timeModified,
                   commitEmail, prodtype, backupExternal 
            FROM Projects
            JOIN Users ON (creatorId=Users.userId)
            WHERE hostname=?
        '''
        cu.execute(sql, hostname)
        d = dict(self.db._getOne(cu, errors.ProductNotFound, hostname))
        d['id'] = d.pop('projectId')
        return models.Product(**d)

    def getProductVersion(self, hostname, versionName):
        # accept fqdn.
        if '.' in hostname:
            hostname, domainname = hostname.split('.', 1)
        cu = self.db.cursor()
        cu.execute('''SELECT productVersionId as id, 
                          PVTable.namespace, PVTable.name, PVTable.description  
                      FROM Projects 
                      JOIN ProductVersions as PVTable USING (projectId)
                      WHERE Projects.hostname=? AND PVTable.name=?''', 
                      hostname, versionName)
        results = self.db._getOne(cu, errors.ProductVersionNotFound, 
                                  (hostname, versionName))
        id, namespace, name, description = results
        return models.ProductVersion(id=id, hostname=hostname,
                                     namespace=namespace, name=name, 
                                     description=description)

    def createProduct(self, name, description, hostname,
                      domainname, namespace, isAppliance,
                      projecturl, shortname, prodtype,
                      version, commitEmail, isPrivate):
        # All database operations must abort cleanly, especially when
        # creating the repository fails. Otherwise, we'll end up with
        # a completely broken project that may not even delete cleanly.
        #
        # No database operation inside this block may commit the
        # transaction.
        self.db.transaction()
        try:
            createTime = time.time()
            projectId = self.db.projects.new(
                name=name,
                creatorId=self.server.userId, 
                description=description, 
                hostname=hostname,
                domainname=domainname, 
                namespace=namespace,
                isAppliance=isAppliance, 
                projecturl=projecturl,
                timeModified=createTime, 
                timeCreated=createTime,
                shortname=shortname, 
                prodtype=prodtype, 
                commitEmail=commitEmail, 
                hidden=isPrivate,
                version=version,
                commit=False)

            # add to RepNameMap if projectDomainName != domainname
            fqdn = ".".join((hostname, domainname))
            projectDomainName = self.cfg.projectDomainName.split(':')[0]
            if domainname != projectDomainName:
                self.db.repNameMap.new(fromName='%s.%s' % (hostname, projectDomainName),
                                       toName=fqdn, commit=False)
            self.db.labels.addLabel(projectId, '%s@%s:%s-%s-devel' % (fqdn, namespace, hostname, version),
                "http://%s%srepos/%s/" % (
                self.cfg.projectSiteHost, self.cfg.basePath, hostname),
                authType='userpass', username=self.cfg.authUser, password=self.cfg.authPass, commit=False)

            self.reposMgr.createRepository(hostname, domainname, isPrivate=isPrivate)
            # can only add members after the repository is set up
            if self.auth.userId >= 0:
                self.setMemberLevel(projectId, self.auth.userId, userlevels.OWNER)
            self.publisher.notify('ProjectCreated', self.auth.auth, projectId)
        except:
            self.db.rollback()
            raise
        self.db.commit()
        return projectId

    def isMember(self, projectId, userId):
        cu = self.db.cursor()
        cu.execute("""SELECT level FROM ProjectUsers
                      WHERE projectId = ? AND userId = ?""",
                      projectId, userId)
        if cu.fetchone():
            return True
        return False

    def _getProductFQDN(self, projectId):
        cu = self.db.cursor()
        cu.execute('SELECT hostname, domainname from Projects where projectId=?', projectId)
        return '.'.join(tuple(cu.next()))

    def _getUsername(self, userId):
        cu = self.db.cursor()
        cu.execute('SELECT username from Users where userId=?', userId)
        return cu.next()[0]

    def _getPassword(self, userId):
        cu = self.db.cursor()
        cu.execute('SELECT passwd, salt from Users where userId=?', userId)
        return cu.next()

    def setMemberLevel(self, projectId, userId, level):
        fqdn = self._getProdutFQDN(projectId)
        username = self._getUsername(userId)
        isMember = self.isMember(projectId, userId)
        write = level in userlevels.WRITERS
        mirror = level == userlevels.OWNER
        admin = level == userlevels.OWNER and self.cfg.projectAdmin

        if isMember:
            if self.db.projectUsers.onlyOwner(projectId, userId) and \
                   (level != userlevels.OWNER):
                raise users.LastOwner
            cu = self.db.cursor()

            cu.execute("""UPDATE ProjectUsers SET level=? WHERE userId=? and
                projectId=?""", level, userId, projectId)
            self.reposMgr.editUser(fqdn, username, write=write,
                                   mirror=mirror, admin=admin)
            self.publisher.notify('UserProjectChanged', self.auth.auth, userId, projectId, level)
            return False
        else:
            password, salt = self._getPassword(userId)
            self.db.transaction()
            try:
                self.db.projectUsers.new(userId=userId, projectId=projectId,
                                      level=level, commit=False)
                self.reposMgr.addUserByMd5(fqdn, username, salt, password, write=True,
                                           mirror=True, admin=admin)
                self.publisher.notify('UserProjectAdded', self.auth.auth, userId, projectId, level)
            except:
                self.db.rollback()
                raise
            else:
                self.db.commit()
            return True

    def removeMember(self, projectId, userId):
        fqdn = self._getProductFQDN(projectId)
        username = self._getUsername(userId)
        if self.db.projectUsers.onlyOwner(projectId, userId):
            raise users.LastOwner
        self.reposMgr.deleteUser(fqdn, username)
        self.db.projectUsers.delete(projectId, userId)
        self.publisher.notify('UserProjectRemoved', self.auth.auth, userId, projectId)

    def createProductVersion(self, fqdn, version, namespace, description):
        product = self.db.getProduct(fqdn)
        if not namespace:
            namespace = product.namespace
        projectId = product.id
        # Check the namespace
        projects._validateNamespace(namespace)
        # make sure it is a valid product version
        projects._validateProductVersion(name)
        
        try:
            return self.productVersions.new(projectId = projectId,
                                            namespace = namespace,
                                            name = name,
                                            description = description)
        except mint_error.DuplicateItem:
            raise mint_error.DuplicateProductVersion

    def updateProductVersion(self, fqdn, version, description):
        productVersion = self.getProductVersion(fqdn, version)
        self.productVersions.update(productVersion.id, 
                                    description = description)

    def getProductVersionDefinition(self, fqdn, version):
        productVersion = self.getProductVersion(fqdn, version)
        product = self.getProduct(fqdn)
        pd = proddef.ProductDefinition()
        pd.setProductShortname(product.shortname)
        pd.setConaryRepositoryHostname(product.getFQDN())
        pd.setConaryNamespace(productVersion.namespace)
        pd.setProductVersion(productVersion.name)
        cclient = self.reposMgr.getInternalConaryClient(fqdn)
        try:
            pd.loadFromRepository(cclient)
        except Exception, e:
            # XXX could this exception handler be more specific? As written
            # any error in the proddef module will be masked.
            raise ProductDefinitionVersionNotFound
        return pd

    def setProductVersionDefinition(self, fqdn, version, prodDef):
        cclient = self.reposMgr.getInternalConaryClient(fqdn)
        prodDef.saveToRepository(cclient,
                'Product Definition commit from rBuilder\n')

    def rebaseProductVersionDefinition(self, fqdn, version, platformLabel):
        pd = self.getProductVersionDefinition(fqdn, version)
        cclient = self.reposMgr.getInternalConaryClient(fqdn)
        pd.rebase(cclient, platformLabel)
        pd.saveToRepository(cclient, 
                'Product Definition commit from rBuilder\n')


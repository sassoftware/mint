#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import time

from conary.lib import util
from rpath_common.proddef import api1 as proddef

from mint import helperfuncs
from mint import mint_error
from mint import projects
from mint import userlevels
from mint import templates
from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import reposmgr
from mint.templates import groupTemplate


class ProductManager(object):
    def __init__(self, cfg, db, auth, publisher=None):
        self.cfg = cfg
        self.db = db
        self.auth = auth
        self.reposMgr = reposmgr.RepositoryManager(cfg, db, 
                                                   self.db.projects.reposDB,
                                                   auth)
        self.publisher = publisher

    def getProduct(self, fqdn):
        # accept fqdn.
        hostname = fqdn.split('.')[0]
        cu = self.db.cursor()
        sql = '''
            SELECT Projects.projectId as productId,hostname,name,shortname,
                   domainname, namespace, 
                   description, Users.username as creator, projectUrl,
                   isAppliance, Projects.timeCreated, Projects.timeModified,
                   commitEmail, prodtype, backupExternal 
            FROM Projects
            LEFT JOIN Users ON (creatorId=Users.userId)
            WHERE hostname=?
        '''
        cu.execute(sql, hostname)
        d = dict(self.db._getOne(cu, errors.ProductNotFound, hostname))
        d['repositoryHostname'] = d['shortname'] + '.' + d.pop('domainname')
        p = models.Product(**d)
        return p

    def listProducts(self):
        cu = self.db.cursor()
        if self.auth.isAdmin:
            cu.execute('''
                SELECT Projects.projectId as productId,
                   hostname,name,shortname,
                   domainname, namespace, 
                   description, Users.username as creator, projectUrl,
                   isAppliance, Projects.timeCreated, Projects.timeModified,
                   commitEmail, prodtype, backupExternal 
                FROM Projects 
                LEFT JOIN Users ON (creatorId=Users.userId)
                ORDER BY hostname''')
        else:
            cu.execute('''
                SELECT Projects.projectId as productId,
                   hostname,name,shortname, domainname, namespace, 
                   description, Users.username as creator, projectUrl,
                   isAppliance, Projects.timeCreated, Projects.timeModified,
                   commitEmail, prodtype, backupExternal 
                FROM Projects 
                LEFT JOIN ProjectUsers ON (
                    ProjectUsers.projectId=Projects.projectId 
                    AND ProjectUsers.userId=?)
                LEFT JOIN Users ON (creatorId=Users.userId)
                WHERE NOT Projects.hidden OR 
                      ProjectUsers.level IS NOT NULL
                ORDER BY hostname
               ''', self.auth.userId)
        results = models.ProductSearchResultList()
        for row in cu:
            d = dict(row)
            d['repositoryHostname'] = d['hostname'] + '.' + d.pop('domainname')
            p = models.Product(**d)
            results.products.append(p)
        return results


    def getProductVersion(self, hostname, versionName):
        # accept fqdn.
        if '.' in hostname:
            hostname, domainname = hostname.split('.', 1)
        cu = self.db.cursor()
        cu.execute('''SELECT productVersionId as versionId, 
                          PVTable.namespace, PVTable.name, PVTable.description  
                      FROM Projects 
                      JOIN ProductVersions as PVTable USING (projectId)
                      WHERE Projects.hostname=? AND PVTable.name=?''', 
                      hostname, versionName)
        results = self.db._getOne(cu, errors.ProductVersionNotFound, 
                                  (hostname, versionName))
        versionId, namespace, name, description = results
        return models.ProductVersion(versionId=versionId, hostname=hostname,
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
        if namespace is None:
            namespace = self.cfg.namespace
        try:
            createTime = time.time()
            projectId = self.db.projects.new(
                name=name,
                creatorId=self.auth.userId, 
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
            self.db.labels.addLabel(projectId, 
                '%s@%s:%s-%s-devel' % (fqdn, namespace, 
                                       hostname, version),
                "http://%s%srepos/%s/" % (
                self.cfg.projectSiteHost, self.cfg.basePath, hostname),
                authType='userpass', username=self.cfg.authUser, 
                password=self.cfg.authPass, commit=False)

            self.reposMgr.createRepository(hostname, domainname, 
                                           isPrivate=isPrivate)
            # can only add members after the repository is set up
            if self.auth.userId >= 0:
                self.setMemberLevel(projectId, self.auth.userId, userlevels.OWNER)
            self.publisher.notify('ProjectCreated', projectId)
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
                raise mint_error.LastOwner
            cu = self.db.cursor()

            cu.execute("""UPDATE ProjectUsers SET level=? WHERE userId=? and
                projectId=?""", level, userId, projectId)
            self.reposMgr.editUser(fqdn, username, write=write,
                                   mirror=mirror, admin=admin)
            self.publisher.notify('UserProjectChanged', userId, projectId, level)
            return False
        else:
            password, salt = self._getPassword(userId)
            self.db.transaction()
            try:
                self.db.projectUsers.new(userId=userId, projectId=projectId,
                                      level=level, commit=False)
                self.reposMgr.addUserByMd5(fqdn, username, salt, password, write=True,
                                           mirror=True, admin=admin)
                self.publisher.notify('UserProjectAdded', userId, 
                                      projectId, level)
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
            raise mint_error.LastOwner
        self.reposMgr.deleteUser(fqdn, username)
        self.db.projectUsers.delete(projectId, userId)
        self.publisher.notify('UserProjectRemoved', 
                              userId, projectId)

    def createProductVersion(self, fqdn, version, namespace, description,
                             platformLabel):
        product = self.getProduct(fqdn)
        if not namespace:
            namespace = product.namespace
        projectId = product.id
        # Check the namespace
        projects._validateNamespace(namespace)
        # make sure it is a valid product version
        projects._validateProductVersion(version)

        # initial product definition
        prodDef = helperfuncs.sanitizeProductDefinition(product.shortname,
                        description, product.hostname, product.domainname, 
                        product.shortname, version,
                        '', namespace)
        label = prodDef.getDefaultLabel()

        # validate the label, which will be added later.  This is done
        # here so the project is not created before this error occurs
        if projects.validLabel.match(label) == None:
            raise mint_error.InvalidLabel(label)

        if platformLabel:
            cclient = self.reposMgr.getInternalConaryClient(fqdn)
            prodDef.rebase(cclient, platformLabel)
        self.setProductVersionDefinition(fqdn, version, prodDef)
        
        try:
            versionId = self.db.productVersions.new(projectId = projectId,
                                               namespace = namespace,
                                               name = version,
                                               description = description)
        except mint_error.DuplicateItem:
            raise mint_error.DuplicateProductVersion

        groupName = helperfuncs.getDefaultImageGroupName(product.hostname)
        className = util.convertPackageNameToClassName(groupName)
        # convert from unicode
        recipeStr = str(templates.write(groupTemplate,
                        cfg = self.cfg,
                        groupApplianceLabel=platformLabel,
                        groupName=groupName,
                        recipeClassName=className,
                        version=version) + '\n')
        self.reposMgr.createSourceTrove(fqdn, groupName,
                                    label, version,
                                    {'%s.recipe' % groupName: recipeStr},
                                    'Initial appliance image group template')
        return versionId

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
            raise mint_error.ProductDefinitionVersionNotFound
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

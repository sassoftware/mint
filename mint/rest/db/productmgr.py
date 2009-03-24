#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import os
import itertools
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
                                                   self.db.db.projects.reposDB,
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
                   commitEmail, prodtype, backupExternal, hidden, level
            FROM Projects
            LEFT JOIN Users ON (creatorId=Users.userId)
            LEFT JOIN ProjectUsers ON (
                            Projects.projectId=ProjectUsers.projectId
                            AND ProjectUsers.userId=?)
            WHERE hostname=?
        '''
        cu.execute(sql, self.auth.userId, hostname)
        d = dict(self.db._getOne(cu, errors.ProductNotFound, hostname))

        level = d.pop('level', None)
        if level is not None:
            d['role'] = userlevels.names[level]

        d['repositoryHostname'] = d['shortname'] + '.' + d['domainname']
        p = models.Product(**d)
        return p

    def listProducts(self, start=0, limit=None):
        cu = self.db.cursor()
        if self.auth.isAdmin:
            sql = '''
                SELECT Projects.projectId as productId,
                   hostname,name,shortname,
                   domainname, namespace, 
                   description, Users.username as creator, projectUrl,
                   isAppliance, Projects.timeCreated, Projects.timeModified,
                   commitEmail, prodtype, backupExternal, ProjectUsers.level 
                FROM Projects 
                LEFT JOIN ProjectUsers ON (
                    ProjectUsers.projectId=Projects.projectId 
                    AND ProjectUsers.userId=?)
                LEFT JOIN Users ON (creatorId=Users.userId)
                ORDER BY hostname'''
        else:
            sql = '''\
                SELECT Projects.projectId as productId,
                   hostname,name,shortname, domainname, namespace, 
                   description, Users.username as creator, projectUrl,
                   isAppliance, Projects.timeCreated, Projects.timeModified,
                   commitEmail, prodtype, backupExternal, ProjectUsers.level 
                FROM Projects 
                LEFT JOIN ProjectUsers ON (
                    ProjectUsers.projectId=Projects.projectId 
                    AND ProjectUsers.userId=?)
                LEFT JOIN Users ON (creatorId=Users.userId)
                WHERE NOT Projects.hidden OR 
                      ProjectUsers.level IS NOT NULL
                ORDER BY hostname'''
        if limit:
            sql += ' LIMIT %d' % limit
        if start:
            sql += ' OFFSET %d' % start
        cu.execute(sql, self.auth.userId)
        results = models.ProductSearchResultList()
        for row in cu:
            d = dict(row)
            level = d.pop('level', None)
            if level is not None:
                d['role'] = userlevels.names[level]
            d['repositoryHostname'] = d['hostname'] + '.' + d['domainname']
            p = models.Product(**d)
            results.products.append(p)
        return results


    def getProductVersion(self, fqdn, versionName):
        # accept fqdn.
        hostname = fqdn.split('.')[0]
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
        if namespace is None:
            namespace = self.cfg.namespace
        createTime = time.time()
        projectId = self.db.db.projects.new(
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
            self.db.db.repNameMap.new(fromName='%s.%s' % (hostname, projectDomainName),
                                   toName=fqdn, commit=False)
        self.db.db.labels.addLabel(projectId, 
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
            self.setMemberLevel(projectId, self.auth.userId, userlevels.OWNER,
                                notify=False)
        self.publisher.notify('ProjectCreated', projectId)
        return projectId

    def _getMemberLevel(self, projectId, userId):
        # internal fn because it takes projectId + userId 
        # instead of hostname + username
        cu = self.db.cursor()
        cu.execute("""SELECT level FROM ProjectUsers
                      WHERE projectId = ? AND userId = ?""",
                      projectId, userId)
        level = cu.fetchone()
        if level:
            return True, level[0]
        return False, None

    def _getProductFQDN(self, projectId):
        cu = self.db.cursor()
        cu.execute('SELECT hostname, domainname from Projects where projectId=?', projectId)
        return '.'.join(tuple(cu.next()))

    def setMemberLevel(self, projectId, userId, level, notify=True):
        fqdn = self._getProductFQDN(projectId)
        username = self.db.userMgr._getUsername(userId)
        isMember, oldLevel = self._getMemberLevel(projectId, userId)
        write = level in userlevels.WRITERS
        mirror = level == userlevels.OWNER
        admin = level == userlevels.OWNER and self.cfg.projectAdmin

        if isMember:
            if level == oldLevel:
                return
            if (level != userlevels.OWNER and oldLevel == userlevels.OWNER
                and self.db.db.projectUsers.onlyOwner(projectId, userId)):
                # TODO: this error is not quite right.  We're not explicitly
                # trying to "orphan" the project just demote the last owner.
                raise mint_error.LastOwner
            cu = self.db.cursor()

            cu.execute("""UPDATE ProjectUsers SET level=? WHERE userId=? and
                projectId=?""", level, userId, projectId)
            self.reposMgr.editUser(fqdn, username, write=write,
                                   mirror=mirror, admin=admin)
            if notify:
                self.publisher.notify('UserProductChanged', userId, projectId, 
                                      oldLevel, level)
            return False
        else:
            password, salt = self.db.userMgr._getPassword(userId)
            self.db.db.projectUsers.new(userId=userId, projectId=projectId,
                                     level=level, commit=False)
            self.reposMgr.addUserByMd5(fqdn, username, salt, password, 
                                       write=write, mirror=mirror, admin=admin)
            if notify:
                self.publisher.notify('UserProductAdded', userId,
                                      projectId, level)
            return True

    def deleteMember(self, projectId, userId, notify=True):
        fqdn = self._getProductFQDN(projectId)
        username = self.db.userMgr._getUsername(userId)
        if self.db.db.projectUsers.lastOwner(projectId, userId):
            # This check ensures there are no developers assigned
            # to this project.  (As opposed to onlyOwner which merely
            # checks that this user is not the last owner.)  TODO:   
            # rename these checks to be clearer and move them here,
            # and create separate exceptions. 
            raise mint_error.LastOwner
        self.reposMgr.deleteUser(fqdn, username)
        self.db.db.projectUsers.delete(projectId, userId)
        if notify:
            self.publisher.notify('UserProductRemoved', 
                                  userId, projectId)

    def createProductVersion(self, fqdn, version, namespace, description,
                             platformLabel):
        product = self.getProduct(fqdn)
        if not namespace:
            namespace = product.namespace
        projectId = product.productId
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
            cclient = self.reposMgr.getConaryClientForProduct(fqdn)
            prodDef.rebase(cclient, platformLabel)
        self.setProductVersionDefinition(fqdn, version, prodDef)
        
        try:
            versionId = self.db.db.productVersions.new(projectId = projectId,
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

    def getProductVersionForLabel(self, fqdn, label):
        cu = self.db.cursor()
        cu.execute('''SELECT productVersionId, hostname, 
                             domainname, shortname, 
                             ProductVersions.namespace,    
                             ProductVersions.name 
                      FROM Projects 
                      JOIN ProductVersions USING(projectId)
                      WHERE hostname=?''', fqdn.split('.')[0])
        for versionId, hostname, domainname, shortname, namespace, name in cu:
            fqdn = '%s.%s' % (hostname, domainname)
            pd = proddef.ProductDefinition()
            pd.setProductShortname(shortname)
            pd.setConaryRepositoryHostname(fqdn)
            pd.setConaryNamespace(namespace)
            pd.setProductVersion(name)
            baseLabel = pd.getProductDefinitionLabel()
            # assumption to speed this up.  
            # Stages are baselabel + '-' + extention (or just baseLabel)
            if not str(label).startswith(str(baseLabel)):
                continue
            try:
                cclient = self.reposMgr.getConaryClientForProduct(fqdn)
                pd.loadFromRepository(cclient)
            except Exception, e:
                return versionId, None

            for stage in pd.getStages():
                stageLabel = pd.getLabelForStage(stage.name)
                if str(label) == stageLabel:
                    return versionId, str(stage.name)
            return versionId, None
        return None, None


    def updateProductVersion(self, fqdn, version, description):
        productVersion = self.getProductVersion(fqdn, version)
        self.db.db.productVersions.update(productVersion.versionId, 
                                          description = description)

    def getProductVersionDefinition(self, fqdn, version):
        productVersion = self.getProductVersion(fqdn, version)
        product = self.getProduct(fqdn)
        pd = proddef.ProductDefinition()
        pd.setProductShortname(product.shortname)
        pd.setConaryRepositoryHostname(product.getFQDN())
        pd.setConaryNamespace(productVersion.namespace)
        pd.setProductVersion(productVersion.name)
        cclient = self.reposMgr.getConaryClientForProduct(fqdn)
        try:
            pd.loadFromRepository(cclient)
        except Exception, e:
            # XXX could this exception handler be more specific? As written
            # any error in the proddef module will be masked.
            raise mint_error.ProductDefinitionVersionNotFound
        return pd

    def setProductVersionDefinition(self, fqdn, version, prodDef):
        cclient = self.reposMgr.getConaryClientForProduct(fqdn)
        prodDef.saveToRepository(cclient,
                'Product Definition commit from rBuilder\n')

    def rebaseProductVersionPlatform(self, fqdn, version, platformLabel):
        pd = self.getProductVersionDefinition(fqdn, version)
        cclient = self.reposMgr.getConaryClientForProduct(fqdn)
        pd.rebase(cclient, platformLabel)
        pd.saveToRepository(cclient, 
                'Product Definition commit from rBuilder\n')



    def setProductVersionBuildDefinitions(self, hostname, version, model):
        pd = self.getProductVersionDefinition(hostname, version)
        pd.clearBuildDefinition()
        for buildDef in model.buildDefinitions:
            self._addBuildDefinition(buildDef, pd)
        cclient = self.reposMgr.getConaryClientForProduct(hostname)
        pd.saveToRepository(cclient,
                            'Product Definition commit from rBuilder\n')
        return pd

    def _addBuildDefinition(self, buildDef, prodDef):
        if not buildDef.name:
            raise Exception
        if not buildDef.flavorSet or not buildDef.flavorSet.id:
            flavorSetRef = None
        else:
            flavorSetRef = os.path.basename(buildDef.flavorSet.id)

        if not buildDef.architecture or not buildDef.architecture.id:
            raise Exception
        architectureRef = os.path.basename(buildDef.architecture.id)

        if not buildDef.container or not buildDef.container.id:
            raise Exception
        containerRef = os.path.basename(buildDef.container.id)
        options = buildDef.container.options
        bdentry = (containerRef, architectureRef, flavorSetRef)
        # Find a matching build template
        for buildTempl in itertools.chain(prodDef.getBuildTemplates(),
                                          prodDef.platform.getBuildTemplates()):
            ent = (buildTempl.containerTemplateRef,
                buildTempl.architectureRef, buildTempl.flavorSetRef)
            if bdentry == ent:
                break
        else: # for
            # No build template found; chicken out
            raise Exception
        # For now, we don't allow the client to specify the stages
        stages = [ x.name for x in prodDef.getStages() ]
        imageFields = dict((x, getattr(options, x)) for x in options._fields)
        prodDef.addBuildDefinition(name = buildDef.name,
            containerTemplateRef = containerRef,
            architectureRef = architectureRef,
            flavorSetRef = flavorSetRef,
            image = prodDef.imageType(None, imageFields),
            stages = stages)


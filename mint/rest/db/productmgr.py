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

    def listProducts(self, start=0, limit=None, search=None, role=None):
        cu = self.db.cursor()

        query = '''
            SELECT p.projectId AS productId,
                p.hostname, p.name, p.shortname, p.domainname, p.namespace,
                p.description, creator.username AS creator, p.projectUrl,
                p.isAppliance, p.timeCreated, p.timeModified, p.commitEmail,
                p.prodtype, p.backupExternal, member.level AS role
            FROM Projects p
            LEFT JOIN ProjectUsers member ON (
                member.projectId = p.projectId
                AND member.userId = ? )
            LEFT JOIN Users creator ON ( p.creatorId = creator.userId )
            '''
        args = [self.auth.userId]
        clauses = []

        if role:
            clauses.append('member.level = ?')
            args.append(userlevels.idsByName[role.lower()])
        elif not self.auth.isAdmin:
            # Non-admins can't see hidden projects they aren't a member of
            clauses.append('( p.hidden = 0 OR member.level IS NOT NULL )')

        if search:
            search = search.replace('\\', '\\\\')
            search = search.replace('%','\\%')
            search = search.replace('_','\\_')
            clauses.append('p.shortname LIKE ?')
            args.append('%' + search + '%')

        if clauses:
            query += 'WHERE ' + (' AND '.join(clauses))
        query += ' ORDER BY p.shortname ASC'

        if limit:
            query += ' LIMIT %d' % limit
        if start:
            query += ' OFFSET %d' % start
        cu.execute(query, *args)

        results = models.ProductSearchResultList()
        for row in cu:
            d = dict(row)

            role = d.pop('role')
            if role is not None:
                d['role'] = userlevels.names[role]
            d['repositoryHostname'] = d['hostname'] + '.' + d['domainname']

            p = models.Product(**d)
            results.products.append(p)
        return results


    def getProductVersion(self, fqdn, versionName):
        # accept fqdn.
        hostname = fqdn.split('.')[0]
        cu = self.db.cursor()
        cu.execute('''SELECT productVersionId as versionId, 
                          PVTable.namespace, PVTable.name, PVTable.description,
                          PVTable.timeCreated, Projects.hostname
                      FROM Projects 
                      JOIN ProductVersions as PVTable USING (projectId)
                      WHERE Projects.hostname=? AND PVTable.name=?''', 
                      hostname, versionName)
        results = self.db._getOne(cu, errors.ProductVersionNotFound, 
                                  (hostname, versionName))
        return models.ProductVersion(**dict(results))

    def createProduct(self, name, description, hostname,
                      domainname, namespace, isAppliance,
                      projecturl, shortname, prodtype,
                      version, commitEmail, isPrivate):
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

        self.reposMgr.createRepository(projectId, hostname, domainname, 
                                       isPrivate=isPrivate)
        # can only add members after the repository is set up
        if self.auth.userId >= 0:
            self.setMemberLevel(projectId, self.auth.userId, userlevels.OWNER,
                                notify=False)
        self.publisher.notify('ProductCreated', projectId)
        return projectId

    def createExternalProduct(self, title, hostname, domainname, url,
                              authInfo, mirror=False, backupExternal=False):
        cu = self.db.cursor()
        createTime = time.time()
        cu.execute('''INSERT INTO Projects (name, creatorId, description,
                shortname, hostname, domainname, projecturl, external,
                timeModified, timeCreated, backupExternal)
                VALUES (?, ?, '', ?, ?, ?, '', 1, ?, ?, ?)''',
                title, self.auth.userId, hostname, hostname, domainname,
                createTime, createTime, int(backupExternal))
        productId = cu.lastrowid
        if mirror:
            self.reposMgr.addIncomingMirror(productId, hostname, domainname, 
                                            url, authInfo)
        else:
            self.reposMgr.addExternalRepository(productId, 
                                                hostname, domainname, url,
                                                authInfo)
        self.setMemberLevel(productId, self.auth.userId, userlevels.OWNER)
        self.publisher.notify('ExternalProductCreated', productId)
        return productId

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
            if not self.reposMgr._isProductExternal(fqdn):
                self.reposMgr.editUser(fqdn, username, write=write,
                                       mirror=mirror, admin=admin)
            if notify:
                self.publisher.notify('UserProductChanged', userId, projectId, 
                                      oldLevel, level)
            return False
        else:
            self.db.db.projectUsers.new(userId=userId, projectId=projectId,
                                        level=level, commit=False)
            if not self.reposMgr._isProductExternal(fqdn):
                password, salt = self.db.userMgr._getPassword(userId)
                self.reposMgr.addUserByMd5(fqdn, username, salt, password, 
                                           write=write, mirror=mirror, 
                                           admin=admin)
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
            versionId = self.db.db.productVersions.new(projectId=projectId,
                    namespace=namespace, name=version, description=description,
                    timeCreated=time.time())
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
            raise errors.InvalidItem("Build name missing")
        if not buildDef.flavorSet or not buildDef.flavorSet.id:
            flavorSetRef = None
        else:
            flavorSetRef = os.path.basename(buildDef.flavorSet.id)

        if not buildDef.architecture or not buildDef.architecture.id:
            raise errors.InvalidItem("Architecture missing")
        architectureRef = os.path.basename(buildDef.architecture.id)

        if not buildDef.container or not buildDef.container.id:
            raise errors.InvalidItem("Container missing")
        containerRef = os.path.basename(buildDef.container.id)
        options = buildDef.container.options
        bdentry = (containerRef, architectureRef, flavorSetRef)
        # Find a matching build template
        if prodDef.platform:
            templateIter = itertools.chain(prodDef.getBuildTemplates(),
                                           prodDef.platform.getBuildTemplates())
        else:
            # It is valid for the platform to be missing (although not
            # terribly useful)
            templateIter = prodDef.getBuildTemplates()
        for buildTempl in templateIter:
            ent = (buildTempl.containerTemplateRef,
                buildTempl.architectureRef, buildTempl.flavorSetRef)
            if bdentry == ent:
                break
        else: # for
            # No build template found; chicken out
            raise errors.InvalidItem("Invalid combination of container "
                "template, architecture and flavor set (%s, %s, %s)"
                    % bdentry)
        # For now, we don't allow the client to specify the stages
        stages = [ x.name for x in prodDef.getStages() ]
        imageFields = dict((x, getattr(options, x)) for x in options._fields)
        prodDef.addBuildDefinition(name = buildDef.name,
            containerTemplateRef = containerRef,
            architectureRef = architectureRef,
            flavorSetRef = flavorSetRef,
            image = prodDef.imageType(None, imageFields),
            stages = stages)

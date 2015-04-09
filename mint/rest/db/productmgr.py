#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import logging
import os
import itertools
import time

from conary.dbstore import sqlerrors
from conary.lib import util
from rpath_proddef import api1 as proddef

from mint import helperfuncs
from mint import mint_error
from mint import projects
from mint import userlevels
from mint import templates
from mint.rest import errors
from mint.rest.api import models
from mint.rest.db import manager
from mint.rest.db import reposmgr
from mint.rest.db import platformmgr
from mint.templates import groupTemplate

log = logging.getLogger(__name__)


class ProductManager(manager.Manager):
    def __init__(self, cfg, db, auth, publisher=None):
        manager.Manager.__init__(self, cfg, db, auth, publisher)
        self.reposMgr = reposmgr.RepositoryManager(cfg, db, auth)
        self.platformMgr = platformmgr.PlatformManager(cfg, db, auth)

    def _getProducts(self, whereClauses=(), limit=None, offset=0):
        whereClauses = list(whereClauses)
        sql = '''
            SELECT p.projectId AS productId, hostname, name, shortname,
                domainname, namespace, description, cr.username AS creator,
                projectUrl, p.timeCreated,
                p.timeModified, commitEmail, prodtype, backupExternal,
                hidden, m.level AS role, fqdn AS repositoryHostname
            FROM Projects p
            LEFT JOIN ProjectUsers m ON (
                p.projectId = m.projectId
                AND m.userId = ? )
            LEFT JOIN Users cr ON ( p.creatorId = cr.userId )
        '''
        args = [self.auth.userId]

        if not self.auth.isAdmin:
            # Private projects are invisible to non-member non-admins.
            whereClauses.append(
                    ('( NOT p.hidden OR m.level IS NOT NULL )', ()))

        if whereClauses:
            sql += ' WHERE ' + ' AND '.join(x[0] for x in whereClauses)
            args.extend(itertools.chain(*[x[1] for x in whereClauses]))
        sql += ' ORDER BY p.shortname ASC'
        if limit:
            sql += ' LIMIT %d' % (limit,)
            if offset:
                sql += ' OFFSET %d' % (offset,)

        cu = self.db.cursor()
        cu.execute(sql, *args)

        results = []
        for row in cu:
            role = row.pop('role')
            if role is None:
                # If we got access to this product, but have no specific
                # privileges, role is User
                role = userlevels.USER
            row['role'] = userlevels.names[role]
            row['name'] = cu.decode(row['name'])
            if row['description'] is not None:
                row['description'] = cu.decode(row['description'])

            results.append(models.Product(row))
        return results

    def getProduct(self, fqdn):
        hostname = fqdn.split('.')[0]
        results = self._getProducts([('hostname = ?', (hostname,))])
        if not results:
            raise errors.ProductNotFound(hostname)
        assert len(results) == 1  # guaranteed by unique constraint
        return results[0]

    def listProducts(self, start=0, limit=None, search=None, roles=None,
                     prodtype=None):
        clauses = []
        if roles is not None:
            # The User role is now granted to all viewers of public projects
            roles = set(userlevels.idsByName[x.lower()]
                for x in roles)
            withUser = userlevels.USER in roles
            roles = ', '.join('%d' % x for x in sorted(roles))
            if withUser:
                clauses.append(('(m.level IN ( %s ) OR m.level IS NULL)' % roles, ()))
            else:
                clauses.append(('m.level IN ( %s )' % roles, ()))

        if search:
            search = search.replace('\\', '\\\\')
            search = search.replace('%','\\%')
            search = search.replace('_','\\_')
            search = '%' + search + '%'
            clauses.append(('(UPPER(p.shortname) LIKE UPPER(?) OR UPPER(p.name) LIKE UPPER(?))', (search, search,)))

        if prodtype:
            if prodtype.lower() == 'appliance':
                # search for PlatformFoundation types also
                clauses.append(('(UPPER(p.prodtype) = UPPER(?) or UPPER(p.prodtype) = ?)', (prodtype, 'PLATFORMFOUNDATION' )))
            else:
                clauses.append(('(UPPER(p.prodtype) = UPPER(?))', (prodtype, )))

        ret = models.ProductSearchResultList()
        ret.products = self._getProducts(clauses, limit, start)
        return ret

    def getProductVersion(self, fqdn, versionName):
        productVersion = self._getMinimalProductVersion(fqdn, versionName)
        pd = self.getProductVersionDefinitionByProductVersion(productVersion.hostname, productVersion)
        # Use sourceGroup here since this is really the name of the source
        # trove that needs to be cooked.
        productVersion.sourceGroup = pd.getImageGroup()
        return productVersion

    def _getMinimalProductVersion(self, fqdn, versionName):
        # accept fqdn.
        hostname = fqdn.split('.')[0]
        cu = self.db.cursor()
        cu.execute('''SELECT productVersionId as versionId, 
                          PVTable.namespace, PVTable.name, PVTable.description,
                          PVTable.timeCreated, Projects.hostname, PVTable.label
                      FROM Projects 
                      JOIN ProductVersions as PVTable USING (projectId)
                      WHERE Projects.hostname=? AND PVTable.name=?''', 
                      hostname, versionName)
        row = self.db._getOne(cu, errors.ProductVersionNotFound, 
                                  (hostname, versionName))

        return models.ProductVersion(row)

    def createProduct(self, name, description, hostname,
                      domainname, namespace,
                      projecturl, shortname, prodtype,
                      version, commitEmail, isPrivate):
        if namespace is None:
            namespace = self.cfg.namespace
        else:
            v = helperfuncs.validateNamespace(namespace)
            if v != True:
                raise mint_error.InvalidNamespace
        createTime = time.time()
        if self.auth.userId > 0:
            creatorId = self.auth.userId
        else:
            creatorId = None

        try:
            projectId = self.db.db.projects.new(
                name=name,
                creatorId=creatorId,
                description=description, 
                hostname=hostname,
                domainname=domainname, 
                fqdn='%s.%s' % (hostname, domainname),
                database=self.cfg.defaultDatabase,
                namespace=namespace,
                isAppliance=(prodtype == 'Appliance' or prodtype == 'PlatformFoundation'),
                projecturl=projecturl,
                timeModified=createTime, 
                timeCreated=createTime,
                shortname=shortname, 
                prodtype=prodtype, 
                commitEmail=commitEmail, 
                hidden=bool(isPrivate),
                version=version,
                commit=False)
        except sqlerrors.CursorError, e:
            raise mint_error.InvalidError(e.msg)

        self.reposMgr.createRepository(projectId)

        # can only add members after the repository is set up
        if self.auth.userId >= 0:
            self.setMemberLevel(projectId, self.auth.userId, userlevels.OWNER,
                                notify=False)
        self.publisher.notify('ProductCreated', projectId)
        return projectId

    def updateProduct(self, hostname, name,
                       description, projecturl, commitEmail,
                       prodtype=None, hidden=True, namespace=None):
        oldproduct = self._getProducts([('hostname = ?', (hostname,))])[0]
        cu = self.db.cursor()
        params = dict(name=name,
                      description=description,
                      projecturl=projecturl,
                      commitEmail=commitEmail,
                      timeModified=time.time())
        if prodtype is not None:
            params['prodtype'] = prodtype
            params['isAppliance'] = (prodtype == 'Appliance' or prodtype == 'PlatformFoundation')
        if namespace is not None:
            v = helperfuncs.validateNamespace(namespace)
            if v != True:
                raise mint_error.InvalidNamespace
            params['namespace'] = namespace

        if hidden:
            # only admin can hide
            if self.auth.isAdmin:
                params['hidden'] = True
        else:
            params['hidden'] = False

        keys = '=?, '.join(params) + '=?'
        values = params.values()
        values.append(hostname)
        try:
            cu.execute('''UPDATE Projects SET %s
                      WHERE hostname=?''' % keys,
                   *values)
        except sqlerrors.CursorError, e:
            raise mint_error.InvalidError(e.msg)

        if bool(oldproduct.hidden) == True and hidden == False:
            self.publisher.notify('ProductUnhidden', oldproduct.id)

    def createExternalProduct(self, title, hostname, domainname, url,
                              authInfo, mirror=False, backupExternal=False):
        cu = self.db.cursor()
        createTime = time.time()
        creatorId = self.auth.userId > 0 and self.auth.userId or None

        fqdn = self.reposMgr._getFqdn(hostname, domainname)
        try:
            product = self.getProduct(hostname)
            productId = product.productId

            # Need to look in the labels table to see if there is a different
            # repository url there.
            labelIdMap, repoMap, userMap, entMap = \
                self.db.db.labels.getLabelsForProject(productId) 
            url = repoMap.get(fqdn, url)
        except errors.ItemNotFound:
            productId = None

        database = None
        if mirror:
            database = self.cfg.defaultDatabase

        if not productId:
            # Need a new entry in projects table.
            cu.execute('''INSERT INTO Projects (name, creatorId, description,
                    shortname, hostname, domainname, fqdn, projecturl, external,
                    timeModified, timeCreated, backupExternal, database)
                    VALUES (?, ?, '', ?, ?, ?, ?, '', ?, ?, ?, ?, ?)''',
                    title, creatorId, hostname, hostname, domainname,
                    fqdn, True,
                    createTime, createTime, bool(backupExternal), database)
            productId = cu.lastrowid

        if mirror:
            self.reposMgr.addIncomingMirror(productId, hostname, domainname, 
                                            url, authInfo, True)
        else:
            self.reposMgr.addExternalRepository(productId, 
                                                hostname, domainname, url,
                                                authInfo, mirror)
        if self.auth.userId > -1:
            self.setMemberLevel(productId, self.auth.userId, userlevels.OWNER)
        self.publisher.notify('ExternalProductCreated', productId)
        cu.execute("""UPDATE querysets_queryset SET tagged_date = NULL
            WHERE resource_type = 'project_branch_stage'
            OR resource_type = 'project'""")

        return productId

    def deleteExternalProduct(self, productId):
        cu = self.db.cursor()
        self.db.db.projects.delete(productId)
        return

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
        cu.execute('SELECT fqdn FROM Projects where projectId=?', projectId)
        return cu.next()[0]

    def setMemberLevel(self, projectId, userId, level, notify=True):
        fqdn = self._getProductFQDN(projectId)
        username = self.db.userMgr._getUsername(userId)
        isMember, oldLevel = self._getMemberLevel(projectId, userId)
        if isMember:
            if level == oldLevel:
                return
            cu = self.db.cursor()

            cu.execute("""UPDATE ProjectUsers SET level=? WHERE userId=? and
                projectId=?""", level, userId, projectId)
            if not self.reposMgr._isProductExternal(fqdn):
                self.reposMgr.editUser(fqdn, username, level)
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
                                           level)
            if notify:
                self.publisher.notify('UserProductAdded', userId,
                                      projectId, oldLevel, level)
            return True

    def deleteMember(self, projectId, userId, notify=True):
        fqdn = self._getProductFQDN(projectId)
        username = self.db.userMgr._getUsername(userId)
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
        prodDef = helperfuncs.sanitizeProductDefinition(product.name,
                        description, product.repositoryHostname,
                        product.shortname, version,
                        '', namespace)
        label = prodDef.getDefaultLabel()

        # validate the label, which will be added later.  This is done
        # here so the project is not created before this error occurs
        if projects.validLabel.match(label) == None:
            raise mint_error.InvalidLabel(label)

        if platformLabel:
            cclient = self.reposMgr.getUserClient()
            prodDef.rebase(cclient, platformLabel)
        self.setProductVersionDefinition(fqdn, version, prodDef)
        
        try:
            versionId = self.db.db.productVersions.new(projectId=projectId,
                    namespace=namespace, name=version, description=description,
                    label=prodDef.getProductDefinitionLabel(),
                    timeCreated=time.time())
        except mint_error.DuplicateItem:
            raise mint_error.DuplicateProductVersion

        if product.prodtype == 'Appliance' or product.prodtype == 'PlatformFoundation':
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
        cu.execute('''SELECT productVersionId, fqdn,
                             shortname, 
                             ProductVersions.namespace,    
                             ProductVersions.name 
                      FROM Projects 
                      JOIN ProductVersions USING(projectId)
                      WHERE hostname=?''', fqdn.split('.')[0])
        for versionId, fqdn, shortname, namespace, name in cu:
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
                cclient = self.reposMgr.getUserClient()
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
        productVersion = self._getMinimalProductVersion(fqdn, version)
        return self.getProductVersionDefinitionByProductVersion(fqdn, productVersion)

    def getProductVersionDefinitionByProductVersion(self, hostname, productVersion):
        product = self.getProduct(hostname)
        pd = proddef.ProductDefinition()
        if productVersion.label:
            pd.setBaseLabel(productVersion.label)
        else:
            pd.setProductShortname(product.shortname)
            pd.setConaryRepositoryHostname(product.getFQDN())
            pd.setConaryNamespace(productVersion.namespace)
            pd.setProductVersion(productVersion.name)
        cclient = self.reposMgr.getAdminClient(write=False)
        try:
            pd.loadFromRepository(cclient)
        except Exception, e:
            # XXX could this exception handler be more specific? As written
            # any error in the proddef module will be masked.
            raise mint_error.ProductDefinitionVersionNotFound
        return pd

    def setProductVersionDefinition(self, fqdn, version, prodDef):
        cclient = self.reposMgr.getUserClient()
        prodDef.saveToRepository(cclient,
                'Product Definition commit from rBuilder\n')

    def rebaseProductVersionPlatform(self, fqdn, version, platformVersion):
        pd = self.getProductVersionDefinition(fqdn, version)
        cclient = self.reposMgr.getUserClient()
        name = platformVersion.name
        label = platformVersion.label
        if str(label) == '':
            label = None
        # support rebase to latest if special string is sent
        # see RBL-8673
        kwargs = {}
        if name != "rebase-to-latest-on-versionless-platform":
            kwargs['platformVersion'] = platformVersion.revision
        pd.rebase(cclient, label, **kwargs)
        pd.saveToRepository(cclient, 
                'Product Definition commit from rBuilder\n')

    def setProductVersionBuildDefinitions(self, hostname, version, model):
        pd = self.getProductVersionDefinition(hostname, version)
        pd.clearBuildDefinition()
        for buildDef in model.buildDefinitions:
            self._addBuildDefinition(buildDef, pd)
        cclient = self.reposMgr.getUserClient()
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
        options = buildDef.options
        bdentry = (containerRef, architectureRef, flavorSetRef)
        # Find a matching build template
        if prodDef.platform:
            templateIter = itertools.chain(prodDef.getBuildTemplates(),
                                           prodDef.platform.getBuildTemplates())
        else:
            # It is valid for the platform to be missing (although not
            # terribly useful)
            templateIter = prodDef.getBuildTemplates()
        allowedCombinations = set(
            (bt.containerTemplateRef, bt.architectureRef, bt.flavorSetRef)
            for bt in templateIter)
        if bdentry not in allowedCombinations:
            # Hmm. OK, the old UI was manufacturing additional flavor sets,
            # let's try to ignore them
            nbdentry = (bdentry[0], bdentry[1], None)
            if nbdentry not in allowedCombinations:
                # No build template found; chicken out
                raise errors.InvalidItem("Invalid combination of container "
                    "template, architecture and flavor set (%s, %s, %s)"
                        % bdentry)
            # Use this build template instead
            flavorSetRef = None
        # For now, we don't allow the client to specify the stages
        stages = [ x.name for x in prodDef.getStages() ]
        imageFields = dict((x, getattr(options, x)) for x in options._fields)
        prodDef.addBuildDefinition(name = buildDef.name,
            containerTemplateRef = containerRef,
            architectureRef = architectureRef,
            flavorSetRef = flavorSetRef,
            image = prodDef.imageType(None, imageFields),
            stages = stages)

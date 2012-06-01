#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import os
import itertools
import time
import types

from conary import trove
from conary import versions
from conary.conaryclient import cmdline
from conary.deps import deps
from conary.dbstore import sqlerrors
from conary.lib import util
from rpath_proddef import api1 as proddef
from rpath_job import api1 as rpath_job

from mint import helperfuncs
from mint import jobstatus
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

class ProductVersionCallback(object):
    def __init__(self, hostname, version, job):
        self.hostname = hostname
        self.version = version
        self.job = job
        self.prefix = ''

    def _message(self, txt, usePrefix=True):
        if usePrefix:
            message = self.prefix + txt
        else:
            message = txt

        self.job.message = message

    def done(self):
        self.job.status = self.job.STATUS_COMPLETED

    def error(self, e):
        self.job.status = self.job.STATUS_FAILED
        self._message("Promote failed: %s" % e)

    def committingTransaction(self):
        self._message("Committing database transaction")

class ProductJobStore(rpath_job.JobStore):
    _storageSubdir = 'product-load-jobs'

class ProductManager(manager.Manager):
    def __init__(self, cfg, db, auth, publisher=None):
        manager.Manager.__init__(self, cfg, db, auth, publisher)
        self.reposMgr = reposmgr.RepositoryManager(cfg, db, auth)
        self.platformMgr = platformmgr.PlatformManager(cfg, db, auth)
        self.jobStore = ProductJobStore(
            os.path.join(self.cfg.dataPath, 'jobs'))

    def _getProducts(self, whereClauses=(), limit=None, offset=0):
        whereClauses = list(whereClauses)
        sql = '''
            SELECT p.projectId AS productId, hostname, name, shortname,
                domainname, namespace, description, cr.username AS creator,
                projectUrl, p.timeCreated,
                p.timeModified, commitEmail, prodtype, backupExternal,
                hidden, m.level AS role, fqdn AS repositoryHostname,
                ( SELECT pubReleaseId FROM PublishedReleases r
                    WHERE r.projectId = p.projectId
                    AND timePublished IS NOT NULL
                    ORDER BY timePublished DESC LIMIT 1
                ) AS latestRelease
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
                          PVTable.timeCreated, Projects.hostname
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

        authInfo = models.AuthInfo('userpass',
                self.cfg.authUser, self.cfg.authPass)
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
            self.reposMgr._generateConaryrcFile()

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
        self.setMemberLevel(productId, self.auth.userId, userlevels.OWNER)
        self.publisher.notify('ExternalProductCreated', productId)

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

        if level != userlevels.USER:
            self.db.db.membershipRequests.deleteRequest(projectId, userId,
                                                        commit=False)
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

    def updateProductVersionStage(self, hostname, version, stageName, trove):
        job = self.jobStore.create()

        promoteJob = models.GroupPromoteJob()
        promoteJob.jobId = job.id
        promoteJob.hostname = hostname
        promoteJob.version = version
        promoteJob.stage = stageName
        promoteJob.group = str(trove.name)

        client = self.reposMgr.getConaryClient()
        pd = self.getProductVersionDefinition(hostname, version)

        rpath_job.BackgroundRunner(self._promoteAndPublishPlatformDef) (
                client, pd, job, hostname, version, stageName, trove)

        return promoteJob

    def getGroupPromoteJobStatus(self, hostname, version, stage, jobId):
        job = self.jobStore.get(jobId)
        status = models.GroupPromoteJobStatus()
        message = job.message
        done = True and job.status == job.STATUS_COMPLETED or False
        error = True and job.status == job.STATUS_FAILED or False

        if bool(done):
            code = jobstatus.FINISHED
        elif bool(error):
            code = jobstatus.ERROR
        else:
            code = jobstatus.RUNNING

        status.set_status(code, message)
        return status

#---------------------CUT HERE WHEN THE REVOLUTION COMES-----------------------
    def getSourceGroupMatch(self, buildDefinition):
        """
        Find a source group defined on a different build definition that has a
        matching build flavor and image group as the given build definition.

        @param buildDefinition: build definition defining what flavor and
        image group to match.
        @type buildDefinition: L{proddef.Build}
        @rtype: string
        @return: source group name to build for this build definition. If none
        is found, return None.
        """
        # If there is no image group defined on buildDefinition, there's no
        # point in testing anything.
        if not buildDefinition.imageGroup:
            return None

        for bd in self._handle.product.getBuildDefinitions():
            # Test for flavor equality.
            if bd.getBuildBaseFlavor() == buildDefinition.getBuildBaseFlavor():

                # Test for image group equality.
                if bd.imageGroup and \
                   bd.imageGroup == buildDefinition.imageGroup:

                    # If defined, return the source group for this definition.
                    sourceGroup = bd.getBuildSourceGroup()
                    if sourceGroup:
                        return sourceGroup

        return None

    def getBuildDefinitionGroupToBuild(self, buildDefinition):
        """
        Find the source group to build for this build definition.
        @param buildDefinition: build definition defining the group to build.
        @type buildDefinition: L{proddef.Build}
        @rtype: string
        @return: Look for and return the first group that is found out of:
            - build definition source group
            - top level source group
            - build definition image group
            - top level image group
        """
        # getBuildSourceGroup takes care of looking at sourceGroup definied
        # on the build definition or at the top level.
        buildSourceGroup = buildDefinition.getBuildSourceGroup()

        if buildSourceGroup:
            return buildSourceGroup
        else:
            sourceGroupMatch = self.getSourceGroupMatch(buildDefinition)
            if sourceGroupMatch:
                return sourceGroupMatch

        # No sourceGroup defined anywhere that we can use, use an imageGroup.
        # getBuildImageGroup actually takes care of returning the top
        # level image group if there's not one set for the build
        # definition itself.
        return buildDefinition.getBuildImageGroup()

    @staticmethod
    def _getLabel(label):
        """
        Converts a label string into an B{opaque} Conary label object,
        or returns the B{opaque} label object.
        @param label: a representation of a conary label
        @type label: string or B{opaque} conary.versions.Label
        @return: B{opaque} Conary label object
        @rtype: conary.versions.Label
        """
        if isinstance(label, types.StringTypes):
            return versions.Label(str(label))
        return label

    @staticmethod
    def _getFlavor(flavor=None, keepNone=False):
        """
        Converts a version string into an B{opaque} Conary flavor object
        or returns the B{opaque} flavor object.
        @param flavor: conary flavor
        @type flavor: string or B{opaque} conary.deps.deps.Flavor
        @param keepNone: if True, leave None objects as None instead
        of converting to empty flavor
        @type keepNone: boolean
        @return: B{opaque} Conary flavor object
        @rtype: conary.deps.deps.Flavor
        """
        if flavor is None:
            if keepNone:
                return None
            else:
                return(deps.Flavor())
        if isinstance(flavor, types.StringTypes):
            return deps.parseFlavor(str(flavor), raiseError=True)
        return flavor

    def _overrideFlavors(self, baseFlavor, flavorList):
        baseFlavor = self._getFlavor(baseFlavor)
        return [ str(deps.overrideFlavor(baseFlavor, self._getFlavor(x)))
                 for x in flavorList ] 

    def getVersionGroupFlavors(self, pd, version):
        buildDefs = pd.getBuildDefinitions()
        groupFlavors = [ (str(self.getBuildDefinitionGroupToBuild(x)) +
                            "=%s" % str(version),
                          str(x.getBuildBaseFlavor()))
                         for x in buildDefs ]
        fullFlavors = self._overrideFlavors(str(pd.getBaseFlavor()),
                                             [x[1] for x in groupFlavors])
        return [(x[0][0], x[1]) for x in zip(groupFlavors, fullFlavors)]

    def _findTrovesFlattened(self, client, specList, labelPath=None,
                             defaultFlavor=None, allowMissing=False):
        results = self._findTroves(client, specList, labelPath=labelPath,
                                   defaultFlavor=defaultFlavor,
                                   allowMissing=allowMissing)
        return list(itertools.chain(*results.values()))

    def _findTroves(self, client, specList, labelPath=None,
                    defaultFlavor=None, allowMissing=False):
        newSpecList = []
        specMap = {}
        for spec in specList:
            if not isinstance(spec, tuple):
                newSpec = cmdline.parseTroveSpec(spec)
            else:
                newSpec = spec
            newSpecList.append(newSpec)
            specMap[newSpec] = spec
        repos = client.getRepos()
        if isinstance(labelPath, (tuple, list)):
            labelPath = [ self._getLabel(x) for x in labelPath ]
        elif labelPath:
            labelPath = self._getLabel(labelPath)

        defaultFlavor = self._getFlavor(defaultFlavor, keepNone=True)
        results = repos.findTroves(labelPath, newSpecList,
                                   defaultFlavor = defaultFlavor,
                                   allowMissing=allowMissing)
        return dict((specMap[x[0]], x[1]) for x in results.items())

    def _promoteAndPublishPlatformDef(self, client, pd, job, hostname, version, stageName, trv):
        callback = ProductVersionCallback(hostname, version, job)

        shouldPublish, targetLabels = self._promoteGroup(client, pd, job,
                hostname, version, stageName, trv, callback)

        # Republish platform definitions if this project is a platform and we
        # are promoting to the release stage.
        if shouldPublish and str(stageName) == 'Release':
            self._updatePlatformDefinition(targetLabels, callback)

        callback.done()

    def _promoteGroup(self, client, pd, job, hostname, version, stageName, trv,
        callback=None):

        nextStage = str(stageName)
        activeStage = None
        activeLabel = str(trv.label)

        if callback is None:
            callback = ProductVersionCallback(hostname, version, job)

        for stage in pd.getStages():
            if str(stage.name) == nextStage:
                break
            activeStage = stage.name

        callback._message('Getting all trove information for the promotion')

        # Collect a list of groups to promote.
        groupSpecs = [ '%s[%s]' % x for x in self.getVersionGroupFlavors(pd,
            trv.version) ]
        allTroves = self._findTrovesFlattened(client, groupSpecs, activeLabel)

        fromTo = pd.getPromoteMapsForStages(activeStage, nextStage)

        targetLabels = set()
        promoteMap = {}
        for (fromLabel, toLabel) in fromTo.iteritems():
            source = versions.Label(str(fromLabel))
            target = versions.VersionFromString(str(toLabel))
            promoteMap[source] = target

            targetLabels.add(target.label().asString())

        callback._message('Creating clone changeset')
        success, cs = client.createSiblingCloneChangeSet(promoteMap,
                        allTroves,cloneSources=True)

        if success:
            callback._message('Committing ChangeSet')
            client.getRepos().commitChangeSet(cs)
            callback._message('Committed')
        else:

            # Check to see if the trove that we are trying to promote is already
            # on the target label.
            targetSpecs = client.repos.findTroves(None,
                [(n, promoteMap.get(v.trailingLabel()), f)
                for n, v, f in allTroves ], getLeaves=False)

            reqSpecs = sorted([ x for x in
                itertools.chain(*targetSpecs.values()) ])

            ti = client.repos.getTroveInfo(trove._TROVEINFO_TAG_CLONEDFROM,
                reqSpecs)

            sourceVersions = [ (n, t(), f) for (n, v, f), t in
                itertools.izip(reqSpecs, ti) ]

            error = False
            for spec in allTroves:
                if spec not in sourceVersions:
                    error = True
                    break

            if error:
                callback.error('Changeset was not cloned')
                return False, None

            else:
                callback._message('This version has already been promoted')

        return True, targetLabels

    def _updatePlatformDefinition(self, labels, callback):
        self.db.db.reopen()
        cu = self.db.db.cursor()

        found = False
        for label in labels:
            cu.execute("SELECT platformId FROM Platforms WHERE label = ?",
                (label, ))
            row = cu.fetchone()
            if row:
                found = True
                break

        if not found:
            return

        callback._message('Publishing platform definition')

        # Update the platform definition
        pl = self.platformMgr._lookupFromRepository(label, True)

        if pl is not None:
            callback._message('Published')
        else:
            callback.error('Error publising platform definition')

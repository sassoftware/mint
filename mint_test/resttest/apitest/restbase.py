#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint import buildtypes
import testsetup

import base64
import os
import re
import subprocess
import tempfile
import time
from conary.dbstore.sqllib import CaselessDict
from conary import conaryclient

from restlib.http import handler
from restlib.http import request
from mint import helperfuncs
from mint import users
from mint.mint_error import UserAlreadyExists
from mint.rest.api import site
from mint.rest.db import platformmgr
from mint.rest.middleware import auth
from mint.rest.middleware import formatter
from mint.rest.modellib import converter
from rpath_proddef import api1 as proddef

from mint_test import mint_rephelp

from testutils import mock

URLQUOTE_RE = re.compile('%([A-Z0-9]{2})')

class BaseRestTest(mint_rephelp.MintDatabaseHelper):
    buildDefs = [
        ('Citrix XenServer 32-bit', 'xen', 'x86', 'xenOvaImage'),
        ('Citrix XenServer 64-bit', 'xen', 'x86_64', 'xenOvaImage'),
        ('VMware ESX 32-bit', 'vmware', 'x86', 'vmwareEsxImage'),
        ('VMware ESX 64-bit', 'vmware', 'x86_64', 'vmwareEsxImage'),
    ]
    buildTemplates = buildDefs
    architectures = []
    containerTemplates = []
    flavorSets = []
    productVersion = '1.0'
    productName = 'Project 1'
    productShortName = 'testproject'
    productVersionDescription = 'Version description'
    productDomainName = mint_rephelp.MINT_PROJECT_DOMAIN
    productHostname = "%s.%s" % (productShortName, productDomainName)

    availablePlatforms = [ 'localhost@rpath:plat-1', 'localhost@rpath:plat-2', ]

    def setUp(self):
        try:
            mint_rephelp.MintDatabaseHelper.setUp(self)
            self.mockProddef()
        except Exception, e:
            self.tearDown()
            raise e

    ControllerFactory = None

    def setupProduct(self):
        self.setUpProductDefinition()

        pd = self._setupProduct()
        # used by other tests before setupProduct was fixturized.
        self.productDefinition = pd

    @mint_rephelp.restFixturize('apitest.setupProduct')
    def _setupProduct(self):
        version = self.productVersion
        projectName = self.productName
        shortName = self.productShortName
        domainName = self.productDomainName
        description = self.productVersionDescription
        db = self.openRestDatabase()
        self.createUser('adminuser', admin=True)
        self.setDbUser(db, 'adminuser')
        self.createProduct(shortName,
                           name=projectName,
                           domainname=domainName, db=db)
        self.createProductVersion(db, shortName,
                                  version,
                                  description=description,
                                  namespace=self.mintCfg.namespace)
        pd = helperfuncs.sanitizeProductDefinition(
            projectName, '', '.'.join((shortName, domainName)),
            shortName, version, '', self.mintCfg.namespace)
        stageRefs = [ x.name for x in pd.getStages() ]
        for _name, displayName, _flavor in self.architectures:
            pd.addArchitecture(_name, displayName, _flavor)
        for _name, displayName, _flavor in self.flavorSets:
            pd.addFlavorSet(_name, displayName, _flavor)
        for _name, opts in self.containerTemplates:
            pd.addContainerTemplate(pd.imageType(_name, opts))
        for buildName, flavorSetRef, archRef, containerTemplateRef in \
                    self.buildTemplates:
            pd.addBuildTemplate(name = buildName,
                displayName = buildName,
                flavorSetRef = flavorSetRef,
                architectureRef = archRef,
                containerTemplateRef = containerTemplateRef)
        for buildName, flavorSetRef, archRef, containerTemplateRef in \
                    self.buildDefs:
            pd.addBuildDefinition(name = buildName,
                flavorSetRef = flavorSetRef,
                architectureRef = archRef,
                containerTemplateRef = containerTemplateRef,
                stages = stageRefs)
        client = db.productMgr.reposMgr.getConaryClientForProduct(shortName)
        pd.setPlatformName('localhost@rpath:plat-1')
        pd.saveToRepository(client, 'Product Definition commit\n')
        return pd

    @mint_rephelp.restFixturize('apitest.setupReleases')
    def setupReleases(self):
        self.setupProduct()
        # Add a group
        label = self.productDefinition.getDefaultLabel()
        db = self.openRestDatabase()
        self.setDbUser(db, 'adminuser')
        client = db.productMgr.reposMgr.getConaryClientForProduct(self.productShortName)
        repos = client.getRepos()
        self.addComponent("foo:bin=%s" % label, repos=repos)
        self.addCollection("foo=%s" % label, ['foo:bin'], repos=repos)
        groupTrv = self.addCollection("group-foo=%s" % label, ['foo'],
                                      repos=repos)

        # Let's add some images
        images = [
            ('Image 1', buildtypes.INSTALLABLE_ISO),
            ('Image 2', buildtypes.TARBALL),
        ]
        groupName = groupTrv.getName()
        groupVer = groupTrv.getVersion().freeze()
        groupFlv = str(groupTrv.getFlavor())
        imageIds = []
        for imageName, imageType in images:
            imageId = self.createImage(db, self.productShortName,
                imageType, name = imageName,
                description = "Description for %s" % imageName,
                troveName = groupName,
                troveVersion = groupVer,
                troveFlavor = groupFlv)
            self.setImageFiles(db, self.productShortName, imageId)
            imageIds.append(imageId)

        # make sure the times are different fo
        imageId3 = self.createImage(db, self.productShortName,
                                   buildtypes.TARBALL,
                                   name = 'Image 3')
        self.setImageFiles(db, self.productShortName, imageId3)

        releaseId = db.createRelease(self.productShortName, 'Release Name', '',
                'v1', imageIds)
        releaseId2 = db.createRelease(self.productShortName, 'Release Name', '',
                'v1', [imageId3])
        db.publishRelease(self.productShortName, releaseId2, True)

    def mockProddef(self):
        oldLoadFromRepository = proddef.PlatformDefinition.loadFromRepository
        def newLoadFromRepository(slf, *args, **kw):
            oldClient = args[0]
            label = args[1]
            if label.startswith('localhost@'):
                return oldLoadFromRepository(slf, self.cclient, label)
            return oldLoadFromRepository(slf, oldClient, label)

        self.mock(proddef.PlatformDefinition, 'loadFromRepository',
            newLoadFromRepository)

    def _addPlatform(self, label, platformDef):
        restdb = self.openRestDatabase()
        platformName = platformDef.getPlatformName()
        plat = restdb.platformMgr.platforms._platformModelFactory(
            platformName=platformName,
            label=label, configurable=True, enabled=True)
        restdb.platformMgr.platforms._create(plat, platformDef)
        restdb.commit()

    def setupPlatforms(self):
        mock.mock(platformmgr.Platforms, '_checkMirrorPermissions',
                        True)
        repos = self.openRepository()
        self.cclient = self.getConaryClient()
        self.cclient.repos = repos
        platformLabel1 = self.availablePlatforms[0]
        pl1 = self.productDefinition.toPlatformDefinition()
        cst = pl1.newContentSourceType('RHN', 'RHN', isSingleton = True)
        cst2 = pl1.newContentSourceType('satellite', 'satellite')
        ds = pl1.newDataSource('Channel 1', 'Channel 1')
        pl1.setContentProvider('Crowbar', 'Crowbar', [cst, cst2], [ds])
        pl1.setPlatformName('Crowbar Linux 1')
        pl1.setPlatformUsageTerms('Terms of Use 1')
        pl1.addArchitecture('x86', 'x86', 'is:x86 x86(~i486, ~i586, ~i686, ~cmov, ~mmx, ~sse, ~sse2)')
        pl1.addArchitecture('x86_64', 'x86 (64-bit)', 'is:x86_64 x86(~i486, ~i586, ~i686, ~cmov, ~mmx, ~sse, ~sse2)')
        pl1.addFlavorSet('xen', 'Xen DomU', '~xen, ~domU, ~!dom0, ~!vmware')
        pl1.addFlavorSet('vmware','VMware','~vmware, ~!xen, !domU, ~!dom0')
        pl1.addContainerTemplate(pl1.imageType('vmwareEsxImage', {'autoResolve':'false', 'natNetworking':'true', 'baseFileName':'', 'vmSnapshots':'false', 'swapSize':'512', 'vmMemory':'256', 'installLabelPath':'', 'freespace':'1024'}))
        pl1.addContainerTemplate(pl1.imageType('xenOvaImage', {'autoResolve':'false', 'baseFileName':'', 'swapSize':'512', 'vmMemory':'256', 'installLabelPath':'', 'freespace':'1024'}))
        pl1.saveToRepository(self.cclient, platformLabel1)
        self._addPlatform(platformLabel1, pl1)

        platformLabel2 = self.availablePlatforms[1]
        pl2 = self.productDefinition.toPlatformDefinition()
        cst = pl1.newContentSourceType('RHN', 'RHN')
        ds = pl1.newDataSource('Channel 1', 'Channel 1')
        pl1.setContentProvider('Crowbar', 'Crowbar', [cst], [ds])
        pl2.setPlatformName('Crowbar Linux 2')
        pl2.setPlatformUsageTerms('Terms of Use 2')
        sp = pl2.getSearchPaths()[0]
        sp.set_isPlatformTrove(True)
        pl2.saveToRepository(self.cclient, platformLabel2)
        self._addPlatform(platformLabel2, pl2)

    def setupPlatform3(self, repositoryOnly=False):
        repos = self.openRepository()
        self.cclient = self.getConaryClient()
        self.cclient.repos = repos
        # platformLabel1 = self.mintCfg.availablePlatforms[0]
        platformLabel1 = 'localhost@rpath:plat-3'
        pl1 = self.productDefinition.toPlatformDefinition()
        cst = pl1.newContentSourceType('RHN', 'RHN', isSingleton = True)
        ds = pl1.newDataSource('Channel 1', 'Channel 1')
        pl1.setContentProvider('Crowbar', 'Crowbar', [cst], [ds])
        pl1.setPlatformName('Crowbar Linux 3')
        pl1.setPlatformUsageTerms('Terms of Use 1')
        pl1.addArchitecture('x86', 'x86', 'is:x86 x86(~i486, ~i586, ~i686, ~cmov, ~mmx, ~sse, ~sse2)')
        pl1.addFlavorSet('xen', 'Xen DomU', '~xen, ~domU, ~!dom0, ~!vmware')
        pl1.saveToRepository(self.cclient, platformLabel1)
        if not repositoryOnly:
            self._addPlatform(platformLabel1, pl1)
        return pl1

    def getConaryClient(self):
        return conaryclient.ConaryClient(self.cfg)

    def getRestClient(self, **kw):
        if 'db' in kw:
            db = kw.pop('db')
        else:
            subscribers = kw.pop('subscribers', None)
            db = self.openRestDatabase(subscribers = subscribers)

        admin = kw.pop('admin', None)
        if 'username' not in kw:
            if admin:
                kw['username'] = 'adminuser'
            else:
                kw['username'] = 'someuser'
        if 'password' not in kw:
            kw['password'] = kw['username']
            if kw['username']:
                try:
                    self.createUser(kw['username'], kw['password'], admin=admin)
                except UserAlreadyExists:
                    pass

        return self.ControllerFactory(self.mintCfg, db, **kw)

    def escapeURLQuotes(self, foo):
        """
        Escape URL quotes (%FF sequences) with an extra %
        so they can be used with the % operator.
        """
        return URLQUOTE_RE.sub('%%\\1', foo)

    def getTestProjectRepos(self):
        db = self.openMintDatabase()
        reposMgr = db.productMgr.reposMgr
        return reposMgr.getRepositoryClientForProduct('testproject')

    def assertBlobEquals(self, actual, expected):
        """
        Like assertEquals but prints a diff.
        """
        if actual != expected:
            if actual and expected:
                actualF = tempfile.NamedTemporaryFile(prefix='actual-')
                actualF.write(actual)
                actualF.flush()

                expectedF = tempfile.NamedTemporaryFile(prefix='expected-')
                expectedF.write(expected)
                expectedF.flush()

                proc = subprocess.Popen(['/usr/bin/diff', '-u',
                    expectedF.name, actualF.name],
                    shell=False, stdout=subprocess.PIPE)
                diff, _ = proc.communicate()

                raise self.failureException("Results do not match.\nDiff:\n%s"
                        % (diff,))
            elif actual:
                raise self.failureException("Expected no output, actual "
                        "result is:\n%s" % (actual,))
            else:
                raise self.failureException("Got no output, expected "
                        "result is:\n%s" % (expected,))


class Controller(object):
    RequestFactory = None
    HandlerFactory = None
    FormatCallbackFactory = None
    def __init__(self, cfg, restDb, username, password):
        self.server = 'localhost'
        self.port = '8000'
        self.controller = site.RbuilderRestServer(cfg, restDb)
        self.handler = self.HandlerFactory(self.controller)
        self.handler.addCallback(auth.AuthenticationCallback(cfg, restDb,
            self.controller))
        self.handler.addCallback(self.FormatCallbackFactory(self.controller))
        self.restDb = restDb
        self.username = username
        self.password = password

    def call(self, method, uri, body=None, convert=False, headers=None):
        request = self.RequestFactory(method, uri, body=body)
        request._convert = convert

        if self.username:
            request.headers['Authorization'] = 'Basic ' + base64.b64encode(
                    self.username + ':' + self.password)

        if headers:
            request.headers.update(headers)
        response = self.handler.handle(request)
        if convert:
            response = response.content
        return request, response

    def convert(self, type, request, object):
        return converter.toText(type, object, self.controller, request)

class MockRequest(request.Request):
    def __init__(self, method, uri, username=None, admin=False,
                 body=None):
        self.method = method
        self.uri = uri
        self.extension = None
        self.body = body
        request.Request.__init__(self, None, '/api')

    def _setProperties(self):
        self.headers = CaselessDict()
        # self.method is set in __init__
        self.remote = (None, None)

    def _getRawPath(self):
        return 'http://localhost:8000', ('/api/' + self.uri)

    def _getHeaders(self):
        return {}

    def read(self):
        return self.body

    def _getPostData(self):
        return {}

    def _getRemote(self):
        return (None, None)

    def getContentLength(self):
        return self.body and len(self.body) or 0


class MockHandler(handler.HttpHandler):
    def handle(self, request, pathPrefix=''):
        return self.getResponse(request)

    class exceptionCallback(object):
        def processException(self, request, excClass, exception, tb):
            raise excClass, exception, tb


class MockFormatCallback(formatter.FormatCallback):
    def processResponse(self, request, res):
        if request._convert:
            return formatter.FormatCallback.processResponse(self, request, res)
        else:
            return res

# Set defaults
# We do this here because I did not want to move classes around
BaseRestTest.ControllerFactory = Controller
Controller.FormatCallbackFactory = MockFormatCallback
Controller.HandlerFactory = MockHandler
Controller.RequestFactory = MockRequest

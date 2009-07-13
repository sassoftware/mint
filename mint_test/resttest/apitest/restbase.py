#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint import buildtypes
import testsetup

import os
import re
import subprocess
import tempfile
import time

from restlib.http import request
from mint import helperfuncs
from mint import users
from mint.rest.api import site
from mint.rest.modellib import converter

import mint_rephelp

URLQUOTE_RE = re.compile('%([A-Z0-9]{2})')

class BaseRestTest(mint_rephelp.MintDatabaseHelper):
    buildDefs = [
        ('Citrix XenServer 32-bit', 'xen', 'x86', 'xenOvaImage'),
        ('Citrix XenServer 64-bit', 'xen', 'x86_64', 'xenOvaImage'),
        ('VMware ESX 32-bit', 'vmware', 'x86', 'vmwareEsxImage'),
        ('VMware ESX 64-bit', 'vmware', 'x86_64', 'vmwareEsxImage'),
    ]
    productVersion = '1.0'
    productName = 'Project 1'
    productShortName = 'testproject'
    productVersionDescription = 'Version description'
    productDomainName = mint_rephelp.MINT_PROJECT_DOMAIN
    productHostname = "%s.%s" % (productShortName, productDomainName)

    def setupProduct(self):
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
            projectName, '', shortName, domainName,
            shortName, version, '', self.mintCfg.namespace)
        stageRefs = [ x.name for x in pd.getStages() ]
        for buildName, flavorSetRef, archRef, containerTemplateRef in \
                    self.buildDefs:
            pd.addBuildDefinition(name = buildName,
                flavorSetRef = flavorSetRef,
                architectureRef = archRef,
                containerTemplateRef = containerTemplateRef,
                stages = stageRefs)
        client = db.productMgr.reposMgr.getConaryClientForProduct(shortName)
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


    def getRestClient(self, **kw):
        if 'db' in kw:
            db = kw.pop('db')
        else:
            subscribers = kw.pop('subscribers', None)
            db = self.openRestDatabase(subscribers = subscribers)
        return Controller(self.mintCfg, db, **kw)

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
    def __init__(self, cfg, restDb, username=None, admin=False):
        self.server = 'localhost'
        self.port = '8000'
        self.controller = site.RbuilderRestServer(cfg, restDb)
        self.restDb = restDb
        if username:
            cu = self.restDb.cursor()
            cu.execute("select userId from Users where username=?", username)
            userId = cu.fetchone()
            if userId:
                userId = userId[0]
            else:
                userId = 1
            self.auth = users.Authorization(authorized=True, admin=admin,
                                            userId=userId,
                                            username=username)
        else:
            self.auth = users.Authorization(authoried=False, admin=False,
                                           userId=-1)


    def call(self, method, uri, body=None, convert=False):
        request = MockRequest(method, uri, body=body)
        request.rootController = self.controller
        if self.auth.authorized:
            request.mintAuth = self.auth
        else:
            request.mintAuth = None
        request.auth = (self.auth.username, self.auth.username)
        fn, remainder, args, kw = self.controller.getView(method,
                                                request.unparsedPath)
        request.unparsedPath = remainder
        self.restDb.setAuth(self.auth, request.auth)
        if hasattr(fn, 'model'):
            modelName, model = fn.model
            kw[modelName] = converter.fromText('xml',
                                               body,
                                               model, self.controller, request)
        response = fn(request, *args, **kw)
        if convert:
            response = converter.toText('xml', response, self.controller,
                                        request)
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
        self.headers = {}
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

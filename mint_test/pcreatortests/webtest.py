#!/usr/bin/python
#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#

import sys
from mint_test import testsetup
from mint_test import mint_rephelp
from mint_test import webprojecttest
from mint_test.mint_rephelp import FQDN
from pcreator import factorydata

from conary.lib import util
from testrunner import pathManager
from testutils import mock

from factory_test.factorydatatest import basicXmlDef

import re, os, StringIO
import json

import mint.mint_error
import mint.web.webhandler
from types import MethodType

from rpath_proddef import api1 as proddef

from mint_test.pcreatortests.packagecreatoruitest import getPackageCreatorFactoriesData1


class TestPackageCreatorUIWeb(webprojecttest.WebProjectBaseTest):
    """ Unit tests for the web ui pieces of the Package Creator """

    def setUp(self):
        webprojecttest.WebProjectBaseTest.setUp(self)
        self.setUpProductDefinition()

    def testPackageCreatorUI(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                mint_rephelp.MINT_PROJECT_DOMAIN)
        self.webLogin('testuser', 'testpass')
        page = self.fetch('/project/testproject/newPackage',
                server=self.getProjectServerHostname())
        self.assertEquals(page.code, 302, "This call should redirect since there are no versions setup")
        client.addProductVersion(projectId, self.mintCfg.namespace, "version1", "Fluff description")

        #Without the current version set, it should redirect
        page = self.fetch('/project/testproject/newPackage',
                server=self.getProjectServerHostname())
        self.assertEquals(page.code, 302, "This call should redirect since there is no current version set")

        #set the current version
        page = self.fetch('/project/testproject/setProductVersion?versionId=1&redirect_to=/foo',
                server=self.getProjectServerHostname())
        page = self.fetch('/project/testproject/newPackage',
                server=self.getProjectServerHostname())
        assert 'version1' in page.body
        assert 'VALUE="Upload"' in page.body
        match = re.search('upload_iframe\?uploadId=([^;]+);', page.body)
        assert match, "Did not find an id in the page body"
        sessionHandle = match.groups()[0]
        assert sessionHandle, "expected sessionHandle"
        #Make sure it actually did what we asked
        #Get the tempPath
        tmppath = os.path.join(self.mintCfg.dataPath, 'tmp', 'rb-pc-upload-%s' % sessionHandle)

        #set the current version to the other
        client.addProductVersion(projectId, self.mintCfg.namespace+'tag', "version2", "Fluff description")
        page = self.fetch('/project/testproject/setProductVersion?versionId=2&redirect_to=/foo',
                server=self.getProjectServerHostname())
        page = self.fetch('/project/testproject/newPackage',
                server=self.getProjectServerHostname())
        assert 'version2' in page.body
        assert self.mintCfg.namespace+'tag' in page.body

        assert os.path.isdir(tmppath)

    def testPackageCreatorIframe(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                mint_rephelp.MINT_PROJECT_DOMAIN)
        self.webLogin('testuser', 'testpass')
        page = self.fetch('/project/testproject/upload_iframe?uploadId=foobarbaz;fieldname=upldfile',
                server=self.getProjectServerHostname())
        assert 'ACTION="/cgi-bin/fileupload.cgi?uploadId=foobarbaz;fieldname=upldfile"' in page.body
        assert not 'INPUT TYPE="submit"' in page.body.lower(), "Did you forget to remove the submit button?"
        assert 'INPUT TYPE="file" NAME="uploadfile"' in page.body, 'The file field name is fixed'
        assert 'NAME="project" VALUE="testproject"' in page.body, 'Make sure the project name is in the form'

    def extractElement(self, page, elemType, attributeName, attributeValue):
        match = re.search("<%(elemType)s[^>]*%(attributeName)s=['|\"]%(attributeValue)s['|\"][^>]*>" % dict(elemType=elemType, attributeName=attributeName, attributeValue=attributeValue), page)
        if match:
            return match.group()
        else:
            return match

    def _setupProjectHandlerMockClientMethod(self, methodName, mockMethod, requestName):
        ### All this, just to monkeypatch the client
        projectHandler = self._setupProjectHandler()
        projectHandler.req = mint_rephelp.FakeRequest(FQDN, 'POST', requestName)
        auth = projectHandler.client.checkAuth()
        projectHandler.projectList = projectHandler.client.getProjectsByMember(auth.userId)
        projectHandler.projectDict = {}
        self.mock(projectHandler.client, methodName, MethodType(mockMethod, projectHandler.client))

        return projectHandler, auth

    def _setupSiteHandlerMockClientMethod(self, methodName, mockMethod, requestName):
        ### All this, just to monkeypatch the client
        siteHandler, auth = self._setupSiteHandler()
        siteHandler.req = mint_rephelp.FakeRequest(self.getServerHostname(), 'POST', requestName)
        siteHandler.siteDict = {}
        self.mock(siteHandler.client, methodName, MethodType(mockMethod, siteHandler.client))

        return siteHandler, auth

    def _setupInterviewEnvironment(self, mockMethod):
        fields = {
            'uploadDirectoryHandle': 'foobarbaz',
        }
        cmd = 'testproject/getPackageFactories'

        projectHandler,auth = self._setupProjectHandlerMockClientMethod(
                            'getPackageFactories', mockMethod, cmd)
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}

        func = projectHandler.handle(context)
        self._setModeForSession('package-creator')
        return func, context

    def testErrorRetrievingFactoriesInterviewTemplate(self):
        ret = []
        def fakepackagefactories(s, *args):
            raise mint.mint_error.PackageCreatorError("No idea why this happened")
        func,context = self._setupInterviewEnvironment(fakepackagefactories)
        self.assertRaises(mint.web.webhandler.HttpMovedTemporarily, func, auth=context['auth'], **context['fields'])

    def testMultipleFactoriesInterviewTemplate(self):
        self.factorystream = StringIO.StringIO(basicXmlDef)
        def fakepackagefactories(s, *args):
            ret = []
            ret.append(('rpm1', factorydata.FactoryDefinition(fromStream=self.factorystream), {'a': 'b'}),)
            self.factorystream.seek(0)
            ret.append(('rpm2', factorydata.FactoryDefinition(fromStream=self.factorystream), {'a': 'b'}),)
            return 'foobarbaz', ret, {}

        func,context = self._setupInterviewEnvironment(fakepackagefactories)
        page = func(auth=context['auth'], **context['fields'])
        self.failUnless('form action="savePackage"' in page)
        ## Look for the select box
        elem = self.extractElement(page, 'select', 'name', 'factoryHandle')
        self.failUnless(elem)
        self.failUnless('id="factoryHandle"' in elem)
        self.failUnless('onchange="javascript:changeFactory()"' in elem)
        self.failUnless('<option value="rpm1">foo</option>' in page)
        self.failUnless('<option value="rpm2">foo</option>' in page)
        match = re.search('input type="text" id="0_intField_id" value="0" name="intField"', page)
        self.failUnless(match, 'expected 0_intField was not found in the page')
        match = re.search('input type="text" id="1_intField_id" value="0" name="intField"', page)
        self.failUnless(match, 'expected 1_intField was not found in the page')


    def testPackageCreatorInterviewTemplate(self):
        # This method only tests that the page was rendered as expected with
        # the proper UI elements
        self.factorystream = open(
                 os.path.join(pathManager.getPath('PACKAGE_CREATOR_SERVICE_FACTORY_PATH'),
                              'factory-stub', 'data-definition.xml'))
        self.prefilled={'version': '0.1999', 'license': 'GPL', 'multiple_license': 'GPL', 'description': 'line1\nline2'}
        def fakepackagefactories(s, *args):
            self.factorystream.seek(0)
            return 'foobarbaz', [('stub', factorydata.FactoryDefinition(fromStream=self.factorystream), self.prefilled)], {}

        func,context = self._setupInterviewEnvironment(fakepackagefactories)

        #The rest of the tests can be done with the stub factory
        page = func(auth=context['auth'], **context['fields'])

        #The name element for the stub is blank
        elem = self.extractElement(page, 'input', 'name', 'name')
        self.failUnless(('value=""' in elem) or ("value=" not in elem), "No value should be set")
        #Should not also have a textarea
        elem = self.extractElement(page, 'textarea', 'name', 'name')
        self.failIf(elem)

        #The version element has no default, but has a prefilled value
        elem = self.extractElement(page, 'input', 'name', 'version')
        self.failUnless(('value="0.1999"' in elem), "No value was set")
        #Should not also have a textarea
        elem = self.extractElement(page, 'textarea', 'name', 'version')
        self.failIf(elem)

        #The description element should be shown as a text area
        elem = self.extractElement(page, 'input', 'name', 'description')
        self.failIf(elem)
        #Should not also have a textarea
        elem = self.extractElement(page, 'textarea', 'name', 'description')
        self.failUnless(elem)
        self.failUnless(self.prefilled['description'] in page)

        # Tests for small single select (radio)
        elem = self.extractElement(page, 'input', 'id', '0_license_id_BSD')
        self.failIf('checked' in elem)
        elem = self.extractElement(page, 'input', 'id', '0_license_id_GPL')
        self.failUnless('checked' in elem)
        elem = self.extractElement(page, 'input', 'id', '0_license_id_GPL V3')
        self.failIf('checked' in elem)

        #Tests for multiple select (checkbox)
        elem = self.extractElement(page, 'input', 'id', '0_multiple_license_id_BSD')
        self.failIf('checked' in elem)
        elem = self.extractElement(page, 'input', 'id', '0_multiple_license_id_GPL')
        self.failUnless('checked' in elem)
        elem = self.extractElement(page, 'input', 'id', '0_multiple_license_id_GPL V3')
        self.failIf('checked' in elem)

        #Now a select box with default
        elem = self.extractElement(page, 'select', 'name', 'integer_value_with_default')
        self.failUnless(elem)
        self.failIf('multiple=' in elem)
        elem = self.extractElement(page, 'option', 'id', '0_integer_value_with_default_id_3')
        self.failUnless(elem)
        self.failIf('selected' in elem)
        elem = self.extractElement(page, 'option', 'id', '0_integer_value_with_default_id_9')
        self.failUnless(elem)
        self.failUnless('selected' in elem)
        #Check for the constraint description
        self.failUnless('pick a number between 1 and 10' in page)
        #Check that the label is not marked as required
        elem = self.extractElement(page, 'label', 'id', '0_integer_value_with_default_id_label')
        self.failIf('class="required"' in elem)

        #Now a select box with multiple
        elem = self.extractElement(page, 'select', 'name', 'integer_value_with_multiple')
        self.failUnless(elem)
        self.failUnless('multiple=' in elem)
        elem = self.extractElement(page, 'option', 'id', '0_integer_value_with_multiple_id_3')
        self.failUnless(elem)
        self.failIf('selected' in elem)

        # Very large integer range
        elem = self.extractElement(page, 'input', 'name', 'very_large_integer_range')
        self.failUnless(elem)

        #Boolean
        elem = self.extractElement(page, 'input', 'id', '0_boolean_value_id_True')
        self.failUnless(elem)
        self.failIf('checked' in elem)
        elem = self.extractElement(page, 'input', 'id', '0_boolean_value_id_False')
        self.failUnless(elem)
        self.failIf('checked' in elem)
        #This element should be required
        elem = self.extractElement(page, 'label', 'id', '0_boolean_value_id_label')
        self.failUnless('class="required"' in elem)

        self.prefilled['boolean_value'] = 'TrUe'
        page = func(auth=context['auth'], **context['fields'])
        elem = self.extractElement(page, 'input', 'id', '0_boolean_value_id_True')
        self.failUnless(elem)
        self.failUnless('checked="checked"' in elem)
        elem = self.extractElement(page, 'input', 'id', '0_boolean_value_id_False')
        self.failUnless(elem)
        self.failIf('checked' in elem)

        #Large descriptions
        self.prefilled['description'] = 'a' * 49
        page = func(auth=context['auth'], **context['fields'])
        #The description of 49 characters should be a text area
        elem = self.extractElement(page, 'textarea', 'name', 'description')
        self.failIf(elem)
        #Should not also have an input
        elem = self.extractElement(page, 'input', 'name', 'description')
        self.failUnless(elem)
        self.failUnless(self.prefilled['description'] in page)

        self.prefilled['description'] = 'a' * 50
        page = func(auth=context['auth'], **context['fields'])
        elem = self.extractElement(page, 'input', 'name', 'description')
        self.failIf(elem)
        elem = self.extractElement(page, 'textarea', 'name', 'description')
        self.failUnless(elem)
        self.failUnless(self.prefilled['description'] in page)


    def _setModeForSession(self, modeName, sessionUser='testuser', sessionHandle='foobarbaz'):
        dataPath = os.path.join(self.mintCfg.dataPath, 'tmp', sessionUser, sessionHandle)
        util.mkdirChain(dataPath)
        modePath = os.path.join(dataPath, 'mode')
        f = open(modePath, 'w')
        f.write(json.dumps(modeName))
        f.close()

    def _setupMaintainInterviewEnvironment(self, mockMethod):
        fields = {
            'name': 'grnotify',
            'label': 'foo.local.test@foo:bar',
            'prodVer': 'v1',
            'namespace': 'ns1',
        }
        cmd = 'testproject/maintainPackageInterview'

        projectHandler,auth = self._setupProjectHandlerMockClientMethod(
                            'getPackageFactoriesFromRepoArchive', mockMethod, cmd)
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}

        func = projectHandler.handle(context)
        self._setModeForSession('package-creator')
        return func, context

    def testMaintainPackageInterview(self):
        self.factorystream = StringIO.StringIO(basicXmlDef)
        def fakePackageFactories(s, *args):
            ret = []
            ret.append(('rpm1', factorydata.FactoryDefinition(fromStream=self.factorystream), {'a': 'b'}),)
            self.factorystream.seek(0)
            ret.append(('rpm2', factorydata.FactoryDefinition(fromStream=self.factorystream), {'a': 'b'}),)
            return 'foobarbaz', ret, {}

        func, context = self._setupMaintainInterviewEnvironment(fakePackageFactories)

        page = func(auth=context['auth'], **context['fields'])
        self.failUnless('form action="savePackage"' in page)

    def testNewUpload(self):
        fields = {
            'name': 'grnotify',
            'label': 'foo.local.test@foo:bar',
            'prodVer': 'v1',
            'namespace': 'ns1',
        }
        cmd = 'testproject/newUpload'
        def fakeStartPackageCreatorSession(s, *args):
            return 'asdfiafisd'
        projectHandler, auth = self._setupProjectHandlerMockClientMethod('startPackageCreatorSession', fakeStartPackageCreatorSession, cmd)
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)
        page = func(auth=auth, **fields)
        elem = self.extractElement(page, 'input', 'name', 'sessionHandle')
        self.failUnless('value="asdfiafisd"' in elem)
        self.failUnless('Editing grnotify' in page)

    def testSavePackage(self):
        from factory_test.packagecreatortest import expectedFactories1
        from factory_test.factorydatatest import dictDef
        cmd = 'testproject/savePackage'
        factoryHandle = expectedFactories1[0][0]
        factoryData = expectedFactories1[0][3]
        fields = {
            'sessionHandle': 'foobarbaz',
            'factoryHandle': factoryHandle
        }
        fields.update(factoryData)
        def fakeSavePackage(s, *args):
            self.assertEquals(args[0], 'foobarbaz')
            self.assertEquals(args[1], factoryHandle)
            self.assertEquals(args[2], factoryData)
        projectHandler,auth = self._setupProjectHandlerMockClientMethod(
                            'savePackage', fakeSavePackage, cmd)
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}

        func = projectHandler.handle(context)
        page = func(auth=auth, **fields)
        self.failUnless('Package Build Status' in page)

    def testGetPackageBuildLogsFail(self):
        cmd = 'testproject/getPackageBuildLogs'
        fields = {
            'sessionHandle': 'foobarbaz',
        }

        def fakeGetPackageBuildLogs(s, sesH):
            self.assertEquals(sesH, 'foobarbaz')
            raise mint.mint_error.PackageCreatorError("No idea why this happened")
        projectHandler,auth = self._setupProjectHandlerMockClientMethod(
                            'getPackageBuildLogs', fakeGetPackageBuildLogs, cmd)
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)
        self.assertRaises(mint.web.webhandler.HttpMovedTemporarily, func, auth=context['auth'], **context['fields'])

    def testGetPackageBuildLogs(self):
        cmd = 'testproject/getPackageBuildLogs'
        fields = {
            'sessionHandle': 'foobarbaz',
        }

        def fakeGetPackageBuildLogs(s, sesH):
            self.assertEquals(sesH, 'foobarbaz')
            return "A big long string"
        projectHandler,auth = self._setupProjectHandlerMockClientMethod(
                            'getPackageBuildLogs', fakeGetPackageBuildLogs, cmd)
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)
        page = func(auth=auth, **fields)
        self.assertEquals("A big long string", page)

    def testRebaseProductVersion(self):
        self.called = False
        def fakeRebase(pd, cclient, label):
            self.assertEquals(label, 'conary.rpath.com@rpl:2-devel')
            self.called = True
        self.mock(proddef.ProductDefinition, 'rebase', fakeRebase)
        self.mock(proddef.ProductDefinition, 'saveToRepository', lambda *x: None)
        methodName = 'processRebaseProductVersion'

        def getProductDefinition(self, *args, **kwargs):
            pd = proddef.ProductDefinition()
            pd.setProductName("Mocked product name")
            pd.setProductShortname("mockedProductShortVersion")
            pd.setProductVersion("1.0")
            pd.setProductDescription("Mocked product description")
            pd.setProductVersionDescription("Mocked product version description")
            pd.setConaryRepositoryHostname("conary.example.com")
            pd.setConaryNamespace("cns")
            pd.setImageGroup("group-os")
            pd.addStage(name = "devel", labelSuffix = "-devel")
            pd.addStage(name = "qa", labelSuffix = "-qa")
            pd.addStage(name = "release", labelSuffix = "")
            return pd

        cmd = 'testproject/processRebaseProductVersion'
        fields = {'id': 1, 'platformLabel': 'conary.rpath.com@rpl:2-devel',
                'action': 'Update Appliance Platform'}
        projectHandler, auth = self._setupProjectHandlerMockClientMethod('getProductDefinitionForVersion', getProductDefinition, cmd)
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)
        try:
            page = func(auth = auth, **fields)
        except mint.web.webhandler.HttpMovedTemporarily:
            pass
        self.assertEquals(self.called, True)

    def testEditVersionHardcodedValues(self):
        self.called = False
        def fakeRebase(pd, cclient, label):
            self.assertEquals(label, 'conary.rpath.com@rpl:2-devel')
            self.called = True
        self.mock(proddef.ProductDefinition, 'rebase', fakeRebase)
        self.mock(proddef.ProductDefinition, 'saveToRepository', lambda *x: None)

        def fail(self, *args, **kwargs):
            self.fail('this codepath should not have been taken')

        methodName = 'processEditVersion'
        cmd = 'testproject/processEditVersion'
        fields = {'id': -1, 'namespace': 'foo', 'name': '1', 'description': '',
                'sessionHandle': 'foobarbaz', 'pdstages-1-name': 'devel', 'pdstages-1-labelSuffix': '-devel', 'platformLabel': 'conary.rpath.com@rpl:2-devel'}
        projectHandler, auth = self._setupProjectHandlerMockClientMethod('getProductVersion', fail, cmd)
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)
        try:
            page = func(auth = auth, **fields)
        except mint.web.webhandler.HttpMovedTemporarily:
            pass

        self.assertEquals(projectHandler._getCurrentProductVersion(), 2)  #This should be set to the new version
        client = projectHandler.client
        projectId = projectHandler.projectId
        self.assertEquals(self.called, True)
        #The _setupProjectHandlerMockClientMethod created product version is versionId 1
        self.failUnless([2, 1, 'foo', '1', ''] in  client.getProductVersionListForProduct(projectId))

    def testEditVersionMissingValues(self):
        methodName = 'processEditVersion'
        cmd = 'testproject/processEditVersion'
        fields = {'id': -1, 'namespace': 'foo', 'name': '', 'description': '',
                'sessionHandle': 'foobarbaz', 'pdstages-1-name': 'devel', 'pdstages-1-labelSuffix': '-devel'}

        #set up the request
        projectHandler = self._setupProjectHandler()
        projectHandler.req = mint_rephelp.FakeRequest(FQDN, 'POST', cmd)
        projectHandler.baseUrl = 'http://%s/' % FQDN
        auth = projectHandler.client.checkAuth()
        projectHandler.projectList = projectHandler.client.getProjectsByMember(auth.userId)
        projectHandler.projectDict = {}

        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)

        def fail(*args, **kwargs):
            raise RuntimeError('rebase was called')

        # make sure that rebase does NOT get called
        self.mock(proddef.ProductDefinition, 'rebase', fail)

        #mock the write method, since we really want to see what was returned, instead of a rendered page
        self.mock(projectHandler.client, 'getAvailablePlatforms', lambda: [])
        self.mock(projectHandler, '_write', lambda *a, **k: (a,k))

        pagea, pagek = func(auth=auth, **fields)
        #The primary result
        self.assertEquals(pagea[0], 'editVersion')
        self.assertEquals(projectHandler._getErrors(), ['Missing major version'])

    def testListPackagesEmpty(self):
        fields = {}
        cmd = 'testproject/packageCreatorPackages'
        def getPackageList1(s, projectId):
            return {}
        projectHandler, auth = self._setupProjectHandlerMockClientMethod('getPackageCreatorPackages', getPackageList1, cmd)
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)
        page = func(auth=auth, **fields)
        assert 'No packages available' in page, "Should show a message for the empty results"

    def testListPackagesSimple(self):
        fields = {}
        cmd = 'testproject/packageCreatorPackages'
        def getPackageList(s, projectId):
            return {u'vs1': getPackageCreatorFactoriesData1['vs1']}
        projectHandler, auth = self._setupProjectHandlerMockClientMethod('getPackageCreatorPackages', getPackageList, cmd)
        vId = projectHandler.client.addProductVersion(projectHandler.projectId, "ns1", "vs1", "Fluff description")
        projectHandler._setCurrentProductVersion(vId)
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)
        page = func(auth=auth, **fields)

        headings, uploadLines = self._extractPackageListLines(page)

        self.assertEquals(len(uploadLines), 2)
        self.assertEquals(len(headings), 1)
        self.failUnless('Version vs1 (ns1)' in headings[0])

    def _extractPackageListLines(self, page):
        #Extract all lines containing "newUpload"
        strio = StringIO.StringIO(page)
        uploadLines = []
        headings = []
        while True:
            line = strio.readline()
            if not line: break
            line = line.strip()
            if 'newUpload' in line:
                uploadLines.append(line)
            if 'class="package-version-header"' in line:
                headings.append(line)
        return headings, uploadLines

    def testListPackagesMeaty(self):
        fields = {}
        cmd = 'testproject/packageCreatorPackages'
        def getPackageList(s, projectId):
            return getPackageCreatorFactoriesData1
        projectHandler, auth = self._setupProjectHandlerMockClientMethod('getPackageCreatorPackages', getPackageList, cmd)
        vId = projectHandler.client.addProductVersion(projectHandler.projectId, "ns1", "vs1", "Fluff description")
        projectHandler._setCurrentProductVersion(vId)
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)
        page = func(auth=auth, **fields)

        headings, uploadLines = self._extractPackageListLines(page)

        self.assertEquals(len(uploadLines), 2)
        assert "newUpload?name=grnotify:source&amp;label=testproject.rpath.local2@ns1:testproject-vs1-devel/0.4.5-1&amp;prodVer=vs1&amp;namespace=ns1" in uploadLines[0]
        assert '"newUpload?name=zope:source&amp;label=testproject.rpath.local2@ns1:testproject-vs1-devel/2.7.8-1&amp;prodVer=vs1&amp;namespace=ns1"' in uploadLines[1]

        self.assertEquals( len(headings), 1)
        assert 'Version vs1 (ns1)' in headings[0]

    def testCreateProject(self):
        self.called = False
        def fakeRebase(pd, cclient, label):
            self.assertEquals(label, 'conary.rpath.com@rpl:2-devel')
            self.called = True
        self.mock(proddef.ProductDefinition, 'rebase', fakeRebase)
        self.mock(proddef.ProductDefinition, 'saveToRepository', lambda *x: None)

        def fakeNewProject(*args, **kwargs):
            return self.newProject(client)

        methodName = 'newProject'
        cmd = '/createProject'
        fields = {'title': 'Test Project', 'hostname': 'test', 'domainname': 'test', 'blurb': '', 'appliance': True, 'namespace': 'rpl', 'shortname': 'test', 'version': '1', 'prodtype': 'Appliance', 'platformLabel': 'conary.rpath.com@rpl:2-devel'}
        siteHandler, auth = self._setupSiteHandlerMockClientMethod('1newProject', fakeNewProject, cmd)
        context = {'auth': auth, 'cmd': cmd, 'client': siteHandler.client, 'fields': fields}
        func = siteHandler.handle(context)
        try:
            page = func(auth = auth, **fields)
        except mint.web.webhandler.HttpMovedTemporarily:
            pass

        self.assertEquals(self.called, True)


if __name__ == "__main__":
    testsetup.main()


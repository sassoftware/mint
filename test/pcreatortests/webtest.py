#!/usr/bin/python
#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#

import sys
if '..' not in sys.path: sys.path.append('..')
import testsuite
testsuite.setup()
import mint_rephelp
import mock
import webprojecttest
from pcreator import factorydata

import factory_test.testSetup
factory_test.testSetup.setup()

import testrunner.resources

from factory_test.factorydatatest import basicXmlDef

import re, os, StringIO

import mint.mint_error
import mint.web.webhandler
from types import MethodType

from rpath_common.proddef import api1 as proddef

import pcreatortests.packagecreatoruitest

class TestPackageCreatorUIWeb(webprojecttest.WebProjectBaseTest):
    """ Unit tests for the web ui pieces of the Package Creator """

    @testsuite.context('more_cowbell')
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
        assert 'value="Upload"' in page.body
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

    @testsuite.context('more_cowbell')
    def testPackageCreatorIframe(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                mint_rephelp.MINT_PROJECT_DOMAIN)
        self.webLogin('testuser', 'testpass')
        page = self.fetch('/project/testproject/upload_iframe?uploadId=foobarbaz;fieldname=upldfile',
                server=self.getProjectServerHostname())
        assert 'action="/cgi-bin/fileupload.cgi?uploadId=foobarbaz;fieldname=upldfile"' in page.body
        assert not 'input type="submit"' in page.body.lower(), "Did you forget to remove the submit button?"
        assert 'input type="file" name="uploadfile"' in page.body, 'The file field name is fixed'
        assert 'name="project" value="testproject"' in page.body, 'Make sure the project name is in the form'

    def extractElement(self, page, elemType, attributeName, attributeValue):
        match = re.search("<%(elemType)s[^>]*%(attributeName)s=['|\"]%(attributeValue)s['|\"][^>]*>" % dict(elemType=elemType, attributeName=attributeName, attributeValue=attributeValue), page)
        if match:
            return match.group()
        else:
            return match

    def _setupProjectHandlerMockClientMethod(self, methodName, mockMethod, requestName):
        ### All this, just to monkeypatch the client
        projectHandler = self._setupProjectHandler()
        projectHandler.req = mint_rephelp.FakeRequest(self.getProjectServerHostname(), 'POST', requestName)
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
                 os.path.join(conary_test.resources.factoryRecipePath,
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

    def testEditVersionRebaseUpdate(self):
        self.called = False
        def fakeRebase(pd, cclient, label):
            self.assertEquals(label, None)
            self.called = True
        self.mock(proddef.ProductDefinition, 'rebase', fakeRebase)
        methodName = 'processEditVersion'

        def getProductDefinition(self, *args, **kwargs):
            return proddef.ProductDefinition()

        cmd = 'testproject/processEditVersion'
        fields = {'id': 1, 'namespace': 'foo', 'name': '1', 'description': '',
                'sessionHandle': 'foobarbaz', 'pdstages-1-name': 'devel', 'pdstages-1-labelSuffix': '-devel', 'updatePlatform': '1'}
        projectHandler, auth = self._setupProjectHandlerMockClientMethod('getProductDefinitionForVersion', getProductDefinition, cmd)
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)
        try:
            page = func(auth = auth, **fields)
        except mint.web.webhandler.HttpMoved:
            pass
        self.assertEquals(self.called, True)


    def testEditVersionHardcodedValues(self):
        self.called = False
        def fakeRebase(pd, cclient, label):
            self.assertEquals(label, 'conary.rpath.com@rpl:2-devel')
            self.called = True
        self.mock(proddef.ProductDefinition, 'rebase', fakeRebase)

        def fail(self, *args, **kwargs):
            self.fail('this codepath should not have been taken')

        methodName = 'processEditVersion'
        cmd = 'testproject/processEditVersion'
        fields = {'id': -1, 'namespace': 'foo', 'name': '1', 'description': '',
                'sessionHandle': 'foobarbaz', 'pdstages-1-name': 'devel', 'pdstages-1-labelSuffix': '-devel'}
        projectHandler, auth = self._setupProjectHandlerMockClientMethod('getProductVersion', fail, cmd)
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)
        try:
            page = func(auth = auth, **fields)
        except mint.web.webhandler.HttpMoved:
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
        projectHandler.req = mint_rephelp.FakeRequest(self.getProjectServerHostname(), 'POST', cmd)
        auth = projectHandler.client.checkAuth()
        projectHandler.projectList = projectHandler.client.getProjectsByMember(auth.userId)
        projectHandler.projectDict = {}

        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)

        #Mock out the product definition completely
        self.mock(proddef, 'ProductDefinition', mock.mockClass(proddef.ProductDefinition))

        #mock the write method, since we really want to see what was returned, instead of a rendered page
        self.mock(projectHandler, '_write', lambda *a, **k: (a,k))

        pagea, pagek = func(auth=auth, **fields)
        #The primary result
        self.assertEquals(pagea[0], 'editVersion')
        self.assertEquals(projectHandler._getErrors(), ['Missing major version'])
        # make sure that rebase did NOT get called
        pagek['productDefinition'].rebase._mock.assertNotCalled()

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
            return {u'vs1': pcreatortests.packagecreatoruitest.getPackageCreatorFactoriesData1['vs1']}
        projectHandler, auth = self._setupProjectHandlerMockClientMethod('getPackageCreatorPackages', getPackageList, cmd)
        projectHandler._setCurrentProductVersion(-1)
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)
        page = func(auth=auth, **fields)

        h3eadings, uploadLines = self._extractPackageListLines(page)

        self.assertEquals(len(uploadLines), 2)
        self.assertEquals(len(h3eadings), 1)
        self.assertEquals(h3eadings[0], '<h3>Product Version vs1 (ns1)</h3>')

    def _extractPackageListLines(self, page):
        #Extract all lines containing "newUpload"
        strio = StringIO.StringIO(page)
        uploadLines = []
        h3eadings = []
        while True:
            line = strio.readline()
            if not line: break
            line = line.strip()
            if 'newUpload' in line:
                uploadLines.append(line)
            if '<h3>' in line:
                h3eadings.append(line)
        return h3eadings, uploadLines

    def testListPackagesMeaty(self):
        fields = {}
        cmd = 'testproject/packageCreatorPackages'
        def getPackageList(s, projectId):
            return pcreatortests.packagecreatoruitest.getPackageCreatorFactoriesData1
        projectHandler, auth = self._setupProjectHandlerMockClientMethod('getPackageCreatorPackages', getPackageList, cmd)
        projectHandler._setCurrentProductVersion(-1) #unset the current session so we see all of them
        context = {'auth': auth, 'cmd': cmd, 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)
        page = func(auth=auth, **fields)

        h3eadings, uploadLines = self._extractPackageListLines(page)

        self.assertEquals(len(uploadLines), 4)
        assert "newUpload?name=grnotify:source&amp;label=testproject.rpath.local2@ns1:testproject-vs1-devel&amp;prodVer=vs1&amp;namespace=ns1" in uploadLines[0]
        assert '"newUpload?name=zope:source&amp;label=testproject.rpath.local2@ns1:testproject-vs1-devel&amp;prodVer=vs1&amp;namespace=ns1"' in uploadLines[1]
        assert '"newUpload?name=grnotify:source&amp;label=testproject.rpath.local2@ns1:testproject-vs2-devel&amp;prodVer=vs2&amp;namespace=ns1"' in uploadLines[2]
        assert '"newUpload?name=grnotify:source&amp;label=testproject.rpath.local2@ns2:testproject-vs2-devel&amp;prodVer=vs2&amp;namespace=ns2"' in uploadLines[3]

        self.assertEquals( len(h3eadings), 3)
        assert 'Product Version vs1 (ns1)' in h3eadings[0]
        assert 'Product Version vs2 (ns1)' in h3eadings[1]
        assert 'Product Version vs2 (ns2)' in h3eadings[2]

    def testCreateProject(self):
        self.called = False
        def fakeRebase(pd, cclient, label):
            self.assertEquals(label, 'conary.rpath.com@rpl:2-devel')
            self.called = True
        self.mock(proddef.ProductDefinition, 'rebase', fakeRebase)

        def fakeNewProject(*args, **kwargs):
            return self.newProject(client)

        def fakeSetProductDefinitionForVersion(*args, **kwargs):
            pass

        methodName = 'newProject'
        cmd = '/createProject'
        fields = {'title': 'Test Project', 'hostname': 'test', 'domainname': 'test', 'blurb': '', 'appliance': True, 'namespace': 'rpl', 'shortname': 'test', 'version': '1', 'prodtype': 'Appliance'}
        siteHandler, auth = self._setupSiteHandlerMockClientMethod('1newProject', fakeNewProject, cmd)
        siteHandler.client.setProductDefinitionForVersion = \
                fakeSetProductDefinitionForVersion
        context = {'auth': auth, 'cmd': cmd, 'client': siteHandler.client, 'fields': fields}
        func = siteHandler.handle(context)
        try:
            page = func(auth = auth, **fields)
        except mint.web.webhandler.HttpMoved:
            pass

        self.assertEquals(self.called, True)


if __name__ == "__main__":
    testsuite.main()


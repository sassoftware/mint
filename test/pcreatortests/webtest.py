#!/usr/bin/python
#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#

import testsuite
testsuite.setup()
import mint_rephelp
import webprojecttest
from pcreator import factorydata

import factory_test.testSetup
factory_test.testSetup.setup()

import conary_test.resources

from factory_test.factorydatatest import basicXmlDef

import re, os, StringIO

import mint.mint_error
import mint.web.webhandler
from types import MethodType

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
        client.addProductVersion(projectId, "version1", "Fluff description")
        client.addProductVersion(projectId, "version2", "Fluff description")
        page = self.fetch('/project/testproject/newPackage',
                server=self.getProjectServerHostname())
        assert 'version1</option>' in page.body
        assert 'version2</option>' in page.body
        assert 'value="Create Package"' in page.body
        match = re.search('upload_iframe\?uploadId=([^;]+);', page.body)
        assert match, "Did not find an id in the page body"
        sessionHandle = match.groups()[0]
        assert sessionHandle, "expected sessionHandle"
        #Make sure it actually did what we asked
        #Get the tempPath
        tmppath = os.path.join(self.mintCfg.dataPath, 'tmp', 'rb-pc-upload-%s' % sessionHandle)
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

    def _setupInterviewEnvironment(self, mockMethod):
        fields = {
            'sessionHandle': 'foobarbaz',
            'versionId': '1',
            'uploadfile': 'UPLOADED',
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
            return ret

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
                 os.path.join(conary_test.resources.factoryArchivePath,
                              'recipedata', 'stub-definition.xml'))
        self.prefilled={'version': '0.1999', 'license': 'GPL', 'multiple_license': 'GPL', 'description': 'line1\nline2'}
        def fakepackagefactories(s, *args):
            self.factorystream.seek(0)
            return [('stub', factorydata.FactoryDefinition(fromStream=self.factorystream), self.prefilled)]

        func,context = self._setupInterviewEnvironment(fakepackagefactories)

        #The rest of the tests can be done with the stub factory
        page = func(auth=context['auth'], **context['fields'])

        import epdb; epdb.st()
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

        self.prefilled['boolean_value'] = 'TrUe'
        page = func(auth=context['auth'], **context['fields'])
        elem = self.extractElement(page, 'input', 'id', '0_boolean_value_id_True')
        self.failUnless(elem)
        self.failUnless('checked="checked"' in elem)
        elem = self.extractElement(page, 'input', 'id', '0_boolean_value_id_False')
        self.failUnless(elem)
        self.failIf('checked' in elem)

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

if __name__ == "__main__":
    testsuite.main()


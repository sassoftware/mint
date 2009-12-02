#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

import testsuite
testsuite.setup()

import os

from conary.lib import util

from mint_test import mint_rephelp
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN, MINT_DOMAIN
from mint import helperfuncs

class FakeUpdateServiceServerProxy:

    def __init__(self, url, *args, **kwargs):
        self.url = url
        self.mirrorusers = self
        self.MirrorUsers = self

    def addRandomUser(self, name):
        return 'thisisamirrorpassword'


class FakerAPA(mint_rephelp.StubXMLRPCServerController):

    class FakerAPAInterface:

        # dispatcher that works around methods that
        # look like 'foo.bar.baz.actualmethod' and
        # just calls 'actualmethod'
        def _dispatch(self, name, params):
            func = getattr(self, name.split('.')[-1])
            return func(*params)

        def addRandomUser(self, name):
            return 'thisisamirrorpassword'

    def handlerFactory(self):
        return self.FakerAPAInterface()

class WebPageTest(mint_rephelp.WebRepositoryHelper):
    def testCreateExternalProject(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')

        self.webLogin('adminuser', 'adminpass')
        page = self.fetch("/admin/addExternal")

        page = page.postForm(1, self.post,
                             {'hostname' : 'rap',
                              'name' : 'rPath Appliance Platform',
                              'label' : 'rap.rpath.com@rpath:linux-1',
                              'url' : ''})

        page = self.assertNotContent("/admin/addExternal",
                                     'NAME="hostname" VALUE="rap"')

        page = self.assertContent("/admin/external", "rPath Appliance Platform")
        project = client.getProjectByHostname("rap")

        # test editing
        page = self.fetch("/admin/editExternal?projectId=%d" % project.id)
        page = page.postForm(1, self.post,
                             {'name' : 'rPath LINUX',
                              'label' : 'conary.rpath.com@rpl:devel',
                              'url' : ''})
        project.refresh()
        self.failUnlessEqual(project.name, 'rPath LINUX')

    def testCreateMirroredProject(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')

        self.webLogin('adminuser', 'adminpass')

        page = self.fetch("/admin/addExternal")
        page = page.postForm(1, self.post,
                             {'hostname' : 'rap',
                              'name' : 'rPath Appliance Platform',
                              'label' : 'rap.rpath.com@rpath:linux-1',
                              'url' : '',
                              'useMirror': 'net',
                              'authType': 'userpass',
                              'externalUser': 'mirror',
                              'externalPass': 'mirrorpass'})

        # ensure "first time" content does not appear on page
        page = self.assertNotContent("/admin/addExternal",
                                     'NAME="hostname" VALUE="rap"')

        # and make sure that the appropriate database entries are created
        assert(client.getInboundMirrors() == [[1, 1,
            'rap.rpath.com@rpath:linux-1',
            'https://rap.rpath.com/conary/', 'userpass', 'mirror',
            'mirrorpass', '', '', 0]])

        # and make sure that the 'shell' repository was created
        assert(os.path.exists(os.path.join(self.reposDir + '-mint', 'repos', 'rap.rpath.com')))

    @testsuite.tests('RBL-2039')
    def testConfigureMirrorBackup(self):
        '''
        Check that an external mirrored project can be configured for
        backups.
        '''
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        details = { 'hostname' : 'rap',
                    'name' : 'rPath Appliance Platform',
                    'label' : 'rap.rpath.com@rpath:linux-1',
                    'url' : '',
                    'useMirror': 'net',
                    'authType': 'userpass',
                    'externalUser': 'mirror',
                    'externalPass': 'mirrorpass'}

        # Create without backup
        page = self.fetch("/admin/addExternal")
                        
        page.postForm(1, self.post, details)

        project = client.getProjectByHostname("rap")
        self.failUnlessEqual(project.backupExternal, 0)

        # Turn backups on
        page = self.fetch("/admin/editExternal?projectId=%d" % project.id)
        details['backupExternal'] = '1'
        page.postForm(1, self.post, details)

        project.refresh()
        self.failUnlessEqual(project.backupExternal, 1)

    def testPreloadMirroredProject(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')

        self.webLogin('adminuser', 'adminpass')

        page = self.fetch("/admin/addExternal")
        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:1',
                              'url' : '',
                              'useMirror': 'preload',
                              'authType': 'userpass',
                              'externalUser': 'mirror',
                              'externalPass': 'mirrorpass'})

        pText = helperfuncs.getProjectText().lower()
        page = self.assertContent("/project/rpath/",
            "To preload this external %s as a local mirror"%pText)

        page = self.fetch("/admin/addExternal")

        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath2',
                              'name' : 'rPath Linux 2',
                              'label' : 'conary.rpath.com@rpl:1',
                              'url' : '',
                              'useMirror': 'preload',
                              'authType': 'none',
                              'externalUser': 'anonymous',
                              'externalPass': 'anonymous'})

        self.assertNotContent("/project/rpath2/",
            "To preload this external %s as a local mirror"%pText)

    def setupUser(self, repos, reposLabel, user, pw):
        repos.addRole(reposLabel, user)
        repos.addUser(reposLabel, user, pw)
        repos.addRoleMember(reposLabel, user, user)
        repos.addAcl(reposLabel, user, None, None, write=False, remove=False)
        repos.setRoleCanMirror(reposLabel, user, True)
        return self.getRepositoryClient(user = user, password = pw)

    def testCreateExternalProjectEntitlement(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        entClass = 'entitlementclass'
        entKey = 'entitlementkey'
        repos = self.openRepository(1)
        userRepos = self.setupUser(repos, 'localhost1@rpl:devel', 'user', 'bar')

        repos.addEntitlementClass('localhost1', entClass, 'user')
        repos.addEntitlementKeys('localhost1', entClass, [entKey])

        util.mkdirChain(self.mintCfg.dataPath + "/entitlements/")
        # ensure "first time" content appears on page
        page = self.fetch("/admin/addExternal")
        page = page.postForm(1, self.post,
            {'hostname':        'external',
             'name':            'External Project',
             'label':           'localhost1@rpl:devel',
             'url':             'http://localhost:%d/conary/' % self.servers.getServer(1).port,
             'authType':        'entitlement',
             'externalEntKey':  entKey,
            }
        )

        # re-edit page
        page = self.fetch("/admin/editExternal?projectId=1")
        formData = page.getFormData(1)[0]
        self.assertEqual(formData.get('authType'), ['entitlement'])
        self.assertEqual(formData.get('externalEntKey'), entKey)


    def testCreateExternalProjectEntitlementExtraWhitespace(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        entClass = 'entitlementclass'
        entKey = 'entitlementkey'
        repos = self.openRepository(1)
        userRepos = self.setupUser(repos, 'localhost1@rpl:devel', 'user', 'bar')

        repos.addEntitlementClass('localhost1', entClass, 'user')
        repos.addEntitlementKeys('localhost1', entClass, [entKey])

        util.mkdirChain(self.mintCfg.dataPath + "/entitlements/")
        # ensure "first time" content appears on page
        page = self.fetch("/admin/addExternal")
        page = page.postForm(1, self.post,
            {'hostname':        'external',
             'name':            'External Project',
             'label':           'localhost1@rpl:devel',
             'url':             'http://localhost:%d/conary/' % self.servers.getServer(1).port,
             'authType':        'entitlement',
             'externalEntKey':  '%s    \n' % entKey,
             'externalEntClass':'  %s' % entClass,
            }
        )

        # re-edit page
        page = self.fetch("/admin/editExternal?projectId=1")
        formData = page.getFormData(1)[0]
        self.assertEqual(formData.get('authType'), ['entitlement'])
        self.assertEqual(formData.get('externalEntKey'), entKey)

    def testExternalProjectMirrorAllLabels(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        util.mkdirChain(self.mintCfg.dataPath + "/entitlements/")
        # ensure "first time" content appears on page
        page = self.fetch("/admin/addExternal")
        page = page.postForm(1, self.post,
            {'hostname':                'rpath',
             'name':                    'rPath Linux',
             'label':                   'conary.rpath.com@rpl:devel',
             'url':                     '',
             'authType':                'userpass',
             'externalUser':            'test',
             'externalPass':            'pass',
             'allLabels':               '1',
             'additionalLabelsToMirror':'',
             'useMirror':               'net',
            }
        )

        self.failUnlessEqual(client.getInboundMirror(1)['allLabels'], 1)

    def testCreateExternalProjectNoAuth(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        # check errors
        page = self.fetch("/admin/addExternal")
        page = page.postForm(1, self.post,
             {'hostname':       'rpath',
              'name':           '',
              'label':          'conary.rpath.com@rpl:devel',
              'url':            '',
              'operation':      'process_external'}
        )
        pText = helperfuncs.getProjectText().lower()
        assert('Missing %s title'%pText in page.body)

        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:devel',
                              'url' : '',
                              'operation' : 'process_external'})

        # ensure "first time" content does not appear on page
        page = self.assertNotContent("/admin/addExternal",
                                     'NAME="hostname" VALUE="rpath"')

        # and make sure that the appropriate database entries are created
        self.assertEquals(client.getLabelsForProject(1),
            ({'conary.rpath.com@rpl:devel': 1},
             {'conary.rpath.com': 'http://conary.rpath.com/conary/'},
             [], []))

    def testEditMirroredProject(self):
        # mainly make sure that user-entered settings are preserved on the edit
        # page, and not taken from the internal Labels table by mistake (RBL-1170)
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        page = self.fetch("/admin/addExternal")
        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:1',
                              'url' : '',
                              'useMirror': 'net',
                              'authType': 'userpass',
                              'externalUser': 'mirror',
                              'externalPass': 'mirrorpass',
                              'additionalLabelsToMirror': ''})

        p = client.getProjectByHostname('rpath')
        page = self.fetch("/admin/editExternal?projectId=%d" % p.id)

        self.failUnless('VALUE="https://conary.rpath.com/conary/"' in page.body)
        self.failUnless('NAME="externalUser" VALUE="mirror"' in page.body)
        self.failUnless('NAME="externalPass" VALUE="mirrorpass"' in page.body)

        # check editing of additionalLabelsToMirror
        page = self.fetch("/admin/editExternal?projectId=%d" % p.id)
        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:1-other',
                              'url' : '',
                              'useMirror': 'net',
                              'authType': 'userpass',
                              'externalUser': 'mirror',
                              'externalPass': 'mirrorpass'})

        self.failUnlessEqual(client.getInboundMirror(1)['sourceLabels'], 'conary.rpath.com@rpl:1-other')

        self.fetch('/admin/external')

        # turn off mirroring
        page = self.fetch("/admin/editExternal?projectId=%d" % p.id)
        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:1',
                              'url' : '',
                              'useMirror': 'none',
                              'authType': 'userpass',
                              'externalUser': 'mirror',
                              'externalPass': 'mirrorpass'})

        self.failUnlessEqual(client.getInboundMirrors(), [])
        self.failUnlessEqual(client.translateProjectFQDN('rpath' + MINT_PROJECT_DOMAIN),
            'rpath' + MINT_PROJECT_DOMAIN)

    def testExternalToMirroredProject(self):
        # mainly make sure that user-entered settings are preserved on the edit
        # page, and not taken from the internal Labels table by mistake (RBL-1170)
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        page = self.fetch("/admin/addExternal")
        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:1',
                              'url' : '',
                              'useMirror': 'none',
                              'authType': 'userpass',
                              'externalUser': 'mirror',
                              'externalPass': 'mirrorpass',
                              'additionalLabelsToMirror': ''})

        self.failIf(os.path.exists(os.path.join(self.reposDir + '-mint', 'repos', 'conary.rpath.com')))

        # turn off mirroring
        p = client.getProjectByHostname('rpath')
        page = self.fetch("/admin/editExternal?projectId=%d" % p.id)
        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:1',
                              'url' : '',
                              'useMirror': 'net',
                              'authType': 'userpass',
                              'externalUser': 'mirror',
                              'externalPass': 'mirrorpass'})

        self.failUnlessEqual(len(client.getInboundMirrors()), 1)
        self.failUnless(os.path.exists(os.path.join(self.reposDir + '-mint', 'repos', 'conary.rpath.com')))

    def testEditExternalProject(self):
        # make sure that editing an external projects' label actually does the
        # edit (RBL-1234)
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        page = self.fetch("/admin/addExternal")
        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:1',
                              'url' : '',
                              'useMirror': 'preload',
                              'authType': 'userpass',
                              'externalUser': 'mirror',
                              'externalPass': 'mirrorpass'})

        p = client.getProjectByHostname('rpath')
        page = self.fetch("/admin/editExternal?projectId=%d" % p.id)
        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:1-newlabel',
                              'url' : '',
                              'useMirror': 'none',
                              'authType': 'none',
                              'externalUser': '',
                              'externalPass': ''})
        self.failUnlessEqual(p.getLabel(), "conary.rpath.com@rpl:1-newlabel")

    @testsuite.tests('RBL-3179')
    def testEditExternalProjectWithLabelTableBreakage(self):
        """
        This tests the case where the labelId of a project != the projectId
        (bad assumption in code).
        """
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        projectId1 = self.newProject(client, 'Created before external project',
                hostname = 'before')

        # make a bogus label to knock the assumption off
        cu = self.db.cursor()
        cu.execute("""INSERT INTO Labels VALUES(NULL, -1, 'boguslabel.example.com@foo:bar', 'http://boguslabel.example.com/conary/', 'none', '', '', '')""")
        self.db.commit()

        page = self.fetch("/admin/addExternal")
        page = page.postForm(1, self.post,
                             {'hostname' : 'myexternal',
                              'name' : 'Thee External Project and Tra-La-La Band (with Choir)',
                              'label' : 'myexternal.example.com@sgp:1',
                              'url' : '',
                              'useMirror': 'none',
                              'authType': 'none',
                              'externalUser': '',
                              'externalPass': ''})

        projectExt = client.getProjectByHostname('myexternal')

        # make sure project has the right label
        page = self.assertContent('/admin/editExternal?projectId=%d' % projectExt.id,
                content = 'myexternal.example.com@sgp:1')

    def testBrowseUsers(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        page = self.assertContent("/users", code = [200],
            content = '<A HREF="/userInfo?id=%d"' % userId)

    def testNoAdminPowers(self):
        self.assertCode("/admin/", code = 403)

    def testFrontPage(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')

        self.webLogin('adminuser', 'adminpass')
        self.assertContent('/admin/', code = [200],
            content = 'Administration Menu')

        self.assertCode("/admin/404", code = 404)
        self.assertCode("/admin/cfg", code = 404)

    def testNewUser(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')

        self.webLogin('adminuser', 'adminpass')
        origPage = self.assertContent('/admin/newUser', code = [200],
            content = 'Create an Account')

        newUserInfo = \
            {'newUsername':  'newuser',
             'fullName':     'Full Name',
             'email':        'test@example.com',
             'displayEmail': 'test at example dot com',
             'blurb':        'This is my blurb.',
             'password':     'password',
             'password2':    'password',
            }

        page = origPage.postForm(1, self.post, newUserInfo)

        # sanity check
        newUserId = client.getUserIdByName('newuser')
        user = client.getUser(newUserId)
        self.failUnlessEqual(user.fullName, 'Full Name')

        # error conditions
        broken = newUserInfo.copy()
        broken['newUsername'] = ''
        page = origPage.postForm(1, self.post, broken)
        assert('You must supply a username.' in page.body)

        broken = newUserInfo.copy()
        broken['email'] = ''
        page = origPage.postForm(1, self.post, broken)
        assert('You must supply a valid e-mail address.' in page.body)

        broken = newUserInfo.copy()
        broken['password'] = broken['password2'] = ''
        page = origPage.postForm(1, self.post, broken)
        assert('Password field left blank.' in page.body)

        broken = newUserInfo.copy()
        broken['password2'] = 'different'
        page = origPage.postForm(1, self.post, broken)
        assert('Passwords do not match.' in page.body)

        broken = newUserInfo.copy()
        broken['password'] = broken['password2'] = 'short'
        page = origPage.postForm(1, self.post, broken)
        assert('Password must be 6 characters or longer.' in page.body)

        page = origPage.postForm(1, self.post, newUserInfo)
        assert('An account with that username already exists.' in page.body)

    def testReports(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        page = self.assertContent('/admin/reports', code = [200],
            content = 'Select a Report')

        # make sure we get a real pdf
        page = page.postForm(1, self.post, {'reportName': 'site_summary'})
        assert(page.body.startswith('%PDF-1.3'))

    def testSelections(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        data = dict(name='name', link='link', rank='1', op='set')
        page = self.fetch('/admin/addSelection', postdata = data)
        assert('Manage Front Page Selections' in page.body)

        x = client.getFrontPageSelection()
        page = self.fetch('/admin/deleteSelection',
            postdata = {'itemId': str(x[0]['itemId'])})
        assert('Manage Front Page Selections' in page.body)

    def testAddOutboundMirror(self):
        '''
        Test basic functionality of the add outbound mirror page.
        '''
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        projectId = self.newProject(client)

        form = self.fetch('/admin/editOutbound')

        # Add an outbound mirror with all labels
        page = form.postForm(1, self.post, {
            'projectId': str(projectId),
            'mirrorSources': '1',
            'allLabels': '1',
            'mirrorBy': 'label',
            'action': 'Save',
            'useReleases': '0',
          })

        # Add an outbound mirror with some labels
        page = form.postForm(1, self.post, {
            'projectId': str(projectId),
            'mirrorSources': '1',
            'allLabels': '0',
            'labelList': ['conary.example.com@rpl:1',
                'conary.example.com@rpl:1-devel'],
            'mirrorBy': 'label',
            'action': 'Save',
            'useReleases': '0',
          })

        # Add an outbound mirror with some labels and no sources
        page = form.postForm(1, self.post, {
            'projectId': str(projectId),
            'mirrorSources': '0',
            'allLabels': '0',
            'labelList': 'conary.example.com@rpl:1',
            'mirrorBy': 'label',
            'action': 'Save',
            'useReleases': '0',
          })

        # Add an outbound mirror with some labels and some groups
        page = form.postForm(1, self.post, {
            'projectId': str(projectId),
            'mirrorSources': '0',
            'allLabels': '0',
            'labelList': 'conary.example.com@rpl:1',
            'mirrorBy': 'group',
            'groups': ['group-foo', 'group-bar'],
            'action': 'Save',
            'useReleases': '0',
          })

        # Add an outbound mirror with mirror-by-release
        page = form.postForm(1, self.post, {
            'projectId': str(projectId),
            'mirrorSources': '0',
            'allLabels': '0',
            'mirrorBy': 'label',
            'action': 'Save',
            'useReleases': '1',
          })

        mirrors = client.getOutboundMirrors()
        mirrors = [(project, labels, allLabels, recurse,
            matchStrings, useReleases) for (_, project, labels, allLabels,
            recurse, matchStrings, _, _, useReleases) in mirrors]
        self.failUnlessEqual(mirrors, [
            # All labels
            (projectId, '', True, False, ['+.*'], False),
            # Some labels, with sources
            (projectId,
                'conary.example.com@rpl:1 conary.example.com@rpl:1-devel',
                False, False, ['+.*'], False),
            # Some labels, no sources
            (projectId, 'conary.example.com@rpl:1', False, False,
                ['-.*:source', '-.*:debuginfo', '+.*'], False),
            # Some labels, some groups
            (projectId, 'conary.example.com@rpl:1', False, True,
                ['+group-foo', '+group-bar'], False),
            # All labels
            (projectId, '', False, False, [], True),
          ])


class UpdateServiceWebTest(mint_rephelp.WebRepositoryHelper):

    def setUp(self):
        self.faker = FakerAPA()
        mint_rephelp.WebRepositoryHelper.setUp(self)

    def tearDown(self):
        mint_rephelp.WebRepositoryHelper.tearDown(self)
        if self.faker: self.faker.kill()

    def testCreateUpdateServiceWeb(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')
        page = self.assertNotContent('/admin/updateServices',
                content = 'Remove Selected')

        page = self.fetch("/admin/editUpdateService")
        self.failUnless('Add Update Service' in page.body,
                "We should be in add mode")

        rapaHostPort = '%s:%s' % (self.faker.getHost(),
                self.faker.getPort())
        page = page.postForm(1, self.fetchWithRedirect,
                    { 'hostname': rapaHostPort,
                              'description': 'WYSIWYG',
                              'adminUser': 'agent',
                              'adminPassword': 'secret',
                              'action': 'submit' })

        self.failUnless('Update Service added' in page.body)
        self.failUnless(rapaHostPort in page.body)
        self.failUnless('WYSIWYG' in page.body)
        self.failUnless('Remove Selected' in page.body)

    def testEditUpdateServiceWeb(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')
        rapaHostPort = '%s:%s' % (self.faker.getHost(),
                self.faker.getPort())
        rus1id = client.addUpdateService(rapaHostPort,
                'agent', 'secret', 'WYSIWYG')

        page = self.assertContent('/admin/updateServices',
                content = 'WYSIWYG')

        page = page.assertContent('/admin/editUpdateService?id=%d' % rus1id,
                content = 'Edit Update Service')

        self.failUnless(rapaHostPort in page.body)
        self.failUnless('WYSIWYG' in page.body)
        self.failIf('Update Service Username' in page.body,
                'Editing the username/password is not available in edit mode')

        page = page.postForm(1, self.fetchWithRedirect,
                            { 'description': 'Chumbawamba',
                              'action': 'Submit'})

        self.failUnless('Update Service changed' in page.body)
        self.failUnless('Chumbawamba' in page.body)

    def testDeleteUpdateServiceWeb(self):
        import xmlrpclib
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')


        _oldServerProxy = xmlrpclib.ServerProxy
        try:
            xmlrpclib.ServerProxy = FakeUpdateServiceServerProxy

            rus1id = client.addUpdateService('test1.example.com',
                    'agent', 'secret', 'Do not delete me')
            rus2id = client.addUpdateService('test2.example.com',
                    'agent', 'secret', 'Kill me with fire')
            rus3id = client.addUpdateService('test3.example.com',
                    'agent', 'secret', 'Do not delete me, either')
        finally:
            xmlrpclib.ServerProxy = _oldServerProxy

        page = self.fetch('/admin/updateServices')

        page = page.postForm(1, self.postAssertContent,
                { 'remove': {str(rus2id): 'checked'} }, "Are you sure")

        page = page.postForm(1, self.fetchWithRedirect, {'confirmed': "1"})

        self.failIf("Kill me with fire" in page.body)

if __name__ == "__main__":
    testsuite.main()

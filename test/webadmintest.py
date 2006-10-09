#!/usr/bin/python2.4
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

import testsuite
testsuite.setup()

import os
from conary.lib import util

import mint_rephelp
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN, MINT_DOMAIN
from mint import database

class WebPageTest(mint_rephelp.WebRepositoryHelper):
    def testCreateExternalProject(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')

        self.webLogin('adminuser', 'adminpass')

        # ensure "first time" content appears on page
        page = self.assertContent("/admin/external",
                                  'name="hostname" value="rpath"')

        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:devel',
                              'url' : '',
                              'operation' : 'process_external'})

        # ensure "first time" content does not appear on page
        page = self.assertNotContent("/admin/external",
                                     'name="hostname" value="rpath"')

    def testCreateMirroredProject(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')

        self.webLogin('adminuser', 'adminpass')

        # ensure "first time" content appears on page
        page = self.assertContent("/admin/external",
                                  'name="hostname" value="rpath"')

        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:devel',
                              'url' : '',
                              'useMirror': '1',
                              'externalAuth': '1',
                              'externalUser': 'mirror',
                              'externalPass': 'mirrorpass',
                              'operation' : 'process_external'})

        # ensure "first time" content does not appear on page
        page = self.assertNotContent("/admin/external",
                                     'name="hostname" value="rpath"')

        # and make sure that the appropriate database entries are created
        assert(client.getInboundLabels() == [[1, 1, 'https://conary.rpath.com/conary/', 'mirror', 'mirrorpass']])

        # and make sure that the 'shell' repository was created
        assert(os.path.exists(os.path.join(self.reposDir, 'repos', 'conary.rpath.com')))

    def testCreateExternalProjectEntitlement(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        util.mkdirChain(self.mintCfg.dataPath + "/entitlements/")
        # ensure "first time" content appears on page
        page = self.fetch("/admin/external")
        page = page.postForm(1, self.post,
            {'hostname':        'rpath',
             'name':            'rPath Linux',
             'label':           'conary.rpath.com@rpl:devel',
             'url':             '',
             'externalAuth':    '1',
             'operation':       'process_external',
             'authType':        'entitlement',
             'externalEntKey':  'entitlementkey',
             'externalEntClass':'entitlementclass',
            }
        )

        assert(os.path.exists(self.mintCfg.dataPath + "/entitlements/conary.rpath.com"))

    def testCreateExternalProjectNoAuth(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        # ensure "first time" content appears on page
        page = self.assertContent("/admin/external",
                                  'name="hostname" value="rpath"')

        # check errors
        page = self.fetch("/admin/external")
        page = page.postForm(1, self.post,
             {'hostname':       'rpath',
              'name':           '',
              'label':          'conary.rpath.com@rpl:devel',
              'url':            '',
              'operation':      'process_external'}
        )
        assert('Missing project title' in page.body)

        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:devel',
                              'url' : '',
                              'operation' : 'process_external'})

        # ensure "first time" content does not appear on page
        page = self.assertNotContent("/admin/external",
                                     'name="hostname" value="rpath"')

        # and make sure that the appropriate database entries are created
        assert(client.getLabelsForProject(1) == ({'conary.rpath.com@rpl:devel': 1},
                                                 {'conary.rpath.com': 'http://conary.rpath.com/conary/'},
                                                 {'conary.rpath.com': ('anonymous', 'anonymous')}))


    def testCreateOutboundMirror(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        projectId = client.newProject("Foo", "testproject", MINT_PROJECT_DOMAIN)

        self.webLogin('adminuser', 'adminpass')

        # ensure "first time" content appears on page
        page = self.assertContent("/admin/outbound",
            content = "No projects are currently mirrored")
        page = self.assertContent("/admin/addOutbound",
            content = "Project to mirror:")

        page = page.postForm(1, self.post,
            {'projectId':       str(projectId),
             'targetUrl':       'http://www.example.com/conary/',
             'mirrorUser':      'mirror',
             'mirrorPass':      'mirrorpass',
             'mirrorSources':   0})

        self.assertContent("/admin/outbound",
            content = "testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel")
        assert(client.getOutboundLabels() == \
            [[projectId, 1, 'http://www.example.com/conary/', 'mirror', 'mirrorpass', False, False]])
        assert(client.getOutboundMatchTroves(projectId) == \
               ['-.*:source', '-.*:debuginfo', '+.*'])

        page = self.fetch("/admin/outbound")
        page = page.postForm(1, self.post,
            {'remove':      '1 http://www.example.com/conary/',
             'operation':   'remove_outbound'})

        assert(client.getOutboundLabels() == [])
        assert(client.getOutboundMatchTroves(projectId) == [])

    def testCreateOutboundMirrorSources(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        projectId = client.newProject("Foo", "testproject", MINT_PROJECT_DOMAIN)

        self.webLogin('adminuser', 'adminpass')

        page = self.fetch("/admin/addOutbound")
        page = page.postForm(1, self.post,
            {'projectId':       str(projectId),
             'targetUrl':       'http://www.example.com/conary/',
             'mirrorUser':      'mirror',
             'mirrorPass':      'mirrorpass',
             'mirrorSources':   '1'})

        self.assertContent("/admin/outbound",
            content = "testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel")
        assert(client.getOutboundLabels() == \
            [[projectId, 1, 'http://www.example.com/conary/', 'mirror', 'mirrorpass', False, False]])
        assert(client.getOutboundMatchTroves(projectId) == [])

    def testBrowseUsers(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        page = self.assertContent("/users", code = [200],
            content = '<a href="/userInfo?id=%d"' % userId)

    def testNotifyAllUsers(self):
        self.quickMintUser('localuser', 'localpass', email = 'test@localhost')
        self.quickMintUser('otheruser', 'otherpass', email = 'test@NONE')
        client, userId = self.quickMintAdmin('adminuser', 'adminpass',
                                             email = "test@NONE")

        self.webLogin('adminuser', 'adminpass')

        page = self.assertContent("/admin/notify",
            code = [200], content = 'value="notify_send"')

        page = page.postForm(1, self.post,
            {'subject':     'This is is my subject',
             'body':        'This is my body.',
             'operation':  'notify_send'})

        # make sure that our users were invalidated properly. admins and users
        # at localhost are expempted from invalidation
        self.assertRaises(database.ItemNotFound,
                          client.server._server.getConfirmation, 'adminuser')
        self.assertRaises(database.ItemNotFound,
                          client.server._server.getConfirmation, 'localuser')
        assert(client.server._server.getConfirmation('otheruser'))

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
            content = 'Select a report')

        # make sure we get a real pdf
        page = page.postForm(1, self.post, {'reportName': 'site_summary'})
        assert(page.body.startswith('%PDF-1.3'))

    def testUseIt(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        # test the /useIt path
        origPage = self.assertContent('/admin/useIt', code = [200],
            content = 'Manage Use It Icons')

        client.addUseItIcon(1, 'test name', 'test link')
        page = self.assertContent('/admin/useIt', code = [200],
            content = 'Manage Use It Icons')

        for x in range(4):
            client.addUseItIcon(x, 'test name %d' % x, 'test link')
        page = self.assertContent('/admin/useIt', code = [200],
            content = 'Manage Use It Icons')

        for x in range(6):
            client.addUseItIcon(x, 'test name %d' % x, 'test link')
        page = self.assertContent('/admin/useIt', code = [200],
            content = 'Manage Use It Icons')

        # test the setter/previewer
        params = {'op': 'preview'}
        for x in range(6):
            params.update({'name%d' % x: 'link_name_%d' % x, 'link%d' % x: 'link_%d' % x})
        page = origPage.postForm(1, self.post, params)
        assert('link_name_1' in page.body)

        params['op'] = 'set'
        page = origPage.postForm(1, self.post, params)
        assert('link_name_1' in page.body)

        page = self.fetch('/admin/deleteUseItIcon',
            postdata = {'itemId': '1'}, ok_codes = [200])
        assert('link_name_0' not in page.body)

    def testJobs(self):
        raise testsuite.SkipTestException("apache tries to run sudo to fetch job server status")
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        self.assertContent('/admin/jobs', code = [200],
            content = 'Retrieving job status from server')

    def testSelections(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        data = dict(name='name', link='link', rank='1', op='preview')
        page = self.fetch('/admin/addSelection', postdata = data)
        assert('<a href="link">name</a>' in page.body)

        data['op'] = 'set'
        page = self.fetch('/admin/addSelection', postdata = data)
        assert('Manage Front Page Selections' in page.body)

        x = client.getFrontPageSelection()
        page = self.fetch('/admin/deleteSelection',
            postdata = {'itemId': str(x[0]['itemId'])})
        assert('Manage Front Page Selections' in page.body)

    def testSpotlight(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        origPage = self.assertContent('/admin/spotlight', code = [200],
            content = 'Manage Spotlight Appliances')

        data = dict(title = 'Title', text = 'This is a test.',
            link = 'http://www.example.com/', logo = 'logo.gif',
            showArchive = '1', startDate = '05/05/2000', endDate = '05/06/2050',
            operation = 'preview')
        page = origPage.postForm(1, self.post, data)
        assert('Click for more information.' in page.body)

        data['operation'] = 'apply'
        page = origPage.postForm(1, self.post, data)
        assert('This is a test.' in page.body)

        x = client.getSpotlightAll()
        page = self.fetch('/admin/deleteSpotlightItem',
            postdata = {'itemId': str(x[0]['itemId']),
                        'title': x[0]['title']})
        assert('Delete Appliance Spotlight Entry "Title"?' in page.body)

        page = self.fetch('/admin/delSpotlight',
            postdata = {'itemId': str(x[0]['itemId'])})
        self.failUnlessEqual(client.getSpotlightAll(), False)


if __name__ == "__main__":
    testsuite.main()

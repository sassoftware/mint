#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
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
from mint.web import admin
from mint.web.webhandler import HttpMoved

class rogueReq(object):
    def __init__(self):
        self.err_headers_out = {}
        self.headers_out = {}
        self.uri = ''

class WebPageTest(mint_rephelp.WebRepositoryHelper):
    def testCreateExternalProject(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')

        self.webLogin('adminuser', 'adminpass')

        # ensure "first time" content appears on page
        page = self.assertContent("/admin/addExternal",
                                  'name="hostname" value="rpath"')

        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:devel',
                              'url' : ''})

        page = self.assertNotContent("/admin/addExternal",
                                     'name="hostname" value="rpath"')

        page = self.assertContent("/admin/external", "rPath Linux")
        project = client.getProjectByHostname("rpath")

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

        # ensure "first time" content appears on page
        page = self.assertContent("/admin/addExternal",
                                  'name="hostname" value="rpath"')

        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:1',
                              'url' : '',
                              'useMirror': 'net',
                              'authType': 'userpass',
                              'externalUser': 'mirror',
                              'externalPass': 'mirrorpass'})

        # ensure "first time" content does not appear on page
        page = self.assertNotContent("/admin/addExternal",
                                     'name="hostname" value="rpath"')

        # and make sure that the appropriate database entries are created
        assert(client.getInboundMirrors() == [[1, 1,
            'conary.rpath.com@rpl:1 conary.rpath.com@rpl:1-compat conary.rpath.com@rpl:1-xen',
            'https://conary.rpath.com/conary/', 'mirror', 'mirrorpass', 0]])

        # and make sure that the 'shell' repository was created
        assert(os.path.exists(os.path.join(self.reposDir, 'repos', 'conary.rpath.com')))

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

        page = self.assertContent("/project/rpath/",
            "To preload this external project as a local mirror")

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
            "To preload this external project as a local mirror")

    def testCreateExternalProjectEntitlement(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        util.mkdirChain(self.mintCfg.dataPath + "/entitlements/")
        # ensure "first time" content appears on page
        page = self.fetch("/admin/addExternal")
        page = page.postForm(1, self.post,
            {'hostname':        'rpath',
             'name':            'rPath Linux',
             'label':           'conary.rpath.com@rpl:devel',
             'url':             '',
             'authType':        'entitlement',
             'externalEntKey':  'entitlementkey',
             'externalEntClass':'entitlementclass',
            }
        )

        assert(os.path.exists(self.mintCfg.dataPath + "/entitlements/conary.rpath.com"))

    def testCreateExternalProjectEntitlementExtraWhitespace(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        util.mkdirChain(self.mintCfg.dataPath + "/entitlements/")
        # ensure "first time" content appears on page
        page = self.fetch("/admin/addExternal")
        page = page.postForm(1, self.post,
            {'hostname':        'rpath',
             'name':            'rPath Linux',
             'label':           'conary.rpath.com@rpl:devel',
             'url':             '',
             'authType':        'entitlement',
             'externalEntKey':  'entitlementkey  \n',
             'externalEntClass':'  entitlementclass',
            }
        )

        from conary.conarycfg import loadEntitlementFromString

        entPath = self.mintCfg.dataPath + "/entitlements/conary.rpath.com"
        xmlContent = open(entPath).read()
        ent = loadEntitlementFromString(xmlContent, "conary.rpath.com", entPath)
        self.failUnlessEqual(ent, ('entitlementclass', 'entitlementkey'))

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
             'authType':                'entitlement',
             'externalEntKey':          'entitlementkey',
             'externalEntClass':        'entitlementclass',
             'allLabels':                   '1',
             'additionalLabelsToMirror':'',
             'useMirror':              'net',
            }
        )

        self.failUnlessEqual(client.getInboundMirror(1)['allLabels'], 1)

    def testCreateExternalProjectNoAuth(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        # ensure "first time" content appears on page
        page = self.assertContent("/admin/addExternal",
                                  'name="hostname" value="rpath"')

        # check errors
        page = self.fetch("/admin/addExternal")
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
        page = self.assertNotContent("/admin/addExternal",
                                     'name="hostname" value="rpath"')

        # and make sure that the appropriate database entries are created
        assert(client.getLabelsForProject(1) == ({'conary.rpath.com@rpl:devel': 1},
                                                 {'conary.rpath.com': 'http://conary.rpath.com/conary/'},
                                                 {'conary.rpath.com': ('anonymous', 'anonymous')}))

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

        self.failUnless('value="https://conary.rpath.com/conary/"' in page.body)
        self.failUnless('name="externalUser" value="mirror"' in page.body)
        self.failUnless('name="externalPass" value="mirrorpass"' in page.body)

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

        self.failIf(os.path.exists(os.path.join(self.reposDir, 'repos', 'conary.rpath.com')))

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
        self.failUnless(os.path.exists(os.path.join(self.reposDir, 'repos', 'conary.rpath.com')))

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

    def testCreateOutboundMirror(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        # Test repMapName
        projectId = client.newExternalProject("Foo", "testproject",
            MINT_PROJECT_DOMAIN, 'testproject.fake.project.domain@rpl:devel',
            'https://fake.project.domain/conary/', True)
        client.addRemappedRepository('testproject.' + MINT_PROJECT_DOMAIN,
                                     'testproject.fake.project.domain')
        self.webLogin('adminuser', 'adminpass')

        # ensure "first time" content appears on page
        page = self.assertContent("/admin/addOutbound",
            content = "Project to mirror:")

        def fakeUpdateMirror(user, servername, host, sp):
            return 'totallyfakepassword'

        ad = admin.AdminHandler()
        ad._updateMirror = fakeUpdateMirror
        ad.session = {}
        ad.client = client
        ad.cfg = self.mintCfg
        ad.req = rogueReq()
        self.assertRaises(HttpMoved, ad.processAddOutbound,
                              projectId=projectId)
        self.assertRaises(HttpMoved, ad.processAddOutbound,
                              projectId=projectId,
                              mirrorSources=1,
                              mirrorBy='group',
                              groups='group-test')

        ad = admin.AdminHandler()
        ad._updateMirror = fakeUpdateMirror
        ad.session = {}
        ad.client = client
        ad.cfg = self.mintCfg
        ad.req = rogueReq()
        self.assertRaises(HttpMoved, ad.processAddOutboundMirrorTarget, outboundMirrorId=1,
                targetUrl='https://www.example.com/conary/', mirrorUser='foo',
                mirrorPass='bar')
        self.assertRaises(HttpMoved, ad.processAddOutboundMirrorTarget, outboundMirrorId=2,
                targetUrl='https://www.example.com/conary/', mirrorUser='foo',
                mirrorPass='bar')


        label = "testproject." + 'fake.project.domain' + "@rpl:devel"
        self.assertContent("/admin/outbound", content = label)
        fqdn = client.translateProjectFQDN(client.getProject(projectId).getFQDN())
        assert(client.getOutboundMirrors() == \
            [[1, 1, 'testproject.fake.project.domain@rpl:devel', False, False, ['-.*:source', '-.*:debuginfo', '+.*'], 0], [2, 1, 'testproject.fake.project.domain@rpl:devel', False, True, ['+group-test'], 1]])

        assert(client.getOutboundMirrorTargets(1) == \
                        [[1, 'https://www.example.com/conary/',
                    '%s-www.example.com' % fqdn, 'totallyfakepassword']])
        assert(client.getOutboundMirrorTargets(2) == \
            [[2, 'https://www.example.com/conary/', 'group-test-testproject.fake.project.domain-www.example.com', 'totallyfakepassword']])
        assert(client.getOutboundMirrorMatchTroves(1) == \
               ['-.*:source', '-.*:debuginfo', '+.*'])

        assert(client.getOutboundMirrorMatchTroves(2) == \
               ['+group-test'])

        page = self.fetch("/admin/outbound")
        page = page.postForm(1, self.post,
            {'remove':      ['1'],
             'operation':   'remove_outbound'})
        page = page.postForm(1, self.post,
                {'yesArgs': {'func': 'removeOutbound', 'removeJSON': "['1']", 'confirmed': "1" }})

        page = self.fetch("/admin/outbound")
        page = page.postForm(1, self.post,
            {'remove':      ['2'],
             'operation':   'remove_outbound'})
        page = page.postForm(1, self.post,
                {'yesArgs': {'func': 'removeOutbound', 'removeJSON': "['2']", 'confirmed': "1" }})

        assert(client.getOutboundMirrors() == [])

    def testCreateOutboundMirrorSources(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        projectId = client.newProject("Foo", "testproject", MINT_PROJECT_DOMAIN)

        self.webLogin('adminuser', 'adminpass')

        page = self.fetch("/admin/addOutbound")

        def fakeUpdateMirror(user, servername, sp):
            return 'totallyfakepassword'

        ad = admin.AdminHandler()
        ad._updateMirror = fakeUpdateMirror
        ad.session = {}
        ad.client = client
        ad.cfg = self.mintCfg
        ad.req = rogueReq()
        self.assertRaises(HttpMoved, ad.processAddOutbound,
                              projectId=projectId,
                              mirrorSources=1)

        label = "testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel"
        self.assertContent("/admin/outbound", content = label)
        #fqdn = client.getProject(projectId).getFQDN()
        assert(client.getOutboundMirrors() == \
            [[1, 1, label, False, False, [], 0]])

        #assert(client.getOutboundMirrorTargets(1) == \
                #    [ [ 'https://www.example.com/conary/', '%s-www.example.com' % fqdn, 'totallyfakepassword' ] ])
        assert(client.getOutboundMirrorMatchTroves(1) == [])

        self.assertRaises(HttpMoved, ad.processAddOutbound,
                              projectId=projectId,
                              mirrorSources=0,
                              mirrorBy='group',
                              groups='group-test')
        assert(client.getOutboundMirrors()[1][5] == ['-.*:source', '-.*:debuginfo', '+group-test'])
        import epdb
        epdb.st()

    def testBrowseUsers(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        page = self.assertContent("/users", code = [200],
            content = '<a href="/userInfo?id=%d"' % userId)

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
            showArchive = '1', startDate = '05/05/2000', endDate = '05/06/2030',
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

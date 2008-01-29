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
import StringIO

import mint_rephelp
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN, MINT_DOMAIN
from mint import database
from mint import helperfuncs
from mint import mirror
from mint import constants
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
                                  'name="hostname" value="rap"')

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
                                  'name="hostname" value="rap"')

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
            'conary.rpath.com@rpl:1',
            'https://conary.rpath.com/conary/', 'userpass', 'mirror',
            'mirrorpass', '', 0]])

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

    def setupUser(self, repos, reposLabel, user, pw, troves, label):
        repos.addUser(reposLabel, user, pw)
        repos.addAcl(reposLabel, user, troves, label, False, False, False)
        repos.setUserGroupCanMirror(reposLabel, user, True)

        return self.getRepositoryClient(user = user, password = pw)

    def testCreateExternalProjectEntitlement(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        entClass = 'entitlementclass'
        entKey = 'entitlementkey'
        repos = self.openRepository(1)
        userRepos = self.setupUser(repos, 'localhost1@rpl:devel', 'user', 'bar', None, None)

        repos.addEntitlementGroup('localhost1', entClass, 'user')
        repos.addEntitlements('localhost1', entClass, [entKey])

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
        userRepos = self.setupUser(repos, 'localhost1@rpl:devel', 'user', 'bar', None, None)

        repos.addEntitlementGroup('localhost1', entClass, 'user')
        repos.addEntitlements('localhost1', entClass, [entKey])

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

        # ensure "first time" content appears on page
        page = self.assertContent("/admin/addExternal",
                                  'name="hostname" value="rap"')

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
                                     'name="hostname" value="rpath"')

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
        pText = helperfuncs.getProjectText().title()
        page = self.assertContent("/admin/addOutbound",
            content = "%s to mirror:"%pText)

        def fakeUpdateMirror(*P, **K):
            return 'totallyfakepassword'

        ad = admin.AdminHandler()
        ad._updateMirror = fakeUpdateMirror
        ad.session = {}
        ad.client = client
        ad.cfg = self.mintCfg
        ad.req = rogueReq()
        self.assertRaises(HttpMoved, ad.processAddOutbound,
                              projectId=projectId, action="Save",
                              labelList=['testproject.fake.project.domain@rpl:devel'])
        self.assertRaises(HttpMoved, ad.processAddOutbound,
                              projectId=projectId,
                              mirrorSources=1,
                              mirrorBy='group',
                              labelList=['testproject.fake.project.domain@rpl:devel'],
                              groups='group-test', action="Save")

        ad = admin.AdminHandler()
        ad._updateMirror = fakeUpdateMirror
        ad.session = {}
        ad.client = client
        ad.cfg = self.mintCfg
        ad.req = rogueReq()
        self.assertRaises(HttpMoved, ad.processAddOutboundMirrorTarget, outboundMirrorId=1,
                targetUrl='https://www.example.com/conary/', mirrorUser='foo',
                mirrorPass='bar')
        oldTrans = admin.ProxiedTransport.__init__
        oldProxy = ad.cfg.proxy.copy()
        try:
            ad.cfg.proxy.update({'https':'https://fake.proxy.setting:1234'})
            sio = StringIO.StringIO()
            admin.ProxiedTransport.__init__ = lambda x,y: sio.write(y)
            self.assertRaises(HttpMoved, ad.processAddOutboundMirrorTarget, outboundMirrorId=2,
                targetUrl='https://www.example.com/conary/', mirrorUser='foo',
                mirrorPass='bar')
            assert(sio.getvalue() == 'https://fake.proxy.setting:1234')
        finally:
            admin.ProxiedTransport.__init__ = oldTrans
            ad.cfg.proxy = oldProxy
            sio.close()

        label = "testproject." + 'fake.project.domain' + "@rpl:devel"
        self.assertContent("/admin/outbound", content = label)
        expectedUser = helperfuncs.hashMirrorRepositoryUser(self.mintCfg.hostName, self.mintCfg.siteDomainName, 'www.example.com', 1, label, '-.*:source -.*:debuginfo +.*')
        assert(client.getOutboundMirrors() == \
            [[1, 1, 'testproject.fake.project.domain@rpl:devel', False, False, ['-.*:source', '-.*:debuginfo', '+.*'], 0, True], [2, 1, 'testproject.fake.project.domain@rpl:devel', False, True, ['+group-test'], 1, True]])

        assert(client.getOutboundMirrorTargets(1) == \
                        [[1, 'https://www.example.com/conary/',
                         expectedUser, 'totallyfakepassword']])
        expectedUser = helperfuncs.hashMirrorRepositoryUser(self.mintCfg.hostName, self.mintCfg.siteDomainName, 'www.example.com', 1, label, '+group-test')
        assert(client.getOutboundMirrorTargets(2) == \
            [[2, 'https://www.example.com/conary/', expectedUser, 'totallyfakepassword']])
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

    def testCreateOutboundMirrorSameServername(self):
        rusPasswordInfo = dict()

        def fakeUpdateMirror1(user, *P, **K):
            rusPasswordInfo[user] = 'totallyfake'
            return 'totallyfake'

        def fakeUpdateMirror2(user, *P, **K):
            rusPasswordInfo[user] = 'totallyfakealso'
            return 'totallyfakealso'

        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')
        projectId = client.newExternalProject("tp-1-release",
                "tp-1-release", MINT_PROJECT_DOMAIN,
                'repos.example.com@tp:1-release',
                'https://repos.example.com/conary/', False)

        projectId2 = client.newExternalProject("tp-1-devel",
                "tp-1-devel", MINT_PROJECT_DOMAIN,
                'repos.example.com@tp:1-devel',
                'https://repos.example.com/conary/', False)

        ad = admin.AdminHandler()
        ad._updateMirror = fakeUpdateMirror1
        ad.session = {}
        ad.client = client
        ad.cfg = self.mintCfg
        ad.req = rogueReq()
        self.assertRaises(HttpMoved, ad.processAddOutbound,
                              projectId=projectId, id = -1,
                              allLabels=True, action="Save")
        self.assertRaises(HttpMoved, ad.processAddOutboundMirrorTarget,
                outboundMirrorId=1,
                targetUrl='https://rus.example.com/conary/',
                mirrorUser='foo',
                mirrorPass='bar')
        obm = client.getOutboundMirror(1)
        obt = client.getOutboundMirrorTarget(1)

        ad2 = admin.AdminHandler()
        ad2._updateMirror = fakeUpdateMirror2
        ad2.session = {}
        ad2.client = client
        ad2.cfg = self.mintCfg
        ad2.req = rogueReq()
        self.assertRaises(HttpMoved, ad2.processAddOutbound,
                              projectId=projectId2, id = -1,
                              allLabels=True, action="Save")
        self.assertRaises(HttpMoved, ad2.processAddOutboundMirrorTarget,
                outboundMirrorId=2,
                targetUrl='https://rus.example.com/conary/',
                mirrorUser='foo',
                mirrorPass='bar')
        obm2 = client.getOutboundMirror(2)
        obt2 = client.getOutboundMirrorTarget(2)

        self.failUnlessEqual(len(rusPasswordInfo), 2,
                "Tripped over RBL-2318")
        self.failUnlessEqual(rusPasswordInfo[obt['username']],
                obt['password'])
        self.failUnlessEqual(rusPasswordInfo[obt2['username']],
                obt2['password'])

    def testCreateOutboundMirrorSources(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        projectId = client.newProject("Foo", "testproject", MINT_PROJECT_DOMAIN)

        self.webLogin('adminuser', 'adminpass')

        page = self.fetch("/admin/addOutbound")

        def fakeUpdateMirror(user, servername, mirrorUrl, sp):
            return 'totallyfakepassword'

        ad = admin.AdminHandler()
        ad._updateMirror = fakeUpdateMirror
        ad.session = {}
        ad.client = client
        ad.cfg = self.mintCfg
        ad.req = rogueReq()
        label = "testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel"
        self.assertRaises(HttpMoved, ad.processAddOutbound,
                              projectId=projectId, labelList=[label],
                              mirrorSources=1, action="Save")

        self.assertContent("/admin/outbound", content = label)
        assert(client.getOutboundMirrors() == \
            [[1, 1, label, False, False, mirror.INCLUDE_ALL_MATCH_TROVES, 0, True]])

        assert(client.getOutboundMirrorMatchTroves(1) == mirror.INCLUDE_ALL_MATCH_TROVES)

        self.assertRaises(HttpMoved, ad.processAddOutbound,
                              projectId=projectId,
                              mirrorSources=0,
                              labelList=[label],
                              mirrorBy='group',
                              groups='group-test', action="Save")
        assert(client.getOutboundMirrors()[1][5] == ['-.*:source', '-.*:debuginfo', '+group-test'])

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

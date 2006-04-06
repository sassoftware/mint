#!/usr/bin/python2.4
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

import os
import testsuite
testsuite.setup()

import mint_rephelp
from mint_rephelp import MINT_PROJECT_DOMAIN, MINT_DOMAIN
from conary.repository import errors
from mint import mint_error
from mint import releasetypes
from mint.distro import jsversion

class MaintenanceTest(mint_rephelp.WebRepositoryHelper):
    def testLogins(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        adminClient, adminUserId = self.quickMintAdmin('admin', 'admin')
        # test that we can log in
        page = self.webLogin('foouser', 'foopass')
        page = self.fetchWithRedirect('/logout')
        page = self.webLogin('admin', 'admin')
        page = self.fetchWithRedirect('/logout')
        f = open(self.mintCfg.maintenanceLockPath, 'w')
        f.close()
        try:
            # test that browsers get redirected to maintenance page
            page = self.fetch(self.mintCfg.basePath, ok_codes = [302])
            self.failIf(self.mintCfg.basePath + 'maintenance' not in page.body,
                        "Browsers should be redirected to maintenance page")
            # test that non-admin users are not allowed to log in.
            self.clearCookies()
            page = self.fetchWithRedirect(self.mintCfg.basePath)
            page = page.postForm(1, self.fetchWithRedirect,
                                 {'username': 'foouser',
                                  'password': 'foopass'})
            self.failIf('is currently undergoing maintenance' not in page.body,
                        "non-admin user appears to have logged in")

            # ensure no cookies are set
            self.failIf(self.cookies, "non-admin user got session cookies.")

            page = self.fetchWithRedirect(self.mintCfg.basePath)
            page = page.postForm(1, self.fetchWithRedirect,
                                 {'username': 'admin',
                                  'password': 'admin'})
            self.failIf('is currently undergoing maintenance' in page.body,
                        "admin user's login was rejected.")

            # ensure cookies are set
            self.failIf(not self.cookies, "admin user got no session cookies.")

            self.failIf('Maintenance Mode' not in page.body,
                        "Page does not indicate maintenance mode")
        finally:
            os.unlink(self.mintCfg.maintenanceLockPath)

    def testProjects(self):
        client, userId = self.quickMintAdmin('admin', 'admin')
        page = self.webLogin('admin', 'admin')
        f = open(self.mintCfg.maintenanceLockPath, 'w')
        f.close()
        try:
            page = self.fetchWithRedirect('/newProject')
            page = page.postForm(1, self.post, {'title': 'Bar Project',
                                                'hostname': 'bar'})
            self.failIf("Repositories are currenly offline" not in page.body,
                        "Admin user was allowed to create a project")
        finally:
            os.unlink(self.mintCfg.maintenanceLockPath)

    def testCommits(self):
        client, userId = self.quickMintAdmin('admin', 'admin')
        self.newProject(client)

        # ensure we are allowed to commit
        self.addComponent('test:data',
                          '/testproject.' + MINT_PROJECT_DOMAIN + \
                          '@rpl:devel/1.0-1-1')
        f = open(self.mintCfg.maintenanceLockPath, 'w')
        f.close()
        try:
            # ensure commit fails in maintenanceMode.
            self.assertRaises(errors.OpenError, self.addComponent,
                              'test:data',
                              '/testproject.' + MINT_PROJECT_DOMAIN + \
                              '@rpl:devel/1.0-1-1')
        finally:
            os.unlink(self.mintCfg.maintenanceLockPath)

    def testJobs(self):
        client, userId = self.quickMintAdmin('admin', 'admin')
        # use a shim client and skip the lockfile.
        maintenanceMode = self.mintServer.cfg.maintenanceMode
        self.mintServer.cfg.maintenanceMode = True
        try:
            self.assertRaises(mint_error.MaintenanceMode,
                              client.startNextJob,
                              ['1#x86'],
                              {'imageTypes' : [releasetypes.STUB_IMAGE]},
                              jsversion.getDefaultVersion())
        finally:
            self.mintServer.cfg.maintenanceMode = maintenanceMode

    def testRepos(self):
        client, userId = self.quickMintAdmin('admin', 'admin')
        self.newProject(client)
        f = open(self.mintCfg.maintenanceLockPath, 'w')
        f.close()
        try:
            # this call would normally not be safe.
            page = self.fetchWithRedirect('/repos/testproject/browse',
                              server = self.getProjectServerHostname())
            self.failIf("is currently undergoing maintenance" not in page.body,
                        "It appears we could browse the repo")
        finally:
            os.unlink(self.mintCfg.maintenanceLockPath)

    def testUsers(self):
        # use a shim client and skip the lockfile.
        maintenanceMode = self.mintServer.cfg.maintenanceMode
        self.mintServer.cfg.maintenanceMode = True
        try:
            self.assertRaises(mint_error.MaintenanceMode,
                              self.quickMintUser, 'newuser', 'newpass')
        finally:
            self.mintServer.cfg.maintenanceMode = maintenanceMode

    def testToggleLock(self):
        self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')
        page = self.fetchWithRedirect(self.mintCfg.basePath + 'administer' + \
                                      "?operation=maintenance_mode")
        self.failIf(os.path.exists(self.mintCfg.maintenanceLockPath),
                    "lock existed before test started")
        try:
            page.postForm(1, self.post, {'operation' :
                                         'toggle_maintenance_lock'})
            self.failIf(not os.path.exists(self.mintCfg.maintenanceLockPath),
                        "lock wasn't created by admin interface")
            page.postForm(1, self.post, {'operation' :
                                         'toggle_maintenance_lock'})
            self.failIf(os.path.exists(self.mintCfg.maintenanceLockPath),
                        "lock wasn't removed by admin interface")
        finally:
            try:
                os.unlink(self.mintCfg.maintenanceLockPath)
            except:
                # ignore "missing file" errors silently
                pass

if __name__ == "__main__":
    testsuite.main()

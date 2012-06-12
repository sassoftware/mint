#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

import testsuite
testsuite.setup()

import os

from mint_test import mint_rephelp
from mint_rephelp import MINT_PROJECT_DOMAIN, MINT_DOMAIN

from mint import config
from mint import maintenance
from mint import mint_error
from mint import buildtypes
from mint import users

from conary.repository import errors

class MaintenanceTest(mint_rephelp.WebRepositoryHelper):
    def tearDown(self):
        # ensure that locks cannot transcend test cases.
        try:
            os.unlink(self.mintCfg.maintenanceLockPath)
        except OSError, e:
            if e.errno != 2:
                raise
        mint_rephelp.WebRepositoryHelper.tearDown(self)

    def setMaintenanceMode(self, mode):
        maintenance.setMaintenanceMode(self.mintCfg, mode)

    def testLogins(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        adminClient, adminUserId = self.quickMintAdmin('admin', 'admin')
        # test that we can log in
        page = self.webLogin('foouser', 'foopass')
        page = self.fetchWithRedirect('/logout')
        page = self.webLogin('admin', 'admin')
        page = self.fetchWithRedirect('/logout')

        self.setMaintenanceMode(maintenance.LOCKED_MODE)

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

        self.failIf('maintenance mode' not in page.body,
                    "Page does not indicate maintenance mode")

    def testProjects(self):
        client, userId = self.quickMintAdmin('admin', 'admin')
        page = self.webLogin('admin', 'admin')
        self.setMaintenanceMode(maintenance.LOCKED_MODE)
        page = self.fetchWithRedirect('/newProject')
        page = page.postForm(1, self.post, {'title': 'Bar Project',
                                            'shortname': 'bar',
                                            'prodtype': 'Appliance',
                                            'version': '1.0'})
        self.failIf("Repositories are currently offline" not in page.body,
                    "Admin user was allowed to create a project")

    def testCommits(self):
        client, userId = self.quickMintAdmin('admin', 'admin')
        self.newProject(client)

        # ensure we are allowed to commit
        self.addComponent('test:data',
                          '/testproject.' + MINT_PROJECT_DOMAIN + \
                          '@rpl:devel/1.0-1-1')
        self.setMaintenanceMode(maintenance.LOCKED_MODE)

        # ensure commit fails in maintenance mode.
        self.assertRaises(errors.OpenError, self.addComponent,
                          'test:data',
                          '/testproject.' + MINT_PROJECT_DOMAIN + \
                          '@rpl:devel/1.0-1-1')

    def testUsers(self):
        # use a shim client and skip the lockfile.
        self.setMaintenanceMode(maintenance.LOCKED_MODE)
        self.assertRaises(mint_error.MaintenanceMode,
                          self.quickMintUser, 'newuser', 'newpass')

    def testToggleLock(self):
        self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')
        page = self.fetchWithRedirect(self.mintCfg.basePath + 'admin/maintenance')
        self.failIf(os.path.exists(self.mintCfg.maintenanceLockPath),
                    "lock existed before test started")
        page.postForm(1, self.post, {'curMode' :
                                     str(maintenance.NORMAL_MODE)})
        self.failIf(maintenance.getMaintenanceMode(self.mintCfg) != \
                    maintenance.LOCKED_MODE,
                    "lock wasn't created by admin interface")
        page.postForm(1, self.post, {'curMode':
                                     str(maintenance.LOCKED_MODE)})
        self.failIf(maintenance.getMaintenanceMode(self.mintCfg) != \
                    maintenance.NORMAL_MODE,
                    "lock wasn't removed by admin interface")

    def testGetMode(self):
        self.failIf(maintenance.getMaintenanceMode(self.mintCfg) !=
                    maintenance.NORMAL_MODE,
                    "missing lock file didn't equate to normal mode")
        for mode in (maintenance.NORMAL_MODE, maintenance.LOCKED_MODE):
            f = open(self.mintCfg.maintenanceLockPath, 'w')
            f.write(mode * chr(0))
            f.close()
            self.failIf(maintenance.getMaintenanceMode(self.mintCfg) !=
                        mode, "getMaintenanceMode returned incorrect value")

    def testSetMode(self):
        maintenance.setMaintenanceMode(self.mintCfg, maintenance.NORMAL_MODE)
        self.failIf(os.path.exists(self.mintCfg.maintenanceLockPath),
                    "setMaintenanceMode to normal didn't remove lock file")
        maintenance.setMaintenanceMode(self.mintCfg, maintenance.LOCKED_MODE)
        f = open(self.mintCfg.maintenanceLockPath)
        mode = len(f.read())
        f.close()
        self.failIf(mode != maintenance.LOCKED_MODE,
                    "maintenance mode not set properly")

    def testEnforceNormalMode(self):
        cfg = config.MintConfig()
        cfg.maintenanceLockPath = self.mintCfg.maintenanceLockPath
        userAuth = users.Authorization(authorized = True, username = "foo",
                                       stagnent = False)
        adminAuth = users.Authorization(authorized = True, username = "foo",
                                        stagnent = False, admin = True)
        # ensure no calls to enforceMaintenanceMode raise exception
        maintenance.enforceMaintenanceMode(cfg, userAuth)
        maintenance.enforceMaintenanceMode(cfg)
        maintenance.enforceMaintenanceMode(cfg, adminAuth)

    def testEnforceLockedMode(self):
        cfg = config.MintConfig()
        cfg.maintenanceLockPath = self.mintCfg.maintenanceLockPath
        userAuth = users.Authorization(authorized = True, username = "foo",
                                       stagnent = False)
        adminAuth = users.Authorization(authorized = True, username = "foo",
                                        stagnent = False, admin = True)
        # ensure proper calls to enforceMaintenanceMode raise exception
        self.setMaintenanceMode(maintenance.LOCKED_MODE)
        self.assertRaises(mint_error.MaintenanceMode,
                          maintenance.enforceMaintenanceMode, cfg, userAuth)
        self.assertRaises(mint_error.MaintenanceMode,
                          maintenance.enforceMaintenanceMode, cfg)
        maintenance.enforceMaintenanceMode(cfg, adminAuth)

    def testUserRedirect(self):
        page = self.fetchWithRedirect(self.mintCfg.basePath + 'maintenance')
        self.failIf(page.url != self.mintCfg.basePath,
                    "maintenance landing page didn't redirect to main page "
                    "when not in maintenance mode.")

    def testAdminRedirect(self):
        self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')
        self.setMaintenanceMode(maintenance.LOCKED_MODE)
        page = self.fetchWithRedirect(self.mintCfg.basePath + 'maintenance')
        self.failIf(page.url != self.mintCfg.basePath + 'administer',
                    "maintenance landing page didn't redirect to admin page "
                    "for admin users.")

    def testMaintenanceLockPerms(self):
        self.setMaintenanceMode(maintenance.LOCKED_MODE)
        lockDir = os.path.sep.join( \
            self.mintCfg.maintenanceLockPath.split(os.path.sep)[:-1])
        fMode = os.stat(lockDir)[0]
        try:
            os.chmod(lockDir, 0)
            self.assertRaises(OSError, self.setMaintenanceMode,
                              maintenance.NORMAL_MODE)
        finally:
            os.chmod(lockDir, fMode)


if __name__ == "__main__":
    testsuite.main()

#!/usr/bin/python

import datetime
import os
import sys
import tempfile
import time

import testsetup

from conary import versions
from conary.deps import deps

import mint_test
from mint_test import fixtures

from rpath_models import System

builtins = sys.modules.keys()
unimported = {}

class DjangoTest(fixtures.FixturedUnitTest):

    def setUpDjangoSettingsModule(self):
        settingsFile = os.path.join(mint_test.__path__[0], 'server/settings.py.in')
        settingsModule = os.path.join(self.cfg.dataPath, 'settings.py')
        dbDriver = 'sqlite3'
        user = ''
        port = ''
        os.system("sed 's|@MINTDBPATH@|%s|;s|@MINTDBDRIVER@|%s|;"
                        "s|@MINTDBUSER@|%s|;s|@MINTDBPORT@|%s|' %s > %s" % \
            (os.path.join(self.cfg.dataPath, 'mintdb'), dbDriver,
             user, port, settingsFile, settingsModule))
        sys.path.insert(0, self.cfg.dataPath)
        os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

    def importDjango(self):
        from mint.django_rest.rbuilder import models as rbuildermodels
        from mint.django_rest.rbuilder import inventory
        from mint.django_rest.rbuilder.inventory import systemdbmgr
        from mint.django_rest.rbuilder.inventory import models as systemmodels
        self.inventory = inventory
        self.rbuildermodels = rbuildermodels
        self.systemdbmgr = systemdbmgr
        self.systemmodels = systemmodels

    def _unImport(self):
        # "Unimport" anything that was imported so the next test will have a new
        # settings.py.
        for k, v in sys.modules.items():
            if k not in builtins or 'django' in k:
                unimported[k] = v
                sys.modules.pop(k)

    def setUp(self):
        unimported = {}
        self._unImport()
        fixtures.FixturedUnitTest.setUp(self)
        self.db, self.data = self.loadFixture('Empty')
        # Need to prepare settings.py before importing any django modules.
        self.setUpDjangoSettingsModule()
        self.importDjango()

    def _import(self):
        for k, v in unimported.items():
            sys.modules[k] = v

    def tearDown(self):
        self._import()
        fixtures.FixturedUnitTest.tearDown(self)


class SystemDbMgrTest(DjangoTest):

    def _data(self):
        # Set up some test data.
        #
        # Add target
        target = self.rbuildermodels.Targets.objects.create(
            targettype='aws', targetname='ec2')
        target = self.rbuildermodels.Targets.objects.get(
            targettype='aws', targetname='ec2')
        # Add user
        user = self.rbuildermodels.Users.objects.create(username='testuser',
            timecreated=str(time.time()), timeaccessed=str(time.time()),
            active=1)
        # Add credentials
        self.rbuildermodels.TargetUserCredentials(targetid=target, userid=user,
            credentials='testusercredentials').save()

        self.sdm = self.systemdbmgr.SystemDBManager(None, 'testuser')

    def _createSystem(self):
        system = System(target_system_id='testinstanceid',
                    target_type='aws', target_name='ec2',
                    registration_date=datetime.datetime.now(),
                    available=True)
        systemTarget = self.sdm.createSystem(system)
        return system, systemTarget

    def setUp(self):
        DjangoTest.setUp(self)
        self._data()

    def testCreateSystem(self):
        self._createSystem()
        self.assertEquals(1, len(self.systemmodels.managed_system.objects.all()))
        self.assertEquals(1, len(self.systemmodels.system_target.objects.all()))
        systemTarget = self.systemmodels.system_target.objects.get(target_system_id='testinstanceid')
        self.assertEquals('testinstanceid', systemTarget.target_system_id)

    def testCreateSystemWithSSLInfo(self):
        system = System(target_system_id='testinstanceid',
                    target_type='aws', target_name='ec2',
                    registration_date=datetime.datetime.now(),
                    ssl_client_certificate='/tmp/client',
                    ssl_client_key='/tmp/key',
                    available=True)
        self.sdm.createSystem(system)
        managedSystem = \
            self.systemmodels.system_target.objects.get(target_system_id='testinstanceid').managed_system
        self.assertEquals('/tmp/client', managedSystem.ssl_client_certificate)
        self.assertEquals('/tmp/key', managedSystem.ssl_client_key)

    def testUpdateSystem(self):
        system, systemTarget = self._createSystem()
        system.ssl_client_certificate = '/sslcert'
        system.ssl_client_key = '/sslkey'
        self.sdm.updateSystem(system)
        system = self.systemmodels.system_target.objects.get(target_system_id='testinstanceid')
        self.assertEquals('/sslcert', system.managed_system.ssl_client_certificate)
        self.assertEquals('/sslkey', system.managed_system.ssl_client_key)

    def testGetSystemByInstanceId(self):
        tmpDir = self.cfg.dataPath
        # Create ssl cert and ssl key
        sslCertFilePath = os.path.join(tmpDir, "sslcert")
        sslKeyFilePath = os.path.join(tmpDir, "sslkey")
        file(sslCertFilePath, "w")
        file(sslKeyFilePath, "w")
        system, systemTarget = self._createSystem()
        system.launching_user = self.sdm.user
        system.ssl_client_certificate = sslCertFilePath
        system.ssl_client_key = sslKeyFilePath
        self.sdm.updateSystem(system)

        system = self.sdm.getSystemByInstanceId('testinstanceid')
        self.assertEquals(system.ssl_client_certificate, sslCertFilePath)
        self.assertEquals(system.ssl_client_key, sslKeyFilePath)
        self.assertTrue(system.is_manageable)

        # Get rid of one of the files, should make the system unmanageable
        os.unlink(sslCertFilePath)
        system = self.sdm.getSystemByInstanceId('testinstanceid')
        self.assertEquals(system.ssl_client_certificate, sslCertFilePath)
        self.assertEquals(system.ssl_client_key, sslKeyFilePath)
        self.assertFalse(system.is_manageable)

    def testIsManageable(self):
        self._createSystem()
        systemTarget = self.systemmodels.system_target.objects.get(target_system_id='testinstanceid')
        self.assertTrue(self.sdm.isManageable(systemTarget.managed_system))

        # Create new user
        newUser = self.rbuildermodels.Users.objects.create(username='testuser2',
            timecreated=str(time.time()), timeaccessed=str(time.time()),
            active=1)
        # Now make the system owned by newUser
        systemTarget.managed_system.launching_user_id = newUser.userid
        systemTarget.managed_system.save()
        systemTarget = self.systemmodels.system_target.objects.get(target_system_id='testinstanceid')
        # No longer manageable, since testuser2 has no credentials
        self.assertFalse(self.sdm.isManageable(systemTarget.managed_system))

        target = self.rbuildermodels.Targets.objects.get(
            targettype='aws', targetname='ec2')
        self.rbuildermodels.TargetUserCredentials(targetid=target,
            userid=newUser, credentials='testusercredentials newUser2').save()

        systemTarget = self.systemmodels.system_target.objects.get(target_system_id='testinstanceid')
        # No longer manageable, since testuser2 has no credentials
        self.assertFalse(self.sdm.isManageable(systemTarget.managed_system))

        # Update credentials
        cu = self.systemdbmgr.connection.cursor()
        cu.execute("""UPDATE TargetUserCredentials SET credentials = %s
            WHERE targetId = %s AND userId = %s""",
            [ "testusercredentials", target.targetid, newUser.userid ])
        systemTarget = self.systemmodels.system_target.objects.get(target_system_id='testinstanceid')
        # Back to being manageable, same credentials as the current user
        self.assertTrue(self.sdm.isManageable(systemTarget.managed_system))

    def _getVersion(self): 
        name = 'group-appliance'
        version = versions.ThawVersion("/foo@bar:baz/1234567890:1-2-3")
        flavor = deps.parseFlavor("is:x86")
        return name, version, flavor

    def testAddSoftwareVersion(self):
        self.sdm.addSoftwareVersion(self._getVersion())
        svs = self.systemmodels.software_version.objects.all()
        self.assertEquals(1, len(svs))
        self.assertEquals('group-appliance', svs[0].name)
        self.assertEquals('/foo@bar:baz/1234567890.000:1-2-3', str(svs[0].version))
        self.assertEquals('is: x86', str(svs[0].flavor))
 
    def testGetManagedSystemForInstanceId(self):
        managedSystem = self.sdm.getManagedSystemForInstanceId('testinstanceid')
        self.assertTrue(managedSystem is None)

        self._createSystem()
        managedSystem = self.sdm.getManagedSystemForInstanceId('testinstanceid')
        self.assertTrue(isinstance(managedSystem, self.systemmodels.managed_system))
        

    def _setSoftwareVersion(self):
        system, systemTarget = self._createSystem()
        self.sdm.setSoftwareVersionForInstanceId('testinstanceid', [self._getVersion()])
        ssv = self.systemmodels.system_software_version.objects.filter(
                managed_system=systemTarget.managed_system)
        return ssv

    def testSetSoftwareVersionForInstanceId(self):
        ssv = self._setSoftwareVersion()
        self.assertEquals(1, len(ssv))

    def testGetSoftwareVersionForInstanceId(self):
        ssv = self._setSoftwareVersion()
        managedSystem = ssv[0].managed_system
        instanceId = self.systemmodels.system_target.objects.filter(
                        managed_system=managedSystem)[0].target_system_id
        vers = self.sdm.getSoftwareVersionsForInstanceId(instanceId)
        self.assertEquals('group-appliance=/foo@bar:baz/1234567890.000:1-2-3[is: x86]',
                str(vers))

    def testDeleteSoftwareVersionsForInstanceId(self):
        ssv = self._setSoftwareVersion()
        managedSystem = ssv[0].managed_system
        self.sdm.deleteSoftwareVersionsForInstanceId('testinstanceid')
        vers = self.systemmodels.system_software_version.objects.filter(
                managed_system=managedSystem)
        self.assertEquals(0, len(vers))

if __name__ == "__main__":
        testsetup.main()

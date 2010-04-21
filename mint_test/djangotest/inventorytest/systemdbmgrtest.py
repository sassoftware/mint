#!/usr/bin/python

import datetime
import os
import sys
import tempfile
import time

from testrunner import testhelp

from conary import versions
from conary.deps import deps

import mint_test
from mint_test import fixtures

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
        system = self.inventory.System(target_system_id='testinstanceid',
                    target_type='aws', target_name='ec2',
                    registration_date=datetime.datetime.now())
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

    def testUpdateSystem(self):
        system, systemTarget = self._createSystem()
        system.ssl_client_certificate = '/sslcert'
        system.ssl_client_key = '/sslkey'
        self.sdm.updateSystem(system)
        system = self.systemmodels.system_target.objects.get(target_system_id='testinstanceid')
        self.assertEquals('/sslcert', system.managed_system.ssl_client_certificate)
        self.assertEquals('/sslkey', system.managed_system.ssl_client_key)

    def testGetSystemByInstanceId(self):
        system, systemTarget = self._createSystem()
        system.launching_user = self.sdm.user
        system.ssl_client_certificate = '/sslcert'
        system.ssl_client_key = '/sslkey'
        self.sdm.updateSystem(system)
        system = self.sdm.getSystemByInstanceId('testinstanceid')
        self.assertEquals('/sslcert', system.ssl_client_certificate)
        self.assertEquals('/sslkey', system.ssl_client_key)

    def testIsManageable(self):
        self._createSystem()
        systemTarget = self.systemmodels.system_target.objects.get(target_system_id='testinstanceid')
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

#!/usr/bin/python

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
        from mint.django_rest.rbuilder.inventory import systemdbmgr
        from mint.django_rest.rbuilder.inventory import models as systemmodels
        self.rbuildermodels = rbuildermodels
        self.systemdbmgr = systemdbmgr
        self.systemmodels = systemmodels

    def _unImport(self):
        # "Unimport" anything that was imported so the next test will have a new
        # settings.py.
        for k, v in sys.modules.items():
            if k not in builtins or 'django' in k:
                sys.modules.pop(k)

    def setUp(self):
        self._unImport()
        fixtures.FixturedUnitTest.setUp(self)
        self.db, self.data = self.loadFixture('Empty')
        # Need to prepare settings.py before importing any django modules.
        self.setUpDjangoSettingsModule()
        self.importDjango()

    def tearDown(self):
        self._unImport()
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

    def setUp(self):
        DjangoTest.setUp(self)
        self._data()

    def testLaunchSystem(self):
        self.sdm.launchSystem('testinstanceid', 'aws', 'ec2')
        self.assertEquals(1, len(self.systemmodels.ManagedSystem.objects.all()))
        self.assertEquals(1, len(self.systemmodels.SystemTarget.objects.all()))
        systemTarget = self.systemmodels.SystemTarget.objects.get(targetSystemId='testinstanceid')
        self.assertEquals('testinstanceid', systemTarget.targetSystemId)

    def testSetSystemSSLInfo(self):
        self.sdm.launchSystem('testinstanceid', 'aws', 'ec2')
        self.sdm.setSystemSSLInfo('testinstanceid', '/sslcert', '/sslkey')
        system = self.systemmodels.SystemTarget.objects.get(targetSystemId='testinstanceid')
        self.assertEquals('/sslcert', system.managedSystem.sslClientCertificate)
        self.assertEquals('/sslkey', system.managedSystem.sslClientKey)

    def testGetSystemSSLInfo(self):
        self.sdm.launchSystem('testinstanceid', 'aws', 'ec2')
        self.sdm.setSystemSSLInfo('testinstanceid', '/sslcert', '/sslkey')
        cert, key = self.sdm.getSystemSSLInfo('testinstanceid')
        self.assertEquals('/sslcert', cert)
        self.assertEquals('/sslkey', key)

    def testIsManageable(self):
        self.sdm.launchSystem('testinstanceid', 'aws', 'ec2')
        systemTarget = self.systemmodels.SystemTarget.objects.get(targetSystemId='testinstanceid')
        self.assertTrue(self.sdm.isManageable(systemTarget.managedSystem))

    def _getVersion(self): 
        name = 'group-appliance'
        version = versions.ThawVersion("/foo@bar:baz/1234567890:1-2-3")
        flavor = deps.parseFlavor("is:x86")
        return name, version, flavor

    def testAddSoftwareVersion(self):
        self.sdm.addSoftwareVersion(self._getVersion())
        svs = self.systemmodels.SoftwareVersion.objects.all()
        self.assertEquals(1, len(svs))
        self.assertEquals('group-appliance', svs[0].name)
        self.assertEquals('/foo@bar:baz/1234567890.000:1-2-3', str(svs[0].version))
        self.assertEquals('is: x86', str(svs[0].flavor))
 
    def testGetManagedSystemForInstanceId(self):
        managedSystem = self.sdm.getManagedSystemForInstanceId('testinstanceid')
        self.assertTrue(managedSystem is None)

        self.sdm.launchSystem('testinstanceid', 'aws', 'ec2')
        managedSystem = self.sdm.getManagedSystemForInstanceId('testinstanceid')
        self.assertTrue(isinstance(managedSystem, self.systemmodels.ManagedSystem))
        

    def _setSoftwareVersion(self):
        systemTarget = self.sdm.launchSystem('testinstanceid', 'aws', 'ec2')
        self.sdm.setSoftwareVersionForInstanceId('testinstanceid', [self._getVersion()])
        ssv = self.systemmodels.SystemSoftwareVersion.objects.filter(
                managedSystem=systemTarget.managedSystem)
        return ssv

    def testSetSoftwareVersionForInstanceId(self):
        ssv = self._setSoftwareVersion()
        self.assertEquals(1, len(ssv))

    def testGetSoftwareVersionForInstanceId(self):
        ssv = self._setSoftwareVersion()
        managedSystem = ssv[0].managedSystem
        instanceId = self.systemmodels.SystemTarget.objects.filter(
                        managedSystem=managedSystem)[0].targetSystemId
        vers = self.sdm.getSoftwareVersionsForInstanceId(instanceId)
        self.assertEquals('group-appliance=/foo@bar:baz/1234567890.000:1-2-3[is: x86]',
                str(vers))

    def testDeleteSoftwareVersionsForInstanceId(self):
        ssv = self._setSoftwareVersion()
        managedSystem = ssv[0].managedSystem
        self.sdm.deleteSoftwareVersionsForInstanceId('testinstanceid')
        vers = self.systemmodels.SystemSoftwareVersion.objects.filter(
                managedSystem=managedSystem)
        self.assertEquals(0, len(vers))

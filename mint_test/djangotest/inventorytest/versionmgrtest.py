#!/usr/bin/python

import testsuite

import os
import sys
import time

import testsetup

from testutils import mock

from conary import versions
from conary.deps import deps

from mint_test import djangotest

class VersionMgrTest(djangotest.DjangoTest):

    def setUp(self):
        djangotest.DjangoTest.setUp(self)
        self.setUpData()

    def testSetInstalledSoftwareMockUpdates(self):
        mock.mockMethod(self.mgr.versionMgr.set_available_updates)

        self.assertEquals(len(self.system.installed_software.all()), 0)
        self.mgr.setInstalledSoftware(self.system, [self.trove])
        self.assertEquals(len(self.system.installed_software.all()), 1)
        self.mgr.versionMgr.set_available_updates._mock.assertCalled(self.trove)
        trove = self.system.installed_software.all()[0]
        version = trove.version
        self.assertEquals(trove.name, 'group-clover-appliance')
        self.assertEquals(version.ordering, '1272410162.98')
        self.assertEquals(version.revision, '1-2-1')
        self.assertEquals(version.label, 'clover.eng.rpath.com@rpath:clover-1-devel')
        self.assertEquals(str(version.full), 
            '/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1')
        self.assertEquals(trove.is_top_level, True)

    def testSetInstalledSoftware(self):
        # Mocking
        currentVersion = self.trove2.getVersion()
        currentVersion.versions[-1].timeStamp = 1272410163.98
        findTrovesRet = {(self.trove2.name, currentVersion,
            self.trove2.getFlavor()): [(self.trove2.name, currentVersion,
            self.trove2.getFlavor())]}
        updateVersion = versions.VersionFromString('/conary.rpath.com@rpl:devel/7.2.0-1-1')
        updateVersion.versions[-1].timeStamp = 1272410164.98
        updateVersion2 = versions.VersionFromString('/conary.rpath.com@rpl:devel/7.2.042-1-1')
        updateVersion2.versions[-1].timeStamp = 1272410165.98
        getTroveVersionListRet = {self.trove2.name: \
            {updateVersion: [self.trove2.getFlavor()],
             updateVersion2: [self.trove2.getFlavor()]}}
        self.mgr.versionMgr.cclient = self.mgr.versionMgr.get_conary_client()
        mock.mockMethod(self.mgr.versionMgr.cclient.repos.findTroves, findTrovesRet)
        mock.mockMethod(self.mgr.versionMgr.cclient.repos.getTroveVersionList, getTroveVersionListRet)

        # Set the trove on the system, this should trigger a check for
        # available updates for that trove
        self.mgr.setInstalledSoftware(self.system, [self.trove2])
        
        # Trove should now have 2 available_updates in the db.
        self.assertEquals(2, len(self.trove2.available_updates.all()))

    def setUpData(self):
        version = self.systemmodels.Version()
        version.full = '/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1'
        version.label = 'clover.eng.rpath.com@rpath:clover-1-devel'
        version.ordering = '1272410162.98'
        version.revision = '1-2-1'
        version.flavor = \
            '~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)'
        version.save()

        trove = self.systemmodels.Trove()
        trove.name = 'group-clover-appliance'
        trove.version = version
        trove.flavor = \
            '~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)'
        trove.save()

        version_update = self.systemmodels.Version()
        version_update.full = '/clover.eng.rpath.com@rpath:clover-1-devel/1-3-1'
        version_update.label = 'clover.eng.rpath.com@rpath:clover-1-devel'
        version_update.ordering = '1272410162.98'
        version_update.revision = '1-3-1'
        version_update.flavor = \
            '~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)'
        version_update.save()

        version_update2 = self.systemmodels.Version()
        version_update2.full = '/clover.eng.rpath.com@rpath:clover-1-devel/1-4-1'
        version_update2.label = 'clover.eng.rpath.com@rpath:clover-1-devel'
        version_update2.ordering = '1272410162.98'
        version_update2.revision = '1-4-1'
        version_update2.flavor = \
            '~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)'
        version_update2.save()

        trove.available_updates.add(version_update)
        trove.available_updates.add(version_update2)
        trove.save()

        version2 = self.systemmodels.Version()
        version2.full = '/conary.rpath.com@rpl:devel/7.1.330-1-1'
        version2.label = 'conary.rpath.com@rpl:devel'
        version2.ordering = '1272410163.98'
        version2.flavor = 'desktop is: x86_64'
        version2.revision = '7.1.330-1-1'
        version2.save()

        trove2 = self.systemmodels.Trove()
        trove2.name = 'vim'
        trove2.flavor = 'desktop is: x86_64'
        trove2.version = version2
        trove2.save()

        self.trove = trove
        self.trove2 = trove2

        system = self.systemmodels.System()
        system.name = 'testsystemname'
        system.description = 'testsystemdescription'
        system.local_uuid = 'testsystemlocaluuid'
        system.generated_uuid = 'testsystemgenerateduuid'
        system.ssl_client_certificate = 'testsystemsslclientcertificate'
        system.ssl_client_key = 'testsystemsslclientkey'
        system.ssl_server_certificate = 'testsystemsslservercertificate'
        system.activated = True
        system.current_state = 'activated'
        system.save()

        network = self.systemmodels.Network()
        network.ip_address = '1.1.1.1'
        network.device_name = 'eth0'
        network.public_dns_name = 'testnetwork.example.com'
        network.netmask = '255.255.255.0'
        network.port_type = 'lan'
        network.system = system
        network.save()

        self.system = system


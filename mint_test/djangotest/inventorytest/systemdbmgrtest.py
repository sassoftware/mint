#!/usr/bin/python

import testsuite

import os
import sys
import testsuite
import time

import testsetup

from conary import versions
from conary.deps import deps

from mint_test import djangotest

class SystemDbMgrTest(djangotest.DjangoTest):

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

    @staticmethod
    def _newSystem(**kw):
        kwargs = dict(
                    target_system_id='testinstanceid',
                    target_type='aws', target_name='ec2',
                    launch_date=int(time.time()),
                    scheduled_event_start_date=int(time.time()),
                    available=True,
        )
        kwargs.update(kw)
        return System(**kwargs)

    def _launchSystem(self, **kwargs):
        system = self._newSystem(**kwargs)
        systemTarget = self.sdm.launchSystem(system)
        return system, systemTarget

    def _addSchedule(self, schedule=None, created=None):
        if schedule is None:
            schedule = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
RRULE:FREQ=DAILY
END:VEVENT
END:VCALENDAR"""
        if created is None:
            created = int(time.time())
        return self.sdm.addSchedule(Schedule(schedule=schedule, enabled=True,
            created=created))

    def setUp(self):
        djangotest.DjangoTest.setUp(self)
        self._data()

    def testLaunchSystem(self):
        raise testsuite.SkipTestException("Skipping until inventory integration complete")
        self._launchSystem()
        self.assertEquals(1, len(self.systemmodels.managed_system.objects.all()))
        self.assertEquals(1, len(self.systemmodels.system_target.objects.all()))
        systemTarget = self.systemmodels.system_target.objects.get(target_system_id='testinstanceid')
        self.assertEquals('testinstanceid', systemTarget.target_system_id)

    def testLaunchSystemWithSSLInfo(self):
        raise testsuite.SkipTestException("Skipping until inventory integration complete")
        system, systemTarget = self._launchSystem(
                    ssl_client_certificate='/tmp/client',
                    ssl_client_key='/tmp/key')
        managedSystem = \
            self.systemmodels.system_target.objects.get(target_system_id='testinstanceid').managed_system
        self.assertEquals('/tmp/client', managedSystem.ssl_client_certificate)
        self.assertEquals('/tmp/key', managedSystem.ssl_client_key)

    def testUpdateSystem(self):
        raise testsuite.SkipTestException("Skipping until inventory integration complete")
        system, systemTarget = self._launchSystem()
        system.ssl_client_certificate = '/sslcert'
        system.ssl_client_key = '/sslkey'
        self.sdm.updateSystem(system)
        systemTarget = self.systemmodels.system_target.objects.get(target_system_id='testinstanceid')
        managedSystem = systemTarget.managed_system
        self.assertEquals('/sslcert', managedSystem.ssl_client_certificate)
        self.assertEquals('/sslkey', managedSystem.ssl_client_key)

    def testGetSystemByInstanceId(self):
        raise testsuite.SkipTestException("Skipping until inventory integration complete")
        tmpDir = self.cfg.dataPath
        # Create ssl cert and ssl key
        sslCertFilePath = os.path.join(tmpDir, "sslcert")
        sslKeyFilePath = os.path.join(tmpDir, "sslkey")
        file(sslCertFilePath, "w")
        file(sslKeyFilePath, "w")
        system, systemTarget = self._launchSystem()
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
        raise testsuite.SkipTestException("Skipping until inventory integration complete")
        self._launchSystem()
        systemTarget = self.systemmodels.system_target.objects.get(target_system_id='testinstanceid')
        managedSystem = systemTarget.managed_system
        self.assertTrue(self.sdm.isManageable(managedSystem))

        # Create new user
        newUser = self.rbuildermodels.Users.objects.create(username='testuser2',
            timecreated=str(time.time()), timeaccessed=str(time.time()),
            active=1)
        # Now make the system owned by newUser
        managedSystem = systemTarget.managed_system
        managedSystem.launching_user_id = newUser.userid
        managedSystem.save()
        systemTarget = self.systemmodels.system_target.objects.get(target_system_id='testinstanceid')
        managedSystem = systemTarget.managed_system
        # No longer manageable, since testuser2 has no credentials
        self.assertFalse(self.sdm.isManageable(managedSystem))

        target = self.rbuildermodels.Targets.objects.get(
            targettype='aws', targetname='ec2')
        self.rbuildermodels.TargetUserCredentials(targetid=target,
            userid=newUser, credentials='testusercredentials newUser2').save()

        systemTarget = self.systemmodels.system_target.objects.get(target_system_id='testinstanceid')
        # No longer manageable, since testuser2 has no credentials
        managedSystem = systemTarget.managed_system
        self.assertFalse(self.sdm.isManageable(managedSystem))

        # Update credentials
        cu = self.systemdbmgr.connection.cursor()
        cu.execute("""UPDATE TargetUserCredentials SET credentials = %s
            WHERE targetId = %s AND userId = %s""",
            [ "testusercredentials", target.targetid, newUser.userid ])
        systemTarget = self.systemmodels.system_target.objects.get(target_system_id='testinstanceid')
        # Back to being manageable, same credentials as the current user
        managedSystem = systemTarget.managed_system
        self.assertTrue(self.sdm.isManageable(managedSystem))

    def _getVersion(self): 
        name = 'group-appliance'
        version = versions.ThawVersion("/foo@bar:baz/1234567890:1-2-3")
        flavor = deps.parseFlavor("is:x86")
        return name, version, flavor

    def testAddSoftwareVersion(self):
        raise testsuite.SkipTestException("Skipping until inventory integration complete")
        self.sdm.addSoftwareVersion(self._getVersion())
        svs = self.systemmodels.software_version.objects.all()
        self.assertEquals(1, len(svs))
        self.assertEquals('group-appliance', svs[0].name)
        self.assertEquals('/foo@bar:baz/1234567890.000:1-2-3', str(svs[0].version))
        self.assertEquals('is: x86', str(svs[0].flavor))
 
    def testGetManagedSystemForInstanceId(self):
        raise testsuite.SkipTestException("Skipping until inventory integration complete")
        managedSystem = self.sdm.getManagedSystemForInstanceId('testinstanceid')
        self.assertTrue(managedSystem is None)

        self._launchSystem()
        managedSystem = self.sdm.getManagedSystemForInstanceId('testinstanceid')
        self.assertTrue(isinstance(managedSystem, self.systemmodels.managed_system))
        

    def _setSoftwareVersion(self):
        system, systemTarget = self._launchSystem()
        self.sdm.setSoftwareVersionForInstanceId('testinstanceid', [self._getVersion()])
        managedSystem = systemTarget.managed_system
        ssv = self.systemmodels.system_software_version.objects.filter(
                managed_system=managedSystem)
        return ssv

    def testSetSoftwareVersionForInstanceId(self):
        raise testsuite.SkipTestException("Skipping until inventory integration complete")
        ssv = self._setSoftwareVersion()
        self.assertEquals(1, len(ssv))

    def testGetSoftwareVersionForInstanceId(self):
        raise testsuite.SkipTestException("Skipping until inventory integration complete")
        ssv = self._setSoftwareVersion()
        managedSystem = ssv[0].managed_system
        instanceId = self.systemmodels.system_target.objects.filter(
                        managed_system=managedSystem)[0].target_system_id
        vers = self.sdm.getSoftwareVersionsForInstanceId(instanceId)
        self.assertEquals('group-appliance=/foo@bar:baz/1234567890.000:1-2-3[is: x86]',
                str(vers))

    def testDeleteSoftwareVersionsForInstanceId(self):
        raise testsuite.SkipTestException("Skipping until inventory integration complete")
        ssv = self._setSoftwareVersion()
        managedSystem = ssv[0].managed_system
        self.sdm.deleteSoftwareVersionsForInstanceId('testinstanceid')
        vers = self.systemmodels.system_software_version.objects.filter(
                managed_system=managedSystem)
        self.assertEquals(0, len(vers))

    def testAddSchedule(self):
        raise testsuite.SkipTestException("Skipping until inventory integration complete")
        created1 = int(time.time() + 10)
        created2 = created1 - 5
        self._addSchedule(created=created1)
        self._addSchedule(created=created2)
        sch = self.sdm.getSchedule()
        self.failUnlessEqual(sch.created, created1)

    def testSetScheduledEvents(self):
        raise testsuite.SkipTestException("Skipping until inventory integration complete")
        self._addSchedule()
        system1, targetSystem1 = self._launchSystem(target_system_id='targetInstanceId1')
        evts = self.sdm.getScheduledEvents([system1])
        # We normally get 2 events here, but depending on timing we may only
        # get one (we're creating events 2 days in advance starting with the
        # registration time)
        self.failUnless(len(evts) >= 1)

        system2, targetSystem2 = self._launchSystem(target_system_id='targetInstanceId2')
        self.sdm.computeScheduledEvents([system1, system2])
        evts = self.sdm.getScheduledEvents([system1, system2])
        self.failUnlessEqual(set(x.managed_system.id for x in evts),
            set([targetSystem1.managed_system.id,
            targetSystem2.managed_system.id]))

if __name__ == "__main__":
        testsetup.main()

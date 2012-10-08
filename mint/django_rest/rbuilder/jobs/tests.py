#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from lxml import etree

from mint.django_rest.test_utils import XMLTestCase, RepeaterMixIn

from mint.django_rest.rbuilder.jobs import models
from mint.django_rest.rbuilder.jobs import testsxml
from mint.django_rest.rbuilder.inventory import models as invmodels

from xobj import xobj

class BaseJobsTest(XMLTestCase):
    def _mock(self):
        pass

    def setUp(self):
        XMLTestCase.setUp(self)
        self._mock()

        eventUuid1 = 'eventuuid001'
        jobUuid1 = 'rmakeuuid001'
        eventUuid2 = 'eventuuid002'
        jobUuid2 = 'rmakeuuid002'
        eventUuid3 = 'eventuuid003'
        jobUuid3 = 'rmakeuuid003'
        system = self._saveSystem()

        user = self.getUser('testuser')
        self.job1 = self._newSystemJob(system, eventUuid1, jobUuid1,
            models.EventType.SYSTEM_REGISTRATION, createdBy=user)
        self.job2 = self._newSystemJob(system, eventUuid2, jobUuid2,
            models.EventType.SYSTEM_UPDATE, createdBy=user)

        self.system = system

class CacheTest(XMLTestCase):
    "Simple test for the caching module"
    def testInvalidateCache(self):
        Cache = models.modellib.Cache
        # Populate the cache
        jt1 = Cache.get(models.EventType, name=models.EventType.SYSTEM_REGISTRATION)
        # Add new job type
        jt2 = models.EventType.objects.create(name='fake',
            description='fakefake', priority=1)
        jt3 = Cache.get(models.EventType, name='fake')
        self.failUnlessEqual(jt2.job_type_id, jt3.job_type_id)

class JobsTestCase(BaseJobsTest):

    def _mock(self):
        models.Job.getRmakeJob = self.mockGetRmakeJob

    def mockGetRmakeJob(self):
        self.mockGetRmakeJob_called = True

    def testGetJobs(self):
        response = self._get('jobs/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.jobs_xml)

    def testGetJobsSortBySyntheticFields(self):
        response = self._get('jobs/?order_by=job_description')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.jobs_xml.replace('order_by=""',
                'order_by="job_description"'))

    def testGetJobStates(self):
        response = self._get('job_states/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.job_states_xml)

    def testGetJob(self):
        response = self._get('jobs/rmakeuuid001/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.job_xml)

    def testGetJobState(self):
        response = self._get('job_states/1/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.job_state_xml)

    def testGetSystemJobs(self):
        response = self._get('inventory/systems/%s/jobs/' % \
            self.system.pk, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.systems_jobs_xml)

    def testUpdateJob(self):
        jobUuid = 'jobUuid1'
        jobToken = 'jobToken1'
        job = self._newJob(jobUuid, jobToken=jobToken,
            jobType=models.EventType.TARGET_REFRESH_IMAGES)

        jobXml = """
<job>
  <job_status>Completed</job_status>
  <status_code>200</status_code>
  <status_text>Some status here</status_text>
  <results encoding="identity">
    <images>
      <image id="id1">
        <imageId>id1</imageId>
      </image>
      <image id="id2">
        <imageId>id2</imageId>
      </image>
    </images>
  </results>
</job>
"""
        response = self._put('jobs/%s' % jobUuid, jobXml,
            jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.job.id, "http://testserver/api/v1/jobs/%s" % job.job_uuid)

class Jobs2TestCase(BaseJobsTest):
    def _mock(self):
        class DummyStatus(object):
            def __init__(slf, **kwargs):
                slf.__dict__.update(kwargs)
        class DummyJob(object):
            def __init__(slf, job_uuid, code, text, detail, final, completed, failed):
                slf.job_uuid = job_uuid
                slf.status = DummyStatus(code=code, text=text, detail=detail,
                    final=final, completed=completed, failed=failed)
        class Dummy(object):
            data = dict(
                rmakeuuid001 = (101, "text 101", "detail 101", False,
                    False, False),
                rmakeuuid002 = (202, "text 202", "detail 202", True,
                    True, False),
                rmakeuuid003 = (404, "text 404", "detail 404", True,
                    False, True),
            )
            @staticmethod
            def mockGetRmakeJob(slf):
                jobUuid = slf.job_uuid
                code, text, detail, final, completed, failed = Dummy.data[jobUuid]
                j = DummyJob(jobUuid, code, text, detail, final, completed, failed)
                return j
        self.mock(models.Job, 'getRmakeJob', Dummy.mockGetRmakeJob)

    def testGetJobs(self):
        # Mark job2 as succeeded, to make sure the status doesn't get updated
        # from the rmake job again (this is a stretch)
        completedState = models.JobState.objects.get(name=models.JobState.COMPLETED)
        self.job2.job_state = completedState
        self.job2.status_code = 299
        self.job2.status_text = "text 299"
        self.job2.status_detail = "no such luck"
        self.job2.save()

        response = self._get('jobs/')
        self.assertEquals(response.status_code, 200)

        obj = xobj.parse(response.content)
        jobs = obj.jobs.job

        self.failUnlessEqual([ str(x.job_state) for x in jobs ],
            [models.JobState.RUNNING, models.JobState.COMPLETED])

        self.failUnlessEqual([ int(x.status_code) for x in jobs ],
            [100, 299])
        self.failUnlessEqual([ x.status_text for x in jobs ],
            ["Initializing", "text 299"])

class JobCreationTest(BaseJobsTest, RepeaterMixIn):
    def _mock(self):
        RepeaterMixIn.setUpRepeaterClient(self)
        from mint.django_rest.rbuilder.inventory.manager import repeatermgr
        self.mock(repeatermgr.RepeaterManager, 'repeaterClient',
            self.mgr.repeaterMgr.repeaterClient)

    def testCreateJob(self):
        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/19"/>
  <descriptor id="http://testserver/api/v1/target_types/6/descriptor_create_target"/>
  <descriptor_data>
    <alias>newbie</alias>
    <description>Brand new cloud</description>
    <name>newbie.eng.rpath.com</name>
    <zone>Local rBuilder</zone>
  </descriptor_data>
</job>
"""
        response = self._post('jobs', jobXml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id, "http://testserver/api/v1/target_types/6/descriptor_create_target")

        dbjob = models.Job.objects.get(job_uuid=job.job_uuid)
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target_type.name for x in dbjob.jobtargettype_set.all() ],
            [ 'xen-enterprise' ],
        )

    def testCreateJobSystemScan(self):
        topLevelGroup = "group-foo=/a@b:c/1-2-3"
        jobType = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_SCAN)
        system = self._saveSystem()
        system.save()
        invmodels.SystemDesiredTopLevelItem.objects.create(
            system=system, trove_spec=topLevelGroup)
        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/inventory/systems/%(systemId)s/descriptors/survey_scan"/>
  <descriptor_data/>
</job>
""" % dict(jobTypeId=jobType.job_type_id, systemId=system.system_id)

        response = self._post('jobs', jobXml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/inventory/systems/%s/descriptors/survey_scan" % system.system_id)

        repClient = self.mgr.repeaterMgr.repeaterClient
        cimParams = repClient.CimParams
        resLoc = repClient.ResultsLocation

        callList = repClient.getCallList()

        eventUuids = [ x.args[0].pop('eventUuid') for x in callList ]

        dbjob = models.Job.objects.get(job_uuid=job.job_uuid)
        # Make sure the job is related to the system
        self.failUnlessEqual(
            [ (x.system_id, x.event_uuid) for x in dbjob.systems.all() ],
            [ (system.system_id, eventUuids[0]) ],
        )



        self.failUnlessEqual(callList,
            [
                ('survey_scan_cim',
                    (
                        cimParams(**{'targetType': None, 'instanceId': None, 'targetName': None, 'port': 5989, 'host': u'1.1.1.1', 'launchWaitTime': 1200, 'clientKey': u'testsystemsslclientkey', 'requiredNetwork': None, 'clientCert': u'testsystemsslclientcertificate'}),

                    ),
                    dict(
                        desiredTopLevelItems = [u'group-foo=/a@b:c/1-2-3'],
                        zone=system.managing_zone.name,
                        uuid=job.job_uuid,
                    ),
                ),
            ])

        # We should have a running job
        system = invmodels.System.objects.get(system_id=system.system_id)
        self.assertEquals(system.has_running_jobs, True)

        # same deal with wmi

        system.management_interface = self.mgr.wmiManagementInterface()
        system.save()

        response = self._post('jobs', jobXml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/inventory/systems/%s/descriptors/survey_scan" % system.system_id)

        callList = repClient.getCallList()
        eventUuids = [ x.args[0].pop('eventUuid') for x in callList[1:] ]

        dbjob = models.Job.objects.get(job_uuid=job.job_uuid)

        # Make sure the job is related to the system
        self.failUnlessEqual(
            [ (x.system_id, x.event_uuid) for x in dbjob.systems.all() ],
            [ (system.system_id, eventUuids[0]) ]
        )

        repClient = self.mgr.repeaterMgr.repeaterClient
        cimParams = repClient.CimParams
        resLoc = repClient.ResultsLocation

        # Ignore cim one
        self.failUnlessEqual(len(callList), 2)

        wmiParams = repClient.WmiParams

        self.failUnlessEqual(callList[1:],
            [
                ('survey_scan_wmi',
                    (
                        wmiParams(**{'port': 5989, 'host': u'1.1.1.1', 'requiredNetwork': None,}),

                    ),
                    dict(
                        desiredTopLevelItems = [u'group-foo=/a@b:c/1-2-3'],
                        zone=system.managing_zone.name,
                        uuid=job.job_uuid,
                    ),
                ),
            ])

        # ssh interface should fail

        system.management_interface = self.mgr.sshManagementInterface()
        system.save()

        response = self._post('jobs', jobXml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 400)
        self.assertXMLEquals(response.content, """
<fault><code>400</code><message>Unsupported management interface</message><traceback></traceback></fault>""")

    def testJobSystemScanResults(self):
        jobType = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_SCAN)
        system = self._saveSystem()
        system.save()

        # No jobs running
        system = invmodels.System.objects.get(system_id=system.system_id)
        self.assertEquals(system.has_running_jobs, False)

        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/inventory/systems/%(systemId)s/descriptors/survey_scan"/>
  <descriptor_data/>
</job>
""" % dict(jobTypeId=jobType.job_type_id, systemId=system.system_id)

        response = self._post('jobs', jobXml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/inventory/systems/%s/descriptors/survey_scan" % system.system_id)

        # We should have a running job
        system = invmodels.System.objects.get(system_id=system.system_id)
        self.assertEquals(system.has_running_jobs, True)

        dbjob = models.Job.objects.get(job_uuid=job.job_uuid)

        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Done</status_text>
  <results>
    <surveys>
      <survey>
        <uuid>aa-bb-cc-dd</uuid>
        <config_properties/>
        <desired_properties/>
        <observed_properties/>
        <discovered_properties/>
        <validation_report/>
        <rpm_packages/>
        <conary_packages/>
        <services/>
      </survey>
    </surveys>
  </results>
</job>
"""

        # Grab token
        jobToken = dbjob.job_token
        jobUrl = "jobs/%s" % dbjob.job_uuid
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        # print response.content
        job = obj.job
        self.failUnlessEqual(job.job_uuid, dbjob.job_uuid)

        # Make sure the job is related to the survey
        self.failUnlessEqual(
            [ x.survey.uuid for x in dbjob.created_surveys.all() ],
            [ 'aa-bb-cc-dd' ]
        )

        # #2337 - make sure active flags are not set
        dbsystem = system.__class__.objects.get(system_id=system.system_id)
        self.assertEquals(bool(dbsystem.has_active_jobs), False)
        self.assertEquals(bool(dbsystem.has_running_jobs), False)

    def testCreateJobSystemConfigApply(self):
        jobType = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_CONFIGURE)
        system = self._saveSystem()
        system.configuration = "<configuration><blah>1</blah></configuration>"
        system.save()

        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/inventory/systems/%(systemId)s/descriptors/configure"/>
  <descriptor_data/>
</job>
""" % dict(jobTypeId=jobType.job_type_id, systemId=system.system_id)

        url = 'inventory/systems/%s/jobs' % system.system_id
        response = self._post(url, jobXml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/inventory/systems/%s/descriptors/configure" % system.system_id)

        repClient = self.mgr.repeaterMgr.repeaterClient
        cimParams = repClient.CimParams
        resLoc = repClient.ResultsLocation

        callList = repClient.getCallList()

        eventUuids = [ x.args[0].pop('eventUuid') for x in callList ]

        dbjob = models.Job.objects.get(job_uuid=job.job_uuid)
        # Make sure the job is related to the system
        self.failUnlessEqual(
            [ (x.system_id, x.event_uuid) for x in dbjob.systems.all() ],
            [ (system.system_id, eventUuids[0]) ],
        )



        self.failUnlessEqual(callList,
            [
                ('configuration_cim',
                    (
                        cimParams(**{'targetType': None, 'instanceId': None, 'targetName': None, 'port': 5989, 'host': u'1.1.1.1', 'launchWaitTime': 1200, 'clientKey': u'testsystemsslclientkey', 'requiredNetwork': None, 'clientCert': u'testsystemsslclientcertificate'}),

                    ),
                    dict(
                        configuration = system.configuration,
                        zone=system.managing_zone.name,
                        uuid=job.job_uuid,
                    ),
                ),
            ])

        # We should have a running job
        system = invmodels.System.objects.get(system_id=system.system_id)
        self.assertEquals(system.has_running_jobs, True)

        # Get rid of the cim job, leave only the wmi one
        dbjob.delete()
        system.updateDerivedData()

        system = invmodels.System.objects.get(system_id=system.system_id)
        self.assertEquals(system.has_running_jobs, False)

        # same deal with wmi

        system.management_interface = self.mgr.wmiManagementInterface()
        system.save()

        response = self._post(url, jobXml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/inventory/systems/%s/descriptors/configure" % system.system_id)

        callList = repClient.getCallList()
        eventUuids = [ x.args[0].pop('eventUuid') for x in callList[1:] ]

        dbjob = models.Job.objects.get(job_uuid=job.job_uuid)

        # Make sure the job is related to the system
        self.failUnlessEqual(
            [ (x.system_id, x.event_uuid) for x in dbjob.systems.all() ],
            [ (system.system_id, eventUuids[0]) ]
        )

        repClient = self.mgr.repeaterMgr.repeaterClient
        wmiParams = repClient.WmiParams
        resLoc = repClient.ResultsLocation

        # Ignore cim one
        self.failUnlessEqual(len(callList), 2)

        self.failUnlessEqual(callList[1:],
            [
                ('configuration_wmi',
                    (
                        wmiParams(**{'port': 5989, 'host': u'1.1.1.1', 'requiredNetwork': None,}),

                    ),
                    dict(
                        configuration = system.configuration,
                        zone=system.managing_zone.name,
                        uuid=job.job_uuid,
                    ),
                ),
            ])

        # We should have a running job
        system = invmodels.System.objects.get(system_id=system.system_id)
        self.assertEquals(system.has_running_jobs, True)

        # ssh interface should fail

        system.management_interface = self.mgr.sshManagementInterface()
        system.save()

        response = self._post(url, jobXml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 400)
        self.assertXMLEquals(response.content, """
<fault><code>400</code><message>Unsupported management interface</message><traceback></traceback></fault>""")

        dbjob = models.Job.objects.get(job_uuid=job.job_uuid)

        dbsystem = system.__class__.objects.get(system_id=system.system_id)
        self.assertEquals(bool(dbsystem.has_active_jobs), True)
        self.assertEquals(bool(dbsystem.has_running_jobs), True)
        # System needs to apply configuration
        self.assertEquals(bool(dbsystem.configuration_applied), False)

        stdout = """
<configurators>
  <write_status>
    <errors>
      <config_error-b9812828-0d6a-11e2-a354-005056b40871>
        <name>config_error-b9812828-0d6a-11e2-a354-005056b40871</name>
        <error_list>
          <error>
            <code>0</code>
            <detail>Stdout = \nStderr = \nReturnCode = 0\n</detail>
            <message>httpd-config.sh</message>
          </error>
        </error_list>
      </config_error-b9812828-0d6a-11e2-a354-005056b40871>
    </errors>
    <status>success</status>
  </write_status>
</configurators>
"""

        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Done</status_text>
  <results>
    <system>
      <scriptOutput>
        <returnCode>0</returnCode>
        <stdout><![CDATA[%s]]></stdout>
        <stderr>[2012-10-03 10:57:55.023-0400] [INFO] (client) Running command: configurator
[2012-10-03 10:57:55.027-0400] [WARNING] (client) Can't import dmidecode, falling back to dmidecode command.
[2012-10-03 10:57:55.035-0400] [WARNING] (client) Can't use dmidecode command, falling back to mac address
[2012-10-03 10:57:55.037-0400] [INFO] (client) Attempting to run configurators on 303a3530-3a35-363a-6234-3a30383a3731
[2012-10-03 10:58:00.460-0400] [INFO] (client) Configurators succeeded
[2012-10-03 10:58:00.464-0400] [INFO] (client) Command finished: configurator
</stderr>
      </scriptOutput>
    </system>
  </results>
</job>
""" % stdout

        # Grab token
        jobToken = dbjob.job_token
        jobUrl = "jobs/%s" % dbjob.job_uuid
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        # print response.content
        job = obj.job
        self.failUnlessEqual(job.job_uuid, dbjob.job_uuid)

        # #2337 - make sure active flags are not set
        dbsystem = system.__class__.objects.get(system_id=system.system_id)
        self.assertEquals(bool(dbsystem.has_active_jobs), False)
        self.assertEquals(bool(dbsystem.has_running_jobs), False)

        # System should have the config applied
        self.assertEquals(bool(dbsystem.configuration_applied), True)

        # Verify status_text and status_detail
        self.assertEquals(job.status_text, 'Done')
        dbjob = models.Job.objects.get(job_uuid=dbjob.job_uuid)
        self.assertXMLEquals(dbjob.status_detail, stdout)

        # Now pretend we have an error
        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Done</status_text>
  <results>
    <system>
      <scriptOutput>
        <returnCode>1</returnCode>
        <stdout><![CDATA[%s]]></stdout>
        <stderr>SPLOSION
Some more errors here
</stderr>
      </scriptOutput>
    </system>
  </results>
</job>
""" % stdout

        # Grab token
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        # print response.content
        job = obj.job
        self.failUnlessEqual(job.job_uuid, dbjob.job_uuid)

        self.assertEquals(job.status_text, 'SPLOSION\nSome more errors here\n')
        dbjob = models.Job.objects.get(job_uuid=dbjob.job_uuid)
        self.assertXMLEquals(dbjob.status_detail, stdout)

    def _makeSystem(self):
        system = self._saveSystem()
        system.save()
        invmodels.SystemDesiredTopLevelItem.objects.create(
            system=system, trove_spec='group-fake=/fake.rpath.com@rpath:fake-0/1234.000:0-0-0[]')
        url = "inventory/systems/%(systemId)s/descriptors/update" % dict(
            systemId=system.system_id)
        response = self._get(url,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)

        tree = etree.fromstring(response.content)
        nsmap = dict(dsc='http://www.rpath.com/permanent/descriptor-1.1.xsd')
        fieldNames = tree.xpath('/dsc:descriptor/dsc:dataFields/dsc:field/dsc:name/text()',
            namespaces=nsmap)
        self.assertEquals(fieldNames, ['trove_label', 'dry_run', ])

        return system


    def _createUpdateXml(self, systemId, topLevelGroup, dryRun):
        jobType = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_UPDATE)
        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/inventory/systems/%(systemId)s/descriptors/update"/>
  <descriptor_data>
    <trove_label>%(topLevelGroup)s</trove_label>
    <dry_run>%(dryRun)s</dry_run>
  </descriptor_data>
</job>
""" % dict(jobTypeId=jobType.job_type_id, systemId=systemId,
            topLevelGroup=topLevelGroup, dryRun=dryRun)

        return jobXml

    def _postJob(self, jobXml, systemId):
        url = "inventory/systems/%(systemId)s/jobs" % dict(
            systemId=systemId)
        response = self._post(url, jobXml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/inventory/systems/%s/descriptors/update" % systemId)

        return job

    def _confirmRmakePost(self, payload, dbjob):
        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Done</status_text>
  <results>
    %s
  </results>
</job>
""" % payload

        # Grab token, pretend to be rMake putting CIM job results back to mint.
        jobToken = dbjob.job_token
        jobUrl = "jobs/%s" % dbjob.job_uuid
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.job_uuid, dbjob.job_uuid)

        # Make sure the job is related to the survey
        self.assertXMLEquals(
            dbjob.created_previews.all()[0].preview,
            "<?xml version='1.0' encoding='UTF-8'?>%s" % payload,
            ignoreNodes=['desired', 'observed']
        )

    def _fetchPreviewResponseContent(self, payload, dbjob):
        # Fetch the job
        jobUrl = "jobs/%s" % dbjob.job_uuid
        response = self._get(jobUrl)
        self.assertEquals(response.status_code, 200)

        tree = etree.fromstring(response.content)
        resources = tree.xpath('/job/created_resources')
        self.assertXMLEquals(etree.tostring(resources[0]),
            '<created_resources><preview id="http://testserver/api/v1/inventory/previews/1"/>\n</created_resources>')

        # Make sure we can fetch the preview
        url = "inventory/previews/1"
        response = self._get(url, username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(
            response.content,
            payload,
            ignoreNodes=['desired', 'observed'])

        return response.content

    def _testJobSystemSoftwareUpdate(self, topLevelGroup, payload, dryRun=False):
        system = self._makeSystem()

        jobXml = self._createUpdateXml(system.system_id, topLevelGroup, str(dryRun).lower())
        job = self._postJob(jobXml, system.system_id)

        dbjob = models.Job.objects.get(job_uuid=job.job_uuid)

        self._confirmRmakePost(payload, dbjob)

        content = self._fetchPreviewResponseContent(payload, dbjob)

        system = system.__class__.objects.get(system_id=system.system_id)
        return system, content

    def testJobSystemSoftwareUpdateWithPreview(self):
        old = "group-fake=/fake.rpath.com@rpath:fake-0/1234.000:0-0-0[]"
        new = "group-fake=/fake.rpath.com@rpath:fake-1/1357.000:2-0-0[]"
        payload = """
<preview>
  <conary_package_changes>
    <conary_package_change>
      <type>changed</type>
      <from_conary_package>
        <name>group-fake</name>
        <version>group-fake=/fake.rpath.com@rpath:fake-0/1234.000:0-0-0</version>
      </from_conary_package>
      <to_conary_package>
        <name>group-fake</name>
        <version>group-fake=/fake.rpath.com@rpath:fake-1/1357.000:2-0-0</version>
      </to_conary_package>
    </conary_package_change>
  </conary_package_changes>
  <observed>%(old)s</observed>
  <desired>%(new)s</desired>
</preview>""" % locals()
        system, content = self._testJobSystemSoftwareUpdate(new, payload, dryRun=True)

        observed = xobj.parse(content).preview.observed
        topLevelItems = sorted(x.trove_spec for x in system.desired_top_level_items.all())
        self.assertEquals(topLevelItems, [ old ])

        # Confirm <observed> is still on original version in accordance with dryRun=True.
        frum = getattr(xobj.parse(payload).preview.conary_package_changes.conary_package_change, 'from_conary_package')
        f_ver = getattr(frum, 'version')
        self.assertEquals(observed, f_ver + '[]')

    def testJobSystemSoftwareUpdateWithUpdate(self):
        old = "group-fake=/fake.rpath.com@rpath:fake-0/1234.000:0-0-0[]"
        new = "group-fake=/fake.rpath.com@rpath:fake-1/1357.000:2-0-0[]"
        payload = """
<preview>
  <conary_package_changes>
    <conary_package_change>
      <type>changed</type>
      <from_conary_package>
        <name>group-fake</name>
        <version>group-fake=/fake.rpath.com@rpath:fake-0/1234.000:0-0-0</version>
      </from_conary_package>
      <to_conary_package>
        <name>group-fake</name>
        <version>group-fake=/fake.rpath.com@rpath:fake-1/1357.000:2-0-0</version>
      </to_conary_package>
    </conary_package_change>
  </conary_package_changes>
  <observed>%(new)s</observed>
  <desired>%(new)s</desired>
</preview>""" % locals()
        system, content = self._testJobSystemSoftwareUpdate(new, payload, dryRun=False)

        observed = xobj.parse(content).preview.observed
        topLevelItems = sorted(x.trove_spec for x in system.desired_top_level_items.all())

        self.assertEquals(topLevelItems, [ new ])

        # Confirm <observed> is now on desired version in accordance with dryRun=False.
        to = getattr(xobj.parse(payload).preview.conary_package_changes.conary_package_change, 'to_conary_package')
        t_ver = getattr(to, 'version')
        self.assertEquals(observed, t_ver + '[]')

#     def testJobSystemSoftwareUpdateWithAddedPackage(self):
#         topLevelGroup = "group-foo=example.com@rpath:42/1-2-3"

#         payload = """
# <preview>
#   <conary_package_changes>
#     <conary_package_change>
#       <type>changed</type>
#       <from_conary_package>
#         <name>group-foo</name>
#         <version>/example.com@rpath:42/1-2-3</version>
#       </from_conary_package>
#       <to_conary_package>
#         <name>group-foo</name>
#         <version>/example.com@rpath:42/4-5-6</version>
#       </to_conary_package>
#     </conary_package_change>
#   </conary_package_changes>
# </preview>"""
#         return self._testJobSystemSoftwareUpdate(topLevelGroup, payload, dryRun=False)


import base64
import cPickle
import os
import random
from lxml import etree
from xobj import xobj
from datetime import datetime, timedelta

from smartform import descriptor

from django.contrib.redirects import models as redirectmodels
from django.db import connection, transaction
from django.template import TemplateDoesNotExist

from mint.django_rest import timeutils
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.manager import rbuildermanager
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory import survey_models
from mint.django_rest.rbuilder.inventory import zones as zmodels
from mint.django_rest.rbuilder.targets import models as targetmodels
from mint.django_rest.rbuilder.jobs import models as jobmodels
from mint.django_rest.rbuilder.inventory import testsxml
from mint.django_rest.rbuilder.inventory import testsxml2
from mint.django_rest.rbuilder.projects import models as projectmodels
from mint.lib import x509
from mint.rest.api import models as restmodels

# Suppress all non critical msg's from output
# still emits traceback for failed tests
import logging
logging.disable(logging.CRITICAL)

from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

class AuthTests(XMLTestCase):
    def testAuthRCE1341(self):
        password = "password with 'weird :chars"
        response = self._get('inventory/log/', username="test-rce1341",
            password=password)
        self.assertEquals(response.status_code, 200)

        # Now pretend it's an external user
        from mint.django_rest.rbuilder.users import models as usermodels
        u = usermodels.User.objects.get(user_name='test-rce1341')
        u.update(passwd=None)

        # Capture the requested password
        class MockAuthClient(object):
            def __init__(slf):
                slf.args = []
            def checkPassword(slf, username, password):
                slf.args.append((username, password))
                return True
        authClient = MockAuthClient()
        from mint.lib import auth_client
        self.mock(auth_client, 'getClient', lambda *args: authClient)

        response = self._get('inventory/log/', username="test-rce1341",
            password=password)
        self.assertEquals(response.status_code, 200)

        self.assertEquals(authClient.args, [('test-rce1341', password)])

class SurveyTests(XMLTestCase):
    fixtures = ['users']

    def setUp(self):
        XMLTestCase.setUp(self)

    def _makeSurvey(self, system=None, created_date=None, removable=True):
        if system is None:
            system = self._makeSystem()

        uuid = str(self.uuid4())
        user = usersmodels.User.objects.get(user_name='JeanValjean1')
        survey = survey_models.Survey(
            name='x', uuid=uuid, system=system, created_by=user,
            modified_by=user, removable=removable)
        survey.save()

        if created_date is not None:
            survey.created_date = created_date
            survey.save()

        return survey

    def _makeSystem(self):
        zone = self._saveZone()
        sys = self.newSystem(name="blinky", description="ghost")
        sys.managing_zone=zone
        sys.save()
        return sys

    def _hiturl(self, url):
        response = self._get(url,
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)

    def test_survey_serialization(self):
        survey = self._makeSurvey()
        tag1 = survey_models.SurveyTag(
            survey = survey,
            name = 'needs_review'
        )
        tag1.save()
        rpm_package = survey_models.RpmPackageInfo(
            name = 'asdf', epoch = 0, version = '5',
            release = '6', architecture = 'x86_64',
            description = 'enterprise middleware abstraction layer',
            signature = 'X'
        )
        rpm_package.save()
        conary_package = survey_models.ConaryPackageInfo(
            name = 'jkl', version = '7', flavor = 'orange',
            description = 'Type-R', revision = '8',
            architecture = 'ia64', signature = 'X',
            rpm_package_info = rpm_package
        )
        conary_package.save()
        scp = survey_models.SurveyConaryPackage(
            survey = survey,
            conary_package_info = conary_package,
            install_date=self.mgr.sysMgr.now(),
        )
        scp.save()
        srp = survey_models.SurveyRpmPackage(
            survey = survey, rpm_package_info = rpm_package,
            install_date=self.mgr.sysMgr.now(),
        )
        srp.save()
        service = survey_models.ServiceInfo(
            name = 'httpd', autostart = True, runlevels = '3,4,5'
        )
        service.save()
        iss = survey_models.SurveyService(
            survey = survey, service_info = service,
            status = 'is maybe doing stuff'
        )
        iss.save()
        response = self._get("inventory/surveys/%s" % survey.uuid,
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        # this is an incomplete test as the survey didn't actually post
        # self.assertXMLEquals(response.content, testsxml.survey_output_xml, ignoreNodes=['created_date','install_date','modified_date'])

        url = "inventory/systems/%s/surveys" % survey.system.pk
        response = self._get(url, username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.surveys_xml % {'uuid': survey.uuid})

    def test_survey_serialization_windows(self):

        survey = self._makeSurvey()
        tag1 = survey_models.SurveyTag(
            survey = survey,
            name = 'needs_review'
        )
        tag1.save()
        windows_package = survey_models.WindowsPackageInfo(
            publisher    = 'konami',
            product_code = 'up-up-down-down',
            package_code = 'left-right-right-left',
            product_name = 'contra',
            type         = 'msi',
            upgrade_code = 'B-A-B-A select-start',
            version      = '1.0'
        )
        windows_package.save()

        windows_patch = survey_models.WindowsPatchInfo(
            display_name  = 'Add Internet Multiplayer',
            uninstallable = True,
            patch_code    = 'up-c-down-c-left-c-right-c',
            product_code  = 'up-a-down-a-left-a-right-a',
            transforms    = 'bubblebee,starscream'
        )

        windows_patch.save()
        windows_patch_info = survey_models.WindowsPatchInfo.objects.get(display_name='Add Internet Multiplayer')
        windows_package_info = survey_models.WindowsPackageInfo.objects.get(product_name='contra')
        windows_patch_info.save()
        windows_patch_link = survey_models.SurveyWindowsPatchPackageLink(
            windows_patch_info   = windows_patch_info,
            windows_package_info = windows_package_info
        )
        windows_patch_link.save()
        spackage = survey_models.SurveyWindowsPackage(
            survey = survey,
            windows_package_info = windows_package_info,
            install_source='e:/path/to/stuff',
            local_package='c:/path/to/stuff',
            install_date=self.mgr.sysMgr.now(),
        )
        spackage.save()
        spatch = survey_models.SurveyWindowsPatch(
            survey = survey,
            windows_patch_info = windows_patch_info,
            local_package='d:/path/to/stuff',
            is_installed=True,
            install_date=self.mgr.sysMgr.now(),
        )
        spatch.save()
        service = survey_models.WindowsServiceInfo(
            name = 'minesweeper',
            display_name='minesweeper',
            type = 'AcmeService32',
            handle = 'AcmeServiceHandle',
            _required_services = 'solitaire',
        )
        service.save()
        service2 = survey_models.WindowsServiceInfo(
            name = 'solitaire',
            display_name='solitare',
            type = 'AcmeService32',
            handle = 'AcmeServiceHandle',
            _required_services = '',
        )
        service2.save()
        iss = survey_models.SurveyWindowsService(
            survey = survey, windows_service_info = service,
            status = 'running',
        )
        iss.save()
        iss2 = survey_models.SurveyWindowsService(
            survey = survey, windows_service_info = service2,
            status = 'stopped',
        )
        iss2.save()
        response = self._get("inventory/surveys/%s" % survey.uuid,
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)

    def test_survey_post(self):

        # make sure we can post a survey and it mostly looks
        # like the model saved version above -- much of the
        # data posted is not required for input (like hrefs)
        sys = self._makeSystem()
        # No top leve items initially
        self.assertEquals(sys.desired_top_level_items.count(), 0)
        url = "inventory/systems/%s/surveys" % sys.pk

        response = self._post(url,
            data = testsxml.survey_input_xml % {'uuid': str(self.uuid4())},
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)

        # Make sure the system has a system model
        system = models.System.objects.get(system_id=sys.system_id)
        self.assertEquals(system.latest_survey.has_system_model, True)
        self.assertEquals(system.latest_survey.system_model, """\
search group-haystack=haystack.rpath.com@rpath:haystack-1/1-1-1
install group-haystack
install needle
""")
        self.assertEquals(str(system.latest_survey.system_model_modified_date),
            "2009-02-13 23:31:30+00:00")

        # We should have top level items
        self.assertEquals(sorted(x.trove_spec
            for x in sys.desired_top_level_items.all()),
            ['jkl=7[orange]'])

        # Config and Update actions should be disabled
        system_url = url = "inventory/systems/%s" % system.system_id
        response = self._get(url,
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        tree = etree.fromstring(response.content)
        actionsStatus = tree.xpath('/system/actions/action[name="Apply system configuration"]/enabled')
        self.assertEqual([x.text for x in actionsStatus], [ 'false' ])
        updateStatus = tree.xpath('/system/actions/action[name="Update Software"]/enabled')
        self.assertEqual([x.text for x in updateStatus], [ 'false' ])

        # Hack last survey to pretend it doesn't have a system model
        survey_models.Survey.objects.filter(survey_id=system.latest_survey.survey_id).update(has_system_model=False, system_model=None, system_model_modified_date=None)
        system.__class__.objects.filter(system_id=system.system_id).update(configuration="<foo>value</foo>")

        # Config and Update actions should now be enabled
        response = self._get(url,
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        tree = etree.fromstring(response.content)
        actionsStatus = tree.xpath('/system/actions/action[name="Apply system configuration"]/enabled')
        self.assertEqual([x.text for x in actionsStatus], [ 'true' ])
        updateStatus = tree.xpath('/system/actions/action[name="Update Software"]/enabled')
        self.assertEqual([x.text for x in updateStatus], [ 'true' ])

        response = self._get(url,
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)

        url = "inventory/surveys/1234"
        response = self._get(url,
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        # self.assertXMLEquals(response.content, testsxml.survey_output_xml)
        # make sure inline urls work
        self._hiturl("inventory/survey_tags/1")
        self._hiturl("inventory/survey_rpm_packages/1")
        self._hiturl("inventory/survey_conary_packages/1")
        self._hiturl("inventory/survey_services/1")
        self._hiturl("inventory/rpm_package_info/1")
        self._hiturl("inventory/conary_package_info/1")
        self._hiturl("inventory/service_info/1")

        url = "inventory/surveys/1234"
        response = self._put(url,
            data = testsxml.survey_mod_xml,
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        surv = survey_models.Survey.objects.get(uuid='1234')
        self.assertEqual(surv.removable, True) # Bug 2209

        # post a second survey to verify that updating the latest survey
        # info still works and see if the latest survey date matches
        response = self._put("inventory/surveys/1234",
            data = testsxml.survey_input_xml % {'uuid': str(self.uuid4())},
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        sys = models.System.objects.get(pk=sys.pk)
        self.assertTrue(sys.latest_survey.created_date is not None)

        # not included yet only because IDs don't line up?
        #self.assertXMLEquals(response.content, testsxml.survey_output_xml2)

        # post an alternate survey, primarily for checking config and compliance diffs
        # other parts of diffs will be checked in other tests, this one just has
        # all the config parts populated so it makes sense here
        response = self._post("inventory/systems/%s/surveys" % sys.pk,
            data = testsxml.survey_input_xml_alt.replace('jkl', 'group-klm'),
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)
 
        # Top-level item should not have changed
        topLevelItemMgr = models.SystemDesiredTopLevelItem.objects
        self.assertEquals(sorted(x.trove_spec
                for x in topLevelItemMgr.filter(system=sys)),
            ['jkl=7[orange]'])

        response = self._get("inventory/surveys/1234/diffs/99999",
            username = 'admin', password='password')
        self.assertEqual(response.status_code, 200)

        # delete the system, make sure nothing explodes
        response = self._delete("inventory/systems/%s" % sys.pk,
            username='admin', password='password')
        self.assertEqual(response.status_code, 204)

    def test_survey_post_long(self):
        sys = self._makeSystem()
        url = "inventory/systems/%s/surveys" % sys.pk
        response = self._post(url,
            data = testsxml2.very_long_survey,
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)

    def test_survey_post_windows(self):
        sys = self._makeSystem()
        url = "inventory/systems/%s/surveys" % sys.pk
        response = self._post(url,
            data = testsxml2.windows_upload_survey_xml,
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)

        self._hiturl('inventory/survey_windows_patches/1')
        self._hiturl('inventory/survey_windows_os_patches/1')
        self._hiturl('inventory/windows_patch_info/1')
        self._hiturl('inventory/windows_package_info/1')
        self._hiturl('inventory/survey_windows_packages/1')
        self._hiturl('inventory/survey_windows_services/2')
        self._hiturl('inventory/windows_service_info/1')

        response = self._post(url,
            data = testsxml2.windows_upload_survey_xml2,
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        
        # BOOKMARK
        # test complex query against surveys
        search = '/api/v1/inventory/systems;filter_by=EQUAL(latest_survey.windows_packages.windows_package_info.publisher,konami)'
        response = self._get(search, username='admin', password='password')
        self.assertEqual(response.status_code, 200)
       


        url = "inventory/surveys/%s/diffs/%s" % ('123456789', '987654321')
        response = self._get(url, username='admin', password='password')
        self.assertEqual(response.status_code, 200)

        url = "inventory/systems/%s/surveys" % sys.pk
        response = self._post(url,
            data = testsxml2.windows_upload_survey_xml3,
            username='admin', password='password')
        self.assertEqual(response.status_code, 200)

        url = "inventory/surveys/%s/diffs/%s" % ('123456789', '555')
        response = self._get(url, username='admin', password='password')
        self.assertEqual(response.status_code, 200)

    def test_survey_diff_linux_heavy(self):

        sys = self._makeSystem()
        url = "inventory/systems/%s/surveys" % sys.pk

        surveys = [ testsxml2.one, testsxml2.two, testsxml2.three,
            testsxml2.four, testsxml2.five ]

        for x in surveys:
            response = self._post(url,
                data = x,
                username='admin', password='password')
            self.assertEqual(response.status_code, 200)

        url = "inventory/surveys/%s/diffs/%s" % ('504', '505')
        # TODO: time this
        response = self._get(url, username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        # hit it again to test cached diff logic
        response = self._get(url, username='admin', password='password')
        self.assertEqual(response.status_code, 200)

        url = "inventory/surveys/%s/diffs/%s" % ('503', '501')
        response = self._get(url, username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        sys = models.System.objects.get(pk=sys.pk)
        key1 = sys.latest_survey.pk

        # verify we can delete the survey
        url = "inventory/surveys/%s" % '505'
        response = self._delete(url, username='admin', password='password')
        self.assertEqual(response.status_code, 204)
        # verify system did not cascade
        # and that since we deleted teh latest survey there is still a latest
        # survey
        surl = "inventory/systems/%s" % sys.pk
        response = self._get(surl, username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        sys = models.System.objects.get(pk=sys.pk)
        key2 = sys.latest_survey.pk
        self.assertTrue(key1 != key2)

        # verify delete stuck
        response = self._get(url, username='admin', password='password')
        self.assertEqual(response.status_code, 404)
        # check 404 support for survey not existing, second delete
        response = self._delete(url, username='admin', password='password')
        self.assertEqual(response.status_code, 404)

        # delete the system, make sure nothing explodes
        response = self._delete("inventory/systems/%s" % sys.pk,
            username='admin', password='password')
        self.assertEqual(response.status_code, 204)

    def testPostSystemWithSurvey(self):
        """
        Make sure a system can provide a survey at registration time
        """
        models.System.objects.all().delete()
        system_xml = testsxml.system_post_xml.replace("</system>",
            testsxml2.two + "\n</system>")
        response = self._post('inventory/systems/', data=system_xml)
        self.assertEquals(response.status_code, 200)
        doc = xobj.parse(response.content)
        systemId = doc.system.system_id
        # Make sure we got a survey
        system = models.System.objects.get(system_id=systemId)
        self.assertEquals(system.surveys.count(), 1)

    def testSurveysAreRemovableByDefault(self):
        survey = self._makeSurvey()
        self.assertTrue(survey.removable)

    def testDoNotPurgeLatestOrUnremovableSurveys(self):
        sys = self._makeSystem()
        unremovable1 = self._makeSurvey(removable=False, system=sys)
        unremovable2 = self._makeSurvey(removable=False, system=sys)
        latest = self._makeSurvey(removable=True, system=sys)
        deleted = self.mgr.deleteRemovableSurveys(olderThanDays=0)
        remaining = survey_models.Survey.objects.all()
        self.assertEqual(0, len(deleted))
        self.assertEqual(3, len(remaining))
        self.assertIn(unremovable1, remaining)
        self.assertIn(unremovable2, remaining)
        self.assertIn(latest, remaining)

    def testDoNotPurgeRecentSurveys(self):
        sys = self._makeSystem()
        removable1 = self._makeSurvey(system=sys)
        removable2 = self._makeSurvey(system=sys)
        removable3 = self._makeSurvey(system=sys)
        deleted = self.mgr.deleteRemovableSurveys(olderThanDays=30)
        remaining = survey_models.Survey.objects.all()
        self.assertEqual(0, len(deleted))
        self.assertEqual(3, len(remaining))
        self.assertIn(removable1, remaining)
        self.assertIn(removable2, remaining)
        self.assertIn(removable3, remaining)

    def testPurgeAllOldRemovableSurveysUnlessLatestForSystem(self):
        present = datetime.now()
        past = present - timedelta(days=60)

        sys1 = self._makeSystem()
        old_unremovable1 = self._makeSurvey(system=sys1, created_date=past,
                                            removable=False)
        old_removable1 = self._makeSurvey(system=sys1, created_date=past)
        recent_removable1 = self._makeSurvey(system=sys1, created_date=present)
        latest_removable1 = self._makeSurvey(system=sys1, created_date=present)

        sys2 = self._makeSystem()
        old_removable2a = self._makeSurvey(system=sys2, created_date=past)
        old_removable2b = self._makeSurvey(system=sys2, created_date=past)
        latest_unremovable2 = self._makeSurvey(system=sys2,
                                               created_date=present,
                                               removable=False)

        deleted = self.mgr.deleteRemovableSurveys(olderThanDays=30)
        self.assertEqual(3, len(deleted))
        self.assertIn(old_removable1, deleted)
        self.assertIn(old_removable2a, deleted)
        self.assertIn(old_removable2b, deleted)

        remaining = survey_models.Survey.objects.all()
        self.assertEqual(4, len(remaining))
        self.assertIn(old_unremovable1, remaining)
        self.assertIn(recent_removable1, remaining)
        self.assertIn(latest_removable1, remaining)
        self.assertIn(latest_unremovable2, remaining)


class AssimilatorTestCase(XMLTestCase, test_utils.SmartformMixIn):
    '''
    This tests actions as well as the assimilator.  See if we can list the jobs on
    a system, get the descriptor for spawning that job, and whether we can actually
    start that job.  note: rpath-repeater is mocked, so that will return successful
    job XML even if parameters are insufficient.
    '''

    def setUp(self):
        # make a new system, get ids to use when spawning job
        XMLTestCase.setUp(self)
        self.system = self.newSystem(name="blinky", description="ghost")
        self.system.management_interface = models.ManagementInterface.objects.get(name='ssh')
        self.mgr.addSystem(self.system)
        self.assimilate = jobmodels.EventType.SYSTEM_ASSIMILATE
        self.event_type = jobmodels.EventType.objects.get(name=self.assimilate)
        self.type_id  = self.event_type.pk
        self.system.save()

        # system needs  a network
        network = models.Network()
        network.dns_name = 'testnetwork.example.com'
        network.system = self.system
        network.save()
        self.system.networks.add(network)
        # system.save not required
        self.system = models.System.objects.get(pk=self.system.pk)
        self.assertTrue(self.mgr.sysMgr.getSystemHasHostInfo(self.system))
        self.setUpSchemaDir()

    def testExpectedActions(self):
        # do we see assimilate as a possible action?
        response = self._get('inventory/systems/%s' % self.system.pk, username="admin",
            password="password")
        obj = xobj.parse(response.content)
        # xobj hack: obj doesn't listify 1 element lists
        # don't break tests if there is only 1 action
        actions = obj.system.actions.action
        if not isinstance(actions, list):
           actions = [actions]
        self.assertTrue(len(actions) == 5)

    def testFetchActionsDescriptor(self):
        descriptorTestData = [
            ('assimilation', 'System Assimilation', 'System Assimilation'),
            ('survey_scan', 'System Scan', 'System Scan'),
        ]
        for descriptorType, descrName, descrDescr in descriptorTestData:
            # can we determine what smartform we need to populate?
            url = "inventory/systems/%s/descriptors/%s" % (self.system.pk, descriptorType)
            response = self._get(url, username="admin", password="password")
            self.failUnlessEqual(response.status_code, 200)
            obj = xobj.parse(response.content)
            self.failUnlessEqual(obj.descriptor.metadata.displayName, descrName)
            self.failUnlessEqual(obj.descriptor.metadata.descriptions.desc, descrDescr)
            # make sure the same works with parameters
            url = "inventory/systems/%s/descriptors/%s?foo=bar" % (self.system.pk,
                descriptorType)
            response = self._get(url, username="admin", password="password")
            self.failUnlessEqual(response.status_code, 200)
            obj = xobj.parse(response.content)
            self.failUnlessEqual(obj.descriptor.metadata.displayName, descrName)
            self.failUnlessEqual(obj.descriptor.metadata.descriptions.desc, descrDescr)

    def testSpawnAction(self):
        # can we launch the job>?
        # first make sure SSH managemnet interface credentials are set
        self.assertTrue(self.mgr.sysMgr.getSystemHasHostInfo(self.system))
        response = self._post('inventory/systems/%s/credentials' % \
            self.system.pk,
            data=testsxml.ssh_credentials_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        # now post a barebones job to the systems jobs collection
        url = "inventory/systems/%s/jobs/" % (self.system.pk)
        response = self._post(url, testsxml.system_assimilator_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.system_event.event_type.id,
            'http://testserver/api/v1/inventory/event_types/12')

class InventoryTestCase(XMLTestCase):

    def testGetTypes(self):
        response = self._get('inventory/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.inventory_xml)

        response = self._post('inventory/?_method=GET')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.inventory_xml)

    def testPostTypes(self):
        response = self._post('inventory/')
        self.assertEquals(response.status_code, 405)

    def notestPutTypes(self):
        response = self._put('inventory/')
        self.assertEquals(response.status_code, 405)

    def testDeleteTypes(self):
        response = self._delete('inventory/')
        self.assertEquals(response.status_code, 405)

    def testGetTypesNoTrailingSlash(self):
        response = self._get('inventory')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.inventory_xml)

        response = self._post('inventory?_method=GET')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.inventory_xml)

class LogTestCase(XMLTestCase):

    def testGetLogAuth(self):
        """
        Ensure requires auth but not admin
        """
        response = self._get('inventory/log/')
        self.assertEquals(response.status_code, 401)

        response = self._get('inventory/log/', username="testuser",
            password="password")
        self.assertEquals(response.status_code, 200)

    def testGetLog(self):
        system = self.newSystem(name="mgoblue",
            description="best appliance ever")
        self.mgr.addSystem(system)
        system = self.newSystem(name="mgoblue2",
            description="best appliance ever2")
        self.mgr.addSystem(system)
        system = self.newSystem(name="mgoblue3",
            description="best appliance ever3")
        self.mgr.addSystem(system)
        response = self._get('inventory/log/', username="testuser",
            password="password")
        # unsure of what correct log XML should actually be
        #self.assertXMLEquals(response.content, testsxml.systems_log_xml,
        #    ignoreNodes = [ 'entry_date' ])

class ZonesTestCase(XMLTestCase):

    def testGetZones(self):
        zmodels.Zone.objects.all().delete()
        zone = self._saveZone()
        # Create a system, just for kicks
        system = self.newSystem(name="foo", managing_zone=zone)
        system.save()
        response = self._get('inventory/zones/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.zones_xml % (zone.created_date.isoformat()),
            ignoreNodes = [ 'created_date', 'created_by', 'modified_by', 'modified_date' ])

    def testGetZoneAuth(self):
        """
        Ensure requires auth but not admin
        """
        self._saveZone()
        response = self._get('inventory/zones/2/')
        self.assertEquals(response.status_code, 401)

        response = self._get('inventory/zones/2/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetZone(self):
        zmodels.Zone.objects.all().delete()
        zone = self._saveZone()
        response = self._get('inventory/zones/2/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.zone_xml % (zone.created_date.isoformat()),
            ignoreNodes = [ 'created_date', 'created_by', 'modified_by', 'modified_date', 'latest_survey' ])

    def testAddZoneNodeNull(self):

        try:
            self.mgr.addZone(None)
        except:
            assert(False) # should not throw exception

    def testAddZone(self):
        zone = self._saveZone()
        new_zone = self.mgr.addZone(zone)
        assert(new_zone is not None)

    def testPostZoneAuth(self):
        """
        Ensure we require admin to post zones
        """
        response = self._post('inventory/zones/',
            data= testsxml.zone_post_xml)
        self.assertEquals(response.status_code, 401)

        response = self._post('inventory/zones/',
            data=testsxml.zone_post_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)

    def testPostZone(self):
        zmodels.Zone.objects.all().delete()
        xml = testsxml.zone_post_xml
        response = self._post('inventory/zones/',
            data=xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        zone = zmodels.Zone.objects.get(pk=2)
        self.assertXMLEquals(response.content, testsxml.zone_post_response_xml % \
            (zone.created_date.isoformat()))

        # test posting a second zone https://issues.rpath.com/browse/RBL-7229
        response = self._post('inventory/zones/',
            data=testsxml.zone_post_2_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        zones = zmodels.Zone.objects.all()
        self.assertTrue(len(zones) == 2)

    def testPutZoneAuth(self):
        """
        Ensure we require admin to put zones
        """
        zone = zmodels.Zone.objects.get(pk=1)
        response = self._put('inventory/zones/1/',
            data=testsxml.zone_put_xml % zone.created_date)
        self.assertEquals(response.status_code, 401)

        response = self._put('inventory/zones/1/',
            data=testsxml.zone_put_xml % zone.created_date,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)

    def testPutZoneNotFound(self):
        """
        Ensure we return 404 if we update zone that doesn't exist
        """
        zone = zmodels.Zone.objects.get(pk=1)
        try:
            response = self._put('inventory/zones/1zcvxzvzgvsdzfewrew4t4tga34/',
                data=testsxml.zone_put_xml % zone.created_date,
                username="testuser", password="password")
            self.assertEquals(response.status_code, 404)
        except TemplateDoesNotExist, e:
            # might not have template, so check for 404 in error
            self.assertTrue("404" in str(e))

    def testPutZone(self):
        zmodels.Zone.objects.all().delete()
        zone = self._saveZone()
        response = self._put('inventory/zones/%d/' % zone.zone_id,
            data=testsxml.zone_put_xml % zone.created_date, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        zone = zmodels.Zone.objects.get(pk=zone.zone_id)
        self.assertTrue(zone.name == "zoneputname")
        self.assertTrue(zone.description == "zoneputdesc")

    def testDeleteZoneAuth(self):
        """
        Ensure we require admin to delete zones
        """
        response = self._delete('inventory/zones/1/')
        self.assertEquals(response.status_code, 401)

        response = self._delete('inventory/zones/1/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)

    def testDeleteZone(self):
        """
        Ensure we can delete zones
        """
        zmodels.Zone.objects.all().delete()
        self._saveZone()
        response = self._delete('inventory/zones/2/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 204)
        try:
            zmodels.Zone.objects.get(pk=1)
            self.fail("Lookup should have failed due to deletion")
        except zmodels.Zone.DoesNotExist:
            pass # what we expect

class ManagementInterfacesTestCase(XMLTestCase):
    def testGetManagementInterfaces(self):
        models.ManagementInterface.objects.all().delete()
        mi = models.ManagementInterface(name="foo", description="bar", port=8000, credentials_descriptor="<foo/>")
        mi.save()
        response = self._get('inventory/management_interfaces/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.management_interfaces_xml, ignoreNodes = [ 'created_date', 'modified_by', 'created_by', 'modified_date', 'latest_survey' ])

    def testGetManagementInterfacesAuth(self):
        """
        Don't require auth or admin
        """
        response = self._get('inventory/management_interfaces/')
        self.assertEquals(response.status_code, 200)

        response = self._get('inventory/management_interfaces/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetManagementInterface(self):
        models.ManagementInterface.objects.all().delete()
        mi = models.ManagementInterface(name="foo", description="bar", port=8000, credentials_descriptor="<foo/>")
        mi.save()
        response = self._get('inventory/management_interfaces/%s/' % mi.pk,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.management_interface_xml, ignoreNodes = [ 'created_date', 'modified_by', 'created_by', 'modified_date', 'latest_survey' ])

    def testPutManagementInterfaceAuth(self):
        """
        Ensure we require admin to put
        """
        response = self._put('inventory/management_interfaces/1/',
            data=testsxml.management_interface_put_xml)
        self.assertEquals(response.status_code, 401)

        response = self._put('inventory/management_interfaces/1/',
            data=testsxml.management_interface_put_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)

    def testPutManagementInterfaceNotFound(self):
        """
        Ensure we return 404 if we update one that doesn't exist
        """
        try:
            response = self._put('inventory/management_interfaces/1zcvxzvzgvsdzfewrew4t4tga34/',
                data=testsxml.management_interface_put_xml,
                username="admin", password="password")
            self.assertEquals(response.status_code, 404)
        except TemplateDoesNotExist, e:
            # might not have template, so check for 404 in error
            self.assertTrue("404" in str(e))

    def testPutManagementInterface(self):
        models.ManagementInterface.objects.all().delete()
        mi = models.ManagementInterface(name="foo2", description="bar", port=8000, credentials_descriptor="<foo/>")
        mi.save()
        self.assertTrue('<name>thisnameshouldnotstick</name>' in testsxml.management_interface_put_xml)
        response = self._put('inventory/management_interfaces/4',
            data=testsxml.management_interface_put_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        mi = models.ManagementInterface.objects.get(pk=mi.pk)
        # name is read only, should not get changed
        self.assertTrue(mi.name != "thisnameshouldnotstick")
        self.failUnlessEqual(mi.port, 123)
        self.failUnlessEqual(mi.credentials_descriptor, "<foo/>")

class SystemTypesTestCase(XMLTestCase):

    def testGetSystemTypes(self):
        models.SystemType.objects.all().delete()
        si = models.SystemType(name="foo", description="bar", creation_descriptor="<foo></foo>")
        si.save()
        response = self._get('inventory/system_types/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.system_types_xml, ignoreNodes = [ 'created_date', 'modified_date', 'created_by', 'modified_by', 'latest_survey' ])

    def testGetSystemTypesAuth(self):
        """
        Ensure requires correct auth but is wide open otherwise
        """
        response = self._get('inventory/system_types/',
            username='baduser', password='badpass')
        self.assertEquals(response.status_code, 401)

        response = self._get('inventory/system_types/')
        self.assertEquals(response.status_code, 200)

        response = self._get('inventory/system_types/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetSystemType(self):
        models.SystemType.objects.all().delete()
        si = models.SystemType(name="foo", description="bar", creation_descriptor="<foo></foo>")
        si.save()
        response = self._get('inventory/system_types/%s/' % si.pk,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.system_type_xml, ignoreNodes = [ 'created_date', 'created_by', 'modified_by', 'modified_date', 'latest_survey' ])

    def testGetSystemTypeSystems(self):
        system = self._saveSystem()
        response = self._get('inventory/system_types/%d/systems/' % \
            system.system_type.system_type_id,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_type_systems_xml,
            ignoreNodes = [ 'created_date', 'actions',  'created_by', 'modified_by', 'modified_date', 'latest_survey'])

    def testPutSystemTypeAuth(self):
        """
        Ensure we require admin to put
        """
        response = self._put('inventory/system_types/1/',
            data=testsxml.system_types_put_xml)
        self.assertEquals(response.status_code, 401)

        response = self._put('inventory/system_types/1/',
            data=testsxml.system_types_put_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)

    def XXXtestPutSystemTypes(self):
        """
        Skipping this test for now, there are problems with PUT support and
        APIReadOnly fields of which name on SystemType is.
        """
        models.SystemType.objects.all().delete()
        si = models.SystemType(name="foo", description="bar", creation_descriptor="<foo></foo>")
        si.save()
        self.assertTrue('<name>thisnameshouldnotstick</name>' in testsxml.system_types_put_xml)
        response = self._put('inventory/system_types/1',
            data=testsxml.system_types_put_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        si = models.SystemType.objects.get(pk=si.pk)
        # name is read only, should not get changed
        self.assertTrue(si.name != "thisnameshouldnotstick")
        self.assertTrue(si.infrastructure == True)

    def testAddWindowsBuildService(self):
        system = self.mgr.sysMgr.addWindowsBuildService("myname", "mydesc", "1.1.1.1")
        network = self.mgr.sysMgr.extractNetworkToUse(system)
        assert(system.name =="myname")
        assert(system.description == "mydesc")
        assert(system.system_type.name == models.SystemType.INFRASTRUCTURE_WINDOWS_BUILD_NODE)
        assert(network.dns_name == "1.1.1.1")

    def testGetWindowsBuildServiceNodes(self):
        models.SystemType.objects.all().delete()
        models.SystemType.objects.all().delete()
        st = models.SystemType(name=models.SystemType.INFRASTRUCTURE_WINDOWS_BUILD_NODE,
            description=models.SystemType.INFRASTRUCTURE_WINDOWS_BUILD_NODE_DESC, infrastructure=True,
            creation_descriptor="<foo></foo>")
        st.save()
        system = models.System()
        system.name = 'testsystemname'
        system.description = 'testsystemdescription'
        system.managing_zone = self.localZone
        system.management_interface = models.ManagementInterface.objects.get(pk=1)
        system.system_type = st
        system.save()

        network = models.Network()
        network.ip_address = '1.1.1.1'
        network.device_name = 'eth0'
        network.dns_name = 'testnetwork.example.com'
        network.netmask = '255.255.255.0'
        network.port_type = 'lan'
        network.system = system
        network.save()

        st2 = models.SystemType(name=models.SystemType.INVENTORY,
            description=models.SystemType.INVENTORY_DESC, infrastructure=True,
            creation_descriptor="<foo></foo>")
        st2.save()

        system2 = models.System()
        system2.name = 'testsystemname2'
        system2.description = 'testsystemdescription2'
        system2.managing_zone = self.localZone
        system2.management_interface = models.ManagementInterface.objects.get(pk=1)
        system2.st = st2
        system2.save()

        buildNodes = self.mgr.sysMgr.getWindowsBuildServiceNodes()
        assert(len(buildNodes) == 1)
        assert(buildNodes[0].system_id == system.system_id)

    def testGetWindowsBuildServiceNodesEmpty(self):
        models.SystemType.objects.all().delete()
        models.SystemType.objects.all().delete()

        buildNodes = self.mgr.sysMgr.getWindowsBuildServiceNodes()
        assert(buildNodes is not None)
        assert(len(buildNodes) == 0)

class SystemStatesTestCase(XMLTestCase):

    def testGetSystemStates(self):
        response = self._get('inventory/system_states/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_states_xml,
            ignoreNodes = [ 'created_date' ])

    def testGetSystemState(self):
        response = self._get('inventory/system_states/1/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_state_xml,
            ignoreNodes = [ 'created_date' ])

class NetworkTestCase(XMLTestCase):

    def testGetNetworks(self):
        models.System.objects.all().delete()
        self._saveSystem()
        response = self._get('inventory/networks/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.networks_xml, ignoreNodes = [ 'created_date' ])

    def testGetNetworkAuth(self):
        """
        Ensure requires auth but not admin
        """
        self._saveSystem()
        response = self._get('inventory/networks/1/')
        self.assertEquals(response.status_code, 401)

        response = self._get('inventory/networks/1/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testPutNetworkAuth(self):
        """
        Ensure we require admin to put zones
        """
        response = self._put('inventory/networks/1/',
            data= testsxml.network_put_xml)
        self.assertEquals(response.status_code, 401)

        response = self._put('inventory/networks/1/',
            data=testsxml.network_put_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)

    def testPutNetworkLocalIp(self):
        """
        Ensure Network models are not saved if pointing to link-local IPs.
        """
        models.System.objects.all().delete()
        self._saveSystem()
        old_count = models.Network.objects.count()
        self._put('inventory/networks/1/',
                  data=testsxml.network_put_xml_opt_ip_addr % "169.254.4.4",
                  username="admin", password="password")
        self.assertEquals(old_count, models.Network.objects.count())

        self._put('inventory/networks/1/',
                  data=testsxml.network_put_xml_opt_ip_addr % "4.4.4.4",
                  username="admin", password="password")
        self.assertEquals(old_count + 1, models.Network.objects.count())

    def testPutNetworkNotFound(self):
        """
        Ensure we return 404 if we update network that doesn't exist
        """
        try:
            response = self._put('inventory/networks/1zcvxzvzgvsdzfewrew4t4tga34/',
                data=testsxml.network_put_xml,
                username="testuser", password="password")
            self.assertEquals(response.status_code, 404)
        except TemplateDoesNotExist, e:
            # might not have template, so check for 404 in error
            self.assertTrue("404" in str(e))

    def testPutNetwork(self):
        models.System.objects.all().delete()
        self._saveSystem()
        response = self._put('inventory/networks/2/',
            data=testsxml.network_put_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        network = models.Network.objects.get(pk=2)
        self.assertTrue(network.dns_name == "new.com")
        self.assertTrue(network.ip_address == "2.2.2.2")

    def testDeleteNetworkAuth(self):
        """
        Ensure we require admin to put zones
        """
        response = self._delete('inventory/networks/1/')
        self.assertEquals(response.status_code, 401)

        response = self._delete('inventory/networks/1/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)

    def testDeleteNetwork(self):
        models.System.objects.all().delete()
        self._saveSystem()
        network = models.Network.objects.get(pk=2)
        self.assertTrue(network is not None)
        response = self._delete('inventory/networks/2/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 204)
        try:
            network = models.Network.objects.get(pk=1)
            self.assertTrue(False) # should have been deleted
        except models.Network.DoesNotExist:
            pass  #expected

    def testGetNetwork(self):
        models.System.objects.all().delete()
        self._saveSystem()
        response = self._get('inventory/networks/2/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.network_xml, ignoreNodes = [ 'created_date' ])

class ManagementNodesTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)
        models.ManagementNode.objects.all().delete()

    def testManagementNodeSave(self):
        zone = self._saveZone()
        # make sure state gets set to unmanaged
        management_node = models.ManagementNode(name="mgoblue",
            description="best node ever", zone=zone, managing_zone=zone)
        _eq = self.failUnlessEqual
        _eq(management_node.current_state_id, None)
        management_node.save()
        _eq(management_node.current_state.name, models.SystemState.UNMANAGED)

        # make sure we honor the state if set though
        management_node = models.ManagementNode(name="mgoblue", zone=zone,
            description="best node ever",
            current_state=self.mgr.sysMgr.systemState(models.SystemState.DEAD),
            managing_zone=zone)
        management_node.save()
        _eq(management_node.current_state.name, models.SystemState.DEAD)

    # -----------------
    def testGetManagementNodes(self):
        management_node = self._saveManagementNode()
        response = self._get('inventory/management_nodes/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.management_nodes_xml % (management_node.networks.all()[0].created_date.isoformat(),
                                             management_node.current_state.created_date.isoformat(),
                                             management_node.created_date.isoformat()))

    def testPutManagementNodes(self):
        lz = zmodels.Zone.LOCAL_ZONE
        management_node0 = self._saveManagementNode(zoneName=lz)
        self._saveManagementNode(idx=1, zoneName=lz)
        dataTempl = """
<management_nodes>
%s
</management_nodes>"""

        nodeTempl = """<management_node>
<node_jid>%s</node_jid>
<zone_name>%s</zone_name>
</management_node>
"""

        nodeTempl = """<management_node>
<hostname>boo!</hostname>
<node_jid>%(jid)s</node_jid>
<local>%(local)s</local>
<zone><name>%(zoneName)s</name></zone>
<networks><network><ip_address>%(ipAddress)s</ip_address><dns_name>%(ipAddress)s</dns_name><device_name>eth0</device_name></network></networks>
</management_node>
"""


        # Old node in new zone
        # Make sure we don't overwrite the IP address
        nodes = [ dict(jid=management_node0.node_jid, zoneName='new zone 0',
            ipAddress='2.2.2.210', local=False) ]
        # New node in old zone
        nodes.append(dict(jid='node1@host1/node1', zoneName=lz,
            ipAddress='2.2.2.3', local=True))
        # New node in new zone
        nodes.append(dict(jid='node2@host2/node2', zoneName='new zone 2',
            ipAddress='2.2.2.4', local=False))
        # management_node1 is gone

        data = dataTempl % ''.join(nodeTempl % x for x in nodes)
        # First, check that we enforce localhost auth
        response = self._put('inventory/management_nodes',
            headers={'X-rPath-Repeater' : 'does not matter'},
            data=data)
        self.failUnlessEqual(response.status_code, 403)

        # Now a valid PUT
        response = self._put('inventory/management_nodes',
            data=data)
        self.failUnlessEqual(response.status_code, 200)

        obj = xobj.parse(response.content)
        nodes = obj.management_nodes.management_node
        zone0 = zmodels.Zone.objects.get(name='new zone 0')
        zone2 = zmodels.Zone.objects.get(name='new zone 2')
        exp = [(management_node0.node_jid, zone0.zone_id, 'false',
                'test management node', zone0.zone_id,),
            # RBL-7703: this should go away
            ('node01@rbuilder.rpath', management_node0.zone_id, 'true',
                'test management node 01', management_node0.zone_id,),
            ('node1@host1/node1', management_node0.zone_id, 'true',
                'boo!', management_node0.zone_id,),
            ('node2@host2/node2', zone2.zone_id, 'false',
                'boo!', zone2.zone_id,)
        ]
        self.failUnlessEqual(
            [ (str(x.node_jid), int(os.path.basename(x.zone.id)),
                    str(x.local), str(x.name),
                    int(os.path.basename(x.managing_zone.id)))
                for x in nodes ],
            exp)

        node = models.ManagementNode.objects.get(pk=management_node0)
        self.failUnlessEqual(
            [ x.ip_address for x in node.networks.all() ],
            [ '2.2.2.210' ])

        node = models.ManagementNode.objects.get(node_jid='node1@host1/node1')
        self.failUnlessEqual(
            [ x.ip_address for x in node.networks.all() ],
            [ '2.2.2.3' ])

    def testGetManagementNodeAuth(self):
        """
        Ensure requires auth but not admin
        """
        node = self._saveManagementNode()
        response = self._get('inventory/management_nodes/%s/' % node.system_ptr_id)
        self.assertEquals(response.status_code, 401)

        response = self._get('inventory/management_nodes/%s/' % node.system_ptr_id,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetManagementNode(self):
        management_node = self._saveManagementNode()
        response = self._get('inventory/management_nodes/%s/' % management_node.system_ptr_id,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.management_node_xml % (management_node.networks.all()[0].created_date.isoformat(),
                                            management_node.current_state.created_date.isoformat(),
                                            management_node.created_date.isoformat()))

    def testAddManagementNode(self):
        management_node = self._saveManagementNode()
        new_management_node = self.mgr.addManagementNode(management_node)
        assert(new_management_node is not None)
        assert(new_management_node.local)
        type = models.SystemType.objects.get(name = models.SystemType.INFRASTRUCTURE_MANAGEMENT_NODE)
        assert(new_management_node.type == type)

    def testPostManagementNodeAuth(self):
        """
        Ensure requires admin
        """
        models.ManagementNode.objects.all().delete()
        self._saveZone()
        response = self._post('inventory/management_nodes/',
            data=testsxml.management_node_post_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 401)

        response = self._post('inventory/management_nodes/',
            data=testsxml.management_node_post_xml, content_type='text/xml',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)

        response = self._post('inventory/management_nodes/',
            data=testsxml.management_node_post_xml, content_type='text/xml',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

    def testPostManagementNode(self):
        models.ManagementNode.objects.all().delete()
        self._saveZone()
        xml = testsxml.management_node_post_xml
        response = self._post('inventory/management_nodes/',
            data=xml, content_type='text/xml', username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        management_node = models.ManagementNode.objects.get(pk=3)
        management_node_xml = testsxml.management_node_post_response_xml.replace(
            '<registration_date/>',
            '<registration_date>%s</registration_date>' % \
            (management_node.registration_date.isoformat()))
        self.assertXMLEquals(response.content, management_node_xml % \
            (management_node.networks.all()[0].created_date.isoformat(),
             management_node.current_state.created_date.isoformat(),
             management_node.created_date.isoformat()))

    def testGetManagementNodesForZone(self):
        management_node = self._saveManagementNode()
        response = self._get('inventory/zones/%d/management_nodes/' % management_node.zone.zone_id,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.management_nodes_xml % (management_node.networks.all()[0].created_date.isoformat(),
                                             management_node.current_state.created_date.isoformat(),
                                             management_node.created_date.isoformat()))

    def testGetManagementNodeForZoneAuth(self):
        """
        Ensure quires auth but not admin
        """
        management_node = self._saveManagementNode()
        response = self._get('inventory/zones/%d/management_nodes/%s/' % (
            management_node.zone.zone_id, management_node.system_ptr_id))
        self.assertEquals(response.status_code, 401)

        response = self._get('inventory/zones/%d/management_nodes/%s/' % (
            management_node.zone.zone_id, management_node.system_ptr_id),
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetManagementNodeForZone(self):
        management_node = self._saveManagementNode()
        response = self._get('inventory/zones/%d/management_nodes/%s/' % (
            management_node.zone.zone_id, management_node.system_ptr_id),
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.management_node_xml % (management_node.networks.all()[0].created_date.isoformat(),
                                            management_node.current_state.created_date.isoformat(),
                                            management_node.created_date.isoformat()))

    def testAddManagementNodeForZoneNull(self):

        try:
            # create the system
            managementNode = None
            self.mgr.addManagementNodeForZone(None, managementNode)
        except:
            assert(False) # should not throw exception

    def testAddManagementNodeForZone(self):
        management_node = self._saveManagementNode()
        new_management_node = self.mgr.addManagementNodeForZone(management_node.zone.zone_id, management_node)
        assert(new_management_node is not None)
        assert(new_management_node.local)
        assert(management_node.type == models.SystemType.objects.get(
            name = models.SystemType.INFRASTRUCTURE_MANAGEMENT_NODE))

    def testAddManagementNodeSave(self):
        management_node = self._saveManagementNode()
        management_node.system_type = models.SystemType.objects.get(
            name = models.SystemType.INVENTORY)
        # now save, which should automatically set management_node
        management_node.save()
        assert(management_node.system_type == models.SystemType.objects.get(
            name = models.SystemType.INFRASTRUCTURE_MANAGEMENT_NODE))

    def testPostManagementNodeForZoneAuth(self):
        """
        Ensure requires admin
        """
        models.ManagementNode.objects.all().delete()
        zone = self._saveZone()
        response = self._post('inventory/zones/%d/management_nodes/' % zone.zone_id,
            data=testsxml.management_node_zone_post_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 401)

        response = self._post('inventory/zones/%d/management_nodes/' % zone.zone_id,
            data=testsxml.management_node_zone_post_xml, content_type='text/xml',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)

        response = self._post('inventory/zones/%d/management_nodes/' % zone.zone_id,
            data=testsxml.management_node_zone_post_xml, content_type='text/xml',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

    def testPostManagementNodeForZone(self):
        models.ManagementNode.objects.all().delete()
        zone = self._saveZone()
        xml = testsxml.management_node_zone_post_xml
        response = self._post('inventory/zones/%d/management_nodes/' % zone.zone_id,
            data=xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        management_node = models.ManagementNode.objects.get(pk=3)
        management_node_xml = testsxml.management_node_zone_post_response_xml.replace(
            '<registration_date/>',
            '<registration_date>%s</registration_date>' % \
            (management_node.registration_date.isoformat()))
        self.assertXMLEquals(response.content, management_node_xml % \
            (management_node.networks.all()[0].created_date.isoformat(),
             management_node.current_state.created_date.isoformat(),
             management_node.created_date.isoformat()))

class NetworksTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)
        self.system = self.newSystem(name="mgoblue",
            description="best appliance ever")
        self.system.save()

    def testExtractNetworkToUse(self):

        # try a net with no pinned/active nets, but only one net
        network = models.Network(dns_name="foo.com", active=False, pinned=False)
        network.system = self.system
        network.save()
        net = self.mgr.sysMgr.extractNetworkToUse(self.system)
        self.failUnlessEqual(net.dns_name, "foo.com")

        # Second network showed up, we assume no network
        network2 = models.Network(dns_name = "foo2.com", active=False,
            pinned=False)
        network2.system = self.system
        network2.save()
        net = self.mgr.sysMgr.extractNetworkToUse(self.system)
        self.failUnlessEqual(net, None)

        # try one with pinned only
        network.pinned = True
        network.save()
        net = self.mgr.sysMgr.extractNetworkToUse(self.system)
        self.failUnlessEqual(net.dns_name, "foo.com")

        # try one with active only
        network.pinned = False
        network.active = True
        network.save()
        net = self.mgr.sysMgr.extractNetworkToUse(self.system)
        self.failUnlessEqual(net.dns_name, "foo.com")

        # now add a pinned one in addition to active one to test order
        network3 = models.Network(dns_name="foo3.com", active=False, pinned=True)
        network3.system = self.system
        network3.save()
        self.failUnlessEqual(
            sorted((x.dns_name, x.pinned, x.active)
                for x in self.system.networks.all()),
            [
                ('foo.com', False, True),
                ('foo2.com', False, False),
                ('foo3.com', True, False),
            ])
        net = self.mgr.sysMgr.extractNetworkToUse(self.system)
        self.failUnlessEqual(net.network_id, network3.network_id)

class SystemsTestCase(XMLTestCase):
    fixtures = ['system_job', 'targets']

    def setUp(self):
        XMLTestCase.setUp(self)
        self.mock_scheduleSystemRegistrationEvent_called = False
        self.mockGetRmakeJob_called = False
        self.mock_scheduleSystemDetectMgmtInterfaceEvent_called = False
        self.mgr.sysMgr.scheduleSystemRegistrationEvent = self.mock_scheduleSystemRegistrationEvent
        self.mgr.sysMgr.scheduleSystemDetectMgmtInterfaceEvent = \
            self.mock_scheduleSystemDetectMgmtInterfaceEvent
        jobmodels.Job.getRmakeJob = self.mockGetRmakeJob

    def tearDown(self):
        XMLTestCase.tearDown(self)

    def mock_scheduleSystemRegistrationEvent(self, system):
        self.mock_scheduleSystemRegistrationEvent_called = True

    def mockGetRmakeJob(self):
        self.mockGetRmakeJob_called = True

    def mock_scheduleSystemDetectMgmtInterfaceEvent(self, system):
        self.mock_scheduleSystemDetectMgmtInterfaceEvent_called = True

    def testSystemPutAuth(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        eventUuid = 'eventuuid001'
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            eventUuid=eventUuid)

        system = self.newSystem(name="blah")
        system.save()

        system2 = self.newSystem(name="blip")
        system2.save()

        self._newSystemJob(system, eventUuid, 'rmakejob007',
            jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)

        xmlTempl = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
</system>
"""
        # No event uuid, no auth; this fails
        response = self._put('inventory/systems/%s' % system.pk,
            data=xmlTempl % params)
        self.failUnlessEqual(response.status_code, 401)

        # Bad event uuid; this fails
        response = self._put('inventory/systems/%s' % system.pk,
            data=xmlTempl % params,
            headers = { 'X-rBuilder-Event-UUID' : eventUuid + '-bogus'})
        self.failUnlessEqual(response.status_code, 401)

        # Good uuid, bad system
        response = self._put('inventory/systems/%s' % system2.pk,
            data=xmlTempl % params,
            headers = { 'X-rBuilder-Event-UUID' : eventUuid })
        self.failUnlessEqual(response.status_code, 401)

        # uuid validation, this works
        response = self._put('inventory/systems/%s' % system.pk,
            data=xmlTempl % params,
            headers = { 'X-rBuilder-Event-UUID' : eventUuid },
            username='admin', password='password')
        self.failUnlessEqual(response.status_code, 200)

        # user/pass auth, this works
        response = self._put('inventory/systems/%s' % system.pk,
            data=xmlTempl % params, username='testuser', password='password')
        self.failUnlessEqual(response.status_code, 200)

        # uuid valid, bad auth - this fails
        response = self._put('inventory/systems/%s' % system.pk,
            data=xmlTempl % params, username='testuser', password='bogus',
            headers = { 'X-rBuilder-Event-UUID' : eventUuid })
        self.failUnlessEqual(response.status_code, 401)

        # uuid bad, goodauth - this fails
        response = self._put('inventory/systems/%s' % system.pk,
            data=xmlTempl % params, username='admin', password='password',
            headers = { 'X-rBuilder-Event-UUID' : eventUuid + '-bogus' })
        self.failUnlessEqual(response.status_code, 401)

    def testSystemMothballAuth(self):
        """
        Ensure admin users can mothball systems https://issues.rpath.com/browse/RBL-7170
        """

        # TODO:  This test will fail until https://issues.rpath.com/browse/RBL-7172
        # is fixed, please to do remove it!

        models.System.objects.all().delete()
        system = self._saveSystem()

        # fail if anon
        response = self._put('inventory/systems/%d/' % system.system_id,
            data=testsxml.systems_put_mothball_xml)
        self.failUnlessEqual(response.status_code, 401)

        # fail if regular user
        response = self._put('inventory/systems/%d/' % system.system_id,
            data=testsxml.systems_put_mothball_xml,
            username="testuser", password="password")
        self.failUnlessEqual(response.status_code, 401)

    def testSystemMothball(self):
        """
        Ensure admin users can mothball systems https://issues.rpath.com/browse/RBL-7170
        """
        models.System.objects.all().delete()
        system = self._saveSystem()
        # work if admin
        response = self._put('inventory/systems/%d/' % system.system_id,
            data=testsxml.systems_put_mothball_xml,
            username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)
        system = models.System.objects.get(pk=system.system_id)
        self.assertTrue(system.current_state.name == models.SystemState.MOTHBALLED)
        self.assertTrue(system.current_state.description == models.SystemState.MOTHBALLED_DESC)

    def testBulkSystemAdd(self):
        xmlTempl = """\
  <system>
    <name>%(name)s</name>
    <description>%(name)s</description>
    <networks>
      <network>
        <device_name>eth0</device_name>
        <dns_name>%(dnsName)s</dns_name>
      </network>
    </networks>
    <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
  </system>
"""
        systems = []
        for i in range(10):
            params = dict(name="name %03d" % i,
                description="description %03d" % i,
                dnsName="dns-name-%03d" % i,
                zoneId=self.localZone.zone_id)
            systems.append(xmlTempl % params)
        xml = "<systems>" + ''.join(systems) + "</systems>"
        url = "inventory/systems"
        response = self._post(url, data=xml, username='admin', password='password')
        self.failUnlessEqual(response.status_code, 200)


    def testSystemSave(self):
        # make sure state gets set to unmanaged
        system = self.newSystem(name="mgoblue",
            description="best appliance ever")
        _eq = self.failUnlessEqual
        _eq(system.current_state_id, None)
        system.save()
        _eq(system.current_state.name, models.SystemState.UNMANAGED)

        # make sure we honor the state if set though
        system = self.newSystem(name="mgoblue",
            description="best appliance ever",
            current_state=self.mgr.sysMgr.systemState(models.SystemState.DEAD))
        system.save()
        _eq(system.current_state.name, models.SystemState.DEAD)

        # test name fallback to hostname
        system = self.newSystem(hostname="mgoblue",
            description="best appliance ever")
        self.failUnlessEqual(system.name, '')
        system.save()
        self.failUnlessEqual(system.name, system.hostname)

        # test name fallback to blank
        system = self.newSystem(description="best appliance ever")
        self.failUnlessEqual(system.name, '')
        system.save()
        self.failUnlessEqual(system.name, '')

        # make sure we honor the name if set though
        system = self.newSystem(name="mgoblue")
        system.save()
        self.failUnlessEqual(system.name, "mgoblue")

    def testSystemSaveAgentPort(self):
        # make sure state gets set to unmanaged
        system = self.newSystem(name="mgoblue",
            description="best appliance ever")
        self.assertTrue(system.agent_port is None)
        system.management_interface = models.ManagementInterface.objects.get(pk=1)
        system.save()
        self.assertTrue(system.agent_port == system.management_interface.port)

        system.agent_port = 897
        system.save()
        self.assertTrue(system.agent_port == 897)

        system = self.newSystem(name="mgoblue2",
            description="best appliance ever")
        system.save()
        self.assertTrue(system.agent_port is None)

    def testAddSystem(self):
        # create the system
        system = self.newSystem(name="mgoblue",
            description="best appliance ever")
        new_system = self.mgr.addSystem(system)
        assert(new_system is not None)
        self.failUnlessEqual(new_system.current_state.name,
            models.SystemState.UNMANAGED)

        # make sure we scheduled our registration event
        assert(self.mock_scheduleSystemDetectMgmtInterfaceEvent_called)

    def testAddRegisteredSystem(self):
        # create the system
        system = self.newSystem(name="mgoblue",
            description="best appliance ever",
            local_uuid='123', generated_uuid='456')
        new_system = self.mgr.addSystem(system)
        assert(new_system is not None)
        self.failUnlessEqual(new_system.current_state.name,
            models.SystemState.RESPONSIVE)

        # make sure we did not schedule registration
        self.failUnlessEqual(self.mock_scheduleSystemRegistrationEvent_called,
            False)

    def testAddRegisteredManagementNodeSystem(self):
        zone = self._saveZone()
        system_type = models.SystemType.objects.get(
            name = models.SystemType.INFRASTRUCTURE_MANAGEMENT_NODE)
        # create the system
        system = self.newSystem(name="mgoblue",
            description="best appliance ever",
            system_type=system_type,
            local_uuid='123', generated_uuid='456')
        system.zone = zone
        new_system = self.mgr.addSystem(system)
        assert(new_system is not None)
        self.failUnlessEqual(new_system.current_state.name,
            models.SystemState.RESPONSIVE)

        # make sure we did not schedule registration
        self.failUnlessEqual(self.mock_scheduleSystemRegistrationEvent_called,
            False)

    def testAddSystemNull(self):

        try:
            # create the system
            system = None
            self.mgr.addSystem(system)
        except:
            assert(False) # should not throw exception

    def testAddSystemNoNetwork(self):
        """
        Ensure a network is not pinned per https://issues.rpath.com/browse/RBL-7152
        """
        models.System.objects.all().delete()
        system = self.newSystem(name="foo", description="bar")
        self.mgr.addSystem(system)

    def testPostSystemNoNetwork(self):
        """
        Ensure a network is not pinned per https://issues.rpath.com/browse/RBL-7152
        """
        models.System.objects.all().delete()
        system_xml = testsxml.system_post_no_network_xml
        response = self._post('inventory/systems/', data=system_xml)
        self.assertEquals(response.status_code, 200)
        try:
            models.System.objects.get(pk=3)
        except models.System.DoesNotExist:
            self.assertTrue(False) # should exist

    def testPostSystemNetworkUnpinned(self):
        """
        Unpinned network_address
        """
        models.System.objects.all().delete()
        system_xml = testsxml.system_post_network_unpinned
        response = self._post('inventory/systems/',
            data=system_xml, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=3)
        self.failUnlessEqual(
            [ (x.dns_name, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('1.2.3.4', None, False, ), ])
        xml = system.to_xml()
        x = xobj.parse(xml)
        self.failUnlessEqual(x.system.network_address.address, "1.2.3.4")
        self.failUnlessEqual(x.system.network_address.pinned, "False")

    def testPostSystemNetworkPinned(self):
        """
        Pinned network_address
        """
        models.System.objects.all().delete()
        system_xml = testsxml.system_post_network_pinned
        response = self._post('inventory/systems/',
            data=system_xml, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=3)
        self.failUnlessEqual(
            [ (x.dns_name, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('1.2.3.4', None, True, ), ])
        xml = system.to_xml()
        x = xobj.parse(xml)
        self.failUnlessEqual(x.system.network_address.address, "1.2.3.4")
        self.failUnlessEqual(x.system.network_address.pinned, "True")

    def testPutSystemNetworkUnpinned(self):
        models.System.objects.all().delete()
        system = self.newSystem(name="aaa", description="bbb")
        system.save()
        # No networks initially
        self.failUnlessEqual(list(system.networks.all()), [])

        xml_data = testsxml.system_post_network_unpinned
        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('1.2.3.4', None, False, ), ])

        system = models.System.objects.get(pk=system.pk)

        # Add a bunch of network addresses, none of them pinned
        system.networks.all().delete()

        network = models.Network(system=system, dns_name='blah1',
            ip_address='10.1.1.1', active=True, pinned=False)
        network.save()
        network = models.Network(system=system, dns_name='blah2',
            ip_address='10.2.2.2', active=False, pinned=False)
        network.save()

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('1.2.3.4', None, False, ), ])

        # Add a bunch of network addresses, none of them pinned
        # Pretend the active interface is the same as the one the client
        # specified.
        system.networks.all().delete()

        network = models.Network(system=system, dns_name='blah1',
            ip_address='1.2.3.4', active=True, pinned=False)
        network.save()
        network = models.Network(system=system, dns_name='blah2',
            ip_address='10.2.2.2', active=False, pinned=False)
        network.save()

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.ip_address, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('blah1', '1.2.3.4', True, False, ),
              ('blah2', '10.2.2.2', False, False, ) ])

        # Add a bunch of network addresses, one of them pinned.
        # We should unpin in this case.
        system.networks.all().delete()

        network = models.Network(system=system, dns_name='blah1',
            ip_address='10.1.1.1', active=False, pinned=True)
        network.save()
        network = models.Network(system=system, dns_name='blah2',
            ip_address='10.2.2.2', active=True, pinned=False)
        network.save()

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('1.2.3.4', None, False, ), ])

    def testPutSystemNetworkPinned(self):
        models.System.objects.all().delete()
        system = self.newSystem(name="aaa", description="bbb")
        system.save()
        # No networks initially
        self.failUnlessEqual(list(system.networks.all()), [])

        xml_data = testsxml.system_post_network_pinned
        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('1.2.3.4', None, True, ), ])

        system = models.System.objects.get(pk=system.pk)

        # Add a bunch of network addresses, none of them pinned
        system.networks.all().delete()

        network = models.Network(system=system, dns_name='blah1',
            ip_address='10.1.1.1', active=True, pinned=False)
        network.save()
        network = models.Network(system=system, dns_name='blah2',
            ip_address='10.2.2.2', active=False, pinned=False)
        network.save()

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.ip_address, x.active, x.pinned)
                for x in system.networks.all() ],
            [
                ('blah1', '10.1.1.1', True, False),
                ('blah2', '10.2.2.2', False, False),
                ('1.2.3.4', None, None, True),
            ])

        # Add a bunch of network addresses, none of them pinned
        # Pretend the active interface is the same as the one the client
        # specified.
        system.networks.all().delete()

        network = models.Network(system=system, dns_name='blah1',
            ip_address='1.2.3.4', active=True, pinned=False)
        network.save()
        network = models.Network(system=system, dns_name='blah2',
            ip_address='10.2.2.2', active=False, pinned=False)
        network.save()

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.ip_address, x.active, x.pinned)
                for x in system.networks.all() ],
            [
                ('blah1', '1.2.3.4', True, False),
                ('blah2', '10.2.2.2', False, False),
                ('1.2.3.4', None, None, True),
            ])

        # Add a bunch of network addresses, one of them pinned.
        # We should unpin in this case.
        system.networks.all().delete()

        network = models.Network(system=system, dns_name='blah1',
            ip_address='1.2.3.4', active=False, pinned=True)
        network.save()
        network = models.Network(system=system, dns_name='blah2',
            ip_address='10.2.2.2', active=True, pinned=False)
        network.save()

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml_data,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        self.failUnlessEqual(
            [ (x.dns_name, x.ip_address, x.active, x.pinned)
                for x in system.networks.all() ],
            [ ('blah1', '1.2.3.4', False, True, ),
              ('blah2', '10.2.2.2', True, False, ) ])

    def testPostNewSystemNetworkPinned(self):
        xmlTempl = """\
<system>
  <name>%(name)s</name>
  <network_address>
    <address>%(ipAddr)s</address>
    <pinned>true</pinned>
  </network_address>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>"""
        params = dict(name='test1', zoneId=self.localZone.zone_id,
            ipAddr='1.1.1.1')
        response = self._post('inventory/systems/',
            data=xmlTempl % params, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        doc = xobj.parse(response.content)
        systemId = doc.system.system_id
        system = models.System.objects.get(system_id=systemId)
        self.assertEquals(
            [ (x.dns_name, x.ip_address, x.active, x.pinned)
                for x in system.networks.order_by('dns_name') ],
            [ (params['ipAddr'], None, None, True), ])


    def testPostSystemNetworkPreservePinned(self):
        """
        Pinned network_address
        """
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid)
        xmlTempl = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <networks>
    <network>
      <active>false</active>
      <device_name>eth0</device_name>
      <dns_name>10.1.1.1</dns_name>
      <ip_address>10.1.1.1</ip_address>
      <netmask>255.255.255.0</netmask>
    </network>
    <network>
      <active>true</active>
      <device_name>eth1</device_name>
      <dns_name>blah2.example.com</dns_name>
      <ip_address>10.2.2.2</ip_address>
      <netmask>255.255.255.0</netmask>
    </network>
  </networks>
</system>
"""
        models.System.objects.all().delete()
        system = self.newSystem(name="aaa", description="bbb",
            local_uuid=localUuid, generated_uuid=generatedUuid)
        system.save()

        # Add a bunch of network addresses, one of them pinned.
        # We should preserve the pinned one
        system.networks.all().delete()

        network = models.Network(system=system, dns_name='blah1',
            active=False, pinned=True)
        network.save()
        network = models.Network(system=system, dns_name='ignoreme',
            active=False, pinned=True)
        network.save()
        network = models.Network(system=system, dns_name='blah2.example.com',
            ip_address='10.2.2.2', netmask='255.255.255.0',
            active=True, pinned=False, device_name='eth0')
        network.save()

        system_xml = xmlTempl % params
        response = self._post('inventory/systems/',
            data=system_xml, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(
            [ (x.dns_name, x.ip_address, x.active, x.pinned)
                for x in system.networks.order_by('dns_name') ],
            [
                ('10.1.1.1', '10.1.1.1', False, None, ),
                ('blah1', None, False, True, ),
                ('blah2.example.com', '10.2.2.2', True, False, ),
            ])
        xml = system.to_xml()
        x = xobj.parse(xml)
        self.failUnlessEqual(x.system.network_address.address, "blah1")
        self.failUnlessEqual(x.system.network_address.pinned, "True")

    def testGetSystems(self):
        system = self._saveSystem()
        response = self._get('inventory/systems/', username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.systems_xml % (system.networks.all()[0].created_date.isoformat(), system.created_date.isoformat()),
            ignoreNodes = [ 'latest_survey', 'created_date', 'modified_date', 'created_by', 'modified_by' ])
        response = self._get('inventory/systems', username='testuser', password='password')
        self.assertEquals(response.status_code, 403)

    def testPostSystemNetworkDuplicateAddress(self):
        """
        RCE-985

        2 entries in network:
        IP_ADDRESS  DNS_NAME
        -----------+--------
        (null)      10.1.1.1
        10.1.1.1    ...
        we should update the second and delete the first, not the other way
        around.
        """
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid)
        xmlTempl = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <networks>
    <network>
      <active>true</active>
      <device_name>eth0</device_name>
      <dns_name>dhcp1.example.com</dns_name>
      <ip_address>10.1.1.1</ip_address>
      <netmask>255.255.255.0</netmask>
    </network>
  </networks>
</system>
"""
        models.System.objects.all().delete()
        system = self.newSystem(name="aaa", description="bbb",
            local_uuid=localUuid, generated_uuid=generatedUuid)
        system.save()
        models.Network.objects.create(system=system,
            dns_name='10.1.1.1', active=True, pinned=False)
        nw = models.Network.objects.create(system=system,
            ip_address='10.1.1.1', dns_name='dhcp1.example.com',
            active=True, pinned=False)

        system_xml = xmlTempl % params
        response = self._post('inventory/systems/', data=system_xml)
        self.assertEquals(response.status_code, 200)

        system = models.System.objects.get(system_id=system.system_id)
        self.assertEquals([
            (x.network_id, x.ip_address) for x in system.networks.all() ],
            [(nw.network_id, '10.1.1.1')])

    def testPostSystemNetworkAddressChange(self):
        """
        Pinned network_address
        """
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid)
        xmlTempl = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <networks>
    <network>
      <active>false</active>
      <device_name>eth0</device_name>
      <dns_name>10.1.1.1</dns_name>
      <ip_address>10.1.1.1</ip_address>
      <netmask>255.255.255.0</netmask>
    </network>
  </networks>
</system>
"""
        models.System.objects.all().delete()
        system = self.newSystem(name="aaa", description="bbb",
            local_uuid=localUuid, generated_uuid=generatedUuid)
        system.save()
        network = models.Network(system=system, ip_address='1.2.3.4',
            dns_name='blah1', active=True, pinned=False)
        network.save()

        system_xml = xmlTempl % params
        response = self._post('inventory/systems/', data=system_xml)
        self.assertEquals(response.status_code, 200)

        system = models.System.objects.get(system_id=system.system_id)
        self.assertEquals([ x.ip_address for x in system.networks.all() ],
            ['10.1.1.1'])

    def testGetSystemAuth(self):
        """
        Ensure requires auth but not admin
        """
        system = self._saveSystem()
        response = self._get('inventory/systems/%d/' % system.system_id)
        self.assertEquals(response.status_code, 401)

        response = self._get('inventory/systems/%d/' % system.system_id,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 403)

        response = self._get('inventory/systems/%d/' % system.system_id,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetSystemDoesntExist(self):
        models.System.objects.all().delete()
        system = self._saveSystem()
        system.to_xml()
        response = self._get('inventory/systems/86753021/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 404)

    def testGetSystem(self):
        models.System.objects.all().delete()
        system = self._saveSystem()
        system.to_xml()
        response = self._get('inventory/systems/%d/' % system.system_id,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.system_xml % (system.networks.all()[0].created_date.isoformat(), system.created_date.isoformat()),
            ignoreNodes = [ 'latest_survey', 'created_date', 'modified_date', 'created_by', 'modified_by', 'time_created', 'time_updated' ])

    def testDeleteSystemDoesNotExist(self):
        # deleting a system that doesn't exist should be a 404, not an error
        models.System.objects.all().delete()
        response = self._delete('inventory/systems/%d/' % 42,
            username="admin", password="password")
        self.assertEquals(response.status_code, 404)

    def testGetSystemWithTarget(self):
        models.System.objects.all().delete()
        targetType = targetmodels.TargetType.objects.get(name='vmware')
        target = targetmodels.Target(target_type=targetType,
            name='testtargetname', description='testtargetdescription',
            state=targetmodels.Target.States.OPERATIONAL,
            zone=self.localZone)
        target.save()
        system = self._saveSystem()
        system.target = target
        system.save()
        response = self._get('inventory/systems/%d/' % system.system_id,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_target_xml % \
            (system.networks.all()[0].created_date.isoformat(), system.created_date.isoformat()),
            ignoreNodes = [ 'latest_survey', 'created_date', 'modified_date', 'created_by', 'modified_by', 'time_created', 'time_updated' ])

    def testPostSystemAuth(self):
        """
        Ensure wide open for rpath-tools usage
        """
        system_xml = testsxml.system_post_xml
        response = self._post('inventory/systems/',
            data=system_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)

    def testPostSystemBadNetwork(self):
        """Ensure network address validation is done pre-save"""
        system_xml = testsxml.system_post_xml_bad_network
        response = self._post('inventory/systems/',
            data=system_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 400)
        self.assertTrue(response.content.find('<fault>') != -1)

    def testPostSystem(self):
        models.System.objects.all().delete()
        system_xml = testsxml.system_post_xml
        response = self._post('inventory/systems/',
            data=system_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=3)
        system_xml = testsxml.system_post_xml_response.replace('<registration_date/>',
            '<registration_date>%s</registration_date>' % \
            (system.registration_date.isoformat()))
        self.assertXMLEquals(response.content, system_xml % \
            (system.networks.all()[0].created_date.isoformat(), system.created_date.isoformat()),
            ignoreNodes = [ 'created_date', 'ssl_client_certificate',
                            'time_created', 'time_updated',
                            'registration_date', 'actions',
                            'created_by', 'modified_by',
                            'created_date', 'modified_date', 'latest_survey'])

    def testPostSystemThroughManagementNode(self):
        # Send the identity of the management node
        models.System.objects.all().delete()
        self._saveManagementNode()
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        eventUuid = 'eventuuid001'
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            eventUuid=eventUuid)
        xmlTempl = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
</system>
"""
        zoneName = base64.b64encode(self.localZone.name)
        response = self._post('inventory/systems/',
            data=xmlTempl % params,
            headers={ 'X-rPath-Management-Zone' : zoneName },
            username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)

    def testPostSystemDupUuid(self):
        # add the first system
        models.System.objects.all().delete()
        system_xml = testsxml.system_post_xml_dup
        response = self._post('inventory/systems/',
            data=system_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=3)
        self.failUnlessEqual(system.name, "testsystemname")

        # add it with same uuids but with different name to make sure
        # we get back same system with updated prop
        system_xml = testsxml.system_post_xml_dup2
        response = self._post('inventory/systems/',
            data=system_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        this_system = models.System.objects.get(pk=3)
        self.failUnlessEqual(this_system.name, "testsystemnameChanged")

    def testPutSystemManagementInterface(self):
        system = self._saveSystem()

        # Test that a mgmt interface can be changed.
        response = self._put('inventory/systems/%s' % system.pk,
            data=testsxml.system_mgmt_interface_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.assertEquals(system.management_interface.name, 'wmi')
        self.assertEquals(system.management_interface.pk, 2)

        # Test that a mgmt interface can be added.
        system.management_interface = None
        system.save()
        response = self._put('inventory/systems/%s' % system.pk,
            data=testsxml.system_mgmt_interface_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.assertEquals(system.management_interface.name, 'wmi')
        self.assertEquals(system.management_interface.pk, 2)

        # Test that mgmt interface can be deleted
        response = self._put('inventory/systems/%s' % system.pk,
            data=testsxml.system_delete_mgmt_interface_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.assertEquals(system.management_interface, None)

    def testSystemCredentials(self):
        system = self._saveSystem()
        response = self._post('inventory/systems/%s/credentials' % \
            system.pk,
            data=testsxml.credentials_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.credentials_resp_xml)

        response = self._get('inventory/systems/%s/credentials' % \
            system.pk,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.credentials_resp_xml)

        response = self._put('inventory/systems/%s/credentials' % \
            system.pk,
            data=testsxml.credentials_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.credentials_put_resp_xml)

        system = models.System.objects.get(pk=system.pk)

        creds = system.credentials
        # Do a simple PUT on systems
        xml = """\
<system>
  <credentials>blahblah</credentials>
</system>
"""
        response = self._put('inventory/systems/%s' % system.pk,
            data=xml,
            username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system.credentials, creds)

    def testSystemWmiCredentials(self):
        system = self._saveSystem()
        system.management_interface = models.ManagementInterface.objects.get(name='wmi')
        system.save()
        response = self._post('inventory/systems/%s/credentials' % \
            system.pk,
            data=testsxml.credentials_wmi_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.credentials_wmi_resp_xml)

        response = self._get('inventory/systems/%s/credentials' % \
            system.pk,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.credentials_wmi_resp_xml)

        response = self._put('inventory/systems/%s/credentials' % \
            system.pk,
            data=testsxml.credentials_wmi_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.credentials_wmi_put_resp_xml)

    def testSystemConfiguration(self):
        system = self._saveSystem()
        url = 'inventory/systems/%s/configuration' % system.pk

        response = self._post(url,
            data=testsxml.configuration_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.configuration_post_xml)

        response = self._get(url,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.configuration_post_xml)

        response = self._put(url,
            data=testsxml.configuration_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.configuration_put_xml)

        # Now test with some real config
        self._mockConfigDescriptorCache()

        self.mgr.sysMgr.setObservedTopLevelItems(system,
            set([ 'group-foo=/blah@rpl:1/12345.67:1-1-1' ]))

        response = self._put(url,
            data=testsxml.configuration_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 400)
        self.assertXMLEquals(response.content,
                '''<fault><code>400</code><message>["Missing field: 'vhosts'"]</message><traceback/></fault>''')

        # Now some good data
        configurationXml = """\
<configuration>
  <vhosts>
    <vhost>
      <serverName>aaa</serverName>
      <documentRoot>aaa</documentRoot>
    </vhost>
  </vhosts>
  <ignored-1/>
  <ignored-2/>
</configuration>
"""

        response = self._put(url,
            data=configurationXml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        system = system.__class__.objects.get(system_id=system.system_id)
        configurationXmlFixed = configurationXml.replace('<vhosts>',
            '<vhosts list="true">')
        self.assertXMLEquals(system.configuration, configurationXmlFixed)

        # now also test the configuration job
        # test failing because of no network interface...
        #response = self._post('inventory/systems/%s/jobs' % system.pk,
        #    data = testsxml.system_configuration_xml % system.pk,
        #    username='admin', password='password')
        #self.assertEquals(response.status_code, 200)
        #self.assertXMLEquals(response.content, '<wrong></wrong>')


    def _getSystemConfigurationDescriptor(self, system_id):
        return self.mgr.getSystemConfigurationDescriptor(system_id)

    def testSystemConfigurationDescriptor(self):
        system = self._saveSystem()

        response = self._get('inventory/systems/%s/configuration_descriptor' % \
            system.pk,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, '<configuration/>')

        self._mockConfigDescriptorCache()

        self.mgr.sysMgr.setObservedTopLevelItems(system,
            set([ 'group-foo=/blah@rpl:1/12345.67:1-1-1' ]))

        response = self._get('inventory/systems/%s/configuration_descriptor' % \
            system.pk,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        descr = descriptor.ConfigurationDescriptor(fromStream=response.content)
        self.assertEquals(
            [ x.name for x in descr.getDataFields() ],
            [ 'vhosts' ])
        # Check the fields we unconditionally change on the way out
        self.assertEquals(descr.getDisplayName(), 'Configuration Descriptor')
        self.assertEquals(descr.getRootElement(), 'configuration')

    def _mockConfigDescriptorCache(self):
        from rpath_tools.client.utils.config_descriptor_cache import ConfigDescriptorCache
        descr = self._getConfigDescriptor()
        mockGetDescriptor = lambda x, y: descr
        self.mock(ConfigDescriptorCache, 'getDescriptor', mockGetDescriptor)
        return descr

    def _getConfigDescriptor(self):

        vhost = descriptor.ConfigurationDescriptor()
        vhost.setId("apache-configuration/vhost")
        vhost.setRootElement('vhost')
        vhost.setDisplayName('Virtual Host Configuration')
        vhost.addDescription('Virtual Host Configuration')
        vhost.addDataField('serverName', type="str", required=True,
            descriptions="Virtual Host Name")
        vhost.addDataField('documentRoot', type="str", required=True,
            descriptions="Virtual Host Document Root") 

        descr = descriptor.ConfigurationDescriptor()
        descr.setId("Some-ID")
        descr.setDisplayName('Ignored')
        descr.addDescription('Ignored')
        descr.setRootElement('ignored')

        descr.addDataField('vhosts', type=descr.ListType(vhost),
            required=True, descriptions="Virtual Hosts",
            constraints=[dict(constraintName='uniqueKey', value="serverName"),
                dict(constraintName="minLength", value=1)])
        return descr

    def testGetSystemLogAuth(self):
        """
        Ensure requires auth but not admin
        """
        models.System.objects.all().delete()
        response = self._post('inventory/systems/',
            data=testsxml.system_post_xml, username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        response = self._get('inventory/systems/3/system_log/')
        self.assertEquals(response.status_code, 401)

        response = self._get('inventory/systems/3/system_log/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        response = self._get('inventory/systems/3/system_log/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)


    def testGetSystemLog(self):
        models.System.objects.all().delete()
        response = self._post('inventory/systems/',
            data=testsxml.system_post_xml)
        self.assertEquals(response.status_code, 200)
        response = self._get('inventory/systems/3/system_log/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        content = []
        # Just remove lines with dates in them, it's easier to test for now.
        for line in response.content.split('\n'):
            if 'entry_date' in line or \
               'will be enabled on' in line:
                continue
            else:
                content.append(line)
        self.assertXMLEquals('\n'.join(content), testsxml.system_log_xml)

    def testGetSystemHasHostInfo(self):
        system = self.newSystem(name="mgoblue")
        system.save()
        assert(self.mgr.sysMgr.getSystemHasHostInfo(system) == False)

        network = models.Network(system=system)
        network.save()
        system.networks.add(network)
        assert(self.mgr.sysMgr.getSystemHasHostInfo(system) == False)

        network2 = models.Network(ip_address="1.1.1.1", system=system)
        network2.save()
        system.networks.add(network2)
        assert(self.mgr.sysMgr.getSystemHasHostInfo(system))

        network2.delete()
        network = models.Network(ipv6_address="1.1.1.1", system=system)
        network.save()
        system.networks.add(network)
        assert(self.mgr.sysMgr.getSystemHasHostInfo(system))

        network.delete()
        network = models.Network(dns_name="foo.bar.com", system=system)
        network.save()
        system.networks.add(network)
        assert(self.mgr.sysMgr.getSystemHasHostInfo(system))

    def testDedupByBootUuid(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        bootUuid = 'eventuuid001'
        targetSystemId = 'target-system-id-001'

        # Create 2 systems with differnt target_system_id, just like ec2 would
        # if you asked it to launch 2 instances
        system = self.newSystem(name="blah", target_system_id=targetSystemId)
        system.save()

        system2 = self.newSystem(name="blah2",
            target_system_id=targetSystemId.replace('001', '002'))
        system2.save()

        # Create a job
        cu = connection.cursor()
        now = self.mgr.sysMgr.now()
        cu.execute("""
            INSERT INTO jobs (job_uuid, job_type_id, job_state_id, created_by,
                created, modified)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            [ bootUuid, 1, 1, 1, now, now])
        jobId = cu.lastrowid

        # Pretend that this job launched 2 systems (the way ec2 can do)
        cu.execute("INSERT INTO job_system (job_id, system_id) VALUES (%s, %s)",
            [ jobId, system.pk ])
        cu.execute("INSERT INTO job_system (job_id, system_id) VALUES (%s, %s)",
            [ jobId, system2.pk ])

        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            bootUuid=bootUuid, targetSystemId=targetSystemId,
            survey=testsxml.survey_input_xml)

        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <boot_uuid>%(bootUuid)s</boot_uuid>
  <target_system_id>%(targetSystemId)s</target_system_id>
  %(survey)s
</system>
""" % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.local_uuid, localUuid)
        self.failUnlessEqual(model.generated_uuid, generatedUuid)
        self.failUnlessEqual(model.boot_uuid, bootUuid)
        self.failUnlessEqual(model.pk, system.pk)
        self.failUnlessEqual(model.target_system_id, targetSystemId)

        # Fetch system, make sure we have a survey for it
        system = self.mgr.addSystem(model)
        self.failUnlessEqual(
            [ x.uuid for x in system.surveys.all() ],
            [ '1234', ])
        self.failUnlessEqual(system.latest_survey.uuid, '1234')

    def testLoadFromObjectEventUuid(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        eventUuid = 'eventuuid001'
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            eventUuid=eventUuid, zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.local_uuid, localUuid)
        self.failUnlessEqual(model.generated_uuid, generatedUuid)
        self.failUnlessEqual(model.event_uuid, eventUuid)

    def _setupDedupEventUuid(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        eventUuid = 'eventuuid001'
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            eventUuid=eventUuid, zoneId=self.localZone.zone_id,
            survey=testsxml.survey_input_xml)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
  %(survey)s
</system>
""" % params

        # Create a system with just a name
        system = self.newSystem(name = 'blippy')
        system.save()
        # Create a job
        eventType = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)
        job = jobmodels.Job(job_uuid = 'rmakeuuid001', job_type=eventType,
            job_state=self.mgr.sysMgr.jobState(jobmodels.JobState.RUNNING))
        job.save()
        systemJob = models.SystemJob(system=system, job=job,
            event_uuid=eventUuid)
        systemJob.save()
        return system, xml

    def testDedupByEventUuid(self):
        system, xml = self._setupDedupEventUuid()
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        # We should have loaded the old one
        self.failUnlessEqual(system.pk, model.pk)
        self.failUnlessEqual(model.name, 'blippy')
        # Catch the case of synthetic fields not being converted to
        # unicode (xobj types confuse database drivers)
        self.failUnlessEqual(type(model.event_uuid), unicode)

        # Fetch system, make sure we have a survey for it
        system = self.mgr.addSystem(model)
        self.assertEquals(
            [ x.uuid for x in system.surveys.all() ],
            [ '1234', ])
        self.assertEquals(system.latest_survey.uuid, '1234')

    def testDedupByEventUuidWithRemoval1(self):
        system, systemRemoved = self._testDedupByEventUuidWithRemoval(targetSystemFirst=False)
        entries = self.mgr.getSystemLogEntries(system)
        self.failUnlessEqual(
            [ x.entry for x in entries ],
            [
                '(copied) Log message from target system',
                'Log message from empty system'
            ])

    def testDedupByEventUuidPUT(self):
        system, xml = self._setupDedupEventUuid()
        url = 'inventory/systems/%s' % system.system_id
        headers = { 'X-rBuilder-Event-UUID' :
            system.systemjob_set.all()[0].event_uuid }
        response = self._put(url, data=xml, headers=headers)
        self.assertEquals(response.status_code, 200)

        # Make sure survey got saved
        system = system.__class__.objects.get(system_id=system.system_id)
        self.assertEquals(
            [ x.uuid for x in system.surveys.all() ],
            [ '1234', ])
        self.assertEquals(system.latest_survey.uuid, '1234')

    def testDedupByEventUuidWithRemoval2(self):
        system, systemRemoved = self._testDedupByEventUuidWithRemoval(targetSystemFirst=True)
        entries = self.mgr.getSystemLogEntries(system)
        self.failUnlessEqual(
            [ x.entry for x in entries ],
            [
                '(copied) Log message from empty system',
                'Log message from target system',
            ])

    def _newEmptySystem(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        # Create the system, pretending it's registered
        system = self.newSystem(name='blippy', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()
        self.mgr.sysMgr.log_system(system, "Log message from empty system")
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid)
        return system, params

    def _testDedupByEventUuidWithRemoval(self, targetSystemFirst=False):
        eventUuid = 'eventuuid001'

        if not targetSystemFirst:
            system0, params = self._newEmptySystem()

        # Create a target system
        targetSystemId = 'systemid-001'
        targetSystemName = 'target system name 001'
        targetSystemDescription = 'target system description 001'
        targetSystemState = "Obflusterating"
        tgt1 = targetmodels.Target.objects.get(pk=1) # vsphere1
        system1 = self.newSystem(name="bloppy", target=tgt1,
            target_system_id=targetSystemId,
            target_system_name=targetSystemName,
            target_system_description=targetSystemDescription,
            target_system_state=targetSystemState)
        system1.save()
        self.mgr.sysMgr.log_system(system1, "Log message from target system")

        # Create a job
        eventType = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)
        job = jobmodels.Job(job_uuid = 'rmakeuuid001', job_type=eventType,
            job_state=self.mgr.sysMgr.jobState(jobmodels.JobState.RUNNING))
        job.save()
        systemJob = models.SystemJob(system=system1, job=job,
            event_uuid=eventUuid)
        systemJob.save()

        if targetSystemFirst:
            system0, params = self._newEmptySystem()

        params.update(eventUuid=eventUuid, zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params

        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)

        # We should have loaded the old one
        self.failUnlessEqual(model.pk, system0.pk)
        self.failUnlessEqual(model.name, 'blippy')
        self.failUnlessEqual(model.event_uuid, eventUuid)

        self.mgr.sysMgr.mergeSystems(model)

        systemToKeep, systemRemoved = sorted([ system0, system1 ],
            key = lambda x: x.pk)
        systemRemovedUrl = systemRemoved.get_absolute_url()
        system = models.System.objects.get(pk=systemToKeep.pk)

        # At this point, properties from system1 should have copied over
        self.failUnlessEqual(system.target.pk, tgt1.pk)
        self.failUnlessEqual(system.target_system_id, targetSystemId)
        self.failUnlessEqual(system.target_system_name, targetSystemName)
        self.failUnlessEqual(system.target_system_description, targetSystemDescription)
        self.failUnlessEqual(system.target_system_state, targetSystemState)
        self.failUnlessEqual(system.local_uuid, params['localUuid'])
        self.failUnlessEqual(system.generated_uuid, params['generatedUuid'])

        # The other system should be gone
        self.failUnlessEqual(list(models.System.objects.filter(
            pk=systemRemoved.pk)),
            [])

        # A redirect should have been created
        redirect = redirectmodels.Redirect.objects.filter(
            new_path=systemToKeep.get_absolute_url(),
            old_path=systemRemovedUrl)
        self.assertEquals(len(redirect), 1)

        return system, systemRemoved

    def testCurrentStateUpdateApi(self):
        # Make sure current state can be updated via the API.  This allows
        # users to mothball systems at any point in time, etc.
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'

        system = self.newSystem(name='blippy', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()

        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <current_state>
    <description>Retired</description>
    <name>mothballed</name>
    <system_state_id>10</system_state_id>
  </current_state>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params

        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.pk, system.pk)
        self.failUnlessEqual(model.current_state.name, "mothballed")

    def testUpdateCurrentState(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        eventUuid = 'eventuuid001'
        jobState = "Completed"
        jobUuid = 'rmakeuuid001'
        statusCode = 291
        statusText = "text 291"
        statusDetail = "detail 291"

        system = self.newSystem(name='blippy', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()

        # Create a job
        eventType = jobmodels.EventType.objects.get(
            name = jobmodels.EventType.SYSTEM_UPDATE)
        job = jobmodels.Job(job_uuid=jobUuid, job_type=eventType,
            job_state=self.mgr.sysMgr.jobState(jobmodels.JobState.RUNNING))
        job.save()
        systemJob = models.SystemJob(system=system, job=job,
            event_uuid=eventUuid)
        systemJob.save()

        # Pass bogus event uuid, we should not update
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            eventUuid=eventUuid + "bogus", jobUuid=jobUuid + "bogus",
            jobState=jobState, zoneId=self.localZone.zone_id,
            statusCode=statusCode, statusText=statusText,
            statusDetail=statusDetail)

        xmlTempl = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <event_uuid>%(eventUuid)s</event_uuid>
  <jobs>
    <job>
      <job_uuid>%(jobUuid)s</job_uuid>
      <job_state>%(jobState)s</job_state>
      <status_code>%(statusCode)s</status_code>
      <status_text>%(statusText)s</status_text>
      <status_detail>%(statusDetail)s</status_detail>
    </job>
  </jobs>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
"""
        xml = xmlTempl % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        from mint.django_rest.rbuilder import modellib
        model = models.System.objects.load_from_object(xobjmodel, request=None,
            flags=modellib.Flags(save=False))
        self.failUnlessEqual(model.pk, system.pk)

        # We expect nothing to be updated, since there's no such job
        job = jobmodels.Job.objects.get(pk=job.pk)
        self.failUnlessEqual(job.job_state.name, 'Running')
        self.failUnlessEqual(model.lastJob, None)

        # Now set jobUuid to be correct
        params['jobUuid'] = jobUuid
        xml = xmlTempl % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.pk, system.pk)

        # We still expect nothing to be updated, since the event_uuid is wrong
        job = jobmodels.Job.objects.get(pk=job.pk)
        self.failUnlessEqual(job.job_state.name, 'Running')
        self.failUnlessEqual(model.lastJob, None)

        # Now set eventUuid to be correct
        params['eventUuid'] = eventUuid
        xml = xmlTempl % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.pk, system.pk)

        job = jobmodels.Job.objects.get(pk=job.pk)
        self.failUnlessEqual(job.job_state.name, jobState)
        self.failUnlessEqual(model.lastJob.pk, job.pk)
        self.failUnlessEqual(job.status_code, statusCode)
        self.failUnlessEqual(job.status_text, statusText)
        self.failUnlessEqual(job.status_detail, statusDetail)

        # Make sure that pasting a system job with just the event uuid and job
        # info works (i.e. without the local and generated uuids)
        xmlTempl = """\
<system>
  <event_uuid>%(eventUuid)s</event_uuid>
  <jobs>
    <job>
      <job_uuid>%(jobUuid)s</job_uuid>
      <job_state>%(jobState)s</job_state>
      <status_code>%(statusCode)s</status_code>
      <status_text>%(statusText)s</status_text>
      <status_detail>%(statusDetail)s</status_detail>
    </job>
  </jobs>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
"""
        jobState = 'Failed'
        params['jobState'] = jobState
        statusCode = params['statusCode'] = 432
        statusText = params['statusText'] = "status text 432"
        statusDetail = params['statusDetail'] = "status detail 432"

        xml = xmlTempl % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.pk, system.pk)

        job = jobmodels.Job.objects.get(pk=job.pk)
        self.failUnlessEqual(job.job_state.name, jobState)
        self.failUnlessEqual(model.lastJob.pk, job.pk)
        self.failUnlessEqual(job.status_code, statusCode)
        self.failUnlessEqual(job.status_text, statusText)
        self.failUnlessEqual(job.status_detail, statusDetail)

    def testLoadFromObjectHiddenFields(self):
        # Make sure one can't overwrite hidden fields (sslClientKey is hidden)
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        sslClientCert = 'sslClientCert'
        sslClientKey = 'sslClientKey'

        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            zoneId=self.localZone.zone_id)

        system = self.newSystem(name='blippy', local_uuid=localUuid,
            generated_uuid=generatedUuid,
            _ssl_client_certificate=sslClientCert,
            _ssl_client_key=sslClientKey)
        system.save()

        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <ssl_client_certificate>thou shalt not change me</ssl_client_certificate>
  <ssl_client_key>thou shalt not change me</ssl_client_key>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.local_uuid, localUuid)
        self.failUnlessEqual(model.generated_uuid, generatedUuid)
        self.failUnlessEqual(model._ssl_client_certificate, sslClientCert)
        self.failUnlessEqual(model._ssl_client_key, sslClientKey)

    def testBooleanFieldSerialization(self):
        # XML schema sez lowercase true or false for boolean fields
        system = self.newSystem(name = 'blippy')
        system.save()
        network = models.Network(dns_name="foo3.com", ip_address='1.2.3.4',
            active=False, pinned=True, system=system)
        network.save()
        xml = network.to_xml()
        self.failUnlessIn("<active>false</active>", xml)
        self.failUnlessIn("<pinned>true</pinned>", xml)

    def testAgentPort(self):
        # RBL-7150
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        agentPort = 12345
        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            agentPort=agentPort, zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <agent_port>%(agentPort)s</agent_port>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params
        obj = xobj.parse(xml)
        xobjmodel = obj.system
        model = models.System.objects.load_from_object(xobjmodel, request=None)
        self.failUnlessEqual(model.agent_port, agentPort)
        self.failUnlessIn("<agent_port>%s</agent_port>" % agentPort,
            model.to_xml())

    def testSetSystemState(self):
        # RBL-6795
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        systemState = 'dead'

        system = self.newSystem(name='blah', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()

        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            systemState=systemState, zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <current_state>
    <name>%(systemState)s</name>
  </current_state>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml, username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system.current_state.name, systemState)

    def testPutShouldUpdateExisting(self):
        # Make sure that, if we PUT data to a system, we're updating exactly
        # the one specified in the URL - RBL-7182
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        systemState = 'dead'

        system = self.newSystem(name='blah')
        system.save()

        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            systemState=systemState, zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <current_state>
    <name>%(systemState)s</name>
  </current_state>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml, username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system.local_uuid, localUuid)
        self.failUnlessEqual(system.generated_uuid, generatedUuid)
        self.failUnlessEqual(system.current_state.name, systemState)

    def testSetSystemManagementInterface(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        agentPort = 8675309

        managementInterface = models.Cache.get(models.ManagementInterface,
            name="wmi")
        managementInterfaceId = managementInterface.pk

        system = self.newSystem(name='blah', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()

        self.failUnlessEqual(system.management_interface_id, None)

        params = dict(localUuid=localUuid, generatedUuid=generatedUuid,
            agentPort=agentPort,
            managementInterfaceId=managementInterfaceId)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <management_interface href="/api/v1/inventory/management_interfaces/%(managementInterfaceId)s"/>
  <agent_port>%(agentPort)s</agent_port>
</system>
""" % params

        """
  <management_interface>
    <name>%(managementInterfaceName)s</name>
  </management_interface>
        """

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml, username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)
        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system.management_interface_id,
            managementInterfaceId)
        self.failUnlessEqual(system.agent_port, agentPort)

    def testGetCredentialsWhenMissing(self):
        system = self.newSystem(name="blah")
        system.save()
        creds = self.mgr.getSystemCredentials(system.pk)
        self.assertXMLEquals(creds.to_xml(),
            '<credentials id="/api/v1/inventory/systems/%s/credentials"/>' %
                system.pk)

    def testGetConfiguration(self):
        system = self.newSystem(name="blah")
        system.configuration = configuration = "<configuration><a>a</a><b>b</b></configuration>"
        system.save()
        url = "inventory/systems/%s/configuration" % system.pk
        response = self._get(url,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, configuration)

        config = self.mgr.getSystemConfiguration(system.pk)
        self.assertXMLEquals(config, configuration)

    def testGetConfigurationWhenMissing(self):
        system = self.newSystem(name="blah")
        system.save()
        config = self.mgr.getSystemConfiguration(system.pk)
        self.assertXMLEquals(config, '<configuration/>')

    def testMarkSystemShutdown(self):
        p = dict(local_uuid="abc", generated_uuid="def")
        system = self.newSystem(name="blah", **p)
        system.save()

        p.update(currentState = "non-responsive-shutdown")

        url = 'inventory/systems'
        xml = """
<system>
  <local_uuid>%(local_uuid)s</local_uuid>
  <generated_uuid>%(generated_uuid)s</generated_uuid>
  <current_state><name>%(currentState)s</name></current_state>
</system>
"""
        response = self._post(url, data=xml % p)
        self.failUnlessEqual(response.status_code, 200)

        system = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system.current_state.name,
            p['currentState'])

    def testAddSystemsSameGeneratedUuid(self):
        # RBL-8211 - get rid of unnecessary unique constraint on generated_uuid
        guuid = "some-uuid"
        luuid1 = "localuuid001"
        luuid2 = "localuuid002"
        system1 = self.newSystem(local_uuid=luuid1, generated_uuid=guuid)
        system1.save()
        system2 = self.newSystem(local_uuid=luuid2, generated_uuid=guuid)
        system2.save()

        system1 = models.System.objects.get(local_uuid=luuid1,
            generated_uuid=guuid)
        system2 = models.System.objects.get(local_uuid=luuid2,
            generated_uuid=guuid)
        self.failIf(system1.pk == system2.pk)

    def testIncompleteRegistration(self):
        # Mingle #1733
        generatedUuid = 'JeanValjean'
        params = dict(localUuid='', generatedUuid=generatedUuid,
                zoneId=self.localZone.zone_id)
        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
""" % params
        resp = self._post('inventory/systems', data=xml)
        self.failUnlessEqual(resp.status_code, 200)
        data = xobj.parse(resp.content)
        systemId = data.system.system_id
        system = models.System.objects.get(system_id=systemId)
        actual = [ x.entry for x in models.SystemLogEntry.objects.filter(system_log__system__system_id = system.system_id) ]
        desired = [
              u'System added to inventory',
              u'Incomplete registration: missing local_uuid. Possible cause: dmidecode malfunctioning',
        ]
        self.failUnlessEqual(actual,desired)

class SystemCertificateTestCase(XMLTestCase):
    def testGenerateSystemCertificates(self):
        system = self.newSystem(local_uuid="localuuid001",
            generated_uuid="generateduuid001")
        system.save()
        self.failUnlessEqual(system._ssl_client_certificate, None)
        self.failUnlessEqual(system._ssl_client_key, None)
        self.mgr.sysMgr.generateSystemCertificates(system)

        clientCert = system._ssl_client_certificate
        clientKey = system._ssl_client_key

        crt = x509.X509(None, None)
        crt.load_from_strings(clientCert, clientKey)
        self.failUnlessEqual(crt.x509.get_subject().as_text(),
            'O=rPath rBuilder, OU=http://rpath.com, CN=local_uuid:localuuid001 generated_uuid:generateduuid001 serial:0')
        # Make sure the cert is signed with the low grade CA
        issuer = 'O=rBuilder Low-Grade Certificate Authority, OU=Created at 2010-09-02 11:18:53-0400'
        # We're using self-signed certs
        issuer = 'O=rPath rBuilder, OU=http://rpath.com, CN=local_uuid:localuuid001 generated_uuid:generateduuid001 serial:0'

        self.failUnlessEqual(crt.x509.get_issuer().as_text(), issuer)
        # Test some of the other functions, while we're at it
        fingerprint = crt.fingerprint
        self.failUnlessEqual(len(fingerprint), 40)

        certHash = crt.hash
        # This always changes, so no point in comparing anything other than
        # length
        self.failUnlessEqual(len(certHash), 8)

        # The issuer hash is always known, since it's our LG CA
        #self.failUnlessEqual(crt.hash_issuer, '6d8bb0a1')
        self.failUnlessEqual(crt.hash_issuer, certHash)

        # Try again, we should not re-generate the cert
        self.mgr.sysMgr.generateSystemCertificates(system)
        self.failUnlessEqual(system._ssl_client_certificate, clientCert)
        self.failUnlessEqual(system._ssl_client_key, clientKey)

class SystemStateTestCase(XMLTestCase):
    def setUp(self):
        XMLTestCase.setUp(self)
        jobmodels.Job.getRmakeJob = self.mockGetRmakeJob

    def mockGetRmakeJob(self):
        self.mockGetRmakeJob_called = True

    def testSetCurrentState(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        jobState = "Completed"

        eventUuid1 = 'eventuuid001'
        jobUuid1 = 'rmakeuuid001'

        system = self.newSystem(name='blippy')
        system.save()

        self._newSystemJob(system, eventUuid1, jobUuid1,
            jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)

        params = dict(eventUuid=eventUuid1, jobUuid=jobUuid1, jobState=jobState,
            zoneId=self.localZone.zone_id)

        xmlTempl = """\
<system>
  <event_uuid>%(eventUuid)s</event_uuid>
  <jobs>
    <job>
      <job_uuid>%(jobUuid)s</job_uuid>
      <job_state>%(jobState)s</job_state>
    </job>
  </jobs>
  <managing_zone href="http://testserver/api/v1/inventory/zones/%(zoneId)s"/>
</system>
"""
        xml = xmlTempl % params

        response = self._put('inventory/systems/%s' % system.pk,
            data=xml, headers = { 'X-rBuilder-Event-UUID' : eventUuid1 },
            username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)

        system2 = models.System.objects.get(pk=system.pk)
        # Just because the job completed, it doesn't mean the registration
        # succeeded
        self.failUnlessEqual(system2.current_state.name,
            models.SystemState.RESPONSIVE)
        log = models.SystemLog.objects.filter(system=system).get()
        logEntries = log.system_log_entries.order_by('-entry_date')

        system2 = models.System.objects.get(pk=system.pk)
        self.failUnlessEqual(system2.current_state.name,
            models.SystemState.RESPONSIVE)
        log = models.SystemLog.objects.filter(system=system).get()
        logEntries = log.system_log_entries.order_by('-entry_date')
        # don't care so much
        #self.failUnlessEqual([ x.entry for x in logEntries ],
        #    [
        #        'System state change: Unmanaged -> Online',
        #    ])


    def testGetNextSystemState(self):
        localUuid = 'localuuid001'
        generatedUuid = 'generateduuid001'
        jobState = "Completed"

        eventUuid1 = 'eventuuid001'
        jobUuid1 = 'rmakeuuid001'
        eventUuid2 = 'eventuuid002'
        jobUuid2 = 'rmakeuuid002'
        eventUuid3 = 'eventuuid003'
        jobUuid3 = 'rmakeuuid003'
        eventUuid4 = 'eventuuid004'
        jobUuid4 = 'rmakeuuid004'
        eventUuid5 = 'eventuuid005'
        jobUuid5 = 'rmakeuuid005'
        eventUuid6 = 'eventuuid006'
        jobUuid6 = 'rmakeuuid006'
        eventUuid7 = 'eventuuid007'
        jobUuid7 = 'rmakeuuid007'

        system = self.newSystem(name='blippy', local_uuid=localUuid,
            generated_uuid=generatedUuid)
        system.save()

        stateCompleted = self.mgr.sysMgr.jobState(jobmodels.JobState.COMPLETED)
        stateFailed = self.mgr.sysMgr.jobState(jobmodels.JobState.FAILED)

        job1 = self._newSystemJob(system, eventUuid1, jobUuid1,
            jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)

        jobRegNoAuth = self._newSystemJob(system, eventUuid6, jobUuid6,
            jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE, statusCode = 401)

        UNMANAGED = models.SystemState.UNMANAGED
        UNMANAGED_CREDENTIALS_REQUIRED = models.SystemState.UNMANAGED_CREDENTIALS_REQUIRED
        REGISTERED = models.SystemState.REGISTERED
        RESPONSIVE = models.SystemState.RESPONSIVE
        NONRESPONSIVE = models.SystemState.NONRESPONSIVE
        NONRESPONSIVE_NET = models.SystemState.NONRESPONSIVE_NET
        NONRESPONSIVE_HOST = models.SystemState.NONRESPONSIVE_HOST
        NONRESPONSIVE_SHUTDOWN = models.SystemState.NONRESPONSIVE_SHUTDOWN
        NONRESPONSIVE_SUSPENDED = models.SystemState.NONRESPONSIVE_SUSPENDED
        NONRESPONSIVE_CREDENTIALS = models.SystemState.NONRESPONSIVE_CREDENTIALS
        DEAD = models.SystemState.DEAD
        MOTHBALLED = models.SystemState.MOTHBALLED

        tests = [
            (job1, stateCompleted, UNMANAGED, RESPONSIVE),
            (job1, stateCompleted, UNMANAGED_CREDENTIALS_REQUIRED, RESPONSIVE),
            (job1, stateCompleted, REGISTERED, None),
            (job1, stateCompleted, RESPONSIVE, None),
            (job1, stateCompleted, NONRESPONSIVE_HOST, None),
            (job1, stateCompleted, NONRESPONSIVE_NET, None),
            (job1, stateCompleted, NONRESPONSIVE_SHUTDOWN, None),
            (job1, stateCompleted, NONRESPONSIVE_SUSPENDED, None),
            (job1, stateCompleted, NONRESPONSIVE_CREDENTIALS, None),
            (job1, stateCompleted, NONRESPONSIVE, None),
            (job1, stateCompleted, DEAD, None),
            (job1, stateCompleted, MOTHBALLED, None),

            (job1, stateFailed, UNMANAGED, None),
            (job1, stateFailed, UNMANAGED_CREDENTIALS_REQUIRED, None),
            (job1, stateFailed, REGISTERED, None),
            (job1, stateFailed, RESPONSIVE, None),
            (job1, stateFailed, NONRESPONSIVE_HOST, None),
            (job1, stateFailed, NONRESPONSIVE_NET, None),
            (job1, stateFailed, NONRESPONSIVE_SHUTDOWN, None),
            (job1, stateFailed, NONRESPONSIVE_SUSPENDED, None),
            (job1, stateFailed, NONRESPONSIVE_CREDENTIALS, None),
            (job1, stateFailed, NONRESPONSIVE, None),
            (job1, stateFailed, DEAD, None),
            (job1, stateFailed, MOTHBALLED, None),
        ]
        transitionsCompleted = []
        for oldState in [UNMANAGED, UNMANAGED_CREDENTIALS_REQUIRED,
                REGISTERED, RESPONSIVE,
                NONRESPONSIVE_HOST, NONRESPONSIVE_NET, NONRESPONSIVE_SHUTDOWN,
                NONRESPONSIVE_SUSPENDED, NONRESPONSIVE,
                NONRESPONSIVE_CREDENTIALS, DEAD, MOTHBALLED]:
            transitionsCompleted.append((oldState, RESPONSIVE))
        transitionsFailed = [
            (REGISTERED, NONRESPONSIVE),
            (RESPONSIVE, NONRESPONSIVE),
        ]
        for oldState in [UNMANAGED, UNMANAGED_CREDENTIALS_REQUIRED,
                NONRESPONSIVE_HOST, NONRESPONSIVE_NET,
                NONRESPONSIVE_SHUTDOWN, NONRESPONSIVE_SUSPENDED,
                NONRESPONSIVE, NONRESPONSIVE_CREDENTIALS, DEAD, MOTHBALLED]:
            transitionsFailed.append((oldState, None))

        # Failed auth tests`
        for job in [ jobRegNoAuth ]:
            tests.append((job, stateFailed, UNMANAGED,
                UNMANAGED_CREDENTIALS_REQUIRED))
            tests.append((job, stateFailed, UNMANAGED_CREDENTIALS_REQUIRED,
                None))
            for oldState in [REGISTERED, RESPONSIVE, NONRESPONSIVE_NET,
                    NONRESPONSIVE_HOST, NONRESPONSIVE_SHUTDOWN,
                    NONRESPONSIVE_SUSPENDED, DEAD]:
                tests.append((job, stateFailed, oldState,
                    NONRESPONSIVE_CREDENTIALS))
            for oldState in [NONRESPONSIVE_CREDENTIALS, MOTHBALLED]:
                tests.append((job, stateFailed, oldState, None))


        # these tests are no longer applicable because they test the internals
        # of a particular function versus the desired result of the changes
        # in the objects.  Disabling them since intent could not be discerned.
        for (job, jobState, oldState, newState) in tests:
            system.current_state = self.mgr.sysMgr.systemState(oldState)
            job.job_state = jobState
            ret = self.mgr.sysMgr.getNextSystemState(system, job)
            msg = "Job %s (%s; %s): %s -> %s (expected: %s)" % (
                (job.job_type.name, jobState.name, job.status_code,
                 oldState, ret, newState))

class EventTypeTestCase(XMLTestCase):

    def testGetEventTypes(self):
        response = self._get('inventory/event_types/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.event_types_xml)

    def testGetEventType(self):
        response = self._get('inventory/event_types/1/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.event_type_xml)

    def testPutEventTypeAuth(self):
        """
        Ensure we require admin to put event types
        """
        response = self._put('inventory/event_types/1/',
            data= testsxml.event_type_put_xml, content_type='text/xml')
        self.assertEquals(response.status_code, 401)

        response = self._put('inventory/event_types/1/',
            data=testsxml.event_type_put_xml, content_type='text/xml',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)

    def testPutEventType(self):
        jobmodels.EventType.objects.all().delete()
        event_type = jobmodels.EventType(name="foo", description="bar", priority=110)
        event_type.save()
        self.assertTrue(event_type.priority == 110)
        xml = testsxml.event_type_put_xml % dict(event_type_id=event_type.pk)
        response = self._put('inventory/event_types/%s/' % event_type.job_type_id,
            data=xml, content_type='text/xml',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        event_type = jobmodels.EventType.objects.get(pk=event_type.pk)
        self.assertTrue(event_type.priority == 1)

    def testPutEventTypeName(self):
        """
        Do not allow changing the event type name https://issues.rpath.com/browse/RBL-7171
        """
        jobmodels.EventType.objects.all().delete()
        event_type = jobmodels.EventType(name=jobmodels.EventType.SYSTEM_UPDATE, description="bar", priority=110)
        event_type.save()
        self.failUnlessEqual(event_type.name, jobmodels.EventType.SYSTEM_UPDATE)
        xml = testsxml.event_type_put_name_change_xml % dict(event_type_id=event_type.pk)
        response = self._put('inventory/event_types/%d/' % event_type.pk,
            data=xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        event_type = jobmodels.EventType.objects.get(pk=event_type.pk)
        # name should not have changed
        self.failUnlessEqual(event_type.name, jobmodels.EventType.SYSTEM_UPDATE)

class SystemEventTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)

        # need a system
        network = models.Network(ip_address='1.1.1.1')
        self.system = self.newSystem(name="mgoblue",
            description="best appliance ever",
            management_interface=models.ManagementInterface.objects.get(name='cim'))
        self.system.save()
        network.system = self.system
        self.system.networks.add(network)
        self.system.save()

        # start with no logs/system events
        models.SystemLog.objects.all().delete()
        models.SystemEvent.objects.all().delete()

        self.mock_dispatchSystemEvent_called = False
        self.mgr.sysMgr.dispatchSystemEvent = self.mock_dispatchSystemEvent

        self.old_DispatchSystemEvent = rbuildermanager.SystemManager._dispatchSystemEvent

    def tearDown(self):
        rbuildermanager.SystemManager._dispatchSystemEvent = self.old_DispatchSystemEvent
        XMLTestCase.tearDown(self)

    def mock_dispatchSystemEvent(self, event):
        self.mock_dispatchSystemEvent_called = True

    # test needs update
    #
    #def testGetSystemEventsRest(self):
    #    act_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION)
    #    event2 = models.SystemEvent(system=self.system,event_type=act_event, priority=act_event.priority)
    #    event2.save()
    #    response = self._get('inventory/system_events/',
    #       username="testuser", password="password")
    #    self.assertEquals(response.status_code, 200)
    #    self.assertXMLEquals(response.content,
    #        testsxml.system_events_xml % \
    #             (event2.time_created.isoformat(), event2.time_enabled.isoformat()))

    def testGetSystemEventRestAuth(self):
        """
        Ensure requires auth but not admin
        """
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        event = models.SystemEvent(system=self.system,event_type=update_event, priority=update_event.priority)
        event.save()
        response = self._get('inventory/system_events/%d/' % event.system_event_id)
        self.assertEquals(response.status_code, 401)

        response = self._get('inventory/system_events/%d/' % event.system_event_id,
           username="testuser", password="password")
        self.assertEquals(response.status_code, 200)

    def testGetSystemEventRest(self):
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        event = models.SystemEvent(system=self.system,event_type=update_event, priority=update_event.priority)
        event.save()
        response = self._get('inventory/system_events/%d/' % event.system_event_id,
           username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.system_event_xml % (event.time_created.isoformat(), event.time_enabled.isoformat()))

    def testGetSystemEvent(self):
        # add an event
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        event = models.SystemEvent(system=self.system,event_type=update_event, priority=update_event.priority)
        event.save()
        new_event = self.mgr.getSystemEvent(event.system_event_id)
        assert(new_event == event)

    def testGetSystemEvents(self):
        # add an event
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        act_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)
        event1 = models.SystemEvent(system=self.system,event_type=update_event, priority=update_event.priority)
        event1.save()
        event2 = models.SystemEvent(system=self.system,event_type=act_event, priority=act_event.priority)
        event2.save()
        SystemEvents = self.mgr.getSystemEvents()
        assert(len(SystemEvents.system_event) == 2)

    def testDeleteSystemEvent(self):
        # add an event
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        event = models.SystemEvent(system=self.system,event_type=update_event, priority=update_event.priority)
        event.save()
        self.mgr.deleteSystemEvent(event.system_event_id)
        events = models.SystemEvent.objects.all()
        assert(len(events) == 0)

    def testCreateSystemEvent(self):
        local_system = self.newSystem(name="mgoblue_local", description="best appliance ever")
        local_system.save()
        network = models.Network(system=local_system)
        network.save()
        local_system.networks.add(network)
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        event = self.mgr.createSystemEvent(local_system, update_event)
        assert(event is None)
        assert(self.mock_dispatchSystemEvent_called == False)

        network2 = models.Network(system=local_system, ip_address="1.1.1.1")
        network2.save()
        local_system.networks.add(network2)
        event = self.mgr.createSystemEvent(local_system, update_event)
        assert(event is not None)

    def testSaveSystemEvent(self):
        self._saveSystem()
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        event = models.SystemEvent(system=self.system, event_type=update_event)
        event.save()
        # make sure event priority was set even though we didn't pass it in
        assert(event.priority == update_event.priority)

        event2 = models.SystemEvent(system=self.system, event_type=update_event, priority=1)
        event2.save()
        # make sure we honor priority if set
        assert(event2.priority == 1)

    def testScheduleSystemRegistrationEvent(self):
        # registration events are no longer dispatched immediately (RBL-8851)
        self.mgr.scheduleSystemRegistrationEvent(self.system)

        registration_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)
        event = models.SystemEvent.objects.filter(system=self.system,event_type=registration_event).get()
        assert(event is not None)
        # should have been enabled immediately
        assert(event.time_enabled <= timeutils.now())

        # make sure we have our log event
        log = models.SystemLog.objects.filter(system=self.system).get()
        sys_registered_entries = log.system_log_entries.all()
        assert(len(sys_registered_entries) == 1)

    def testAddSystemEventNull(self):

        try:
            self.mgr.addSystemSystemEvent(None, None)
        except:
            assert(False) # should not throw exception

    def testAddSystemRegistrationEvent(self):
        # registration events are no longer dispatched immediately (RBL-8851)
        registration_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)
        systemEvent = models.SystemEvent(system=self.system,
            event_type=registration_event, priority=registration_event.priority,
            time_enabled=timeutils.now())
        systemEvent.save()
        assert(systemEvent is not None)
        self.mgr.addSystemSystemEvent(self.system.system_id, systemEvent)


    # temporarily disabled -- needs to send an old school job not a new one?

    #def testPostSystemEventAuth(self):
    #    """
    #    Ensure requires auth but not admin
    #    """
    #    url = 'inventory/systems/%d/system_events/' % self.system.system_id
    #    system_event_post_xml = testsxml.system_event_post_xml
    #    response = self._post(url, data=system_event_post_xml)
    #    self.assertEquals(response.status_code, 401)
    #
    #    response = self._post(url,
    #        data=system_event_post_xml,
    #        username="admin", password="password")
    #    self.assertEquals(response.status_code, 200)

    #def testPostSystemEvent(self):
    #    url = 'inventory/systems/%d/system_events/' % self.system.system_id
    #    system_event_post_xml = testsxml.system_event_post_xml
    #    response = self._post(url,
    #        data=system_event_post_xml,
    #        username="admin", password="password")
    #    self.assertEquals(response.status_code, 200)
    #    system_event = models.SystemEvent.objects.get(pk=1)
    #    # TODO: looser checking of XML returns

    def testIncompatibleEvents(self):
        def mock__dispatchSystemEvent(self, event):
            system = event.system
            job_uuid = str(random.random())
            job = jobmodels.Job(job_uuid=job_uuid, job_token=job_uuid*2,
                job_state=jobmodels.JobState.objects.get(name='Running'),
                job_type=event.event_type)
            job.save()
            systemJob = models.SystemJob(job=job, system=system,
                event_uuid=str(random.random()))
            systemJob.save()

        rbuildermanager.SystemManager._dispatchSystemEvent = mock__dispatchSystemEvent

        # Clear system events
        [j.delete() for j in self.system.systemjob_set.all()]

        url = 'inventory/systems/%d/system_events/' % self.system.system_id

        # Schedule an update, should succeed
        response = self._post(url,
            data=testsxml.system_event_update_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertTrue('<fault>' not in response.content)

        # Schedule a shutdown, should fail
        response = self._post(url,
            data=testsxml.system_event_immediate_shutdown_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 409)
        self.assertTrue('<fault>' in response.content)

        # Clear system events
        [j.delete() for j in self.system.systemjob_set.all()]

        # Schedule a registration, should succeed
        response = self._post(url,
            data=testsxml.system_event_immediate_registration_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertTrue('<fault>' not in response.content)

class SystemEventProcessingTestCase(XMLTestCase):

    # do not load other fixtures for this test case as it is very data order dependent
    fixtures = ['system_event_processing']

    def setUp(self):
        XMLTestCase.setUp(self)

        self.mintConfig = self.mgr.cfg
        self.mock(self.mgr.sysMgr, 'extractNetworkToUse',
            self.mock_extractNetworkToUse)
        self.resetFlags()

    def resetFlags(self):
        self.mock_extractNetworkToUse_called = False

    def mock_extractNetworkToUse(self, system):
        self.mock_extractNetworkToUse_called = True
        return None

    def testProcessSystemEvents(self):

        # set default processing size to 1
        self.mintConfig.systemEventsNumToProcess = 1

        #remove the registration event so we handle the poll now event
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)
        event.delete()

    def testProcessSystemEventsNoTrigger(self):
        # make sure registration event doesn't trigger next poll event
        # start with no regular poll events
        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        models.SystemEvent.objects.filter(event_type=update_event).delete()
        try:
            models.SystemEvent.objects.get(event_type=update_event)
            assert(False) # should have failed
        except models.SystemEvent.DoesNotExist:
            pass

        # make sure next one is registration now event
        events = self.mgr.sysMgr.getSystemEventsForProcessing()
        event = events[0]
        self.failUnlessEqual(event.event_type.name,
            jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)
        self.mgr.sysMgr.processSystemEvents()

        # should have no poll events still
        try:
            models.SystemEvent.objects.get(event_type=update_event)
            assert(False) # should have failed
        except models.SystemEvent.DoesNotExist:
            pass

    def testDispatchSystemEvent(self):
        self.resetFlags()
        self.failIf(self.mock_extractNetworkToUse_called)

        update_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_UPDATE)
        act_event = self.mgr.sysMgr.eventType(jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)

        system = self.newSystem(name="hey")
        system.save()
        # sanity check dispatching poll event
        event = models.SystemEvent(system=system,event_type=update_event, priority=update_event.priority)
        event.save()
        self.mgr.sysMgr.dispatchSystemEvent(event)
        transaction.commit()

        self.failUnlessEqual(event.system_event_id, None)
        # _extractNetworkToUse is only called if we have a repeater client
        self.failIf(self.mock_extractNetworkToUse_called)

        self.failUnlessEqual(event.system_event_id, None)
        # _extractNetworkToUse is only called if we have a repeater client
        self.failIf(self.mock_extractNetworkToUse_called)

        # sanity check dispatching registration event
        self.resetFlags()
        event = models.SystemEvent(system=system, event_type=act_event, priority=act_event.priority)
        event.save()
        self.mgr.sysMgr.dispatchSystemEvent(event)
        transaction.commit()

        self.failUnlessEqual(event.system_event_id, None)

class SystemEventProcessing2TestCase(XMLTestCase, test_utils.RepeaterMixIn):
    # do not load other fixtures for this test case as it is very data order dependent
    fixtures = ['system_event_processing']

    def setUp(self):
        XMLTestCase.setUp(self)
        test_utils.RepeaterMixIn.setUpRepeaterClient(self)
        self.system2 = system = self.newSystem(name="hey")
        system.save()
        network2 = models.Network(ip_address="2.2.2.2", active=True)
        network3 = models.Network(ip_address="3.3.3.3", pinned=True)
        system.networks.add(network2)
        system.networks.add(network3)
        system.save()
        self._uuid = 0

    def _setupEvent(self, eventType, eventData=None):
        self.system2.agent_port = 12345
        self.system2.save()
        eventType = self.mgr.sysMgr.eventType(eventType)
        # Remove all networks
        for net in self.system2.networks.all():
            net.delete()
        network = models.Network(dns_name = 'superduper.com')
        network.system = self.system2
        network.save()
        # sanity check dispatching poll event
        event = models.SystemEvent(system=self.system2,
            event_type=eventType, priority=eventType.priority)
        if eventData:
            if isinstance(eventData, basestring):
                event.event_data = eventData
            else:
                event.event_data = cPickle.dumps(eventData)
        event.save()
        return event

    def _mockUuid(self):
        def mockedUuid4():
            self._uuid += 1
            return "really-unique-uuid-%03d" % self._uuid
        from mint.lib import uuid
        self.mock(uuid, 'uuid4', mockedUuid4)

    def _dispatchEvent(self, event):
        self._mockUuid()
        self.mgr.sysMgr.dispatchSystemEvent(event)


    def testDispatchActivateSystemEvent(self):
        event = self._setupEvent(jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE)
        self._dispatchEvent(event)
        transaction.commit()

        cimParams = self.mgr.repeaterMgr.repeaterClient.CimParams
        resLoc = self.mgr.repeaterMgr.repeaterClient.ResultsLocation

        self.failUnlessEqual(self.mgr.repeaterMgr.repeaterClient.getCallList(),
            [
                ('register_cim',
                    (
                        cimParams(host='superduper.com',
                            port=12345,
                            eventUuid = 'really-unique-uuid-001',
                            clientKey=testsxml.pkey_pem,
                            clientCert=testsxml.x509_pem,
                            requiredNetwork=None,
                            targetName=None,
                            targetType=None,
                            instanceId=None,
                            launchWaitTime=1200),
                    ),
                    dict(
                        zone='Local rBuilder',
                        jobToken='really-unique-uuid-002',
                        uuid='really-unique-uuid-003',
                        resultsLocation=resLoc(
                            path='/api/v1/inventory/systems/4',
                            port=80),
                    ),
                ),
            ])
        system = self.mgr.getSystem(self.system2.system_id)
        jobs = system.jobs.all()
        self.failUnlessEqual([ x.job_uuid for x in jobs ],
            ['really-unique-uuid-003'])
        # XXX find a better way to extract the additional field from the
        # many-to-many table
        self.failUnlessEqual(
            [ x.event_uuid for x in models.SystemJob.objects.filter(system__system_id = system.system_id) ],
            [ 'really-unique-uuid-001' ])

    def testDispatchManagementInterfaceEvent(self):
        event = self._setupEvent(jobmodels.EventType.SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE)
        self._dispatchEvent(event)
        transaction.commit()

        mgmtIfaceParams = self.mgr.repeaterMgr.repeaterClient.ManagementInterfaceParams
        resLoc = self.mgr.repeaterMgr.repeaterClient.ResultsLocation

        self.failUnlessEqual(self.mgr.repeaterMgr.repeaterClient.getCallList(),
            [
                ('detectMgmtInterface',
                    (
                        mgmtIfaceParams(host='superduper.com',
                            eventUuid = 'really-unique-uuid-001',
                            interfacesList=[
                                {
                                    'port': 135,
                                    'interfaceHref':
                                      '/api/v1/inventory/management_interfaces/2',
                                },
                                {
                                    'port': 5989,
                                    'interfaceHref':
                                      '/api/v1/inventory/management_interfaces/1',
                                },
                                {
                                    'port': 22,
                                    'interfaceHref':
                                      '/api/v1/inventory/management_interfaces/3',
                                }
                                ]
                        ),
                    ),
                    dict(
                        zone='Local rBuilder',
                        jobToken='really-unique-uuid-002',
                        uuid='really-unique-uuid-003',
                        resultsLocation=resLoc(
                            path='/api/v1/inventory/systems/4',
                            port=80),
                    ),
                ),
            ])
        system = self.mgr.getSystem(self.system2.system_id)
        jobs = system.jobs.all()
        self.failUnlessEqual([ x.job_uuid for x in jobs ],
            ['really-unique-uuid-003'])
        # XXX find a better way to extract the additional field from the
        # many-to-many table
        self.failUnlessEqual(
            [ x.event_uuid for x in models.SystemJob.objects.filter(system__system_id = system.system_id) ],
            [ 'really-unique-uuid-001' ])

    def testInterfaceDetection(self):
        self._mockUuid()

        eventUuid1 = "eventUuid1"
        jobUuid1 = "jobUuid1"
        eventUuid2 = "eventUuid2"
        jobUuid2 = "jobUuid2"

        CIM = models.Cache.get(models.ManagementInterface,
            name=models.ManagementInterface.CIM)
        WMI = models.Cache.get(models.ManagementInterface,
            name=models.ManagementInterface.WMI)

        systemCim = self.newSystem(name="blah cim",
            management_interface=CIM)
        systemCim.save()
        network = models.Network(dns_name="blah cim", ip_address="1.2.3.4",
            system=systemCim)
        network.save()
        systemWmi = self.newSystem(name="blah wmi",
            management_interface=WMI)
        systemWmi.save()
        network = models.Network(dns_name="blah wmi", ip_address="1.2.3.4",
            system=systemWmi)

        jobCim = self._newSystemJob(systemCim, eventUuid1, jobUuid1,
            jobmodels.EventType.SYSTEM_DETECT_MANAGEMENT_INTERFACE,
            jobState=jobmodels.JobState.COMPLETED)
        jobWmi = self._newSystemJob(systemWmi, eventUuid2, jobUuid2,
            jobmodels.EventType.SYSTEM_DETECT_MANAGEMENT_INTERFACE,
            jobState=jobmodels.JobState.COMPLETED)

        repClient = self.mgr.repeaterMgr.repeaterClient
        cimParams = repClient.CimParams
        resLoc = repClient.ResultsLocation

        # Clear out the system events table
        models.SystemEvent.objects.all().delete()
        transaction.commit()
        transaction.enter_transaction_management()
        connection.managed(True)

        self.failUnlessEqual(self.mgr.repeaterMgr.repeaterClient.getCallList(),
            [])

        newState = self.mgr.sysMgr.getNextSystemState(systemCim, jobCim)
        self.failUnlessEqual(newState, None)
        # Nothing in the call stack yet
        self.failUnlessEqual(self.mgr.repeaterMgr.repeaterClient.getCallList(),
            [])

        # Force commit, this is normally done by the middleware
        transaction.commit()
        self.failUnlessEqual(self.mgr.repeaterMgr.repeaterClient.getCallList(),
            [
                ('register_cim',
                    (
                        cimParams(host='1.2.3.4',
                            port=5989,
                            eventUuid='really-unique-uuid-001',
                            clientKey=testsxml.pkey_pem,
                            clientCert=testsxml.x509_pem,
                            requiredNetwork=None,
                            targetName=None,
                            targetType=None,
                            instanceId=None,
                            launchWaitTime=1200),
                    ),
                    dict(zone='Local rBuilder',
                        jobToken='really-unique-uuid-002',
                        uuid='really-unique-uuid-003',
                        resultsLocation=resLoc(
                            path='/api/v1/inventory/systems/%s' % systemCim.pk,
                            port=80),
                    ),
                ),
            ])

        # Clean the deck
        self.mgr.repeaterMgr.repeaterClient.reset()

        newState = self.mgr.sysMgr.getNextSystemState(systemWmi, jobWmi)
        self.failUnlessEqual(newState,
            models.SystemState.UNMANAGED_CREDENTIALS_REQUIRED)
        # Being a WMI system, we need credentials
        self.failUnlessEqual(self.mgr.repeaterMgr.repeaterClient.getCallList(),
            [])

    def testDispatchConfigurationCim(self):
        pass
        #self._mockUuid()
        #cimInt = models.Cache.get(models.ManagementInterface,
        #    name=models.ManagementInterface.CIM)
        #self.system2.management_interface = cimInt
        #configDict = dict(a='1', b='2')
        #self.system2.configuration = self.mgr.sysMgr.marshalCredentials(
        #    configDict)
        #self.system2.save()
        #self.mgr.sysMgr.scheduleSystemConfigurationEvent(self.system2)
        #transaction.commit()

        #repClient = self.mgr.repeaterMgr.repeaterClient
        #cimParams = repClient.CimParams
        #resLoc = repClient.ResultsLocation

        #eventUuid = models.SystemJob.objects.all()[0].event_uuid

        # possibly need to fix results -- TBD -- otherwise too low level of a test?

        #self.failUnlessEqual(repClient.getCallList(),
        #    [
        #        ('configuration_cim',
        #            (
        #                cimParams(host='3.3.3.3',
        #                    port=None,
        #                    eventUuid=eventUuid,
        #                    clientKey=testsxml.pkey_pem,
        #                    clientCert=testsxml.x509_pem,
        #                    requiredNetwork='3.3.3.3',
        #                    targetName=None,
        #                    targetType=None,
        #                    instanceId=None,
        #                    launchWaitTime=1200),
        #            ),
        #            dict(
        #                zone='Local rBuilder',
        #                configuration='<configuration><a>1</a><b>2</b></configuration>',
        #                uuid='really-unique-uuid-002',
        #                resultsLocation=resLoc(
        #                    path='/api/v1/inventory/systems/%s' % self.system2.pk,
        #                    port=80),
        #            ),
        #        ),
        #    ])

    def testPostSystemWmiManagementInterface(self):

        # Register a WMI-managed system, and don't post credentials.
        # Make sure the system is in the proper state
        # (NON_RESPONSIVE_CREDENTIALS) and no jobs are pending.
        xmlTempl = """\
<system>
  <network_address>
    <address>172.16.175.240</address>
    <pinned>false</pinned>
  </network_address>
  <name>WmiSystem</name>
  <management_interface href="/api/v1/inventory/management_interfaces/%(mgmtInterfaceId)s"/>
  <managing_zone href="/api/v1/inventory/zones/1"/>
</system>
"""
        mgmtIface = self.mgr.wmiManagementInterface()
        data = xmlTempl % dict(localUuid="aaa", generatedUuid="bbb",
            mgmtInterfaceId=mgmtIface.management_interface_id)
        response = self._post('inventory/systems/', data=data)
        self.failUnlessEqual(response.status_code, 200)
        doc = xobj.parse(response.content)
        systemId = int(doc.system.system_id)
        system = models.System.objects.get(system_id=systemId)
        self.failUnlessEqual(system.current_state.name, 'unmanaged-credentials')
        # No jobs
        self.failUnlessEqual(len(system.systemjob_set.all()), 0)

        self.disablePostCommitActions()

        # Now set credentials
        url = "inventory/systems/%d/credentials" % system.system_id
        response = self._post(url,
            data=testsxml.credentials_xml,
            username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)

        system = models.System.objects.get(system_id=system.system_id)

        # We want a queued registration job
        self.failUnlessEqual(
            [x.job.job_state.name for x in system.systemjob_set.all()],
            ['Queued'])

        self.failUnlessEqual(len(self.devNullList), 1)
        self.failUnlessEqual(system.current_state.name, 'unmanaged')


class TargetSystemImportTest(XMLTestCase, test_utils.RepeaterMixIn):
    fixtures = ['users', 'targets']

    class Driver(object):
        def __init__(self, cloudType, cloudName, userId, instances):
            self.cloudType = cloudType
            self.cloudName = cloudName
            self.instances = instances
            self.userId = userId

        def getAllInstances(self):
            return self.instances

    class TargetInstance(object):
        class _X(object):
            def __init__(self, data):
                self.data = data
            def getText(self):
                return self.data

        def __init__(self, instanceId, instanceName, instanceDescription,
                     dnsName, state):
            self.instanceId = self._X(instanceId)
            self.instanceName = self._X(instanceName)
            self.instanceDescription = self._X(instanceDescription)
            self.state = self._X(state)
            self.dnsName = self._X(dnsName)

    def setUp(self):
        XMLTestCase.setUp(self)
        test_utils.RepeaterMixIn.setUpRepeaterClient(self)

        TI = self.TargetInstance

        self.vsphere1_001 = TI('vsphere1-001', 'Instance 1', 'Instance desc 1',
                    'dnsName1-001', 'running', )
        self.vsphere1_003 = TI('vsphere1-003', 'Instance 3', 'Instance desc 3',
                    'dnsName1-003', 'shutdown', )
        self.vsphere1_004 = TI('vsphere1-004', 'Instance 4', 'Instance desc 4',
                    'dnsName1-004', 'suspended', )

        self.vsphere2_001 = TI('vsphere2-001', 'Instance 1', 'Instance desc 1',
                    'dnsName2-001', 'running', )
        self.vsphere2_003 = TI('vsphere2-003', 'Instance 3', 'Instance desc 3',
                    'dnsName2-003', 'shutdown', )
        self.vsphere2_004 = TI('vsphere2-004', 'Instance 4', 'Instance desc 4',
                    'dnsName2-004', 'suspended', )

        self.ec2_001 = TI('ec2aws-001', 'Instance 1', 'Instance desc 1',
                    'dnsName1-001', 'running', )
        self.ec2_003 = TI('ec2aws-003', 'Instance 3', 'Instance desc 3',
                    'dnsName1-003', 'shutdown', )
        self.ec2_004 = TI('ec2aws-004', 'Instance 4', 'Instance desc 4',
                    'dnsName1-004', 'suspended', )

        self._targets = [
            ('vmware', 'vsphere1.eng.rpath.com', 'JeanValjean1', [
                self.vsphere1_001,
                self.vsphere1_003,
                self.vsphere1_004,
            ]),
            ('vmware', 'vsphere2.eng.rpath.com', 'JeanValjean2', [
                self.vsphere2_001,
                self.vsphere2_003,
            ]),
            ('vmware', 'vsphere2.eng.rpath.com', 'JeanValjean3', [
                self.vsphere2_001,
                self.vsphere2_004,
            ]),
            ('ec2', 'aws', 'JeanValjean1', [
                self.ec2_001,
                self.ec2_003,
                self.ec2_004,
            ]),
        ]

        self.drivers = []

        for (targetType, targetName, userName, systems) in self._targets:
            self.drivers.append(self.Driver(targetType, targetName, userName,
                systems))
        # Set the db version
        from mint.db import schema
        v = rbuildermodels.DatabaseVersion(
            version=schema.RBUILDER_DB_VERSION.major,
            minor=schema.RBUILDER_DB_VERSION.minor)
        v.save()

        zone = self.localZone

        # Create some dummy systems
        self.tgt1 = targetmodels.Target.objects.get(pk=1) # vsphere1
        self.tgt2 = targetmodels.Target.objects.get(pk=2) # vsphere2
        self.tgt3 = targetmodels.Target.objects.get(pk=3) # ec2
        c1 = targetmodels.TargetCredentials.objects.get(pk=1)
        c2 = targetmodels.TargetCredentials.objects.get(pk=2)
        c3 = targetmodels.TargetCredentials.objects.get(pk=3)
        systems = [
            ('vsphere1-001', 'vsphere1 001', self.tgt1, [c2]),
            ('vsphere1-002', 'vsphere1 002', self.tgt1, [c1, c2]),

            ('vsphere2-001', 'vsphere2 001', self.tgt2, [c1]),
            ('vsphere2-002', 'vsphere2 002', self.tgt2, [c3]),
            ('vsphere2-003', 'vsphere2 003', self.tgt2, []),

            ('ec2aws-001', 'ec2aws 001', self.tgt3, [c1]),
            ('ec2aws-002', 'ec2aws 002', self.tgt3, [c3]),
        ]
        for (systemId, systemName, target, credList) in systems:
            description = systemName + " description"
            sy = models.System(name=systemName, target_system_id=systemId,
                target=target, description=description, managing_zone=zone)
            sy.save()
            nw = models.Network(system=sy, dns_name=systemId)
            nw.save()
            for cred in credList:
                stc = models.SystemTargetCredentials(system=sy, credentials=cred)
                stc.save()
        # Modify the network for one of the systems to look real
        sy = models.System.objects.get(target_system_id='vsphere1-001')
        nw = sy.networks.all()[0]
        nw.dns_name = 'dnsName1-001'
        nw.save()

    def testImportTargetSystems(self):
        jobs = self.mgr.sysMgr.importTargetSystems()
        self.failUnlessEqual(
            [ [ y.target.name for y in x.target_jobs.all() ] for x in jobs ],
            [
                ['vsphere2.eng.rpath.com'],
                ['vsphere1.eng.rpath.com'],
                ['vsphere2.eng.rpath.com'],
                ['aws'],
            ])

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            ['targets.configure', 'targets.listInstances'] * 4)
        realCall = calls[-1]
        self.failUnlessEqual(realCall.args, ())
        self.failUnlessEqual(realCall.kwargs, dict(uuid=jobs[-1].job_uuid))
        self.mgr.repeaterMgr.repeaterClient.reset()


    def testIsManageable(self):
        # First, make sure these two users have the same credentials
        user1 = usersmodels.User.objects.get(user_name='JeanValjean1')
        user2 = usersmodels.User.objects.get(user_name='JeanValjean2')
        user3 = usersmodels.User.objects.get(user_name='JeanValjean3')
        self.failUnlessEqual(
            targetmodels.TargetUserCredentials.objects.get(
                target=self.tgt3, user=user1).target_credentials.pk,
            targetmodels.TargetUserCredentials.objects.get(
                target=self.tgt3, user=user2).target_credentials.pk,
        )

        system = models.System.objects.get(target_system_id='ec2aws-002')
        # Mark the system as being launched by user1
        system.launching_user = user1

        # Owner, so manageable
        self.mgr.user = user1
        self.failUnlessEqual(self.mgr.sysMgr.isManageable(system), True)
        # same credentials
        self.mgr.user = user2
        self.failUnlessEqual(self.mgr.sysMgr.isManageable(system), True)
        # Different credentials
        self.mgr.user = user3
        self.failUnlessEqual(self.mgr.sysMgr.isManageable(system), False)

    def testGetSystemWithTarget(self):
        system = models.System.objects.get(target_system_id='vsphere1-002')
        url = 'inventory/systems/%s' % system.pk
        response = self._get(url, username='admin', password='password')
        self.failUnlessEqual(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.system_with_target)

    def testAddLaunchedSystem(self):
        user2 = usersmodels.User.objects.get(user_name='JeanValjean2')
        self.mgr.user = user2
        params = dict(
            target_system_id = "target-system-id-001",
            target_system_name = "target-system-name 001",
            target_system_description = "target-system-description 001",
            target_system_state = "Frisbulating",
        )
        dnsName = 'dns-name-1'
        ipAddress = '1.2.3.4'
        system = self.newSystem(**params)

        system.boot_uuid = bootUuid = str(self.uuid4())
        system.ssl_client_certificate = "ssl client certificate 001"
        system.ssl_client_key = "ssl client key 001"
        # To mimic the workflow from target, we initially add the target
        # system with no networking info
        system = self.mgr.addLaunchedSystem(system,
            targetName=self.tgt2.name,
            targetType=self.tgt2.target_type)
        for k, v in params.items():
            self.failUnlessEqual(getattr(system, k), v)
        # Make sure we have credentials
        stc = list(system.target_credentials.all())[0]
        self.failUnlessIn(stc.credentials_id,
            [ x.target_credentials_id
                for x in user2.target_user_credentials.all() ])
        self.failUnlessEqual(system.managing_zone.name,
            zmodels.Zone.LOCAL_ZONE)
        self.failUnlessEqual(system.target_system_name, params['target_system_name'])
        self.failUnlessEqual(system.name, params['target_system_name'])
        self.failUnlessEqual(system.target_system_description,
            params['target_system_description'])
        self.failUnlessEqual(system.description,
            params['target_system_description'])

        # Test that it got persisted
        savedsystem = models.System.objects.get(pk=system.pk)

        resp = self._get('inventory/systems/%s' % system.system_id,
            username='admin', password='password')
        self.failUnlessEqual(resp.status_code, 200)
        self.failUnlessIn('<launching_user id="http://testserver/api/v1/users/3">',
            resp.content)

        # Make sure we've saved the boot uuid
        cu = connection.cursor()
        cu.execute("""
            SELECT j.job_uuid
              FROM job_system AS js
              JOIN inventory_system AS invsys USING (system_id)
              JOIN jobs AS j ON (js.job_id=j.job_id)
             WHERE invsys.system_id = %s""", [ system.system_id ])
        self.failUnlessEqual([ x[0] for x in cu ],
            [ bootUuid, ])

        # Mingle #1962: don't add the same network entry multiple times
        # Add networks, to pretend the system registered while we were
        # waiting for the target to report its ip address.
        models.Network.objects.filter(system=savedsystem).delete()
        models.Network.objects.create(system=savedsystem,
            dns_name=dnsName, ip_address=ipAddress, device_name='eth0',
            active=True)

        system = self.mgr.addLaunchedSystem(system,
            dnsName=dnsName,
            targetName=self.tgt2.name,
            targetType=self.tgt2.target_type)
        self.failUnlessEqual(
            [ (x.dns_name, x.ip_address) for x in system.networks.all() ],
            [ (dnsName, ipAddress) ])

        def repl(item, a, b):
            try:
                return item.replace(a, b)
            except:
                # booleans don't support this operatiion
                return item

        # Make sure we have an entry in target_system
        tsys = targetmodels.TargetSystem.objects.get(target=system.target,
            target_internal_id=system.target_system_id)
        self.failUnlessEqual(tsys.name, system.name)

        # Another system, no description
        params = dict((x, repl(y, '001', '003'))
            for (x, y) in params.items())
        params['target_system_description'] = None

        system = self.newSystem(**params)

        system = self.mgr.addLaunchedSystem(system,
            dnsName=dnsName,
            targetName=self.tgt2.name,
            targetType=self.tgt2.target_type)

        self.failUnlessEqual(system.target_system_name, params['target_system_name'])
        self.failUnlessEqual(system.name, params['target_system_name'])
        self.failUnlessEqual(system.target_system_description,
            params['target_system_description'])
        self.failUnlessEqual(system.description, params['target_system_description'])
        tsys = targetmodels.TargetSystem.objects.get(target=system.target,
            target_internal_id=system.target_system_id)
        self.failUnlessEqual(tsys.name, system.name)
        self.failUnlessEqual(tsys.description, '')

        # Another system that specifies a name and description
        params = dict((x, repl(y, '003', '002'))
            for (x, y) in params.items())
        params.update(name="system-name-002",
            description="system-description-002")
        system = self.newSystem(**params)

        system = self.mgr.addLaunchedSystem(system,
            dnsName=dnsName,
            targetName=self.tgt2.name,
            targetType=self.tgt2.target_type)

        self.failUnlessEqual(system.target_system_name, params['target_system_name'])
        self.failUnlessEqual(system.name, params['name'])
        self.failUnlessEqual(system.target_system_description,
            params['target_system_description'])
        self.failUnlessEqual(system.description, params['description'])

    def testAddLaunchedSystem2(self):
        systemConfiguration = "<system_configuration><a>1</a><b>2</b></system_configuration>"
        user2 = usersmodels.User.objects.get(user_name='JeanValjean2')
        self.mgr.user = user2
        params = dict(
            target_system_id = "target-system-id-001",
            target_system_name = "target-system-name 001",
            target_system_description = "target-system-description 001",
            target_system_state = "Frisbulating",
            created_by = user2,
            management_interface = models.Cache.get(models.ManagementInterface,
                name=models.ManagementInterface.CIM),
        )
        system = self.newSystem(**params)

        system.boot_uuid = bootUuid = str(self.uuid4())
        system.ssl_client_certificate = "ssl client certificate 001"
        system.ssl_client_key = "ssl client key 001"

        system = self.mgr.addLaunchedSystem(system,
            targetName=self.tgt2.name,
            targetType=self.tgt2.target_type,
            configurationData=systemConfiguration,
            )
        for k, v in params.items():
            self.failUnlessEqual(getattr(system, k), v)

        savedsystem = models.System.objects.get(pk=system.pk)
        self.assertXMLEquals(savedsystem.configuration, systemConfiguration)
        self.assertEquals(bool(savedsystem.configuration_set), True)

        # System registers and passes a boot uuid
        params = dict(localUuid=str(self.uuid4()),
            generatedUuid=str(self.uuid4()),
            ipAddress='10.10.10.10',
            bootUuid=bootUuid)

        xml = """\
<system>
  <local_uuid>%(localUuid)s</local_uuid>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <boot_uuid>%(bootUuid)s</boot_uuid>
  <hostname>bluetorch.example.com</hostname>
  <networks>
    <network>
      <ip_address>%(ipAddress)s</ip_address>
      <dns_name>%(ipAddress)s</dns_name>
    </network>
  </networks>
</system>
""" % params
        url = "inventory/systems"
        response = self._post(url, data=xml)
        self.assertEquals(response.status_code, 200)

        # We should have a job
        self.assertEquals([ j.job_type.name for j in savedsystem.jobs.all() ],
            ['system apply configuration'])

    def testCaptureSystem(self):
        user2 = usersmodels.User.objects.get(user_name='JeanValjean2')
        self.mgr.user = user2
        params = dict(
            target_system_id = "target-system-id-001",
            target_system_name = "target-system-name 001",
            target_system_description = "target-system-description 001",
            target_system_state = "Frisbulating",
            _ssl_client_certificate = "ssl client certificate 001",
            _ssl_client_key = "ssl client key 001",
        )
        dnsName = 'dns-name-1'
        system = self.newSystem(**params)
        system = self.mgr.addLaunchedSystem(system,
            dnsName=dnsName,
            targetName=self.tgt2.name,
            targetType=self.tgt2.target_type)

        stage = projectmodels.Stage.objects.filter(project__name='chater-foo',
            name='Development')[0]
        params = dict(stage=stage, imageName="foo image")
        self.mgr.captureSystem(system, params)

class CollectionTest(XMLTestCase):
    fixtures = ['system_collection']

    def xobjResponse(self, url):
        response = self._get(url,
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        return systems

    def testGetDefaultCollection(self):
        response = self._get('inventory/systems/',
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.per_page, '10')
        self.assertEquals(systems.start_index, '0')
        self.assertEquals(systems.end_index, '9')
        self.assertTrue(systems.next_page.endswith(
            '/api/v1/query_sets/5/all;start_index=10;limit=10'))
        self.assertEquals(systems.previous_page, '')
        self.assertEquals(systems.order_by, '')
        self.assertEquals(systems.filter_by, '')

    def testGetNextPage(self):
        response = self._get('inventory/systems/',
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        response = self._get(systems.next_page,
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.per_page, '10')
        self.assertEquals(systems.start_index, '10')
        self.assertEquals(systems.end_index, '19')
        self.assertTrue(systems.next_page.endswith(
            '/api/v1/query_sets/5/all;start_index=20;limit=10'))
        self.assertTrue(systems.previous_page.endswith(
            '/api/v1/query_sets/5/all;start_index=0;limit=10'))
        self.assertEquals(systems.order_by, '')
        self.assertEquals(systems.filter_by, '')

    def testGetPreviousPage(self):
        response = self._get('inventory/systems/',
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        response = self._get(systems.next_page,
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        response = self._get(systems.previous_page,
            username="admin", password="password")
        xobjModel = xobj.parse(response.content)
        systems = xobjModel.systems
        self.assertEquals(systems.per_page, '10')
        self.assertEquals(systems.start_index, '0')
        self.assertEquals(systems.end_index, '9')
        self.assertTrue(systems.next_page.endswith(
            '/api/v1/query_sets/5/all;start_index=10;limit=10'))
        self.assertEquals(systems.previous_page, '')
        self.assertEquals(systems.order_by, '')
        self.assertEquals(systems.filter_by, '')

    def testOrderBy(self):
        systems = self.xobjResponse('/api/v1/inventory/systems;order_by=name')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            ['10', '100', '101', '102', '103', '104', '105', '106', '107', '108'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;order_by=name')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;order_by=name')
        self.assertEquals(systems.order_by, 'name')
        systems = self.xobjResponse('/api/v1/inventory/systems;order_by=-name')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            ['rPath Update Servic', '99', '98', '97', '96', '95', '94', '93', '92', '91'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;order_by=-name')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;order_by=-name')
        self.assertEquals(systems.order_by, '-name')

    def testQueryTree(self):
        from mint.django_rest.rbuilder.modellib import collections
        q = collections.AndOperator(
               # port=8080 for a given type of configurator
               collections.AndOperator(
                   collections.EqualOperator('latest_survey.survey_config.type', '0'),
                   collections.EqualOperator('latest_survey.survey_config.value', '8080'),
                   collections.LikeOperator('latest_survey.survey_config.key', '/port'),
               ),
               # name has substring either a or not e (super arbitrary) 
               collections.OrOperator(
                   collections.LikeOperator('latest_survey.rpm_packages.rpm_package_info.name', 'a'),
                   collections.NotLikeOperator('latest_survey.rpm_packages.rpm_package_info.name', 'e'),
               )
        )

        # shorter form!
        q2 = collections.AndOperator(
               collections.ContainsOperator('latest_survey.survey_config', collections.AndOperator(
                   collections.EqualOperator('type', '0'),
                   collections.EqualOperator('value', '8080'),
                   collections.LikeOperator('key', '/port'),
               )),
               collections.ContainsOperator('latest_survey.rpm_packages.rpm_package_info', collections.OrOperator(
                   collections.LikeOperator('name', 'a'),
                   collections.NotLikeOperator('name', 'e'),
               ))
        )

        test1 = 'AND(AND(EQUAL(latest_survey.survey_config.type,0),EQUAL(latest_survey.survey_config.value,8080),LIKE(latest_survey.survey_config.key,/port)),OR(LIKE(latest_survey.rpm_packages.rpm_package_info.name,a),NOT_LIKE(latest_survey.rpm_packages.rpm_package_info.name,e)))'
        test2 = 'AND(CONTAINS(latest_survey.survey_config,AND(EQUAL(type,0),EQUAL(value,8080),LIKE(key,/port))),CONTAINS(latest_survey.rpm_packages.rpm_package_info,OR(LIKE(name,a),NOT_LIKE(name,e))))'
        self.assertEquals(q.asString(), test1)
        self.assertEquals(q2.asString(), test2)

        # test the queryset/SQL builder engine
        djQs = collections.filterTree(models.System.objects.all(), q).query
        djQs2 = collections.filterTree(models.System.objects.all(), q2).query
        self.assertEquals(str(djQs),str(djQs2))

        # Lexer...
        lexer = collections.Lexer()
        tree = lexer.scan(test1)
        self.assertEquals(tree.asString(), test1)
        self.assertEquals(tree, q)

        # Simpler tests
        tests = [
            (collections.EqualOperator('key', 'port'), 'EQUAL(key,port)'),
            (collections.EqualOperator('key', r'a "quoted" value'),
                r'EQUAL(key,"a \"quoted\" value")'),
            (collections.EqualOperator('key', r'Extra ( and ), backslash \ stray \n\r and "'),
                r'EQUAL(key,"Extra ( and ), backslash \\ stray \\n\\r and \"")'),
            # No need to add quotes around a word with \ in it
            (collections.EqualOperator('key', r'with \ within'),
                r'EQUAL(key,with \\ within)'),
        ]
        for q, strrepr in tests:
            tree = lexer.scan(strrepr)
            self.assertEquals(tree, q)
            self.assertEquals(q.asString(), strrepr)
            self.assertEquals(tree.asString(), strrepr)

        # One-way tests - extra quotes that get stripped out etc
        tests = [
            (collections.EqualOperator('key', r'with \ within'),
                r'EQUAL(key,"with \\ within")'),
            (collections.EqualOperator('key', 'port'), 'EQUAL(key,"port")'),
            (collections.EqualOperator('key', ' value with spaces '),
                ' EQUAL ( key ,  " value with spaces "  )'),
        ]
        for q, strrepr in tests:
            tree = lexer.scan(strrepr)
            self.assertEquals(tree, q)

        # Errors
        tests = [
            ('EQUAL(key,"port)', 'Closing quote not found'),
            ('abc', 'Unable to parse abc'),
            ('FOO(key,"port)', 'Unknown operator FOO'),
            ('EQUAL(key,port)junk', "Garbage found at the end of the expression: 'junk'"),
            ('EQUAL(key,port', 'Unable to parse EQUAL(key,port'),
        ]
        InvalidData = collections.errors.InvalidData
        for strrepr, err in tests:
            e = self.assertRaises(InvalidData, lexer.scan, strrepr)
            self.assertEquals(e.msg, err)

    def testFilterBy(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=[name,LIKE,3]')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'3', u'13', u'23', u'30', u'31', u'32', u'33', u'34', u'35', u'36'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.filter_by,
            '[name,LIKE,3]')
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=[name,NOT_LIKE,3]')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'rPath Update Servic', u'4', u'5', u'6', u'7', u'8', u'9', u'10', u'11', u'12'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;filter_by=[name,NOT_LIKE,3]')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;filter_by=[name,NOT_LIKE,3]')
        self.assertEquals(systems.filter_by,
            '[name,NOT_LIKE,3]')
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=[name,NOT_LIKE,3],[description,NOT_LIKE,Update]')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'4', u'5', u'6', u'7', u'8', u'9', u'10', u'11', u'12', u'14'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;filter_by=[name,NOT_LIKE,3],[description,NOT_LIKE,Update]')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;filter_by=[name,NOT_LIKE,3],[description,NOT_LIKE,Update]')
        self.assertEquals(systems.filter_by,
            '[name,NOT_LIKE,3],[description,NOT_LIKE,Update]')

    def testFilterBy2(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=LIKE(name,3)')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'3', u'13', u'23', u'30', u'31', u'32', u'33', u'34', u'35', u'36'])

    def testFilterByIn(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=IN(system_id,1, 3 , 5)')
        self.assertEquals([x.system_id for x in systems.system],
            ['3', '5'])

    def testFilterByAndIn(self):
        # RCE-1158
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=AND(IS_NULL(local_uuid,false),IN(system_id,1, 3 , 5))')
        self.assertEquals([x.system_id for x in systems.system],
            ['3', '5'])

    def testFilterByIsNull(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=IS_NULL(local_uuid,true)')
        self.assertEquals([x.system_id for x in systems.system],
            ['2', '50'])

    def testOrderAndFilterBy(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=[name,LIKE,3];order_by=-name')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'93', u'83', u'73', u'63', u'53', u'43', u'39', u'38', u'37', u'36'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.filter_by,
            '[name,LIKE,3]')
        self.assertEquals(systems.order_by,
            '-name')
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.filter_by,
            '[name,LIKE,3]')
        self.assertEquals(systems.order_by,
            '-name')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'93', u'83', u'73', u'63', u'53', u'43', u'39', u'38', u'37', u'36'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.filter_by,
            '[name,LIKE,3]')
        self.assertEquals(systems.order_by,
            '-name')

    def testLimit(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;limit=5')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'rPath Update Servic', u'3', u'4', u'5', u'6'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=5')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=5;limit=5')
        self.assertEquals(systems.limit, '5')

    def testOrderAndFilterAndLimitBy(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;limit=5;filter_by=[name,LIKE,3];order_by=-name')
        self.assertEquals([x.name.strip('System name ') for x in systems.system],
            [u'93', u'83', u'73', u'63', u'53'])
        self.assertEquals(systems.id,
            'http://testserver/api/v1/query_sets/5/all;start_index=0;limit=5;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.next_page,
            'http://testserver/api/v1/query_sets/5/all;start_index=5;limit=5;order_by=-name;filter_by=[name,LIKE,3]')
        self.assertEquals(systems.limit,
            '5')
        self.assertEquals(systems.filter_by,
            '[name,LIKE,3]')
        self.assertEquals(systems.order_by,
            '-name')

    def testFilterByBoolean(self):
        systems = self.xobjResponse(
            '/api/v1/inventory/systems;filter_by=[local_uuid,IS_NULL,True]')
        # System 50 and the Update Service are the only one set up with a null
        # local_uuid in the fixture
        self.assertEquals([x.system_id for x in systems.system],
            [u'2', u'50'])

refProductDefintion1 = """\
<?xml version='1.0' encoding='UTF-8'?>
<productDefinition xmlns="http://www.rpath.com/permanent/rpd-2.0.xsd" xmlns:xsi=
"http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-2.0.xsd rpd-2.0.xsd" version="2.0">
  <productName>My Awesome Appliance</productName>
  <productShortname>awesome</productShortname>
  <productDescription>Awesome</productDescription>
  <productVersion>1.0</productVersion>
  <productVersionDescription>Awesome Version</productVersionDescription>
  <conaryRepositoryHostname>product.example.com</conaryRepositoryHostname>
  <conaryNamespace>exm</conaryNamespace>
  <imageGroup>group-awesome-dist</imageGroup>
  <baseFlavor>is: x86 x86_64</baseFlavor>
  <stages>
    <stage labelSuffix="-devel" name="devel"/>
    <stage labelSuffix="-qa" name="qa"/>
    <stage labelSuffix="" name="release"/>
  </stages>
  <searchPaths/>
</productDefinition>
"""

class Retirement(XMLTestCase):
    '''
    Some tests above attempt to test retirement in the model, this is an API
    test.
    '''
    def setUp(self):
        # make a new system
        XMLTestCase.setUp(self)
        self.system = self.newSystem(name="blinky", description="ghost")
        self.system.management_interface = models.ManagementInterface.objects.get(name='ssh')
        self.mgr.addSystem(self.system)

    def testRetire(self):
        generatedUuid = 'generateduuid001'
        localUuid = 'localuuid001'

        system = self.newSystem(name='blippy', local_uuid=localUuid,
             generated_uuid=generatedUuid)
        system.current_state = self.mgr.sysMgr.systemState(
            models.SystemState.RESPONSIVE)
        system.save()

        response = self._get("inventory/systems/%s" % self.system.pk,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)

        response = self._post('inventory/systems/%s/credentials' % \
            self.system.pk,
            data=testsxml.credentials_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)

        params = dict(
            localUuid=localUuid,
            generatedUuid=generatedUuid,
            zoneId=self.localZone.zone_id
        )
        xml = testsxml.retirement_xml % params

        # response from put indicates same state as subsequent get
        response = self._put("inventory/systems/%s" % self.system.pk,
            username='admin', password='password', data=testsxml.retirement_xml)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        xObjModel = obj.system
        self.failUnlessEqual(obj.system.current_state.name, "mothballed")

        response = self._get("inventory/systems/%s" % self.system.pk,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        xObjModel = obj.system
        self.failUnlessEqual(obj.system.current_state.name, "mothballed")


class AntiRecursiveSaving(XMLTestCase):
    '''
       Generalized xobj test.  Make sure that when saving an object with child members,
    in this case a system & a management interface, and we go to EDIT
    that system, we can't CREATE a new, non-existant management interface OR
    rename an existing management interface.   This, if present, would
    allow for priveledge escalation.
    '''
    def setUp(self):
        # make a new system
        XMLTestCase.setUp(self)
        self.system = self.newSystem(name="blinky", description="ghost")
        self.system.management_interface = models.ManagementInterface.objects.get(name='ssh')
        self.mgr.addSystem(self.system)

    def testCannotModifySubObjects(self):
        # make sure that fields in foreign key relationships, when saved,
        # do not allow editing the object represented by the FK.
        response = self._get("inventory/systems/%s" % self.system.pk,
            username='admin', password='password')
        xml = response.content
        self.assertEquals(response.status_code, 200)
        xml2 = xml.replace("Secure Shell (SSH)", "Special Hacker Interface (SHI)")
        response = self._put("inventory/systems/%s" % self.system.pk,
            data=xml2, username='admin', password='password')
        # this raised a 400 because one of the objects we tried to save
        # did not exist, bad input.
        self.assertEquals(response.status_code, 400)
        response = self._get("inventory/systems/%s" % self.system.pk,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(response.content.find("Hacker Interface") == -1)

    def testCannotCreateNewSubObjects(self):
        # make sure we do not allow creating new sub objects on a put.
        response = self._get("inventory/systems/%s" % self.system.pk,
            username='admin', password='password')
        xml = response.content
        xml2 = xml.replace("management_interfaces/3", "management_interfaces/9999")
        xml2 = xml2.replace("Secure Shell (SSH)", "Special Hacker Interface (SHI)")
        response = self._put("inventory/systems/%s" % self.system.pk,
            data=xml2, username='admin', password='password')
        self.assertTrue(response.status_code, 200)
        response = self._get("inventory/systems/%s" % self.system.pk,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(response.content.find("Hacker Interface") == -1)
        self.assertTrue(response.content.find("management_interfaces/4") == -1)

    def testPostShouldNotInjectNewSubObjects(self):
        # make sure we do not allow saving new sub objects on a post...
        response = self._post("inventory/systems",
            username='admin', password='password',
            data=testsxml.system_post_forge_object)
        # sub object didn't exist, so causes a 400, bad input
        self.assertEquals(response.status_code, 400)
        interfaces = list(models.ManagementInterface.objects.all())
        self.assertEquals(len(interfaces), 3, 'no interfaces added')

class DescriptorTestCase(XMLTestCase, test_utils.RepeaterMixIn):
    def setUp(self):
        XMLTestCase.setUp(self)
        self.setUpRepeaterClient()

    def testGetImageMetadataImportDescriptor(self):
        response = self._get("inventory/image_import_metadata_descriptor",
            username='testuser', password='password')
        self.failUnlessEqual(response.status_code, 200)
        obj = xobj.parse(response.content)
        fields = obj.descriptor.dataFields.field
        # These are coming from test_utils, not from the real descriptor
        self.failUnlessEqual(
            [x.name for x in fields],
            ['metadata.owner', 'metadata.admin'])

class ModuleHooksTest(XMLTestCase):
    """
    Added here, so we don't add modulehooks as a django app. Surprisingly,
    it seems to work, minus the testsuite being run.
    """
    def testGetModuleHooks(self):
        moduleHooksDir = self.mintCfg.moduleHooksDir
        os.makedirs(self.mintCfg.moduleHooksDir)
        # Some extensions
        for i in range(5):
            file(os.path.join(moduleHooksDir, 'file-%d.swf' % i), "w")
        # Some dummy files
        for i in range(3):
            file(os.path.join(moduleHooksDir, 'file-%d.blah' % i), "w")

        response = self._get("module_hooks",
            username="testuser", password="password")
        self.failUnlessEqual(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(int(obj.module_hooks.count), 5)
        self.failUnlessEqual(
            sorted(x.url for x in obj.module_hooks.module_hook),
                [
                    'hooks/file-0.swf',
                    'hooks/file-1.swf',
                    'hooks/file-2.swf',
                    'hooks/file-3.swf',
                    'hooks/file-4.swf',
                ])

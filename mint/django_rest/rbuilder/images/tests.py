from testutils import mock
import testsxml
from xobj import xobj

import logging
logging.disable(logging.CRITICAL)

from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

from mint.lib import uuid
from mint.django_rest.rbuilder.images import models
from mint.django_rest.rbuilder.inventory import models as invmodels
from mint.django_rest.rbuilder.jobs import models as jobsmodels
from mint.django_rest.rbuilder.projects import models as projectsmodels
from mint.django_rest.rbuilder.users import models as usermodels
from mint.django_rest.rbuilder.rbac import models as rbacmodels
from mint.django_rest.rbuilder.querysets import models as querymodels
from mint.django_rest.rbuilder.rbac.tests import RbacEngine
from mint.django_rest import timeutils

class ImagesTestCase(RbacEngine):

    def setUp(self):
        RbacEngine.setUp(self)
        self._init()

    def _init(self):
        mock.mock(self.mgr, "createRepositoryForProject")
        user1 = usermodels.User(
            user_name='jimphoo', full_name='Jim Phoo', email='jimphoo@noreply.com')
        user1.save()
        user2 = usermodels.User(
            user_name='janephoo', full_name='Jane Phoo', email='janephoo@noreply.com')
        user2.save()

        for i in range(3):
            # make project
            proj = self.addProject("foo%s" % i, domainName='eng.rpath.com')
            # and branch
            branch = projectsmodels.ProjectVersion(
                project=proj, name="trunk", label="foo%s.eng.rpath.com@rpath:foo-trunk" % i)
            branch.save()
            # now make stages
            stage = projectsmodels.Stage(project=proj,
                project_branch=branch, name="Development", label="foo%s@ns:trunk-devel" % i)
            stage.save()
            stage = projectsmodels.Stage(project=proj,
                project_branch=branch, name="QA", label="foo%s@ns:trunk-qa" % i)
            stage.save()
            stage = projectsmodels.Stage(project=proj,
                project_branch=branch, name="Stage", label="foo%s@ns:trunk-stage" % i)
            stage.save()
            stage = projectsmodels.Stage(project=proj,
                project_branch=branch, name="Release", label="foo%s@ns:trunk" % i)
            stage.save()
            # release
            release = projectsmodels.Release(project=proj,
                name='release%s' % i, version='releaseVersion%s' % i, description='description%s' % i,
                created_by=user1, updated_by=user2, published_by=user2)
            release.save()
            # images
            image = models.Image(
                project=proj, release=release, _image_type=10, job_uuid='1',
                name="image-%s" % i, trove_name='troveName%s' % i, trove_version='/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-%d-1' % i,
                trove_flavor='1#x86:i486:i586:i686|5#use:~!xen', created_by=user1, updated_by=user2, image_count=1,
                output_trove=None, project_branch=branch, stage_name='stage%s' % i,
                description="image-%s" % i)
            image.save()
            # now buildfiles and fileurls
            buildFile = models.BuildFile(image=image, size=i, sha1='%s' % i)
            buildFile.save()
            
            fileUrl = models.FileUrl(url_type=0, url='http://example.com/%s/' % i)
            fileUrl.save()
            
            buildFilesUrlsMap = models.BuildFilesUrlsMap(file=buildFile, url=fileUrl)
            buildFilesUrlsMap.save()
            
            buildFile = models.BuildFile(image=image, size=i+1, sha1='%s' % (i + 1))
            buildFile.save()
        
            fileUrl = models.FileUrl(url_type=0, url='http://example.com/%s/' % (i + 1))
            fileUrl.save()
        
            buildFilesUrlsMap = models.BuildFilesUrlsMap(file=buildFile, url=fileUrl)
            buildFilesUrlsMap.save()
            
        self._setupRbac()

    # invalidate the querysets so tags can be applied
    def _retagQuerySets(self):
        self.mgr.retagQuerySetsByType('project')
        self.mgr.retagQuerySetsByType('image')
            
    def _setupRbac(self):
 
        # RbacEngine test base class has already done a decent amount of setup
        # now just add the grants for the things we are working with

        role              = rbacmodels.RbacRole.objects.get(name='developer')
        self.all_projects = querymodels.QuerySet.objects.get(name='All Projects')
        self.all_images   = querymodels.QuerySet.objects.get(name='All Images')
        modmembers        = rbacmodels.RbacPermissionType.objects.get(name='ModMembers')
        readset           = rbacmodels.RbacPermissionType.objects.get(name='ReadSet')
        createresource    = rbacmodels.RbacPermissionType.objects.get(name='CreateResource')
        admin             = usermodels.User.objects.get(user_name='admin')

        for queryset in [ self.all_projects, self.all_images ]:
            for permission in [ modmembers, createresource, readset  ]:
                rbacmodels.RbacPermission(
                    queryset      = queryset,
                    role          = role,
                    permission    = permission,
                    created_by    = admin,
                    modified_by   = admin,
                    created_date  = timeutils.now(),
                    modified_date = timeutils.now()
                ).save()

        self._retagQuerySets()

    # def testCanListAndAccessImages(self):
    # 
    #     # WARNING --
    #     # these are just stub tests until we can resolve what the unified
    #     # images table looks like.  We'll need real ones later that
    #     # inject items into the DB.
    # 
    #     # once rbac for images is implemented this should redirect to a queryset
    #     # for now, it's just a stub
    #     url = 'images/'
    #     response = self._get(url, username='admin', password='password')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertXMLEquals(response.content, testsxml.images_get_xml)
    #  
    #     # also a stub
    #     url = "images/1"
    #     response = self._get(url, username='admin', password='password')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertXMLEquals(response.content, testsxml.image_get_xml)
    #

    def testGetImages(self):
        response = self._get('images/', username='admin', password='password')
        self.assertEquals(response.status_code, 200)

        # now as non-admin, should get filtered results, full contents
        response = self._get('images/', username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        
        # now as user with no permissions, should get 0 results post redirect
        # pending redirection code change (FIXME)
        # response = self._get('images/', username='testuser', password='password')
        # self.assertEquals(response.status_code, 403)

    def testGetImage(self):

        image = models.Image.objects.get(pk=1)
        url = "images/%s" % image.pk

        response = self._get(url, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.image_get_xml)
        
        response = self._get(url, username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        
        response = self._get(url, username='testuser', password='password')
        self.assertEquals(response.status_code, 403)

    def testGetImageBuildFiles(self):
        image = models.Image.objects.get(pk=1)
        url = "images/%s/build_files/" % image.pk
        
        response = self._get(url, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.build_files_get_xml)
        
        response = self._get(url, username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        
        response = self._get(url, username='testuser', password='password')
        self.assertEquals(response.status_code, 403)
        
    def testGetImageBuildFile(self):
        buildFile = models.BuildFile.objects.get(pk=1)
        url = "images/%s/build_files/%s/" % (buildFile.image_id, buildFile.pk)

        response = self._get(url, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.build_file_get_xml)

        response = self._get(url, username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)

        response = self._get(url, username='testuser', password='password')
        self.assertEquals(response.status_code, 403)
        
    def _testCreateImage(self, username, expected_code):
        url = 'images/'
        response = self._post(url, username=username, password='password', data=testsxml.image_post_xml)
        self.assertEquals(response.status_code, expected_code)
        if expected_code == 200:
            image = xobj.parse(response.content)
            self.assertEquals(image.image.name, 'image-20')
            self.assertEquals(image.image.trove_name, 'troveName20')
            self.assertEquals(image.image.image_id, u'4')
       
    def testCreateImageAdmin(self):
        self._testCreateImage('admin', 200)

    def testCreateImageNonAdmin(self):
        self._testCreateImage('ExampleDeveloper', 200)

    def testCreateImageNoAuthz(self):
        self._testCreateImage('testuser', 403)
 
    def _testUpdateImage(self, username, expected_code):
        response = self._post('images/',
            username=username, password='password', data=testsxml.image_post_xml)
        self.assertEquals(response.status_code, expected_code)
        if expected_code != 200:
            return
        image = xobj.parse(response.content)
        response = self._put('images/%s' % image.image.image_id,
            username=username, password='password', data=testsxml.image_put_xml)
        self.assertEquals(response.status_code, expected_code)
        image_updated = xobj.parse(response.content)
        self.assertEquals(image_updated.image.trove_name, 'troveName20-Changed')
        
    def testUpdateImageAdmin(self):
        self._testUpdateImage('admin', 200)
 
    def testUpdateImageNonAdmin(self):
        self._testUpdateImage('ExampleDeveloper', 200)

    def testUpdateImageNoAuthz(self):
        self._testUpdateImage('testuser', 403)

    def _testDeleteImage(self, username, expected_code):
        response = self._delete('images/1', username=username, password='password')
        self.assertEquals(response.status_code, expected_code)
        
    def testDeleteImageAdmin(self):
        self._testDeleteImage('admin', 204)

    def testDeleteImageNonAdmin(self):
        self._testDeleteImage('ExampleDeveloper', 204)

    def testDeleteImageNoAuthz(self):
        self._testDeleteImage('testuser', 403)

    def _testCreateImageBuildFile(self, username, expected_code):
        response = self._post('images/1/build_files/',
            username=username, password='password', data=testsxml.build_file_post_xml)
        self.assertEquals(response.status_code, expected_code)
        if expected_code == 200:
            self.assertXMLEquals(response.content, testsxml.build_file_posted_xml)

    def testCreateImageBuildFileAdmin(self):
        self._testCreateImageBuildFile('admin', 200)

    def testCreateImageBuildFileNonAdmin(self):
        self._testCreateImageBuildFile('ExampleDeveloper', 200)

    def testCreateImageBuildFileNoAuthz(self):
        self._testCreateImageBuildFile('testuser', 403)

    def _testUpdateImageBuildFile(self, username, expected_code):
        response = self._post('images/1/build_files/',
            username=username, password='password', data=testsxml.build_file_post_xml)
        self.assertEqual(response.status_code, expected_code)
        if expected_code != 200:
            return
        buildFile = xobj.parse(response.content)
        file_id = buildFile.file.file_id
        response = self._put('images/1/build_files/%s' % file_id,
            username=username, password='password', data=testsxml.build_file_put_xml)
        self.assertEquals(response.status_code, expected_code)
        buildFileUpdated = xobj.parse(response.content)
        self.assertEquals(buildFileUpdated.file.title, 'newtitle')

    def testUpdateImageBuildFileAdmin(self):
        self._testUpdateImageBuildFile('admin', 200)

    def testUpdateImageBuildFileNonAdmin(self):
        self._testUpdateImageBuildFile('ExampleDeveloper', 200)

    def testUpdateImageBuildFileNoAuthz(self):
        self._testUpdateImageBuildFile('testuser', 403)

    def testUpdateImageBuildFileAuthToken(self):
        user = self.getUser('testuser')
        self.mgr.user = user

        # Needed by setTargetUserCredentials
        class Auth(object):
            def __init__(self, user):
                self.userId = user.user_id
                self.user = user

        self.mgr._auth = Auth(user)

        img = models.Image.objects.get(name='image-0')
        imgFile = img.files.all()[0]
        targetImageId = str(uuid.uuid4())

        # We need a job for authentication
        jobUuid = str(uuid.uuid4())
        jobToken = str(uuid.uuid4())
        job = self._newJob(jobUuid, jobToken=jobToken,
            jobType=jobsmodels.EventType.TARGET_DEPLOY_IMAGE,
            createdBy=user)
        models.JobImage.objects.create(job=job, image=img)
        tgtType = self.mgr.getTargetTypeByName('vmware')

        tgt = self.mgr.createTarget(tgtType, 'tgtname',
            dict(zone='Local rBuilder'))
        self.mgr.setTargetUserCredentials(tgt, dict(username='foo', password='bar'))

        xmlTemplate = """\
<file>
  <target_images>
    <target_image>
      <target id="/api/v1/targets/%(targetId)s"/>
      <image id="id1">
        <imageId>id1</imageId>
        <longName>long name for id1</longName>
        <shortName>short name for id1</shortName>
        <productName>product name for id1</productName>
        <internalTargetId>%(targetImageId)s</internalTargetId>
      </image>
    </target_image>
  </target_images>
</file>
"""
        xml = xmlTemplate % dict(targetId=tgt.target_id,
            targetImageId=targetImageId)
        url = 'images/%s/build_files/%s' % (img.image_id, imgFile.file_id)
        xml = xml
        response = self._put(url, data=xml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        doc = xobj.parse(response.content)
        self.failUnlessEqual(doc.file.file_id, str(imgFile.file_id))
        # Make sure the target image id was saved
        tids = imgFile.targetimagesdeployed_set.all()
        self.failUnlessEqual(
            [ x.target_image_id for x in tids ],
            [ targetImageId ])

    def _testDeleteImageBuildFile(self, username, expected_code):
        response = self._delete('images/1/build_files/1', username=username, password='password')
        self.assertEquals(response.status_code, expected_code)

    def testDeleteImageBuildFileAdmin(self):
        self._testDeleteImageBuildFile('admin', 204)

    def testDeleteImageBuildFileNonAdmin(self):
        self._testDeleteImageBuildFile('ExampleDeveloper', 204)

    def testDeleteImageBuildFileNonAuthz(self):
        self._testDeleteImageBuildFile('testuser', 403)
        
    def testGetRelease(self):
        url = 'releases/1'
        response = self._get(url, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.release_get_xml)

        response = self._get(url, username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        
        response = self._get(url, username='testuser', password='password')
        self.assertEquals(response.status_code, 403)
        
    def testGetReleases(self):

        # there is no releases queryset so nothing to redirect to, only admins
        # can read this
        url = 'releases/'
        response = self._get(url, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.releases_get_xml)
        
        # FIXME: non-admin accessing admin resources in API returns wrong
        # error code, fix @access.admin!
        response = self._get(url, username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 401)  # should be 403

    def _testCreateRelease(self, username, expected_code):

        response = self._post('releases/',
            username=username, password='password', data=testsxml.release_post_xml)
        self.assertEquals(response.status_code, expected_code)
        if expected_code != 200:
            return
        release = xobj.parse(response.content).release
        self.assertEquals(release.name, u'release100')
        self.assertEquals(release.description, u'description100')
        self.assertEquals(release.project.id, u"http://testserver/api/v1/projects/foo0")
        self.assertEquals(release.published_by.id, u"http://testserver/api/v1/users/2002")
        
    def testCreateReleaseAdmin(self):
        self._testCreateRelease('admin', 200)

    def testCreateReleaseNonAdmin(self):
        self._testCreateRelease('ExampleDeveloper', 200)

    def testCreateReleaseNoAuth(self):
        self._testCreateRelease('testuser', 403)

    def _testUpdateRelease(self, username, expected_code):
        response = self._put('releases/1',
            username=username, password='password', data=testsxml.release_put_xml)
        self.assertEquals(response.status_code, expected_code)
        if expected_code == 200:
            release = xobj.parse(response.content).release
            self.assertEquals(release.name, u'release100')
            self.assertEquals(release.description, u'description100')
            self.assertEquals(release.version, u'releaseVersion100')
        
    def testUpdateReleaseAdmin(self):
        self._testUpdateRelease('admin', 200)

    def testUpdateReleaseNonAdmin(self):
        self._testUpdateRelease('ExampleDeveloper', 200)

    def testUpdateReleaseNoAuthz(self):
        self._testUpdateRelease('testuser', 403)

    def testDeleteRelease(self):
        response = self._delete('releases/1', username='admin', password='password')
        self.assertEquals(response.status_code, 204)
        
    def _testGetUrlFileByBuildFile(self, username, expected_code):
        response = self._get('images/1/build_files/1/file_url', username=username, password='password')
        self.assertEquals(response.status_code, expected_code)
        if expected_code != 200:
            return
        self.assertXMLEquals(response.content, testsxml.build_file_url_get_xml)
        response = self._get('images/3/build_files/3/file_url', username=username, password='password')
        self.assertEquals(response.status_code, expected_code)
        fileUrl = xobj.parse(response.content).file_url
        self.assertEquals(fileUrl.url, u'http://example.com/1/')
        self.assertEquals(fileUrl.url_type, u'0')

    def testGetUrlFileByBuildFileAdmin(self):
        self._testGetUrlFileByBuildFile('admin', 200)

    def testGetUrlFileByBuildFileNonAdmin(self):
        self._testGetUrlFileByBuildFile('ExampleDeveloper', 200)

    def testGetUrlFileByBuildFileNoAuthz(self):
        self._testGetUrlFileByBuildFile('testuser', 403)
        
    def testGetBuildLog(self):
        url = 'images/3/build_log'
        response = self._get(url, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        response = self._get(url, username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        response = self._get(url, username='testuser', password='password')
        self.assertEquals(response.status_code, 403)

    def testGetImageTypes(self):
        # is anonymous
        response = self._get('image_types/', username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.image_types_get_xml)
        
    def testGetImageType(self):
        # is anonymous
        response = self._get('image_types/1', username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.image_type_get_xml)

    def testGetImageJobs(self):

        # TODO: rbac tests somewhat missing -- need to isolate some errors
        # with rmake mocking not working in my environment -- MPD

        imageId = 3

        for i in range(3):
            jobTypes = [ jobsmodels.EventType.TARGET_DEPLOY_IMAGE,
                jobsmodels.EventType.TARGET_LAUNCH_SYSTEM ]
            for j, jobType in enumerate(jobTypes):
                jobUuid = "job-uuid-%02d-%02d" % (i, j)
                job = self._newJob(jobUuid, jobType=jobType)
                models.JobImage.objects.create(job=job, image_id=imageId)

        # TODO: add tests for non-admon access w/ rights
        response = self._get('images/%s/jobs' % imageId,
            username='admin', password='password')
        self.failUnlessEqual(response.status_code, 200)
        doc = xobj.parse(response.content)
        self.failUnlessEqual([ x.job_uuid for x in doc.jobs.job ],
            [
                'job-uuid-02-01',
                'job-uuid-02-00',
                'job-uuid-01-01',
                'job-uuid-01-00',
                'job-uuid-00-01',
                'job-uuid-00-00',
            ])

    def testAddLaunchedSystemForImage(self):
        user = self.getUser('testuser')
        self.mgr.user = user

        # Needed by setTargetUserCredentials
        class Auth(object):
            def __init__(self, user):
                self.userId = user.user_id
                self.user = user

        self.mgr._auth = Auth(user)

        img = models.Image.objects.get(name='image-0')
        imgFile = img.files.all()[0]
        targetImageId = str(uuid.uuid4())

        # We need a job for authentication
        jobUuid = str(uuid.uuid4())
        jobToken = str(uuid.uuid4())
        job = self._newJob(jobUuid, jobToken=jobToken,
            jobType=jobsmodels.EventType.TARGET_LAUNCH_SYSTEM,
            createdBy=user)
        models.JobImage.objects.create(job=job, image=img)
        tgtType = self.mgr.getTargetTypeByName('vmware')

        tgt = self.mgr.createTarget(tgtType, 'tgtname',
            dict(zone='Local rBuilder'))
        self.mgr.setTargetUserCredentials(tgt, dict(username='foo', password='bar'))

        xmlTemplate = """\
<systems>
  <system>
    <target_system_id>long-id-1</target_system_id>
    <target_system_name>target-system-name-1</target_system_name>
    <target_system_description>target-system-description-1</target_system_description>
    <ssl_client_certificate>ssl-client-certificate-1</ssl_client_certificate>
    <ssl_client_key>ssl-client-key-1</ssl_client_key>
    <targetType>vmware</targetType>
    <targetName>tgtname</targetName>
    <dnsName>1.2.3.4</dnsName>
  </system>
  <system>
    <target_system_id>long-id-2</target_system_id>
    <target_system_name>target-system-name-2</target_system_name>
    <target_system_description>target-system-description-2</target_system_description>
    <ssl_client_certificate>ssl-client-certificate-2</ssl_client_certificate>
    <ssl_client_key>ssl-client-key-2</ssl_client_key>
    <targetType>vmware</targetType>
    <targetName>tgtname</targetName>
    <dnsName>1.2.3.5</dnsName>
  </system>
</systems>
"""
        xml = xmlTemplate % dict(targetId=tgt.target_id,
            targetImageId=targetImageId)
        url = 'images/%s/systems' % (img.image_id, )
        xml = xml
        response = self._post(url, data=xml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        doc = xobj.parse(response.content)
        systems = doc.systems.system
        self.failUnlessEqual(
            [ x.target_system_id for x in systems ],
            ['long-id-1', 'long-id-2'])

        systemIds = [ x.system_id for x in systems ]
        expNetworks = [ '1.2.3.4', '1.2.3.5', ]

        for systemId, expNetwork in zip(systemIds, expNetworks):
            system = invmodels.System.objects.get(system_id=systemId)
            network = system.networks.all()[0]
            self.failUnlessEqual(network.dns_name, expNetwork)

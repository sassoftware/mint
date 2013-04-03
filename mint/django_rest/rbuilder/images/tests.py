import hashlib
import os
import subprocess

from testutils import mock
import testsxml
from xobj import xobj

import logging
logging.disable(logging.CRITICAL)

from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

from conary import deps, trovetup, versions

from mint import jobstatus
from mint.lib import uuid
from mint.django_rest.rbuilder.images import models
from mint.django_rest.rbuilder.inventory import models as invmodels
from mint.django_rest.rbuilder.jobs import models as jobsmodels
from mint.django_rest.rbuilder.projects import models as projectsmodels
from mint.django_rest.rbuilder.users import models as usermodels
from mint.django_rest.rbuilder.rbac import models as rbacmodels
from mint.django_rest.rbuilder.querysets import models as querymodels
from mint.django_rest.rbuilder.rbac.tests import RbacEngine
from mint.django_rest.rbuilder.targets import models as tgtmodels
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

        jobUuids = [
                '7be3373b-38f4-4048-9e30-dce87d8529c9',
                'c4610ef0-f937-4af3-a8f8-8665451ab416',
                '540bb963-a655-4c49-bab5-a40c9d67ac28',
        ]

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
            # images
            image = models.Image(
                project=proj, _image_type=10, job_uuid=jobUuids[i],
                name="image-%s" % i, trove_name='troveName%s' % i, trove_version='/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-%d-1' % i,
                trove_flavor='1#x86:i486:i586:i686|5#use:~!xen', created_by=user1, updated_by=user2, image_count=1,
                output_trove=None, project_branch=branch, stage_name='stage%s' % i,
                description="image-%s" % i)
            image.save()
            # now buildfiles and fileurls
            buildFile = models.BuildFile(image=image, size=i, sha1='%s' % i,
                    title='foo')
            buildFile.save()

            fileUrl = models.FileUrl(url_type=0, url='http://example.com/%s/' % i)
            fileUrl.save()

            buildFilesUrlsMap = models.BuildFilesUrlsMap(file=buildFile, url=fileUrl)
            buildFilesUrlsMap.save()

            buildFile = models.BuildFile(image=image, size=i+1,
                    sha1='%s' % (i + 1), title='foo')
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
        # XXX FIXME: only metadata is editable. This test does not
        # handle metadata. Technically the status code should probably
        # be different too.
        return
        #image_updated = xobj.parse(response.content)
        #self.assertEquals(image_updated.image.trove_name, 'troveName20-Changed')

    def testUpdateImageAdmin(self):
        self._testUpdateImage('admin', 200)

    def testUpdateImageNonAdmin(self):
        self._testUpdateImage('ExampleDeveloper', 200)

    def testUpdateImageNoAuthz(self):
        self._testUpdateImage('testuser', 403)

    def testUpdateImageMetadata(self):
        img = self._setupImageOutputToken()
        models.Image.objects.filter(image_id=img.image_id).update(
                output_trove="image-foo:source=/chater-foo.eng.rpath.com@rpath:chater-foo-1/1-1[]")
        data = """\
<image>
  <metadata>
    <key1>value1</key1>
    <key2>value2</key2>
    <key3>value3</key3>
  </metadata>
</image>
"""
        # mock Conary access
        # We need the metadata dict twice, since we compute it once at
        # load time and once at save time
        kvmeta = [dict(a=1, b=2)]
        def mockGetKeyValueMetadata(slf, troveTups):
            return kvmeta

        def mockUpdateKeyValueMetadata(slf, jobs, *args, **kwargs):
            del kvmeta[:]
            kvmeta.append(jobs[0][1])
            return [ x[0] for x in jobs ]

        self.mock(self.mgr.restDb.productMgr.reposMgr.__class__,
            'getKeyValueMetadata', mockGetKeyValueMetadata)
        self.mock(self.mgr.restDb.productMgr.reposMgr.__class__,
            'updateKeyValueMetadata', mockUpdateKeyValueMetadata)

        url = "images/%s" % img.image_id
        response = self._put(url, data=data,
            username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.assertEquals(obj.image.metadata.key1, 'value1')
        self.assertEquals(obj.image.metadata.key2, 'value2')
        self.assertEquals(obj.image.metadata.key3, 'value3')

        # Make sure something got logged
        fileObj = self.mgr.restDb.fileMgr.openImageFile(
            img.project.short_name, img.image_id, "build.log", "r")
        self.assertEquals(fileObj.read(), "")

    def _testDeleteImage(self, username, expected_code):
        response = self._delete('images/1', username=username, password='password')
        self.assertEquals(response.status_code, expected_code)

    def testCannotDeleteLayeredSource(self):
        image1 = models.Image.objects.get(pk=1)
        image2 = models.Image.objects.get(pk=2)
        image2.base_image = image1
        image2.save()
        self._testDeleteImage('admin', 403)

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
  <title>dummy file</title>
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
        # Make sure we have entries in target_deployable_image
        self.failUnlessEqual(
            [ x.target_image.target_internal_id
                for x in imgFile.target_deployable_images.all() ],
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
        self.mgr.retagQuerySetsByType('image')
        response = self._get('images/%s/jobs' % imageId,
            username='admin', password='password')
        if response.status_code != 200:
            print response.content
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

        # Test sorting by job description
        response = self._get('images/%s/jobs?order_by=job_description' % imageId,
            username='admin', password='password')
        self.unmock()
        self.assertEquals(response.status_code, 400)
        doc = xobj.parse(response.content)
        self.assertEquals(doc.fault.code, '400')
        self.assertTrue(doc.fault.message.startswith(
            "Cannot resolve keyword u'job_description' into field."),
            doc.fault.message)

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
        url = 'jobs/%s/systems' % (job.job_uuid, )
        response = self._post(url, data=xml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        doc = xobj.parse(response.content)
        systems = doc.systems.system
        self.failUnlessEqual(
            [ x.target_system_id for x in systems ],
            ['long-id-1', 'long-id-2'])

        systemIds = [ x.system_id for x in systems ]
        expNetworks = [ '1.2.3.4', '1.2.3.5', ]

        trvSpec = 'troveName0=/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-0-1[~!xen is: x86(i486,i586,i686)]'

        for i, (systemId, expNetwork) in enumerate(zip(systemIds, expNetworks)):
            system = invmodels.System.objects.get(system_id=systemId)
            network = system.networks.all()[0]
            self.failUnlessEqual(network.dns_name, expNetwork)
            self.failUnlessEqual(system.source_image, img)
            self.failUnlessEqual(system.project_id, img.project_id)
            self.failUnlessEqual(system.project_branch_id, img.project_branch_id)
            self.failUnlessEqual(system.project_branch_stage_id, img.project_branch_stage_id)
            self.failUnlessEqual(
                [ x.trove_spec for x in system.desired_top_level_items.all() ],
                [ trvSpec ])
            self.failUnlessEqual(
                [ x.trove_spec for x in system.observed_top_level_items.all() ],
                [ trvSpec ])
            self.failUnlessEqual(system._ssl_client_certificate,
                'ssl-client-certificate-%s' % (i+1))
            self.failUnlessEqual(system._ssl_client_key,
                'ssl-client-key-%s' % (i+1))

        # Make sure the systems were associated with the job
        self.assertEquals(sorted(x.system.target_system_id
            for x in job.created_systems.all()),
            ['long-id-1', 'long-id-2'])

        # post again, should not fail (trying to add the same system
        # as a created artifact multiple times)
        response = self._post(url, data=xml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)

    def _setupImageOutputToken(self):
        img = models.Image.objects.get(name='image-0')
        img.project_branch_stage = projectsmodels.Stage.objects.filter(
            project__short_name='chater-foo',
            project_branch__name='1',
            name='Development')[0]
        self.mgr.createImageBuild(img)
        return img

    def _setupFileContentsList(self, img, contentMap=None):
        imgPath = os.path.join(self.mgr.cfg.imagesPath, img.project.short_name,
            str(img.image_id))
        os.makedirs(imgPath)
        if contentMap is None:
            contentMap = [
                ('filename1.ova', "Contents for ova file have 35 bytes"),
                ('filename2.tar.gz', "Contents for ovf 0.99 file have 40 bytes"),
            ]
        fileContentList = []
        for idx, (fname, content) in enumerate(contentMap):
            sha1 = hashlib.sha1(content).hexdigest()
            params = dict(
                sha1 = sha1,
                size = len(content),
                title = "File %s" % idx,
                filename = os.path.join(imgPath, fname),
            )
            fileContentList.append(params)
            with open(params['filename'], 'w') as fobj:
                fobj.write(content)
            with open(params['filename'] + '.sha1', 'w') as fobj:
                fobj.write(sha1 + '\n')
        return fileContentList

    def testPutImageBuildFiles(self):
        # Mock repository interaction
        retNvf = trovetup.TroveTuple(
            'image-blabbedy',
            versions.VersionFromString('/example.com@test:1/1-1-1'),
            deps.deps.Flavor(''))

        createSourceTroveCallArgs = []
        def mockCreateSourceTrove(slf, *args, **kwargs):
            createSourceTroveCallArgs.append((args, kwargs))
            return retNvf
        self.mock(self.mgr.reposMgr.__class__, 'createSourceTrove', mockCreateSourceTrove)

        retKVmeta = [ dict(owner='Jennay', workload='heavy') ]
        getKeyValueMetadataCallArgs = []
        def mockGetKeyValueMetadata(slf, *args, **kwargs):
            getKeyValueMetadataCallArgs.append((args, kwargs))
            return retKVmeta
        self.mock(self.mgr.restDb.productMgr.reposMgr.__class__,
                'getKeyValueMetadata', mockGetKeyValueMetadata)

        xmlFilesTmpl = """<files>%s<attributes><installed_size>56245126</installed_size></attributes></files>"""
        xmlFileTmpl = """
  <file>
    <title>%(title)s</title>
    <size>%(size)s</size>
    <sha1>%(sha1)s</sha1>
    <file_name>%(filename)s</file_name>
  </file>"""

        img = self._setupImageOutputToken()
        fileContentList = self._setupFileContentsList(img)

        xml = xmlFilesTmpl % '\n'.join(xmlFileTmpl % x for x in fileContentList)

        # Grab the image outputToken
        outputToken = img.image_data.filter(name='outputToken')[0].value

        response = self._put('images/%s/build_files' % img.image_id,
            data=xml,
            headers={'X-rBuilder-OutputToken': outputToken},
        )

        self.failUnlessEqual(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(
            [(x.title, x.sha1) for x in obj.files.file],
            [(x['title'], x['sha1']) for x in fileContentList])

        # Make sure installed_size got in the db
        self.assertEquals(
            [ (x.value, x.data_type) for x in
                img.image_data.filter(name='attributes.installed_size') ],
            [ ('56245126', 2), ])

        self.failUnlessEqual(createSourceTroveCallArgs, [])

        # same deal, now with metadata
        xmlFilesTmpl = xmlFilesTmpl.replace('</files>', """\
  <metadata>
    <owner>JeanValjean</owner>
  </metadata>
</files>""")

        xml = xmlFilesTmpl % '\n'.join(xmlFileTmpl % x for x in fileContentList)

        response = self._put('images/%s/build_files' % img.image_id,
            data=xml,
            headers={'X-rBuilder-OutputToken': outputToken},
        )

        self.failUnlessEqual(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(
            [(x.title, x.sha1) for x in obj.files.file],
            [(x['title'], x['sha1']) for x in fileContentList])

        self.failUnlessEqual(
                [ (x[0][:4], x[0][4].keys(), x[1]) for x in createSourceTroveCallArgs ],
                [
                    (
                        (u'chater-foo.eng.rpath.com', u'image-chater-foo',
                            u'chater-foo.eng.rpath.com@rpath:chater-foo-1-devel',
                            u'1'),
                        ['filename1.ova', 'filename2.tar.gz', ],
                        {'admin': True, 'changeLogMessage': 'Image imported',
                            'factoryName': 'rbuilder-image',
                            'metadata': {'owner': 'JeanValjean'}}
                    ),
                ])
        self.failUnlessEqual(
            [ ([ y.asString() for y in x[0][0] ], x[1]) for x in getKeyValueMetadataCallArgs ],
            [
                (['image-blabbedy=/example.com@test:1/1-1-1[]'], {}),
                (['image-blabbedy=/example.com@test:1/1-1-1[]'], {}),
            ])

    def testPutImageBuildLog(self):
        img = self._setupImageOutputToken()

        # Grab the image outputToken
        outputToken = img.image_data.filter(name='outputToken')[0].value

        data = "Build log data here"
        response = self._post('images/%s/build_log' % img.image_id,
            data=data,
            headers={'X-rBuilder-OutputToken': outputToken},
        )
        self.failUnlessEqual(response.status_code, 204)

        buildLog = self.mgr.getBuildLog(img.image_id)
        self.assertEqual(buildLog, data)

        data2 = "\nAnd some more data"

        response = self._post('images/%s/build_log' % img.image_id,
            data=data2,
            headers={'X-rBuilder-OutputToken': outputToken},
        )
        self.failUnlessEqual(response.status_code, 204)

        buildLog = self.mgr.getBuildLog(img.image_id)
        self.assertEqual(buildLog, data + data2)

    class MockKey(object):
        class MockPolicy(object):
            class MockACL(object):
                def add_user_grant(self, permission, user_id):
                    pass

            def __init__(self):
                self.acl = self.MockACL()

        def __init__(self, keyName):
            self.keyName = keyName

        def set_contents_from_file(self, fp, cb = None, policy = None):
            if cb:
                cb(10, 16)

        def get_acl(self):
            return self.MockPolicy()

        def set_acl(self, acl):
            pass

    class MockBucket(test_utils.CallProxy):
        def new_key(self, key_name):
            return self.MockKey(key_name)
        def get_key(self, key_name):
            return self.MockKey(key_name)
    MockBucket.MockKey = MockKey

    def testPutImageStatus(self):
        # Set up EC2
        # Needed by setTargetUserCredentials
        class Auth(object):
            def __init__(self, user):
                self.userId = user.user_id
                self.user = user

        user = self.getUser('jimphoo')
        self.mgr._auth = Auth(user)

        tgtType = self.mgr.getTargetTypeByName('ec2')
        tgt = self.mgr.createTarget(tgtType, 'aws', targetData=dict(
            ec2AccountId="8675309",
            ec2S3Bucket="bukkit",
            ec2PublicKey="rbuilder-wide public key",
            ec2PrivateKey="rbuilder-wide private key",
            ec2Certificate ="ec2 certificate",
            ec2CertificateKey="ec2 certificate key",
            zone='Local rBuilder',
        ))
        self.mgr.setTargetUserCredentials(tgt, dict(accountId="12345",
            publicAccessKeyId="public key", secretAccessKey="secret key"))

        from mint import ec2
        self.mock(ec2.S3Wrapper, 'createBucket',
            lambda *args, **kwargs: self.MockBucket())

        img = self._setupImageOutputToken()
        archiveContents = file(self.createFakeAmiBuild()).read()
        fileContentList = self._setupFileContentsList(img, contentMap=[
            ('image.tar.gz', archiveContents)
        ])

        # Grab the image outputToken
        outputToken = img.image_data.filter(name='outputToken')[0].value

        # Set up some files for the image
        xmlFilesTmpl = """<files>%s</files>"""
        xmlFileTmpl = """
  <file>
    <title>%(title)s</title>
    <size>%(size)s</size>
    <sha1>%(sha1)s</sha1>
    <file_name>%(filename)s</file_name>
  </file>"""

        xml = xmlFilesTmpl % '\n'.join(xmlFileTmpl % x for x in fileContentList)

        # Temporary fix for django being silly (1.3.1 doesn't seem to
        # have problems with unicode): encode as utf-8
        response = self._put('images/%s/build_files' % img.image_id,
            data=xml.encode('utf-8'),
            headers={'X-rBuilder-OutputToken': outputToken},
        )
        self.failUnlessEqual(response.status_code, 200)

        xmlTemplate = """\
<image>
  <status>%(status)s</status>
  <status_message>%(statusMessage)s</status_message>
</image>"""

        params = dict(status=jobstatus.WAITING, statusMessage="For Godot")
        response = self._put('images/%s' % img.image_id,
            data=xmlTemplate % params,
            headers={'X-rBuilder-OutputToken': outputToken},
        )
        self.failUnlessEqual(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.assertEqual(obj.image.status, '0')
        self.assertEqual(obj.image.status_message, 'For Godot')

        status = models.Image.objects.filter(
            image_id=img.image_id).values_list("status", "status_message")
        self.assertEqual(status[0],
            (params['status'], params['statusMessage']))

        # Update status to another non-final state
        params = dict(status=jobstatus.RUNNING, statusMessage="For president")
        response = self._put('images/%s' % img.image_id,
            data=xmlTemplate % params,
            headers={'X-rBuilder-OutputToken': outputToken},
        )
        self.failUnlessEqual(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.assertEqual(obj.image.status, '100')
        self.assertEqual(obj.image.status_message, 'For president')

        status = models.Image.objects.filter(
            image_id=img.image_id).values_list("status", "status_message")
        self.assertEqual(status[0],
            (params['status'], params['statusMessage']))

        # Update status to FINISHED
        # To test auth token removal
        authToken = models.AuthTokens.objects.create(token=str(self.uuid4()),
            user=img.created_by, image=img,
            expires_date=self.mgr.sysMgr.now())
        # To test AMI image upload
        from mint import buildtypes
        models.Image.objects.filter(image_id=img.image_id).update(
            _image_type=buildtypes.AMI)

        params = dict(status=jobstatus.FINISHED, statusMessage="really done")
        response = self._put('images/%s' % img.image_id,
            data=xmlTemplate % params,
            headers={'X-rBuilder-OutputToken': outputToken},
        )
        self.failUnlessEqual(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.assertEqual(obj.image.status, '300')
        self.assertEqual(obj.image.status_message, 'really done')

        status = models.Image.objects.filter(
            image_id=img.image_id).values_list("status", "status_message")
        self.assertEqual(status[0],
            (params['status'], params['statusMessage']))

        # Token should be gone
        self.assertEquals(
            list(models.AuthTokens.objects.filter(token=authToken.token)),
            [])

        self.assertEqual(
            sorted((x.name, x.value)
                for x in models.ImageData.objects.filter(
                    image__image_id=img.image_id)),
            [
                ('outputToken', outputToken),
            ]
        )

        # AMIs are no longer published at build time
        self.assertEqual(list(
            tgtmodels.TargetImagesDeployed.objects.filter(build_file__image__image_id=img.image_id).values_list('target__name')),
            [ ])

        # We can deploy the image again
        self.assertEqual(list(
            tgtmodels.TargetDeployableImage.objects.filter(build_file__image__image_id=img.image_id).values_list('target__name')),
            [ ('aws', ), ])

        # Did we tag this image?
        # XXX write test

    def createFakeAmiBuild(self):
        dirPath = os.path.join(self.workDir, "image.ami")
        os.makedirs(dirPath)
        file(os.path.join(dirPath, "image.img.part.1"), "w")
        file(os.path.join(dirPath, "image.img.part.2"), "w")
        file(os.path.join(dirPath, "image.img.part.3"), "w")
        file(os.path.join(dirPath, "image.img.manifest.xml"), "w")
        tarFile = os.path.join(self.workDir, "image.ami.tar.gz")
        subprocess.call(["tar", "zcf", tarFile, "-C", self.workDir, "image.ami"])
        return tarFile

    def testImageBuildCancellation(self):
        img = self._setupImageOutputToken()
        # Mark image as complete, action should be disabled
        img.status = 300
        img.save()
        response = self._get('images/%s' % img.image_id,
            username='admin', password='password')
        doc = xobj.parse(response.content)

        self.failUnlessEqual(doc.image.jobs.id,
            'http://testserver/api/v1/images/%s/jobs' % img.image_id)

        actions = doc.image.actions.action
        if not isinstance(actions, list):
            actions = [ actions ]
        # Make sure we have an image cancellation action
        self.failUnlessEqual([ x.job_type.id for x in actions ],
            [ 'http://testserver/api/v1/inventory/event_types/25' ])
        self.failUnlessEqual([ x.enabled for x in actions ],
            [ 'false', ])
        self.failUnlessEqual([ x.descriptor.id for x in actions ],
            [ 'http://testserver/api/v1/images/%s/descriptors/cancel_build' % img.image_id ])

        # Mark image as running
        img.status = 100
        img.save()

        models.ImageData.objects.create(image=img, name='uuid',
            value='0xDEADBEEF', data_type=0)

        response = self._get('images/%s' % img.image_id,
            username='admin', password='password')
        doc = xobj.parse(response.content)
        actions = doc.image.actions.action
        if not isinstance(actions, list):
            actions = [ actions ]
        self.failUnlessEqual([ x.enabled for x in actions ],
            [ 'true', ])

        # Fetch the descriptor
        response = self._get('images/%s/descriptors/cancel_build' % img.image_id,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        doc = xobj.parse(response.content)
        self.assertEquals(doc.descriptor.metadata.displayName,
            'Cancel Image Build')
        self.assertEquals(doc.descriptor.metadata.descriptions.desc,
            'Cancel Image Build')

        # Mock mcp
        from mcp import client as mcpclient
        class MockClient(test_utils.CallProxy):
            def __call__(slf, *args, **kwargs):
                # Trick to record the class constructor
                slf._fake_init(*args, **kwargs)
                return slf
        self.mock(mcpclient, "Client", MockClient())

        # Compose job
        templ = """\
<job>
  <job_type id="http://testserver/api/v1/inventory/event_types/25"/>
  <descriptor id="http://testserver/api/v1/images/%(imageId)s/descriptors/cancel_build"/>
  <descriptor_data/>
</job>
"""
        data = templ % dict(imageId = img.image_id)
        response = self._post('images/%s/jobs' % img.image_id, data=data,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        doc = xobj.parse(response.content)
        jobId = os.path.basename(doc.job.id)

        # Fetch call list
        callList = mcpclient.Client.getCallList()
        self.assertEquals([ (x.name, x.args, x.kwargs) for x in callList ],
            [
                ('_fake_init', ('127.0.0.1', 50900), {}),
                ('stop_job', (u'0xDEADBEEF',), {}),
            ])

        response = self._get('jobs/%s' % jobId, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        doc = xobj.parse(response.content)
        self.assertEquals(doc.job.status_text, "Done")

    def testImageSetProductVersion(self):
        # RCE-626
        from django.db import transaction
        from mint.db import builds

        img = self._setupImageOutputToken()
        imageId = img.image_id
        projectBranchId = img.project_branch_id
        projectBranchStageId = img.project_branch_stage_id
        self.assertTrue(projectBranchStageId is not None)
        stageName = img.stage_name
        models.Image.objects.filter(image_id=imageId).update(project_branch=None,
            project_branch_stage=None)
        transaction.commit()
        olddb = self.mgr.restDb.db
        b = builds.BuildsTable(olddb)
        b.setProductVersion(imageId, projectBranchId, stageName)

        img = models.Image.objects.get(image_id=imageId)
        self.assertEqual(img.project_branch_id, projectBranchId)
        self.assertEqual(img.project_branch_stage_id, projectBranchStageId)

from testutils import mock
import testsxml
from xobj import xobj

import logging
logging.disable(logging.CRITICAL)

from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

from mint.django_rest.rbuilder.images import models
from mint.django_rest.rbuilder.jobs import models as jobsmodels
from mint.django_rest.rbuilder.projects import models as projectsmodels
from mint.django_rest.rbuilder.users import models as usermodels

class ImagesTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)
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
        self.assertXMLEquals(response.content, testsxml.images_get_xml)

    def testGetImage(self):
        image = models.Image.objects.get(pk=1)
        response = self._get('images/%s' % image.pk, 
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.image_get_xml)
        
    def testGetImageBuildFiles(self):
        image = models.Image.objects.get(pk=1)
        response = self._get('images/%s/build_files/' % image.pk, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.build_files_get_xml)
        
    def testGetImageBuildFile(self):
        buildFile = models.BuildFile.objects.get(pk=1)
        response = self._get('images/%s/build_files/%s/' % (buildFile.image_id, buildFile.pk),
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.build_file_get_xml)
        
    def testCreateImage(self):
        response = self._post('images/',
            username='admin', password='password', data=testsxml.image_post_xml)
        self.assertEquals(response.status_code, 200)
        image = xobj.parse(response.content)
        self.assertEquals(image.image.name, 'image-20')
        self.assertEquals(image.image.trove_name, 'troveName20')
        self.assertEquals(image.image.image_id, u'4')
        
    def testUpdateImage(self):
        response = self._post('images/',
            username='admin', password='password', data=testsxml.image_post_xml)
        image = xobj.parse(response.content)
        response = self._put('images/%s' % image.image.image_id,
            username='admin', password='password', data=testsxml.image_put_xml)
        self.assertEquals(response.status_code, 200)
        image_updated = xobj.parse(response.content)
        self.assertEquals(image_updated.image.trove_name, 'troveName20-Changed')
        
    def testDeleteImage(self):
        response = self._delete('images/1', username='admin', password='password')
        self.assertEquals(response.status_code, 204)
        
    def testCreateImageBuildFile(self):
        response = self._post('images/1/build_files/',
            username='admin', password='password', data=testsxml.build_file_post_xml)
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.build_file_posted_xml)
        
    def testUpdateImageBuildFile(self):
        response = self._post('images/1/build_files/',
            username='admin', password='password', data=testsxml.build_file_post_xml)
        buildFile = xobj.parse(response.content)
        file_id = buildFile.file.file_id
        response = self._put('images/1/build_files/%s' % file_id,
            username='admin', password='password', data=testsxml.build_file_put_xml)
        buildFileUpdated = xobj.parse(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(buildFileUpdated.file.title, 'newtitle')
        
    def testDeleteImageBuildFile(self):
        response = self._delete('images/1/build_files/1', username='admin', password='password')
        self.assertEquals(response.status_code, 204)
        
    def testGetRelease(self):
        response = self._get('releases/1', username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.release_get_xml)
        
    def testGetReleases(self):
        response = self._get('releases/', username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.releases_get_xml)
        
    def testCreateRelease(self):
        response = self._post('releases/',
            username='admin', password='password', data=testsxml.release_post_xml)
        self.assertEquals(response.status_code, 200)
        release = xobj.parse(response.content).release
        self.assertEquals(release.name, u'release100')
        self.assertEquals(release.description, u'description100')
        self.assertEquals(release.project.id, u"http://testserver/api/v1/projects/foo0")
        self.assertEquals(release.published_by.id, u"http://testserver/api/v1/users/2002")
        
    def testUpdateRelease(self):
        response = self._put('releases/1',
            username='admin', password='password', data=testsxml.release_put_xml)
        self.assertEquals(response.status_code, 200)
        release = xobj.parse(response.content).release
        self.assertEquals(release.name, u'release100')
        self.assertEquals(release.description, u'description100')
        self.assertEquals(release.version, u'releaseVersion100')
        
    def testDeleteRelease(self):
        response = self._delete('releases/1', username='admin', password='password')
        self.assertEquals(response.status_code, 204)
        
    def testGetUrlFileByBuildFile(self):
        response = self._get('images/1/build_files/1/file_url', username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.build_file_url_get_xml)
        response = self._get('images/3/build_files/3/file_url', username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        fileUrl = xobj.parse(response.content).file_url
        self.assertEquals(fileUrl.url, u'http://example.com/1/')
        self.assertEquals(fileUrl.url_type, u'0')
        
    def testGetBuildLog(self):
        response = self._get('images/3/build_log', username='admin', password='password')
        self.assertEquals(response.status_code, 200)

    def testGetImageTypes(self):
        response = self._get('image_types/', username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.image_types_get_xml)
        
    def testGetImageType(self):
        response = self._get('image_types/1', username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.image_type_get_xml)

    def testGetImageJobs(self):
        imageId = 3

        for i in range(3):
            jobTypes = [ jobsmodels.EventType.TARGET_DEPLOY_IMAGE,
                jobsmodels.EventType.TARGET_LAUNCH_SYSTEM ]
            for j, jobType in enumerate(jobTypes):
                jobUuid = "job-uuid-%02d-%02d" % (i, j)
                job = self._newJob(jobUuid, jobType=jobType)
                models.JobImage.objects.create(job=job, image_id=imageId)

        response = self._get('images/%s/jobs' % imageId,
            username='testuser', password='password')
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

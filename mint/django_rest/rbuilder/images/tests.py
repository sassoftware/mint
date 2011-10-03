import testsxml
from xobj import xobj

import logging
logging.disable(logging.CRITICAL)

from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

from mint.django_rest.rbuilder.projects import models as projectsmodels
from mint.django_rest.rbuilder.images import models
from mint.django_rest.rbuilder.users import models as usermodels

class ImagesTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)
        self._init()

    def _init(self):
        
        user1 = usermodels.User(
            user_name='jimphoo', full_name='Jim Phoo', email='jimphoo@noreply.com')
        user1.save()
        user2 = usermodels.User(
            user_name='janephoo', full_name='Jane Phoo', email='janephoo@noreply.com')
        user2.save()
            
        for i in range(3):
            # make project
            proj = self._addProject("foo%s" % i)
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
            release = models.Release(project=proj,
                name='release%s' % i, version='releaseVersion%s' % i, description='description%s' % i,
                created_by=user1, updated_by=user2, published_by=user2)
            release.save()
            # images
            image = models.Image(
                project=proj, release=release, build_type=10, job_uuid='1',
                name="image-%s" % i, trove_name='troveName%s' % i, trove_version='/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-%d-1' % i,
                trove_flavor='1#x86:i486:i586:i686|5#use:~!xen', created_by=user1, updated_by=user2, build_count=1,
                output_trove=None, project_branch=branch, stage_name='stage%s' % i,
                description="image-%s" % i)
            image.save()
            # now buildfiles
            buildFile = models.BuildFile(build=image, size=i, sha1='%s' % i)
            buildFile.save()
        

    def _addProject(self, short_name, namespace='ns'):
        project = projectsmodels.Project()
        project.name = project.hostname = project.short_name = short_name
        project.namespace = namespace
        project.domain_name = 'eng.rpath.com'
        # project = self.mgr.projectManager.addProject(project)
        project.save()
        return project

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
        response = self._get('images/%s/build_files/%s/' % (buildFile.build_id, buildFile.pk),
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
        file_id = buildFile.build_file.file_id
        response = self._put('images/1/build_files/%s' % file_id,
            username='admin', password='password', data=testsxml.build_file_put_xml)
        buildFileUpdated = xobj.parse(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(buildFileUpdated.build_file.title, 'newtitle')
        
    def testDeleteImageBuildFile(self):
        response = self._delete('images/1/build_files/1', username='admin', password='password')
        self.assertEquals(response.status_code, 204)
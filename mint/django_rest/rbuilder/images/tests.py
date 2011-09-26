import testsxml
#from xobj import xobj

import logging
logging.disable(logging.CRITICAL)

from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

class ImagesTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)

    def _initImages(self):
        prj = self._addProject("foo")
        image = models.Image(name="image-1", description="image-1",
            project=prj, build_type=10)
        image.save()

    def _addProject(self, short_name, namespace='ns'):
        project = models.Project()
        project.name = project.hostname = project.short_name = short_name
        project.namespace = namespace
        project.domain_name = 'test.local2'
        project = self.mgr.projectManager.addProject(project)

        return project

    def _initProject(self, name='chater-foo'):
        proj = models.Project.objects.get(name='chater-foo')
        branch = models.ProjectVersion(project=proj, name="trunk", label="chater-foo.eng.rpath.com@rpath:chater-foo-trunk")
        branch.save()
        stage = models.Stage(project=proj,
            project_branch=branch, name="Development", label="foo@ns:trunk-devel")
        stage.save()
        stage = models.Stage(project=proj,
            project_branch=branch, name="QA", label="foo@ns:trunk-qa")
        stage.save()
        stage = models.Stage(project=proj,
            project_branch=branch, name="Stage", label="foo@ns:trunk-stage")
        stage.save()
        stage = models.Stage(project=proj,
            project_branch=branch, name="Release", label="foo@ns:trunk")
        stage.save()

    def testCanListAndAccessImages(self):

        # WARNING --
        # these are just stub tests until we can resolve what the unified
        # images table looks like.  We'll need real ones later that
        # inject items into the DB.

        # once rbac for images is implemented this should redirect to a queryset
        # for now, it's just a stub
        url = 'images/'
        response = self._get(url, username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.images_get_xml)
 
        # also a stub
        url = "images/1"
        response = self._get(url, username='admin', password='password')
        self.assertEqual(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.image_get_xml)

    def testUpdateImage(self):
        pass
        

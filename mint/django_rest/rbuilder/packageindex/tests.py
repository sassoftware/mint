from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

from mint.django_rest.rbuilder.packageindex import models
from mint.django_rest.rbuilder.projects import models as projmodels

class Test(XMLTestCase):
    def setUp(self):
        XMLTestCase.setUp(self)
        project = projmodels.Project.objects.get(name='chater-foo')
        branch = projmodels.ProjectVersion.objects.get(project=project, name='1')

        self.package = models.Package.objects.create(project=project,
                name="foo", version="/%s/1-2-3" % branch.label,
                branch_name=branch.name,
                server_name=branch.label.split('@', 1)[0],
                )

    def testModel(self):
        # RCE-1535 - empty version should not break synthetic fields
        models.Package()
        # Proceed with meaningful test
        url = "packages/%s" % self.package.package_id
        response = self._get(url, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, """\
<package id="http://testserver/api/v1/packages/1">
  <branch_name>1</branch_name>
  <is_source>0</is_source>
  <name>foo</name>
  <package_id>1</package_id>
  <project id="http://testserver/api/v1/projects/chater-foo">
    <domain_name>eng.rpath.com</domain_name>
    <name>chater-foo</name>
    <short_name>chater-foo</short_name>
  </project>
  <server_name>chater-foo.eng.rpath.com</server_name>
  <trailing_label>chater-foo.eng.rpath.com@rpath:chater-foo-1</trailing_label>
  <trailing_version>1-2-3</trailing_version>
  <version>/chater-foo.eng.rpath.com@rpath:chater-foo-1/1-2-3</version>
</package>
""")

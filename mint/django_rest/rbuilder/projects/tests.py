#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.rbuilder.projects import manager
from mint.django_rest.rbuilder.projects import models
from mint.django_rest.rbuilder.projects import testsxml
from mint.django_rest.rbuilder.repos import manager as reposmanager
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager import rbuildermanager
from xobj import xobj
from mint.django_rest.rbuilder.rbac.tests import RbacEngine
from testutils import mock
from mint.django_rest.rbuilder.images import models as imagesmodels
from mint.django_rest.rbuilder.rbac import models as rbacmodels
from mint.django_rest.rbuilder.querysets import models as querymodels
from mint.django_rest.rbuilder.users import models as usersmodels
from datetime import datetime

class ProjectsTestCase(RbacEngine):
    fixtures = ["projects", "project_image_fixtures"]

    def setUp(self):
        RbacEngine.setUp(self)
        mock.mock(reposmanager.ReposManager, "createRepositoryForProject")
        mock.mock(reposmanager.ReposManager, "createSourceTrove")
        mock.mock(reposmanager.ReposManager, "generateConaryrcFile")
        MockProdDef = mock.MockObject()
        MockProdDef.getImageGroup._mock.setReturn("group-foo-appliance")
        MockProdDef.loadFromRepository._mock.setReturn(MockProdDef)
        mock.mock(basemanager.BaseRbuilderManager, "restDb")
        basemanager.BaseRbuilderManager.restDb.getProductVersionDefinitionFromVersion._mock.setDefaultReturn(MockProdDef)
        mock.mock(manager.ProjectManager, "setProductVersionDefinition")
        self.mgr = rbuildermanager.RbuilderManager()
        self.mintConfig = self.mgr.cfg
    
        # add sysadmin user with permission to "All Projects" and "All Project Branch Stages"
        # developer user does NOT have access to these .. skipping XML versions here as these
        # are well covered in rbac/tests.py
                  
        role          = rbacmodels.RbacRole.objects.get(name='developer')
        all_projects  = querymodels.QuerySet.objects.get(name='All Projects')
        all_pbs       = querymodels.QuerySet.objects.get(name='All Project Stages')
        modmembers    = rbacmodels.RbacPermissionType.objects.get(name='ModMembers')
        admin         = usersmodels.User.objects.get(user_name='admin')

        for queryset in [ all_projects, all_pbs ]:
            for permission in [ modmembers ]:
                rbacmodels.RbacPermission(
                    queryset      = queryset,
                    role          = role,
                    permission    = permission,
                    created_by    = admin,
                    modified_by   = admin,
                    created_date  = datetime.now(),
                    modified_date = datetime.now()
                ).save()

        self._retagQuerySets()
 
        # invalidate the querysets so tags can be applied
    def _retagQuerySets(self):
        self.mgr.retagQuerySetsByType('project')
        self.mgr.retagQuerySetsByType('project_branch_stage')

 
    def _addProject(self, short_name, namespace='ns'):
        project = models.Project()
        project.name = project.hostname = project.short_name = short_name
        project.namespace = namespace
        project.domain_name = 'test.local2'
        project = self.mgr.projectManager.addProject(project)
        
        return project

    def _setupTestFoo(self):
        proj = self._addProject("foo")
        stage = models.Stage(project=proj, name="Development", label="foo@ns:trunk-devel")
        stage.save()
        stage = models.Stage(project=proj, name="QA", label="foo@ns:trunk-qa")
        stage.save()

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
        self._retagQuerySets()

    def testGetProjects(self):
        # as admin or granted user, should succeed
        for username in [ 'admin', 'ExampleDeveloper' ]:
            response = self._get('projects/',
                username="admin", password="password")
            self.assertEquals(response.status_code, 200)
            projects = xobj.parse(response.content).projects.project
            self.assertEquals(len(projects), 4)

        # as testuser, should fail
        response = self._get('projects/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)
        
        response = self._get('projects/')
        self.assertEquals(response.status_code, 401)

    def testGetProject(self):

        # admins and grants can get in
        for username in [ 'admin', 'ExampleDeveloper' ]:
            response = self._get('projects/chater-foo/',
                username=username, password='password'
            )
            # FIXME: missing XML tests!, need to add
            self.assertEquals(response.status_code, 200)
        
        # other users cannot get this item
        response = self._get('projects/chater-foo/',
            username='ExampleSysadmin', password='password')
        self.assertEquals(response.status_code, 403)
        
        # anon obviously cannot
        response = self._get('projects/chater-foo')
        self.assertEquals(response.status_code, 401)

    def testGetProjectBranchesFunctionsFromGrant(self):
        self._initProject()

        # FIXME: missing XML tip
        response = self._get('projects/chater-foo/project_branches', username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)

        response = self._get('projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk',
            username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        
        response = self._get('projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages', username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)

        response = self._get('projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Stage', username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)

    def testAddProject(self):

        # FIXME: can anyone create a project or just admin?   We need to come up with a policy for this.

        response = self._post('projects',
            data=testsxml.project_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        projectId = project.project_id
        project = models.Project.objects.get(pk=projectId)
        self.assertEquals("test-project", project.name)
        self.assertEquals(1, project.creator.user_id)
        
    def testAddProjectNoHostname(self):
        response = self._post('projects',
            data=testsxml.project_post_no_hostname_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        projectId = project.project_id
        project = models.Project.objects.get(pk=projectId)
        self.assertEquals("test-project", project.hostname)
        
    def testAddProjectNoRepoHostname(self):
        response = self._post('projects',
            data=testsxml.project_post_no_repo_hostname_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        projectId = project.project_id
        project = models.Project.objects.get(pk=projectId)
        self.assertEquals("test-project.eng.rpath.com", project.repository_hostname)
        self.assertEquals(1, project.creator.user_id)
        
    def testAddProjectNoDomainName(self):
        response = self._post('projects',
            data=testsxml.project_post_no_domain_name_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        self.failUnlessEqual(project.repository_hostname, 'test-project.rpath.local2')

        projectId = project.project_id
        project = models.Project.objects.get(pk=projectId)
        self.failUnlessEqual(project.repository_hostname, 'test-project.rpath.local2')
        self.assertEquals(project.creator.user_id, 1)
        
    def testAddProjectNoNamespace(self):
        response = self._post('projects',
            data=testsxml.project_post_no_namespace_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        projectId = project.project_id
        project = models.Project.objects.get(pk=projectId)
        self.assertEquals(project.namespace, 'ns')
        self.assertEquals(1, project.creator.user_id)
        
    def testAddProjectExternal(self):
        response = self._post('projects',
            data=testsxml.project_post_external_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        self.assertEquals("rPath Windows Build Service", project.name)
        self.assertEquals("https://rb.rpath.com/repos/rwbs/browse", project.upstream_url)
        
    def testUpdateProject(self):

        for username in [ 'admin', 'ExampleDeveloper' ]:
            response = self._put('projects/chater-foo',
                data=testsxml.project_put_xml,
                username="admin", password="password")
            self.assertEquals(response.status_code, 200)
            project = xobj.parse(response.content).project
            projectId = project.project_id
            project = models.Project.objects.get(pk=projectId)
            self.assertEquals("updated description",
                project.description)
            
        response = self._put('projects/chater-foo',
            data=testsxml.project_put_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)

            
    def testUpdateProjectAuthenticatedWithGrant(self):
        response = self._put('projects/chater-foo',
            data=testsxml.project_put_xml,
            username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)

    def testDeleteProject_admin(self):
        response = self._delete('projects/chater-foo',
            username="admin", password="password")
        self.assertEquals(response.status_code, 204)

    def testDeleteProject_grant(self):
        response = self._delete('projects/chater-foo',
            username="ExampleDeveloper", password="password")
        self.assertEquals(response.status_code, 204)

    def testDeleteProject_nogrant(self):
        response = self._delete('projects/chater-foo',
            username="testuser", password='password')
        self.assertEquals(response.status_code, 403)

    def testGetAggregateProjectBranches(self):
        for username in [ 'admin', 'ExampleDeveloper' ]:
            response = self._get('project_branches/',
                username="admin", password="password")
            self.assertEquals(response.status_code, 200)
            # FIXME: convert to XML test
            branches = xobj.parse(response.content).project_branches.project_branch
            self.failUnlessEqual([ x.label for x in branches ],
                ['chater-foo.eng.rpath.com@rpath:chater-foo-1',
                 'postgres.rpath.com@rpath:postgres-1',
                 'postgres.rpath.com@rpath:postgres-2',
                 'postgres-private.rpath.com@rpath:postgres-private-1'])

    def testAddProjectVersionToProject(self):
        self._addProject("foo")
        # response = self._post('projects/foo/project_branches/',
        #     data=testsxml.project_version_post_with_project_xml,
        #     username="ExampleDeveloper", password="password")
        response = self._post('projects/foo/project_branches/',
            data=testsxml.project_version_post_with_project_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        branch = xobj.parse(response.content).project_branch
        branch = models.ProjectVersion.objects.get(pk=branch.branch_id)
        self.assertEquals('42', branch.name)
        # FIXME: convert to XML test
        # make sure stages are there
        # XXX project creation does not handle stage creation at the
        # moment
        self.assertEquals(len(branch.project_branch_stages.all()), 3)

    def testAddProjectVersionToProjectTwo(self):
        # add project as admin    
        response = self._post('projects',
            data=testsxml.project_post_xml,
            username="ExampleDeveloper", password="password")
        self.assertEquals(response.status_code, 200)
        
        # try to add project as different user
        response = self._post('project_branches/',
            data=testsxml.project_version_post_with_project_no_auth_xml)
        self.assertEquals(response.status_code, 401)

        # FIXME: XML tests??

    def testUpdateProjectBranch(self):
        response = self._put('projects/postgres/project_branches/postgres.rpath.com@rpath:postgres-1',
            data=testsxml.project_version_put_xml,
            username="ExampleDeveloper", password="password")
        self.assertEquals(response.status_code, 200)
        branch = xobj.parse(response.content).project_branch
        branch = models.ProjectVersion.objects.get(pk=branch.branch_id)
        self.assertEquals(branch.description, "updated description")

    def testUpdateProjectBranchSecurity(self):
        # Unauthenticated
        response = self._put('projects/postgres/project_branches/postgres.rpath.com@rpath:postgres-1',
            data=testsxml.project_version_put_xml)
        self.assertEquals(response.status_code, 401)

        # Not a project owner -- rejected by conary lib hence 403 not 401
        response = self._put('projects/postgres/project_branches/postgres.rpath.com@rpath:postgres-1',
            data=testsxml.project_version_put_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)

    def testDeleteProjectBranch(self):
        response = self._delete('projects/postgres/project_branches/postgres.rpath.com@rpath:postgres-1',
            username="admin", password="password")
        self.assertEquals(response.status_code, 204)

    def testDeleteProjectBranchAnonymous(self):
        response = self._delete('projects/postgres/project_branches/postgres.rpath.com@rpath:postgres-1')
        self.assertEquals(response.status_code, 401)
        
    def testGetAggregateProjectBranchStages(self):
        self._initProject()
        response = self._get('project_branch_stages/',
            username="ExampleDeveloper", password="password", pagination=';start_index=0;limit=9999')
        self.assertEquals(response.status_code, 200)
        stages = xobj.parse(response.content).project_branch_stages.project_branch_stage
        oldMaxDiff = self.maxDiff
        self.maxDiff = None
        self.failUnlessEqual([ x.label for x in stages ],
            [
                'label',
                'postgres.rpath.com@rpath:postgres-1-qa',
                'postgres.rpath.com@rpath:postgres-1',
                'postgres.rpath.com@rpath:postgres-2-devel',
                'postgres.rpath.com@rpath:postgres-2-qa',
                'postgres.rpath.com@rpath:postgres-2',
                'postgres-private.rpath.com@rpath:postgres-1-devel',
                'postgres-private.rpath.com@rpath:postgres-1-qa',
                'postgres-private.rpath.com@rpath:postgres-1',
                'foo@ns:trunk-devel',
                'foo@ns:trunk-qa',
                'foo@ns:trunk-stage',
                'foo@ns:trunk'
            ])
        self.maxDiff = oldMaxDiff
        
        response = self._get('project_branch_stages/',
            username='ExampleDeveloper', password="password")
        self.assertEquals(response.status_code, 401)
        
    def testGetProjectAllBranchStages(self):
        self._initProject()
        response = self._get('projects/chater-foo/project_branch_stages',
            username="ExampleDeveloper", password="password")
        self.assertEquals(response.status_code, 200)
        stages = xobj.parse(response.content).project_branch_stages.project_branch_stage

        self.failUnlessEqual([ x.label for x in stages ],
            [
                'label',
                'foo@ns:trunk-devel',
                'foo@ns:trunk-qa',
                'foo@ns:trunk-stage',
                'foo@ns:trunk',
            ])

        response = self._get('projects/chater-foo/project_branch_stages',
            username='testuser', password="password")
        self.assertEquals(response.status_code, 403)

    def testGetProjectImages(self):
        # Add image
        prj = self._addProject("foo")
        image = imagesmodels.Image(name="image-1", description="image-1",
            project=prj, _image_type=10)
        image.save()
        response = self._get('projects/%s/images/' % prj.short_name,
                    username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        image = imagesmodels.Image.objects.get(pk=image.pk)
        self.assertEquals(image.image_type.image_type_id, 10)
        self.assertEquals(image.image_type.name, 'Microsoft (R) Hyper-V')
        self.assertEquals(image.image_type.description, 'VHD for Microsoft (R) Hyper-V')

        response = self._get('projects/%s/images/' % prj.short_name,
                    username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 403)

    def testAddProjectBranchStageImage(self):
        self._initProject()
        prj = models.Project.objects.get(name='chater-foo')
        branch = models.ProjectVersion.objects.get(
            project__project_id=prj.project_id, name='trunk')
        stage = models.Stage.objects.get(
            project_branch__branch_id=branch.branch_id, name='Development')
        url = "projects/%s/project_branches/%s/project_branch_stages/%s/images/"
        urlparams = (prj.short_name, branch.label, stage.name)
        response = self._post(url % urlparams, 
            username='ExampleDeveloper', password='password', data=testsxml.project_branch_stage_images_post_xml)
        self.assertEquals(response.status_code, 200)
        

    def testGetProjectBranchStagesByProject(self):
        self._initProject()
        prj = models.Project.objects.get(name='chater-foo')
        branch = models.ProjectVersion.objects.get(
            project__project_id=prj.project_id, name='trunk')
        url = ('projects/%s/project_branches/%s/project_branch_stages/' %
                (prj.short_name, branch.label))
        response = self._get(url, username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        stgs = xobj.parse(response.content)
        self.assertXMLEquals(stgs.toxml(), testsxml.project_branch_stages_xml)

    def testGetProjectBranchStage(self):
        self._initProject()
        prj = models.Project.objects.get(name='chater-foo')
        branch = models.ProjectVersion.objects.get(
            project__project_id=prj.project_id, name='trunk')
        stage = models.Stage.objects.get(
            project_branch__branch_id=branch.branch_id, name='Development')

        # First image has no stage reference
        image = imagesmodels.Image(name="image-1", description="image-1",
            project=prj, project_branch=branch, _image_type=10,
            stage_name=stage.name)
        image.save()

        # Second image has a stage reference
        image = imagesmodels.Image(name="image-2", description="image-2",
            project=prj, project_branch=branch, project_branch_stage=stage,
            _image_type=10)
        image.save()

        url = ('projects/%s/project_branches/%s/project_branch_stages/%s' %
                (prj.short_name, branch.label, stage.name))
        response = self._get(url, username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        stg = xobj.parse(response.content).project_branch_stage

        # Make sure we have a link for images
        self.failUnlessEqual(stg.images.id, 'http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Development/images')

        # Make sure we have a project_branch
        self.failUnlessEqual(stg.project_branch.id, 'http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk')
        self.failUnlessEqual(stg.project_branch.name, 'trunk')

        url += '/images'
        response = self._get(url,
            username="ExampleDeveloper", password="password")
        self.assertEquals(response.status_code, 200)
        images = xobj.parse(response.content).images
        self.failUnlessEqual(images.id, 'http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Development/images;start_index=0;limit=10')

        images = images.image
        self.failUnlessEqual([ x.name for x in images ],
            ['image-1', 'image-2', ])

        # Test project images too
        url = 'projects/%s' % (prj.short_name, )
        response = self._get(url,
            username="ExampleDeveloper", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        self.failUnlessEqual(project.images.id, 'http://testserver/api/v1/projects/chater-foo/images')
        url += '/images'
        response = self._get(url,
            username="ExampleDeveloper", password="password")
        self.assertEquals(response.status_code, 200)
        images = xobj.parse(response.content).images
        self.failUnlessEqual(images.id, 'http://testserver/api/v1/projects/chater-foo/images;start_index=0;limit=10')

        images = images.image
        self.failUnlessEqual([ x.name for x in images ],
            ['image from fixture', 'image-1', 'image-2', ])

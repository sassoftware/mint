#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.rbuilder.inventory.tests import XMLTestCase

from mint.django_rest.rbuilder.projects import manager # pyflakes=ignore
from mint.django_rest.rbuilder.projects import models # pyflakes=ignore
from mint.django_rest.rbuilder.projects import testsxml # pyflakes=ignore
from mint.django_rest.rbuilder.repos import manager as reposmanager
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager import rbuildermanager
from xobj import xobj

from testutils import mock


class ProjectsTestCase(XMLTestCase):
    fixtures = ["projects", "project_image_fixtures"]

    def setUp(self):
        XMLTestCase.setUp(self)
        mock.mock(reposmanager.ReposManager, "createRepositoryForProject")
        mock.mock(reposmanager.ReposManager, "createSourceTrove")
        mock.mock(reposmanager.ReposManager, "generateConaryrcFile")
        MockProdDef = mock.MockObject()
        MockProdDef.getImageGroup._mock.setReturn("group-foo-appliance")
        mock.mock(basemanager.BaseRbuilderManager, "restDb")
        basemanager.BaseRbuilderManager.restDb.getProductVersionDefinitionFromVersion._mock.setDefaultReturn(MockProdDef)
        mock.mock(manager.ProjectManager, "setProductVersionDefinition")
        self.mgr = rbuildermanager.RbuilderManager()
        self.mintConfig = self.mgr.cfg
        
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

    def testGetProjectsAdmin(self):
        response = self._get('projects/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        projects = xobj.parse(response.content).projects.project
        self.assertEquals(len(projects), 4)

    def testGetProjectsUser(self):
        response = self._get('projects/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        projects = xobj.parse(response.content).projects.project
        self.assertEquals(len(projects), 4)
        self.assertEquals([p.short_name for p in projects],
            [u'chater-foo', u'postgres', u'postgres-private', u'example2'])

        response = self._get('projects/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        projects = xobj.parse(response.content).projects.project
        self.assertEquals(len(projects), 3)
    
    # def testGetProjectsAnon(self):
    #     response = self._get('projects/')
    #     self.assertEquals(response.status_code, 200)
    #     projects = xobj.parse(response.content).projects.project
    #     self.failUnlessEqual([ x.name for x in projects ],
    #         ['chater-foo', 'postgres', 'name2', ])
    #     self.failUnlessEqual([ x.id for x in projects ],
    #       [
    #         'http://testserver/api/v1/projects/chater-foo',
    #         'http://testserver/api/v1/projects/postgres',
    #         'http://testserver/api/v1/projects/example2',
    #       ])

    def testGetProjectsAnon(self):
        # needs to fail for user w/o rbac/rmember perms
        response = self._get('projects/')
        self.assertEquals(response.status_code, 401)

    # def testGetProjectAnon(self):
    #     response = self._get('projects/chater-foo')
    #     self.assertEquals(response.status_code, 200)
    #     project = xobj.parse(response.content).project
    #     self.failUnlessEqual(project.short_name, 'chater-foo')
    #     self.failUnlessEqual(project.project_branches.id,
    #         'http://testserver/api/v1/projects/chater-foo/project_branches')

    def testGetProjectAnon(self):
        response = self._get('projects/chater-foo')
        self.assertEquals(response.status_code, 401)

    # def testGetProjectBranchesAnon(self):
    #     self._initProject()
    #     response = self._get('projects/chater-foo/project_branches')
    #     self.assertEquals(response.status_code, 200)
    #     branches = xobj.parse(response.content).project_branches.project_branch
    #     self.failUnlessEqual([ x.name for x in branches ],
    #         ['1', 'trunk'])
    #     self.failUnlessEqual([ x.project_branch_stages.id for x in branches ],
    #         [
    #             'http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-1/project_branch_stages',
    #             'http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages',
    #         ])

    def testGetProjectBranchesAnon(self):
        self._initProject()
        response = self._get('projects/chater-foo/project_branches')
        self.assertEquals(response.status_code, 401)

    # def testGetProjectBranchAnon(self):
    #     self._initProject()
    #     response = self._get('projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk')
    #     self.assertEquals(response.status_code, 200)
    #     branch = xobj.parse(response.content).project_branch
    #     self.failUnlessEqual(branch.name, 'trunk')
    #     self.failUnlessEqual(branch.project_branch_stages.id,
    #             'http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages')
    #     # Comparing XML is more involved maintenance-wise, avoid doing
    #     # that for collections
    #     self.assertXMLEquals(response.content, testsxml.project_branch_xml)

    def testGetProjectBranchAnon(self):
        self._initProject()
        response = self._get('projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk')
        self.assertEquals(response.status_code, 401)

    # def testGetProjectBranchStagesAnon(self):
    #     self._initProject()
    #     response = self._get('projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages')
    #     self.assertEquals(response.status_code, 200)
    #     stages = xobj.parse(response.content).project_branch_stages.project_branch_stage
    #     self.failUnlessEqual([ x.name for x in stages ], ['Development', 'QA', 'Stage', 'Release'])
    #     self.failUnlessEqual([ x.id for x in stages ],
    #       [
    #         'http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Development',
    #         'http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/QA',
    #         'http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Stage',
    #         'http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Release',
    #      ])

    def testGetProjectBranchStagesAnon(self):
        self._initProject()
        response = self._get('projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages')
        self.assertEquals(response.status_code, 401)

    # def testGetProjectBranchStageAnon(self):
    #     self._initProject()
    #     response = self._get('projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Stage')
    #     self.assertEquals(response.status_code, 200)
    #     stage = xobj.parse(response.content).project_branch_stage
    #     self.failUnlessEqual(stage.name, 'Stage')
    #     self.failUnlessEqual(stage.id, 'http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Stage')
    # 
    #     # Comparing XML is more involved maintenance-wise, avoid doing
    #     # that for collections
    #     self.assertXMLEquals(response.content, testsxml.project_branch_stage_xml)
    
    def testGetProjectBranchStageAnon(self):
        self._initProject()
        response = self._get('projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Stage')
        self.assertEquals(response.status_code, 401)

    def testAddProject(self):
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
        
    def testAddProjectExternalNoUrlNoAuth(self):
        response = self._post('projects',
            data=testsxml.project_post_external_no_url_no_auth_xml)
        self.assertEquals(response.status_code, 401)
        
    def testAddProjectExternalNoUrlExternalAuth(self):
        response = self._post('projects',
            data=testsxml.project_post_external_no_url_external_auth_xml)
        self.assertEquals(response.status_code, 401)

    def testUpdateProject(self):
        response = self._put('projects/chater-foo',
            data=testsxml.project_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        projectId = project.project_id
        project = models.Project.objects.get(pk=projectId)
        self.assertEquals("updated description",
            project.description)

    def testDeleteProject(self):
        response = self._delete('projects/chater-foo',
            username="admin", password="password")
        self.assertEquals(response.status_code, 204)

    def testGetAggregateProjectBranches(self):
        response = self._get('project_branches/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        branches = xobj.parse(response.content).project_branches.project_branch
        self.failUnlessEqual([ x.label for x in branches ],
            ['chater-foo.eng.rpath.com@rpath:chater-foo-1',
             'postgres.rpath.com@rpath:postgres-1',
             'postgres.rpath.com@rpath:postgres-2'])

    def testAddProjectVersionToProject(self):
        self._addProject("foo")
        response = self._post('projects/foo/project_branches/',
            data=testsxml.project_version_post_with_project_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        branch = xobj.parse(response.content).project_branch
        branch = models.ProjectVersion.objects.get(pk=branch.branch_id)
        self.assertEquals('42', branch.name)

        # make sure stages are there
        # XXX project creation does not handle stage creation at the
        # moment
        self.assertEquals(len(branch.project_branch_stages.all()), 3)

    def testAddProjectVersionToProjectNoAuth(self):
        # add project as admin    
        response = self._post('projects',
            data=testsxml.project_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        
        # try to add project as different user
        response = self._post('project_branches/',
            data=testsxml.project_version_post_with_project_no_auth_xml)
        self.assertEquals(response.status_code, 401)

    def testUpdateProjectBranch(self):
        response = self._put('projects/postgres/project_branches/postgres.rpath.com@rpath:postgres-1',
            data=testsxml.project_version_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        branch = xobj.parse(response.content).project_branch
        branch = models.ProjectVersion.objects.get(pk=branch.branch_id)
        self.assertEquals(branch.description, "updated description")

    def testUpdateProjectBranchNoAuth(self):
        # Unauthenticated
        response = self._put('projects/postgres/project_branches/postgres.rpath.com@rpath:postgres-1',
            data=testsxml.project_version_put_xml)
        self.assertEquals(response.status_code, 401)

        # Not a project owner
        response = self._put('projects/postgres/project_branches/postgres.rpath.com@rpath:postgres-1',
            data=testsxml.project_version_put_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 403)

    def testDeleteProjectBranch(self):
        response = self._delete('projects/postgres/project_branches/postgres.rpath.com@rpath:postgres-1',
            username="admin", password="password")
        self.assertEquals(response.status_code, 204)

    def testDeleteProjectBranchNoAuth(self):
        response = self._delete('projects/postgres/project_branches/postgres.rpath.com@rpath:postgres-1')
        self.assertEquals(response.status_code, 401)
        
    def testGetAggregateProjectBranchStages(self):
        self._initProject()
        response = self._get('project_branch_stages/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        stages = xobj.parse(response.content).project_branch_stages.project_branch_stage
        self.failUnlessEqual([ x.label for x in stages ],
            [
                'label',
                'foo@ns:trunk-devel',
                'foo@ns:trunk-qa',
                'foo@ns:trunk-stage',
                'foo@ns:trunk',
                'postgres.rpath.com@rpath:postgres-1-qa',
                'postgres.rpath.com@rpath:postgres-1',
                'postgres.rpath.com@rpath:postgres-2-devel',
                'postgres.rpath.com@rpath:postgres-2-qa',
                'postgres.rpath.com@rpath:postgres-2',
            ])

    def testGetProjectAllBranchStages(self):
        self._initProject()
        response = self._get('projects/chater-foo/project_branch_stages',
            username="testuser", password="password")
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


    def testGetProjectImages(self):
        # Add image
        prj = self._addProject("foo")
        image = models.Image(name="image-1", description="image-1",
            project=prj, build_type=10)
        image.save()

        response = self._get('projects/%s/images/' % prj.short_name,
                    username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        image = models.Image.objects.get(pk=image.pk)
        self.assertEquals(image.build_type, 10)

    def testGetProjectBranchStage(self):
        self._initProject()
        prj = models.Project.objects.get(name='chater-foo')
        branch = models.ProjectVersion.objects.get(
            project__project_id=prj.project_id, name='trunk')
        stage = models.Stage.objects.get(
            project_branch__branch_id=branch.branch_id, name='Development')

        # First image has no stage reference
        image = models.Image(name="image-1", description="image-1",
            project=prj, project_branch=branch, build_type=10,
            stage_name=stage.name)
        image.save()

        # Second image has a stage reference
        image = models.Image(name="image-2", description="image-2",
            project=prj, project_branch=branch, project_branch_stage=stage, build_type=10)
        image.save()

        url = ('projects/%s/project_branches/%s/project_branch_stages/%s' %
                (prj.short_name, branch.label, stage.name))
        response = self._get(url, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        stg = xobj.parse(response.content).project_branch_stage

        # Make sure we have a link for images
        self.failUnlessEqual(stg.images.id, 'http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Development/images')

        # Make sure we have a project_branch
        self.failUnlessEqual(stg.project_branch.id, 'http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk')
        self.failUnlessEqual(stg.project_branch.name, 'trunk')

        url += '/images'
        response = self._get(url,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        images = xobj.parse(response.content).images
        self.failUnlessEqual(images.id, 'http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Development/images;start_index=0;limit=10')

        images = images.image
        self.failUnlessEqual([ x.name for x in images ],
            ['image-1', 'image-2', ])

        # Test project images too
        url = 'projects/%s' % (prj.short_name, )
        response = self._get(url,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        self.failUnlessEqual(project.images.id, 'http://testserver/api/v1/projects/chater-foo/images')
        url += '/images'
        response = self._get(url,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        images = xobj.parse(response.content).images
        self.failUnlessEqual(images.id, 'http://testserver/api/v1/projects/chater-foo/images;start_index=0;limit=10')

        images = images.image
        self.failUnlessEqual([ x.name for x in images ],
            ['image from fixture', 'image-1', 'image-2', ])

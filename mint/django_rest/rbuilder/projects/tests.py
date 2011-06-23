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
    fixtures = ["projects"]

    def setUp(self):
        XMLTestCase.setUp(self)
        mock.mock(reposmanager.ReposManager, "createRepositoryForProject")
        mock.mock(reposmanager.ReposManager, "createSourceTrove")
        mock.mock(reposmanager.ReposManager, "generateConaryrcFile")
        mock.mock(basemanager.BaseRbuilderManager, "restDb")
        mock.mock(manager.ProjectManager, "setProductVersionDefinition")
        self.mgr = rbuildermanager.RbuilderManager()
        
    def _addProject(self, short_name):
        project = models.Project()
        project.name = project.hostname = project.short_name = short_name
        project = self.mgr.projectManager.addProject(project)
        
        return project

    def testGetProjectsAdmin(self):
        response = self._get('projects/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        projects = xobj.parse(response.content).projects.project
        self.assertEquals(len(projects), 3)

    def testGetProjectsUser(self):
        response = self._get('projects/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        projects = xobj.parse(response.content).projects.project
        self.assertEquals(len(projects), 2)
        self.assertEquals([p.short_name for p in projects],
            ['chater-foo', 'postgres'])

        response = self._get('projects/',
            username="testuser2", password="password")
        self.assertEquals(response.status_code, 200)
        projects = xobj.parse(response.content).projects.project
        self.assertEquals(len(projects), 3)
    
    def testGetProjectsAnon(self):
        response = self._get('projects/')
        self.assertEquals(response.status_code, 200)
        projects = xobj.parse(response.content).projects.project
        self.assertEquals(len(projects), 2)

    def testAddProject(self):
        response = self._post('projects',
            data=testsxml.project_post_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        projectId = project.project_id
        project = models.Project.objects.get(pk=projectId)
        self.assertEquals("test-project", project.name)
        self.assertEquals(2000, project.creator.user_id)

    def testUpdateProject(self):
        response = self._put('projects/chater-foo',
            data=testsxml.project_put_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        projectId = project.project_id
        project = models.Project.objects.get(pk=projectId)
        self.assertEquals("updated description",
            project.description)

    def testDeleteProject(self):
        response = self._delete('projects/chater-foo',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 204)
        
    def testGetProjectVersion(self):
        response = self._get('project_branches/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        branches = xobj.parse(response.content).project_branches.project_branch
        self.assertEquals(len(branches), 4)

    def testAddProjectVersionNoProject(self):
        response = self._post('project_branches/',
            data=testsxml.project_version_post_no_project_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        branch = xobj.parse(response.content).project_branch
        branch = models.ProjectVersion.objects.get(pk=branch.branch_id)
        self.assertEquals('42', branch.name)
        
        # validate project that was created
        self.assertEquals('foo appliance', branch.project.name)
        self.assertEquals('foo', branch.project.short_name)
        self.assertEquals(0, branch.project.external)
        self.assertEquals('Appliance', branch.project.project_type)
        
        # make sure stages are there
        self.assertEquals(3, len(branch.project_branch_stages.all()))
        
    def testAddProjectVersionToProject(self):
        self._addProject("foo")
        response = self._post('project_branches/',
            data=testsxml.project_version_post_with_project_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        branch = xobj.parse(response.content).project_branch
        branch = models.ProjectVersion.objects.get(pk=branch.branch_id)
        self.assertEquals('42', branch.name)
        
        # make sure stages are there
        self.assertEquals(3, len(branch.project_branch_stages.all()))
        
    def testAddProjectVersionToProjectNoAuth(self):
        # add project as admin
        response = self._post('projects',
            data=testsxml.project_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        
        # try to add project as different user
        response = self._post('project_branches/',
            data=testsxml.project_version_post_with_project_no_auth_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)

    def testUpdateProjectVersion(self):
        response = self._put('project_branches/2',
            data=testsxml.project_version_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        branch = xobj.parse(response.content).project_branch
        branch = models.ProjectVersion.objects.get(pk=branch.branch_id)
        self.assertEquals("updated description",
            branch.description)
        
    def testUpdateProjectVersionNoAuth(self):
        response = self._put('project_branches/2',
            data=testsxml.project_version_put_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)

    def testDeleteProjectVersion(self):
        response = self._delete('project_branches/2',
            username="admin", password="password")
        self.assertEquals(response.status_code, 204)
        
    def testDeleteProjectVersionNoAuth(self):
        response = self._delete('project_branches/2',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 401)
        
    def testGetProjectBranchStages(self):
        response = self._get('project_branch_stages/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        stages = xobj.parse(response.content).project_branch_stages.project_branch_stage
        self.assertEquals(len(stages), 9)
        
    def testGetProjectBranchStagesByVersion(self):
        # add a branch to work with
        response = self._post('project_branches/',
            data=testsxml.project_version_post_no_project_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        branch = xobj.parse(response.content).project_branch
        branch = models.ProjectVersion.objects.get(pk=branch.branch_id)
        
        # get branch stages
        response = self._get('project_branches/%s/project_branch_stages' % branch.branch_id,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        stages = xobj.parse(response.content).project_branch_stages.project_branch_stage
        self.assertEquals(len(stages), 3)



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

    def testGetProjectsAdmin(self):
        response = self._get('/api/projects/',
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        projects = xobj.parse(response.content).projects.project
        self.assertEquals(len(projects), 3)

    def testGetProjectsUser(self):
        response = self._get('/api/projects/',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        projects = xobj.parse(response.content).projects.project
        self.assertEquals(len(projects), 2)
        self.assertEquals([p.short_name for p in projects],
            ['chater-foo', 'postgres'])

        response = self._get('/api/projects/',
            username="testuser2", password="password")
        self.assertEquals(response.status_code, 200)
        projects = xobj.parse(response.content).projects.project
        self.assertEquals(len(projects), 3)
    
    def testGetProjectsAnon(self):
        response = self._get('/api/projects/')
        self.assertEquals(response.status_code, 200)
        projects = xobj.parse(response.content).projects.project
        self.assertEquals(len(projects), 2)

    def testAddProject(self):
        response = self._post('/api/projects',
            data=testsxml.project_post_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        projectId = project.project_id
        project = models.Project.objects.get(pk=projectId)
        self.assertEquals("test-project", project.name)
        self.assertEquals(2000, project.creator.user_id)

    def testUpdateProject(self):
        response = self._put('/api/projects/chater-foo',
            data=testsxml.project_put_xml,
            username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        projectId = project.project_id
        project = models.Project.objects.get(pk=projectId)
        self.assertEquals("updated description",
            project.description)

    def testDeleteProject(self):
        response = self._delete('/api/projects/chater-foo',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 204)

    def testAddProjectVersion(self):
        response = self._post('/api/projects/postgres/versions',
            data=testsxml.project_version_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        version = xobj.parse(response.content).project_version
        version = models.ProjectVersion.objects.get(pk=version.version_id)
        self.assertEquals('42', version.name)

    def testUpdateProjectVersion(self):
        response = self._put('/api/projects/postgres/versions/2',
            data=testsxml.project_version_put_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        version = xobj.parse(response.content).project_version
        version = models.ProjectVersion.objects.get(pk=version.version_id)
        self.assertEquals("updated description",
            version.description)

    def testDeleteProjectVersion(self):
        response = self._delete('/api/projects/postgres/versions/2',
            username="testuser", password="password")
        self.assertEquals(response.status_code, 204)



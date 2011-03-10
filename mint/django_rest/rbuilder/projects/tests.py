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

from xobj import xobj

class ProjectsTestCase(XMLTestCase):
    fixtures = ["projects"]

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



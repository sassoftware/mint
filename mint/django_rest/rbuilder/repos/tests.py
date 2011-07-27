#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

import os

from mint.django_rest.rbuilder.inventory.tests import XMLTestCase

from mint.django_rest.rbuilder.repos import manager # pyflakes=ignore
from mint.django_rest.rbuilder.repos import models # pyflakes=ignore
#from mint.django_rest.rbuilder.repos import testsxml # pyflakes=ignore
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.projects import models as projmodels

#from xobj import xobj

#from testutils import mock

class LabelTestCase(XMLTestCase):
    fixtures = ["repos"]
	
	
    def setUpProjects(self):
        dataDir = os.path.join(self.workDir, "rbtop")
        self.mgr.reposMgr.cfg.dataPath = os.path.join(dataDir, "data")
        self.mgr.reposMgr.cfg.conaryRcFile = os.path.join(dataDir, "conaryrc")
        self.mgr.reposMgr.cfg.reposContentsDir = os.path.join(dataDir, "repos/%s/contents")
        self.mgr.reposMgr.cfg.logPath = os.path.join(dataDir, "logs")
        self.mgr.reposMgr.cfg.authUser = "mintuser"
        self.mgr.reposMgr.cfg.authPass = "abc123"
        os.makedirs(self.mgr.reposMgr.cfg.logPath)

    def testIterRepositories(self):
		# Iterate over the repositories in the fixture
        repos = self.mgr.reposMgr.iterRepositories(hidden=False, disabled=False)
        self.failUnlessEqual([x.shortName for x in repos], ['chater-foo'])
        
    def testGetRepositoryForProject(self):
        self.setUpProjects()
        project = projmodels.Project(short_name="test1", external=False,
			repository_hostname="test1.local", database="sqlite test1_local")
        project.save()
        self.mgr.reposMgr.createRepositoryForProject(project)
        repHandle = self.mgr.reposMgr.getRepositoryForProject(project)
        self.failUnlessEqual(repHandle.shortName, 'test1')

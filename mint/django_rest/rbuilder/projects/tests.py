#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest import timeutils
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
from mint.django_rest.rbuilder.platforms import models as platformsmodels

class ProjectsTestCase(RbacEngine):
    fixtures = ["projects", "project_image_fixtures"]

    def setUp(self):
        RbacEngine.setUp(self)
        mock.mock(reposmanager.ReposManager, "createRepositoryForProject")
        mock.mock(reposmanager.ReposManager, "createSourceTrove")
        MockProdDef = mock.MockObject()
        MockProdDef.getImageGroup._mock.setReturn("group-foo-appliance")
        MockProdDef.loadFromRepository._mock.setReturn(MockProdDef)
        # Discard mock at the end of the test
        self.mock(basemanager.BaseRbuilderManager, "restDb", mock.MockObject())
        basemanager.BaseRbuilderManager.restDb.getProductVersionDefinitionFromVersion._mock.setDefaultReturn(MockProdDef)
        mock.mock(manager.ProjectManager, "setProductVersionDefinition")
        self.mgr = rbuildermanager.RbuilderManager()
        self.mintConfig = self.mgr.cfg

        # add sysadmin user with permission to "All Projects" and "All Project Branch Stages"
        # developer user does NOT have access to these .. skipping XML versions here as these
        # are well covered in rbac/tests.py

        role              = rbacmodels.RbacRole.objects.get(name='developer')
        self.all_projects = querymodels.QuerySet.objects.get(name='All Projects')
        self.all_pbs      = querymodels.QuerySet.objects.get(name='All Project Stages')
        modmembers        = rbacmodels.RbacPermissionType.objects.get(name='ModMembers')
        createresource    = rbacmodels.RbacPermissionType.objects.get(name='CreateResource')
        admin             = usersmodels.User.objects.get(user_name='admin')

        for queryset in [ self.all_projects, self.all_pbs ]:
            for permission in [ modmembers, createresource  ]:
                rbacmodels.RbacPermission(
                    queryset      = queryset,
                    role          = role,
                    permission    = permission,
                    created_by    = admin,
                    modified_by   = admin,
                    created_date  = timeutils.now(),
                    modified_date = timeutils.now()
                ).save()

        self._retagQuerySets()

        # invalidate the querysets so tags can be applied
    def _retagQuerySets(self):
        self.mgr.retagQuerySetsByType('project')
        self.mgr.retagQuerySetsByType('project_branch_stage')

    def _testRbacHttpMethodPerms(self, url, methodType='GET', data=None):
        """
        Check the following:
        Unauthenticated user
        Authenticated user w/o permissions
        Authenticated user with permissions
        Admin user

        TODO: Come back and update code to handle POST's and PUT's.  Since we want to do
        more XML testing, we need an intuitive way to handle returning the response's content
        """
        usernames = {
            'NonAuthUser'      : 401,
            'testuser'         : 403,
            'ExampleDeveloper' : 200,
            'admin'            : 200
        }
        passwd = 'password'
        methodType = methodType.lower()

        if methodType == 'get':
            method = lambda username: self._get(url, username=username, password=passwd)
        else:
            raise Exception('Invalid HTTP Method')

        statusCodeResults = {}
        for uname, status in usernames.items():
            response = method(uname)
            statusCodeResults[uname] = (status, response.status_code)

        return statusCodeResults

    def _initProject(self, name='chater-foo', adorn=False):
        proj = models.Project.objects.get(name=name)
        platform = platformsmodels.Platform(
            label='label-foo', platform_name='foo-platform-name')
        platform.save()
        branch = models.ProjectVersion(project=proj, name="trunk", label="chater-foo.eng.rpath.com@rpath:chater-foo-trunk")
        branch.save()
        stageMap = [
            ("Development", "foo@ns:trunk-devel"),
            ("QA", "foo@ns:trunk-qa"),
            ("Stage", "foo@ns:trunk-stage"),
            ("Release", "foo@ns:trunk"),
        ]
        for stageName, stageLabel in stageMap:
            stage = models.Stage(project=proj, project_branch=branch,
                name=stageName, label=stageLabel)
            stage.save()
        if adorn:
            for i in range(1, 3):
                image = imagesmodels.Image(
                    project=proj, _image_type=10, job_uuid='1',
                    name="image-%s" % i, trove_name='troveName%s' % i, trove_version='/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-%d-1' % i,
                    trove_flavor='1#x86:i486:i586:i686|5#use:~!xen', image_count=1,
                    output_trove=None, project_branch=branch, stage_name='stage%s' % i,
                    description="image-%s" % i)
                image.save()
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
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.empty_projects)

        response = self._get('projects/')
        self.assertEquals(response.status_code, 401)

    def testGetProject(self):
        E = models.modellib.Etree
        # admins and grants can get in
        for username in [ 'admin', 'ExampleDeveloper' ]:
            response = self._get('projects/chater-foo/',
                username=username, password='password'
            )
            # FIXME: missing XML tests!, need to add
            self.assertEquals(response.status_code, 200)
            project = E.fromstring(response.content)
            self.assertEquals(project.xpath('project_branch_stages/@id'),
                    ['http://testserver/api/v1/projects/chater-foo/project_branch_stages'])
        # other users cannot get this item
        response = self._get('projects/chater-foo/',
            username='ExampleSysadmin', password='password')
        self.assertEquals(response.status_code, 403)

        # anon obviously cannot
        response = self._get('projects/chater-foo')
        self.assertEquals(response.status_code, 401)

    def testGetProjectBranch(self):
        response = self._get('projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-1',
                username='ExampleDeveloper', password='password',
        )
        self.assertEquals(response.status_code, 200)
        project = models.modellib.Etree.fromstring(response.content)
        self.assertEquals(project.xpath('project_branch_stages/@id'),
                ['http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-1/project_branch_stages'])

    def testGetProjectBranchesFunctionsFromGrant(self):
        self._initProject()

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

        response = self._post('projects',
            data=testsxml.project_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        projectId = project.project_id
        project = models.Project.objects.get(pk=projectId)
        self.assertEquals("test-project", project.name)
        self.assertEquals(1, project.created_by.user_id)
        self.assertEquals(1, project.modified_by.user_id)
        self.assertTrue(project.created_date is not None)
        self.assertTrue(project.modified_date is not None)

        # adding project again should give a 400 error
        response = self._post('projects',
            data=testsxml.project_post_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 409)



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
        self.assertEquals(1, project.created_by.user_id)

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
        self.assertEquals(project.created_by.user_id, 1)

    def testAddProjectNoNamespace(self):
        response = self._post('projects',
            data=testsxml.project_post_no_namespace_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        projectId = project.project_id
        project = models.Project.objects.get(pk=projectId)
        self.assertEquals(project.namespace, 'ns')
        self.assertEquals(1, project.created_by.user_id)

    def testAddProjectExternal(self):
        response = self._post('projects',
            data=testsxml.project_post_external_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        project = xobj.parse(response.content).project
        self.assertEquals(project.name, "rPath Windows Build Service")
        self.assertEquals(project.upstream_url, "https://rb.rpath.com/repos/rwbs/browse")
        self.assertEquals(project.role, "Owner")
        self.assertEquals(project.project_branch_stages.id,
                "http://testserver/api/v1/projects/rwbs/project_branch_stages")

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
        response = self._get('project_branches/',
            username='admin', password="password")
        if response.status_code != 200:
            print response.content

        self.assertEquals(response.status_code, 200)
        # FIXME: convert to XML test
        branches = xobj.parse(response.content).project_branches.project_branch
        self.failUnlessEqual([ x.label for x in branches ],
            ['chater-foo.eng.rpath.com@rpath:chater-foo-1',
             'postgres.rpath.com@rpath:postgres-1',
             'postgres.rpath.com@rpath:postgres-2',
             'postgres-private.rpath.com@rpath:postgres-private-1'])

    def testAddProjectVersionToProject(self):
        self.addProject("foo")
        platform = platformsmodels.Platform(
            label='label-foo', platform_name='foo-platform-name')
        platform.save()
        response = self._post('projects/foo/project_branches/',
            data=testsxml.project_version_post_with_project_xml,
            username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        branch = xobj.parse(response.content).project_branch
        branch = models.ProjectVersion.objects.get(pk=branch.branch_id)
        self.assertEquals('42', branch.name)
        self.assertTrue(branch.created_by is not None)
        self.assertTrue(branch.modified_by is not None)
        self.assertTrue(branch.created_date is not None)
        self.assertTrue(branch.modified_date is not None)

        # FIXME: convert to XML test
        # make sure stages are there
        # XXX project creation does not handle stage creation at the
        # moment
        self.assertEquals(len(branch.project_branch_stages.all()), 3)

        # make sure creating the branch caused stages to auto vivify
        # and they have creator/modified info
        stages = models.Stage.objects.filter(project__name='foo')
        self.assertEquals(len(stages), 3, 'stages auto created')
        for stage in stages:
            self.assertTrue(stage.created_by is not None)
            self.assertTrue(stage.modified_by is not None)
            self.assertTrue(stage.created_date is not None)
            self.assertTrue(stage.modified_date is not None)


    def testAddProjectVersionToProjectTwo(self):
        # add project as developer
        response = self._post('projects',
            data=testsxml.project_post_xml,
            username="ExampleDeveloper", password="password")
        self.assertEquals(response.status_code, 200)
        platform = platformsmodels.Platform(
            label='label-foo', platform_name='foo-platform-name')
        platform.save()

        # try POSTing with pb pointing to project with valid perms
        response = self._post('projects/test-project/project_branches',
            data=testsxml.project_version_post_with_project_xml2,
            username="ExampleDeveloper", password="password")
        self.assertEquals(response.status_code, 200)
        branch = xobj.parse(response.content).project_branch
        self.assertEquals(branch.name, u'50')
        self.assertEquals(branch.project.id, u"http://testserver/api/v1/projects/test-project")

        # try to add project as different user
        response = self._post('project_branches/',
            data=testsxml.project_version_post_with_project_no_auth_xml)
        self.assertEquals(response.status_code, 401)

        # FIXME: XML tests??

    def testUpdateProjectBranch(self):
        # can update the branch if we can update the P, but need P tags first.
        # tests above didn't add these objects using the API so invalidations didn't happen
        response = self._get("query_sets/%s/all" % self.all_projects.pk,
            username="ExampleDeveloper", password="password")
        self.assertEquals(response.status_code, 200)

        response = self._put('projects/postgres/project_branches/postgres.rpath.com@rpath:postgres-1',
            data=testsxml.project_version_put_xml,
            username="ExampleDeveloper", password="password")
        if response.status_code != 200:
            print response.content
        self.assertEquals(response.status_code, 200)
        branch = xobj.parse(response.content).project_branch
        branch = models.ProjectVersion.objects.get(pk=branch.branch_id)
        self.assertEquals(branch.description, "updated description")

        # FIXME BOOKMARK -- verify that modified_date has changed

    def testUpdateProjectBranchSecurity(self):
        # Unauthenticated
        response = self._put('projects/postgres/project_branches/postgres.rpath.com@rpath:postgres-1',
            data=testsxml.project_version_put_xml)
        self.assertEquals(response.status_code, 401)

        # Not a project owner -- rejected by conary lib hence 403 not 401
        response = self._put('projects/postgres/project_branches/postgres.rpath.com@rpath:postgres-1',
            data=testsxml.project_version_put_xml,
            username="testuser", password="password")
        if response.status_code != 403:
            print response.content
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
            username="admin", password="password", pagination=';start_index=0;limit=9999')
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

        # developer can still fetch all stages collection since it's a queryset,
        # though it should return only what he can see.  FIXME: determine
        # if what we get is actually correct before adding XML test.
        response = self._get('project_branch_stages/',
            username='ExampleDeveloper', password="password")
        self.assertEquals(response.status_code, 200)
        # self.assertXMLEquals(response.content, testsxml.developer_stages)


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
        prj = self.addProject("foo")
        image = imagesmodels.Image(name="image-1", description="image-1",
            project=prj, _image_type=10)
        image.save()
        response = self._get('projects/%s/images/' % prj.short_name,
                    username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        image = imagesmodels.Image.objects.get(pk=image.pk)
        self.assertEquals(image.image_type.image_type_id, 10)
        self.assertEquals(image.image_type.name, 'Microsoft (R) Hyper-V')
        self.assertEquals(image.image_type.description, 'VHD for Microsoft(R) Hyper-V(R)')

        response = self._get('projects/%s/images/' % prj.short_name,
                    username='testuser', password='password')
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

        # get the XML back, also see if the image list is sortable
        url = "projects/%s/project_branches/%s/project_branch_stages/%s/images/;limit=100;order_by=name;start_index=0"
        response = self._get(url % urlparams, username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.test_get_images_from_pbs_xml)

    def testGetProjectBranchStageImages(self):
        # SUP-4166
        self._initProject()
        prj = models.Project.objects.get(name='chater-foo')
        branch1 = models.ProjectVersion.objects.get(
            project__project_id=prj.project_id, name='trunk')
        stageDev1 = models.Stage.objects.get(
            project_branch__branch_id=branch1.branch_id, name='Development')

        branch2 = models.ProjectVersion.objects.get(
            project__project_id=prj.project_id, name='1')
        stageDev2 = models.Stage(project=prj, project_branch=branch2, name='Development')
        stageDev2.save()

        stages = [ stageDev1, stageDev2 ]

        # Add both branch images and stage images
        for stage in stages:
            branch = stage.project_branch
            imagesmodels.Image.objects.filter(project_branch=branch)
            for i in range(2):
                name = "image-%s-%s" % (branch.name, i)
                image = imagesmodels.Image(name=name,
                    description=name,
                    project_branch=branch,
                    project=prj,
                    # this is a for a stage name that is not set
                    # which was a legacy thing.
                    _image_type=10,
                    trove_version='/foo@rpath:1/12345:%d-1' % i,
                    trove_flavor='1#x86:i486:i586:i686|5#use:~!xen',
                    image_count=1)
                self.mgr.createImageBuild(image)

                name += 'devel'
                image = imagesmodels.Image(
                    name=name,
                    description=name,
                    project=prj,
                    # since this isn't what the real app stores (unfortunately)...
                    project_branch_stage=stage,
                    # the tests must also set this...
                    stage_name=stage.name,
                    _image_type=10,
                    trove_version='/foo@rpath:1/12345:%d-1' % i,
                    trove_flavor='1#x86:i486:i586:i686|5#use:~!xen',
                    image_count=1)
                self.mgr.createImageBuild(image)

        # Make sure there's no cross-polination
        imgs = self.mgr.getProjectBranchStageImages(prj.short_name,
            branch2.label, stageDev2.name)

        actual  = [ x.name for x in imgs.image ]
        desired = [
           u'image from fixture',
           u'image-trunk-0',
           u'image-trunk-1',
           u'image-1-0',
           u'image-1-0devel',
           u'image-1-1',
           u'image-1-1devel'
        ]
        self.failUnlessEqual(actual, desired)

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
            ['image from fixture', 'image-1', 'image-2' ])

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
            [u'image from fixture', u'image-1', u'image-2'])


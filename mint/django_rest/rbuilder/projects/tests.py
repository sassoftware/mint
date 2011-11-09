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
        mock.mock(reposmanager.ReposManager, "generateConaryrcFile")
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
        usernames = {'NonAuthUser':401, 'testuser':403, 'ExampleDeveloper':200, 'admin':200}
        passwd = 'password'
        methodType = methodType.lower()
        
        if methodType == 'get':
            method = lambda username: self._get(url, username=username, password=passwd)
        # elif methodType == 'post':
        #     method = lambda username: self._post(url, username=username, password=passwd, data=data)
        # elif methodType == 'put':
        #     method = lambda username: self._put(url, username=username, password=passwd, data=data)
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
        if adorn:
            for i in range(1, 3):
                release = models.Release(project=proj,
                    name='release%s' % i, version='releaseVersion%s' % i, description='description%s' % i)
                release.save()
                image = imagesmodels.Image(
                    project=proj, release=release, _image_type=10, job_uuid='1',
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
        self.assertEquals(1, project.created_by.user_id)
        
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
        response = self._get('project_branches/',
            username='admin', password="password")
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
        # FIXME: convert to XML test
        # make sure stages are there
        # XXX project creation does not handle stage creation at the
        # moment
        self.assertEquals(len(branch.project_branch_stages.all()), 3)

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
        self.assertEquals(image.image_type.description, 'VHD for Microsoft (R) Hyper-V')

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
            [u'image from fixture', u'image-1', u'image-2'])

    def testGetReleasesByProject(self):
        self._initProject(adorn=True)
        response = self._get('projects/chater-foo/releases', username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.releases_by_project_get_xml)
        
    def testAddRelease(self):
        self.addProject('foo', user='ExampleDeveloper')
        response = self._post('projects/foo/releases',
            username='ExampleDeveloper', password='password', data=testsxml.release_by_project_post_xml)
        self.assertEquals(response.status_code, 200)
        release = xobj.parse(response.content).release
        self.assertEquals(release.description, 'description2002')
        self.assertEquals(release.project.id, 'http://testserver/api/v1/projects/foo')
        self.assertEquals(release.id, "http://testserver/api/v1/releases/1")
    
    def testAddReleaseByInferringProject(self):
        self.addProject('foo', user='admin')
        response = self._post('projects/foo/releases',
            username='admin', password='password', data=testsxml.release_by_project_no_project_post_xml)
        self.assertEquals(response.status_code, 200)
        release = xobj.parse(response.content).release
        self.assertEquals(release.name, 'release2002')
        self.assertEquals(release.project.id, 'http://testserver/api/v1/projects/foo')
        self.assertEquals(release.should_mirror, u'0')
        self.assertEquals(release.version, 'releaseVersion2002')
    
    def testGetImagesByRelease(self):
        self._initProject(adorn=True)
        url = 'projects/chater-foo/releases/1/images/'
        status_codes = self._testRbacHttpMethodPerms(url)
        for expectedCode, responseCode in status_codes.values():
            self.assertEquals(expectedCode, responseCode)          
        response = self._get(url, username='ExampleDeveloper', password='password')
        self.assertXMLEquals(response.content, testsxml.image_by_release_get_xml)
        
    def testAddImageByRelease(self):
        self._initProject(adorn=True)
        url = 'projects/chater-foo/releases/1/images/'
        # try unauthenticated
        response = self._post(url,data=testsxml.image_by_release_post_xml)
        self.assertEquals(response.status_code, 401)
        # try authenticated w/o perms
        response = self._post(url,
            username='testuser', password='password', data=testsxml.image_by_release_post_xml)
        self.assertEquals(response.status_code, 403)
        # try authenticated user with write perms
        response = self._post(url,
            username='ExampleDeveloper', password='password', data=testsxml.image_by_release_post_xml)
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.image_by_release_post_result_xml)

#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import testsxml
from xobj import xobj
from mint.django_rest import timeutils
from mint.django_rest.rbuilder.rbac import models
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.querysets import models as querymodels
from mint.django_rest.rbuilder.rbac.manager.rbacmanager import \
   READMEMBERS, MODMEMBERS, READSET, MODSETDEF, CREATERESOURCE

# Suppress all non critical msg's from output
# still emits traceback for failed tests
import logging
logging.disable(logging.CRITICAL)

from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

class RbacTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)
        # some common test bootstrapping
        self._createQuerysets()

    def _createQuerysets(self):
        '''
        create some simple querysets to be used by all tests in common.
        more robust queryset testing exists in the queryset test cases
        '''

        self.req('query_sets/', method='POST', expect=200, is_admin=True,
            data=testsxml.tradingfloor_xml)
        self.req('query_sets/', method='POST', expect=200, is_admin=True,
            data=testsxml.lab_xml)
        self.req('query_sets/', method='POST', expect=200, is_admin=True,
            data=testsxml.datacenter_xml)

        self.tradingfloor_queryset = querymodels.QuerySet.objects.get(
            name='tradingfloor')
        self.datacenter_queryset   = querymodels.QuerySet.objects.get(
            name='datacenter')
        self.lab_queryset          = querymodels.QuerySet.objects.get(
            name='lab')
        self.sys_queryset          = querymodels.QuerySet.objects.get(
            name='All Systems'
        )
        self.user_queryset         = querymodels.QuerySet.objects.get(
            name='All Users'
        )
        self.projects_queryset     = querymodels.QuerySet.objects.get(
            name='All Projects')
        self.images_queryset     = querymodels.QuerySet.objects.get(
            name='All Images')
        self.targets_queryset     = querymodels.QuerySet.objects.get(
            name='All Targets')

        self.test_querysets = [
            self.tradingfloor_queryset,
            self.datacenter_queryset,
            self.lab_queryset,
        ]

        # now create some dummy systems and add them to the chosen queryset for each
        # so that when we check against the resources we can find some things
        # that have context
        self.datacenter_system = self.newSystem(name="dc1")
        self.lab_system        = self.newSystem(name="lab1")
        self.tradingfloor_system = self.newSystem(name="tf1")
        # this one will not be matched by a queryset
        self.lost_system         = self.newSystem(name="iAmLost")
        self.datacenter_system.save()
        self.lab_system.save()
        self.tradingfloor_system.save()
        self.lost_system.save()
        self.test_systems = [
            self.tradingfloor_system,
            self.datacenter_system,
            self.lab_system,
        ]

        self.req('query_sets/%s/chosen/' % self.datacenter_queryset.pk,
             method='POST', expect=200, is_admin=True,
            data=self.datacenter_system.to_xml())
        self.req('query_sets/%s/chosen/' % self.lab_queryset.pk,
            method='POST', expect=200, is_admin=True,
            data=self.lab_system.to_xml())
        self.req('query_sets/%s/chosen/' % self.tradingfloor_queryset.pk,
            method='POST', expect=200, is_admin=True,
            data=self.tradingfloor_system.to_xml())

        # now in order to make sure the system tags are there for the test,
        # do a query against them -- we'll mix query types
        self.req('query_sets/%s/chosen/' % self.datacenter_queryset.pk,
             method='GET', expect=200, is_admin=True)
        self.req('query_sets/%s/all/' % self.lab_queryset.pk,
             method='GET', expect=200, is_admin=True)
        self.req('query_sets/%s/chosen/' % self.tradingfloor_queryset.pk,
             method='GET', expect=200, is_admin=True)
        self.req('query_sets/%s/all' % self.projects_queryset.pk,
             method='GET', expect=200, is_admin=True)
        self.req('query_sets/%s/all' % self.images_queryset.pk,
             method='GET', expect=200, is_admin=True)
        self.req('query_sets/%s/all' % self.targets_queryset.pk,
             method='GET', expect=200, is_admin=True)

    def _xobj_list_hack(self, item):
        '''
        xobj hack: obj doesn't listify 1 element lists
        don't break tests if there is only 1 action
        '''
        if type(item) != type(item):
            return [item]
        else:
            return item

    def req(self, url, method='GET', expect=200, is_authenticated=False, is_admin=False, **kwargs):
        '''Test a HTTP operation and it's return value, return the contents'''
        method_map = {
           'GET'    : self._get,
           'POST'   : self._post,
           'DELETE' : self._delete,
           'PUT'    : self._put
        }

        if is_admin:
             response = method_map[method](url, username="admin", password="password", **kwargs)
        elif is_authenticated:
             response = method_map[method](url, username="testuser", password="password", **kwargs)
        else:
            response = method_map[method](url, **kwargs)
        self.failUnlessEqual(response.status_code, expect, "Expected status code of %s for %s:\n%s" % (expect, url, response.content))
        return response.content

class RbacBasicTestCase(RbacTestCase):

    def testModelsForRbacRoles(self):
        '''verify django models for roles work'''

        sysadmin = models.RbacRole(
            name='sysadmin',
            created_by=usersmodels.User.objects.get(user_name='admin'),
            modified_by=usersmodels.User.objects.get(user_name='admin'),
            created_date=timeutils.now(),
            modified_date=timeutils.now(),
        )
        sysadmin.save()
        developer = models.RbacRole(
            name='developer',
            created_by=usersmodels.User.objects.get(user_name='admin'),
            modified_by=usersmodels.User.objects.get(user_name='admin'),
            created_date=timeutils.now(),
            modified_date=timeutils.now()
        )
        developer.save()

        self.assertEquals(len(models.RbacRole.objects.all()), 3,
            'correct number of results'
        )

        developer2 = models.RbacRole.objects.get(name='developer')
        self.assertEquals(developer2.pk, 3)

    def testModelsForRbacPermissions(self):

        size = len(list(querymodels.QuerySet.objects.all()))

        # TODO: load from queryset fixture?
        queryset1 = querymodels.QuerySet()
        queryset1.save()

        role1    = models.RbacRole(
            name='sysadmin',
            created_by=usersmodels.User.objects.get(user_name='admin'),
            modified_by=usersmodels.User.objects.get(user_name='admin'),
            created_date=timeutils.now(),
            modified_date=timeutils.now()
        )
        role1.save()
        role1    = models.RbacRole.objects.get(name='sysadmin')
        action_name = MODSETDEF
        permission = models.RbacPermission(
           queryset        = queryset1,
           role            = role1,
           permission      = models.RbacPermissionType.objects.get(name=action_name),
           created_by=usersmodels.User.objects.get(user_name='admin'),
           modified_by=usersmodels.User.objects.get(user_name='admin'),
           created_date=timeutils.now(),
           modified_date=timeutils.now()
        )
        permission.save()
        permissions2 = models.RbacPermission.objects.filter(
           queryset = queryset1,
        )
        self.assertEquals(len(permissions2), 1, 'correct length')
        found = permissions2[0]
        self.assertEquals(found.permission.name, action_name, 'saved ok')
        self.assertEquals(found.queryset.pk, size+1, 'saved ok')
        self.assertEquals(found.role.name, 'sysadmin', 'saved ok')

    def testModelsForUserRoleAssignment(self):
        # note -- we may also keep roles in AD, this is for the case
        # where we sync them or manage them internally.  This will
        # probably need to be configurable
        user1 = usersmodels.User(
            user_name = "test",
            full_name = "test"
        )
        user1.save()
        role1 = models.RbacRole(
             name='sysadmin',
             created_by=usersmodels.User.objects.get(user_name='admin'),
             modified_by=usersmodels.User.objects.get(user_name='admin')
        )
        role1.save()
        role1 = models.RbacRole.objects.get(name='sysadmin')
        mapping = models.RbacUserRole(
            user = user1,
            role = role1,
            created_by=usersmodels.User.objects.get(user_name='admin'),
            modified_by=usersmodels.User.objects.get(user_name='admin'),
            created_date=timeutils.now(),
            modified_date=timeutils.now()
        )
        mapping.save()
        mappings2  = models.RbacUserRole.objects.filter(
            user = user1,
        )
        self.assertEquals(len(mappings2), 1, 'correct length')
        found = mappings2[0]
        self.assertEquals(found.user.user_name, 'test', 'saved ok')
        self.assertEquals(found.role.name, 'sysadmin', 'saved ok')

class RbacRoleViews(RbacTestCase):

    def setUp(self):
        RbacTestCase.setUp(self)
        self.seed_data = [ 'sysadmin', 'developer', 'intern' ]
        created_by=usersmodels.User.objects.get(user_name='admin'),
        for item in self.seed_data:
            models.RbacRole(
                name=item,
                created_by=usersmodels.User.objects.get(user_name='admin'),
                modified_by=usersmodels.User.objects.get(user_name='admin'),
            ).save()

    def testCanListRoles(self):

        url = 'rbac/roles'
        content = self.req(url, method='GET', expect=403, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)

        obj = xobj.parse(content)
        found_items = self._xobj_list_hack(obj.roles.role)
        found_items = [ item.name for item in found_items ]
        for expected in self.seed_data:
            self.assertTrue(expected in found_items, 'found item')

        # now try the queryset version for listing roles
        queryset = querymodels.QuerySet.objects.get(name='All Roles')
        url = "query_sets/%s/all" % queryset.pk
        content = self.req(url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.role_queryset_xml)

    def testCanGetSingleRole(self):

        url = 'rbac/roles/3'
        content = self.req(url, method='GET', expect=403, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        obj = xobj.parse(content)
        self.assertEqual(obj.role.name, 'developer')
        self.assertXMLEquals(content, testsxml.role_get_xml)

    def testCanAddRoles(self):
        # verify the All Roles queryset doesn't have a tagged date
        # just to make sure the future check will be proving something
        qs = querymodels.QuerySet.objects.get(name='All Roles')
        # hmm, update -- we're already accessing all roles?
        # self.assertEqual(qs.tagged_date, None)
        # now run the queryset to give it a tagged date
        self.req("query_sets/%s/all" % qs.pk, method='GET', is_admin=True)
        qs = querymodels.QuerySet.objects.get(name='All Roles')
        self.assertTrue(qs.tagged_date is not None)
        # add the role and verify we returned a filled in role
        url = 'rbac/roles'
        input = testsxml.role_post_xml_input
        output = testsxml.role_post_xml_output
        content = self.req(url, method='POST', data=input, expect=403, is_authenticated=True)
        content = self.req(url, method='POST', data=input, expect=200, is_admin=True)
        self.assertXMLEquals(content, output)
        # verify that the act of adding a role auto-invalidated the queryset tag
        # so the next UI request will get teh full list of roles without having
        # to manually invalidate the queryset with a queryset invalidation job
        qs = querymodels.QuerySet.objects.get(name='All Roles')
        self.assertTrue(qs.tagged_date is None)

    def testCanDeleteRoles(self):

        url = 'rbac/roles/4'
        self.req(url, method='DELETE', expect=403, is_authenticated=True)
        self.req(url, method='DELETE', expect=204, is_admin=True)
        self.failUnlessRaises(models.RbacRole.DoesNotExist,
            lambda: models.RbacRole.objects.get(name='intern'))

    def testCanUpdateRoles(self):

        url = 'rbac/roles/2' # was 1, 2 == sysadmin?
        input = testsxml.role_put_xml_input   # reusing put data is fine here
        output = testsxml.role_put_xml_output
        content = self.req(url, method='PUT', data=input, expect=403, is_authenticated=True)
        content = self.req(url, method='PUT', data=input, expect=200, is_admin=True)
        found_items = models.RbacRole.objects.get(name='rocketsurgeon')
        all_roles = models.RbacRole.objects.all()
        role_names = [ x.name for x in all_roles ]
        self.assertTrue('developer' not in role_names)
        self.assertTrue('rocketsurgeon' in role_names)
        self.assertXMLEquals(content, output)

class RbacPermissionViews(RbacTestCase):

    def setUp(self):
        RbacTestCase.setUp(self)

        self.seed_data = [ 'sysadmin', 'developer', 'intern' ]
        for item in self.seed_data:
            models.RbacRole(name=item,
                created_by  = usersmodels.User.objects.get(user_name='admin'),
                modified_by = usersmodels.User.objects.get(user_name='admin'),
                created_date  = timeutils.now(),
                modified_date = timeutils.now()
            ).save()

        for permission in [ MODMEMBERS, CREATERESOURCE ] :
            models.RbacPermission(
                queryset      = self.datacenter_queryset,
                role          = models.RbacRole.objects.get(name='sysadmin'),
                permission    = models.RbacPermissionType.objects.get(name=permission),
                created_by    = usersmodels.User.objects.get(user_name='admin'),
                modified_by   = usersmodels.User.objects.get(user_name='admin'),
                created_date  = timeutils.now(),
                modified_date = timeutils.now()
            ).save()
        models.RbacPermission(
            queryset       = self.datacenter_queryset,
            role           = models.RbacRole.objects.get(name='developer'),
            permission     = models.RbacPermissionType.objects.get(name=READMEMBERS),
            created_by     = usersmodels.User.objects.get(user_name='admin'),
            modified_by    = usersmodels.User.objects.get(user_name='admin'),
            created_date  = timeutils.now(),
            modified_date = timeutils.now()
        ).save()

        for permission in [ MODMEMBERS, CREATERESOURCE ] :
            models.RbacPermission(
                queryset       = self.lab_queryset,
                role           = models.RbacRole.objects.get(name='developer'),
                permission     = models.RbacPermissionType.objects.get(name=permission),
                created_by     = usersmodels.User.objects.get(user_name='admin'),
                modified_by    = usersmodels.User.objects.get(user_name='admin'),
                created_date  = timeutils.now(),
                modified_date = timeutils.now()
            ).save()

    def testCanListPermissions(self):
        url = 'rbac/grants'
        content = self.req(url, method='GET', expect=403, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)

        obj = xobj.parse(content)
        found_items = self._xobj_list_hack(obj.grants.grant)
        self.assertEqual(len(found_items), 10, 'right number of items')
        # no need to test full list dump, have test of single
        # self.assertXMLEquals(content, testsxml.permission_list_xml)

        # verify that grants also show up on roles objects
        # via associations
        url = 'rbac/roles'
        content = self.req(url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.role_list_xml_with_grants)

        # verify that we can also retrieve permissions (grants) via
        # queryset and the result is the same as from the collection
        queryset = querymodels.QuerySet.objects.get(name='All Grants')
        url = "query_sets/%s/all" % queryset.pk
        content = self.req(url, method='GET', expect=200, is_admin=True)
        # listing test no longer needed
        # self.assertXMLEquals(content, testsxml.permission_queryset_xml)

        # verify we can list permissions off the role itself
        sysadmin = models.RbacRole.objects.get(name='sysadmin')
        url = "rbac/roles/%s/grants/" % sysadmin.pk
        content = self.req(url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.permission_list_xml_for_role)

    def testCanGetSinglePermission(self):
        url = 'rbac/grants/1'
        content = self.req(url, method='GET', expect=403, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.permission_get_xml)

    def testCanAddPermissions(self):
        url = 'rbac/grants'
        input = testsxml.permission_post_xml_input
        output = testsxml.permission_post_xml_output
        content = self.req(url, method='POST', data=input, expect=403, is_authenticated=True)
        content = self.req(url, method='POST', data=input, expect=200, is_admin=True)
        self.assertXMLEquals(content, output)

    def testCanDeletePermissions(self):

        all = models.RbacPermission.objects.all()
        url = 'rbac/grants/1'
        self.req(url, method='DELETE', expect=403, is_authenticated=True)
        self.req(url, method='DELETE', expect=204, is_admin=True)
        all = models.RbacPermission.objects.all()
        self.assertEqual(len(all), 28, 'deleted an object')

    def testCanUpdatePermissions(self):

        url = 'rbac/grants/1'
        input = testsxml.permission_put_xml_input
        output = testsxml.permission_put_xml_output
        content = self.req(url, method='PUT', data=input, expect=403, is_authenticated=True)
        content = self.req(url, method='PUT', data=input, expect=200, is_admin=True)
        self.assertXMLEquals(content, output)
        perm = models.RbacPermission.objects.get(pk=1)
        self.assertEqual(perm.role.name, 'developer')
        #self.assertEqual(perm.queryset.pk, self.datacenter_queryset.pk)
        self.assertEqual(perm.permission.name, MODMEMBERS)

class RbacUserRoleViewTests(RbacTestCase):

    def setUp(self):

        RbacTestCase.setUp(self)
        #self.seed_data = [ 'datacenter', 'lab', 'tradingfloor' ]
        #for item in self.seed_data:
        #    models.RbacContext(item).save()

        self.seed_data = [ 'sysadmin', 'developer', 'intern' ]
        for item in self.seed_data:
            models.RbacRole(
                name=item,
                created_by=usersmodels.User.objects.get(user_name='admin'),
                modified_by=usersmodels.User.objects.get(user_name='admin')
            ).save()

        self.sysadmin   = models.RbacRole.objects.get(name='sysadmin')
        self.developer  = models.RbacRole.objects.get(name='developer')
        self.intern     = models.RbacRole.objects.get(name='intern')
        # this is a little off as admins are NOT subject to rbac, but
        # we're not testing the auth chain here, just the models and services
        # so it doesn't really matter what users we use in the tests.
        self.admin_user = usersmodels.User.objects.get(user_name='admin')
        self.test_user  = usersmodels.User.objects.get(user_name='testuser')

        # admin user has two roles
        models.RbacUserRole(
            role=self.sysadmin, user=self.admin_user,
            created_by=self.admin_user,
            modified_by=self.admin_user
        ).save()
        models.RbacUserRole(
            role=self.developer, user=self.admin_user,
            created_by=self.admin_user,
            modified_by=self.admin_user
        ).save()
        # test user is an intern, just one role
        models.RbacUserRole(
            role=self.intern, user=self.test_user,
            created_by=self.admin_user,
            modified_by=self.admin_user
        ).save()


    def testCanListUserRoles(self):
        user_id = self.admin_user.pk
        url = "users/%s/roles/" % user_id
        content = self.req(url, method='GET', expect=403, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        obj = xobj.parse(content)
        found_items = self._xobj_list_hack(obj.roles.role)
        self.assertEqual(len(found_items), 3, 'right number of items')
        self.assertXMLEquals(content, testsxml.user_role_list_xml)

    def testCanGetSingleUserRole(self):
        # this is admittedly a rather useless function, which only
        # confirms/denies where a user is in a role.  More likely
        # we'd ask if they had permission to do something, and more
        # as an internals thing than a REST function.  Still, here,
        # for completeness.

        user_id = self.admin_user.pk
        url = "users/%s/roles/1" % user_id # developer role
        content = self.req(url, method='GET', expect=403, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.user_role_get_xml)
        # now verify if the role isn't assigned to the user, we can't fetch it
        url = "users/%s/roles/intern" % user_id
        content = self.req(url, method='GET', expect=404, is_admin=True)

    def testCanAddUserRoles(self):
        user_id = self.admin_user.pk
        url = "users/%s/roles/" % user_id
        # gives the admin user the intern role
        input = testsxml.user_role_post_xml_input
        output = testsxml.user_role_post_xml_output
        content = self.req(url, method='POST', data=input, expect=403, is_authenticated=True)
        content = self.req(url, method='POST', data=input, expect=200, is_admin=True)
        self.assertXMLEquals(content, output)
        #user_role = models.RbacUserRole.objects.get(user = self.admin_user, role=self.intern)
        #self.assertEqual(user_role.user.pk, self.admin_user.pk)
        #self.assertEqual(user_role.role.name, 'intern')

        # list users in role to make sure that relationship collection works
        url = 'rbac/roles/3/users/'
        content = self.req(url, method='GET', expect=403, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.users_in_role_xml)

    # temporarily disabled until test can be adapted to new IDs
    #
    #def testCanDeleteUserRoles(self):
    #    user_id = self.admin_user.pk
    #    url = "users/%s/roles/1" % user_id # developer role
    #    get_url = "users/%s/roles/" % user_id
    #    # make admin no longer a developer
    #    self.req(url, method='DELETE', expect=403, is_authenticated=True)
    #    self.req(url, method='DELETE', expect=204, is_admin=True)
    #    all = models.RbacUserRole.objects.all()
    #    self.assertEquals(len(all), 4, 'right number of objects')
    #    content = self.req(url, method='GET', expect=404, is_admin=True)
    #    content = self.req(get_url, method='GET', expect=200, is_admin=True)
    #    self.assertXMLEquals(content, testsxml.user_role_get_list_xml_after_delete)

def setup_core(self):
    '''suitable function for using in any RBAC based tests for general RBAC setup'''

    RbacTestCase.setUp(self)

    role_seed_data = [ 'sysadmin', 'developer', 'intern' ]
    for item in role_seed_data:
        models.RbacRole(
            name=item,
            created_by=usersmodels.User.objects.get(user_name='admin'),
            modified_by=usersmodels.User.objects.get(user_name='admin')
        ).save()

    def mk_permission(queryset, role, action):
        models.RbacPermission(
            queryset      = queryset,
            role          = models.RbacRole.objects.get(name=role),
            permission    = models.RbacPermissionType.objects.get(name=action),
            created_by    = usersmodels.User.objects.get(user_name='admin'),
            modified_by   = usersmodels.User.objects.get(user_name='admin'),
            created_date  = timeutils.now(),
            modified_date = timeutils.now()
        ).save()

    def mk_user(name, is_admin, role):

        xml = testsxml.user_post_xml % (
            name, name, is_admin
        )
        # admins must register admins
        response = self._post('users/',
            data=xml,
            username='admin', password='password'
        )
        assert response.status_code == 200
        user = xobj.parse(response.content)

        dbuser = usersmodels.User.objects.get(pk = int(user.user.user_id))

        # add rbac role mapping
        models.RbacUserRole(
           user = dbuser,
           role = models.RbacRole.objects.get(name=role),
           created_by=usersmodels.User.objects.get(user_name='admin'),
           modified_by=usersmodels.User.objects.get(user_name='admin')
        ).save()
        return dbuser

    self.developer_role = models.RbacRole.objects.get(name='developer')

    mk_permission(self.datacenter_queryset, 'sysadmin',  MODMEMBERS)
    mk_permission(self.datacenter_queryset, 'sysadmin',  CREATERESOURCE)
    mk_permission(self.datacenter_queryset, 'developer', READMEMBERS)
    mk_permission(self.sys_queryset, 'sysadmin', READSET)
    mk_permission(self.user_queryset, 'sysadmin', READMEMBERS)

    self.admin_user     = usersmodels.User.objects.get(user_name='admin')
    self.admin_user.is_admin = True # already set?
    self.sysadmin_user  = mk_user('ExampleSysadmin', False, 'sysadmin')
    self.developer_user = mk_user('ExampleDeveloper', False, 'developer')
    self.intern_user    = mk_user('ExampleIntern', False, 'intern')

class RbacEngine(RbacTestCase):

    def setUp(self):
        setup_core(self)

class RbacEngineTests(RbacEngine):
    '''Do we know when to grant or deny access?'''

    def testUserRolesAppearInUserXml(self):

        # run all users queryset to make sure tags show up in user XML
        response = self._get("query_sets/%s/all" % self.user_queryset.pk,
            username = "admin",
            password = "password"
        )
        self.assertEquals(response.status_code, 200)

        # make sure rbac role assignments show up on the user object
        # and we have enough to discern permissions
        response = self._get("users/%s" % self.intern_user.pk,
            username = self.intern_user.user_name,
            password = 'password'
        )
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.user_get_xml_with_roles)

    def testAdminUserHasFullAccess(self):
        # admin user can do everything regardless of context
        # or permission
        for action in [ READMEMBERS, MODMEMBERS, READSET, MODSETDEF ]:
            for system in self.test_systems:
                self.assertTrue(self.mgr.userHasRbacPermission(
                    self.admin_user, system, action
                ))
        # CreateResource uses a different check
        self.assertTrue(self.mgr.userHasRbacCreatePermission(
            self.admin_user, 'project'
        ))


    def testGrantMatrixForNewRole(self):
        # RCE-1444
        models.RbacRole.objects.create(
            name='guru',
            created_by=usersmodels.User.objects.get(user_name='admin'),
            modified_by=usersmodels.User.objects.get(user_name='admin'),
            created_date=timeutils.now(),
            modified_date=timeutils.now()
        )
        response = self._get("query_sets/%s/grant_matrix" %
                self.targets_queryset.pk,
            username='admin',
            password='password'
        )
        self.assertEquals(response.status_code, 200)
        # XXX misa: I am not sure if this output is right, but there was
        # no test and the code is really horrible
        self.assertXMLEquals(response.content, """\
<roles count="4" end_index="3" filter_by="" full_collection="" id="http://testserver/api/v1/rbac/roles" limit="999999" next_page="0" num_pages="1" order_by="" per_page="4" previous_page="0" start_index="0">
  <role>
    <createresource_permission>
      <description>Create Resource</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/5</matrix_permission_id>
      <name>CreateResource</name>
      <permission_id>5</permission_id>
    </createresource_permission>
    <description/>
    <matrix_role_id>http://testserver/api/v1/rbac/roles/2</matrix_role_id>
    <modmembers_permission>
      <description>Modify Member Resources</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/2</matrix_permission_id>
      <name>ModMembers</name>
      <permission_id>2</permission_id>
    </modmembers_permission>
    <modsetdef_permission>
      <description>Modify Set Definition</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/4</matrix_permission_id>
      <name>ModSetDef</name>
      <permission_id>4</permission_id>
    </modsetdef_permission>
    <name>sysadmin</name>
    <readmembers_permission>
      <description>Read Member Resources</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/1</matrix_permission_id>
      <name>ReadMembers</name>
      <permission_id>1</permission_id>
    </readmembers_permission>
    <readset_permission>
      <description>Read Set</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/3</matrix_permission_id>
      <name>ReadSet</name>
      <permission_id>3</permission_id>
    </readset_permission>
    <role_id>2</role_id>
  </role>
  <role>
    <createresource_permission>
      <description>Create Resource</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/5</matrix_permission_id>
      <name>CreateResource</name>
      <permission_id>5</permission_id>
    </createresource_permission>
    <description/>
    <matrix_role_id>http://testserver/api/v1/rbac/roles/3</matrix_role_id>
    <modmembers_permission>
      <description>Modify Member Resources</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/2</matrix_permission_id>
      <name>ModMembers</name>
      <permission_id>2</permission_id>
    </modmembers_permission>
    <modsetdef_permission>
      <description>Modify Set Definition</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/4</matrix_permission_id>
      <name>ModSetDef</name>
      <permission_id>4</permission_id>
    </modsetdef_permission>
    <name>developer</name>
    <readmembers_permission>
      <description>Read Member Resources</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/1</matrix_permission_id>
      <name>ReadMembers</name>
      <permission_id>1</permission_id>
    </readmembers_permission>
    <readset_permission>
      <description>Read Set</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/3</matrix_permission_id>
      <name>ReadSet</name>
      <permission_id>3</permission_id>
    </readset_permission>
    <role_id>3</role_id>
  </role>
  <role>
    <createresource_permission>
      <description>Create Resource</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/5</matrix_permission_id>
      <name>CreateResource</name>
      <permission_id>5</permission_id>
    </createresource_permission>
    <description/>
    <matrix_role_id>http://testserver/api/v1/rbac/roles/4</matrix_role_id>
    <modmembers_permission>
      <description>Modify Member Resources</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/2</matrix_permission_id>
      <name>ModMembers</name>
      <permission_id>2</permission_id>
    </modmembers_permission>
    <modsetdef_permission>
      <description>Modify Set Definition</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/4</matrix_permission_id>
      <name>ModSetDef</name>
      <permission_id>4</permission_id>
    </modsetdef_permission>
    <name>intern</name>
    <readmembers_permission>
      <description>Read Member Resources</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/1</matrix_permission_id>
      <name>ReadMembers</name>
      <permission_id>1</permission_id>
    </readmembers_permission>
    <readset_permission>
      <description>Read Set</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/3</matrix_permission_id>
      <name>ReadSet</name>
      <permission_id>3</permission_id>
    </readset_permission>
    <role_id>4</role_id>
  </role>
  <role>
    <createresource_permission>
      <description>Create Resource</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/5</matrix_permission_id>
      <name>CreateResource</name>
      <permission_id>5</permission_id>
    </createresource_permission>
    <description/>
    <matrix_role_id>http://testserver/api/v1/rbac/roles/8</matrix_role_id>
    <modmembers_permission>
      <description>Modify Member Resources</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/2</matrix_permission_id>
      <name>ModMembers</name>
      <permission_id>2</permission_id>
    </modmembers_permission>
    <modsetdef_permission>
      <description>Modify Set Definition</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/4</matrix_permission_id>
      <name>ModSetDef</name>
      <permission_id>4</permission_id>
    </modsetdef_permission>
    <name>guru</name>
    <readmembers_permission>
      <description>Read Member Resources</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/1</matrix_permission_id>
      <name>ReadMembers</name>
      <permission_id>1</permission_id>
    </readmembers_permission>
    <readset_permission>
      <description>Read Set</description>
      <matrix_permission_id>http://testserver/api/v1/rbac/permissions/3</matrix_permission_id>
      <name>ReadSet</name>
      <permission_id>3</permission_id>
    </readset_permission>
    <role_id>8</role_id>
  </role>
</roles>
""")

    def testRbacDecoratorThroughView(self):
        # this tests the decorator in rbac_auth.py
        # disabling until error codes are appropriate

        urls = [
            "inventory/systems/%s" % self.datacenter_system.pk,
        ]

        for url in urls:
            # sysadmin can get in
            response = self._get(url,
                username=self.sysadmin_user.user_name,
                password='password',
            )
            self.assertEquals(response.status_code, 200, "authorized get on %s" % url)
            self.assertTrue(response.content.find("<system") != -1)

            # intern can't get in
            response = self._get(url,
                username=self.intern_user.user_name,
                password='password',
            )

            self.assertEquals(response.status_code, 403, "unauthorized get on %s" % url)
            self.assertTrue(response.content.find("<system") == -1)

            # admin can get in
            response = self._get(url,
                username=self.developer_user.user_name,
                password='password',
            )
            self.assertEquals(response.status_code, 200, "admin get on %s" % url)
            self.assertTrue(response.content.find("<system") != -1)

        # delete uses a custom callback for the decorator, so this
        # covers the other half of the decorator code

        url = "inventory/systems/%s" % self.datacenter_system.pk
        response = self._delete(url,
            username=self.intern_user.user_name,
            password='password',
        )
        self.assertEquals(response.status_code, 403, 'unauthorized delete')

        # delete as sysadmin works
        response = self._delete(url,
               username=self.sysadmin_user.user_name,
               password='password',
        )
        self.assertEquals(response.status_code, 204, 'authorized delete')

        actual_qs = list(querymodels.QuerySet.objects.all())

        # admin can see all query sets
        url = "query_sets/;start_index=0;limit=9999"
        response = self._get(url,
               username='admin',
               password='password'
        )
        self.assertEquals(response.status_code, 200, 'qs lookup')
        xobj_querysets = xobj.parse(response.content)
        results = xobj_querysets.query_sets.query_set
        self.assertEquals(len(results), len(actual_qs), 'admin gets full queryset results')

        # syadmin user can only see some query sets -- those which he has Read Set
        # on and those marked 'public'
        response = self._get(url,
               username=self.sysadmin_user.user_name,
               password='password'
        )
        self.assertEquals(response.status_code, 200, 'qs lookup')
        xobj_querysets = xobj.parse(response.content)
        results = xobj_querysets.query_sets.query_set
        self.assertEquals(len(results), 12, 'sysadmin user gets fewer results')

        # sysadmin user CAN see & use the all systems queryset
        # because he has permissions on it
        response = self._get("query_sets/%s" % self.sys_queryset.pk,
            username=self.sysadmin_user.user_name,
            password='password'
        )
        self.assertEquals(response.status_code, 200)
        response = self._get("query_sets/%s/all" % self.sys_queryset.pk,
            username=self.sysadmin_user.user_name,
            password='password'
        )
        self.assertEquals(response.status_code, 200)

        # able to dump the grant matrix report (UI specific) for
        # queryset
        response = self._get("query_sets/%s/grant_matrix" % self.sys_queryset.pk,
            username='admin',
            password='password'
        )
        self.assertEquals(response.status_code, 200)

        # intern user can't see or use the datacenter query set
        # because he hasn't been given permissions on it, but he can
        # see all systems -- it is public
        response = self._get("query_sets/%s" % self.sys_queryset.pk,
            username=self.intern_user.user_name,
            password='password'
        )
        self.assertEquals(response.status_code, 200)
        response = self._get("query_sets/%s" % self.lab_queryset.pk,
            username=self.intern_user.user_name,
            password='password'
        )
        self.assertEquals(response.status_code, 403)

        # is allowed to get in because ANYBODY can access to try the set
        # but because no permissions are to be matched there should be
        # size zero results

        response = self._get("query_sets/%s/all" % self.sys_queryset.pk,
            username=self.intern_user.user_name,
            password='password'
        )

        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.empty_systems_set)

        # TODO: add a more complex test showing size < full but > 0
        # results.

        # intern user can't read info about sysadmin user
        response = self._get("users/%s" % self.sysadmin_user.pk,
            username=self.intern_user.user_name,
            password='password',
        )
        self.assertEquals(response.status_code, 403)

        # intern user can always read himself
        response = self._get("users/%s" % self.intern_user.pk,
            username=self.intern_user.user_name,
            password='password',
        )
        self.assertEquals(response.status_code, 200)

        # intern user can try to fetch the whole user list, but will get
        # just itself

        # FIXME -- doesn't this redirect to the All Users QS?
        # it should.

        response = self._get("users/",
            username=self.intern_user.user_name,
            password='password',
        )
        self.assertEquals(response.status_code, 200)
        doc = xobj.parse(response.content)
        self.failUnlessEqual(doc.users.user.user_name, self.intern_user.user_name)

        # sysadmin user can't see the whole user list
        # but DOES have permission to ALL USERS queryset
        # and can see the intern because of the queryset
        # mapping
        response = self._get("users/",
            username=self.sysadmin_user.user_name,
            password='password',
        )
        self.assertEquals(response.status_code, 200)
        doc = xobj.parse(response.content)
        self.failUnlessEqual([ x.user_name for x in doc.users.user ],
            [ 'admin', 'testuser', 'test-rce1341', 'ExampleSysadmin',
              'ExampleDeveloper', 'ExampleIntern', ]
        )

        response = self._get("query_sets/%s/all" % self.user_queryset.pk,
            username=self.admin_user.user_name,
            password='password'
        )
        self.assertEquals(response.status_code, 200)
        response = self._get("users/%s" % self.intern_user.pk,
            username=self.sysadmin_user.user_name,
            password='password',
        )
        self.assertEquals(response.status_code, 200)

    def testReadListOfPermissionTypes(self):
        response = self._get("rbac/permissions/")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.permission_type_list_xml)

    def testReadPermissionType(self):
        response = self._get("rbac/permissions/2")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.permission_type_get_xml)

    def testWriteImpliesRead(self):
        # if you can write to something, you can read
        # even if permission isn't in DB
        # write on queryset member also implies read on queryset itself
        for action in [ READMEMBERS, MODMEMBERS ]:
            self.assertTrue(self.mgr.userHasRbacPermission(
                self.sysadmin_user, self.datacenter_system, action
            ))
        # but not write on queryset
        self.assertFalse(self.mgr.userHasRbacPermission(
            self.sysadmin_user, self.datacenter_system, MODSETDEF
        ))
        # nor read, because querysets and member rights are not linked
        self.assertFalse(self.mgr.userHasRbacPermission(
            self.sysadmin_user, self.datacenter_system, READSET
        ))

    def testReadDoesNotImplyWrite(self):
        # if you can read, that doesn't mean write
        self.assertTrue(self.mgr.userHasRbacPermission(
            self.developer_user, self.datacenter_system, READMEMBERS
        ))
        self.assertFalse(self.mgr.userHasRbacPermission(
            self.developer_user, self.datacenter_system, MODMEMBERS
        ))

    def testNothingImpliesLockout(self):
        # if you don't have any permissions, you can neither
        # read nor write
        to_test = [READMEMBERS,MODMEMBERS,READSET,MODSETDEF]
        for action in to_test:
            self.assertFalse(self.mgr.userHasRbacPermission(
                self.developer_user, self.tradingfloor_system, action
            ))

    def testResourceWithoutContextImpliesNonAdminLockout(self):
        # if a resource is not in any queryset access is admin only
        to_test = [READMEMBERS,MODMEMBERS,READSET,MODSETDEF]
        for action in to_test:
            self.assertTrue(self.mgr.userHasRbacPermission(
                self.admin_user, self.lost_system, action,
            ))

class MetaRbac(RbacTestCase):
    '''Tests that involve RBAC on the RBAC'''

    def setUp(self):
        setup_core(self)

    def testRoleWithRbac(self):
        # user can get a role they are in
        # this role should NOT leak other members in the role
        url = "rbac/roles/%s" % self.developer_role.pk
        response = self._get(url, username="ExampleDeveloper", password="password")
        self.assertEqual(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.role_get_xml)
        # user outside of role cannot see role
        response = self._get(url, username="ExampleIntern", password="password")
        self.assertEqual(response.status_code, 403)
        # admin users can always get in
        response = self._get(url, username="admin", password="password")
        self.assertEqual(response.status_code, 200)

    def testCanViewUserRoles(self):
        # ExampleDeveloper can also see his roles
        user_id = self.developer_user.pk
        url = "users/%s/roles/" % user_id
        response = self._get(url, username="ExampleDeveloper", password="password")
        self.assertEqual(response.status_code, 200)
        # but another user cannot see another user's roles
        response = self._get(url, username="ExampleIntern", password="password")
        self.assertEqual(response.status_code, 403)

        # of course admin users can always get in
        response = self._get(url, username="admin", password="password")
        self.assertEqual(response.status_code, 200)
        # also make sure role is visible by alternative URL
        url = "users/%s/roles/%s" % (user_id, self.developer_role.pk)
        response = self._get(url, username="ExampleDeveloper", password="password")
        self.assertEqual(response.status_code, 200)
        # but not by users not in the role
        response = self._get(url, username="ExampleIntern", password="password")
        self.assertEqual(response.status_code, 403)
        # though admins can
        response = self._get(url, username="admin", password="password")
        self.assertEqual(response.status_code, 200)

#####################################################
#  NOTE: RBAC tests for other modules (403 vs 200, etc, also exist in other modules)

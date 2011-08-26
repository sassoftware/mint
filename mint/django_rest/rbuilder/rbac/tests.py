import testsxml
from xobj import xobj
from mint.django_rest.rbuilder.rbac import models
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.querysets import models as querymodels
from mint.django_rest.rbuilder.rbac.manager.rbacmanager import \
   RMEMBER, WMEMBER, RQUERYSET, WQUERYSET

# Suppress all non critical msg's from output
# still emits traceback for failed tests
import logging
logging.disable(logging.CRITICAL)

from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

# REMAINING TEST ITEMS for RBAC:
# * tests for RQUERYSET, WQUERYSET
# * make hasRbacPermission take a resource, not a queryset
# * test on live resources inside of querySets
# * test assertRbac functions

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
        #if response.status_code != expect:
        #     print "RESPONSE: %s\n" % response.content
        self.failUnlessEqual(response.status_code, expect, "Expected status code of %s for %s" % (expect, url))
        return response.content

class RbacBasicTestCase(RbacTestCase):

    #def setUp(self):
    #    # just a stub for later...
    #    XMLTestCase.setUp(self)
    #    pass

    def testModelsForRbacRoles(self):
        '''verify django models for roles work'''

        sysadmin = models.RbacRole(pk='sysadmin')
        sysadmin.save()
        developer = models.RbacRole(pk='developer')
        developer.save()

        self.assertEquals(len(models.RbacRole.objects.all()), 2,
            'correct number of results'
        )

        developer2 = models.RbacRole.objects.get(pk='developer')
        self.assertEquals(developer2.role_id, 'developer', 
            'object fetched correctly'
        )

    def testModelsForRbacPermissions(self):

        # TODO: load from queryset fixture?
        queryset1 = querymodels.QuerySet()
        queryset1.save()

        role1    = models.RbacRole(pk='sysadmin')
        role1.save() 
        action_name = 'speak freely'
        permission = models.RbacPermission(
           queryset        = queryset1,
           role            = role1,
           permission      = action_name,
        )
        permission.save()
        permissions2 = models.RbacPermission.objects.filter(
           queryset = queryset1
        )
        self.assertEquals(len(permissions2), 1, 'correct length')
        found = permissions2[0]
        self.assertEquals(found.permission, action_name, 'saved ok')
        self.assertEquals(found.queryset.pk, 15, 'saved ok')
        self.assertEquals(found.role.pk, 'sysadmin', 'saved ok')

    def testModelsForUserRoleAssignment(self):
        # note -- we may also keep roles in AD, this is for the case
        # where we sync them or manage them internally.  This will 
        # probably need to be configurable
        user1 = usersmodels.User(
            user_name = "test",
            full_name = "test"
        )
        user1.save()
        role1 = models.RbacRole(pk='sysadmin')
        role1.save()
        mapping = models.RbacUserRole(
            user = user1,
            role = role1
        ) 
        mapping.save()
        mappings2  = models.RbacUserRole.objects.filter(
            user = user1
        )
        self.assertEquals(len(mappings2), 1, 'correct length')
        found = mappings2[0]
        self.assertEquals(found.user.user_name, 'test', 'saved ok')
        self.assertEquals(found.role.pk, 'sysadmin', 'saved ok')

class RbacRoleViews(RbacTestCase):

    def setUp(self):
        RbacTestCase.setUp(self)
        self.seed_data = [ 'sysadmin', 'developer', 'intern' ]
        for item in self.seed_data:
            models.RbacRole(item).save()
       
    def testCanListRoles(self):

        url = 'rbac/roles'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)

        obj = xobj.parse(content)
        found_items = self._xobj_list_hack(obj.roles.role)
        found_items = [ item.role_id for item in found_items ] 
        for expected in self.seed_data:
            self.assertTrue(expected in found_items, 'found item')
        self.assertEqual(len(found_items), len(self.seed_data), 'right number of items')
        self.assertXMLEquals(content, testsxml.role_list_xml)
 
    def testCanGetSingleRole(self):

        url = 'rbac/roles/developer'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        obj = xobj.parse(content)
        self.assertEqual(obj.role.role_id, 'developer')
        self.assertXMLEquals(content, testsxml.role_get_xml)

    def testCanAddRoles(self):
        
        url = 'rbac/roles'
        input = testsxml.role_put_xml_input   
        output = testsxml.role_put_xml_output
        content = self.req(url, method='POST', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='POST', data=input, expect=200, is_admin=True)
        found_items = models.RbacRole.objects.get(pk='rocketsurgeon')
        self.assertEqual(found_items.pk, 'rocketsurgeon')
        self.assertXMLEquals(content, output)

    def testCanDeleteRoles(self):

        url = 'rbac/roles/sysadmin'
        self.req(url, method='DELETE', expect=401, is_authenticated=True)
        self.req(url, method='DELETE', expect=204, is_admin=True)
        self.failUnlessRaises(models.RbacRole.DoesNotExist,
            lambda: models.RbacRole.objects.get(pk='sysadmin'))

    def testCanUpdateRoles(self):
        
        url = 'rbac/roles/sysadmin'
        input = testsxml.role_put_xml_input   # reusing put data is fine here
        output = testsxml.role_put_xml_output
        content = self.req(url, method='PUT', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='PUT', data=input, expect=200, is_admin=True)
        found_items = models.RbacRole.objects.get(pk='rocketsurgeon')
        self.failUnlessRaises(models.RbacRole.DoesNotExist,
            lambda: models.RbacRole.objects.get(pk='sysadmin'))
        self.assertEqual(found_items.pk, 'rocketsurgeon')
        self.assertXMLEquals(content, output)

class RbacPermissionViews(RbacTestCase):
    
    def setUp(self):
        RbacTestCase.setUp(self)

        self.seed_data = [ 'sysadmin', 'developer', 'intern' ]
        for item in self.seed_data:
            models.RbacRole(item).save()

        models.RbacPermission(
            queryset      = self.datacenter_queryset,
            role          = models.RbacRole.objects.get(pk='sysadmin'),
            permission    = WMEMBER
        ).save()
        models.RbacPermission(
            queryset       = self.datacenter_queryset,
            role           = models.RbacRole.objects.get(pk='developer'),
            permission     = RMEMBER
        ).save()
        models.RbacPermission(
            queryset       = self.lab_queryset,
            role           = models.RbacRole.objects.get(pk='developer'),
            permission     = WMEMBER
        ).save()

    def testCanListPermissions(self):
        url = 'rbac/grants'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)

        obj = xobj.parse(content)
        found_items = self._xobj_list_hack(obj.grants.grant)
        self.assertEqual(len(found_items), 3, 'right number of items')
        self.assertXMLEquals(content, testsxml.permission_list_xml)

    def testCanGetSinglePermission(self):
        url = 'rbac/grants/1'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.permission_get_xml)

    def testCanAddPermissions(self):
        url = 'rbac/grants'
        input = testsxml.permission_post_xml_input
        output = testsxml.permission_post_xml_output
        content = self.req(url, method='POST', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='POST', data=input, expect=200, is_admin=True)
        self.assertXMLEquals(content, output)
        perm = models.RbacPermission.objects.get(pk=4)
        self.assertEqual(perm.role.pk, 'intern')
        self.assertEqual(perm.queryset.pk, self.tradingfloor_queryset.pk)
        self.assertEqual(perm.permission, WMEMBER)

    def testCanDeletePermissions(self):
       
        all = models.RbacPermission.objects.all()
        url = 'rbac/grants/1'
        self.req(url, method='DELETE', expect=401, is_authenticated=True)
        self.req(url, method='DELETE', expect=204, is_admin=True)
        all = models.RbacPermission.objects.all()
        self.assertEqual(len(all), 2, 'deleted an object')


    def testCanUpdatePermissions(self):
        
        url = 'rbac/grants/1'
        input = testsxml.permission_put_xml_input
        output = testsxml.permission_put_xml_output
        content = self.req(url, method='PUT', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='PUT', data=input, expect=200, is_admin=True)
        self.assertXMLEquals(content, output)
        perm = models.RbacPermission.objects.get(pk=1)
        self.assertEqual(perm.role.pk, 'intern')
        self.assertEqual(perm.queryset.pk, self.datacenter_queryset.pk)
        self.assertEqual(perm.permission, WMEMBER)

class RbacUserRoleViewTests(RbacTestCase):

    def setUp(self):

        RbacTestCase.setUp(self)
        #self.seed_data = [ 'datacenter', 'lab', 'tradingfloor' ]
        #for item in self.seed_data:
        #    models.RbacContext(item).save()

        self.seed_data = [ 'sysadmin', 'developer', 'intern' ]
        for item in self.seed_data:
            models.RbacRole(item).save()
        self.sysadmin   = models.RbacRole.objects.get(role_id='sysadmin')
        self.developer  = models.RbacRole.objects.get(role_id='developer')
        self.intern     = models.RbacRole.objects.get(role_id='intern')
        # this is a little off as admins are NOT subject to rbac, but
        # we're not testing the auth chain here, just the models and services
        # so it doesn't really matter what users we use in the tests.
        self.admin_user = usersmodels.User.objects.get(user_name='admin')
        self.test_user  = usersmodels.User.objects.get(user_name='testuser')

        # admin user has two roles
        models.RbacUserRole(
            role=self.sysadmin, user=self.admin_user,
        ).save()
        models.RbacUserRole(
            role=self.developer, user=self.admin_user,
        ).save()
        # test user is an intern, just one role
        models.RbacUserRole(
            role=self.intern, user=self.test_user
        ).save()

      
    def testCanListUserRoles(self):
        user_id = self.admin_user.pk
        url = "users/%s/roles/" % user_id
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        obj = xobj.parse(content)
        found_items = self._xobj_list_hack(obj.roles.role)
        self.assertEqual(len(found_items), 2, 'right number of items')
        self.assertXMLEquals(content, testsxml.user_role_list_xml)

    def testCanGetSingleUserRole(self):
        # this is admittedly a rather useless function, which only 
        # confirms/denies where a user is in a role.  More likely 
        # we'd ask if they had permission to do something, and more 
        # as an internals thing than a REST function.  Still, here, 
        # for completeness.

        user_id = self.admin_user.pk
        url = "users/%s/roles/developer" % user_id
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
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
        content = self.req(url, method='POST', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='POST', data=input, expect=200, is_admin=True)
        self.assertXMLEquals(content, output)
        user_role = models.RbacUserRole.objects.get(user = self.admin_user, role=self.intern)
        self.assertEqual(user_role.user.pk, self.admin_user.pk)
        self.assertEqual(user_role.role.pk, 'intern')

    def testCanDeleteUserRoles(self):
        user_id = self.admin_user.pk
        url = "users/%s/roles/developer" % user_id
        get_url = "users/%s/roles/" % user_id
        # make admin no longer a developer
        self.req(url, method='DELETE', expect=401, is_authenticated=True)
        self.req(url, method='DELETE', expect=204, is_admin=True)
        all = models.RbacUserRole.objects.all()
        self.assertEquals(len(all), 2, 'right number of objects')
        content = self.req(url, method='GET', expect=404, is_admin=True)
        content = self.req(get_url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.user_role_get_list_xml_after_delete)


class RbacEngine(RbacTestCase):
    def setUp(self):
        RbacTestCase.setUp(self)

        role_seed_data = [ 'sysadmin', 'developer', 'intern' ]
        for item in role_seed_data:
            models.RbacRole(item).save()

        def mk_permission(queryset, role, action):
            models.RbacPermission(
                queryset      = queryset,
                role          = models.RbacRole.objects.get(pk=role),
                permission    = action
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
            #print response.content            

            dbuser = usersmodels.User.objects.get(pk = int(user.user.user_id))

            # add rbac role mapping
            models.RbacUserRole(
               user = dbuser,
               role = models.RbacRole.objects.get(pk=role)
            ).save()
            return dbuser

        mk_permission(self.datacenter_queryset, 'sysadmin',  WMEMBER)
        mk_permission(self.datacenter_queryset, 'developer', RMEMBER)
        mk_permission(self.sys_queryset, 'sysadmin', RQUERYSET)
        mk_permission(self.user_queryset, 'sysadmin', RMEMBER)
        mk_permission(self.projects_queryset, 'sysadmin', RMEMBER)

        self.admin_user     = usersmodels.User.objects.get(user_name='admin')
        self.admin_user._is_admin = True
        self.sysadmin_user  = mk_user('ExampleSysadmin', False, 'sysadmin')
        self.developer_user = mk_user('ExampleDeveloper', False, 'developer')
        self.intern_user    = mk_user('ExampleIntern', False, 'intern')


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
        for action in [ RMEMBER, WMEMBER, RQUERYSET, WQUERYSET ]:
            for system in self.test_systems:
                self.assertTrue(self.mgr.userHasRbacPermission(
                    self.admin_user, system, action
                ))

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

        # syadmin user can only see some query sets       
        response = self._get(url,
               username=self.sysadmin_user.user_name,
               password='password'
        )
        self.assertEquals(response.status_code, 200, 'qs lookup')
        xobj_querysets = xobj.parse(response.content)
        results = xobj_querysets.query_sets.query_set
        # granted permission to 2 systems querysets + 1 user queryset
        self.assertEquals(len(results), 4, 'sysadmin user gets fewer results')
 
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
 
        # intern user can't see or use the datacenter query set
        # because he hasn't been given permissions on it
        response = self._get("query_sets/%s" % self.sys_queryset.pk,
            username=self.intern_user.user_name,
            password='password'
        )
        self.assertEquals(response.status_code, 403)
        response = self._get("query_sets/%s/all" % self.sys_queryset.pk,
            username=self.intern_user.user_name,
            password='password'
        )
        self.assertEquals(response.status_code, 403)

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

        # intern user cannot fetch the whole user list
        # (which is not queryset based, needs admin)
        response = self._get("users/",
            username=self.intern_user.user_name,
            password='password',
        )
        self.assertEquals(response.status_code, 403)
        
        # sysadmin user can't see the whole user list
        # but DOES have permission to ALL USERS queryset
        # and can see the intern because of the queryset
        # mapping 
        response = self._get("users/",
            username=self.sysadmin_user.user_name,
            password='password',
        )
        self.assertEquals(response.status_code, 403)
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
              
 
    def testWriteImpliesRead(self):
        # if you can write to something, you can read
        # even if permission isn't in DB
        # write on queryset member also implies read on queryset itself
        for action in [ RMEMBER, WMEMBER ]:
            self.assertTrue(self.mgr.userHasRbacPermission(
                self.sysadmin_user, self.datacenter_system, action
            ))
        # but not write on queryset
        self.assertFalse(self.mgr.userHasRbacPermission(
            self.sysadmin_user, self.datacenter_system, WQUERYSET
        ))
        # nor read, because querysets and member rights are not linked
        self.assertFalse(self.mgr.userHasRbacPermission(
            self.sysadmin_user, self.datacenter_system, RQUERYSET
        ))

    def testReadDoesNotImplyWrite(self):
        # if you can read, that doesn't mean write
        self.assertTrue(self.mgr.userHasRbacPermission(
            self.developer_user, self.datacenter_system, RMEMBER
        ))
        self.assertFalse(self.mgr.userHasRbacPermission(
            self.developer_user, self.datacenter_system, WMEMBER
        ))

    def testNothingImpliesLockout(self):
        # if you don't have any permissions, you can neither
        # read nor write
        to_test = [RMEMBER,WMEMBER,RQUERYSET,WQUERYSET]
        for action in to_test:
            self.assertFalse(self.mgr.userHasRbacPermission(
                self.developer_user, self.tradingfloor_system, action
            ))

    def testResourceWithoutContextImpliesNonAdminLockout(self):
        # if a resource is not in any queryset access is admin only
        to_test = [RMEMBER,WMEMBER,RQUERYSET,WQUERYSET]
        for action in to_test:
            self.assertTrue(self.mgr.userHasRbacPermission(
                self.admin_user, self.lost_system, action,
            ))

    def testCannotLookupPermissionsOnNonConfiguredAction(self):
        # if you test against an action type that does not
        # exist (due to code error?) you don't get in
        self.assertFalse(self.mgr.userHasRbacPermission(
            self.developer_user, self.lost_system, 'some fake action type'
        ))

# SEE ALSO (PENDING) tests in inventory and other services


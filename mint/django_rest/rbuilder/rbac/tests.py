import testsxml
from xobj import xobj
from mint.django_rest.rbuilder.rbac import models
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.inventory import models as inventorymodels
from mint.django_rest.rbuilder.manager import rbuildermanager

# Suppress all non critical msg's from output
# still emits traceback for failed tests
import logging
logging.disable(logging.CRITICAL)

from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

class RbacTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)

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
        if response.status_code != expect:
             print "RESPONSE: %s\n" % response.content
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

    def testModelsForRbacContexts(self):
        datacenter = models.RbacContext(pk='datacenter')
        datacenter.save()
        desktops = models.RbacContext(pk='desktops')
        desktops.save()
        self.assertEquals(len(models.RbacContext.objects.all()), 2,
           'correct number of results'
        ) 
        desktops2 = models.RbacContext.objects.get(pk='desktops')
        self.assertEqual(desktops2.context_id, 'desktops',
           'fetched correctly'
        )

    def testModelsForRbacPermissions(self):
        context1 = models.RbacContext(pk='datacenter')
        context1.save()
        role1    = models.RbacRole(pk='sysadmin')
        role1.save() 
        action_name = 'speak freely'
        permission = models.RbacPermission(
           rbac_context    = context1,
           rbac_role       = role1,
           # TODO: add choice restrictions
           action     = action_name,
        )
        permission.save()
        permissions2 = models.RbacPermission.objects.filter(
           rbac_context = context1
        )
        self.assertEquals(len(permissions2), 1, 'correct length')
        found = permissions2[0]
        self.assertEquals(found.action, action_name, 'saved ok')
        self.assertEquals(found.rbac_context.pk, 'datacenter', 'saved ok')
        self.assertEquals(found.rbac_role.pk, 'sysadmin', 'saved ok')

    def testModelsForUserRoleAssignment(self):
        # note -- we may also keep roles in AD, this is for the case
        # where we sync them or manage them internally.  This will 
        # probably need to be configurable
        # TODO -- test many to many relation in user
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

    def testModelsForSystemContextAssignment(self):
        pass

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
        found_items = self._xobj_list_hack(obj.rbac_roles.rbac_role)
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
        self.assertEqual(obj.rbac_role.role_id, 'developer')
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
        self.seed_data = [ 'datacenter', 'lab', 'tradingfloor' ]
        for item in self.seed_data:
            models.RbacContext(item).save()
        self.seed_data = [ 'sysadmin', 'developer', 'intern' ]
        for item in self.seed_data:
            models.RbacRole(item).save()
        models.RbacPermission(
            rbac_context  = models.RbacContext.objects.get(pk='datacenter'),
            rbac_role     = models.RbacRole.objects.get(pk='sysadmin'),
            action        = 'write'
        ).save()
        models.RbacPermission(
            rbac_context   = models.RbacContext.objects.get(pk='datacenter'),
            rbac_role      = models.RbacRole.objects.get(pk='developer'),
            action         = 'read'
        ).save()
        models.RbacPermission(
            rbac_context   = models.RbacContext.objects.get(pk='lab'),
            rbac_role      = models.RbacRole.objects.get(pk='developer'),
            action    = 'write'
        ).save()

    def testCanListPermissions(self):
        url = 'rbac/permissions'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)

        obj = xobj.parse(content)
        found_items = self._xobj_list_hack(obj.rbac_permissions.rbac_permission)
        self.assertEqual(len(found_items), 3, 'right number of items')
        self.assertXMLEquals(content, testsxml.permission_list_xml)

    def testCanGetSinglePermission(self):
        url = 'rbac/permissions/1'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.permission_get_xml)

    def testCanAddPermissions(self):
        url = 'rbac/permissions'
        input = testsxml.permission_post_xml_input
        output = testsxml.permission_post_xml_output
        content = self.req(url, method='POST', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='POST', data=input, expect=200, is_admin=True)
        self.assertXMLEquals(content, output)
        perm = models.RbacPermission.objects.get(pk=4)
        self.assertEqual(perm.rbac_role.pk, 'intern')
        self.assertEqual(perm.rbac_context.pk, 'tradingfloor')
        self.assertEqual(perm.action, 'write')

    def testCanDeletePermissions(self):
       
        all = models.RbacPermission.objects.all()
        url = 'rbac/permissions/1'
        self.req(url, method='DELETE', expect=401, is_authenticated=True)
        self.req(url, method='DELETE', expect=204, is_admin=True)
        all = models.RbacPermission.objects.all()
        self.assertEqual(len(all), 2, 'deleted an object')


    def testCanUpdatePermissions(self):
        
        url = 'rbac/permissions/1'
        input = testsxml.permission_put_xml_input
        output = testsxml.permission_put_xml_output
        content = self.req(url, method='PUT', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='PUT', data=input, expect=200, is_admin=True)
        self.assertXMLEquals(content, output)
        perm = models.RbacPermission.objects.get(pk=1)
        self.assertEqual(perm.rbac_role.pk, 'intern')
        self.assertEqual(perm.rbac_context.pk, 'tradingfloor')
        self.assertEqual(perm.action, 'write')

class RbacContextViews(RbacTestCase):

    def setUp(self):

        RbacTestCase.setUp(self)
        self.seed_data = [ 'datacenter', 'lab', 'tradingfloor' ]
        for item in self.seed_data:
            models.RbacContext(item).save()

    def testCanListContexts(self):

        url = 'rbac/contexts'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)

        obj = xobj.parse(content)
        found_items = self._xobj_list_hack(obj.rbac_contexts.rbac_context)
        found_items = [ item.context_id for item in found_items ]
        for expected in self.seed_data:
            self.assertTrue(expected in found_items, 'found item')
        self.assertEqual(len(found_items), len(self.seed_data), 'right number of items')
        self.assertXMLEquals(content, testsxml.context_list_xml)

    def testCanGetSingleContext(self):

        url = 'rbac/contexts/datacenter'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        obj = xobj.parse(content)
        self.assertEqual(obj.rbac_context.context_id, 'datacenter')
        self.assertXMLEquals(content, testsxml.context_get_xml)

    def testCanAddContext(self):

        url = 'rbac/contexts'
        input = testsxml.context_put_xml_input
        output = testsxml.context_put_xml_output
        content = self.req(url, method='POST', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='POST', data=input, expect=200, is_admin=True)
        found_items = models.RbacContext.objects.get(pk='datacenter2')
        self.assertEqual(found_items.pk, 'datacenter2')
        self.assertXMLEquals(content, output)

    def testCanDeleteContext(self):

        url = 'rbac/contexts/lab'
        self.req(url, method='DELETE', expect=401, is_authenticated=True)
        self.req(url, method='DELETE', expect=204, is_admin=True)
        self.failUnlessRaises(models.RbacContext.DoesNotExist,
            lambda: models.RbacContext.objects.get(pk='lab'))

    def testCanUpdateContext(self):

        url = 'rbac/contexts/datacenter'
        input = testsxml.context_put_xml_input   # reusing put data is fine here
        output = testsxml.context_put_xml_output
        content = self.req(url, method='PUT', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='PUT', data=input, expect=200, is_admin=True)
        found_items = models.RbacContext.objects.get(pk='datacenter2')
        self.failUnlessRaises(models.RbacContext.DoesNotExist,
            lambda: models.RbacContext.objects.get(pk='datacenter'))
        self.assertEqual(found_items.pk, 'datacenter2')
        self.assertXMLEquals(content, output)

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
        url = "rbac/users/%s/roles/" % user_id
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        obj = xobj.parse(content)
        found_items = self._xobj_list_hack(obj.rbac_roles.rbac_role)
        self.assertEqual(len(found_items), 2, 'right number of items')
        self.assertXMLEquals(content, testsxml.user_role_list_xml)

    def testCanGetSingleUserRole(self):
        # this is admittedly a rather useless function, which only 
        # confirms/denies where a user is in a role.  More likely 
        # we'd ask if they had permission to do something, and more 
        # as an internals thing than a REST function.  Still, here, 
        # for completeness.

        user_id = self.admin_user.pk
        url = "rbac/users/%s/roles/developer" % user_id
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.user_role_get_xml)
        # now verify if the role isn't assigned to the user, we can't fetch it
        url = "rbac/users/%s/roles/intern" % user_id
        content = self.req(url, method='GET', expect=404, is_admin=True)
          
    def testCanAddUserRoles(self):
        user_id = self.admin_user.pk
        url = "rbac/users/%s/roles/" % user_id
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
        url = "rbac/users/%s/roles/developer" % user_id
        get_url = "rbac/users/%s/roles/" % user_id
        # make admin no longer a developer
        self.req(url, method='DELETE', expect=401, is_authenticated=True)
        self.req(url, method='DELETE', expect=204, is_admin=True)
        all = models.RbacUserRole.objects.all()
        self.assertEquals(len(all), 2, 'right number of objects')
        content = self.req(url, method='GET', expect=404, is_admin=True)
        content = self.req(get_url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.user_role_get_list_xml_after_delete)

    # (UPDATE DOES NOT MAKE SENSE, AND IS NOT SUPPORTED)

class RbacSystemViewTests(RbacTestCase):
    ''' Can we view and manipulate the system context as an admin?'''

    def setUp(self):
        RbacTestCase.setUp(self)
        
        mgr = rbuildermanager.RbuilderManager()
        local_zone = mgr.sysMgr.getLocalZone()
        self.system = inventorymodels.System(
            name='testSystem', managing_zone=local_zone
        )
        self.datacenter = models.RbacContext('datacenter')
        self.lab = models.RbacContext('lab')
        self.datacenter.save()
        self.lab.save()
        self.system.rbac_context = self.datacenter
        self.system.save()

    def testCanGetSystemContext(self):
        url = "rbac/resources/system/%d/context" % self.system.pk
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.system_context_get_xml)

    def testCanAssignSystemToContext(self):
        url = "rbac/resources/system/%d/context" % self.system.pk
        input = testsxml.system_context_put_xml_input   
        output = testsxml.system_context_put_xml_output
        content = self.req(url, method='PUT', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='PUT', data=input, expect=200, is_admin=True)
        found_item = inventorymodels.System.objects.get(name='testSystem')
        self.assertEquals(found_item.rbac_context.pk, 'lab')
        content = self.req(url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.system_context_get_xml2)

    def testCanRemoveSystemContext(self):
        url = "rbac/resources/system/%d/context" % self.system.pk
        content = self.req(url, method='DELETE', expect=401, is_authenticated=True)
        content = self.req(url, method='DELETE', expect=204, is_admin=True)
        found_item = inventorymodels.System.objects.get(name='testSystem')
        self.assertEquals(found_item.rbac_context, None)

class RbacEngineTests(RbacTestCase):
    '''Do we know when to grant or deny access?'''

    def setUp(self):
        RbacTestCase.setUp(self)

        # create a couple of users, with varying contexts
        # sysadmin -- WRITE to datacenter
        # developer -- READ to datacenter
        # developer -- WRITE to lab
        # everyone -- NOTHING to tradingfloor

        self.seed_data = [ 'datacenter', 'lab', 'tradingfloor' ]
        for item in self.seed_data:
            models.RbacContext(item).save()
        self.seed_data = [ 'sysadmin', 'developer', 'intern' ]
        for item in self.seed_data:
            models.RbacRole(item).save()
        models.RbacPermission(
            rbac_context  = models.RbacContext.objects.get(pk='datacenter'),
            rbac_role     = models.RbacRole.objects.get(pk='sysadmin'),
            action        = 'write'
        ).save()
        models.RbacPermission(
            rbac_context   = models.RbacContext.objects.get(pk='datacenter'),
            rbac_role      = models.RbacRole.objects.get(pk='developer'),
            action         = 'read'
        ).save()
        models.RbacPermission(
            rbac_context   = models.RbacContext.objects.get(pk='lab'),
            rbac_role      = models.RbacRole.objects.get(pk='developer'),
            action    = 'write'
        ).save()

        self.admin_user = usersmodels.User.objects.get(user_name='admin')
        self.sysadmin_user = usersmodels.User(
            user_name = 'Example Sysadmin'
        )
        self.sysadmin_user.save()

        self.developer_user = usersmodels.User(
            user_name = 'Example Developer'
        )
        self.developer_user.save()

        # summary:
        # admin user has full access
        #    can READ on tradingfloor
        #    can write on tradingfloor
        # sysadmin user can WRITE on datacenter
        #    read is implied
        # developer can READ on datacenter
        #    write is not granted
        # developer lacks all permissions on tradingfloor
        #    developer can NOT read
        #    developer can NOT write
        # loose system without context?  
        #    admin can write
        #    everybody can read

    def testAdminUserHasFullAccess(self):
        # admin user can do everything regardless of context
        # or permission
        #for action in [ 'read', 'write' ]:
        #    for context in [ 'lab', 'datacenter', 'tradingfloor' ]:
        #        self.assertTrue(self.mgr.userHasRbacPermission(
        #            self.admin_user, context, action
        #        ))
        pass

    def testWriteImpliesRead(self):
        # if you can write to something, you can read
        # even if permission isn't in DB
        #for action in [ 'read', 'write' ]:
        #    self.assertTrue(self.mgr.userHasRbacPermission(
        #        self.sysadmin_user, 'datacenter', action
        #    ))
        pass

    def testReadDoesNotImplyWrite(self):
        # if you can read, that doesn't mean write
        #self.assertTrue(self.mgr.userHasRbacPermission(
        #    self.developer_user, 'datacenter', 'read'
        #))
        #self.assertFalse(self.mgr.userHasRbacPermission(
        #    self.developer_user, 'datacenter', 'write'
        #))
        pass

    def testNothingImpliesLockout(self):
        # if you don't have any permissions, you can neither
        # read nor write
        #self.assertTrue(self.mgr.userHasRbacPermission(
        #    self.developer_user, 'tradingfloor', 'write'
        #))
        #self.assertTrue(self.mgr.userHasRbacPermission(
        #    self.developer_user, 'tradingfloor', 'read'
        #))
        pass

    def testResourceWithoutContextHasImpliedRules(self):
        # admin users can always read and write on
        # resources without contexts
        #self.assertTrue(self.mgr.userHasRbacPermission(
        #    self.admin_user, None, 'read'
        #))
        #self.assertTrue(self.mgr.userHasRbacPermission(
        #    self.admin_user, None, 'write'
        #))
        # non-admin users can only READ on resources
        # without contexts
        #self.assertTrue(self.mgr.userHasRbacPermission(
        #    self.developer_user, None, 'read'
        #))
        #self.assertFalse(self.mgr.userHasRbacPermission(
        #    self.developer_user, None, 'write'
        #))
        pass

    def testCannotLookupPermissionsOnNonConfiguredAction(self):
        # if you test against an action type that does not
        # exist, an error will be raised rather than
        # returning False
        #self.failUnlessRaises(Exception, lambda:
        #    self.mgr.userHasRbacPermission(
        #        self.developer_user, None, 'some fake action type'
        #    )
        #)
        pass

    def testCannotLookupPermissionOnInvalidContext(self):       
        # if you test against a context that doesn't exist an
        # error will be raised instead of returning False
        #self.failUnlessRaises(Exception, lambda:
        #    self.mgr.userHasRbacPermission(
        #        self.developer_user, 'imaginarycontext', 'read'
        #    )
        #)
        pass

# SEE ALSO (PENDING) tests in inventory and other services


# flood rpath database with objects so we can test queryset (and other) performance
# (C) rPath Inc, 2011

# import Django models -- easier cleanup

import psycopg2 as dbapi2
import requests
import xobj
import time
import os

import createxml

# leave test results around for manual testing?
CLEANUP_POST_TEST = False
# unique database prefix to use for created objects
TESTPREFIX = "loadtestspam"
# tables to clean up between runs
TABLES = { 
   'inventory_system'   : 'name',
   'users'              : 'username',
   'rbac_role'          : 'role_name',
   'querysets_queryset' : 'name'
}
# queryset resource_type list
QUERYSET_TYPES = [ 'user', 'project', 'project_branch_stage', 'target', 'system', 'image', ]
QUERYSET_SEARCH = {
    'user'                 : 'user_name',
    'project'              : 'name',
    'project_branch_stage' : 'name',
    'target'               : 'name',
    'system'               : 'name',
    'image'                : 'name'

}
ROLE_COUNT = 10
USERS_PER_ROLE = 10
SYSTEMS_PER_USER = 10
TOTAL_SYSTEMS = SYSTEMS_PER_USER * USERS_PER_ROLE * ROLE_COUNT
URL_TIMES = {}

class Requestor(object):

    def _req(self, method, url, server=None, auth=None, headers=None, 
        body=None, noparse=False, responseCode=200, timing=True):
     
        if not server:
            server = '127.0.0.1'
        url = "https://%s/api/v1%s" % (server, url)

        if not auth:
            auth = (
                os.environ.get('RUSER', 'admin'),
                os.environ.get('RPASS', 'password')
            )
        method = getattr(requests,method)
        start = time.time()
        response = method(url, auth=auth, headers=headers, data=body)
        end = time.time()
        if timing:
            # store time info in usable datastructure for future statistics
            pass
        if response.status_code != responseCode:
            try:
                print response.content
            except AttributeError, ae:
                print "No response"
            assert False, "%s != %s" % (response.status_code, responseCode)
        content =  response.content
 
        if noparse:
            return content
        return xobj.parse(content)

    def _get(self, url, **kwargs):
        return self._req("get", url, **kwargs)

    def _delete(self, url, **kwargs):
        if not kwargs.has_key('responseCode'):
            kwargs['responseCode']=204
        return self._req('delete', url, **kwargs)

    def _post(self, url, body, **kwargs):
        return self._req('post', url, body=body, **kwargs)
 
    def _put(self, url, body, **kwargs):
        return self._req("put", url, body=body, **kwargs)

class Cleanup(object):

  def __init__(self):
      self.db = dbapi2.connect(database="mint", user="postgres", port=5439)

  def run(self):
      self.deleteTestAdditions()
      self.db.close()

  def deleteTestAdditions(self):
      cu = self.db.cursor()
      for table, field in TABLES.iteritems():
          stmt = "DELETE FROM %s WHERE %s LIKE '%%%s%%'" % (table, field, TESTPREFIX)
          print stmt
          cu.execute(stmt)
      self.db.commit()

class ObjectSpammer(Requestor):

    def __init__(self):

        self.users     = {}
        self.userNames = {}
        self.querysets = {}
        self.grants    = {}
        self.querysets = {}
        self.roles     = {}
        self.projects  = {}
        self.systems   = {}

    def run(self):

        for roleCt in xrange(0, ROLE_COUNT):
            print "ADDING ROLE: %s" % roleCt
            roleId = self.addRole(roleCt)
            for resourceType in QUERYSET_TYPES:
                print "... querysets: %s" % resourceType
                qsId = self.addQuerySet(roleId, resourceType)
                self.addGrants(qsId, roleId)
                print "... users: (%s)" % USERS_PER_ROLE
                for userCt in xrange(0, USERS_PER_ROLE):
                    userName = "%s-%s" % (TESTPREFIX, userCt)
                    if not self.userNames.has_key(userName):
                        self.addUserWithRole(userName, roleId)
                    #if resource_type == 'system':
                    #    self.addSystems(userId)

    def addRole(self, roleCt):
        name = "%s-%s" % (TESTPREFIX, roleCt)
        xRole = self._post('/rbac/roles', createxml.createRole % {
           'name' : name
        })
        roleId = int(xRole.role.role_id)
        self.roles[roleId] = None
        return roleId

    def addQuerySet(self, roleId, resourceType):
        name = "%s-role%s-%s" % (TESTPREFIX, roleId, resourceType)
        print "adding QS: %s" % name
        xQs = self._post('/query_sets/', createxml.createQuerySet % {
           'name'         : name,
           'field'        : QUERYSET_SEARCH[resourceType],
           'resourceType' : resourceType
        })
        qsId = int(xQs.query_set.query_set_id)
        self.querysets[qsId] = None
        return qsId

    def addGrants(self, querySetId, roleId):
        # permission IDs so far constant across all rbuilders
        # may have to get dynamically later if we ever remove
        # any in migrations
        #          1 | ReadMembers    | Read Member Resources
        #          2 | ModMembers     | Modify Member Resources
        #          3 | ReadSet        | Read Set
        #          4 | ModSetDef      | Modify Set Definition
        #          5 | CreateResource | Create Resource
        permissionIds = [ 2, 3 ]
        grantIds = []
        for permissionId in permissionIds:
            xGrant = self._post('/rbac/grants', createxml.createGrant % {
                'querySetId'   : querySetId,
                'roleId'       : roleId,
                'permissionId' : permissionId
            })
            grantIds.append(int(xGrant.grant.grant_id))
        return grantIds

    def addUserWithRole(self, userName, roleId):
        xUser = self._post('/users/', createxml.createUser % {
            'name' : userName
        })
        userId = int(xUser.user.user_id)
        xUser = self._post("/rbac/roles/%s/users" % roleId, 
            createxml.addUserToRole % { 'userId' : userId }
        )
        self.users[userId] = None
        self.userNames[userName] = None
        return userId

    def addSystems(self, userId):
        print "!! system additions to implemented yet --"
        #for x in range(0, SYSTEMS_PER_USER):
        #    name = "%s-%s-%s" % (TESTPREFIX, userId, x)
        #    systemId = 123
        #    self.systems[systemId] = None

class AccessTester(object):

    def __init__(self):
        self

    def run(self):
        # request and time the ...
        #    All Systems queryset
        #    All Images
        #    All Projects
        #    All Project Stages
        #    All Users
        pass

if __name__ == '__main__':

    req      = Requestor()
    cleanup  = Cleanup()
    spammer  = ObjectSpammer()
    accessor = AccessTester()

    try:
        print "-- cleaning up any aborted test runs"
        cleanup.run()
        print "-- populating the API"
        spammer.run()
        print "-- testing queryset speed"
        accessor.run()
    finally:
        print "-- cleaning up from test run"
        if CLEANUP_POST_TEST:
            cleanup.run()





from mint.rest.api import models
from mint.rest import errors


class Database(object):
    def __init__(self, cfg, db):
        self.cfg = cfg
        self.db = db
        self.userId = -1
        self.isAdmin = False

    def setAuth(self, userId, username, isAdmin=False):
        self.userId = userId
        self.username = username
        self.isAdmin = isAdmin

    def _getOne(self, cu, exception, key):
        try:
            cu = iter(cu)
            res = cu.next()
            assert (not(list(cu))), key # make sure that we really only
                                        # got one entry
            return res
        except:
            raise exception(key)


    def listProducts(self):
        cu = self.db.cursor()
        if self.isAdmin:
            cu.execute('''
                SELECT projectId, hostname, name 
                FROM Projects ORDER BY hostname''')
        else:
            cu.execute('''
                SELECT Projects.projectId, hostname, name
                FROM Projects 
                LEFT JOIN ProjectUsers ON (
                    ProjectUsers.projectId=Projects.projectId 
                    AND userId=?)
                WHERE NOT Projects.hidden OR 
                      ProjectUsers.level IS NOT NULL
                ORDER BY hostname
               ''', self.userId)
        results = models.ProductSearchResultList()
        for id, hostname, name in cu:
            results.addProduct(id, hostname, name)
        return results

    def getProduct(self, hostname):
        cu = self.db.cursor()
        # NOTE: access check is built into this query - perhaps break out
        # for non-bulk queries.
        sql = '''
            SELECT Projects.projectId,hostname,name,shortname
                   description, Users.username as creator, projectUrl,
                   isAppliance, Projects.timeCreated, Projects.timeModified,
                   commitEmail, prodtype, backupExternal 
            from Projects
            LEFT JOIN ProjectUsers ON (
                ProjectUsers.projectId=Projects.projectId 
                AND ProjectUsers.userId=?)
            JOIN Users ON (Projects.creatorId==Users.userId)
            WHERE hostname=? AND
                  (NOT Projects.hidden OR 
                  ProjectUsers.level IS NOT NULL)
        '''
        cu.execute(sql, self.userId, hostname)
        d = dict(self._getOne(cu, errors.ProductNotFound, hostname))
        d['id'] = d.pop('projectId')
        return models.Product(**d)

    def requireProductReadAccess(self, hostname):
        cu = self.db.cursor()
        cu.execute('''SELECT hidden,level from Projects
                      LEFT JOIN ProjectUsers ON (userId=? 
                              AND ProjectUsers.projectId=Projects.projectId)
                      WHERE hostname=?''', self.userId, hostname)
        d = dict(self._getOne(cu, errors.ProductNotFound, hostname))

    def listProductVersions(self, hostname):
        self.requireProductReadAccess(hostname=hostname)
        cu = self.db.cursor()
        cu.execute('''SELECT productVersionId as id, 
                          PVTable.namespace, PVTable.name, PVTable.description  
                      FROM Projects 
                      JOIN ProductVersions as PVTable USING (projectId)
                      WHERE Projects.hostname=?''', hostname)
        pvl = models.ProductVersionList()
        for id, namespace, name, description in cu:
            pvl.addProductVersion(id, namespace, name, description,
                                  hostname)
        return pvl

    def listProductMembers(self, hostname):
        self.requireProductReadAccess(hostname=hostname)
        cu = self.db.cursor()
        cu.execute('''SELECT username, level
                      FROM Projects
                      JOIN ProjectUsers USING(projectId)
                      JOIN Users USING(userId)
                      WHERE hostname=?''', hostname)
        memberList = models.MemberList()
        for username, level in cu:
            member = models.Membership(hostname=hostname,
                                       username=username,
                                       level=level)
            memberList.members.append(member)
        return memberList

    def getProductMembership(self, hostname, username):
        self.requireProductReadAccess(hostname=hostname)
        cu = self.db.cursor()
        cu.execute('''SELECT level
                      FROM Projects
                      JOIN ProjectUsers USING(projectId)
                      JOIN Users USING(userId)
                      WHERE hostname=? AND username=?''', 
                      hostname, username)
        level, = self._getOne(cu, errors.MemberNotFound, (hostname, username))
        return models.Membership(hostname=hostname, username=username, 
                                 level=level)

    def getProductVersion(self, hostname, versionName):
        self.requireProductReadAccess(hostname=hostname)
        cu = self.db.cursor()
        cu.execute('''SELECT productVersionId as id, 
                          PVTable.namespace, PVTable.name, PVTable.description  
                      FROM Projects 
                      JOIN ProductVersions as PVTable USING (projectId)
                      WHERE Projects.hostname=? AND PVTable.name=?''', 
                      hostname, versionName)
        results = self._getOne(cu, errors.ProductVersionNotFound, 
                               (hostname, versionName))
        id, namespace, name, description = results
        return models.ProductVersion(id=id, hostname=hostname,
                                     namespace=namespace, name=name, 
                                     description=description)

    def requireUserReadAccess(self, username):
        if self.isAdmin or self.username == username:
            return
        raise errors.PermissionDenied()

    def requireAdmin(self):
        if not self.isAdmin:
            raise errors.PermissionDenied()

    def getUser(self, username):
        self.requireUserReadAccess(username)
        cu = self.db.cursor()
        cu.execute("""SELECT userId as id, username, fullName,
                             email, displayEmail, timeCreated, timeAccessed,
                             active, blurb 
                       FROM Users WHERE username=?""", username)
        d = dict(self._getOne(cu, errors.UserNotFound, username))
        return models.User(**d)

    def listMembershipsForUser(self, username):
        self.requireUserReadAccess(username)
        cu = self.db.cursor()
        cu.execute('''SELECT hostname, level
                      FROM Users
                      JOIN ProjectUsers USING(userId)
                      JOIN Projects USING(projectId)
                      WHERE username=?''', username)
        memberList = models.MemberList()
        for hostname, level in cu:
            member = models.Membership(hostname=hostname,
                                       username=username,
                                       level=level)
            memberList.members.append(member)
        return memberList

    def listUsers(self):
        self.requireAdmin()
        cu = self.db.cursor()
        cu.execute("""SELECT userId as id, username, fullName,
                             email, displayEmail, timeCreated, timeAccessed,
                             active, blurb FROM Users""")
        userList = models.UserList()
        for d in cu:
            userList.users.append(models.User(**d))
        return userList

    def listUserGroupsForUser(self, username):
        self.requireAdmin()
        cu = self.db.cursor()
        cu.execute('''SELECT userGroup 
                      FROM Users
                      JOIN UserGroupMembers  USING(userId)
                      JOIN UserGroups  USING(userGroupId)
                      WHERE Users.username=?''', username)
        groupList = models.UserGroupMemberList()
        for userGroup, in cu:
            group = models.UserGroupMember(userGroup, username)
        groupList.groups.append(group)
        return groupList

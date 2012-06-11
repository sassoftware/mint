#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint import userlevels
from mint.rest import errors
from mint.rest.db import manager

class AuthenticationManager(manager.Manager):
    def __init__(self, cfg, db):
        manager.Manager.__init__(self, cfg, db, None)
        self.auth = None
        self.authToken = None
        self.username = None
        self.fullName = None
        self.userId = None
        self.isAdmin = False

    def setAuth(self, auth, authToken):
        self.auth = auth
        self.authToken = authToken
        self.username = auth.username
        self.fullName = auth.fullName
        self.userId = auth.userId
        self.isAdmin = auth.admin

    def requireLogin(self):
        if self.userId < 0:
            raise errors.PermissionDeniedError

    def requireProductReadAccess(self, hostname):
        if self.isAdmin:
            return
        cu = self.db.cursor()
        cu.execute('''SELECT hidden,level from Projects
                      LEFT JOIN ProjectUsers ON (userId=? 
                              AND ProjectUsers.projectId=Projects.projectId)
                      WHERE hostname=?''', self.userId, hostname)
        hidden, level = self.db._getOne(cu, errors.ProductNotFound, hostname)
        if hidden and level is None:
            raise errors.ProductNotFound(hostname)

    def requireProductDeveloper(self, hostname):
        if self.isAdmin:
            return
        cu = self.db.cursor()
        cu.execute('''SELECT hidden,level from Projects
                      LEFT JOIN ProjectUsers ON (userId=? 
                              AND ProjectUsers.projectId=Projects.projectId)
                      WHERE hostname=?''', self.userId, 
                      hostname)
        hidden, level = self.db._getOne(cu, errors.ProductNotFound, hostname)
        if hidden and level is None:
            raise errors.ProductNotFound(hostname)
        if level not in userlevels.WRITERS:
            raise errors.PermissionDeniedError(hostname)

    def requireProductOwner(self, hostname):
        if self.isAdmin:
            return
        cu = self.db.cursor()
        cu.execute('''SELECT hidden,level from Projects
                      LEFT JOIN ProjectUsers ON (userId=? 
                              AND ProjectUsers.projectId=Projects.projectId)
                      WHERE hostname=?''', self.userId, 
                      hostname)
        hidden, level = self.db._getOne(cu, errors.ProductNotFound, hostname)
        if hidden and level is None:
            raise errors.ProductNotFound(hostname)
        if level != userlevels.OWNER:
            raise errors.PermissionDeniedError(hostname)

    def requireUserReadAccess(self, username):
        if self.hasUserReadAccess(username):
            return
        raise errors.PermissionDeniedError()

    def hasUserReadAccess(self, username):
        return (self.isAdmin or self.username == username)

    def requireUserAdmin(self, username):
        if self.isAdmin or self.username == username:
            return
        raise errors.PermissionDeniedError()

    def requireProductCreationRights(self):
        pass

    def requireAdmin(self):
        if not self.isAdmin:
            raise errors.PermissionDeniedError()

    def requireBuildsOnHost(self, hostname, buildIds):
        cu = self.db.cursor()
        for buildId in buildIds:
            cu.execute('''
                SELECT * FROM Builds 
                JOIN Projects USING(projectId)
                WHERE hostname=? AND buildId=?''', hostname, buildId)
            if not cu.fetchall():
                raise errors.BuildNotFound(buildId)

    def requireReleaseOnHost(self, hostname, releaseId):
        cu = self.db.cursor()
        cu.execute('''SELECT hostname FROM PublishedReleases
                      JOIN Projects USING(projectId)
                      WHERE pubReleaseId=?''', releaseId)
        releaseHost, = self.db._getOne(cu, errors.ReleaseNotFound, releaseId)
        if hostname != releaseHost:
            raise errors.ReleaseNotFound(releaseId)

    def requireImageToken(self, hostname, imageId, token):
        cu = self.db.cursor()
        cu.execute("""
            SELECT buildId FROM BuildData bd
                JOIN Builds b USING ( buildId )
                JOIN Projects p USING ( projectId )
            WHERE p.hostname = ? AND b.buildId = ?
                AND bd.name = 'outputToken' AND bd.value = ?""",
                hostname, imageId, token)
        self.db._getOne(cu, errors.BuildNotFound, imageId)

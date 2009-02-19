#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#
from mint.lib import database

class MembershipRequestTable(database.DatabaseTable):
    name = "MembershipRequests"
    fields = ['projectId', 'userId', 'comments']

    def setComments(self, projectId, userId, comments):
        cu = self.db.cursor()

        cu.execute("DELETE FROM MembershipRequests WHERE projectId=? AND userId=?",
            projectId, userId)
        cu.execute("INSERT INTO MembershipRequests VALUES(?,?,?)",
           projectId, userId, comments)
        self.db.commit()

    def userAccountCanceled(self, userId):
        cu = self.db.cursor()
        cu.execute("DELETE from MembershipRequests where userId=?", userId)
        self.db.commit()

    def deleteRequest(self, projectId, userId, commit=True):
        cu = self.db.cursor()
        cu.execute("DELETE from MembershipRequests where projectId=? and userId=?", projectId, userId)
        if commit:
            self.db.commit()
            
    def deleteRequestsByProject(self, projectId, commit=True):
        cu = self.db.cursor()
        cu.execute("DELETE from MembershipRequests where projectId=?", projectId)
        if commit:
            self.db.commit()

    def listRequests(self, projectId):
        cu = self.db.cursor()
        cu.execute("SELECT userId FROM MembershipRequests WHERE projectId=?", projectId)
        return [ x[0] for x in cu.fetchall() ]

    def userHasRequested(self, projectId, userId):
        return userId in self.listRequests(projectId)

    def getComments(self, projectId, userId):
        db = self.db
        cu = db.cursor()
        cu.execute("SELECT comments FROM MembershipRequests WHERE projectId=? AND userId=?", projectId, userId)
        r = cu.fetchone()
        if r:
            return r[0]
        else:
            return ''

    def getProjectIdsWithRequests(self):
        cu = self.db.cursor()
        cu.execute("SELECT UNIQUE(projectId) FROM MembershipRequests")
        return [ x[0] for x in cu.fetchall() ]

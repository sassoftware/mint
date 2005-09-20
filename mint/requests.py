import database
import sqlite3

class MembershipRequestTable(database.DatabaseTable):
    name = "MembershipRequests"
    
    createSQL = """
        CREATE TABLE MembershipRequests(
                                        projectId INTEGER,
                                        userId INTEGER,
                                        comments TEXT,
                                        PRIMARY KEY(projectId, userId)
                                        );
    """
    
    fields = ['projectId', 'userId', 'comments']

    def setComments(self, projectId, userId, comments):
        cu = self.db.cursor()
        try:
            cu.execute("INSERT INTO MembershipRequests VALUES(?,?,?)",
                       projectId, userId, comments)
        except sqlite3.ProgrammingError, e:
            if e.args[0].startswith("column") and \
                   e.args[0].endswith("not unique"):
                cu.execute("""
                    UPDATE MembershipRequests SET comments=?
                    WHERE projectId=? AND userId=?
                    """, comments, projectId, userId)
            else:
                # exception wasn't a duplicate item error...
                raise
        self.db.commit()

    def userAccountCanceled(self, userId):
        cu = self.db.cursor()
        cu.execute("DELETE from MembershipRequests where userId=?", userId)
        self.db.commit()

    def deleteRequest(self, projectId, userId):
        cu = self.db.cursor()
        cu.execute("DELETE from MembershipRequests where projectId=? and userId=?", projectId, userId)
        self.db.commit()

    def listRequests(self, projectId):
        cu = self.db.cursor()
        cu.execute("SELECT userId FROM MembershipRequests WHERE projectId=?", projectId)
        return [ x[0] for x in cu ]

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
            #raise database.ItemNotFound('comment')

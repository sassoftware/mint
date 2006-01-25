#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import database

# reserve special code zero to more more compliant with db engines
(ACTION_VIEW_PROJECT, ACTION_GROUP_BUILDER, ACTION_ISO_GEN, \
 ACTION_PROJECT_READ, ACTION_PROJECT_WRITE, ACTION_GRANT) = range(1, 7)

(OBJ_TYPE_SITE, OBJ_TYPE_PROJECT, OBJ_TYPE_REPORT) = range(1, 4)

LEGAL_OBJECTS = range(1, 4)

class PermissionsTable(database.DatabaseTable):
    name = "Permissions"

    createSQL = """CREATE TABLE Permissions (
                groupId    INTEGER,
                action    INTEGER,
                objectId  INTEGER,
                PRIMARY KEY(groupId, action, objectId))"""

    fields = ['groupId', 'action', 'objectId']

    def getActionAllowed(self, userId, action, objectId):
        cu = self.db.cursor()
        siteId = None

        cu.execute("SELECT objectId FROM Objects WHERE objectType=?",
                   OBJ_TYPE_SITE)
        res = cu.fetchall()
        if res:
            siteId = res[0][0]

        # now loop trough the actual given objects
        cu.execute("SELECT userGroupId FROM UserGroupMembers WHERE userId=?",
                   userId)
        groups = [x[0] for x in cu.fetchall()]

        for groupId in groups:
            cu.execute("""SELECT COUNT(*) FROM Permissions
                              WHERE groupId=? AND action=? AND objectId=?""",
                       groupId, action, objectId)
            if cu.fetchone()[0]:
                return True
            if siteId:
                cu.execute("""SELECT COUNT(*) FROM Permissions
                                  WHERE groupId=? AND action=?
                                      AND objectId=?""",
                           groupId, action, siteId)
                if cu.fetchone()[0]:
                    return True
        return False

    def grant(self, groupId, action, objectId):
        # no permission checks at this level. do it in mint_server.
        cu = self.db.cursor()
        try:
            cu.execute("INSERT INTO Permissions VALUES(?, ?, ?)", groupId,
                       action, objectId)
        except:
            self.db.rollback()
            pass
        else:
            self.db.commit()

    def revoke(self, groupId, action, objectId):
        # no permission checks at this level. do it in mint_server.
        cu = self.db.cursor()
        cu.execute("""DELETE FROM Permissions
                          WHERE groupId=? AND action=? AND objectId=?""",
                   groupId, action, objectId)
        self.db.commit()

# object is horribly vaugue, but remember there's no way of knowing what the
# permission is actually for. eg projects, reports, walking on the grass...
class ObjectsTable(database.KeyedTable):
    name = "Objects"
    key = "objectId"

    createSQL = """CREATE TABLE Objects (
                objectId    %(PRIMARYKEY),
                objectType  INTEGER,
                object      INTEGER)"""

    # fixme. make (objectType, object) unique if possible. that's not to say
    # that object or objectType must be unique separately. it only matters
    # that a given pair be unique...

    fields = ['objectId', 'objectType', 'object']

    def getObjectId(self, id, type):
        """general interface to get an objectId.
        id is generally a primary key to another keyed table.
        type is from an enumerated list of the different kinds of objects that
        can have ACLs.
        return value: objectId from this table
        example: objects.getObjectId(projectId, OBJ_TYPE_PROJECT)
        """
        cu = self.db.cursor()
        if type not in LEGAL_OBJECTS:
            raise database.ItemNotFound
        #FIXME: we need to inherit from the site object...
        if type == OBJ_TYPE_PROJECT:
            cu.execute("""SELECT objectId FROM Objects
                              LEFT JOIN Projects ON
                                  Objects.object=Projects.projectId
                              WHERE projectId=? AND objectType=?""", id, type)
        elif type == OBJ_TYPE_SITE:
            cu.execute("SELECT objectId FROM Objects WHERE objectType=?",
                       OBJ_TYPE_SITE)
        # other table selects go here. They should return a single objectId.

        res = [x[0] for x in cu.fetchall()]
        if len(res) != 1:
            raise database.ItemNotFound
        return res[0]

    def createObject(self, id, type):
        cu = self.db.cursor()
        if type == OBJ_TYPE_SITE:
            cu.execute("""SELECT COUNT(*) FROM Objects
                              WHERE objectType=?""", type)
        else:
            cu.execute("""SELECT COUNT(*) FROM Objects
                              WHERE objectType=? AND object=?""", type, id)
        if cu.fetchone()[0]:
            # FIXME raise a real exception
            raise AssertionError("There can be only one...")
        try:
            cu.execute("""INSERT INTO Objects (object, objectType)
                              VALUES(?, ?)""",
                       id, type)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()

# double check that we actually need this
class MintObject(database.TableObject):
    __slots__ = [ ObjectsTable.key ] + ObjectsTable.fields

    def getItem(self, id):
        return self.server.getMintObject(id)

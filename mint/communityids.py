from mint import database

class CommunityIdsTable(database.DatabaseTable):

    name = "CommunityIds"
    fields = [ 'projectId', 'communityType', 'communityId' ]

    def getCommunityId(self, projectId, communityType):
        cu = self.db.cursor()
        cu.execute("""SELECT communityId FROM CommunityIds WHERE 
                      projectId=? AND communityType=?""", projectId,
                      communityType)
        id = cu.fetchone()
        if id:
            return id[0]
        else:
            return False

    def setCommunityId(self, projectId, communityType, communityId):
        cu = self.db.cursor()
        cu.execute("""SELECT communityId FROM CommunityIds WHERE 
                      projectId=? AND communityType=?""", projectId,
                      communityType)
        if cu.fetchone():
            try:
                cu.execute("""UPDATE communityIds SET communityId=? WHERE
                              projectId=? AND communityType=?""", communityId,
                              projectId, communityType)
                self.db.commit()
            except:
                self.db.rollback()
                raise
        else:
            try:
                cu.execute("""INSERT INTO CommunityIds VALUES (?, ?, ?)""",
                           projectId, communityType, communityId)
                self.db.commit()
            except:
                self.db.rollback()
                raise
        return True

    def deleteCommunityId(self, projectId, communityType):
        cu = self.db.cursor()
        try:
            cu.execute("""DELETE FROM CommunityIds WHERE projectId=? AND
                          communityType=?""", projectId, communityType)
            self.db.commit()
        except:
            self.db.rollback()
            raise
        return True

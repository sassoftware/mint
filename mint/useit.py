#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

from mint import database

class UseItTable(database.KeyedTable):
    name = 'UseIt'
    key = 'itemId'
    createSQL = """CREATE TABLE UseIt (
                    itemId          %(PRIMARYKEY)s,
                    name            CHAR(255),
                    link            CHAR(255)
                );
                """
    fields = ['itemId', 'name', 'link'] 

    def __init__(self, db, cfg):
        database.DatabaseTable.__init__(self, db)
        self.cfg = cfg

    def addIcon(self, itemId, name, link):
        cu = self.db.cursor()
        cu.execute("DELETE FROM %s WHERE itemId=?" % self.name, itemId)
        cu.execute("INSERT INTO %s VALUES (?, ?, ?)" % \
                    self.name, itemId, name, link)
        self.db.commit()
        return True

    def getIcons(self):
        cu = self.db.cursor()
        cu.execute("SELECT * FROM %s ORDER BY itemId" % self.name)
        return cu.fetchall_dict() or False

    def deleteIcon(self, itemId):
        cu = self.db.cursor()
        cu.execute("DELETE FROM %s WHERE itemId=?" % self.name, itemId)
        self.db.commit()
        return True

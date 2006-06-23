#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

from mint import database

class FrontPageSelectionsTable(database.KeyedTable):
    name = 'FrontPageSelections'
    key = 'itemId'
    createSQL = """CREATE TABLE FrontPageSelections (
                    itemId          %(PRIMARYKEY)s,
                    name            CHAR(255),
                    link            CHAR(255),
                    rank            INT
                );
                """
    fields = ['itemId', 'name', 'link', 'rank' ] 

    def __init__(self, db, cfg):
        database.DatabaseTable.__init__(self, db)
        self.cfg = cfg

    def addItem(self, name, link, rank):
        cu = self.db.cursor()
        cu.execute("INSERT INTO %s VALUES (NULL, ?, ?, ?)" % \
                    self.name, name, link, rank)
        self.db.commit()
        return True

    def getAll(self):
        cu = self.db.cursor()
        cu.execute("SELECT * FROM %s ORDER BY rank" % self.name)
        return cu.fetchall_dict()

    def deleteItem(self, itemId):
        cu = self.db.cursor()
        cu.execute("DELETE FROM %s WHERE itemId=?" % self.name, itemId)
        self.db.commit()

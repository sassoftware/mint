#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

import time
from mint import database

class ApplianceSpotlightTable(database.KeyedTable):
    name = 'ApplianceSpotlight'
    key = 'itemId'

    fields = ['itemId', 'title', 'text', 'link', 'logo', 'showArchive', 
              'startDate', 'endDate']

    def __init__(self, db, cfg):
        database.DatabaseTable.__init__(self, db)
        self.cfg = cfg

    def addItem(self, title, text, link, logo, showArchive, startDate, endDate):
        cu = self.db.cursor()

        startDateSec = time.mktime(time.strptime(startDate, "%m/%d/%Y"))
        endDateSec = time.mktime(time.strptime(endDate, "%m/%d/%Y"))
        if (endDateSec <= startDateSec):
            return False

        # Check to see if the end date is later than the start date
        # Be sure dates are not already scheduled
        cu.execute("""SELECT COUNT(*) FROM %s WHERE startDate<=? AND endDate>?
                      OR startDate<? AND endDate>=?""" % self.name,
                      startDateSec, startDateSec, endDateSec, endDateSec)
        if cu.fetchone()[0]:
            return False

        cu.execute("INSERT INTO %s VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)" % \
                    self.name, title, text, link, logo, showArchive,
                    startDateSec, endDateSec)

        self.db.commit()

        return True

    def getAll(self):
        cu = self.db.cursor()
        cu.execute("SELECT * FROM %s ORDER BY startDate DESC" % self.name)
        return cu.fetchall_dict() or False

    def getCurrent(self):
        cu = self.db.cursor()
        date = time.time()
        cu.execute("SELECT * FROM %s WHERE startDate<=? AND endDate>?" % \
                   self.name, date, date)
        return cu.fetchone_dict() or False

    def deleteItem(self, itemId):
        cu = self.db.cursor()
        cu.execute("DELETE FROM %s WHERE itemId=?" % self.name, itemId)
        self.db.commit()
        return True

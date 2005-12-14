#
# Copyright (c) 2005 rPath Inc.
# All rights reserved
#

import database
import time

class VersionTable(database.KeyedTable):
    name = "DatabaseVersion"
    createSQL = """
                CREATE TABLE DatabaseVersion (
                    version INTEGER PRIMARY KEY,
                    timestamp REAL
                )"""
    createSQL_mysql = """
        CREATE TABLE DatabaseVersion (
            version INT PRIMARY KEY,
            timestamp INT
            )"""
    fields = ['version']
    indexes = {'DatabaseVersionIdx': 'CREATE INDEX DatabaseVersionIdx ON DatabaseVersion(version)'}

    def versionCheck(self):
        """ This dummy versionCheck allows __init__ to pass so that the
        DatabaseVersion table gets created.  Otherwise, the upgrade method
        would never create the DatabaseVersion table.
        """
        return True

    def bumpVersion(self):
        version = self.getDBVersion()

        if version != self.schemaVersion:
            cu = self.db.cursor()
            cu.execute("""INSERT into DatabaseVersion (version, timestamp)
                              VALUES(?, ?)""", version + 1, time.time())
            return self.getDBVersion() == self.schemaVersion
        else:
            return True

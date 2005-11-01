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

    def fixVersion(self):
        cu = self.db.cursor()
        version = self.getDBVersion()
        if version != self.schemaVersion:
            #Push the version so that we won't try updating in the future
            cu.execute("INSERT into DatabaseVersion (version, timestamp) VALUES(?, ?)", self.schemaVersion, time.time())
            return self.getDBVersion() == self.schemaVersion
        else:
            return True

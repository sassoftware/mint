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

    fields = ['version']
    indexes = {'DatabaseVersionIdx': 'CREATE INDEX DatabaseVersionIdx ON DatabaseVersion(version)'}

    def versionCheck(self):
        cu = self.db.cursor()
        version = self.getDBVersion()
        if version != self.schemaVersion:
            #Push the version so that we won't try updating in the future
            cu.execute("INSERT into DatabaseVersion (version, timestamp) VALUES(?, ?)", self.schemaVersion, time.time())
            return self.getDBVersion() == self.schemaVersion
        else:
            return True

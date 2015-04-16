#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

from mint.lib import database

termMap = {
    'branch': 'branchName',
    'server': 'serverName',
}


class PackageIndexTable(database.KeyedTable):
    name = 'PackageIndex'
    key = 'pkgId'

    fields = ['pkgId', 'projectId', 'name', 'version']

    def deleteByProject(self, projectId):
        cu = self.db.cursor()
        cu.execute("DELETE FROM PackageIndex WHERE projectId=?", projectId)
        self.db.commit()


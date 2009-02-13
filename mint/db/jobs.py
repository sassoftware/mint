#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#
from mint.lib import database
from mint.mint_error import *

class BuildFilesTable(database.KeyedTable):
    name = 'BuildFiles'
    key = 'fileId'
    fields = ['fileId', 'buildId', 'idx', 'title', 'size', 'sha1' ]

class BuildFilesUrlsMapTable(database.KeyedTable):
    name = 'BuildFilesUrlsMap'
    key = 'fileId'
    fields = ['fileId', 'urlId']
    
    def delete(self, fileId, urlId):
        cu = self.db.cursor()
        cu.execute("DELETE FROM BuildFilesUrlsMap WHERE fileId = ? AND urlId = ?", fileId, urlId)
        self.db.commit()

class FilesUrlsTable(database.KeyedTable):
    name = 'FilesUrls'
    key = 'urlId'
    fields = ['urlId', 'urlType', 'url']

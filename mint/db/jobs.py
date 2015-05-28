#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from mint.lib import data
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

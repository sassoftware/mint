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


import logging
from mint.lib import database

dbReader = database.dbReader
dbWriter = database.dbWriter

log = logging.getLogger(__name__)


class PlatformsTable(database.KeyedTable):
    name = 'platforms'
    key = 'platformId'
    fields = [ 'platformId',
               'label',
               'mode',
               'enabled',
               'projectId',
               'platformName',
               'abstract',
               'configurable',
               'hidden',
               'upstream_url',
               ]

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.KeyedTable.__init__(self, db)

    @dbReader
    def getAll(self, cu):
        sql = """
            SELECT
                platforms.platformId,
                platforms.platformName,
                platforms.label,
                platforms.enabled,
                platforms.abstract,
                platforms.configurable,
                platforms.mode,
                platforms.hidden,
                platforms.upstream_url
            FROM
                platforms
            ORDER BY
                platforms.platformId
        """

        cu.execute(sql)
        return cu.fetchall()

    @dbReader
    def getAllByType(self, cu, type):
        return []

    @dbWriter
    def update(self, cu, platformId, **kw):
        sql = """
            UPDATE platforms
            SET %s = ?
            WHERE platformId = ?
        """
        platformId = int(platformId)
        for k, v in kw.items():
            cu.execute(sql % k, v, platformId)
        return []

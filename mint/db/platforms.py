#
# Copyright (c) rPath, Inc.
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

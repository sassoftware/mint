#
# Copyright (c) 2009 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.opensource.org/licenses/cpl.php.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

from mint.lib import data
from mint.lib import database

dbReader = database.dbReader
dbWriter = database.dbWriter

class ContentSourceTypesTable(database.KeyedTable):
    name = 'contentSourceTypes'
    key = 'contentSourceTypeId'
    fields = [ 'contentSourceTypeId',
               'name' ]

    def getByName(self, name):
        return self.getIdByColumn('name', name)

    @dbReader
    def getAll(self, cu):
        sql = """
            SELECT 
                contentSourceTypeId,
                name
            FROM
                contentSourceTypes
        """
        cu.execute(sql)
        return cu.fetchall()


class PlatformsContentSourceTypesTable(database.DatabaseTable):
    name = 'platformsContentSourceTypes'
    fields = [ 'platformId',
               'contentSourceTypeId' ]

    @dbReader
    def getAllByPlatformId(self, cu, platformId):
        sql = """
            SELECT platformId, contentSourceTypeId
            FROM platformsContentSourceTypes
            WHERE platformId = ?
        """
        cu.execute(sql, platformId)

        return cu.fetchall()

class PlatformsTable(database.KeyedTable):
    name = 'platforms'
    key = 'platformId'
    fields = [ 'platformId',
               'label',
               'mode',
               'enabled' ]

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.KeyedTable.__init__(self, db)

    @dbReader
    def getAll(self, cu):
        sql = """
            SELECT
                platforms.platformId,
                platforms.label,
                platforms.enabled,
                platforms.mode
            FROM
                platforms
            ORDER BY
                platforms.platformId
        """

        cu.execute(sql)
        return cu.fetchall()

    @dbReader
    def getAllByType(self, cu, type):
        sql = """\
            SELECT 
                platforms.platformId
            FROM 
                platforms,
                platformsContentSourceTypes,
                contentSourceTypes
            WHERE
                platforms.platformId = platformsContentSourceTypes.platformId
            AND platformsContentSourceTypes.contentSourceTypeId =
                contentSourceTypes.contentSourceTypeId
            AND contentSourceTypes.name = ?
        """
        cu.execute(sql, type)
        ret = cu.fetchall()
        return ret

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

class PlatformLoadJobsTable(database.KeyedTable):
    name = 'platformLoadJobs'
    key = 'jobId'
    fields = [ 'jobId',
               'platformId',
               'message',
               'done' ]

class PlatformSourcesTable(database.KeyedTable):
    name = 'platformSources'
    key = 'platformSourceId'
    fields = [ 'platformSourceId', 
               'name',
               'shortName',
               'defaultSource',
               'orderIndex',
               'type' ]

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.KeyedTable.__init__(self, db)

    def getIdFromShortName(self, shortName):
        return self.getIdByColumn('shortName', shortName)

    @dbReader
    def getAll(self, cu):
        sql = """\
            SELECT
                platformSources.platformSourceId,
                platformSources.name,
                platformSources.shortName,
                platformSources.defaultSource,
                platformSources.orderIndex,
                contentSourceTypes.name AS contentSourceType
            FROM
                contentSourceTypes,
                platformSources
            WHERE
                platformSources.contentSourceTypeId =
                contentSourceTypes.contentSourceTypeId
        """
        cu.execute(sql)
        return cu.fetchall()

    @dbReader
    def getByPlatformId(self, cu, platformId):
        sql = """\
            SELECT
                platformSources.platformSourceId,
                platformSources.name,
                platformSources.shortName,
                platformSources.defaultSource,
                platformSources.orderIndex,
                contentSourceTypes.name AS contentSourceType
            FROM
                contentSourceTypes,
                platformsPlatformSources,
                platformSources
            WHERE
                platformSources.contentSourceTypeId =
                contentSourceTypes.contentSourceTypeId
            AND
                platformsPlatformSources.platformId = ?
            AND
                platformsPlatformSources.platformSourceId =
                platformSources.platformSourceId
        """
        cu.execute(sql, platformId)
        return cu.fetchall()

class PlatformSourceDataTable(data.GenericDataTable):
    name = 'platformSourceData'

class PlatformsPlatformSourcesTable(database.DatabaseTable):    
    name = 'platformsPlatformSources'
    fields = [ 'platformId',
               'platformSourceId' ]

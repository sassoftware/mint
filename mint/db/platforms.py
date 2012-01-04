#
# Copyright (c) 2011 rPath, Inc.
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

import logging
from mint.lib import data
from mint.lib import database
from mint import mint_error

dbReader = database.dbReader
dbWriter = database.dbWriter

log = logging.getLogger(__name__)


class PlatformsContentSourceTypesTable(database.DatabaseTable):
    name = 'platformsContentSourceTypes'
    fields = [ 'platformId',
               'contentSourceType' ]

    @dbReader
    def getAllByPlatformId(self, cu, platformId):
        sql = """
            SELECT platformId, contentSourceType
            FROM platformsContentSourceTypes
            WHERE platformId = ?
        """
        cu.execute(sql, platformId)

        return cu.fetchall()

    @dbWriter
    def delete(self, cu, platformId, contentSourceType):
        log.info("Deleting content source type %s from platform %s",
                contentSourceType, platformId)
        sql = """
            DELETE
              FROM platformsContentSourceTypes
             WHERE platformId = ?
               AND contentSourceType = ?
        """
        cu.execute(sql, platformId, contentSourceType)

    @dbWriter
    def sync(self, cu, platformId, contentSourceTypes):
        if contentSourceTypes is None:
            return
        oldCST = set(x['contentSourceType'] for x in self.getAllByPlatformId(platformId))
        toAdd = set(contentSourceTypes).difference(oldCST)
        toDelete = oldCST.difference(contentSourceTypes)
        for contentSourceType in toAdd:
            try:
                self.new(
                    platformId=platformId, contentSourceType=contentSourceType)
                log.info("Added content source type %s to platform %s",
                        contentSourceType, platformId)
            except mint_error.DuplicateItem:
                # No need to raise this, the data is already created.
                pass
        for contentSourceType in toDelete:
            self.delete(platformId, contentSourceType)

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
                platforms.hidden
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
                platformsContentSourceTypes
            WHERE
                platforms.platformId = platformsContentSourceTypes.platformId
            AND platformsContentSourceTypes.contentSourceType = ?
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
                platformSources.contentSourceType
            FROM
                platformSources
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
                platformSources.contentSourceType
            FROM
                platformsPlatformSources,
                platformSources
            WHERE
                platformsPlatformSources.platformId = ?
            AND
                platformsPlatformSources.platformSourceId =
                platformSources.platformSourceId
            ORDER BY platformSources.orderIndex
        """
        cu.execute(sql, platformId)
        return cu.fetchall()

class PlatformSourceDataTable(data.GenericDataTable):
    name = 'platformSourceData'

class PlatformsPlatformSourcesTable(database.DatabaseTable):    
    name = 'platformsPlatformSources'
    fields = [ 'platformId',
               'platformSourceId' ]

    @dbReader
    def getAllByPlatformId(self, cu, platformId):
        platformId = int(platformId)
        sql = """
            SELECT platformId, platformSourceId
            FROM platformsPlatformSources
            WHERE platformId = ?
        """
        cu.execute(sql, platformId)

        return cu.fetchall()

    @dbWriter
    def sync(self, cu, platformId, platformSourceIds):
        platformId = int(platformId)
        newIds = set(int(x) for x in platformSourceIds)
        oldIds = set(x['platformSourceId']
            for x in self.getAllByPlatformId(platformId))
        for platformSourceId in newIds.difference(oldIds):
            log.info("Adding platform source %s to platform %s",
                    platformSourceId, platformId)
            self.new(platformId=platformId,
                platformSourceId=platformSourceId)
        # XXX is removal necessary?

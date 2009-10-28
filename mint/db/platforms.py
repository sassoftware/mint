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

class ContentSourceTypesTable(database.KeyedTable):
    name = 'contentSourceTypes'
    key = 'contentSourceTypeId'
    fields = [ 'contentSourceTypeId',
               'name' ]

    def getByName(self, name):
        return self.getIdByColumn('name', name)

class PlatformsContentSourceTypesTable(database.DatabaseTable):
    name = 'platformsContentSourceTypes'
    fields = [ 'platformId',
               'contentSourceTypeId' ]

class PlatformsTable(database.KeyedTable):
    name = 'platforms'
    key = 'platformId'
    fields = [ 'platformId',
               'label',
               'configurable',
               'mode' ]

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.KeyedTable.__init__(self, db)

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

class PlatformSourceDataTable(data.GenericDataTable):
    name = 'platformSourceData'

class PlatformsPlatformSourcesTable(database.DatabaseTable):    
    name = 'platformsPlatformSources'
    fields = [ 'platformId',
               'platformSourceId' ]

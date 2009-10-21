from mint.lib import data
from mint.lib import database

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

class PlatformSourcesTable(database.KeyedTable):
    name = 'platformSources'
    key = 'platformSourceId'
    fields = [ 'platformSourceId', 
               'platformId',
               'name',
               'shortName',
               'defaultSource',
               'orderIndex' ]

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.KeyedTable.__init__(self, db)

    def getIdFromShortName(self, shortName):
        return self.getIdByColumn('shortName', shortName)

class PlatformSourceDataTable(data.GenericDataTable):
    name = 'platformSourceData'

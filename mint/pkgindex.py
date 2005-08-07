#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import database
import searcher

class PackageIndexTable(database.KeyedTable):
    name = 'PackageIndex'
    key = 'pkgId'

    createSQL = """
        CREATE TABLE PackageIndex (
            pkgId       INTEGER PRIMARY KEY,
            projectId   INT,
            name        STR,
            version     STR
        )"""

    fields = ['pkgId', 'name', 'version']

    indexes = {"PackageNameIdx": "CREATE INDEX PackageNameIdx ON PackageIndex(name)"}

    def search(self, terms, limit, offset):
        columns = ['name', 'version', 'projectId']
        searchcols = ['name']

        ids, count = database.KeyedTable.search(self, columns, 'PackageIndex',
            searcher.Searcher.where(terms, searchcols), 'name', None, limit, offset)

        for i, x in enumerate(ids[:]):
            ids[i] = list(x)
            
        return ids, count

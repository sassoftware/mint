#
# Copyright (c) 2005-2006 rPath, Inc.
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
            pkgId       %(PRIMARYKEY)s,
            projectId   INT,
            name        CHAR(255),
            version     CHAR(255)
        )"""

    fields = ['pkgId', 'projectId', 'name', 'version']

    indexes = {"PackageNameIdx": """CREATE INDEX PackageNameIdx
                                        ON PackageIndex(name)""",
               "PackageIndexProjectIdx": """CREATE INDEX PackageIndexProjectIdx
                                                ON PackageIndex(projectId)"""}

    def search(self, terms, limit, offset):
        columns = ['name', 'version', 'projectId']
        searchcols = ['name']

        ids, count = database.KeyedTable.search(self, columns, 'PackageIndex',
            searcher.Searcher.where(terms, searchcols), 'name', None, limit, offset)

        for i, x in enumerate(ids[:]):
            ids[i] = list(x)
            
        return ids, count

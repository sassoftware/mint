#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

from mint import database
from mint import searcher


termMap = {
    'branch': 'branchName',
    'server': 'serverName',
}


class PackageIndexTable(database.KeyedTable):
    name = 'PackageIndex'
    key = 'pkgId'

    fields = ['pkgId', 'projectId', 'name', 'version']

    def search(self, terms, limit, offset):
        columns = ['name', 'version', 'projectId']
        searchcols = ['name']

        terms, limiters = searcher.parseTerms(terms)
        extras, extraSubs = searcher.limitersToSQL(limiters, termMap)

        # with any kind of branch/server limiters, assume we want
        # to filter out sources too.
        if limiters:
            extras += " AND isSource=0"

        terms = " ".join(terms)

        ids, count = database.KeyedTable.search(self, columns, 'PackageIndex',
            searcher.Searcher.where(terms, searchcols, extras, extraSubs),
            searcher.Searcher.order(terms, searchcols, 'name'),
            None, limit, offset)

        for i, x in enumerate(ids[:]):
            ids[i] = list(x)

        return ids, count


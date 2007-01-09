#
# Copyright (c) 2007 rPath, Inc.
#
# All Rights Reserved
#

# short names for some SQL columns
termMap = {
    'branch': 'branchName',
    'server': 'serverName',
}


def parseTerms(self, termsStr):
    # split and strip
    terms = [x.strip() for x in termsStr.split(" ")]

    # limiters are terms that look like: limiter=key, eg, branch=rpl:1
    limiters = [x for x in terms if '=' in x]
    terms = [x for x in terms if '=' not in x]

    return limiters, terms

def limitersToSQL(self, limiters):
    sql = ""

    for limiter in limiters:
        term, key = limiter.split('=')
        sql += " AND %s='%s'" % (termMap[term], key)

    return sql

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


def parseTerms(termsStr):
    # split and strip
    terms = [x.strip() for x in termsStr.split(" ")]

    # limiters are terms that look like: limiter=key, eg, branch=rpl:1
    limiters = [x for x in terms if '=' in x]
    terms = [x for x in terms if '=' not in x]

    return terms, limiters

def limitersToSQL(limiters):
    sql = ""

    for limiter in limiters:
        term, key = limiter.split('=')
        sql += " AND %s='%s'" % (termMap[term], key)

    return sql

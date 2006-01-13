#!/usr/bin/python

from conary import dbstore
import sys
import os

assert(len(sys.argv) > 2)

dbPath = sys.argv[1]
projects = sys.argv[2:]

assert(os.path.exists(dbPath))

db = dbstore.connect(dbPath, 'sqlite')
cu = db.cursor()

ids = []
idMap = {}

for hostname in projects:
    cu.execute("SELECT projectId FROM Projects WHERE hostname=?", hostname)
    id = cu.fetchone()
    if id:
        ids.append(id[0])
        idMap[id[0]] = hostname

assert len(ids) == len(projects), "not all projects were found"

tables = ('Commits', 'GroupTroves', 'Labels', 'MembershipRequests',
          'PackageIndex', 'ProjectUsers', 'Projects', 'Releases')

for id in ids:
    print "DELETING PROJECT %d (%s)" % (id, idMap[id])
    for table in tables:
        print "deleting from table %s" % table
        cu.execute("DELETE FROM %s WHERE projectId=?" % table, id)

db.commit()
print "done"

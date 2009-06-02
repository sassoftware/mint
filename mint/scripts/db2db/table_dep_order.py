#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

"""
Given a postgres database, print the list of tables in the order in which they
should be loaded to keep foreign keys satisfied.

Use this to produce the tables for tablelist.py.
"""

import sys
from conary import dbstore


def main(args):
    if len(args) != 1:
        sys.exit("Usage: %s <psql db path>" % (sys.argv[0],))
    path = args[0]

    db = dbstore.connect(path, 'postgresql')
    db.loadSchema()
    cu = db.cursor()

    tableDeps = {}
    for table in db.tables:
        if table.lower == 'databaseversion':
            continue
        tableDeps[table] = set()

    for table in db.tables:
        cu.execute("""select b.relname
            from pg_catalog.pg_class a
            join pg_catalog.pg_constraint r on a.oid = r.conrelid
            left join pg_catalog.pg_class b on r.confrelid = b.oid
            where a.relname = ? and r.contype = 'f'""", table)
        tableDeps[table] = set(x[0] for x in cu)

    ordered = []
    while tableDeps:
        for table, deps in tableDeps.items():
            if deps:
                continue
            print table
            ordered.append(table)
            for otherDeps in tableDeps.values():
                otherDeps.discard(table)
            del tableDeps[table]

    print repr(ordered)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

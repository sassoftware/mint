#!/usr/bin/python
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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

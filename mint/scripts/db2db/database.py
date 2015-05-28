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


import logging
import sys

from conary import dbstore
from mint.scripts.db2db.schema import getTables, getIndexes
from mint.scripts.db2db.tablelist import TABLE_LIST

log = logging.getLogger(__name__)


# database loader that knows how to insert rows efficiently
class Loader(object):
    binaryCols = ["salt"]

    def __init__(self, db, table, fields):
        self.db = db
        self.table = table
        self.sql = "INSERT INTO %s (%s) VALUES (%s)" % (
            table, ", ".join(fields), ",".join(["?"]*len(fields)))
        self.cu = self.db.cursor()
        self.fields = fields
        # make sure we know when to use cu.binary()
        self.funcs = [ self.__getfunc(x) for x in fields ]

    def announce(self):
        sys.stdout.write("1by1 load table: %s\r" % (self.table,))
        sys.stdout.flush()

    # fields which we should tag as binary
    def __getfunc(self, field):
        if field.lower() in self.binaryCols:
            return self.cu.binary
        return lambda a: a

    # fix up the values in a row to match the transforms
    def rowvals(self, row):
        return tuple(func(val) for (func, val) in zip(self.funcs, row))

    def insertRows(self, rows, callback=None):
        self.cu.executemany(self.sql, [self.rowvals(row) for row in rows])
        if callback:
            callback.increment(len(rows))
        return len(rows)

    def finish(self):
        return 0, 0


class PgSQLLoader(Loader):
    def __init__(self, db, table, fields):
        Loader.__init__(self, db, table, fields)

        # Rows will be inserted into a temp table first
        self.tmpName = 'tmp_' + table
        cu = db.cursor()
        cu.execute("CREATE TEMPORARY TABLE %s ( LIKE %s )"
                % (self.tmpName, table))

    def insertRows(self, rows, callback=None):
        self.db.dbh.bulkload(self.tmpName, (self.rowvals(row) for row in rows),
                self.fields)
        if callback:
            callback.increment(len(rows))
        return len(rows)

    def finish(self):
        cu = self.db.cursor()

        # Clean up fields that violate foreign keys before inserting them.
        cu.execute("""
            select r.conname, r.confdeltype,
                aa.attname, b.relname, ba.attname
            from pg_catalog.pg_constraint r
                left join pg_catalog.pg_class a on r.conrelid = a.oid
                left join pg_catalog.pg_class b on r.confrelid = b.oid
                join pg_catalog.pg_attribute aa ON (
                    a.oid = aa.attrelid and aa.attnum = any(r.conkey) )
                join pg_catalog.pg_attribute ba ON (
                    b.oid = ba.attrelid and ba.attnum = any(r.confkey) ) 
            where r.contype = 'f' and a.relname = ?""", self.table.lower())
        totalDeleted = totalChanges = 0
        for (constraint, action, ourColumn,
                otherTable, otherColumn) in cu.fetchall():
            scrubbed = 0
            if action in ('r', 'c'):
                # RESTRICT/CASCADE -- delete rows without matches
                scrubbed = cu.execute("""DELETE FROM %s us
                    WHERE %s IS NOT NULL AND NOT EXISTS (
                        SELECT * FROM %s them WHERE us.%s = them.%s )"""
                        % (self.tmpName, ourColumn, otherTable,
                            ourColumn, otherColumn))
                if scrubbed:
                    log.warning("%d rows violating constraint %s "
                            "were deleted", scrubbed, constraint)
                    # These rows are completely gone, so we need to inform the
                    # code that compares row counts how many were deleted.
                    totalDeleted += scrubbed
            elif action == 'n':
                # SET NULL -- set fields without matches to NULL
                scrubbed = cu.execute("""UPDATE %s us SET %s = NULL
                    WHERE %s IS NOT NULL AND NOT EXISTS (
                        SELECT * FROM %s them WHERE us.%s = them.%s )"""
                        % (self.tmpName, ourColumn, ourColumn, otherTable,
                            ourColumn, otherColumn))
                if scrubbed:
                    log.warning("%d fields violating constraint %s "
                            "were set null", scrubbed, constraint)
            else:
                log.warning("Don't know how to fix potential foreign key "
                        "violations of type %r on constraint %s",
                        action, constraint)
            totalChanges += scrubbed

        # Copy temp table into the final table
        cu.execute("INSERT INTO %s SELECT * FROM %s"
                % (self.table, self.tmpName))
        return totalDeleted, totalChanges


class Database(object):
    def __init__(self, driver, db):
        self.db = dbstore.connect(db, driver)
        self.db.transaction()
        self.driver = driver
        self.db.loadSchema()
        self._hint = ''
    def createSchema(self):
        # create the tables, avoid the indexes
        log.info("Creating basic schema")
        cu = self.db.cursor()
        for stmt in getTables(self.driver):
            cu.execute(stmt)
        self.db.loadSchema()
    def createIndexes(self):
        log.info("Creating indices")
        cu = self.db.cursor()
        for stmt in getIndexes(self.driver):
            cu.execute(stmt)
        self.db.loadSchema()
    # check self.db.tables against the TableList
    def checkTablesList(self, isSrc=True):
        #  check that we are migrating all the tables in the source
        self.db.loadSchema()
        skip = ['databaseversion', 'instructionsets', 'commitlock']
        knowns = [x.lower() for x in TABLE_LIST]
        haves = [x.lower() for x in self.db.tables]
        if isSrc:
            which = "Source"
        else:
            which = "Target"
        # tableList should not have items not present in the db
        onlyKnowns = set(knowns).difference(set(haves)).difference(set(skip))
        if onlyKnowns:
            raise RuntimeError("%s schema (%s) does not have table(s) %s" %(
                which, self.driver, onlyKnowns))
        # we should not have extra tables in the source
        onlyHaves = set(haves).difference(set(knowns)).difference(set(skip))
        if onlyHaves and isSrc:
            raise RuntimeError("TABLE_LIST needs to be updated to "
                    "handle tables", onlyHaves)
        return True
    
    # functions for when the instance is a source
    def getCount(self, table):
        cu = self.db.cursor()
        cu.execute("select count(*) from %s" % (table,))
        return cu.fetchall()[0][0]
    def getFields(self, table):
        cu = self.db.cursor()
        cu.execute("SELECT * FROM %s LIMIT 1" % (table,))
        return [x.lower() for x in cu.fields()]
    def getTables(self):
        return [x.lower() for x in self.db.tables]
    def iterRows(self, table, fields):
        cu = self.db.itercursor()
        cu.execute("select %s %s from %s" % (self._hint, ', '.join(fields),
            table))
        return cu
    # functions for when the instance is a target
    def prepareInsert(self, table, fields):
        return Loader(self.db, table, fields)
    def finalize(self, version):
        self.db.setVersion(version)
        self.db.commit()
    # useful shortcut
    def close(self):
        self.db.close()


class MySQLDatabase(Database):
    def __init__(self, db):
        Database.__init__(self, "mysql", db)

    def iterRows(self, table, fields):
        cu = self.db.itercursor()
        cu.execute("select %s %s from %s" % (self._hint,
            ', '.join('`%s`' % (x,) for x in fields), table))
        return cu


class PgSQLDatabase(Database):
    def __init__(self, db):
        Database.__init__(self, "postgresql", db)

    def createIndexes(self):
        Database.createIndexes(self)
        # fix the primary keys
        self.fix_primary_keys()
        # update the primary key sequences for all tables

    def fix_primary_keys(self):
        cu = self.db.cursor()
        # get the name of the primary key
        cu.execute("""
        select
            t.relname as table_name,
            col.attname as column_name
        from pg_class t
        join pg_index i on t.oid = i.indrelid and i.indisprimary = true
        join pg_class ind on i.indexrelid = ind.oid
        join pg_attribute col on col.attrelid = t.oid and col.attnum = i.indkey[0]
        where i.indnatts = 1
          and pg_catalog.pg_table_is_visible(t.oid)
        """)
        for (table, col) in cu.fetchall():
            table = table.lower()
            cu.execute("select pg_catalog.pg_get_serial_sequence(?, ?)",
                    (table, col))
            seqname = cu.fetchone()[0]
            if seqname is None:
                # this primary key does not have a sequence associated with it
                continue
            # get the max seq value
            cu.execute("select max(%s) from %s" % (col, table))
            seqval = cu.fetchone()[0]
            if not seqval:
                seqval = 1
            else:
                seqval += 1 # we need the next one in line
            # now reset the sequence for the primary key
            cu.execute("select pg_catalog.setval(?, ?, false)",
                    (seqname, seqval))
            ret = cu.fetchone()[0]
            assert (ret == seqval)

    # functions for when the instance is a target
    def prepareInsert(self, table, fields):
        return PgSQLLoader(self.db, table, fields)

    def finalize(self, version):
        Database.finalize(self, version)
        cu = self.db.cursor()
        log.info("Vacuuming")
        cu.execute("VACUUM ANALYZE")


def getdb(driver, db):
    if driver == "postgresql":
        return PgSQLDatabase(db)
    elif driver == "mysql":
        return MySQLDatabase(db)
    return Database(driver, db)

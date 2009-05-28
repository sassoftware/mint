#!/usr/bin/python
#
# Copyright (c) 2007-2009 rPath, Inc.
#
# All rights reserved.
#

"""
Migrates a mint DB stored in a backend supported by dbstore to another db
stored in a backend supported by dbstore.
"""

import logging
import math
import sys
import time
import itertools
import optparse

from mint.db.schema import RBUILDER_DB_VERSION
from mint.lib import mintutils
from mint.scripts.db2db import tablelist
from mint.scripts.db2db.database import getdb


log = logging.getLogger(__name__)


class Callback(object):
    def __init__(self, table, count):
        self.table = table
        self.count = count
        self.start = self.lastStatus = time.time()
        self.counter = 0

    def increment(self, counter = 1):
        self.counter += counter
        if time.time() > self.lastStatus + 1:
            self.display(False)
            self.lastStatus = time.time()

    def last(self):
        self.display(True)

    def display(self, final=False):
        tnow = time.time()
        tpassed = tnow - self.start
        if not tpassed:
            tpassed = 0.001
        speed = float(self.counter) / tpassed
        if not speed:
            speed = 0.001
        eta = (self.count - self.counter) / speed
        eta = int(math.ceil(eta))

        if final:
            log.debug("copied %s: %d rows in %.03f s (%.02f rows/s)",
                    self.table, self.counter, tpassed, speed)
        else:
            total = self.count or 1 # avoid divide by zero
            log.debug("copying %s: %d/%d rows (%.01f%%) in %.03f s "
                    "(%.02f rows/s, ETA %d s)", self.table, self.counter,
                    self.count, float(self.counter) / total * 100, tpassed,
                    speed, eta)


def migrate_table(src, dst, table, batch=5000):
    log.info("Migrating table %s", table)
    count = src.getCount(table)
    fields = dst.getFields(table)
    dstCu = dst.prepareInsert(table, fields)
    callback = Callback(table, count)
    rowCounter = 0
    commitCounter = 0
    fields = ','.join(fields)
    srcCu = src.iterRows(table, fields)
    while rowCounter <= count:
        rows = srcCu.fetchmany(batch)
        if len(rows) == 0:
            break
        ret = dstCu.insertRows(rows, callback)

        rowCounter += ret
        commitCounter += ret
        if commitCounter > 10000:
            #dst.commit()
            commitCounter = 0
    callback.last()
    deleted, changes = dstCu.finish()
    #dst.commit()
    dstCount = dst.getCount(table)
    assert (count == dstCount + deleted), ("Source Rows count %d != target "
            "rows count %d + %d for table %s" % (count, dstCount, deleted,
                table))
    return deleted, changes


def store_db(option, opt_str, value, parser):
    if parser.values.db is None:
        parser.values.db = []
    parser.values.db.append((opt_str[2:], value))
    if len(parser.values.db) > 2:
        raise optparse.OptionValueError(
                "Can only specify one source and one target database")


def main(args):
    parser = optparse.OptionParser(
            usage="usage: %prog [options] srcopt=DB dstopt=DB")

    for db in ["sqlite", "mysql", "postgresql"]:
        parser.add_option("--" + db, action = "callback", callback=store_db,
                type="string", dest="db", help="specify a %s database" % db,
                metavar=db.upper())

    parser.add_option("--batch", "-b", action="store", dest="batch",
            metavar="N", type=int, default=5000,
            help="batch size in (row count) for each copy operation")
    parser.add_option("--verbose", "-v", action="store_true", dest="verbose",
            default=False, help="verbose output")

    (options, args) = parser.parse_args(args)
    if options.db is None or len(options.db) != 2:
        parser.print_help()
        sys.exit(-1)

    mintutils.setupLogging(consoleLevel=logging.DEBUG)

    if options.db[1][0] != 'postgresql':
        raise RuntimeError("Only postgresql targets are supported at this time")
    src = getdb(*options.db[0])
    dst = getdb(*options.db[1])
    dst.verbose = options.verbose

    # Sanity checks
    dst.createSchema()
    dst.checkTablesList(isSrc=False)
    if src.db.getVersion() != RBUILDER_DB_VERSION:
        log.error("Source and target schemas have different versions")
        log.error("Source: %s", src.db.getVersion())
        log.error("Target: %s", RBUILDER_DB_VERSION)
        raise RuntimeError("Schemas are different")

    # check that the source and target match schemas
    diff = set(src.getTables()).difference(set(dst.getTables()))
    diff.discard('databaseversion')
    if diff:
        log.warning("Only in Source (%s): %s", src.driver, diff)
    diff = set(dst.getTables()).difference(set(src.getTables()))
    if diff:
        log.warning("Only in Target (%s): %s", src.driver, diff)

    # compare each table's schema between the source and target
    for table in tablelist.TABLE_LIST:
        srcFields = src.getFields(table)
        dstFields = dst.getFields(table)
        if set(dstFields) - set(srcFields):
            raise RuntimeError("""\
            Schema definitions are different between databases:
            Table: %s
            %s: %s
            %s: %s""" % (table, src.driver, srcFields, dst.driver, dstFields))

    # now migrate all tables
    changes = 0
    for table in tablelist.TABLE_LIST:
        deleted_, changes_ = migrate_table(src, dst, table, options.batch)
        changes += changes_
        sys.stdout.flush()

    if changes:
        log.warning("A total of %d modifications were made to meet "
                "foreign key constraints.", changes)

    # create the indexes to close the loop
    dst.createIndexes()
    dst.finalize(RBUILDER_DB_VERSION)

    src.close()
    dst.close()

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

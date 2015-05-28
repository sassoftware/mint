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


import re
from conary.dbstore import sqlerrors
from conary.dbstore.sqllib import CaselessDict
from mint.db import schema

DRIVERS = ["sqlite", "mysql", "postgresql"]


class PrintDatabase(object):
    def __init__(self, showTables=True, driver="sqlite"):
        self.tables = self.views = self.sequences = CaselessDict()
        self.tempTables = CaselessDict()
        self.version = 0
        self.showTables = showTables
        self.statements = []
        self.driver = driver
        if self.driver == "sqlite":
            from conary.dbstore import sqlite_drv as drv
        elif driver =="mysql":
            from conary.dbstore import mysql_drv as drv
        elif driver == "postgresql":
            from conary.dbstore import postgresql_drv as drv
        else:
            raise AttributeError("unknown driver", driver)
        self.keywords = drv.KeywordDict()

    def connect(self, *args, **kwargs):
        pass
    def transaction(self):
        pass
    def commit(self):
        pass
    def rollback(self):
        pass
    def cursor(self):
        return self
    def loadSchema(self):
        pass
    # simulate non-existent tables for delete statements
    @staticmethod
    def _skip_delete(sql):
        delfrom = re.compile("(?i)DELETE\s+FROM.*")
        if delfrom.match(sql):
            raise sqlerrors.DatabaseError
        return False
    # ignore create temporary tables
    def _skip_tempTables(self, sql):
        tmptbl = re.compile(
                "(?i)CREATE\s+TEMPORARY\s+TABLE\s+(?P<table>[^ (]+).*")
        match = tmptbl.match(sql)
        if match is not None:
            groups = match.groupdict()
            # remember this temporary table
            self.tempTables.setdefault(groups["table"].strip(), [])
            return True
        return False
    # ignore indexes for temporary tables
    def _skip_Indexes(self, sql, skipAll=False):
        tmpidx = re.compile("(?i)CREATE\s+(UNIQUE\s+)?INDEX\s+\S+\s+"
                "ON\s+(?P<table>[^ (]+).*")
        match = tmpidx.match(sql)
        if match is not None:
            groups = match.groupdict()
            # remember this temporary table
            if skipAll or groups["table"] in self.tempTables:
                return True
        return False
    @staticmethod
    def _skip_Triggers(sql, skipAll=False):
        tmptrg = re.compile("(?i)CREATE\s+(OR\s+REPLACE\s+)?"
                "((DEFINER.*)?TRIGGER|FUNCTION)")
        if tmptrg.match(sql):
            return skipAll
        return False
    def _skip_Tables(self, sql, skipAll = False):
        tbl = re.compile("^(?i)(CREATE|ALTER)\s+(TABLE\s+(?P<table>[^(]+)"
                "|(\s?DEFINER.*)?(\s?SQL SECURITY.*)?VIEW\s+"
                "(?P<view>[^( ]+))\s*([(]|ADD|AS).*")
        match = tbl.match(sql)
        if match is not None:
            groups = match.groupdict()
            if groups["table"]:
                self.tables.setdefault(groups["table"].strip(), [])
            if groups["view"]:
                self.views.setdefault(groups["view"].strip(), True)
            return skipAll
        return False

    def execute(self, sql, *args, **kwargs):
        sql = sql.strip()
        # skip the parametrized schema definitions
        if (args or kwargs) and "?" in sql:
            return
        if (self._skip_delete(sql)
                or self._skip_tempTables(sql)
                or self._skip_Indexes(sql, self.showTables)
                or self._skip_Triggers(sql, self.showTables)
                or self._skip_Tables(sql, not self.showTables)):
            return
        into = re.compile("^(?i)(INSERT INTO).*")
        # we don't do inserts because they're ot part of te schema definition
        if into.match(sql):
            return
        self.statements.append(sql)

    def createTrigger(self, table, column, onAction, pinned=False):
        onAction = onAction.lower()
        name = "%s_%s" % (table, onAction)
        assert(onAction in ["insert", "update"])
        create = "CREATE TRIGGER"
        if self.driver == "postgresql":
            funcName = "%s_func" % name
            if pinned:
                self.execute("""
                CREATE OR REPLACE FUNCTION %s()
                RETURNS trigger
                AS $$
                BEGIN
                    NEW.%s := OLD.%s ;
                    RETURN NEW;
                END ; $$ LANGUAGE 'plpgsql';
                """ % (funcName, column, column))
            else:
                self.execute("""
                CREATE OR REPLACE FUNCTION %s()
                RETURNS trigger
                AS $$
                BEGIN
                    NEW.%s := TO_NUMBER(TO_CHAR(CURRENT_TIMESTAMP, 'YYYYMMDDHH24MISS'), '99999999999999') ;
                    RETURN NEW;
                END ; $$ LANGUAGE 'plpgsql';
                """ % (funcName, column))
            # now create the trigger based on the above function
            self.execute("""
            CREATE TRIGGER %s
            BEFORE %s ON %s
            FOR EACH ROW
            EXECUTE PROCEDURE %s()
            """ % (name, onAction, table, funcName))
            return
        if self.driver == "sqlite":
            when = "AFTER"
            sql = ("UPDATE %s SET %s = unix_timestamp() "
                   "WHERE _ROWID_ = NEW._ROWID_ ; " %(table, column))
        elif self.driver == "mysql":
            when = "BEFORE"
            # force the current_timestamp into a numeric context
            if pinned:
                sql = "SET NEW.%s = OLD.%s ; " % (column, column)
            else:
                sql = "SET NEW.%s = current_timestamp() + 0 ; " % (column,)
            create = "CREATE DEFINER = 'root'@'localhost' TRIGGER"
        else:
            raise NotImplementedError
        sql = """
        %s %s %s %s ON %s
        FOR EACH ROW BEGIN
        %s
        END
        """ % (create, name, when.upper(), onAction.upper(), table, sql)
        self.execute(sql)
        return True

    def createIndex(self, table, name, columns, unique = False):
        if unique:
            unique = "UNIQUE"
        else:
            unique = ""
        sql = "CREATE %s INDEX %s on %s (%s)" % (
            unique, name, table, columns)
        self.execute(sql)
        return True

    def setVersion(self, version):
        self.version = version
    def getVersion(self):
        return self.version


def getTables(driver="sqlite"):
    printer = PrintDatabase(True, driver)
    schema.createSchema(printer)
    return printer.statements


def getIndexes(driver="sqlite"):
    printer = PrintDatabase(False, driver)
    schema.createSchema(printer)
    return printer.statements

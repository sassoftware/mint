#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import sys, time
import weakref
from conary.dbstore import sqlerrors

from mint_error import MintError

class ItemNotFound(MintError):
    def __init__(self, item = "item"):
        self.item = item

    def __str__(self):
        return "requested %s not found" % self.item

class DuplicateItem(MintError):
    def __init__(self, item = "item"):
        self.item = item

    def __str__(self):
        return "duplicate item in %s" % self.item

class UpToDateException(MintError):
    def __init__(self, table = "Unknown Table"):
        self.table = table

    def __str__(self):
            return "The table '%s' is not up to date" % self.table

def concat(db, *items):
    if db.driver == "mysql":
        return "CONCAT(%s)" % ", ".join(items)
    elif db.driver == "sqlite":
        return " || ".join(items)
    raise Exception("Unsupported database")

class TableObject(object):
    """A simple base class defining a object-oriented interface to an SQL table.
       @cvar server: Internal L{mint.mint_server.MintServer} object to modify the object in
                      the database.
       @cvar id: The database primary key of the current object.
    """
    __slots__ = ('server', 'id')

    def getItem(self, id):
        """Abstract method to retrieve information about an object from the database
           and fill the object members with that information.

           @param id: database primary key"""
        raise NotImplementedError

    def __init__(self, server, id):
        """@param server: a L{mint.mint_server.MintServer} object
                          for manipulation of the item
                          represented by this object.
           @param id: database primary key of the item
                      to be represented by this object.
        """
        self.id = id
        self.server = server
        self.refresh()

    def refresh(self):
        """Refreshes the object's internal fields of data about the item by forcing
           a call to L{getItem}."""
        data = self.getItem(self.id)
        for key, val in data.items():
            self.__setattr__(key, val)

    def getId(self):
        """@return: database primary key of the item represented by this object"""
        return self.id

class DatabaseTable(object):
    """
    @cvar name: The name of the table as created by the createSQL string.
    @cvar fields: List of SQL fields as created by the createSQL string.
    @cvar createSQL: SQL statement to create the table for this object.
    @cvar indexes: A dictionary of indeces mapped to the SQL queries to create
    those indeces
    """

    schemaVersion = 15
    name = "Table"
    fields = []
    createSQL = "CREATE TABLE Table ();"
    createSQL_mysql = None
    indexes = {}

    def __init__(self, db):
        """@param db: database connection object. database object will be
        stored by weak reference only. an instance of it must exist outside
        of DatabaseTable objects at all times. This is normally not an issue,
        since MintServer object holds the db and all DatabaseTables objects."""
        assert(self.name and self.fields and self.createSQL)
        self.db = db

        cu = self.db.cursor()

        # create missing tables
        if self.name not in self.db.tables:
            cu.execute(self.createSQL % self.db.keywords)

        #Don't commit here.  Commits must be handled up stream to enable
        #upgrading
        self.upToDate = self.versionCheck()

        # create missing indexes, but only after upgrading.  Missing indeces
        # may be created through the regular index routines instead of being
        # explicitly created in the upgrade code.  If indeces are created
        # before the upgrade check is done, a column not found exception
        # could be raised if a new index is created referencing a new column
        # created in the upgrade procedures.

        if self.upToDate:
            self.db.loadSchema()
            indexes = set(self.db.tables[self.name])
            missing = set(self.indexes.keys()) - indexes

            for index in missing:
                cu.execute(self.indexes[index])

    def __getattribute__(self, name):
        if name == 'db':
            return object.__getattribute__(self, name)()
        return object.__getattribute__(self, name)

    def __setattr__(self, name, val):
        if name == 'db' and not isinstance(val, weakref.ref):
            return object.__setattr__(self, name, weakref.ref(val))
        return object.__setattr__(self, name, val)

    def getDBVersion(self):
        cu = self.db.cursor()

        cu.execute("SELECT COALESCE(MAX(version), 0) FROM DatabaseVersion")
        version = cu.fetchone()[0]

        if not version:
            cu.execute("""INSERT INTO DatabaseVersion(version, timestamp)
                              VALUES(?,?)""", self.schemaVersion, time.time())
            version = self.schemaVersion
        return version

    def versionCheck(self):
        """
        Override this function in tables needing to be modified.  Don't
        forget to increment the schemaVersion when an update happens.
        """
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 0:
                # Do version specific updating in this section
                # do NOT mask exceptions.
                return (dbversion + 1) == self.schemaVersion
        return True

class KeyedTable(DatabaseTable):
    """
    @cvar key: field name of the database table's primary key
    """
    key = "itemId"

    def get(self, id):
        """
        Fetches a single row in the database by primary key.
        @param id: database item primary key
        @return: map of column names to values
        @rtype: dict
        @raise ItemNotFound: row with requested key does not exist in the database.
        """

        cu = self.db.cursor()
        stmt = "SELECT %s FROM %s WHERE %s=?" % (", ".join(self.fields), self.name, self.key)
        cu.execute(stmt, id)

        r = cu.fetchone()
        if not r:
            raise ItemNotFound

        data = {}
        for i, key in enumerate(self.fields):
            if r[i] != None:
                data[key] = r[i]
            else:
                data[key] = ''

        return data

    def getIdByColumn(self, column, value):
        """
        Fetches the first primary key found by arbitrary column and value.
        @param column: database column name
        @param value: value to match primary key
        """
        cu = self.db.cursor()

        stmt = "SELECT %s FROM %s WHERE %s = ?" % (self.key, self.name, column)
        cu.execute(stmt, value)
        r = cu.fetchone()
        if not r:
            raise ItemNotFound
        else:
            return r[0]

    def new(self, **kwargs):
        """
        Adds a row to the database.
        @param kwargs: map of database column names to values.
        @return: primary key id of new item.
        """
        # XXX fix to handle sequences
        values = kwargs.values()
        cols = kwargs.keys()

        stmt = "INSERT INTO %s (%s) VALUES (%s)" %\
            (self.name, ",".join(cols), ",".join('?' * len(values)))
        cu = self.db.cursor()

        try:
            cu.execute(*[stmt] + values)
            self.db.commit()
        except sqlerrors.ColumnNotUnique:
            self.db.rollback()
            raise DuplicateItem(self.name)
        except:
            self.db.rollback()
            raise

        return cu._cursor.lastrowid

    def update(self, id, **kwargs):
        """
        Updates a row in the database.
        @param id: primary key of row to update.
        @param kwargs: map of column names to new values.
        @return: True on success
        @rtype: bool
        """
        values = kwargs.values()
        cols = kwargs.keys()

        params = "=?, ".join(cols) + "=?"
        stmt = "UPDATE %s SET %s WHERE %s=?" % (self.name, params, self.key)

        cu = self.db.cursor()
        try:
            cu.execute(*[stmt] + values + [id])
            self.db.commit()
        except sqlerrors.ColumnNotUnique:
            self.db.rollback()
            raise DuplicateItem(self.name)
        except:
            self.db.rollback()
            raise

        return True

    def search(self, columns, table, where, order, modified, limit, offset):
        """
        Returns a list of items as requested by L{columns} matching L{terms} of length L{limit} starting with item L{offset}.
        @param columns: list of columns to return
        @param table: Table, join or view against which to search
        @param where: Where clause returned by Searcher.where()
        @param searchcols: List of columns to compare with L{terms}
        @param modified: Last modification time.  Empty string to skip this check.
        @param offset: Count at which to begin listing
        @param limit:  Number of items to return
        @return:       a dictionary of the requested items.
                       each entry will contain four bits of data:
                        The hostname for use with linking,
                        The project name,
                        The project's description
                        The date last modified.
        """
        subs = [ ]
        cu = self.db.cursor()
        count = 0

        if modified:
            where += " AND " + modified

        #First get the search result count
        query = "SELECT count(%s) FROM %s " % (columns[0], table) + where[0]
        try:
            cu.execute(query, *where[1])
            r = cu.fetchone()
            count = r[0]
        except Exception, e:
            print >> sys.stderr, str(e), query
            sys.stderr.flush()
            raise
        #Now the actual search results
        query = "SELECT " + ", ".join(columns) + " FROM %s " % table
        query += where[0] + " ORDER BY %s" % order
        subs.extend(where[1])

        if limit > 0:
            query += " LIMIT ? "
            subs.append(limit)
        if offset > 0:
            query += " OFFSET ? "
            subs.append(offset)

        try:
            cu.execute(query, *subs)
        except Exception, e:
            print >> sys.stderr, str(e), query, subs
            sys.stderr.flush()
            raise

        ids = []
        for r in cu.fetchall():
            ids.append(r)
        return ids, count

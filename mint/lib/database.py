#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#
import sys
import weakref

from conary.dbstore import sqlerrors
from conary.dbstore import sqllib

from mint.mint_error import *


# Database operation decorators, for use with TableObject
# derivatives.
def dbMethod(writer=True):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            commit = kwargs.pop('commit', writer)
            cursor = self._cursor(commit)
            try:
                ret = func(self, cursor, *args, **kwargs)
            except:
                self._rollback(commit)
                raise
            self._commit(commit)
            return ret
        wrapper.__wrapped_func__ = func
        wrapper.func_name = func.func_name
        return wrapper
    return decorator

dbReader = dbMethod(False)
dbWriter = dbMethod(True)


def concat(db, *items):
    if db.driver == "mysql":
        return "CONCAT(%s)" % ", ".join(items)
    elif db.driver in ('sqlite', 'postgresql', 'pgpool'):
        return " || ".join(items)
    raise Exception("Unsupported database")

class TableObject(object):
    """A simple base class defining a object-oriented interface to an SQL table.
       @cvar server: Internal L{mint.server.MintServer} object to modify the object in
                      the database.
       @cvar id: The database primary key of the current object.
    """
    __slots__ = ('server', 'id')

    def getItem(self, id):
        """Abstract method to retrieve information about an object from the database
           and fill the object members with that information.

           @param id: database primary key"""
        raise NotImplementedError

    def getDataAsDict(self):
        d = {}
        for x in self.__slots__:
            d[x] = self.__getattribute__(x)
        return d

    def _loadData(self, data={}):
        data = sqllib.CaselessDict(data)
        for x in set(self.__slots__):
            setattr(self, x, data.pop(x, None))
        if data:
            raise AttributeError("Unknown keys: %s" % (" ".join(data.keys())))

    def __init__(self, server, id, initialData=None):
        """@param server: a L{mint.server.MintServer} object
                          for manipulation of the item
                          represented by this object.
           @param id: database primary key of the item
                      to be represented by this object.
           @param initialData: load from an initial dataset
        """
        self.id = id
        self.server = server

        if initialData:
            self._loadData(initialData)
        else:
            self.refresh()

    def refresh(self):
        """Refreshes the object's internal fields of data about the item by forcing
           a call to L{getItem}."""
        data = self.getItem(self.id)
        self._loadData(data)

    def getId(self):
        """@return: database primary key of the item represented by this object"""
        return self.id

class DatabaseTable(object):
    """
    @cvar name: The name of the table as created by the createSQL string.
    @cvar fields: List of SQL fields as created by the createSQL string.
    """

    name = "Table"
    fields = []

    def __init__(self, db):
        """@param db: database connection object. database object will be
        stored by weak reference only. an instance of it must exist outside
        of DatabaseTable objects at all times. This is normally not an issue,
        since MintServer object holds the db and all DatabaseTables objects."""
        assert(self.name and self.fields)
        self.db = db
        # XXX what purpose does creating an unused cursor serve?
        cu = self.db.cursor()

    def _getDb(self):
        return self._db()

    def _setDb(self, db):
        if not isinstance(db, weakref.ref):
            db = weakref.ref(db)
        self._db = db
    db = property(_getDb, _setDb)

    def _cursor(self, commit=True):
        """
        Get a cursor to the database. If C{commit} is C{True}, begin a
        transaction first.

        This should always be paired with C{_rollback} and C{_commit},
        passing the same C{commit} argument as was passed into the
        calling method (defaulting to C{True}), with the exception of
        read-only methods which may always call C{_cursor} with
        C{False}.

        Calls to additional database-aware methods should pass C{False}
        to those methods' C{commit} parameters regardless of their own
        C{commit} parameter.
        """
        if commit:
            self.db.transaction()
        return self.db.cursor()

    def _rollback(self, commit=True):
        if commit:
            self.db.rollback()

    def _commit(self, commit=True):
        if commit:
            self.db.commit()

    @dbWriter
    def new(self, cu, **kwargs):
        """
        Adds a row to the database.
        @param kwargs: map of database column names to values.
        @param commit: whether or not to automatically commit this
          transaction after the statement has executed.
        @return: primary key id of new item.
        """
        # XXX fix to handle sequences
        values = kwargs.values()
        fields = kwargs.keys()
        if self.db.driver == 'mysql':
            fields_ = ", ".join("`%s`" % x for x in fields)
        else:
            fields_ = ", ".join(fields)

        stmt = "INSERT INTO %s (%s) VALUES (%s)" %\
            (self.name, fields_, ",".join('?' * len(values)))

        try:
            ret = cu.execute(*[stmt] + values)
        except sqlerrors.ColumnNotUnique:
            raise DuplicateItem(self.name)

        return ret

class KeyedTable(DatabaseTable):
    """
    @cvar key: field name of the database table's primary key
    """
    key = "itemId"

    @dbReader
    def get(self, cu, id, fields=None):
        """
        Fetches a single row in the database by primary key.
        @param id: database item primary key
        @param fields: fields to retrieve when fetching; using None uses
            default fields from KeyedTable object
        @return: map of column names to values
        @rtype: dict
        @raise ItemNotFound: row with requested key does not exist in the database.
        """

        if not fields:
            fields = self.fields

        if self.db.driver == 'mysql':
            fields_ = ", ".join("`%s`" % x for x in fields)
        else:
            fields_ = ", ".join(fields)
        stmt = "SELECT %s FROM %s WHERE %s=?" % (fields_, self.name, self.key)
        cu.execute(stmt, id)

        r = cu.fetchone()
        if not r:
            raise ItemNotFound

        data = {}
        for i, key in enumerate(fields):
            if r[i] != None:
                data[key] = r[i]
            else:
                data[key] = ''

        return data

    @dbReader
    def getIdByColumn(self, cu, column, value):
        """
        Fetches the first primary key found by arbitrary column and value.
        @param column: database column name
        @param value: value to match primary key
        """
        stmt = "SELECT %s FROM %s WHERE %s = ?" % (self.key, self.name, column)
        cu.execute(stmt, value)
        r = cu.fetchone()
        if not r:
            raise ItemNotFound
        else:
            return r[0]

    @dbWriter
    def new(self, cu, **kwargs):
        """
        Adds a row to the database.
        @param kwargs: map of database column names to values.
        @param commit: whether or not to automatically commit this
          transaction after the statement has executed.
        @return: primary key id of new item.
        """
        # XXX fix to handle sequences
        values = kwargs.values()
        fields = kwargs.keys()
        if self.db.driver == 'mysql':
            fields_ = ", ".join("`%s`" % x for x in fields)
        else:
            fields_ = ", ".join(fields)

        stmt = "INSERT INTO %s (%s) VALUES (%s)" %\
            (self.name, fields_, ",".join('?' * len(values)))

        try:
            cu.execute(*[stmt] + values)
        except sqlerrors.ColumnNotUnique:
            raise DuplicateItem(self.name)

        if self.key in kwargs:
            return kwargs[self.key]
        else:
            return cu.lastid()

    @dbWriter
    def update(self, cu, id, **kwargs):
        """
        Updates a row in the database.
        @param id: primary key of row to update.
        @param commit: whether or not to automatically commit this
          transaction after the statement has executed.
        @param kwargs: map of column names to new values.
        @return: True on success
        @rtype: bool
        """
        values = kwargs.values()
        cols = kwargs.keys()

        params = "=?, ".join(cols) + "=?"
        stmt = "UPDATE %s SET %s WHERE %s=?" % (self.name, params, self.key)

        try:
            cu.execute(*[stmt] + values + [id])
        except sqlerrors.ColumnNotUnique:
            raise DuplicateItem(self.name)

        return True

    @dbWriter
    def delete(self, cu, id):
        """
        Deletes a row in the database.
        @param id: primary key of row to delete.
        @param commit: whether or not to automatically commit this
          transaction after the statement has executed.
        @return: True on success
        @rtype: bool
        """
        stmt = "DELETE FROM %s WHERE %s=?" % (self.name, self.key)
        cu.execute(stmt, id)
        return True

    @dbReader
    def search(self, cu, columns, table, where, order, modified, limit, offset, leftJoins=[]):
        """
        Returns a list of items as requested by L{columns} matching L{terms} of length L{limit} starting with item L{offset}.
        @param columns: list of columns to return
        @param table: Table, join or view against which to search
        @param where: Where clause returned by Searcher.where()
        @param searchcols: List of columns to compare with L{terms}
        @param modified: Last modification time.  Empty string to skip this check.
        @param offset: Count at which to begin listing
        @param limit:  Number of items to return
        @param leftJoins: tuples of table(s) to join on (table, using)
        @return:       a dictionary of the requested items.
                       each entry will contain four bits of data:
                        The hostname for use with linking,
                        The project name,
                        The project's description
                        The date last modified.
        """
        subs = [ ]
        count = 0

        if modified:
            where = where[0] + " AND " + modified, where[1]

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
        for leftJoin in leftJoins:
            query += " LEFT OUTER JOIN %s USING (%s) " % leftJoin
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

def createTemporaryTable(db, tableName, tableColumns):
    cu = db.cursor()
    if tableName in db.tempTables:
        cu.execute("DELETE FROM %s" % tableName)
    else:
        sql = "CREATE TEMPORARY TABLE %s (%s)" % (
            tableName, ','.join(tableColumns))
        cu.execute(sql)
        db.tempTables[tableName] = True

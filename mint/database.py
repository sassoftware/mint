#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import sys

from mint_error import MintError

class ItemNotFound(MintError):
    def __init__(self, table = "table"):
        self.table = table
    def __str__(self):
        return "requested item not found in %s" % self.table

class DuplicateItem(MintError):
    def __init__(self, table = "table"):
        self.table = table
    def __str__(self):
        return "failed to add duplicate item to %s" % self.table

class TableObject:
    __slots__ = ['server', 'id']

    def getItem(self, id):
        raise NotImplementedError

    def __init__(self, server, id):
        self.id = id
        self.server = server
        self.refresh()

    def refresh(self):
        data = self.getItem(self.id)
        self.__dict__.update(data)

    def getId(self):
        return self.id

class DatabaseTable:
    name = None
    fields = []
    createSQL = None

    def __init__(self, db):
        assert(self.name and self.fields and self.createSQL)
        self.db = db

        cu = self.db.cursor()
        cu.execute("SELECT tbl_name FROM sqlite_master WHERE type='table'")

        tables = [ x[0] for x in cu ]
        if self.name not in tables:
            cu.execute(self.createSQL)

def KeyedTable(DatabaseTable):
    key = None

    def get(self, id):
        assert(self.key)
        
        cu = self.db.cursor()
        stmt = "SELECT %s FROM %s WHERE %s=?" % (", ".join(self.fields), self.name, self.key)
        cu.execute(stmt, id)
        try:
            r = cu.next()
        except StopIteration:
            raise ItemNotFound(self.name)

        data = {}
        for i, key in enumerate(self.fields):
            data[key] = r[i]
        return data

    def new(self, **kwargs):
        values = kwargs.values()
        cols = kwargs.keys()

        stmt = "INSERT INTO %s (%s) VALUES (%s)" %\
            (self.name, ",".join(cols), ",".join('?' * len(values)))
        cu = self.db.cursor()

        try:
            cu.execute(*[stmt] + values)
        except sqlite3.ProgrammingError:
            raise DuplicateItem(self.name)

        self.db.commit()
        return cu.lastrowid

#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import sys
import sqlite3

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
        self.db.commit()

class KeyedTable(DatabaseTable):
    key = None

    def get(self, id):
        assert(self.key)
        
        cu = self.db.cursor()
        stmt = "SELECT %s FROM %s WHERE %s=?" % (", ".join(self.fields), self.name, self.key)
        cu.execute(stmt, id)
        try:
            r = cu.next()
        except StopIteration:
            raise ItemNotFound('user')

        data = {}
        for i, key in enumerate(self.fields):
            data[key] = r[i]
        return data

    def getIdByColumn(self, column, value):
        cu = self.db.cursor()
    
        stmt = "SELECT %s FROM %s WHERE %s = ?" % (self.key, self.name, column)
        cu.execute(stmt, value)
        try:
            return cu.next()[0]
        except StopIteration:
            raise ItemNotFound('user')

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

    def update(self, id, **kwargs):
        values = kwargs.values()
        cols = kwargs.keys()
        
        params = "=?, ".join(cols) + "=?"
        stmt = "UPDATE %s SET %s WHERE %s=?" % (self.name, params, self.key)

        cu = self.db.cursor()
        cu.execute(*[stmt] + values + [id])
        self.db.commit()
        return True

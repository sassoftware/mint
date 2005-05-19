#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import sys

class ItemNotFound:
    def __str__(self, table):
        return "requested item not found in %s" % table


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
    key = None

    def __init__(self, db):
        assert(self.name and self.fields and self.createSQL)
        self.db = db

        cu = self.db.cursor()
        cu.execute("SELECT tbl_name FROM sqlite_master WHERE type='table'")

        tables = [ x[0] for x in cu ]
        if self.name not in tables:
            cu.execute(self.createSQL)

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
        cu.execute(*[stmt] + values)

        self.db.commit()
        return cu.lastrowid

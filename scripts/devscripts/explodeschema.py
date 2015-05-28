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


import psycopg2
import re
import sys
from collections import namedtuple
from psycopg2 import extensions


SERIAL_DEFAULT = re.compile(r"^nextval\('.*'::regclass\)$")


def main(args):
    conn1, conn2 = args
    db1 = psycopg2.connect(conn1)
    db1.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    schema1 = _load(db1)
    db2 = psycopg2.connect(conn2)
    db2.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    schema2 = _load(db2)
    for addremove, subpath, value in schema2.diff(schema1):
        print addremove, subpath, value


def diff(old_db, new_db):
    old_schema = _load(old_db)
    new_schema = _load(new_db)
    count = 0
    for addremove, subpath, value in new_schema.diff(old_schema):
        print addremove, subpath, value
        count += 1
    return count


def quoteId(name):
    name = name.replace('"', '""')
    return '"%s"' % name


def fold(items, numCols=1, numUniq=None):
    """
    Iterate over a sorted list of C{items}, grouping by the first C{numCols}
    elements of each tuple and yielding each time a new selector is
    encountered.

    If C{numUniq} is given, that many columns are tested for equality but all
    C{numCols} columns are returned as the "key". For example, C{fold(foo, 1,
    3)} groups based on the first column's value, but returns the first 3
    columns as a key.

    This is similar to L{itertools.groupby()}, but maps more directly to
    operations such as iterating over a SQL cursor.
    """
    if numUniq is None:
        numUniq = numCols
    assert numUniq <= numCols
    last, values = (), []
    for item in items:
        key, value = item[:numCols], item[numCols:]
        if key[:numUniq] != last[:numUniq]:
            if last:
                if numCols == 1:
                    last = last[0]
                yield last, values
            last, values = key, []
        values.append(value)
    if last:
        if numCols == 1:
            last = last[0]
        yield last, values


## Schema objects -- tables, columns, etc.

_SIMPLE_TYPES = (basestring, int, long)


class SchemaObject(object):

    _fields = None

    def diff(self, old, path=()):
        if self._fields is None:
            raise NotImplementedError
        changes = []
        for name in self._fields:
            subpath = path + (name,)
            newval = getattr(self, name)
            oldval = getattr(old, name)
            if newval is None and oldval is None:
                continue
            elif newval is None:
                changes.append(('-', subpath, oldval))
            elif oldval is None:
                changes.append(('+', subpath, newval))
            elif isinstance(newval, SchemaObject):
                changes.extend(newval.diff(oldval, path))
            elif isinstance(newval, _SIMPLE_TYPES):
                assert type(newval) == type(oldval)
                if newval != oldval:
                    changes.append(('-', subpath, oldval))
                    changes.append(('+', subpath, newval))
            else:
                raise TypeError("Can't compare %r at %r" %
                        (type(newval), subpath))
        return changes


class SchemaDict(dict, SchemaObject):

    def diff(self, old, path=()):
        changes = []
        for added in sorted(set(self) - set(old)):
            changes.append(('+', path + (added,), self[added]))
        for removed in sorted(set(old) - set(self)):
            changes.append(('-', path + (removed,), old[removed]))
        for shared in sorted(set(self) & set(old)):
            changes.extend(self[shared].diff(old[shared], path + (shared,)))
        return changes


class SchemaSet(frozenset, SchemaObject):

    def diff(self, old, path=()):
        changes = []
        for x in sorted(self - old):
            changes.append(('+', path, x))
        for x in sorted(old - self):
            changes.append(('-', path, x))
        return changes


class Schema(SchemaObject):

    _fields = ('tables',)

    def __init__(self):
        self.tables = SchemaDict()

    def __repr__(self):
        return '<Schema with %d tables>' % (len(self.tables),)

    def __getitem__(self, key):
        if isinstance(key, basestring):
            key = ('public', key)
        return self.tables[key]


class Table(SchemaObject):

    def __init__(self, namespace, name, columns):
        self.namespace = namespace
        self.name = name
        self.columns = SchemaDict(columns)
        self.constraints = SchemaDict()
        self.indexes = SchemaDict()
        self.rows = SchemaSet()

    def __repr__(self):
        return '<Table %s>' % self.qualified

    def getColumnByNum(self, num):
        for col in self.columns.values():
            if col.num == num:
                return col
        raise KeyError(num)

    @property
    def qualified(self):
        return '%s.%s' % (quoteId(self.namespace), quoteId(self.name))

    @property
    def ref(self):
        return TableRef(self.namespace, self.name)

    def _reduceCons(self):
        return SchemaDict((x._reduce(), x) for x in self.constraints.values())

    def _reduceIndex(self):
        return SchemaDict((x._reduce(), x) for x in self.indexes.values())

    def diff(self, old, path=()):
        changes = []
        changes.extend(self.columns.diff(old.columns, path + ('columns',)))
        oldsub = old._reduceCons()
        newsub = self._reduceCons()
        changes.extend(newsub.diff(oldsub, path + ('constraints',)))
        oldsub = old._reduceIndex()
        newsub = self._reduceIndex()
        changes.extend(newsub.diff(oldsub, path + ('indexes',)))
        changes.extend(self.rows.diff(old.rows, path + ('rows',)))
        return changes


class Column(SchemaObject):

    _fields = ('type', 'notnull', 'default')

    def __init__(self, name, type, num, notnull, default):
        self.name = name
        self.type = type
        self.num = num
        self.notnull = notnull
        self.default = default

    def __repr__(self):
        return '<Column %s %s>' % (quoteId(self.name), self.type)


class Constraint(SchemaObject):

    # Base constraint just has keys, but the keys are used as the comparison
    # key in _reduce so that leaves no fields that need comparing at this
    # level.
    _fields = ()

    def __init__(self, name, keys):
        self.name = name
        self.keys = SchemaSet(keys)

    def __repr__(self):
        return '<%s %s>' % (type(self).__name__, quoteId(self.name))

    def _reduce(self):
        return (type(self).__name__, self.keys)


class UniqueConstraint(Constraint):
    pass


class PrimaryKeyConstraint(UniqueConstraint):
    pass


class ForeignKeyConstraint(Constraint):

    _fields = ('fkTable', 'fkKeys', 'fkOnUpdate', 'fkOnDelete')

    def __init__(self, name, keys, fkTable, fkKeys, fkOnUpdate, fkOnDelete):
        Constraint.__init__(self, name, keys)
        self.fkTable = fkTable
        self.fkKeys = SchemaSet(fkKeys)
        self.fkOnUpdate = fkOnUpdate
        self.fkOnDelete = fkOnDelete


class CheckConstraint(Constraint):

    _fields = ('expr',)

    def __init__(self, name, keys, expr):
        Constraint.__init__(self, name, keys)
        self.expr = expr


class Index(SchemaObject):

    _fields = ('unique', 'keys', 'expr')

    def __init__(self, name, unique, keys, expr):
        self.name = name
        self.unique = unique
        self.keys = SchemaSet(keys)
        self.expr = expr

    def __repr__(self):
        return '<Index %s%s>' % (self.name, self.unique and ' unique' or '')

    def _reduce(self):
        return (self.keys, self.expr, self.unique)


class SerialDefault(SchemaObject):
    """Placeholder for column defaults that fetch from a sequence."""

    def __repr__(self):
        return '<SerialDefault>'

    def diff(self, old, path=()):
        # Always equal to any other SerialDefault. This is because sequences
        # can change names over the life of a schema but the odds of running
        # into a case where a change between two simple serial defaults is
        # significant is very small.
        assert type(self) == type(old)
        return []


class TableRef(namedtuple('TableRef', 'namespace name'), SchemaObject):
    _fields = ('namespace', 'name')

    def __repr__(self):
        return '%s.%s' % (quoteId(self.namespace), quoteId(self.name))


def _load(db):
    cu = db.cursor()
    schema = Schema()

    # Tables and columns
    tableMap = {}
    cu.execute("""
        SELECT t.oid, n.nspname, t.relname,
                a.attnum, a.attname, a.attnotnull,
                pg_catalog.format_type(a.atttypid, a.atttypmod),
                ( SELECT pg_catalog.pg_get_expr(d.adbin, d.adrelid)
                    FROM pg_attrdef d WHERE d.adrelid = a.attrelid AND
                    d.adnum = a.attnum AND a.atthasdef )
            FROM pg_class t
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN pg_attribute a ON a.attrelid = t.oid
        WHERE t.relkind = 'r' AND a.attnum > 0 AND NOT a.attisdropped
            AND nspname = ANY ( pg_catalog.current_schemas(false) )
        ORDER BY t.oid
        """)
    for (oid, namespace, name), columns in fold(cu, 3):
        colsByName = {}
        for colNum, colName, colNotNull, colType, colDefault in columns:
            if colDefault and SERIAL_DEFAULT.match(colDefault):
                colDefault = SerialDefault()
            column = Column(colName, colType, colNum, colNotNull, colDefault)
            colsByName[colName] = column
        ref = TableRef(namespace, name)
        schema.tables[ref] = tableMap[oid] = Table(namespace, name, colsByName)

    # Constraints
    oids = tuple(tableMap)
    cu.execute("""
        SELECT r.oid, r.conrelid, r.conname, r.contype, r.conkey,
            r.confrelid, r.confupdtype, r.confdeltype, r.confkey,
            pg_get_expr(r.conbin, r.conrelid, true)
        FROM pg_constraint r
        WHERE r.conrelid IN %s
        """, (oids,))
    for (oid, tableOID, name, conType, keys, fkOID, fkOnUpdate, fkOnDelete,
            fkKeys, conExpr) in cu:
        table = tableMap[tableOID]
        keys = tuple(table.getColumnByNum(x).name for x in keys)

        if conType == 'p':
            con = PrimaryKeyConstraint(name, keys)
        elif conType == 'u':
            con = UniqueConstraint(name, keys)
        elif conType == 'f':
            fkTable = tableMap[fkOID]
            fkKeys = tuple(fkTable.getColumnByNum(x).name for x in fkKeys)
            fkOnUpdate = FKEY_ACTION_MAP.get(fkOnUpdate)
            fkOnDelete = FKEY_ACTION_MAP.get(fkOnDelete)
            con = ForeignKeyConstraint(name, keys, fkTable.ref, fkKeys,
                    fkOnUpdate, fkOnDelete)
        elif conType == 'c':
            con = CheckConstraint(name, keys, conExpr)
        else:
            raise RuntimeError("Unknown constraint type %r" % (conType,))
        table.constraints[name] = con

    # Indexes
    cu.execute("""
        SELECT x.indexrelid, x.indrelid, i.relname,
            x.indisunique, x.indisprimary, x.indkey,
            pg_get_expr(x.indexprs, x.indrelid, true)
        FROM pg_index x
            JOIN pg_class i ON i.oid = x.indexrelid
        WHERE x.indrelid IN %s
        """, (oids,))
    for oid, tableOID, name, isUnique, isPrimary, keys, expr in cu:
        table = tableMap[tableOID]
        # NB: indkey is an "int2vector", which psycopg2 represents as a
        # string of space-separated numbers.
        keys = tuple(int(x) for x in keys.split())
        if keys == (0,):
            # Expression index
            assert expr is not None
        else:
            keys = tuple(table.getColumnByNum(x).name for x in keys)

        # TODO: ignore indexes implied by a constraint, maybe?
        table.indexes[name] = Index(name, isUnique, keys, expr)


    # Rows
    for table in schema.tables.values():
        ignore_cols = ['created_date', 'modified_date']
        order = ''
        for cons in table.constraints.values():
            if isinstance(cons, PrimaryKeyConstraint):
                order = 'ORDER BY ' + ','.join(cons.keys)
                # Ignore serial primary key columns in row comparisons.
                if len(cons.keys) == 1:
                    col = table.columns[tuple(cons.keys)[0]]
                    if isinstance(col.default, SerialDefault):
                        ignore_cols.append(col.name)
            elif isinstance(cons, ForeignKeyConstraint):
                # Ignore references to serial columns in row comparisons.
                if len(cons.keys) == 1:
                    assert len(cons.fkKeys) == 1
                    colName = tuple(cons.keys)[0]
                    fkName = tuple(cons.fkKeys)[0]
                    col = schema.tables[cons.fkTable].columns[fkName]
                    if isinstance(col.default, SerialDefault):
                        ignore_cols.append(colName)
        cu.execute("SELECT * FROM %s %s" % (table.qualified, order))
        namesIn = [x[0] for x in cu.description]
        namesOut = sorted(set(namesIn) - set(ignore_cols))
        rows = []
        for row in cu:
            row = dict(zip(namesIn, row))
            row = tuple(row[x] for x in namesOut)
            rows.append(tuple(row))
        table.rows = SchemaSet(rows)

    return schema


FKEY_ACTION_MAP = {
        'a': 'NO ACTION',
        'r': 'RESTRICT',
        'c': 'CASCADE',
        'n': 'SET NULL',
        'd': 'SET DEFAULT',
        }


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

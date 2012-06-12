#
# Copyright (c) 2011 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

# INCLUDED IN CLIENT SIDE DISTRIBUTION #

import inspect
from xobj2 import xobj2


def toCamelCaps(name):
    """
    ie: Changes management_nodes to ManagementNodes
    """
    return ''.join(s.capitalize() for s in name.split('_'))


def toUnderscore(name):
    """
    ie: Changes ManagementNodes to management_nodes
    """
    L = []
    F = lambda i, c: L.append(c.lower()) if i == 0 else L.append('_' + c.lower())
    for i, c in enumerate(name):
        if c.isupper():
            F(i, c)
        else:
            L.append(c)
    return ''.join(L)


def indent(txt, n=1):
    """
    n is the number of times txt should be indented
    """
    if txt is None:
        return ''
    splitted = ['    ' + line + '\n' for line in txt.split('\n')]
    joined = ''.join(splitted)
    if n > 1:
        joined = indent(joined, n - 1)
    return joined.rstrip()


def register(cls):
    module = inspect.getmodule(cls)
    module.REGISTRY[cls.__name__] = StubMetadata(cls)
    return cls


class ValidationError(Exception):
    pass
    

class SDKModel(xobj2.XObj):
    def __new__(cls, data='', *args, **kwargs):
        return xobj2.XObj.__new__(cls, data)

    def __init__(self, *args, **kwargs):
        self.__dict__['_xobjMeta'] = getattr(self, '_xobjMeta', xobj2.XObjMetadata())
        for k, v in kwargs.items():
            for attrname in self._xobjMeta.attributes:
                if k == attrname:
                    setattr(self, attrname, str(v))

            # elements take precedence over attrs of
            # same name
            for e in self._xobjMeta.elements:
                if k == e.name:
                    typ = e.type if not isinstance(e.type, list) else e.type[0]
                    if hasattr(typ, '_validate') and not isinstance(v, list):
                        typ._validate(k, v)
                        setattr(self, k, typ(v))
                    else:
                        setattr(self, k, v)
                    break

        self._validators = {}
        for e in self._xobjMeta.elements:
            self._validators[e.name] = e.type._validate if not \
                        isinstance(e.type, list) else e.type[0]._validate

    def __setattr__(self, k, v):
        if hasattr(self, '_validators'):
            validator = self._validators.get(k)
            validator(k, v)
        self.__dict__[k] = v

    def _validate(self, k, v):
        pass
        
        
class StubMetadata(dict):
    def __init__(self, cls):
        super(StubMetadata, self).__init__()
        self.cls = cls
        self.clsname = self.cls.__name__
        for e in self.cls._xobjMeta.elements:
            fieldname, typ = e.name, e.type
            self[fieldname] = typ


class DynamicImportResolver(object):
    def __init__(self, GLOBALS):
        self.registry = GLOBALS['REGISTRY']
        self.globals = GLOBALS

    def rebind(self):
        findRefCls = self.findRefCls
        for clsname, metadata in self.registry.items():
            cls = metadata.cls
            for fieldname, typ in metadata.items():
                newtyp = findRefCls(typ) if not \
                    isinstance(typ, list) else [findRefCls(typ)]
                for i, e in enumerate(cls._xobjMeta.elements):
                    if fieldname == e.name:
                        cls._xobjMeta.elements[i] = xobj2.Field(e.name, newtyp)

    def findRefCls(self, typ):
        typ = typ if not isinstance(typ, list) else typ[0]
        typname = typ.__name__
        modname = getattr(typ, '__module__', None)
        if modname:
            module = __import__(modname, globals(), locals(), -1)
            return module.__dict__[typname]
        else:
            return self.globals.get(typname, typ)
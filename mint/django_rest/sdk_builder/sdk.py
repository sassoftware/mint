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

from xobj import xobj
import inspect


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


class ValidationError(Exception):
    pass


class XObjInitializer(xobj.XObj):
    """
    Just initializes a field, doing validation in the process
    """
    def __init__(self, data=None):
        self._data = self._validate(self.__class__.__name__, data)


def register(cls):
    """
    cls decorator that initializes the registry. this is
    what allows fk and m2m fields to work. it requires
    that the module define an empty dictionary called
    REGISTRY in addition to inlining some module level
    code to rebind referenced class attrs after loading
    """
    name = cls.__name__
    module = inspect.getmodule(cls)
    module.REGISTRY[name] = {}
    for k, v in cls.__dict__.items():
        if isinstance(v, list):
            module.REGISTRY[name][k] = v[0]
        elif isinstance(v, str):
            module.REGISTRY[name][k] = v
    return cls


class SDKClassMeta(type):
    """
    redefining the cls's __init__ method allows the
    instantiation of the class stubs using kwargs. ie:
    >>> p = Package(name="Nano", package_id=1)
    >>> p.name
    Nano
    >>> type(p.name)
    <type 'str'>

    finally, redefining the __setattr__ method is necessary for
    the validation to work. ie:
    >>> p = Package(name="Nano", package_id=1)
    >>> p.name = 1
    ValidationError: Value must be of type str or unicode
    >>> p.name = 'nano, lowercase'
    >>> p.name
    nano, lowercase
    """
    def __new__(meta, name, bases, attrs):
        """
        Complicated but necessary -- redefines a __new__ method to
        return an inlined class with a dynamically generated __init__
        """
        def new(cls, *args, **kwargs):

            def make(k, v):
                attr = getattr(cls, k)
                # for fields in list_fields, attr is a list
                # containing one or more elements
                if isinstance(attr, list):
                    # if field k not specified in kwargs then v will
                    # be a list containing a single item which will be
                    # a class. in this case set v to empty.  otherwise
                    # v will be a list containing zero or more instances
                    # of inner.
                    # HACK: checking by __name__
                    if isinstance(v, list) and not \
                        v[0].__class__.__name__.startswith('converted'):
                        attrVal = []
                    else:
                        assert(isinstance(v, list))
                        attrVal = v
                # when field not in list_fields
                else:
                    # when k not in kwargs
                    if inspect.isclass(v):
                        attrVal = attr('')
                    # when k in kwargs and v isinstance of converted attr. not
                    # sure why this case can happen but regardless, this works
                    # HACK: checking by __name__
                    elif v.__class__.__name__ == ('converted_' + attr.__name__):
                        attrVal = v
                    # when k in kwargs
                    else:
                        attrVal = attr(v)
                return attrVal

            class inner(object):
                def __init__(self, *args, **kwargs):
                    # cast to dict since cls.__dict__ is actually a dictproxy
                    d = dict(cls.__dict__)
                    d.update(kwargs)
                    # if one of the kwargs, with key k and value v, is left out
                    # then v is actually a class, not an instance of some class
                    for k, v in d.items():
                        try:
                            if inspect.isfunction(v) or k.startswith('__'):
                                continue
                            elif k.startswith('_xobj'):
                                attr = v
                            else:
                                # make attr based on how and what input
                                # parameters are passed in kwargs
                                attr = make(k, v)
                            self.__dict__[k] = attr
                        except TypeError:
                            # happens when v should be a class but
                            # is instead the name of a class. this
                            # occurs when a class attribute (which
                            # is the name of a class) has not
                            # been rebound with the actual class. if
                            # v is not a str or unicode then something
                            # really funky is going on
                            assert(isinstance(v, (str, unicode)))
                            raise Exception('class attribute "%s" was not correctly rebound, cannot instantiate' % k)

                def __setattr__(self, k, v):
                    attr = cls.__dict__.get(k, None)
                    if hasattr(attr, '_validate'):
                        v = attr._validate(k, v)
                    self.__dict__[k] = v

            inner.__name__ = 'converted_%s' % cls.__name__
            return inner(*args, **kwargs)
        # rebind __new__ and create class
        attrs['__new__'] = new
        return type.__new__(meta, name, bases, attrs)


class DynamicImportResolver(object):

    def __init__(self, GLOBALS):
        self.globals = GLOBALS
        self.registry = GLOBALS['REGISTRY']

    def rebind(self):
        self.rebindLocals()
        self.rebindGlobals()

    def rebindLocals(self):
        # go before rebindGlobals
        for tag, clsAttrs in self.registry.items():
            for attrName, refClsOrName in clsAttrs.items():
                # use globals not registry since we are doing
                # from Fields import *
                # inside of the the module that runs this code
                if refClsOrName in self.globals and attrName not in ['__module__', '__doc__']:
                    cls, refCls = self.globals[tag], self.globals[refClsOrName]
                    self._setAttr(cls, attrName, refCls)

    def rebindGlobals(self):
        # go after rebindLocals
        for tag, clsAttrs in self.registry.items():
            for attrName, refClsOrName in clsAttrs.items():
                if refClsOrName not in self.globals and attrName not in ['__module__', '__doc__']:
                    cls, refCls = self.globals[tag], self._findRefCls(refClsOrName)
                    self._setAttr(cls, attrName, refCls)

    def _setAttr(self, cls, attrName, refCls):
          if isinstance(getattr(cls, attrName), list):
              setattr(cls, attrName, [refCls])
          else:
              setattr(cls, attrName, refCls)

    def _findRefCls(self, refClsName):
        """
        refClsName = 'rbuilder.Users'
        """
        splitted = refClsName.split('.')
        mod_import_path = '.'.join(splitted[0:-1])
        clsname = splitted[-1]
        if 'rsdk' not in mod_import_path:
            mod_import_path = 'rsdk.' + mod_import_path
        module = __import__(mod_import_path, globals(), locals(), -1)
        return module.__dict__[clsname]

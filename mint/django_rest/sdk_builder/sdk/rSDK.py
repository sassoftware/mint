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
# import xobj_debug as xobj
import inspect


def toCamelCase(name):
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

class GetSetMixin(object):
    """
    Turns what inherits from it into a descriptor.
    Is the basis for the validation framework.
    """
    def __get__(self, instance, owner):
        return self._data

    def __set__(self, instance, value):
        self._data = self._validate(value)

class XObjInitializer(xobj.XObj):
    """
    Just initializes a field, doing validation in the process
    """
    def __init__(self, data=None):
        self._data = self._validate(data)


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
    <class 'sdk.Fields.CharField'>
    
    finally, redefining the __init__ method is necessary for
    the descriptors (which power the validation) to work. ie:
    >>> p = Package(name="Nano", package_id=1)
    >>> p.name = 1
    TypeError: Value must be of type str or unicode
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
            class inner(object):
                def __init__(self, *args, **kwargs):
                    # cast to dict since cls.__dict__ is actually a dictproxy
                    d = dict(cls.__dict__)
                    d.update(kwargs)
                    # if one of the kwargs, with key k and value v, is left out
                    # then v is actually a class, not an instance of some class
                    for k, v in d.items():
                        try:
                            if inspect.isfunction(v) or k.startswith('_'):
                                continue
                            elif inspect.isclass(v):
                                attr = getattr(cls, k)('')
                            else:
                                attr = getattr(cls, k)(v)
                            setattr(inner, k, attr)
                        except TypeError:
                            # this occurs when an extra-module reference is required.
                            # TypeError unhandled during development phase but will
                            # raise an exception in production version
                            pass
            return inner(*args, **kwargs)
        # rebind __new__ and create class
        attrs['__new__'] = new
        klass = type.__new__(meta, name, bases, attrs)
        return klass
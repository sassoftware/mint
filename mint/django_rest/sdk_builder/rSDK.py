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

    def __str__(self):
        return str(self._data)

    __repr__ = __str__

class SDKClassMeta(type):
    """
    this is what allows fk and m2m fields to work.
    requires that the module define an empty dictionary
    called REGISTRY in addition to inlining some module
    level code to rebind referenced class attrs after loading
    
    additionally, redefining the cls's __init__ method allows
    the instantiation of the class stubs using kwargs. ie:
    >>> p = Package(name="Nano", package_id=1)
    >>> p.name
    Nano
    >>> type(p.name)
    <class 'sdk.Fields.CharField'>
    """
    def __new__(meta, name, bases, attrs):
        
        # __init__ allows initializing cls
        # using kwargs
        def __init__(self, *args, **kwargs):
            if kwargs:
                # shadow cls attr
                for k, v in kwargs.items():
                    try:
                        attr = getattr(cls, k)(v)
                        setattr(self, k, attr)
                    except TypeError:
                        setattr(self, k, v)
                        
        # Build cls and set __init__
        cls = type(name, bases, attrs)
        cls.__init__ = __init__
        
        # Get REGISTRY that's bound to cls's module
        module = inspect.getmodule(cls)
        module.REGISTRY[name] = {}
        # Prepare REGISTRY
        for k, v in attrs.items():
            if isinstance(v, list):
                module.REGISTRY[name][k] = v[0]
            elif isinstance(v, str):
                module.REGISTRY[name][k] = v
        return cls
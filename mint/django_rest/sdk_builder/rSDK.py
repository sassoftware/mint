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

def toUnderscore(name):
    """
    used to be unparseName
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

class XObjMixin(object):
    def __setattr__(self, k, v):
        """
        Only do assertion after initialization is complete
        during initialization, setattr always passed a string.
        The idea behind validation in setattr is that once
        the class is initialized, a class attribute may only
        be assigned to if the assigned value is an instance
        or an instance of a subclass of the original type.
        """
        check = lambda x,y: issubclass(x.__class__, y)
        try:
            # self refers to instance of child class
            item = self.__class__.__dict__[k]
            # item is list if so indicated in class stub
            if isinstance(item, list):
                assert(len(item) == 1)
                # FIXME
                # not sure why, but sometimes v is
                # an empty list ... and sometimes
                # it isn't
                if isinstance(v, list):
                    pass
                else:
                    assert(check(v, item[0]))
            else:
                if not k.startswith('_'):
                    assert(check(v, item))
        except KeyError: # __dict__ not initialized yet
            pass
        self.__dict__[k] = v

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
                for k, v in kwargs.items():
                    # shadow cls attr
                    try:
                        attr = getattr(cls, k)(v)
                        setattr(self, k, attr)
                    except TypeError:
                        setattr(self, k, v)
        # Build cls and set __init__
        cls = type(name, bases, attrs)
        cls.__init__ = __init__
        # Get REGISTRY bound to cls's module
        module = inspect.getmodule(cls)
        module.REGISTRY[name] = {}
        # Rebind cls attributes with their
        # corresponding classes
        for k, v in attrs.items():
            if isinstance(v, list):
                module.REGISTRY[name][k] = v[0]
            elif isinstance(v, str):
                module.REGISTRY[name][k] = v
        return cls

class GetSetXMLAttrMeta(type):
    def __init__(klass, name, bases, attrs):
        """
        metaclass necessary to overload xml attribute access.
        because of the MRO, these methods can't be included
        in XObjMixin and its ugly to inline this code in
        every class.
        
        Overloads __getitem__ and __setitem__ such that
        
        class Catalog(xobj.XObj):
            pass
        class Url(xobj.XObj):
            pass
        
        <catalog cid="1">
            <url>http://example.com</url>
        </catalog>
        ...
        doc = parse(XML, typeMap={'catalog':Catalog, 'url':Url})
        doc.catalog['cid'] == '1'
        """
        # must initialize type before modifying klass attrs
        # because __getitem__ and __setitem__ will be overwritten
        # by the methods inherited from bases at initialization
        # time.
        super(GetSetXMLAttrMeta, klass).__init__(name, bases, attrs)

        def __getitem__(self, k):
            if isinstance(k, str):
                # FIXME: below should work
                # return self._xobj.attributes[k]
                # HACK:
                if k in self._xobj.attributes:
                    return getattr(self, k)
                raise KeyError
            else:
                return xobj.XObj.__getitem__(self, k)

        def __setitem__(self, k, v):
            if isinstance(k, str):
                # FIXME: below should work
                # self._xobj.attributes[k] = v
                # HACK:
                if k in self._xobj.attributes:
                    setattr(self, k, v)
            else:
                super(klass, self).__setitem__(k, v)

        klass.__getitem__ = __getitem__
        klass.__setitem__ = __setitem__
    
class Fields(object):
    """
    Need to explicitly specify __name__ attr or else it
    will be listed as 'type'.  A copy of Fields is maintained
    inside of sdk.  Any updates to Fields must
    be propagated (sorry, I know bad technique, but its not
    too much extra effort to maintain -- future FIXME)
    """
    
    class CharField(xobj.XObj):
        __name__ = 'CharField'
        
        def __init__(self, data=None):
            self.data = data
        
        def __get__(self, instance, owner):
            print 'Got!'
            return self.data
            
        def __set__(self, instance, value):
            print 'Value is: ' + value
            self.data = value
            
            
    class DecimalField(xobj.XObj):
        __name__ = 'DecimalField'
    
    class FloatField(xobj.XObj):
        __name__ = 'FloatField'
    
    class IntegerField(xobj.XObj):
        __name__ = 'IntegerField'
    
    class TextField(xobj.XObj):
        __name__ = 'TextField'
    
    class ForeignKey(xobj.XObj):
        __name__ = 'ForeignKey'
    
    class ManyToManyField(xobj.XObj):
        __name__ = 'ManyToManyField'
    
    class OneToOneField(xobj.XObj):
        __name__ = 'OneToOneField'
    
    class AutoField(xobj.XObj):
        __name__ = 'AutoField'
    
    class NullBooleanField(xobj.XObj):
        __name__ = 'NullBooleanField'
    
    class DateTimeUtcField(xobj.XObj):
        __name__ = 'DateTimeUtcField'
    
    class SerializedForeignKey(xobj.XObj):
        __name__ = 'SerializedForeignKey'
    
    class HrefField(xobj.XObj):
        __name__ = 'HrefField'
    
    class DeferredForeignKey(xobj.XObj):
        __name__ = 'DeferredForeignKey'
    
    class SmallIntegerField(xobj.XObj):
        __name__ = 'SmallIntegerField'
    
    class XMLField(xobj.XObj):
        __name__ = 'XMLField'
    
    class InlinedDeferredForeignKey(xobj.XObj):
        __name__ = 'InlinedDeferredForeignKey'
    
    class InlinedForeignKey(xobj.XObj):
        __name__ = 'InlinedForeignKey'
    
    class BooleanField(xobj.XObj):
        __name__ = 'BooleanField'
    
    class URLField(xobj.XObj):
        __name__ = 'URLField'
    
    class DateTimeField(xobj.XObj):
        __name__ = 'DateTimeField'
        
    class EmailField(xobj.XObj):
        __name__ = 'EmailField'

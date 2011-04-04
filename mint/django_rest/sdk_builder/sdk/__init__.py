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

import httplib2
import urlparse
from xobj import xobj

def connect(base_url, auth=None):
    """
    base_url = 'http://server.com/api/'
    auth = (username, password)
    """
    class Client(object):
        """
        from sdk import Models
        api = connect('http://server/api/', (uname, pswd))

        # GET
        api.GET('/packages/') # get all packages
        api.GET('/packages/1') # get first package

        # POST
        pkg = Models.Packages.Package() # create
        pkg.name = 'xobj'
        pkg.description = 'A python to xml serialization library'
        api.POST('/packages/', pkg)

        # PUT
        pkg2 = api.GET('/packages/2')
        pkg2.name = 'Package 2 Renamed'
        api.PUT('/packages/2', pkg2)

        # DELETE
        api.DELETE('/packages/2')

        # Navigate
        pkgs = api.GET('/packages/')
        for p in pkgs.package:
            print 'id: %s' % p['id']
            print 'name: %s, description: %s' % (p.name, p.description)

        # Validate
        pkg = api.GET('/packages/1')
        isinstance(pkg['id'], URLField) # is True
        pkg['id'] = 'bad id' # throws an assertion error
        pkg['id'] = 'http://validid.com/' # works
        """
        
        HEADERS = {'content-type':'text/xml'}
        
        def __init__(self):
            self.base_url = base_url.strip('/')
            self.auth = auth
            self.h = httplib2.Http()
            if auth:
                self.h.add_credentials(*auth)
        
        def GET(self, relative_url):
            url = self._relativeToAbsolute(relative_url)
            r, c = self.h.request(url, 'GET')
            return c
            
        def POST(self, relative_url, obj):
            url = self._relativeToAbsolute(relative_url)
            r, c = self.h.request(url, 'POST', headers=Client.HEADERS, body=obj.toxml())
            return c        
        
        def PUT(self, relative_url, obj):
            url = self._relativeToAbsolute(relative_url)
            r, c = self.h.request(url, 'PUT', headers=Client.HEADERS, body=obj.toxml())
            return c
            
        def DELETE(self, relative_url):
            url = self._relativeToAbsolute(relative_url)
            r, c = self.h.request(url, 'DELETE')
            return None
            
        def _relativeToAbsolute(self, relative_url):
            return urlparse.urljoin(self.base_url, relative_url)
            
    return Client()
    
    
class Fields(object):
    """
    Need to explicitly specify __name__ attr or else it
    will be listed as 'type'.
    """

    class CharField(xobj.XObj):
        __name__ = 'CharField'
            
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


class XObjMixin(object):
    """
    Only do assertion after initialization is complete
    during initialization, setattr always passed a string.
    The idea behind validation in setattr is that once
    the class is initialized, a class attribute may only
    be assigned to if the assigned value is an instance
    or an instance of a subclass of the original type.
    """
    def __setattr__(self, k, v):
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
                assert(check(v, item))
        except KeyError: # __dict__ not initialized yet
            pass
        self.__dict__[k] = v


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

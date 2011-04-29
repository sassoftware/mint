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
import sys
import inspect

MIN_ALLOWED_PYTHON_VERSION = (2, 5) # still needs to be tested on 2.5
MAX_ALLOWED_PYTHON_VERSION = (2, 7, 1)
VERSION_INFO = sys.version_info


if VERSION_INFO[0:2] < MIN_ALLOWED_PYTHON_VERSION:
    raise Exception("Must use python 2.5 or greater")
elif VERSION_INFO[0:3] > MAX_ALLOWED_PYTHON_VERSION:
    raise Exception("Untested for python versions greater than 2.7.1")
    
    
def connect(base_url, auth=None):
    """
    ie:
    base_url = 'http://server.com/api/'
    auth = (username, password)
    """
    class Client(object):
        """
        # Depending on the HTTP method, purgeNode or
        # purgeType may need to be used (ie: to remove all
        # empty references to Users before a PUT or POST)
        
        from sdk.packages import Package, TYPEMAP
        api = connect('http://server/api/', (username, passwd))

        # [GET]
        got = api.GET('packages/', TYPEMAP) # get all packages
        got_1 = api.GET('packages/1', TYPEMAP) # get first package

        # [POST]
        pkg = Package(name='xobj') # create
        pkg.description = 'A python to xml serialization library'
        # ... process package obj further ...
        doc = xobj.Document()
        doc.package = pkg
        posted = api.POST('packages/', doc, TYPEMAP)

        # [PUT]
        pkg_2 = api.GET('packages/2')
        pkg_2.package.name = 'Package 2 Renamed'
        # ... process package obj further ...
        putted = api.PUT('packages/2', pkg_2, TYPEMAP)

        # [DELETE]
        api.DELETE('packages/2')
        """
        
        HEADERS = {'content-type':'text/xml'}
        
        def __init__(self):
            self.base_url = base_url
            self.auth = auth
            self.h = httplib2.Http()
            if auth:
                self.h.add_credentials(*auth)
        
        def GET(self, relative_url, typemap):
            url = self._relativeToAbsoluteUrl(relative_url)
            r, c = self.h.request(url, 'GET')
            return xobj.parse(c, typeMap=typemap)
            
        def POST(self, relative_url, obj, typemap):
            url = self._relativeToAbsoluteUrl(relative_url)
            r, c = self.h.request(url, 'POST', headers=Client.HEADERS, body=obj.toxml())
            return xobj.parse(c, typeMap=typemap)
        
        def PUT(self, relative_url, obj, typemap):
            url = self._relativeToAbsoluteUrl(relative_url)
            r, c = self.h.request(url, 'PUT', headers=Client.HEADERS, body=obj.toxml())
            return xobj.parse(c, typeMap=typemap)
            
        def DELETE(self, relative_url):
            url = self._relativeToAbsolute(relative_url.strip('/'))
            r, c = self.h.request(url, 'DELETE')
            return None
            
        def _relativeToAbsoluteUrl(self, relative_url):
            return urlparse.urljoin(self.base_url, relative_url)
            
    return Client()


def purgeByType(root, type_name):
    if isinstance(root, list):
        for e in root:
            purgeByType(e, type_name)
    else:
        if hasattr(root, '__dict__'):
            for e_name, child in root.__dict__.items():
                if child.__class__.__name__ == 'converted_' + type_name:
                    delattr(root, e_name)
                purgeByType(child, type_name)


def purgeByNode(root, node_name):
    if isinstance(root, list):
        for e in root:
            purgeByNode(e, node_name)
    else:
        if hasattr(root, '__dict__'):
            for e_name, child in root.__dict__.items():
                if e_name == node_name:
                    delattr(root, e_name)
                purgeByNode(child, node_name)
                
                
def rebind(new, typemap):
    for tag, cls in typemap.items():
        for name, field in cls.__dict__.items():
            if isinstance(field, list):
                field = field[0]
            if inspect.isclass(field):
                if issubclass(new, field):
                    setattr(cls, name, new)
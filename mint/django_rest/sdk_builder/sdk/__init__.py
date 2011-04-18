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
        from sdk import packages
        api = connect('http://server/api/', (username, passwd))

        [GET]
        api.GET('/packages/') # get all packages
        api.GET('/packages/1') # get first package

        [POST]
        pkg = packages.Package() # create
        pkg.name = 'xobj'
        pkg.description = 'A python to xml serialization library'
        api.POST('/packages/', pkg)

        [PUT]
        pkg2 = api.GET('/packages/2')
        pkg2.name = 'Package 2 Renamed'
        api.PUT('/packages/2', pkg2)

        [DELETE]
        api.DELETE('/packages/2')

        [Validate]
        pkg = api.GET('/packages/1')
        isinstance(pkg.id, URLField) # is True
        pkg.id = 'bad id' # throws an error
        pkg.id = 'http://validid.com/' # works
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
    

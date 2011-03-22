#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

import os

from xobj import xobj

if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'mint.django_rest.settings'

class LinkElement(object):
    _xobj = xobj.XObjMetadata(
	        attributes = {
				           'href' : str,
				         },
	    )

    def __init__(self, uri, value=None):
        self.href = "%(uri)s" % vars()
        self._xobj.text = value
        
    def __repr__(self):
        return unicode(self._value)
        
class IDElement(object):
    _xobj = xobj.XObjMetadata(
	        attributes = {
				           'id' : str,
				         },
	    )

    def __init__(self, uri):
        self.id = "%(uri)s" % vars()
        
    def __repr__(self):
        return unicode(self.id)  

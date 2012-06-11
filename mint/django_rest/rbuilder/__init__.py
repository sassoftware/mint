#
from xobj import xobj

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

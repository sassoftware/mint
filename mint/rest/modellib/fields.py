
_fieldRegistry = {}
def registerField(field):
    count = len(_fieldRegistry)
    _fieldRegistry[id(field)] = count 

def _sortRegisteredFields(fields):
    fieldNames = [ x[0] for x in fields.iteritems() 
                   if id(x[1]) in _fieldRegistry ]
    return sorted(fieldNames, 
                  key=lambda x: _fieldRegistry[id(fields[x])])

class Field(object):
    editable = True
    def __init__(self, default=None, required=False, visibility=None,
                 editable=None):
        registerField(self)
        self.default = default
        self.required = required
        self.visibility = visibility
        if editable is not None:
            self.editable = editable

class IntegerField(Field):
    pass

class CharField(Field):
    pass

class BooleanField(Field):
    pass

class UrlField(Field):
    editable = False
    def __init__(self, location, urlParameters, *args, **kw):
        Field.__init__(self, *args, **kw)
        self.location = location
        if isinstance(urlParameters, str):
            urlParameters = [urlParameters]
        if urlParameters is None:
            urlParameters = []
        self.urlParameters = urlParameters

class AbsoluteUrlField(Field):
    editable = False

class EmailField(Field):
    pass

class DateTimeField(Field):
    pass

class ListField(Field):
    listType = list
    def __init__(self, valueClass, itemName, default=None, *args, **kw):
        self.valueClass = valueClass
        self.itemName = itemName
        if default is None:
            default = self.listType()
        Field.__init__(self, default=default, *args, **kw)

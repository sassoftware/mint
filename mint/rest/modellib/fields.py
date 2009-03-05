
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
                 editable=None, isAttribute=False, isText=False,
                 displayName=None):
        registerField(self)
        self.default = default
        self.required = required
        self.visibility = visibility
        self.isAttribute = isAttribute
        self.isText = isText
        self.displayName = displayName
        if editable is not None:
            self.editable = editable

class IntegerField(Field):
    pass

class CharField(Field):
    pass

class BooleanField(Field):
    pass

class CalculatedField(Field):
    def getValue(self, controller, request, class_, parent, value):
        return value

class UrlField(CalculatedField):
    def __init__(self, location, urlParameters, *args, **kw):
        query = kw.pop('query', None)

        CalculatedField.__init__(self, *args, **kw)
        self.location = location
        if isinstance(urlParameters, str):
            urlParameters = [urlParameters]
        if urlParameters is None:
            urlParameters = []
        self.urlParameters = urlParameters
        self.query = query

    def getValue(self, controller, request, class_, parent, value):
        instance = class_()
        values = [ getattr(parent, x) for x in self.urlParameters]
        if None in values:
            return None
        values = [str(x) for x in values ]
        instance.href = controller.url(request, 
                                            self.location, *values)
        if self.trailingSlash:
            instance.href += '/'
        if self.query:
            instance.href += '?' + self.query % parent.__dict__

        if value:
            instance._xobj.text = str(value)
        return instance


class ModelField(Field):
    def __init__(self, model, *args, **kw):
        Field.__init__(self, *args, **kw)
        self.model = model
    

class AbsoluteUrlField(Field):
    editable = False

class EmailField(Field):
    pass

class DateTimeField(Field):
    pass

class VersionField(Field):
    pass

class FlavorField(Field):
    pass

class ListField(Field):
    listType = list
    def __init__(self, valueClass, default=None, *args, **kw):
        self.valueClass = valueClass
        if default is None:
            default = self.listType()
        Field.__init__(self, default=default, *args, **kw)

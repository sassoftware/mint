#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
from mint.rest import modellib

class Field(object):
    editable = True
    def __init__(self, default=None, required=False, visibility=None,
                 editable=None, isAttribute=False, isText=False,
                 displayName=None):
        self.displayName = displayName
        self.default = default
        self.required = required
        self.visibility = visibility
        self.isAttribute = isAttribute
        self.isText = isText
        modellib.registerField(self)
        if editable is not None:
            self.editable = editable

    def __del__(self):
        modellib.deregisterField(self)

    def isList(self):
        return False

    def hasModel(self):
        return bool(self.getModel())

    def getModel(self):
        return None

    def getModelInstance(self, value, parent, context):
        return None

    def valueToString(self, value, parent, context):
        if value is not None:
            return str(value)

    def valueFromString(self, value):
        return value
        

class IntegerField(Field):
    def valueFromString(self, value):
        return int(value)

class FloatField(Field):
    def valueFromString(self, value):
        return float(value)

class CharField(Field):
    pass

class BooleanField(Field):
    def valueFromString(self, value):
        if isinstance(value, (int, bool)):
            return bool(value)
        value = value.lower()
        if value in ('true', '1'):
            return True
        elif value in ('false', '0'):
            return False
        else:
            raise ParseError(value)

    def valueToString(self, value, parent, context):
        if value is None:
            return
        if value:
            return 'true'
        return 'false'

class CalculatedField(Field):
    #TODO : add errors for trying to pass this in.
    pass
    
class UrlField(CalculatedField):

    class _Url(modellib.Model):
        href = CharField(isAttribute=True)
        value = CharField(isText=True)

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

    def getModel(self):
        return self._Url

    def _getUrl(self, parent, context):
        values = [ getattr(parent, x) for x in self.urlParameters]
        if None in values:
            return None
        values = [str(x) for x in values ]
        href = context.controller.url(context.request, self.location, *values)
        if self.query:
            href += '?' + self.query % parent.__dict__
        return href

    def getModelInstance(self, value, parent, context):
        modelClass = self.getModel()
        return modelClass(href=self._getUrl(parent, context), 
                          value=value)


class ModelField(Field):

    def __init__(self, model, *args, **kw):
        Field.__init__(self, *args, **kw)
        self.model = model

    def getModel(self):
        return self.model

    def getModelInstance(self, value, parent, context):
        return value
    

class AbsoluteUrlField(CalculatedField):
    
    def valueToString(self, value, parent, context):
        return context.controller.url(context.request,
                                      *parent.get_absolute_url())

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
    def __init__(self, modelClass, default=None, *args, **kw):
        self.valueClass = modelClass
        if default is None:
            default = self.listType()
        Field.__init__(self, default=default, *args, **kw)

    def getModel(self):
        # currently can only have lists of models, not lists of
        # any type of field.
        return self.valueClass

    def getModelInstance(self, value, parent, context):
        return value
    
    def isList(self):
        return True

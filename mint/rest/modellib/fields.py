#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
from conary import versions
from conary.deps import deps

from mint.rest import modellib
from mint.rest.modellib import Field

class IntegerField(Field):
    def _valueFromString(self, value):
        return int(value)

class FloatField(Field):
    def _valueFromString(self, value):
        return float(value)

class CharField(Field):
    def _valueToString(self, value, parent, context):
        if isinstance(value, unicode):
            return value
        else:
            return value.decode('utf8', 'replace')


class BooleanField(Field):
    def _valueFromString(self, value):
        if isinstance(value, (int, bool)):
            return bool(value)
        value = value.lower()
        if value in ('true', '1'):
            return True
        elif value in ('false', '0'):
            return False
        else:
            raise ParseError(value)

    def _valueToString(self, value, parent, context):
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
    handleNone = True
    
    def _valueToString(self, value, parent, context):
        return context.controller.url(context.request,
                                      *parent.get_absolute_url())

class EmailField(Field):
    pass

class DateTimeField(Field):
    pass

class VersionField(Field):
    def _valueFromString(self, value):
        try:
            return versions.VersionFromString(value)
        except ValueError:
            return versions.ThawVersion(value)


class FlavorField(Field):
    def _valueFromString(self, value):
        try:
            return deps.parseFlavor(value)
        except deps.ParseError:
            return deps.ThawFlavor(value)


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

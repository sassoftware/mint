from mint.rest.modellib.fields import *
from mint.rest.modellib import *

class XMLFormatter(object):
    _modelClassCache = {}

    def __init__(self, controller):
        self.controller = controller

    def fromText(self, request, cls, xml):
        self.request = request
        xobjClass = self.getXObjClass(cls)
        className = xobjClass.__name__
        obj = xobj.parse(xml, typeMap={className : xobjClass})
        xobjObject = getattr(obj, className)
        return self.fromXObjObject(cls, xobjObject)

    def toText(self, request, instance):
        self.request = request
        xobjObject = self.getXObjObject(instance.__class__, instance)
        return xobj.toxml(xobjObject, xobjObject.__class__.__name__)

    def getXObjClass(self, cls):
        if issubclass(cls, Field):
            return self.getFieldXObjClass(cls)
        elif issubclass(cls, Model):
            return self.getModelXObjClass(cls)

    def getXObjObject(self, cls, value, parent=None):
        if isinstance(cls, Field):
            return self.getFieldXObjObject(cls, value, parent)
        elif issubclass(cls, Model):
            return self.getModelXObjObject(cls, value, parent)

    def fromXObjObject(self, cls, xobjObject):
        if isinstance(cls, Field):
            return self.fromFieldXObjObject(cls, xobjObject)
        elif issubclass(cls, Model):
            return self.fromModelXObjObject(cls, xobjObject)

    def fromModelXObjObject(self, modelClass, xobjObject):
        attrs = {}
        for fieldName in modelClass._fields:
            field = getattr(modelClass, fieldName)
            if hasattr(field, 'itemName'):
                itemName = field.itemName
            else:
                itemName = fieldName
            value = getattr(xobjObject, itemName)
            realValue = self.fromXObjObject(field, value)
            attrs[fieldName] = realValue
        return modelClass(**attrs)

    def fromFieldXObjObject(self, field, fieldValue):
        if fieldValue is None:
            return None
        if isinstance(field, BooleanField):
            return bool(fieldValue)
        if isinstance(field, ListField):
            return [ self.fromXObjObject(field.valueClass, x) 
                                         for x in fieldValue ]
        return fieldValue

    def getModelXObjClass(self, modelClass):
        if modelClass in self._modelClassCache:
            return self._modelClassCache[modelClass]
        className = modelClass._meta.name
        attrs = {'module' : __name__ }
        for fieldName in modelClass._fields:
            field = getattr(modelClass, fieldName)
            if hasattr(field, 'itemName'):
                fieldName = field.itemName
            attrs[fieldName] = self.getFieldXObjClass(field)
        # orders elements
        attrs['_xobj'] = xobj.XObjMetadata(elements = modelClass._elements,
                                           attributes = modelClass._attributes)
        xobjClass = type.__new__(type, className, xobj.XObj.__mro__, attrs)
        self._modelClassCache[modelClass] = xobjClass
        return xobjClass

    def getModelXObjObject(self, modelClass, modelObject, parent):
        instance = self.getModelXObjClass(modelClass)()
        for fieldName in modelClass._fields:
            field = getattr(modelClass, fieldName)
            value = getattr(modelObject, fieldName)
            childObject = self.getXObjObject(field, value, modelObject)
            if hasattr(field, 'itemName'):
                fieldName = field.itemName
            setattr(instance, fieldName, childObject)
        return instance

    def getFieldXObjClass(self, field):
        if isinstance(field, ListField):
            return [ self.getXObjClass(field.valueClass) ]
        elif isinstance(field, (BooleanField, IntegerField)):
            return int
        elif isinstance(field, UrlField):
            attrs = {}
            attrs['href'] = str
            attrs['_xobj'] = xobj.XObjMetadata(attributes = ['href'])
            xobjClass = type.__new__(type, 'XobjUrl', 
                                     xobj.XObj.__mro__, attrs)
            return xobjClass
        else:
            return str

    def getFieldXObjObject(self, field, value, parent):
        if isinstance(field, AbsoluteUrlField):
            return self.controller.url(self.request, *parent.get_absolute_url())
        elif isinstance(field, UrlField):
            instance = self.getFieldXObjClass(field)()
            values = [ getattr(parent, x) for x in field.urlParameters]
            if None in values:
                return None
            instance.href = self.controller.url(self.request, 
                                                field.location, *values)
            if value:
                instance._xobj.text = value
            return instance
        elif value is None:
            return None
        elif isinstance(field, ListField):
            return [ self.getXObjObject(field.valueClass, x, parent) 
                                        for x in value ]
        elif isinstance(field, BooleanField):
            return int(value)
        return value

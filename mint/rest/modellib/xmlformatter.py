#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.modellib import fields as f
from mint.rest.modellib import Model, xobj

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
        if issubclass(cls, f.Field):
            return self.getFieldXObjClass(cls)
        elif issubclass(cls, Model):
            return self.getModelXObjClass(cls)

    def getXObjObject(self, cls, value, parent=None):
        if isinstance(cls, f.Field):
            return self.getFieldXObjObject(cls, value, parent)
        elif issubclass(cls, Model):
            return self.getModelXObjObject(cls, value, parent)

    def fromXObjObject(self, cls, xobjObject):
        if isinstance(cls, f.Field):
            return self.fromFieldXObjObject(cls, xobjObject)
        elif issubclass(cls, Model):
            return self.fromModelXObjObject(cls, xobjObject)

    def fromModelXObjObject(self, modelClass, xobjObject):
        attrs = {}
        for fieldName in modelClass._fields:
            field = getattr(modelClass, fieldName)
            if hasattr(field, 'displayName') and field.displayName:
                itemName = field.displayName
            else:
                itemName = fieldName
            value = getattr(xobjObject, itemName)
            realValue = self.fromXObjObject(field, value)
            attrs[fieldName] = realValue
        return modelClass(**attrs)

    def fromFieldXObjObject(self, field, fieldValue):
        if fieldValue is None:
            return None
        if isinstance(field, f.BooleanField):
            return bool(fieldValue)
        if isinstance(field, f.ListField):
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
            if hasattr(field, 'displayName') and field.displayName:
                fieldName = field.displayName
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
            if hasattr(field, 'displayName') and field.displayName:
                fieldName = field.displayName
            if field.isText:
                instance._xobj.text = childObject
            else:
                setattr(instance, fieldName, childObject)
        return instance

    def getFieldXObjClass(self, field):
        if isinstance(field, f.ListField):
            return [ self.getXObjClass(field.valueClass) ]
        elif isinstance(field, (f.BooleanField, f.IntegerField)):
            return int
        elif isinstance(field, (f.UrlField, f.CalculatedField)):
            attrs = {}
            attrs['href'] = str
            attrs['_xobj'] = xobj.XObjMetadata(attributes = ['href'])
            xobjClass = type.__new__(type, 'XobjUrl', 
                                     xobj.XObj.__mro__, attrs)
            return xobjClass
        elif isinstance(field, f.ModelField):
            return self.getModelXObjClass(field.model)
        else:
            return str

    def getFieldXObjObject(self, field, value, parent):
        if isinstance(field, f.AbsoluteUrlField):
            return self.controller.url(self.request, *parent.get_absolute_url())
        elif isinstance(field, f.CalculatedField):
            class_ = self.getFieldXObjClass(field)
            return field.getValue(self.controller, self.request, 
                                  class_, parent, value)
        elif value is None:
            return None
        elif isinstance(field, f.ListField):
            return [ self.getXObjObject(field.valueClass, x, parent) 
                                        for x in value ]
        elif isinstance(field, f.BooleanField):
            return int(value)
        elif isinstance(field, f.ModelField):
            return self.getModelXObjObject(field.model, value, parent)
        return str(value)

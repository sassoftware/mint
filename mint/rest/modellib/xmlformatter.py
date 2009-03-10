#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
from xobj import xobj

from mint.rest import modellib
from mint.rest.modellib import fields

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
        if issubclass(cls, fields.Field):
            return self.getFieldXObjClass(cls)
        elif issubclass(cls, modellib.Model):
            return self.getModelXObjClass(cls)

    def getXObjObject(self, cls, value, parent=None):
        if isinstance(cls, fields.Field):
            return self.getFieldXObjObject(cls, value, parent)
        elif issubclass(cls, modellib.Model):
            return self.getModelXObjObject(cls, value, parent)

    def fromXObjObject(self, cls, xobjObject):
        if isinstance(cls, fields.Field):
            return self.fromFieldXObjObject(cls, xobjObject)
        elif issubclass(cls, modellib.Model):
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
        if isinstance(field, fields.BooleanField):
            return bool(fieldValue)
        if isinstance(field, fields.ListField):
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
        if isinstance(field, fields.ListField):
            return [ self.getXObjClass(field.valueClass) ]
        elif isinstance(field, (fields.BooleanField, fields.IntegerField)):
            return int
        elif isinstance(field, (fields.UrlField, fields.CalculatedField)):
            attrs = {}
            attrs['href'] = str
            attrs['_xobj'] = xobj.XObjMetadata(attributes = ['href'])
            xobjClass = type.__new__(type, 'XobjUrl', 
                                     xobj.XObj.__mro__, attrs)
            return xobjClass
        elif isinstance(field, fields.ModelField):
            return self.getModelXObjClass(field.model)
        else:
            return str

    def getFieldXObjObject(self, field, value, parent):
        if isinstance(field, fields.AbsoluteUrlField):
            return self.controller.url(self.request, *parent.get_absolute_url())
        elif isinstance(field, fields.CalculatedField):
            class_ = self.getFieldXObjClass(field)
            return field.getValue(self.controller, self.request, 
                                  class_, parent, value)
        elif value is None:
            return None
        elif isinstance(field, fields.ListField):
            return [ self.getXObjObject(field.valueClass, x, parent) 
                                        for x in value ]
        elif isinstance(field, fields.BooleanField):
            return int(value)
        elif isinstance(field, fields.ModelField):
            return self.getModelXObjObject(field.model, value, parent)
        return str(value)

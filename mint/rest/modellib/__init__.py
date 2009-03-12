#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from xobj import xobj

from mint.rest.modellib import options

_fieldRegistry = {}
def registerField(field):
    count = len(_fieldRegistry)
    _fieldRegistry[id(field)] = count 

def deregisterField(field):
    try:
        _fieldRegistry.remove(id(field))
    except:
        pass

def _sortRegisteredFields(fields):
    fieldNames = [ x[0] for x in fields.iteritems() 
                   if id(x[1]) in _fieldRegistry ]
    return sorted(fieldNames, 
                  key=lambda x: _fieldRegistry[id(fields[x])])


class ModelMeta(type):
    def __new__(mcs, name, bases, attrs):
        new_class = type.__new__(mcs, name, bases, attrs)
        new_class._fields =  _sortRegisteredFields(attrs) 
        for fieldName in new_class._fields:
            field = attrs[fieldName]
            if not field.displayName:
                field.displayName = fieldName
        new_class._attributes = [ attrs[x].displayName 
                                  for x in new_class._fields 
                                  if attrs[x].isAttribute ]
        new_class._elements = [ attrs[x].displayName 
                                  for x in new_class._fields 
                                  if not attrs[x].isAttribute
                                     and not attrs[x].isText ]
        new_class._text =  [ x for x in new_class._fields 
                             if attrs[x].isText ]
        new_class._meta = options.Options(new_class, attrs.pop('Meta', None))
        return new_class

class Model(object):
    """
    Model objects are intended to be objects with structured content.
    The object's structure is defined though class-level variables that are a
    subclass of the fields.Field class.

    This allows one to do:

    class MyField(fields.Field):
        pass

    class YourField(fields.Field):
        pass

    class M(Model):
        myField = MyField()
        yourField = YourField()

    m = M(myField = 'a', yourField = 'b')
    """
    __metaclass__ = ModelMeta

    def __init__(self, *args, **kw):
        fields = list(self._fields)
        cls = self.__class__

        if len(args) > len(self._fields):
            raise TypeError(
                '%s() takes at most %s arguments (%s given)'  % (cls.__name__, 
                                                        len(fields), len(args)))

        for (arg, field) in zip(args, fields):
            setattr(self, field, arg)
        kwfields = set(fields[len(args):])
        for kwarg, value in kw.items():
            className = cls.__name__
            if kwarg not in kwfields:
                if kwarg in fields:
                    raise TypeError('%s() got multiple values for keyword argument %r' % (className, kwarg))
                else:
                    raise TypeError('%s() got an unexpected keyword argument %r' % (className, kwarg))
            kwfields.remove(kwarg)
            setattr(self, kwarg, value)
        for fieldName in kwfields:
            field = getattr(cls, fieldName)
            if field.required:
                raise TypeError('%s is a required parameter for %s()' % (fieldName, cls.__name__))
            if isinstance(field.default, list):
                default = list(field.default)
            else:
                default = field.default
            setattr(self, fieldName, field.default)

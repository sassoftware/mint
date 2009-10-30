#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from conary.dbstore import sqllib
from xobj import xobj

from mint.rest.modellib import options

_fieldRegistry = {}
def _registerField(field):
    count = len(_fieldRegistry)
    _fieldRegistry[id(field)] = count 

def _deregisterField(field):
    try:
        _fieldRegistry.remove(id(field))
    except:
        pass

def _sortRegisteredFields(fields):
    fieldNames = [ x[0] for x in fields.iteritems() 
                   if isinstance(x[1], Field) and id(x[1]) in _fieldRegistry ]
    return sorted(fieldNames, 
                  key=lambda x: _fieldRegistry[id(fields[x])])


class Field(object):
    editable = True
    default = None
    handleNone = False
    def __init__(self, default=None, required=False, visibility=None,
                 editable=None, isAttribute=False, isText=False,
                 displayName=None, display=True):
        self.displayName = displayName
        if default is not None:
            self.default = default
        self.required = required
        self.visibility = visibility
        self.isAttribute = isAttribute
        self.isText = isText
        self.display = display
        _registerField(self)
        if editable is not None:
            self.editable = editable

    def __del__(self):
        _deregisterField(self)

    def isList(self):
        return False

    def hasModel(self):
        return bool(self.getModel())

    def getModel(self):
        return None

    def getModelInstance(self, value, parent, context):
        return None

    def valueToString(self, value, parent, context):
        if value is None and not self.handleNone:
            return None
        return self._valueToString(value, parent, context)

    def _valueToString(self, value, parent, context):
        return str(value)

    def valueFromString(self, value):
        if value is None and not self.handleNone:
            return None
        return self._valueFromString(value)

    def _valueFromString(self, value):
        return value


class ModelMeta(type):
    def __new__(mcs, name, bases, attrs):
        new_class = type.__new__(mcs, name, bases, attrs)
        all_attrs = {}
        for superclass in bases:
            all_attrs.update((x, getattr(new_class, x)) for x in
                                  getattr(superclass, '_fields', []))
        all_attrs.update(attrs)
        new_class._fields =  _sortRegisteredFields(all_attrs) 
        for fieldName in new_class._fields:
            if fieldName not in attrs:
                continue
            field = attrs[fieldName]
            if not field.displayName:
                field.displayName = fieldName
        new_class._attributes = [ all_attrs[x].displayName 
                                  for x in new_class._fields 
                                  if all_attrs[x].isAttribute ]
        new_class._elements = [ all_attrs[x].displayName 
                                  for x in new_class._fields 
                                  if not all_attrs[x].isAttribute
                                     and not all_attrs[x].isText ]
        new_class._text =  [ x for x in new_class._fields 
                             if all_attrs[x].isText ]
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

    def __init__(self, *args, **kwargs):
        fields = list(self._fields)
        cls = self.__class__
        className = self.__class__

        if args and isinstance(args[0], (dict, sqllib.Row)):
            # A dictionary as a single, positional argument.
            assert not kwargs and len(args) == 1
            kwargs = args[0]
            args = []

        args = list(args)
        if isinstance(kwargs, sqllib.Row):
            kwargs = sqllib.CaselessDict(zip(kwargs.fields, kwargs.data))
        else:
            kwargs = sqllib.CaselessDict(kwargs)

        if len(args) > len(self._fields):
            raise TypeError(
                '%s() takes at most %s arguments (%s given)' % (cls.__name__, 
                                                        len(fields), len(args)))

        for fieldName in fields:
            field = getattr(cls, fieldName)
            if args:
                if fieldName in kwargs:
                    raise TypeError('%s() got multiple values for keyword '
                            'argument %r' % (className, fieldName))
                value = args.pop(0)
            elif fieldName in kwargs:
                value = kwargs.pop(fieldName)
            elif field.required:
                raise TypeError('%s is a required parameter for %s()'
                        % (fieldName, className))
            elif isinstance(field.default, list):
                value = list(field.default)
            else:
                value = field.default

            setattr(self, fieldName, value)

        assert not args # checked above
        if kwargs:
            raise TypeError('%s() got an unexpected keyword argument %r'
                    % (className, sorted(kwargs)[0]))

    def __setattr__(self, attr, value):
        fields = list(self._fields)
        lowerFields = [f.lower() for f in fields]

        if attr.lower() in  lowerFields:
            index = lowerFields.index(attr.lower())
            fieldName = fields[index]
            object.__setattr__(self, fieldName, value)
        else:
            object.__setattr__(self, attr, value)

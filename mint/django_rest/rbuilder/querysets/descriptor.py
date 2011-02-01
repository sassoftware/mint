#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.db import models
from xobj import xobj

from mint.django_rest.rbuilder.inventory import models as inventorymodels
from mint.django_rest.rbuilder import modellib

class FieldDescriptor(object):
    _xobj = xobj.XObjMetadata(tag='field_descriptor',
        elements=[
            'field_label', 'field_key', 'value_type',
            'operator_choices', 'value_options'])

class FilterDescriptor(object):
    _xobj = xobj.XObjMetadata(tag='filter_descriptor',
        elements=['field_descriptors'])

    def to_xml(self, request=None, values=None):
        return xobj.toxml(self)

class OperatorChoices(object):
    _xobj = xobj.XObjMetadata(tag='operator_choices')

class OperatorChoice(object):
    _xobj = xobj.XObjMetadata(tag='operator_choice')

    def __init__(self, key, label):
        self.key = key
        self.label = label

class ValueOptions(object):
    _xobj = xobj.XObjMetadata(tag='value_options')

def getFieldValueType(field):
    if isinstance(field, models.IntegerField):
        return 'int'
    if isinstance(field, models.BooleanField):
        return 'bool'
    if isinstance(field, models.DateTimeField):
        return 'datetime'

    # Default to str
    return 'str'

def getFieldValueOptions(field):
    vo = ValueOptions()
    vo.options = []
    if field._choices:
        for key, value in field._choices:
            vo.options.append(key)
    return vo

def allOperatorChoices():
    operatorChoices = OperatorChoices()
    operatorChoices.choices = []
    operators = [o for o in modellib.operatorMap
        if o not in ('IS_NULL',)]
    for operator in operators:
        operatorChoices.choices.append(OperatorChoice(operator, operator))
    return operatorChoices

def strOperatorChoices():
    operatorChoices = OperatorChoices()
    operatorChoices.choices = []
    operators = [o for o in modellib.operatorMap
        if o not in ('LESS_THAN', 'LESS_THAN_OR_EQUAL', 'GREATER_THAN',
            'GREATER_THAN_OR_EQUAL', 'IS_NULL')]
    for operator in operators:
        operatorChoices.choices.append(OperatorChoice(operator, operator))
    return operatorChoices

def boolOperatorChoices():
    operatorChoices = OperatorChoices()
    operatorChoices.choices = []
    for operator in ['EQUAL', 'NOT_EQUAL']:
        operatorChoices.choices.append(OperatorChoice(operator, operator))
    return operatorChoices

def getFieldOperatorChoices(field):
    if isinstance(field, models.IntegerField):
        operatorChoices = allOperatorChoices()
    if isinstance(field, models.BooleanField):
        operatorChoices = allOperatorChoices()

    # Default to str
    operatorChoices = strOperatorChoices()

    if field.null:
        operatorChoices.choices.append(OperatorChoice('IS_NULL', 'IS_NULL'))

    return operatorChoices

def getFieldDescriptors(field, prefix=None):
    fds = []
    if isinstance(field, models.ForeignKey):
        for f in field.rel.to._meta.fields:
            if prefix:
                _prefix = '%s.%s' % (prefix, field.name)
            else:
                _prefix = field.name
            _fds = getFieldDescriptors(f, _prefix)
            [fds.append(_fd) for _fd in _fds]
    else:
        fd = FieldDescriptor()
        if prefix:
            key = '%s.%s' % (prefix, field.name)
        else:
            key = field.name
        fd.field_label = field.name
        fd.field_key = key
        fd.value_type = getFieldValueType(field)
        fd.value_options = getFieldValueOptions(field)
        fd.operator_choices = getFieldOperatorChoices(field)
        fds.append(fd)
    return fds

def getFilterDescriptor(model):
    fd = FilterDescriptor()
    fd.field_descriptors = []
    for field in model._meta.fields:
        _fds = getFieldDescriptors(field)
        [fd.field_descriptors.append(_fd) for _fd in _fds]
    return fd


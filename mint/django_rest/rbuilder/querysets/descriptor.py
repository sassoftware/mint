#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.db import models
from django.db.models import related
from xobj import xobj

from mint.django_rest.rbuilder import modellib

class FieldDescriptor(object):
    _xobj = xobj.XObjMetadata(tag='field_descriptor',
        elements=[
            'field_label', 'field_key', 'value_type',
            'operator_choices', 'value_options'])

class FieldDescriptors(object):
    _xobj = xobj.XObjMetadata(tag='field_descriptors')

class FilterDescriptor(modellib.XObjIdModel):
    _xobj = xobj.XObjMetadata(tag='filter_descriptor',
        elements=['field_descriptors'],
        attributes={'id':str})
    view_name = 'QuerySetFilterDescriptor'

    def serialize(self, *args, **kwargs):
        self.id = self.get_absolute_url(*args, **kwargs)
        return self

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
    operators = [modellib.operatorMap[o] for o in modellib.operatorMap
        if o not in ('IS_NULL', None)]
    for operator in operators:
        operatorChoices.choices.append(OperatorChoice(operator.filterTerm, 
            operator.description))
    return operatorChoices

def strOperatorChoices():
    operatorChoices = OperatorChoices()
    operatorChoices.choices = []
    operators = [modellib.operatorMap[o] for o in modellib.operatorMap
        if o not in ('LESS_THAN', 'LESS_THAN_OR_EQUAL', 'GREATER_THAN',
            'GREATER_THAN_OR_EQUAL', 'IS_NULL', None)]
    for operator in operators:
        operatorChoices.choices.append(OperatorChoice(operator.filterTerm, 
            operator.description))
    return operatorChoices

def boolOperatorChoices():
    operatorChoices = OperatorChoices()
    operatorChoices.choices = []
    operators = [modellib.operatorMap['EQUAL'], modellib.operatorMap['NOT_EQUAL']]
    for operator in operators:
        operatorChoices.choices.append(OperatorChoice(operator.filterTerm, 
            operator.description))
    return operatorChoices

def getFieldOperatorChoices(field):
    if isinstance(field, models.IntegerField):
        operatorChoices = allOperatorChoices()
    if isinstance(field, models.BooleanField):
        operatorChoices = boolOperatorChoices()

    # Default to str
    operatorChoices = strOperatorChoices()

    if field.null:
        operator = modellib.operatorMap['IS_NULL']
        operatorChoices.choices.append(OperatorChoice(operator.filterTerm,
            operator.description))

    return operatorChoices

def getFieldDescriptors(field, prefix=None, processedModels=[]):
    fds = []
    # Not using get_all_field_names in this function b/c of infinite recursion
    if isinstance(field, models.ForeignKey) or \
       isinstance(field, models.ManyToManyField):
        # Skip the model if it has already been processed, as long as it is
        # not directly off the root model (prefix is not None).
        if field.rel.to in processedModels and prefix is not None:
            return fds
        for f in field.rel.to._meta.fields:
            if prefix:
                _prefix = '%s.%s' % (prefix, field.name)
            else:
                _prefix = field.name
            _fds = getFieldDescriptors(f, _prefix, processedModels)
            [fds.append(_fd) for _fd in _fds]
        processedModels.append(field.rel.to)
    elif isinstance(field, related.RelatedObject):
        if field.model() in processedModels and prefix is not None:
            return fds
        for f in field.model()._meta.fields:
            if prefix:
                _prefix = '%s.%s' % (prefix, field.get_accessor_name())
            else:
                _prefix = field.get_accessor_name()
            _fds = getFieldDescriptors(f, _prefix, processedModels)
            [fds.append(_fd) for _fd in _fds]
        processedModels.append(field.model())
    else:   
        fd = FieldDescriptor()
        if prefix:
            key = '%s.%s' % (prefix, field.name)
        else:
            key = field.name
        fd.field_label = getattr(field, 'docstring', field.name)
        fd.field_key = key
        fd.value_type = getFieldValueType(field)
        fd.value_options = getFieldValueOptions(field)
        fd.operator_choices = getFieldOperatorChoices(field)
        fds.append(fd)
    return fds


def getFilterDescriptor(model):
    processedModels = []
    processedModels.append(model)
    fd = FilterDescriptor()
    fd.field_descriptors = FieldDescriptors()
    fd.field_descriptors.descriptors = []
    fieldNames = model._meta.get_all_field_names()
    for fieldName in fieldNames:
        field = model._meta.get_field_by_name(fieldName)[0]
        _fds = getFieldDescriptors(field, None, processedModels)
        [fd.field_descriptors.descriptors.append(_fd) for _fd in _fds]
    return fd


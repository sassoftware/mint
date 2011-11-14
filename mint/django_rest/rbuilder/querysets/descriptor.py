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

# because we don't want to include relations of the same
# type multiple times, we do not offer up some items
# in the filter descriptor.  This does NOT mean
# they can't be added via REST.  Only removed
# as it would be confusing since we don't include
# the actual field name in the dropdown.
EXCLUDE_FIELD_NAMES = [ 'modified_by', 'modified_date']

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

    def operator_sorter(one, two):
        # put negative choices to the bottom of the list
        if one.filterTerm.startswith("NOT") and not two.filterTerm.startswith("NOT"):
            return 1
        if two.filterTerm.startswith("NOT") and not one.filterTerm.startswith("NOT"):
            return -1
        return cmp(one.description, two.description)
    operators.sort(cmp=operator_sorter)

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

    operatorChoices = None
    if isinstance(field, models.IntegerField) or isinstance(field, models.AutoField):
        operatorChoices = allOperatorChoices()
    elif isinstance(field, models.BooleanField):
        operatorChoices = boolOperatorChoices()
    else:
        operatorChoices = strOperatorChoices()

    if field.null:
        operator = modellib.operatorMap['IS_NULL']
        operatorChoices.choices.append(OperatorChoice(operator.filterTerm,
            operator.description))

    return operatorChoices

def getFieldDescriptors(field, prefix=None, processedModels=[], depth=0):
    fds = []
    # Not using get_all_field_names in this function b/c of infinite recursion

    if depth > 1:
        # try not to suck down all of our models into crazy-land
        # we may also want to require that any associations more than X away
        # have a shortname to get in the list.  TODO: some concept of advanced
        # option is on sed's eventual feature list.
        return fds

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
            _fds = getFieldDescriptors(f, _prefix, processedModels, depth+1)
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
            _fds = getFieldDescriptors(f, _prefix, processedModels, depth+1)
            [fds.append(_fd) for _fd in _fds]
        processedModels.append(field.model())
    else:
        fd = FieldDescriptor()
        if prefix:
            key = '%s.%s' % (prefix, field.name)
        else:
            key = field.name
        fd.field_label = getattr(field, 'shortname', None)
        fd.field_key = key
        if fd.field_label is not None and not fd.field_key.startswith("_"):
            fd.value_type = getFieldValueType(field)
            fd.value_options = getFieldValueOptions(field)
            fd.operator_choices = getFieldOperatorChoices(field)
            fds.append(fd)
    return fds

def getFilterDescriptor(model, queryset):
    processedModels = []
    processedModels.append(model)
    fd = FilterDescriptor()
    fd.field_descriptors = FieldDescriptors()
    fd.field_descriptors.descriptors = []
    fieldNames = model._meta.get_all_field_names()
    fieldNames.sort()
    for fieldName in fieldNames:
        if fieldName in EXCLUDE_FIELD_NAMES:
            continue 
        field = model._meta.get_field_by_name(fieldName)[0]
        _fds = getFieldDescriptors(field, None, processedModels)
        [fd.field_descriptors.descriptors.append(_fd) for _fd in _fds]

    # uniquify values as some systems resolve to themselves and so forth
    list = fd.field_descriptors.descriptors
    fds_by_name = {}
    for x in list:
        if x is None or x.field_label is None:
            continue
        if fds_by_name.has_key(x.field_label):
            old = fds_by_name[x.field_label]
            if len(x.field_key) < len(old.field_key):
                fds_by_name[x.field_label] = x
        else:
            fds_by_name[x.field_label] = x
    values = fds_by_name.values()
    values.sort(key = lambda x: str.lower(x.field_label))
    fd.field_descriptors.descriptors = values

    def filter_sort(one, two):
       '''
       Sort alphabetically except that the most important item for each filter
       type must rise to the top
       '''
       if one == two:
           return 0
       search_key = queryset.searchKey()
       if one.field_label == search_key:
           return -1
       if two.field_label == search_key:
           return 1
       return cmp(one.field_label, two.field_label)

    fd.field_descriptors.descriptors.sort(cmp=filter_sort)
    return fd


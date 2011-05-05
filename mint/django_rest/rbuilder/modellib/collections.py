#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

import sys

from django.db import models
from django.db.models import fields
from django.db.models import Q
from django.conf import settings
from django.core import exceptions
from django.core import paginator

from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder.modellib import XObjIdModel

from xobj import xobj

class CollectionPaginator(paginator.Paginator):
    def validate_number(self, number):
        if number == 0:
            return number
        else:
            return paginator.Paginator.validate_number(self, number)

    def page(self, number):
        number = self.validate_number(number)
        bottom = number * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return CollectionPage(self.object_list[bottom:top], number, self)

class CollectionPage(paginator.Page):
    def start_index(self):
        # Special case, return zero if no items.
        if self.paginator.count == 0:
            return 0
        return (self.paginator.per_page * self.number)

    def end_index(self):
        """
        Calculates the end index of this page.  Accounts for the fact that the
        last page (or first page if there's only one page) may not be a full
        page.
        """
        endIndex = self.paginator.per_page * (self.number + 1) - 1
        if self.paginator.count == 0:
            return 0
        elif endIndex > self.paginator.count:
            return self.paginator.count - 1
        else:
            return endIndex

    def has_next(self):
        return (self.number + 1) < self.paginator.num_pages

    def has_previous(self):
        return self.number > 0

filterTermMap = {
    'EQUAL' : 'exact',
    'NOT_EQUAL' : 'exact',
    'LESS_THAN' : 'lt',
    'LESS_THAN_OR_EQUAL' : 'lte',
    'GREATER_THAN' : 'gt',
    'GREATER_THAN_OR_EQUAL' : 'gte',
    'LIKE' : 'contains',
    'NOT_LIKE' : 'contains',
    'IN' : 'in',
    'NOT_IN' : 'in',
    'IS_NULL' : 'isnull',
}

class Operator(object):
    filterTerm = None
    operator = None
    description = None

    def prepValue(self, field, valueStr):
        if isinstance(field, fields.BooleanField):
            valueStr = self.castToBool(valueStr)
        return field.get_prep_value(valueStr)

    def castToBool(self, valueStr):
        """
        The field could either be a boolean field, or the operator might only
        accept boolean values.  Either way, we need a helper method to cast
        strings that correspond to bool values.
        """
        # Might be a bool already.
        if isinstance(valueStr, bool):
            return valueStr

        if valueStr.lower() == 'true':
            return True
        elif valueStr.lower() == 'false' or valueStr == '0':
            return False
        else:
            return bool(valueStr)

class BooleanOperator(Operator):
    def prepValue(self, field, valueStr):
        return self.castToBool(valueStr)

class InOperator(Operator):
    filterTerm = 'IN'
    operator = 'in'
    description = 'in'

    def prepValue(self, field, valueStr):
        if not (valueStr.startswith('(') and valueStr.endswith(')')):
            raise errors.InvalidFilterValue(value=valueStr,
                filter=self.filterTerm)

        valueStr = valueStr.strip('(').strip(')')
        values = valueStr.split(',')
        values = [field.get_prep_value(v) for v in values]
        return values

class NotInOperator(InOperator):
    filterTerm = 'NOT_IN'
    description = 'Not present in'

class NullOperator(BooleanOperator):
    filterTerm = 'IS_NULL'
    operator = 'isnull'
    description = 'Is NULL'

class EqualOperator(Operator):
    filterTerm = 'EQUAL'
    operator = 'exact'
    description = 'Equal to'

class NotEqualOperator(EqualOperator):
    filterTerm = 'NOT_EQUAL'
    description = 'Not equal to'

class LessThanOperator(Operator):
    filterTerm = 'LESS_THAN'
    operator = 'lt'
    description = 'Less than'

class LessThanEqualOperator(Operator):
    filterTerm = 'LESS_THAN_OR_EQUAL'
    operator = 'lte'
    description = 'Less than or equal to'

class GreaterThanOperator(Operator):
    filterTerm = 'GREATER_THAN'
    operator = 'gt'
    description = 'Greater than'

class GreaterThanEqualOperator(Operator):
    filterTerm = 'GREATER_THAN_OR_EQUAL'
    operator = 'gte'
    description = 'Greater than or equal to'

class LikeOperator(Operator):
    filterTerm = 'LIKE'
    operator = 'contains'
    description = 'Contains'

class NotLikeOperator(LikeOperator):
    filterTerm = 'NOT_LIKE'
    operator = 'contains'
    description = 'Does not contain'

def operatorFactory(operator):
    return operatorMap[operator]

def filterDjangoQuerySet(djangoQuerySet, field, operator, value):
    # Ignore fields that don't exist on the model
    fieldName = field.split('.')[0]
    if fieldName not in djangoQuerySet.model._meta.get_all_field_names():
        return djangoQuerySet

    if value is None:
        value = False

    fields = field.split('.')

    if operator in operatorMap:
        nextModel = djangoQuerySet.model()
        for f in fields[:-1]:
            nextModel = nextModel._meta.get_field_by_name(f)[0].rel.to()
        fieldCls = nextModel._meta.get_field_by_name(fields[-1])[0]
        operatorCls = operatorFactory(operator)()
        try:
            value = operatorCls.prepValue(fieldCls, value)
        except:
            raise errors.InvalidFilterValue(value=value,
                filter=operatorCls.filterTerm)
    else:
        raise errors.UnknownFilterOperator(filter=operator)

    # Replace all '.' with '__', to handle fields that span
    # relationships
    k = '%s__%s' % (field.replace('.', '__'), operatorCls.operator)
    filtDict = {k:value}
    if operator.startswith('NOT_'):
        djangoQuerySet = djangoQuerySet.filter(~Q(**filtDict))
    else:
        djangoQuerySet = djangoQuerySet.filter(**filtDict)

    return djangoQuerySet
 
class Collection(XObjIdModel):

    _xobj = xobj.XObjMetadata(
        attributes = {
            'count' : int,
            'full_collection' : str,
            'per_page' : str,
            'start_index' : str,
            'end_index' : str,
            'num_pages' : str,
            'next_page' : str,
            'previous_page' : str,
            'order_by' : str,
            'filter_by' : str,
            'limit' : str,
        }
    )

    class Meta:
        abstract = True

    count = models.IntegerField()
    full_collection = models.TextField()

    per_page = models.IntegerField()
    start_index = models.IntegerField()
    end_index = models.IntegerField()
    num_pages = models.IntegerField()
    next_page = models.TextField()
    previous_page = models.TextField()
    order_by = models.TextField()
    filter_by = models.TextField()
    limit = models.TextField()

    def get_absolute_url(self, request=None, parents=None, model=None,
                         page=None, full=None):
        url = XObjIdModel.get_absolute_url(self, request, parents, model)
        if url is None:
            return url
        if not page and not full:
            page = getattr(self, 'page', None)
        if page:
            limit = request.GET.get('limit', settings.PER_PAGE)
            url += ';start_index=%s;limit=%s' % (page.start_index(), limit)
        if self.order_by:
            url += ';order_by=%s' % self.order_by
        if self.filter_by:
            url += ';filter_by=%s' % self.filter_by
        return url

    def orderBy(self, request, modelList):
        orderBy = request.GET.get('order_by', None)
        if orderBy:
            newOrderParams = []
            orderParams = orderBy.split(',')
            for orderParam in orderParams:

                # Ignore fields that don't exist on the model
                fieldName = orderParam.split('.')[0]
                if fieldName.startswith('-'):
                    fieldName = fieldName[1:]
                if fieldName not in modelList.model._meta.get_all_field_names():
                    continue

                orderParam = orderParam.replace('.', '__')
                newOrderParams.append(orderParam)

            modelList = modelList.order_by(*newOrderParams)
        self.order_by = orderBy

        return modelList

    def filterBy(self, request, modelList):
        filterBy = request.GET.get('filter_by')
        if filterBy:
            self.filter_by = filterBy
            for filt in filterBy.split(']'):
                if not (filt.startswith('[') or filt.startswith(',[')):
                        continue
                filtString = filt.strip(',').strip('[').strip(']')
                field, oper, value = filtString.split(',', 2)
                modelList = filterDjangoQuerySet(modelList,
                    field, oper, value)

        return modelList

    def paginate(self, request, listField, modelList):
        startIndex = int(request.GET.get('start_index', 0))
        limit = int(request.GET.get('limit', settings.PER_PAGE))
        self.limit = limit
        pagination = CollectionPaginator(modelList, limit) 
        pageNumber = startIndex/limit

        try:
            page = pagination.page(pageNumber)
        except paginator.EmptyPage:
            raise errors.CollectionPageNotFound()

        self.page = page
        setattr(self, listField, page.object_list)

        self.count = pagination.count
        self.full_collection = self.get_absolute_url(request, full=True)
        self.per_page = pagination.per_page
        self.start_index = page.start_index()
        self.end_index = page.end_index()
        self.num_pages = pagination.num_pages

        if page.has_next():
            nextPage = pagination.page(page.next_page_number())
            self.next_page = self.get_absolute_url(request, page=nextPage)
        else:
            self.next_page = ''

        if page.has_previous():
            previousPage = pagination.page(page.previous_page_number())
            self.previous_page = self.get_absolute_url(request, page=previousPage)
        else:
            self.previous_page = ''

    def serialize(self, request=None):
        # We only support one list field right now
        if self.list_fields:
            listField = self.list_fields[0]
        else:
            return XObjIdModel.serialize(self, request)

        modelList = getattr(self, listField)
        
        # NEW
        if request:
            modelList = self.filterBy(request, modelList)
            modelList = self.orderBy(request, modelList)
            self.paginate(request, listField, modelList)

        # OLD
        # modelList = self.filterBy(request, modelList)
        # modelList = self.orderBy(request, modelList)
        # self.paginate(request, listField, modelList)

        xobj_model = XObjIdModel.serialize(self, request)

        return xobj_model

operatorMap = {}
for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, 'filterTerm'):
        operatorMap[mod_obj.filterTerm] = mod_obj


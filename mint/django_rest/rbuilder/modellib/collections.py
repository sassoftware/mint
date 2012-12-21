#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

import sys

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core import exceptions

from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder.modellib import XObjIdModel
from mint.jobstatus import FINISHED

from xobj import xobj
import math

filterTermMap = {
    'EQUAL' : 'iexact',
    'NOT_EQUAL' : 'iexact', 
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

class BooleanOperator(Operator):
    pass

class InOperator(Operator):
    filterTerm = 'IN'
    operator = 'in'
    description = 'In list'

class NotInOperator(InOperator):
    filterTerm = 'NOT_IN'
    description = 'Not in list'

class NullOperator(BooleanOperator):
    filterTerm = 'IS_NULL'
    operator = 'isnull'
    description = 'Is NULL'

class EqualOperator(Operator):
    filterTerm = 'EQUAL'
    operator = 'iexact'
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
    operator = 'icontains'
    description = 'Like'

class NotLikeOperator(LikeOperator):
    filterTerm = 'NOT_LIKE'
    operator = 'icontains'
    description = 'Not like'

def operatorFactory(operator):
    return operatorMap[operator]

def filterDjangoQuerySet(djangoQuerySet, field, operator, value, 
        collection=None, queryset=None):
    
    # a bit of a hack to deal with "eclipsed" fields where the name
    # is the default search key but the real field named name
    # is different, but let's be honest, all of QSes are a hack :)
    # example:
    #    Stage default search is by PROJECT name
    #    stage also has a name
    literal=False
    if field.startswith("literal:"):
        field = field.replace("literal:","")
        literal=True

    # attempt to DWIM when asked to search on something
    if not literal:
        # stage search is more logical if the search key is the project name
        if field == 'project_branch_stage.name' or field == 'name':
            if (queryset and queryset.resource_type == 'project_branch_stage') or \
                (collection and collection._xobj.tag == 'project_branch_stages'):
                field = 'project.name'
        # user model doesn't have a name, so point at that
        if field == 'user.name' or field == 'name':
            if (queryset and queryset.resource_type == 'user') or \
                (collection and collection._xobj.tag == 'users'):
                field = 'user.user_name'
        # I think this deals with some inconsistent model relation weirdness but
        # it's unclear
        if field == 'rbac_permission.permission_id' or field == 'permission_id':
            if (queryset and queryset.resource_type == 'grant') or \
               (collection and collection._xobj.tag == 'grants'):
               field = 'permission.permission_id'
        # same
        if field == 'name':
            if (queryset and queryset.resource_type == 'grant') or \
                (collection and collection._xobj.tag == 'grants'):
                field = 'permission.name'
        
 
    fieldName = field.split('.')[0]

    if not hasattr(djangoQuerySet, 'model'):
        raise Exception("filtering is not supported on non-database collections")

    if fieldName not in djangoQuerySet.model._meta.get_all_field_names():
        # if the model field didn't exist, try just the fieldName, 
        # it's possible the model was renamed and a custom query set
        # is no longer accurate.  
        field = field.split('.', 1)[-1]

    if value is None:
        value = False
    
    operatorCls = operatorFactory(operator)()
    operator_name = operatorCls.operator
    # TODO: see why Boolean and Int fields are not getting correct operator choices

    # work around Django SQL generator bug where iexact does not 
    # properly quote things that look like numbers, there is no
    # issue with like queries
    if operator_name == 'iexact':
        try:
            float(value)
            operator_name = 'in'
        except ValueError:
            # not numeric
            pass

    # lists can be entered seperated by commas
    if operator_name == 'in':
        value = value.split(",") 

    # if things look boolean, no need for Django operator
    # as it will just mess up the SQL
    if operator_name == 'iexact':
        lower = str(value).lower()
        if lower in [ 'true', 'false' ]:
            if lower == "true":
                value = True
            elif lower == "false":
                value = False
            operator_name = ''
  
    if operator_name == "isnull":
        lower = str(value).lower()
        if lower in [ 'true', 'false' ]:
            if lower == "true":
                value = True
            elif lower == "false":
                value = False
 
    # Replace all '.' with '__', to handle fields that span
    # relationships
    operator_name = "__%s" % operator_name
    if operator_name == '__':
        operator_name = ''
    k = "%s%s" % (field.replace('.', '__'), operator_name)
    filtDict = { k : value }

    # never be able to list a deleted user account, they are 
    # present for admin metadata only
    if queryset and queryset.resource_type == 'user':
        filtDict['deleted'] = False 
    # image querysets should not show non-successful images
    if queryset and queryset.resource_type == 'image':
        filtDict['status'] = FINISHED

    if operator.startswith('NOT_'):
        qs = djangoQuerySet.filter(~Q(**filtDict))
    else:
        qs = djangoQuerySet.filter(**filtDict)
    return qs

class UnpaginatedCollection(XObjIdModel):
    class Meta:
        abstract = True

class Collection(XObjIdModel):

    _xobj = xobj.XObjMetadata(
        attributes = {
            'id' : str,
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

    # number of total items
    count           = models.IntegerField()
    # URL to the collection without pagination params?
    full_collection = models.TextField()
    # size of each page
    per_page        = models.IntegerField()
    # where in the total list we are currently at
    start_index     = models.IntegerField()
    # last count int he the total list, ignoring pagination
    end_index       = models.IntegerField()
    num_pages       = models.IntegerField()
    # page numbers
    next_page       = models.TextField()
    previous_page   = models.TextField()
    # any requested user parameters:
    order_by        = models.TextField()
    filter_by       = models.TextField()
    limit           = models.TextField()

    def get_absolute_url(self, request=None, parents=None, model=None,
                         paged=False, startIndex=None, full=None):
        url = XObjIdModel.get_absolute_url(self, request, parents, model)

        if url:
            if paged:
                limit = request.GET.get('limit', settings.PER_PAGE)
                url += ';start_index=%s;limit=%s' % (startIndex, limit)
            if self.order_by:
                url += ';order_by=%s' % self.order_by
            if self.filter_by:
                url += ';filter_by=%s' % self.filter_by
        return url

    def _sortByField(key):
        return lambda field: getattr(field, key, None)

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

                orderParam = orderParam.replace('.', '__')
                newOrderParams.append(orderParam)

            if hasattr(modelList, 'order_by'):
                modelList = modelList.order_by(*newOrderParams)
            else:

                param = newOrderParams[0]
                invert = False
                    
                if param.startswith("-"):
                    invert = True
                if param[0] in [ '+', '-', ' ' ]:
                    param = param[1:].strip()

                # a list, not a query set
                modelList = sorted(modelList, 
                    key=lambda f: getattr(f, param)
                )
                if invert:
                    modelList.reverse()

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
                    field, oper, value, collection=self)

        return modelList

    def paginate(self, request, listField, modelList):
        startIndex = int(request.GET.get('start_index', 0))
        self.limit = int(request.GET.get('limit', settings.PER_PAGE))

        if modelList is not None:
            self.count = None
            if type(modelList) == list:
                self.count = len(modelList)
            else:
                # queryset
                self.count = modelList.count()
        else:
            modelList = []
            self.count = 0
        if self.limit == 0:
            self.count = 0

        # compute page counts and numbers
        pageCount  = 0
        pageNumber = 1
        stopIndex  = 0
        if self.limit > 0:
            pageCount  = int(math.ceil(self.count / float(self.limit)))
            pageNumber = int(math.floor(startIndex / float(self.limit)))
            stopIndex  = startIndex + self.limit -1

        # some somewhat confusing fenceposty stuff because we're working in ints
        if pageCount == 0:
            pageCount = 1
        if stopIndex < 0:
            stopIndex = 0
        pageObjectList = []
        if self.limit > 0:
            pageObjectList = modelList[startIndex:(stopIndex+1)]

        # Force qs evaluation here, to catch order_by errors
        try:
            setattr(self, listField, list(pageObjectList))
        except exceptions.FieldError, e:
            if e.args and e.args[0].startswith("Cannot resolve keyword"):
                raise errors.InvalidFilterKey(msg=e.args[0])
            raise

        self.full_collection = self.get_absolute_url(request, full=True)
        self.per_page        = self.limit
        self.start_index     = startIndex
        self.end_index       = stopIndex

        # more handling around the edges
        if self.end_index >= self.count - 1:
            self.end_index = self.count - 1
        if self.end_index < 0:
            self.end_index = 0

        self.num_pages       = pageCount
        self._pagedId        = self.get_absolute_url(request, paged=True, startIndex=startIndex)

        # if there are pages left, link to a next_page
        if self.end_index < self.count - 1:
            nextIndex = startIndex + self.limit
            self.next_page = self.get_absolute_url(request, paged=True, startIndex = nextIndex)

        # if there are pages beforehand, link to them
        if startIndex - self.limit >= 0:
            prevIndex = startIndex - self.limit
            if prevIndex < 0:
                prevIndex = 0
            self.previous_page = self.get_absolute_url(request, paged=True, startIndex= prevIndex)

    def serialize(self, request=None):
        # We only support one list field right now
        if self.list_fields:
            listField = self.list_fields[0]
        else:
            return XObjIdModel.serialize(self, request)

        modelList = getattr(self, listField)
        
        if request:
            modelList = self.filterBy(request, modelList)
            modelList = self.orderBy(request, modelList)
            self.paginate(request, listField, modelList)

        xobj_model = XObjIdModel.serialize(self, request)
        xobj_model.id = self._pagedId

        return xobj_model

operatorMap = {}
for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, 'filterTerm'):
        operatorMap[mod_obj.filterTerm] = mod_obj


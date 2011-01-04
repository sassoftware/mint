#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core import exceptions
from django.core import paginator

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
        if self.number == self.paginator.num_pages:
            return self.paginator.count
        return (self.paginator.per_page * (self.number + 1)) - 1

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
    'MATCHING' : '',
    'NOT_MATCHING' : '',
}

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

    def get_absolute_url(self, request=None, parents=None, model=None,
                         page=None, full=None):
        url = XObjIdModel.get_absolute_url(self, request, parents, model)
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
            try:
                orderParams = orderBy.split(',')
                modelList = modelList.order_by(*orderParams)
            except exceptions.FieldError:
                orderBy = None
        self.order_by = orderBy

        return modelList

    def filterBy(self, request, modelList):
        filterBy = request.GET.get('filter_by')
        if filterBy:
            self.filter_by = filterBy
            filters = []
            qFilters = []
            for filt in filterBy.split(']'):
                if not (filt.startswith('[') or filt.startswith(',[')):
                        continue
                filtString = filt.strip(',').strip('[').strip(']')
                field, oper, value = filtString.split(',', 3)
                if oper.startswith('NOT_'):
                    k = '%s__%s' % (field, filterTermMap[oper])
                    qFilters.append({k:value})
                else:
                    k = '%s__%s' % (field, filterTermMap[oper])
                    filters.append({k:value})

            for qFilter in qFilters:
                modelList = modelList.filter(~Q(**qFilter))

            for filt in filters:
                modelList = modelList.filter(**filt)

        return modelList

    def paginate(self, request, listField, modelList):
        startIndex = int(request.GET.get('start_index', 0))
        limit = int(request.GET.get('limit', settings.PER_PAGE))
        pagination = CollectionPaginator(modelList, limit) 
        pageNumber = startIndex/limit
        page = pagination.page(pageNumber)

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

    def serialize(self, request=None, values=None):
        # We only support one list field right now
        if self.list_fields:
            listField = self.list_fields[0]
        else:
            return XObjIdModel.serialize(self, request, values)

        modelList = getattr(self, listField)

        modelList = self.filterBy(request, modelList)
        modelList = self.orderBy(request, modelList)

        self.paginate(request, listField, modelList)

        xobj_model = XObjIdModel.serialize(self, request, values)

        return xobj_model


#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

BAD_REQUEST = 400
NOT_FOUND = 404
INTERNAL_SERVER_ERROR = 500

class RbuilderError(Exception):
    "An unknown error has occured."

    status = INTERNAL_SERVER_ERROR 

    def __init__(self, **kwargs):
        cls = self.__class__
        self.msg = cls.__doc__
        self.kwargs = kwargs

    def __str__(self):
        try:
            return self.msg % self.kwargs
        except TypeError:
            return self.msg

class CollectionPageNotFound(RbuilderError):
    "The requested page of the collection was not found."
    status = NOT_FOUND

class UnknownFilterOperator(RbuilderError):
    "%(filter)s is an invalid filter operator."
    status = BAD_REQUEST

class InvalidFilterValue(RbuilderError):
    "%(value)s in an invalid value for filter operator %(filter)s"
    status = BAD_REQUEST

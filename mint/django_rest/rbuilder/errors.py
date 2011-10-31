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
        kwargs_msg = kwargs.get('msg', None)
        if kwargs_msg:
            self.msg = kwargs_msg
        else:
            self.msg = cls.__doc__
        self.kwargs = kwargs

    def __str__(self):
        try:
            return self.msg % self.kwargs
        except TypeError:
            return self.msg

class PermissionDenied(RbuilderError):
    "Permission to the requested resource is denied"

    status = 403

class CollectionPageNotFound(RbuilderError):
    "The requested page of the collection was not found."
    status = NOT_FOUND

class UnknownFilterOperator(RbuilderError):
    "%(filter)s is an invalid filter operator."
    status = BAD_REQUEST

class InvalidFilterValue(RbuilderError):
    "%(value)s is an invalid value for filter operator %(filter)s"
    status = BAD_REQUEST


class MirrorCredentialsInvalid(RbuilderError):
    "The supplied %(creds)s credentials do not grant mirror access to the repository at %(url)s"
    status = BAD_REQUEST


class MirrorNotReachable(RbuilderError):
    "Error contacting remote repository at %(url)s: %(reason)s"
    status = BAD_REQUEST

class ResourceNotFound(RbuilderError):
    "The requested resource was not found."
    status = NOT_FOUND

class InvalidData(RbuilderError):
    "The data supplied with the resource was invalid"
    status = BAD_REQUEST

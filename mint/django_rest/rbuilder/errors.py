#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

BAD_REQUEST = 400
NOT_FOUND = 404
INTERNAL_SERVER_ERROR = 500
CONFLICT = 409

class RbuilderError(Exception):
    "An unknown error has occured."

    status = INTERNAL_SERVER_ERROR 

    def __init__(self, **kwargs):
        cls = self.__class__
        kwargs_msg = kwargs.pop('msg', None)
        kwargs_status = kwargs.pop('status', None)
        if kwargs_msg:
            self.msg = kwargs_msg
        else:
            self.msg = cls.__doc__
        if kwargs_status:
            self.status = kwargs_status
        else:
            self.status = getattr(self.__class__, 'status', INTERNAL_SERVER_ERROR)
        self.kwargs = kwargs
        self.traceback = kwargs.pop('traceback', None)

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

class InvalidFilterKey(RbuilderError):
    "%(field)s is an invalid field name."
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

class Conflict(RbuilderError):
    "The resource conflicts with an existing one"
    status = CONFLICT

class InvalidData(RbuilderError):
    "The data supplied with the resource was invalid"
    status = BAD_REQUEST

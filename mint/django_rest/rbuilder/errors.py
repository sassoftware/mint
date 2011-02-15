#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

class RbuilderError(Exception):
    "An unknown error has occured."

    status = 500

    def __init__(self, **kwargs):
        cls = self.__class__
        self.msg = cls.__doc__
        self.kwargs = kwargs

    def __str__(self):
        try:
            return self.msg % self.kwargs
        except TypeError:
            return self.msg

class PermissionDenied(RbuilderError):
    "Permission to the requested resource is denied"

    status = 401

class CollectionPageNotFound(RbuilderError):
    "The requested page of the collection was not found."
    status = 404

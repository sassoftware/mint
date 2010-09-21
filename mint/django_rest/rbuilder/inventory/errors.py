#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

class InventoryError(Exception):
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

class InvalidNetworkInformation(InventoryError):
    "The system does not have valid network information"

class UnknownEventType(InventoryError):
    "An unknown even type was specified: %(eventType)s"

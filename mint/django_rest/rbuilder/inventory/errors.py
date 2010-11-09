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

class JobsAlreadyRunning(InventoryError):
    "The system already has running jobs.  New jobs can not be started on the system."
    status = 200

class IncompatibleEvent(InventoryError):
    status = 200

class IncompatibleSameEvent(IncompatibleEvent):
    """An event of type %(eventType)s is already running, another can not be run
    at the same time."""

class IncompatibleEvents(IncompatibleEvent):
    """The event type %(firstEventType)s is already running, an event type
    %(secondEventType)s can not be run at the same time."""

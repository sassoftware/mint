#
# Copyright (c) 2010, 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder import errors

class InventoryError(errors.RbuilderError):
    pass

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

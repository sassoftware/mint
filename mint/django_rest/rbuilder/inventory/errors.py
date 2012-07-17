#
# Copyright (c) 2010, 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder import errors

class InventoryError(errors.RbuilderError):
    status = 400

class InvalidNetworkInformation(InventoryError):
    "The system does not have valid network information"
    status = 400

class UnknownEventType(InventoryError):
    "An unknown event type was specified: %(eventType)s"
    status = 400

class JobsAlreadyRunning(InventoryError):
    "The system already has running jobs.  New jobs can not be started on the system."
    status = 409

class IncompatibleEvent(InventoryError):
    status = 409

class IncompatibleSameEvent(IncompatibleEvent):
    """An event of type %(eventType)s is already running, another can not be run
    at the same time."""
    status = 409

class IncompatibleEvents(IncompatibleEvent):
    """The event type %(firstEventType)s is already running, an event type
    %(secondEventType)s can not be run at the same time."""
    status = 409

class SystemNotDeployed(InventoryError):
    "The system is not deployed on a target"
    status = 400



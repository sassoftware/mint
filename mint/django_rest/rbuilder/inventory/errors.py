#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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

class InvalidSystemConfiguration(InventoryError):
    "The supplied configuration does not match the system's expectations"
    status = 400

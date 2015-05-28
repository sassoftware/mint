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


BAD_REQUEST = 400
NOT_FOUND = 404
INTERNAL_SERVER_ERROR = 500
CONFLICT = 409
TEMPORARY_REDIRECT = 307
FORBIDDEN = 403

class RbuilderError(Exception):
    "An unknown error has occured."

    status = INTERNAL_SERVER_ERROR

    def __init__(self, **kwargs):
        cls = self.__class__
        kwargs_msg = kwargs.pop('msg', None)
        kwargs_status = kwargs.pop('status', None)
        kwargs_headers = kwargs.pop('headers', {})
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
        self._headers = kwargs_headers

    def __str__(self):
        try:
            return self.msg % self.kwargs
        except TypeError:
            return self.msg

    def iterheaders(self, request):
        for k, v in self._headers.iteritems():
            if hasattr(v, 'serialize'):
                v = v.serialize(request)
            yield k, v

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

class TemporaryRedirect(RbuilderError):
    status = TEMPORARY_REDIRECT

class Forbidden(RbuilderError):
    "The resource is not allowing operations"
    status = FORBIDDEN

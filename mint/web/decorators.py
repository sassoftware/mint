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

import inspect

from mint import mint_error
from mint import userlevels
from mint.mint_error import ItemNotFound
from mint.web import webhandler


def weak_signature_call(_func, *args, **kwargs):
    '''
    Call a function without any keyword arguments it doesn't support.

    If the function does not directly accept an argument, and also
    does not have a magic keyword argument, the argument is dropped
    from the call.
    '''

    argnames, varname, varkwname, _ = inspect.getargspec(_func)
    for kwarg in kwargs.keys():
        if kwarg not in argnames and varkwname is None:
            del kwargs[kwarg]

    return _func(*args, **kwargs)


def requiresHttps(func):
    def requiresHttpsWrapper(self, *args, **kwargs):
        if self.req.scheme == 'http' and self.cfg.SSL:
            raise mint_error.PermissionDenied
        else:
            return weak_signature_call(func, self, *args, **kwargs)

    requiresHttpsWrapper.__wrapped_func__ = func
    return requiresHttpsWrapper


def requiresAdmin(func):
    def requiresAdminWrapper(self, *args, **kwargs):
        if not kwargs['auth'].admin:
            raise mint_error.PermissionDenied
        else:
            return weak_signature_call(func, self, *args, **kwargs)

    requiresAdminWrapper.__wrapped_func__ = func
    return requiresAdminWrapper

def requiresAuth(func):
    def requiresAuthWrapper(self, **kwargs):
        if not kwargs['auth'].authorized:
            raise mint_error.PermissionDenied
        else:
            return weak_signature_call(func, self, **kwargs)

    requiresAuthWrapper.__wrapped_func__ = func
    return requiresAuthWrapper

def ownerOnly(func):
    """
    Require a method to be callable only by the owner of the current project.
    """
    def ownerOnlyWrapper(self, **kwargs):
        if not self.project:
            raise ItemNotFound("project")
        if self.userLevel == userlevels.OWNER or self.auth.admin:
            return weak_signature_call(func, self, **kwargs)
        else:
            raise mint_error.PermissionDenied

    ownerOnlyWrapper.__wrapped_func__ = func
    return ownerOnlyWrapper

def writersOnly(func):
    """
    Require a method to be callable only by a developer or owner of a project.
    """
    def writersOnlyWrapper(self, **kwargs):
        if not self.project:
            raise ItemNotFound("project")
        if self.userLevel in userlevels.WRITERS or self.auth.admin:
            return weak_signature_call(func, self, **kwargs)
        else:
            raise mint_error.PermissionDenied

    writersOnlyWrapper.__wrapped_func__ = func
    return writersOnlyWrapper

def postOnly(func):
    """
    Require a method to be called with the POST HTTP method.
    """
    def postOnlyWrapper(self, *args, **kwargs):
        if self.req.method != 'POST':
            raise webhandler.HttpForbidden
        else:
            return weak_signature_call(func, self, *args, **kwargs)

    postOnlyWrapper.__wrapped_func__ = func
    return postOnlyWrapper

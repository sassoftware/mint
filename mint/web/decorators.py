#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#

import inspect

from mod_python import apache

from mint import mint_error
from mint import userlevels
from mint.mint_error import *
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
        if self.req.subprocess_env.get('HTTPS', 'off') != 'on' and self.cfg.SSL:
            raise mint_error.PermissionDenied
        else:
            return weak_signature_call(func, self, *args, **kwargs)

    requiresHttpsWrapper.__wrapped_func__ = func
    return requiresHttpsWrapper


def _makeURL(schema, req, configuredHost):
    """
    Redirect C{req} to its HTTP/HTTPS counterpart (C{schema}). If
    C{configuredHost} has a port, that will be used to build the host part of
    the URL.
    """
    newHost = req.hostname.rsplit(':', 1)[0]
    if ':' in configuredHost:
        newHost += ':' + configuredHost.split(':')[-1]
    return '%s://%s%s' % (schema, newHost, req.unparsed_uri)


def redirectHttp(func):
    def redirectHttpWrapper(self, *args, **kwargs):
        if (self.req.subprocess_env.get('HTTPS', 'off') != 'off' and
                self.cfg.SSL):
            return self._redirect(_makeURL('http', self.req,
                self.cfg.siteDomainName))
        else:
            return weak_signature_call(func, self, *args, **kwargs)

    redirectHttpWrapper.__wrapped_func__ = func
    return redirectHttpWrapper

def redirectHttps(func):
    def redirectHttpsWrapper(self, *args, **kwargs):
        if (self.req.subprocess_env.get('HTTPS', 'off') != 'on' and
                self.cfg.SSL):
            return self._redirect(_makeURL('https', self.req,
                self.cfg.secureHost))
        else:
            return weak_signature_call(func, self, *args, **kwargs)

    redirectHttpsWrapper.__wrapped_func__ = func
    return redirectHttpsWrapper

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

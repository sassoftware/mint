#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#
import sys

from mod_python import apache

from mint import database
from mint import mailinglists
from mint import mint_error
from mint import userlevels
from mint.web import webhandler

def requiresHttps(func):
    def requiresHttpsWrapper(self, *args, **kwargs):
        if self.req.subprocess_env.get('HTTPS', 'off') != 'on' and self.cfg.SSL:
            raise mint_error.PermissionDenied
        else:
            return func(self, *args, **kwargs)

    requiresHttpsWrapper.__wrapped_func__ = func
    return requiresHttpsWrapper

def redirectHttp(func):
    def redirectHttpWrapper(self, *args, **kwargs):
        if self.req.subprocess_env.get('HTTPS', 'off') != 'off' and self.cfg.SSL:
            return self._redirect('http://%s%s' % ( \
                self.req.headers_in.get('host', self.req.hostname),
                self.req.unparsed_uri))
        else:
            return func(self, *args, **kwargs)

    redirectHttpWrapper.__wrapped_func__ = func
    return redirectHttpWrapper

def redirectHttps(func):
    def redirectHttpsWrapper(self, *args, **kwargs):
        reqPort = self.req.parsed_uri[apache.URI_PORT]
        reqHost = self.req.headers_in.get('host', self.req.hostname)
        if ':' not in reqHost and reqPort and reqPort != 443:
            hostname = '%s:%s' % (reqHost, reqPort)
        else:
            hostname = reqHost
        if (self.req.subprocess_env.get('HTTPS', 'off') != 'on' or \
            hostname != self.cfg.secureHost) and self.cfg.SSL:
            return self._redirect('https://%s%s' % \
                    (self.cfg.secureHost, self.req.unparsed_uri))
        else:
            return func(self, *args, **kwargs)

    redirectHttpsWrapper.__wrapped_func__ = func
    return redirectHttpsWrapper

def requiresAdmin(func):
    def requiresAdminWrapper(self, *args, **kwargs):
        if not kwargs['auth'].admin:
            raise mint_error.PermissionDenied
        else:
            return func(self, *args, **kwargs)

    requiresAdminWrapper.__wrapped_func__ = func
    return requiresAdminWrapper

def requiresAuth(func):
    def requiresAuthWrapper(self, **kwargs):
        if not kwargs['auth'].authorized:
            raise mint_error.PermissionDenied
        else:
            return func(self, **kwargs)

    requiresAuthWrapper.__wrapped_func__ = func
    return requiresAuthWrapper

def ownerOnly(func):
    """
    Require a method to be callable only by the owner of the current project.
    """
    def ownerOnlyWrapper(self, **kwargs):
        if not self.project:
            raise database.ItemNotFound("project")
        if self.userLevel == userlevels.OWNER or self.auth.admin:
            return func(self, **kwargs)
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
            raise database.ItemNotFound("project")
        if self.userLevel in userlevels.WRITERS or self.auth.admin:
            return func(self, **kwargs)
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
            return func(self, *args, **kwargs)

    postOnlyWrapper.__wrapped_func__ = func
    return postOnlyWrapper

def mailList(func):
    """
    Decorate a method so that it is passed a MailingListClient object
    properly formatted and ready to use inside an error handler.
    """
    def mailListWrapper(self, **kwargs):
        mlists = mailinglists.MailingListClient(self.cfg.MailListBaseURL + 'RPC2')
        try:
            return func(self, mlists=mlists, **kwargs)
        except mailinglists.MailingListException, e:
            return self._write("error", shortError = "Mailing List Error",
                error = "An error occurred while talking to the mailing list server: %s" % str(e))

    mailListWrapper.__wrapped_func__ = func
    return mailListWrapper

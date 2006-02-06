#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
from mod_python import apache

from mint import database
from mint import mailinglists
from mint import mint_error
from mint import userlevels
import sys

def requiresHttps(func):
    def wrapper(self, *args, **kwargs):
        if self.req.subprocess_env.get('HTTPS', 'off') != 'on' and self.cfg.SSL:
            raise mint_error.PermissionDenied
        else:
            return func(self, *args, **kwargs)

    return wrapper

def redirectHttp(func):
    def wrapper(self, *args, **kwargs):
        if self.req.subprocess_env.get('HTTPS', 'off') != 'off' and self.cfg.SSL:
            return self._redirect('http://%s%s' %(self.cfg.siteHost, self.req.unparsed_uri))
        else:
            return func(self, *args, **kwargs)
    return wrapper

def redirectHttps(func):
    def wrapper(self, *args, **kwargs):
        if (self.req.subprocess_env.get('HTTPS', 'off') != 'on' or \
            self.req.hostname != self.cfg.secureHost) and self.cfg.SSL:
            return self._redirect('https://%s%s' % (self.cfg.secureHost, self.req.unparsed_uri))
        else:
            return func(self, *args, **kwargs)
    return wrapper

def requiresAdmin(func):
    def wrapper(self, *args, **kwargs):
        if not kwargs['auth'].admin:
            raise mint_error.PermissionDenied
        else:
            return func(self, *args, **kwargs)
    return wrapper

def requiresAuth(func):
    def wrapper(self, **kwargs):
        if not kwargs['auth'].authorized:
            raise mint_error.PermissionDenied
        else:
            return func(self, **kwargs)
    return wrapper

def ownerOnly(func):
    """
    Decorate a method to be callable only by the owner of the
    current package also requires that a package exist.
    """
    def wrapper(self, **kwargs):
        if not self.project:
            raise database.ItemNotFound("project")
        if self.userLevel == userlevels.OWNER or self.auth.admin:
            return func(self, **kwargs)
        else:
            raise mint_error.PermissionDenied
    return wrapper

def mailList(func):
    """
    Decorate a method so that it is passed a MailingListClient object
    properly formatted and ready to use inside an error handler.
    """
    def wrapper(self, **kwargs):
        mlists = mailinglists.MailingListClient(self.cfg.MailListBaseURL + 'RPC2')
        try:
            return func(self, mlists=mlists, **kwargs)
        except mailinglists.MailingListException, e:
            return self._write("error", shortError = "Mailing List Error",
                error = "An error occured while talking to the mailing list server: %s" % str(e))
    return wrapper

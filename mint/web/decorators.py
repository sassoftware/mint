#
# Copyright (c) 2005 rPath, Inc.
#
# All rights reserved
#
from mod_python import apache

from mint import database
from mint import mailinglists
from mint import userlevels

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
        mlists = mailinglists.MailingListClient(self.cfg.MailListBaseURL + 'xmlrpc')
        try:
            return func(self, mlists=mlists, **kwargs)
        except mailinglists.MailingListException, e:
            self._write("error", shortError = "Mailing List Error",
                    error = "An error occured while talking to the mailing list server: %s" % str(e))
            return apache.OK
    return wrapper

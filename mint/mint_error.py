#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

class MintError(Exception):
    pass

class PermissionDenied(MintError):
    def __str__(self):
        return "Permission Denied"

class InvalidLogin(PermissionDenied):
    def __str__(self):
        return "Invalid username or password."

class UnknownException(Exception):
    def __str__(self):
        return "%s %s" % (self.eName, self.eArgs)

    def __init__(self, eName, eArgs):
        self.eName = eName
        self.eArgs = eArgs

class ReleasePublished(MintError):
    def __str__(self):
        return "Cannot alter a release once it is published."

class ReleaseMissing(MintError):
    def __str__(self):
        return "The referenced release does not exist."

class ReleaseEmpty(MintError):
    def __str__(self):
        return "The referenced release has no files and cannot be published."

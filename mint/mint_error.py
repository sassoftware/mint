#
# Copyright (c) 2005 rpath, Inc.
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

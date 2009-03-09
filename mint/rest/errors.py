#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint import mint_error

class ItemNotFound(mint_error.MintError):
    pass

class InvalidSearchType(mint_error.MintError):
    pass

class ProductNotFound(ItemNotFound):
    pass

class ProductVersionNotFound(ItemNotFound):
    pass

class StageNotFound(ItemNotFound):
    pass

class UserNotFound(ItemNotFound):
    pass

class BuildNotFound(ItemNotFound):
    pass

class ReleaseNotFound(ItemNotFound):
    pass

class MemberNotFound(ItemNotFound):
    pass

PermissionDenied = mint_error.PermissionDenied

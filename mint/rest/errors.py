#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint import mint_error

class ItemNotFound(mint_error.MintError):
    def __init__(self, *args, **kw):
        #bypass mint error handling
        Exception.__init__(self, *args, **kw)

    def __str__(self):
        return '%s' % (self.args[0],)

class InvalidTroveSpec(mint_error.MintError):
    status = 400

class InvalidVersion(mint_error.MintError):
    status = 400

class InvalidFlavor(mint_error.MintError):
    status = 400

class InvalidSearchType(mint_error.MintError):
    pass

class ProductNotFound(ItemNotFound):
    status = 404

class ProductVersionNotFound(ItemNotFound):
    pass

class StageNotFound(ItemNotFound):
    pass

class ImageNotFound(ItemNotFound):
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

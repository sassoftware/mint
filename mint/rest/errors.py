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

class PermissionDeniedError(mint_error.MintError):
    "You do not have permission to access this resource."
    status = 403

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

class ExternalRepositoryMirrorError(Exception):
    msg = ("Entitlement does not grant mirror access to"
           " external repository")

class ExternalRepositoryAccessError(Exception):
    def __init__(self, url, e):
        self.url = url
        self.e = str(e)

    def __str__(self):
        if self.url:
            msg = ("Error contacting remote repository. "
                   " Please ensure entitlement and repository "
                   " URL are correct. (%s)" % str(e))
        else:
            msg = ("Error contacting remote repository."
                   " Please ensure entitlement is correct."
                   " (%s)" % str(e))

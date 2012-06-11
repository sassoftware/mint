#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint import mint_error

class ItemNotFound(mint_error.ItemNotFound):
    def __init__(self, *args, **kw):
        #bypass mint error handling
        self.item = args
        Exception.__init__(self, *args, **kw)

    def __str__(self):
        return '%s' % (self.args[0],)

class PermissionDeniedError(mint_error.MintError):
    "You do not have permission to access this resource."
    status = 403

class InvalidItem(mint_error.MintError):
    status = 400

class InvalidTroveSpec(mint_error.MintError):
    status = 400

class InvalidVersion(mint_error.MintError):
    status = 400

class InvalidFlavor(mint_error.MintError):
    status = 400
    
class AuthHeaderError(mint_error.InvalidError):
    "Your authentication header could not be decoded"

class InvalidSearchType(mint_error.MintError):
    pass

class InvalidProjectForPlatform(mint_error.MintError):
    """
    A non-external project already exists that shares the fully qualified
    domainname of the platform that is being enabled.
    """

class PlatformLoadFileNotFound(mint_error.MintError):
    def __init__(self, uri):
        self.uri = uri

    def __str__(self):
        return "Load file %s could not be downloaded." % self.uri

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

class StopJobFailed(mint_error.MintError):
    def __init__(self, jobId, e):
        self.jobId = jobId
        self.e = e

    def __str__(self):
        return "Failed to stop job %s: %s" % (self.jobId, self.e)

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
                   " URL are correct. (%s)" % str(self.e))
        else:
            msg = ("Error contacting remote repository."
                   " Please ensure entitlement is correct."
                   " (%s)" % str(self.e))
        return msg                   

import inspect
__all__ = []
for name, obj in locals().copy().iteritems():
    if inspect.isclass(obj) and issubclass(obj, Exception):
        __all__.append(name)

#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

try:
    from mint import constants
    isRBO = constants.rBuilderOnline
except ImportError:
    # Constants may not be available if this class is copied elsewhere;
    # e.g. to the cmdline client
    isRBO = False

class MintError(Exception):
    msg = "An unknown error occured in mint"
    def __init__(self, msg=None, *args):
        if msg is not None:
            self.msg = msg % args
        else:
            # Use the class object instead of the instance so __init__ does
            # not depend on the object's state; e.g. the default thaw
            # method calls __init__ on an already instantiated object.
            cls = self.__class__
            if cls.__doc__ is not None:
                template = cls.__doc__
            else:
                template = cls.msg

            # Substitute project or product depending on whether we're an
            # rBO or rBA, respectively. Reproduced here instead of using
            # helperfuncs to minimize the number of things that need
            # duplicating to create a mint client.
            project = isRBO and "project" or "product"
            transform = dict(   project=project,
                                Project=project.title(),
                                PROJECT=project.upper())
            self.msg = template % transform

    def __str__(self):
        return self.msg

    # These are for XMLRPC marshalling. The default case works as long as you
    # only need a string and do not override __str__.
    freeze = __str__
    @classmethod
    def thaw(cls, blob):
        ret = cls()
        ret.msg = blob
        return ret

class AdminSelfDemotion(MintError): "You cannot demote yourself."
class AlreadyConfirmed(MintError):
    "Your registration has already been confirmed"
class AMIBuildNotConfigured(MintError):
    "This rBuilder is missing information necessary to build " \
        "Amazon Machine Images. Please consult your site administrator."
class AuthRepoError(MintError):
    "Authentication token could not be manipulated."
class BuildDataNameError(MintError):
    "Named value is not in data template."
class BuildFileMissing(MintError):
    "The referenced build file doesn't exist."
class BuildMissing(MintError): "The referenced build does not exist."
class BuildXmlInvalid(MintError): "Invalid Build XML"
class BuildPublished(MintError):
    "The referenced build is already part of a published release."
class BuildEmpty(MintError):
    "The referenced build has no files and cannot be published."
class ConfirmError(MintError):
    "Your registration could not be confirmed"
class DeleteLocalUrlError(MintError):
    "Deleting a local build file is not supported via this interface."
class DuplicateHostname(MintError):
    "A %(project)s using this hostname already exists"
class DuplicateJob(MintError):
    "A conflicting job is already in progress"
class DuplicateName(MintError):
    "A %(project)s using this title already exists"
class DuplicateLabel(MintError): "Label already exists"
class InvalidHostname(MintError):
    "Invalid hostname: must start with a letter and contain only " \
        "letters, numbers, and hyphens."
class InvalidShortname(MintError):
    def __str__(self):
        return "Invalid short name: must start with a letter and contain only letters, numbers, and hyphens."
class InvalidLabel(MintError):
    def __str__(self):
        return self.reason
    def __init__(self, label):
        self.reason = "The generated development label (%s) is invalid.  This can be caused by an invalid short name, namespace, or version."%label
class InvalidVersion(MintError):
    def __str__(self):
        return "The version is invalid."
class InvalidProdType(MintError):
    def __str__(self):
        return "The selected %s type is invalid."%getProjectText().lower()
class LabelMissing(MintError):
    "%(Project)s label does not exist"
class FailedToLaunchAMIInstance(MintError):
    "Failed to launch AMI instance."
class FileMissing(MintError): "The referenced file does not exist."
class GroupAlreadyExists(MintError): "Group already exists"
class GroupTroveEmpty(MintError): "Group cannot be empty"
class GroupTroveNameError(MintError):
    "Invalid name for group: letters, numbers, hyphens allowed."
class GroupTroveVersionError(MintError):
    "Invalid version for group: letters, numbers, periods allowed."
class HtmlTagNotAllowed(MintError): pass
class HtmlParseError(MintError): pass
class InvalidUsername(MintError):
    "Username may contain only letters, digits, '-', '_', and '.'"
class JobserverVersionMismatch(MintError): # LEGACY
    "Image job cannot be run."
class LastAdmin(MintError):
    "You cannot close the last administrator account."
class LastOwner(MintError):
    "You cannot oprphan a project with developers"
class MailError(MintError): "there was a problem sending email"
class MailingListException(MintError): pass
class MaintenanceMode(MintError): "Repositories are currently offline."
class MessageException(MintError): pass
class NoMirrorLoadDiskFound(MintError):
    "No mirror preload disk was found attached to your appliance."
class NotEntitledError(MintError):
    "The rBuilder is not entitled to a required resource. Please " \
        "contact your administrator."
class ParameterError(MintError):
    "A required parameter had an incorrect data type."
class PermissionDenied(MintError): "Permission Denied"
class PublishedReleaseEmpty(MintError):
    "The referenced release has no builds and cannot be published."
class PublishedReleaseMissing(MintError):
    "The referenced published release does not exist."
class PublishedReleaseNotPublished(MintError):
    "Release has already been unpublished."
class PublishedReleasePublished(MintError):
    "Release has already been published."
class SchemaMigrationError(MintError): pass
class TooManyAMIInstancesPerIP(MintError):
    "Too many AMI instances have been launched from this IP " \
        "address. Please try again later."
class TroveNotSet(MintError):
    "This build is not associated with a group."
class UserAlreadyAdmin(MintError): "User is already an administrator."
class UserAlreadyExists(MintError): "User already exists"
class UserInduction(MintError):
    "Project owner attempted to manipulate a project user in an " \
        "illegal fashion"
BuildFileUrlMissing = BuildFileMissing

# Exceptions with arguments
class DuplicateItem(MintError):
    def __init__(self, item = "item"):
        self.msg = "duplicate item in %s" % item
class ItemNotFound(MintError):
    def __init__(self, item = "item"):
        self.msg = "requested %s not found" % item
class MethodNotSupported(MintError):
    def __init__(self, method):
        self.msg = "method not supported by XMLRPC server: %s" % method
class UnmountFailed(MintError):
    def __init__(self, dev):
        self.msg = "Unable to automatically unmount %s; please manually " \
            "unmount" % dev
class UpToDateException(MintError):
    def __init__(self, table = "Unknown Table"):
        self.msg = "The table '%s' is not up to date" % table
class InvalidBuildOption(MintError):
    def __init__(self, desc):
        self.msg = "Invalid value for %s"%desc
class BuildOptionValidationException(MintError):
    def __init__(self, errlist):
        self.errlist = errlist
        self.msg = str(self.errlist)
    

class DatabaseVersionMismatch(MintError):
    def __init__(self, currentVersion):
        self.msg = "The current database schema does not match the " \
            "version required by this version of rBuilder. " \
            "Current version is %s; required version is %s." % (
                currentVersion, schema.RBUILDER_DB_VERSION)

## Subclassed exceptions
# MessageException
class InvalidReport(MessageException): pass
class InvalidClientVersion(MessageException): pass
class InvalidServerVersion(MessageException): pass
# PermissionDenied
class InvalidLogin(PermissionDenied): "Invalid username or password"


class UnknownException(Exception):
    def __str__(self):
        return "%s %s" % (self.eName, self.eArgs)

    def __init__(self, eName, eArgs):
        self.eName = eName
        self.eArgs = eArgs

# Make only exceptions importable as "from mint_error import *"
import types
__all__ = []
for name, obj in locals().copy().iteritems():
    if isinstance(obj, types.ClassType) and issubclass(obj, Exception):
        __all__.append(name)

#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

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
            from mint.config import isRBO
            project = isRBO() and "project" or "product"
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
        if isinstance(blob, (str, unicode)):
            ret = cls()
            ret.msg = blob
            return ret
        return cls(*tuple(blob))

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
class BuildPublished(MintError):
    "The referenced build is already part of a published release."
class BuildEmpty(MintError):
    "The referenced build has no files and cannot be published."
class ConfigurationMissing(MintError):
    "The rBuilder configuration is missing."
    # this init must be in here because this gets thrown from config.py
    def __init__(self):
        self.msg = self.__doc__
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
class DuplicateProductVersion(MintError): "Product version already exists"
class InvalidHostname(MintError):
    "Invalid hostname: must start with a letter and contain only " \
        "letters, numbers, and hyphens."
class LabelMissing(MintError):
    "%(Project)s label does not exist"
class FailedToLaunchAMIInstance(MintError):
    "Failed to launch AMI instance."
class FileMissing(MintError): "The referenced file does not exist."
class GroupAlreadyExists(MintError): "Group already exists"
class GroupTroveTemplateExists(MintError): "Template group trove already exists"
class GroupTroveEmpty(MintError): "Group cannot be empty"
class GroupTroveNameError(MintError):
    "Invalid name for group: letters, numbers, hyphens allowed."
class GroupTroveVersionError(MintError):
    "Invalid version for group: letters, numbers, periods allowed."
class HtmlTagNotAllowed(MintError): pass
class HtmlParseError(MintError): pass
class InvalidNamespace(MintError):
    "Invalid namespace: may not contain @ or : and may not be more than 16 characters"
class InvalidShortname(MintError):
    "Invalid short name: must start with a letter and contain only letters, numbers, and hyphens."
class InvalidProdType(MintError):
    "The selected %(project)s type is invalid."
class InvalidUsername(MintError):
    "Username may contain only letters, digits, '-', '_', and '.'"
class JobserverVersionMismatch(MintError): # LEGACY
    "Image job cannot be run."
class LastAdmin(MintError):
    "You cannot close the last administrator account."
class LastOwner(MintError):
    "You cannot orphan a %(project)s with developers"
class MailError(MintError): "There was a problem sending email."
class MailingListException(MintError): pass
class MaintenanceMode(MintError): "Repositories are currently offline."
class MessageException(MintError): pass
class MultipleImageTypes(MintError):
    "The build has multiple image types specified."
class NoMirrorLoadDiskFound(MintError):
    "No mirror preload disk was found attached to your appliance."
class NoBuildsDefinedInBuildDefinition(MintError):
    "No images in image set."
class NoImageGroupSpecifiedForProductDefinition(MintError):
    "No imageGroup specified to build in the product definition."
class NotEntitledError(MintError):
    "The rBuilder is not entitled to a required resource. Please " \
        "contact your administrator."
class ParameterError(MintError):
    "A required parameter had an incorrect data type."
class PermissionDenied(MintError): "Permission Denied"
class ProductDefinitionVersionNotFound(MintError):
    "The product definition for the specified product version was not found."
class ProductVersionNotFound(MintError):
    "The specified product version was not found."
class ProductVersionInvalid(MintError):
    "The specified product major version is invalid."
class ProductDefinitionVersionExternalNotSup(MintError):
    "Product versions are not currently supported on external products."
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
    "%(Project)s owner attempted to manipulate a %(project)s user in an " \
        "illegal fashion"
class UpdateServiceNotFound(MintError):
    "The Update Service was not found."
class PackageCreatorError(MintError):
    "Package Creator Error:"

BuildFileUrlMissing = BuildFileMissing

# Exceptions with arguments
class DuplicateItem(MintError):
    def __init__(self, item = "item"):
        MintError.__init__(self)
        self.item = item

    def freeze(self): return (self.item,)

    def __str__(self):
        return "Duplicate item in %s" % self.item

class InvalidLabel(MintError):
    def __init__(self, label):
        self.label = label

    def freeze(self): return (self.label,)

    def __str__(self):
        return "The generated development label %s is invalid. This can be caused by an invalid short name, namespace, or version." % self.label

class ItemNotFound(MintError):
    def __init__(self, item = "item"):
        MintError.__init__(self)
        self.item = item

    def freeze(self): return (self.item,)

    def __str__(self):
        return "Requested %s not found" % self.item

class MethodNotSupported(MintError):
    def __init__(self, method):
        MintError.__init__(self)
        self.method = method

    def freeze(self): return (self.method,)

    def __str__(self):
        return "Method not supported by XMLRPC server: %s" % self.method

class ProductDefinitionError(MintError):
    def __init__(self, reason):
        self.reason = reason

    def freeze(self): return (self.reason,)

    def __str__(self):
        return "There is was a problem that occurred when tryin to access the product definition for %s" % self.reason

class UnmountFailed(MintError):
    def __init__(self, dev):
        MintError.__init__(self)
        self.dev = dev

    def freeze(self): return (self.dev,)

    def __str__(self):
        return "Unable to automatically unmount %s; please manually " \
            "unmount" % self.dev

class UpToDateException(MintError):
    def __init__(self, table = "Unknown Table"):
        MintError.__init__(self)
        self.table = table

    def freeze(self): return (self.msg,)

    def __str__(self):
        return "The table '%s' is not up to date" % self.table

class InvalidBuildOption(MintError):
    def __init__(self, desc):
        MintError.__init__(self)
        self.desc = desc

    def freeze(self): return (self.desc,)

    def __str__(self):
        return "Invalid value for %s" % self.desc

class BuildOptionValidationException(MintError):
    def __init__(self, errlist):
        MintError.__init__(self)
        self.errlist = errlist

    def freeze(self): return (self.errlist,)

    def __str__(self):
        return "The following errors occurred: %s" % ", ".join(self.errlist)
    
class TroveNotFoundForBuildDefinition(MintError):
    "The trove for one or more images was not found."
    def __init__(self, errlist):
        MintError.__init__(self)
        self.errlist = errlist

    def freeze(self): return (self.errlist,)

    def __str__(self):
        return "The following errors occurred: %s" % ", ".join(self.errlist)

class UpdateServiceAuthError(MintError):
    def __init__(self, hostname):
        MintError.__init__(self)
        self.hostname = hostname

    def freeze(self): return (self.hostname,)

    def __str__(self):
        return "The credentials you supplied to access the Update " \
                "Service on %s were incorrect or are not part of the " \
                "admin role on the Update Service." % self.hostname

class UpdateServiceConnectionFailed(MintError):
    def __init__(self, hostname, errmsg):
        MintError.__init__(self)
        self.hostname = hostname
        self.errmsg = errmsg

    def freeze(self): return (self.hostname, self.errmsg)

    def __str__(self):
        return "The Update Service on %s could not be contacted. " \
                "(Reason: %s)" % (self.hostname, self.errmsg)

class UpdateServiceUnknownError(MintError):
    def __init__(self, hostname):
        MintError.__init__(self)
        self.hostname = hostname

    def freeze(self): return (self.hostname,)

    def __str__(self):
        return "An unknown error occurred when attempting to " \
                "configure the Update Service on %s." % self.hostname

class PublishedReleaseMirrorRole(MintError):
    def __init__(self, err = "Unknown error"):
        MintError.__init__(self)
        self.err = err

    def freeze(self): return (self.err,)

    def __str__(self):
        return "Release cannot be published due to an error adding the mirror role/user: %s" % self.err

class DatabaseVersionMismatch(MintError):
    def __init__(self, currentVersion):
        MintError.__init__(self)
	from mint import schema
        self.currentVersion = currentVersion
        self.requiredVersion = schema.RBUILDER_DB_VERSION

    def freeze(self): return (self.currentVersion, self.requiredVersion)

    def __str__(self):
        return "The current database schema does not match the " \
            "version required by this version of rBuilder. " \
            "Current version is %s; required version is %s." % (
                self.currentVersion, self.requiredVersion)
            
class ProductDefinitionInvalidStage(MintError):
    def __init__(self, msg):
        MintError.__init__(self)
        self.msg = msg

    def freeze(self): return (self.msg,)

    def __str__(self):
        return "Invalid product definition stage: %s" % self.msg

class PackageCreatorValidationError(PackageCreatorError):
    "Package Creator Validation Error:"
    def __init__(self, reasons):
        PackageCreatorError.__init__(self)
        self.reasons = reasons

    def freeze(self): return (self.reasons,)

    def __str__(self):
        return "Field validation failed: %s" % ', '.join(self.reasons)

class ProductDefinitionLabelLookupError(MintError):
    "Product Definition Label Lookup Error:"
    def __init__(self, label, possibles):
        MintError.__init__(self)
        self.lookup = label
        self.set = possibles

    def freeze(self): return (self.lookup, self.set)

    def __str__(self):
        return self.msg + " Could not map the label %s to a product definition.  The versioned default labels are %s" % (self.lookup, ", ".join(self.set))

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

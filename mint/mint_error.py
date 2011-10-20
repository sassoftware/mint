#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

class InternalMintError(Exception):
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


### Internal errors -- these are fatal if uncaught
class RepositoryDatabaseError(InternalMintError):
    "Unable to open the repository database"


### Marshallable errors -- these go over XMLRPC
class MintError(InternalMintError):
    status = 403

class PermissionDenied(MintError): 
    "Permission Denied"
    status = 403

class ServerError(MintError):
    status = 500

class InvalidError(MintError):
    status = 400

class MissingError(MintError):
    status = 404

class ConflictError(MintError):
    status = 409

class AdminSelfDemotion(PermissionDenied): "You cannot demote yourself."
class AlreadyConfirmed(InvalidError):
    "Your registration has already been confirmed"

class AuthRepoError(ServerError):
    "Authentication token could not be manipulated."

class BuildDataNameError(InvalidError):
    "Named value is not in data template."
class BuildFileMissing(MissingError):
    "The referenced build file doesn't exist."
class BuildMissing(MissingError): 
    "The referenced build does not exist."
class BuildPublished(PermissionDenied):
    "The referenced build is already part of a release."

class BuildEmpty(ConflictError):
    "The referenced build has no files and cannot be released."
class BuildSystemDown(ServerError):
    "There was a problem contacting the build system."
class ConfigurationMissing(ServerError):
    "The rBuilder configuration is missing."
    # this init must be in here because this gets thrown from config.py
    def __init__(self):
        self.msg = self.__doc__
class ConfirmError(ServerError):
    "Your registration could not be confirmed"


class DeleteLocalUrlError(PermissionDenied):
    "Deleting a local build file is not supported via this interface."
class DuplicateHostname(PermissionDenied):
    "A %(project)s using this hostname already exists"
class DuplicateShortname(PermissionDenied):
    "A %(project)s using this shortname already exists"

class DuplicateJob(PermissionDenied):
    "A conflicting job is already in progress"
class DuplicateName(PermissionDenied):
    "A %(project)s using this title already exists"
class DuplicateLabel(PermissionDenied): 
    "Label already exists"
class DuplicateProductVersion(PermissionDenied): 
    "Product version already exists"
class EC2NotConfigured(PermissionDenied):
    "This rBuilder is missing information " \
    "necessary to communicate with EC2.  Please consult your site administrator."
class InvalidHostname(InvalidError):
    "Invalid hostname: must start with a letter and contain only " \
        "letters, numbers, and hyphens."
class LabelMissing(MissingError):
    "%(Project)s label does not exist"
class FailedToLaunchAMIInstance(ServerError):
    "Failed to launch AMI instance."
class FileMissing(MissingError): 
    "The referenced file does not exist."
class GroupAlreadyExists(PermissionDenied): "Group already exists"
class GroupTroveTemplateExists(PermissionDenied): "Template group trove already exists"
class GroupTroveEmpty(PermissionDenied): "Group cannot be empty"
class GroupTroveNameError(InvalidError):
    "Invalid name for group: letters, numbers, hyphens allowed."
class GroupTroveVersionError(InvalidError):
    "Invalid version for group: letters, numbers, periods allowed."
class HtmlTagNotAllowed(InvalidError): pass
class HtmlParseError(InvalidError): pass
class InvalidNamespace(InvalidError):
    "Invalid namespace: may not contain @ or : and may not be more than 16 characters"
class InvalidShortname(InvalidError):
    "Invalid short name: must start with a letter and contain only letters, numbers, and hyphens."
class InvalidProdType(InvalidError):
    "The selected %(project)s type is invalid."
class InvalidUsername(InvalidError):
    "Username may contain only letters, digits, '-', '_', '.', '\', and '@'"
class JobserverVersionMismatch(ServerError): # LEGACY
    "Image job cannot be run."
class LastAdmin(PermissionDenied):
    "You cannot close the last administrator account."
class LastOwner(PermissionDenied):
    "You cannot orphan a %(project)s with developers"
class MailError(ServerError): 
    "There was a problem sending email."
    status = 500

class MailingListException(ServerError): pass
class MaintenanceMode(ServerError): "Repositories are currently offline."
class MessageException(ServerError): pass
class MultipleImageTypes(InvalidError):
    "The build has multiple image types specified."
class NoMirrorLoadDiskFound(InvalidError):
    "No mirror preload disk was found attached to your appliance."
class NoBuildsDefinedInBuildDefinition(InvalidError):
    "No images in image set."
class NoImageGroupSpecifiedForProductDefinition(InvalidError):
    "No imageGroup specified to build in the product definition."
class NotEntitledError(PermissionDenied):
    "The rBuilder is not entitled to a required resource. Please " \
        "contact your administrator."
class ParameterError(InvalidError):
    "A required parameter had an incorrect data type."
class PlatformDefinitionNotFound(MissingError): "The platform definition was not found."
class PublicToPrivateConversionError(PermissionDenied):
    "Converting public products to private products is not supported."
class ProductDefinitionVersionNotFound(MissingError):
    "The product definition for the specified product version was not found."
class ProductVersionNotFound(MissingError):
    "The specified product version was not found."
class ProductVersionInvalid(InvalidError):
    "The specified product major version is invalid."
class ProductDefinitionVersionExternalNotSup(PermissionDenied):
    "Product versions are not currently supported on external products."
class PublishedReleaseEmpty(ConflictError):
    "The referenced release has no builds and cannot be published."
class PublishedReleaseMissing(MissingError):
    "The referenced release does not exist."
class PublishedReleaseNotPublished(ConflictError):
    "Release has already been unpublished."
class PublishedReleasePublished(ConflictError):
    "Release has already been published."
class RmakeRepositoryExistsError(PermissionDenied):
    "The internal rMake repository is already configured."
class SchemaMigrationError(ServerError): pass
class TargetMissing(MissingError):
    "Target does not exist"
class TargetExists(PermissionDenied):
    "target already exists"
class TooManyAMIInstancesPerIP(PermissionDenied):
    "Too many AMI instances have been launched from this IP " \
        "address. Please try again later."    
class AMIInstanceDoesNotExist(MissingError):
    "The AMI instance does not exist, it may have already been deleted."
class TroveNotSet(ConflictError):
    "This build is not associated with a group."
class IllegalUsername(InvalidError): "The username selected cannot be used."
class UserAlreadyAdmin(PermissionDenied): "User is already an administrator."
class UserAlreadyExists(PermissionDenied): "User already exists"
class UserInduction(PermissionDenied):
    "%(Project)s owner attempted to manipulate a %(project)s user in an " \
        "illegal fashion"
class UpdateServiceNotFound(MissingError):
    "The Update Service was not found."
class SearchPathError(ServerError):
    "Search Path Error:"
class PackageCreatorError(ServerError):
    "Package Creator Error:"
class NoImagesDefined(ServerError):
    "Package Creator Error:"
class OldProductDefinition(ServerError):
    "Package Creator Error:"

BuildFileUrlMissing = BuildFileMissing

# Exceptions with arguments
class DuplicateItem(InvalidError):
    def __init__(self, item = "item"):
        MintError.__init__(self)
        self.item = item

    def freeze(self): return (self.item,)

    def __str__(self):
        return "Duplicate item in %s" % self.item

class InvalidLabel(InvalidError):
    def __init__(self, label):
        self.label = label

    def freeze(self): return (self.label,)

    def __str__(self):
        return "The generated development label %s is invalid. This can be caused by an invalid short name, namespace, or version." % self.label

class ItemNotFound(MissingError):
    def __init__(self, item = "item"):
        MintError.__init__(self)
        self.item = item

    def freeze(self): return (self.item,)

    def __str__(self):
        return "Requested %s not found" % self.item

class MethodNotSupported(PermissionDenied):
    def __init__(self, method):
        MintError.__init__(self)
        self.method = method

    def freeze(self): return (self.method,)

    def __str__(self):
        return "Method not supported by XMLRPC server: %s" % self.method
    
class RepositoryAlreadyExists(PermissionDenied):
    def __init__(self, projectName):
        MintError.__init__(self)
        self.projectName = projectName

    def freeze(self): return (self.projectName,)

    def __str__(self):
        return "A repository for '%s' already exists or was not properly deleted." % self.projectName
    
class ProjectNotDeleted(ServerError):
    def __init__(self, projectName):
        MintError.__init__(self)
        self.projectName = projectName

    def freeze(self): return (self.projectName,)

    def __str__(self):
        return "Unable to delete '%s'.  See the error log for more information." % self.projectName

class ProductDefinitionError(ServerError):
    def __init__(self, reason):
        self.reason = reason

    def freeze(self): return (self.reason,)

    def __str__(self):
        return "There was a problem that occurred when trying to access the product definition for %s" % self.reason

class UnmountFailed(ServerError):
    def __init__(self, dev):
        MintError.__init__(self)
        self.dev = dev

    def freeze(self): return (self.dev,)

    def __str__(self):
        return "Unable to automatically unmount %s; please manually " \
            "unmount" % self.dev

class UpToDateException(ServerError):
    def __init__(self, table = "Unknown Table"):
        MintError.__init__(self)
        self.table = table

    def freeze(self): return (self.msg,)

    def __str__(self):
        return "The table '%s' is not up to date" % self.table

class InvalidBuildOption(InvalidError):
    def __init__(self, desc):
        MintError.__init__(self)
        self.desc = desc

    def freeze(self): return (self.desc,)

    def __str__(self):
        return "Invalid value for %s" % self.desc

class BuildOptionValidationException(InvalidError):
    def __init__(self, errlist):
        MintError.__init__(self)
        self.errlist = errlist

    def freeze(self): return (self.errlist,)

    def __str__(self):
        return "The following error(s) occurred: %s" % ", ".join(self.errlist)
    
class TroveNotFoundForBuildDefinition(MissingError):
    "The trove for one or more images was not found."
    def __init__(self, errlist):
        MintError.__init__(self)
        self.errlist = errlist

    def freeze(self): return (self.errlist,)

    def __str__(self):
        return "The following error(s) occurred: %s" % ", ".join(self.errlist)

class UpdateServiceAuthError(MintError):
    def __init__(self, hostname):
        MintError.__init__(self)
        self.hostname = hostname

    def freeze(self): return (self.hostname,)

    def __str__(self):
        return "The credentials you supplied to access the Update " \
                "Service on %s were incorrect or are not part of the " \
                "admin role on the Update Service." % self.hostname

class UpdateServiceConnectionFailed(ServerError):
    def __init__(self, hostname, errmsg):
        MintError.__init__(self)
        self.hostname = hostname
        self.errmsg = errmsg

    def freeze(self): return (self.hostname, self.errmsg)

    def __str__(self):
        return "The Update Service on %s could not be contacted. " \
                "(Reason: %s)" % (self.hostname, self.errmsg)

class UpdateServiceUnknownError(ServerError):
    def __init__(self, hostname):
        MintError.__init__(self)
        self.hostname = hostname

    def freeze(self): return (self.hostname,)

    def __str__(self):
        return "An unknown error occurred when attempting to " \
                "configure the Update Service on %s." % self.hostname

class PublishedReleaseMirrorRole(ServerError):
    def __init__(self, err = "Unknown error"):
        MintError.__init__(self)
        self.err = err

    def freeze(self): return (self.err,)

    def __str__(self):
        return "Release cannot be published due to an error adding the mirror role/user: %s" % self.err

class DatabaseVersionMismatch(ServerError):
    def __init__(self, currentVersion):
        MintError.__init__(self)
	from mint.db import schema
        self.currentVersion = currentVersion
        self.requiredVersion = schema.RBUILDER_DB_VERSION

    def freeze(self): return (self.currentVersion, self.requiredVersion)

    def __str__(self):
        return "The current database schema does not match the " \
            "version required by this version of rBuilder. " \
            "Current version is %s; required version is %s." % (
                self.currentVersion, self.requiredVersion)
            
class ProductDefinitionInvalidStage(InvalidError):
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

class ProductDefinitionLabelLookupError(ServerError):
    "Product Definition Label Lookup Error:"
    def __init__(self, label, possibles):
        MintError.__init__(self)
        self.lookup = label
        self.set = possibles

    def freeze(self): return (self.lookup, self.set)

    def __str__(self):
        return self.msg + " Could not map the label %s to a product definition.  The versioned default labels are %s" % (self.lookup, ", ".join(self.set))

class EC2Exception(ServerError):
    "A generic EC2 exception"
    def __init__(self, ec2ResponseObj):
        MintError.__init__(self)
        self.ec2ResponseObj = ec2ResponseObj

    def freeze(self): 
        return self.ec2ResponseObj.freeze()
    
    @classmethod
    def thaw(cls, blob):
        from mint import ec2
        ec2ResponseObj = ec2.ErrorResponseObject()
        ec2ResponseObj.thaw(blob)
        return cls(ec2ResponseObj)

    def __str__(self):
        errlist = []
        for error in self.ec2ResponseObj.errors:
            errlist.append(error['message'])
        return ", ".join(errlist)

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
import inspect
__all__ = []
for name, obj in locals().copy().iteritems():
    if inspect.isclass(obj) and issubclass(obj, Exception):
        __all__.append(name)

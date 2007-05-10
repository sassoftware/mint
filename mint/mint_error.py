#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

class MintError(Exception):
    args = []

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

class MessageException(MintError):
    def __init__(self, msg = "Unknown exception"):
        self.msg = msg
    def __str__(self):
        return self.msg

class BuildMissing(MintError):
    def __str__(self):
        return "The referenced build does not exist."

class FileMissing(MintError):
    def __str__(self):
        return "The referenced file does not exist."

class BuildFileMissing(MintError):
    def __str__(self):
        return "The referenced build file doesn't exist."

class BuildFileUrlMissing(MintError):
    def __str__(self):
        return "The referenced build file doesn't exist."

class DeleteLocalUrlError(MintError):
    def __str__(self):
        return "Deleting a local build file is not supported via this interface."

class BuildPublished(MintError):
    def __str__(self):
        return "The referenced build is already part of a published release."

class BuildEmpty(MintError):
    def __str__(self):
        return "The referenced build has no files and cannot be published."

class PublishedReleaseEmpty(MintError):
    def __str__(self):
        return "The referenced release has no builds and cannot be published."

class PublishedReleasePublished(MintError):
    def __str__(self):
        return "Release has already been published."

class PublishedReleaseNotPublished(MintError):
    def __str__(self):
        return "Release has already been unpublished."

class PublishedReleaseMissing(MintError):
    def __str__(self):
        return "The referenced published release does not exist."

class JobserverVersionMismatch(MintError):
    def __str__(self):
        return self.msg

    def __init__(self, msg = "Image job cannot be run."):
        self.msg = msg

class UserAlreadyAdmin(MintError):
    def __str__(self):
        return "User is already an administrator."

class AdminSelfDemotion(MintError):
    def __str__(self):
        return self.msg

    def __init__(self, msg = "You cannot demote yourself."):
        self.msg = msg

class LastAdmin(MintError):
     def __str__(self):
         return self.msg

     def __init__(self, msg = "You cannot close your account since you are the only owner of a project."):
         self.msg = msg

class MaintenanceMode(MintError):
    def __str__(self):
        return self.msg

    def __init__(self, msg = "Repositories are currently offline."):
        self.msg = msg

class ParameterError(MintError):
    def __str__(self):
        return self.reason
    def __init__(self, reason = "A required parameter had an incorrect data type."):
        self.reason = reason

class GroupTroveEmpty(MintError):
    def __str__(self):
        return self.reason
    def __init__(self, reason = "Group cannot be empty"):
        self.reason = reason

class rMakeBuildEmpty(MintError):
    def __str__(self):
        return self.reason
    def __init__(self, reason = "rMake build cannot be empty"):
        self.reason = reason

class rMakeBuildCollision(MintError):
    def __str__(self):
        return self.reason
    def __init__(self, reason = "rMake build already underway"):
        self.reason = reason

class rMakeBuildOrder(MintError):
    def __str__(self):
        return self.reason
    def __init__(self, reason = "rMake build commands submitted out of order"):
        self.reason = reason

class InvalidReport(MessageException):
    pass

class InvalidClientVersion(MessageException):
    pass

class InvalidServerVersion(MessageException):
    pass

class BuildXmlInvalid(MintError):
    def __str__(self):
        return self.reason
    def __init__(self, reason = "Invalid Build XML"):
        self.reason = reason

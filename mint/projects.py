#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#
import os
import re
import string
import socket
import sys
import time

from mint.lib import database
from mint.helperfuncs import truncateForDisplay
from mint import helperfuncs
from mint import userlevels
from mint.mint_error import *

from conary.deps import deps
from conary.conarycfg import ConaryConfiguration


class Project(database.TableObject):
    # XXX: the disabled column is slated for removal next schema upgrade --sgp
    __slots__ = ('projectId', 'creatorId', 'name', 'description', 'hostname',
        'domainname', 'namespace', 'projecturl', 'hidden', 'external',
        'isAppliance', 'disabled', 'timeCreated', 'timeModified',
        'commitEmail', 'shortname', 'prodtype', 'version', 'backupExternal',
        'fqdn', 'database', 'modified_by')

    def getItem(self, id):
        return self.server.getProject(id)

    def getCreatorId(self):
        return self.creatorId

    def getName(self):
        return self.name

    def getNameForDisplay(self, maxWordLen = 15):
        return truncateForDisplay(self.name, maxWordLen = maxWordLen)

    def getDomainname(self):
        return self.domainname
    
    def getNamespace(self):
        return self.namespace

    def getProjectUrl(self):
        return self.projecturl

    def getHostname(self):
        return self.hostname

    def getFQDN(self):
        return self.fqdn

    def getLabel(self):
        return self.server.getDefaultProjectLabel(self.id)

    def getDesc(self):
        return self.description

    def getDescForDisplay(self):
        return truncateForDisplay(self.description, maxWords=100)

    def getTimeCreated(self):
        return self.timeCreated

    def getTimeModified(self):
        return self.timeModified

    def getShortname(self):
        return self.shortname

    def getProdType(self):
        return self.prodtype

    def getVersion(self):
        return self.version

    def getMembers(self):
        return self.server.getMembersByProjectId(self.id)

    def getCommits(self):
        return self.server.getCommitsForProject(self.id)

    def getCommitEmail(self):
        return self.commitEmail

    def getUserLevel(self, userId):
        try:
            return self.server.getUserLevel(userId, self.id)
        except ItemNotFound:
            return userlevels.NONMEMBER

    def updateUserLevel(self, userId, level):
        return self.server.setUserLevel(userId, self.id, level)

    def addMemberById(self, userId, level):
        assert(level in userlevels.LEVELS)
        return self.server.addMember(self.id, userId, "", level)

    def addMemberByName(self, username, level):
        assert(level in userlevels.LEVELS)
        return self.server.addMember(self.id, 0, username, level)

    def listJoinRequests(self):
        return self.server.listJoinRequests(self.id)

    def delMemberById(self, userId):
        return self.server.delMember(self.id, userId)

    def editProject(self, projecturl, desc, name):
        return self.server.editProject(self.id, projecturl, desc, name)

    def setNamespace(self, namespace):
        return self.server.setProjectNamespace(self.id, namespace)

    def setCommitEmail(self, commitEmail):
        return self.server.setProjectCommitEmail(self.id, commitEmail)

    def setBackupExternal(self, backupExternal):
        return self.server.setBackupExternal(self.id, backupExternal)

    def getLabelIdMap(self):
        """Returns a dictionary mapping of label names to database IDs"""
        return self.server.getLabelsForProject(self.id, False, '', '')[0]

    def getConaryConfig(self, overrideAuth = False, newUser = '', newPass = ''):
        '''Creates a ConaryConfiguration object suitable for repository access
        from the same server as MintServer'''

        labelPath, repoMap, userMap, entMap = self.server.getLabelsForProject(self.id, overrideAuth, newUser, newPass)

        cfg = ConaryConfiguration(readConfigFiles=False)
        #cfg.root = ":memory:"
        #cfg.dbPath = ":memory:"

        #cfg.initializeFlavors()
        cfg.buildFlavor = deps.parseFlavor('')

        # depending on these labels being correct is bad.   
        # We don't know what valid labels for this installLabelPath is
        # so using any particular one is wrong.
        #installLabelPath = " ".join(x for x in labelPath.keys())
        #cfg.configLine("installLabelPath %s" % installLabelPath)

        cfg.repositoryMap.update(dict((x[0], x[1]) for x in repoMap.items()))
        for host, authInfo in userMap:
            cfg.user.addServerGlob(host, authInfo[0], authInfo[1])
        for host, entitlement in entMap:
            cfg.entitlement.addEntitlement(host, entitlement[1])

        internalConaryProxies, httpProxies = self.server.getProxies()
        cfg = helperfuncs.configureClientProxies(cfg, internalConaryProxies,
                httpProxies, internalConaryProxies)
        return cfg

    def addLabel(self, label, url, authType='none', username='', password='', entitlement=''):
        return self.server.addLabel(self.id, label, url, authType, username, password, entitlement)

    def editLabel(self, labelId, label, url, authType, username, password,
            entitlement):
        return self.server.editLabel(labelId, label, url, authType, username,
            password, entitlement)

    def removeLabel(self, labelId):
        return self.server.removeLabel(self.id, labelId)

    def addUserKey(self, username, keydata):
        return self.server.addUserKey(self.id, username, keydata)

    def projectAdmin(self, userName):
        return self.server.projectAdmin(self.id, userName)

    def lastOwner(self, userId):
        return self.server.lastOwner(self.id, userId)

    def onlyOwner(self, userId):
        return self.server.onlyOwner(self.id, userId)

    def orphan(self):
        pass

    def adopt(self, auth):
        self.addMemberByName(auth.username, userlevels.OWNER)

    def getUrl(self, baseUrl=None):
        if not baseUrl:
            baseUrl = 'http://%s%s' % (self.server._cfg.siteHost,
                    self.server._cfg.basePath)
        return '%sproject/%s/' % (baseUrl, self.hostname)

    def getBuilds(self):
        return self.server.getBuildsForProject(self.id)

    def getUnpublishedBuilds(self):
        return self.server.getUnpublishedBuildsForProject(self.id)

    def getPublishedReleases(self):
        return self.server.getPublishedReleasesByProject(self.id)

    def getApplianceValue(self):
        if not self.isAppliance:
            if self.isAppliance == 0:
                return "no"
            else:
                return "unknown"
        else:
            return "yes"

    def getProductVersionList(self):
        return self.server.getProductVersionListForProduct(self.id)

    def getDefaultImageGroupName(self):
        return "group-%s-dist" % self.shortname.lower()

    def resolveExtraTrove(self, specialTroveName, imageGroupVersion,
            imageGroupFlavor, specialTroveVersion='', specialTroveFlavor=''):
        """ 
        Resolves an extra trove for a build. Returns a full TroveSpec
        for that trove if found, or an empty string if not found.

        Note that this function is used to resolve the following troves
        commonly used for builds:
        - I{anaconda-custom}
        - I{anaconda-templates}
        - I{media-template}

        In the case of resolving I{anaconda-templates}, the C{MintConfig}
        parameter I{anacondaTemplatesFallback} is used as the default
        searchPath for the trove if all else fails.

        @param specialTroveName: the name of the special trove (e.g.
            'anaconda-templates')
        @type specialTroveName: C{str}
        @param imageGroupVersion: a frozen Version object for the image
            group intended to be used with the build
        @type imageGroupVersion: C{str} (frozen Version object)
        @param imageGroupFlavor: a frozen Flavor object for the image
            group intended to be used with the build
        @type imageGroupFlavor: C{str} (frozen Flavor object)
        @param specialTroveVersion: (optional) A version of the special trove,
            often a label. If no version is given, the imageGroupVersion is used
            instead.
        @type specialTroveVersion: C{str}
        @param specialTroveFlavor: (optional) A flavor string for the special trove
            (e.g. 'is: x86'). If no flavor string is used, the imageGroupFlavor
            is used instead.
        @type specialTroveVersion: C{str}
        @returns The TroveSpec of the special trove, or an empty string
            if no suitable trove was found.
        @rtype C{str}
        """
        if imageGroupVersion is None:
            imageGroupVersion = ''
        elif hasattr(imageGroupVersion, 'asString'):
            imageGroupVersion = imageGroupVersion.asString()
        if imageGroupFlavor is None:
            imageGroupFlavor = ''
        elif hasattr(imageGroupFlavor, 'freeze'):
            imageGroupFlavor = imageGroupFlavor.freeze()

        if specialTroveVersion is None:
            specialTroveVersion = ''
        elif hasattr(specialTroveVersion, 'asString'):
            specialTroveVersion = specialTroveVersion.asString()
        if specialTroveFlavor is None:
            specialTroveFlavor = ''
        elif hasattr(specialTroveFlavor, 'freeze'):
            specialTroveFlavor = specialTroveFlavor.freeze()

        return self.server.resolveExtraTrove(self.id,
                specialTroveName, specialTroveVersion, specialTroveFlavor,
                imageGroupVersion, imageGroupFlavor)


class ProductVersions(database.TableObject):

    __slots__ = ( 'productVersionId',
                  'projectId',
                  'namespace',
                  'name',
                  'description',
                )

    def getItem(self, id):
        return self.server.getProductVersion(id)

validHost = re.compile('^[a-zA-Z][a-zA-Z0-9\-]*$')
# valid product version
validProductVersion = re.compile('^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*$')
validLabel = re.compile('^[a-zA-Z][a-zA-Z0-9\-\@\.\:]*$')

def _validateHostname(hostname, domainname, resHosts):
    if not hostname:
        raise InvalidHostname
    if validHost.match(hostname) == None:
        raise InvalidHostname
    if hostname in resHosts:
        raise InvalidHostname
    if (hostname + "." + domainname) == socket.gethostname():
        raise InvalidHostname
    return None

def _validateShortname(shortname, domainname, resHosts):
    if not shortname:
        raise InvalidShortname
    if validHost.match(shortname) == None:
        raise InvalidShortname
    if shortname in resHosts:
        raise InvalidShortname
    if (shortname + "." + domainname) == socket.gethostname():
        raise InvalidShortname
    return None

def _validateNamespace( namespace):
    v = helperfuncs.validateNamespace(namespace)
    if v != True:
        raise InvalidNamespace

def _validateProductVersion(version):
    if not version:
        raise ProductVersionInvalid
    if not validProductVersion.match(version):
        raise ProductVersionInvalid
    return None

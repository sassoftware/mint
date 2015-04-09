#
# Copyright (c) SAS Institute Inc.
#
import re
import socket

from mint.lib import database
from mint.helperfuncs import truncateForDisplay
from mint import helperfuncs
from mint import userlevels
from mint import mint_error


class Project(database.TableObject):
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

    def getCommitEmail(self):
        return self.commitEmail

    def getUserLevel(self, userId):
        try:
            return self.server.getUserLevel(userId, self.id)
        except mint_error.ItemNotFound:
            return userlevels.NONMEMBER

    def editProject(self, projecturl, desc, name):
        return self.server.editProject(self.id, projecturl, desc, name)

    def getLabelIdMap(self):
        """Returns a dictionary mapping of label names to database IDs"""
        return self.server.getLabelsForProject(self.id, False, '', '')[0]

    def addLabel(self, label, url, authType='none', username='', password='', entitlement=''):
        return self.server.addLabel(self.id, label, url, authType, username, password, entitlement)

    def editLabel(self, labelId, label, url, authType, username, password,
            entitlement):
        return self.server.editLabel(labelId, label, url, authType, username,
            password, entitlement)

    def removeLabel(self, labelId):
        return self.server.removeLabel(self.id, labelId)

    def getUrl(self, baseUrl=None):
        if not baseUrl:
            baseUrl = 'http://%s%s' % (self.server._cfg.siteHost,
                    self.server._cfg.basePath)
        return '%sproject/%s/' % (baseUrl, self.hostname)

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


class ProductVersions(database.TableObject):

    __slots__ = ( 'productVersionId',
                  'projectId',
                  'namespace',
                  'name',
                  'description',
                  'label',
                )

    def getItem(self, id):
        return self.server.getProductVersion(id)

validHost = re.compile('^[a-zA-Z][a-zA-Z0-9\-]*$')
# valid product version
validProductVersion = re.compile('^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*$')
validLabel = re.compile('^[a-zA-Z][a-zA-Z0-9\-\@\.\:]*$')

def _validateHostname(hostname, domainname, resHosts):
    if not hostname:
        raise mint_error.InvalidHostname
    if validHost.match(hostname) == None:
        raise mint_error.InvalidHostname
    if hostname in resHosts:
        raise mint_error.InvalidHostname
    if (hostname + "." + domainname) == socket.gethostname():
        raise mint_error.InvalidHostname
    return None

def _validateShortname(shortname, domainname, resHosts):
    if not shortname:
        raise mint_error.InvalidShortname
    if validHost.match(shortname) == None:
        raise mint_error.InvalidShortname
    if shortname in resHosts:
        raise mint_error.InvalidShortname
    if (shortname + "." + domainname) == socket.gethostname():
        raise mint_error.InvalidShortname
    return None

def _validateNamespace( namespace):
    v = helperfuncs.validateNamespace(namespace)
    if v != True:
        raise mint_error.InvalidNamespace

def _validateProductVersion(version):
    if not version:
        raise mint_error.ProductVersionInvalid
    if not validProductVersion.match(version):
        raise mint_error.ProductVersionInvalid
    return None

#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

import logging
import os
import urllib2
import time
from conary import conarycfg
from conary.lib.cfg import ConfigFile
from conary.lib.cfgtypes import CfgString
from conary.lib.digestlib import sha1
from conary.lib.util import copyfileobj
from StringIO import StringIO
from xobj import xobj

from mint.lib.unixutils import atomicOpen, hashFile
from mint.rest.api.models import siteauth as model

log = logging.getLogger(__name__)


class AuthzConfig(ConfigFile):
    #pylint: disable-msg=R0904
    genUrl = (CfgString, 'https://entitlements.rpath.com/key',
            "URL which we will fetch to generate a new key")
    cachePath = (CfgString, 'authorization.xml',
            "Path where the XML response will be cached, relative to"
            "this configuration file.")
    lastSuccess = (CfgString, None,
            "Date on which the entitlement service last "
            "provided a valid response")


# xobj bits
class XML_href(xobj.XObj):
    _xobj = xobj.XObjMetadata(attributes={'href': str})


class XML_ServiceLevel(xobj.XObj):
    _xobj = xobj.XObjMetadata(attributes={
        'status': str,
        'expired': str, # bool
        'daysRemaining': int,
        'limited': str, # bool
        })


class XML_Identity(xobj.XObj):
    rbuilderId = str
    serviceLevel = XML_ServiceLevel
    registered = str


class XML_Credentials(xobj.XObj):
    key = str
    ec2ProductCodes = str


class XML_Entitlement(xobj.XObj):
    _xobj = xobj.XObjMetadata(attributes={
        'id': str,
        })

    identity = XML_Identity
    credentials = XML_Credentials
    registrationService = XML_href


class XML_AuthzDocument(xobj.Document):
    entitlement = XML_Entitlement


# authz handle
class SiteAuthorization(object):
    # Use the entitlement for this repos to migrate existing installations.
    productRepos = 'products.rpath.com'

    def __init__(self, cfgPath):
        self.cfgPath = os.path.abspath(cfgPath)
        self.cfg = self.xml = None
        self.cfgHash = self.xmlHash = None
        self.load()

    # Readers
    def _getXMLPath(self):
        return os.path.join(os.path.dirname(self.cfgPath),
                self.cfg.cachePath)

    def load(self):
        self.cfg = AuthzConfig()
        if os.path.exists(self.cfgPath):
            fObj = open(self.cfgPath)
            self.cfgHash = hashFile(fObj)
            self.cfg.readObject(self.cfgPath, fObj)
            fObj.close()

            self.loadXML()

        else:
            self.cfg = self.xml = self.cfgHash = self.xmlHash = None

    def loadXML(self, xmlPath=None):
        if xmlPath is None:
            xmlPath = self._getXMLPath()

        if os.path.exists(xmlPath):
            fObj = open(xmlPath)
            self.xmlHash = hashFile(fObj)
            self.xml = xobj.parsef(fObj, documentClass=XML_AuthzDocument)
            fObj.close()
        else:
            self.xml = self.xmlHash = None

    def refresh(self):
        if hashFile(self.cfgPath, missingOk=True) != self.cfgHash:
            self.load()
        elif self.cfg and hashFile(self._getXMLPath(),
                missingOk=True) != self.xmlHash:
            self.loadXML()

    # Writers
    def save(self):
        fObj = atomicOpen(self.cfgPath)
        self.cfg.store(fObj, False)
        fObj.commit()

    def update(self):
        """
        Fetch the entitlement XML blob for this installation.
        """
        if self.xml:
            # Have a key
            url = self.xml.entitlement.id
        else:
            # Need a key
            url = self.cfg.genUrl

        try:
            fObj = urllib2.urlopen(url)
        except:
            # Current policy is to keep trying indefinitely without
            # shutting off the rBuilder.
            log.exception("Unable to get authorization data, deferring:")
            return

        # Write XML to cache path
        self._copySave(fObj)

    def _copySave(self, fObj):
        outObj = atomicOpen(self._getXMLPath())
        copyfileobj(fObj, outObj)
        outObj.flush()

        self.loadXML(outObj.name)

        outObj.commit()
        self.cfg.lastSuccess = int(time.time())
        self.save()

    # Accessors
    def getEntitlement(self):
        if self.xml:
            return self.xml.entitlement.credentials.key
        return None

    def isValid(self):
        if self.xml:
            expired = self.xml.entitlement.identity.serviceLevel.expired
            if expired is True or (expired and expired.lower() == 'true'):
                return False
        return True

    def getExpiration(self):
        if self.xml:
            daysRemaining = self.xml.entitlement.identity.serviceLevel.daysRemaining
            if daysRemaining >= 0:
                return daysRemaining
        return None

    def getIdentityXML(self):
        if self.xml:
            return self.xml.entitlement.identity
        else:
            return None

    def getIdentityModel(self):
        if self.xml:
            ident = self.xml.entitlement.identity
            serviceLevel = model.ServiceLevel(
                    status=ident.serviceLevel.status,
                    daysRemaining=ident.serviceLevel.daysRemaining,
                    expired=ident.serviceLevel.expired.lower() == 'true',
                    limited=ident.serviceLevel.limited.lower() == 'true',
                    )
            identity = model.Identity(
                    rbuilderId=ident.rbuilderId,
                    serviceLevel=serviceLevel,
                    registered=ident.registered,
                    )
        else:
            serviceLevel = model.ServiceLevel(
                    status='Unknown',
                    daysRemaining=-1,
                    expired=True, limited=True)
            identity = model.Identity(
                    rbuilderId='',
                    serviceLevel=serviceLevel,
                    registered=False,
                    )
        return identity

#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

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

from mint.lib.unixutils import atomicOpen


AUTHZ_CONFIG_PATH = '/var/lib/rbuilder/authorization.cfg'


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
class Authorization(object):
    # Use the entitlement for this repos to migrate existing installations.
    productRepos = 'products.rpath.com'

    def __init__(self, cfgPath=AUTHZ_CONFIG_PATH):
        self.cfgPath = os.path.abspath(cfgPath)
        self.cfg = self.xml = None
        self.load()

    # Readers
    def _getXMLPath(self):
        return os.path.join(os.path.dirname(self.cfgPath),
                self.cfg.cachePath)

    def load(self):
        self.cfg = AuthzConfig()
        if os.path.exists(self.cfgPath):
            self.cfg.read(self.cfgPath)
        if os.path.exists(self._getXMLPath()):
            self.loadXML()

    def loadXML(self, xmlPath=None):
        if xmlPath is None:
            xmlPath = self._getXMLPath()
        self.xml = xobj.parsef(xmlPath, documentClass=XML_AuthzDocument)

    # Writers
    def save(self):
        fObj = atomicOpen(self.cfgPath)
        self.cfg.store(fObj, False)
        fObj.commit()

    def refresh(self, conaryCfg=None, migrationOnly=False):
        """
        Fetch the entitlement XML blob for this installation.
        """
        if self.xml: # Have a key
            url = self.xml.entitlement.id
        else: # Need a key
            if not conaryCfg:
                conaryCfg = conarycfg.ConaryConfiguration(True)

            # If there is an entitlement for the product, generate a stub
            # XML file. This eases the migration of existing installs.
            if conaryCfg.entitlement.find(self.productRepos):
                self._generateStub(conaryCfg)
                return

            # Otherwise, ask the service for a new key
            url = self.cfg.genUrl

        if migrationOnly:
            # When called from a group script, we should only act on the
            # "entitlement already configured" case.
            return

        if not url:
            # Stub entitlements have no URL to check
            return

        try:
            fObj = urllib2.urlopen(url)
        except:
            # Current policy is to keep trying indefinitely without
            # shutting off the rBuilder.
            log.exception("Unable to get authorization data, deferring:")
            return

        # Write XML to cache path
        self._copySave(fObj)

    def _generateStub(self, conaryCfg):
        """
        Use the already-configured entitlement to generate a stub identity
        for migration purposes.
        """

        entitlement = str(conaryCfg.entitlement.find(
            self.productRepos)[0][1])

        doc = XML_AuthzDocument()
        doc.entitlement = XML_Entitlement()
        doc.entitlement.id = ""
        doc.entitlement.identity = ident = XML_Identity()
        doc.entitlement.credentials = cred = XML_Credentials()

        ident.rbuilderId = sha1('stub\0' + entitlement).hexdigest()[:16]
        ident.serviceLevel = XML_ServiceLevel()
        ident.serviceLevel.status = 'Full'
        ident.serviceLevel.expired = 'false'
        ident.serviceLevel.daysRemaining = -1
        ident.serviceLevel.limited = 'false'
        ident.registered = 'true'

        cred.key = entitlement
        cred.ec2ProductCodes = ''

        self._copySave(StringIO(doc.toxml()))

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

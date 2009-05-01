#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

import logging
import os
import urllib
import urllib2
import time
from conary import conaryclient
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
    keyUrl = (CfgString, 'https://entitlements.rpath.com/key/',
            "Base URL for the enablement service's key handling")
    cachePath = (CfgString, 'authorization.xml',
            "Path where the XML response will be cached, relative to"
            "this configuration file.")
    lastSuccess = (CfgString, None,
            "Date on which the entitlement service last "
            "provided a valid response.")
    checkRepos = (CfgString, 'products.rpath.com',
            "Repository FQDN whose entitlement should be sent to the "
            "enablement server.")


# xobj bits - authorization blob
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


# xobj bits - key request
class XML_Activate(xobj.XObj):
    # group trove
    name = str
    version = str


class XML_ActivateDocument(xobj.Document):
    activate = XML_Activate


# authz handle
class Getter(object):
    def __init__(self, path, encode=False):
        self.path = path.split('.')
        self.encode = encode

    def __get__(self, instance, owner):
        if not instance.xml:
            return None
        val = instance.xml.entitlement
        for part in self.path:
            val = getattr(val, part)
        if val is None:
            return None
        if self.encode:
            return val.encode('utf8')
        else:
            return val


class SiteAuthorization(object):
    def __init__(self, cfgPath, conaryCfg=None):
        # NB: only set conaryCfg inside scripts. It enables some slow
        # methods that shouldn't be used in web handlers.
        self.cfgPath = os.path.abspath(cfgPath)
        self.conaryCfg = conaryCfg
        self.cfg = self.xml = None
        self.cfgHash = self.xmlHash = None
        self.load()

    # Readers
    def _getXMLPath(self):
        return os.path.join(os.path.dirname(self.cfgPath),
                self.cfg.cachePath)

    def load(self):
        """
        Load the enablement configuration and XML blob from disk, if present.
        """
        self.cfg = AuthzConfig()
        if os.path.exists(self.cfgPath):
            fObj = open(self.cfgPath)
            self.cfgHash = hashFile(fObj)
            self.cfg.readObject(self.cfgPath, fObj)
            fObj.close()

            self.loadXML()

        else:
            self.xml = self.cfgHash = self.xmlHash = None

    def loadXML(self, xmlPath=None):
        """
        Load the enablement XML blob from disk, if present. The configuration
        must already be loaded.
        """
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
        """
        Reload the enablement configuration and XML blob from disk if it
        has been modified since the previous load.
        """
        if hashFile(self.cfgPath, missingOk=True) != self.cfgHash:
            self.load()
        elif self.cfg and hashFile(self._getXMLPath(),
                missingOk=True) != self.xmlHash:
            self.loadXML()

    def _getKeyFromSystem(self):
        """
        Get the entitlement currently configured for the main repository.
        This is the key we will ask the enablement server about.
        """
        assert self.conaryCfg

        #pylint: disable-msg=E1101
        # ccfg does in fact have an "entitlement" member
        matches = self.conaryCfg.entitlement.find(self.cfg.checkRepos)
        if matches:
            return matches[0][1]
        else:
            return None

    def _getGroupVersion(self):
        """
        Determine the name and version of the top-level group trove.
        If there are multiple top-level groups, try to pick the most
        relevant one, otherwise fail.

        @returns: (name, version)
        """
        assert self.conaryCfg
        cli = conaryclient.ConaryClient(self.conaryCfg)

        groups = set(x[0] for x in cli.fullUpdateItemList()
                if x[0].startswith('group-'))
        name = None
        if not groups:
            log.warning("No top-level groups are installed")
            return None
        elif len(groups) == 1:
            name = groups.pop()
        else:
            for x in ('group-rbuilder-appliance', 'group-rbuilder'):
                if x in groups:
                    name = x
                    break
            else:
                log.warning("Multiple top-level groups: %s", " ".join(groups))
                return None

        matches = cli.db.findTrove(None, (name, None, None))
        return max(matches)[:2]

    # Writers
    def generate(self):
        """
        Generate and return a new entitlement key. The associated
        blob will be saved to disk as well.
        """
        groupTrove = self._getGroupVersion()
        if not groupTrove:
            log.error("Can't find top-level group to generate entitlement")
            return None
        name, version = groupTrove

        doc = XML_ActivateDocument()
        doc.activate = XML_Activate()
        doc.activate.name = name
        doc.activate.version = version.asString()

        url = self.cfg.keyUrl
        req = urllib2.Request(url, doc.toxml(), {'Content-type': 'text/xml'})

        log.info("Requesting entitlement for %s=%s from %s",
                name, version, url)

        err = None
        try:
            fObj = urllib2.urlopen(req)
        except:
            log.exception("Failed to generate entitlement:")
            return None

        self._copySaveXML(fObj)
        return str(self.xml.entitlement.credentials.key)

    def update(self):
        """
        Fetch the entitlement XML blob for this installation.

        Returns C{True} if the refresh was successful, or C{False}
        if it failed for any reason.
        """
        key = self._getKeyFromSystem()
        if key:
            url = os.path.join(self.cfg.keyUrl, urllib.quote(key))
            log.debug('Checking %s', url)

            try:
                fObj = urllib2.urlopen(url)
            except:
                # Current policy is to keep trying indefinitely without
                # shutting off the rBuilder.
                log.exception("Deferring authorization check: "
                        "unable to refresh:")
            else:
                self._copySaveXML(fObj)
                return True
        else:
            log.warning("Deferring authorization check: "
                    "no system entitlement.")
        return False

    def save(self):
        """
        Save the current configuration to disk.
        """
        fObj = atomicOpen(self.cfgPath)
        self.cfg.store(fObj, False)
        fObj.commit()

    def _copySaveXML(self, fObj):
        """
        Read the XML blob from C{fObj} (usually a HTTP response), load it,
        and write it to the cache path.
        """
        outObj = atomicOpen(self._getXMLPath())
        copyfileobj(fObj, outObj)
        outObj.flush()

        self.loadXML(outObj.name)

        outObj.commit()
        self.cfg.lastSuccess = int(time.time())
        self.save()

    # Accessors
    def isSystemKeySet(self):
        """
        Does the system have an entitlement key?

        For script use only. Do not call from a web handler.
        """
        return self._getKeyFromSystem() is not None

    def isConfigured(self):
        "Does the authorization exist and contain an entitlement key?"
        return (self.xml is not None
                and self.xml.entitlement.credentials.key is not None)

    def isValid(self):
        "Does the authorization exist and contain a non-expired entitlement?"
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

    rBuilderId = Getter('identity.rbuilderId', True)
    ec2ProductCodes = Getter('credentials.ec2ProductCodes')

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


_AUTH_CACHE = {}
def getSiteAuth(cfgPath):
    """
    Get a L{SiteAuthorization} object for the config at C{cfgPath}, using
    a cached object if one is available.
    """
    if cfgPath in _AUTH_CACHE:
        ret = _AUTH_CACHE[cfgPath]
        ret.refresh()
    else:
        ret = _AUTH_CACHE[cfgPath] = SiteAuthorization(cfgPath)
    return ret

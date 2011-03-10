#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import logging

import rpath_capsule_indexer

from conary.lib import util

from mint.rest.api import models
from mint.lib import mintutils

log = logging.getLogger(__name__)

class Field(object):
    __slots__ = [ 'name', 'value', 'required', 'description', 'prompt',
        'type', 'password', 'encrypted' ]
    name = None
    required = True
    description = None
    prompt = None
    type = None
    password = None
    encrypted = False

    def __init__(self):
        self.value = None

class Username(Field):
    name = 'username'
    required = True
    description = 'User Name'
    prompt = 'User Name'
    type = 'str'
    password = False
    encrypted = True

class UsernameOptional(Username):
    required = False

class Password(Field):
    name = 'password'
    required = True
    description = 'Password'
    prompt = 'Password'
    type = 'str'
    password = True
    encrypted = True

class PasswordOptional(Password):
    required = False

class SourceUrl(Field):
    name = 'sourceUrl'
    required = True
    description = 'Source URL'
    prompt = 'Source URL'
    type = 'str'
    password = False
    regexp = '^(http|https|ftp):\/\/.*'
    regexpDescription = 'URL must begin with ftp://, http://, or https://'

class Name(Field):
    name = 'name'
    required = True
    description = 'Name'
    prompt = 'Name'
    type = 'str'
    password = False

class ContentSourceType(object):
    __slots__ = [ 'proxyMap', '_fieldValues', ]
    fields = []
    model = None
    _ContentSourceTypeName = None

    def __init__(self, proxyMap = None):
        self.proxyMap = proxyMap
        self._fieldValues = dict((x.name, x())
            for x in self.__class__.fields)

    def __setattr__(self, attr, value):
        if attr in self.__slots__:
            return object.__setattr__(self, attr, value)
        if attr not in self._fieldValues:
            raise AttributeError(attr)

        f = self._fieldValues[attr]
        f.value = value

    def __getattr__(self, attr):
        if attr not in self._fieldValues:
            raise AttributeError(attr)
        f = self._fieldValues[attr]
        return f.value

    def getFieldNames(self):
        return [f.name for f in self.__class__.fields]

    def getEncryptedFieldNames(self):
        return [f.name for f in self.__class__.fields if f.encrypted]

    def getContentSourceTypeName(self):
        return self.__class__._ContentSourceTypeName

    def getProxyMap(self):
        return self.proxyMap

    def status(self, *args, **kw):
        raise NotImplementedError

class _RhnSourceType(ContentSourceType):
    xmlrpcUrl = 'XMLRPC'
    cfg = rpath_capsule_indexer.IndexerConfig()
    cfg.channels.append('rhel-i386-as-4')
    # Just use the rhel 4 channel label here, both rhel 4 and rhel 5 pull
    # from the same entitlement pool.

    def getDataSource(self):
        srcChannels = rpath_capsule_indexer.sourcerhn.SourceChannels(self.cfg)
        return rpath_capsule_indexer.sourcerhn.Source_RHN(srcChannels,
            self.username, self.password, proxyMap = self.proxyMap)

    def status(self):
        msg = "Cannot connect to this resource. Verify you have provided correct information."
        try:
            ds = self.getDataSource()
        except rpath_capsule_indexer.errors.RPCError, e:
            log.error("Error validating content source %s: %s" \
                        % (self.name, e))
            return (True, False, msg)
        if not ds.isValid:
            log.error("Error validating content source %s" \
                        % (self.name, ))
            return (False, False, msg)
        
        try:
            remaining = ds.getAvailableEntitlements(self.cfg.channels[0])
        except rpath_capsule_indexer.errors.RPCError, e:
            log.error("Error getting available entitlements: %s" % e)
            return(False, False, msg)

        if remaining <= 0:
            return (False, False, "Insufficient Channel Entitlements.")

        return (True, True, 'Validated Successfully.')

class Rhn(_RhnSourceType):
    fields = [Name, Username, Password]
    model = models.RhnSource
    sourceUrl = 'https://rhn.redhat.com'
    _ContentSourceTypeName = 'Red Hat Network'

class Satellite(_RhnSourceType):
    fields = [Name, Username, Password, SourceUrl]
    model = models.SatelliteSource
    _ContentSourceTypeName = 'Red Hat Satellite'

    def getDataSource(self):
        # We only need the server name
        serverName = util.urlSplit(self.sourceUrl)[3]
        srcChannels = rpath_capsule_indexer.sourcerhn.SourceChannels(self.cfg)
        return rpath_capsule_indexer.sourcerhn.Source(srcChannels, self.name,
            self.username, self.password, serverName, proxyMap = self.proxyMap)

class Proxy(Satellite):
    _ContentSourceTypeName =  'Red Hat Proxy'

class _RepositoryMetadataSourceType(ContentSourceType):
    repomdLabel = None

    def status(self):
        sourceyum = rpath_capsule_indexer.sourceyum
        url = "%s/%s" % (self.sourceUrl, self.repomdLabel)
        authUrl = mintutils.urlAddAuth(url, self.username, self.password)
        try:
            src = sourceyum.YumRepositorySource(self.repomdLabel, authUrl,
                    proxyMap=self.proxyMap)
            if src.timestamp is None:
                return (False, False,
                    "Error validating source at url %s" % url)
        except sourceyum.repomd.errors.DownloadError, e:
            return (False, False,
                'Error validating: %s: %s' % (e.code, e.msg))
        return (True, True, 'Validated Successfully.')


class Smt(_RepositoryMetadataSourceType):
    fields = [Name, UsernameOptional, PasswordOptional, SourceUrl]
    model = models.SmtSource
    _ContentSourceTypeName = 'Subscription Management Tool'
    # Use this channel to verify credentials
    repomdLabel = 'SLES10-SP3-Online/sles-10-i586'

class Nu(Smt):
    fields = [Name, Username, Password]
    model = models.NuSource
    sourceUrl = 'https://nu.novell.com/repo/$RCE'
    _ContentSourceTypeName = 'Novell Update Service'

class Repomd(_RepositoryMetadataSourceType):
    fields = [Name, UsernameOptional, PasswordOptional, SourceUrl]
    model = models.SmtSource
    _ContentSourceTypeName = 'Yum Repository'
    repomdLabel = '5/os/i386'

contentSourceTypes = {'RHN' : Rhn,
                      'satellite' : Satellite,
                      'proxy' : Proxy,
                      'nu' : Nu,
                      'SMT' : Smt,
                      'repomd' : Repomd,
                      }

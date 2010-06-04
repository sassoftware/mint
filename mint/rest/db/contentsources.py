#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import logging

import rpath_capsule_indexer

from conary.lib import util

from mint.rest.api import models

log = logging.getLogger(__name__)

class Field(object):
    name = None
    required = True
    description = None
    prompt = None
    type = None
    value = None
    password = None
    encrypted = False

class Username(Field):
    name = 'username'
    required = True
    description = 'User Name'
    prompt = 'User Name'
    type = 'str'
    password = False
    encrypted = True

class Password(Field):
    name = 'password'
    required = True
    description = 'Password'
    prompt = 'Password'
    type = 'str'
    password = True
    encrypted = True

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
    name = None
    fields = []
    model = None

    def __init__(self):
        pass

    def __setattr__(self, attr, value):
        fieldNames = self.getFieldNames()
        if attr not in fieldNames:
            raise AttributeError

        field = fieldNames.index(attr)
        f = self.fields[field] 
        f.value = value

    def __getattribute__(self, attr):
        fieldNames = object.__getattribute__(self, 'getFieldNames')()
        if attr not in fieldNames:
            return object.__getattribute__(self, attr)

        field = fieldNames.index(attr)
        f = self.fields[field] 
        return f.value

    def getFieldNames(self):
        return [f.name for f in object.__getattribute__(self, 'fields')]

    def getEncryptedFieldNames(self):
        return [f.name for f in object.__getattribute__(self, 'fields') \
                if f.encrypted]

    def status(self, *args, **kw):
        raise NotImplementedError

class Rhn(ContentSourceType):
    xmlrpcUrl = 'XMLRPC'
    fields = [Name(), Username(), Password()]
    model = models.RhnSource
    sourceUrl = 'https://rhn.redhat.com'
    cfg = rpath_capsule_indexer.IndexerConfig()
    cfg.channels.append('rhel-i386-as-4')
    # Just use the rhel 4 channel label here, both rhel 4 and rhel 5 pull
    # from the same entitlement pool.

    def __init__(self, proxies = None):
        self.name = 'Red Hat Network'
        self.__dict__['proxies'] = proxies or {}
        ContentSourceType.__init__(self)

    def getDataSource(self, proxies):
        srcChannels = rpath_capsule_indexer.SourceChannels(self.cfg)
        return rpath_capsule_indexer.Indexer.Source_RHN(srcChannels,
            self.username, self.password, proxies = proxies)

    def status(self):
        msg = "Cannot connect to this resource. Verify you have provided correct information."
        try:
            ds = self.getDataSource(self.__dict__['proxies'])
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

class Satellite(Rhn):
    fields = [Name(), Username(), Password(), SourceUrl()]
    model = models.SatelliteSource

    def __init__(self, proxies = None):
        Rhn.__init__(self, proxies=proxies)
        self.name = 'Red Hat Satellite'

    def getDataSource(self, proxies):
        # We only need the server name
        serverName = util.urlSplit(self.sourceUrl)[3]
        srcChannels = rpath_capsule_indexer.sourcerhn.SourceChannels(self.cfg)
        return rpath_capsule_indexer.sourcerhn.Source(srcChannels, self.name,
            self.username, self.password, serverName, proxies = proxies)

class Proxy(Satellite):
    def __init__(self, proxies = None):
        Satellite.__init__(self, proxies=proxies)
        self.name = 'Red Hat Proxy'

class Nu(ContentSourceType):
    fields = [Name(), Username(), Password()]
    model = models.NuSource
    sourceUrl = 'https://nu.novell.com/repo/$RCE'

    def status(self):
        # TODO fix this once support for these types have been added to the
        # rpath-capsule-indexer
        return (True, True, 'Validated Successfully.')


class Smt(Nu):
    fields = [Name(), Username(), Password(), SourceUrl()]
    model = models.SmtSource

contentSourceTypes = {'RHN' : Rhn,
                      'satellite' : Satellite,
                      'proxy' : Proxy,
                      'nu' : Nu,
                      'SMT' : Smt}

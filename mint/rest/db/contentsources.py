#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import logging
import xmlrpclib

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
    description = 'Username'
    prompt = 'Username'
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
    authUrl = 'rpc/api'
    fields = [Name(), Username(), Password()]
    model = models.RhnSource
    sourceUrl = 'https://rhn.redhat.com'

    def __init__(self):
        self.name = 'Red Hat Network'
        ContentSourceType.__init__(self)

    def status(self):
        url = self.sourceUrl
        if url.endswith('/'):
            url = url[:-1]
        url = "%s/%s" % (self.sourceUrl, self.authUrl)
        s = util.ServerProxy(url)
        msg = "Cannot connect to this resource. Verify you have provided correct information."
        try:
            s.auth.login(self.username, self.password)
            return (True, True, 'Validated Successfully.')
        except xmlrpclib.Fault, e:
            log.error("Error validating content source %s: %s" \
                        % (self.name, e))
            return (True, False, msg)
        except Exception, e:
            log.error("Error validating content source %s: %s" \
                        % (self.name, e))
            return (False, False, msg)

class Satellite(Rhn):
    authUrl = 'rpc/api'
    fields = [Name(), Username(), Password(), SourceUrl()]
    model = models.SatelliteSource

    def __init__(self):
        self.name = 'Red Hat Satellite'
        ContentSourceType.__init__(self)

class Proxy(Satellite):
    
    def __init__(self):
        self.name = 'Red Hat Proxy'
        ContentSourceType.__init__(self)

contentSourceTypes = {'RHN' : Rhn,
                      'satellite' : Satellite,
                      'proxy' : Proxy}

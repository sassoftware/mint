#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import xmlrpclib

from conary.lib import util

from mint.rest.api import models

class Field(object):
    name = None
    required = True
    description = None
    prompt = None
    type = None
    value = None
    password = None

class Username(Field):
    name = 'username'
    required = True
    description = 'Username'
    prompt = 'Username'
    type = 'str'
    password = False

class Password(Field):
    name = 'password'
    required = True
    description = 'Password'
    prompt = 'Password'
    type = 'str'
    password = True

class SourceUrl(Field):
    name = 'sourceUrl'
    required = True
    description = 'Source Url'
    prompt = 'Source Url'
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

    def __getattr__(self, attr):
        fieldNames = self.getFieldNames()
        if attr not in fieldNames:
            return object.__getattribute__(self, attr)

        field = fieldNames.index(attr)
        f = self.fields[field] 
        return f.value

    def getFieldNames(self):
        return [f.name for f in self.fields]

    def status(self, *args, **kw):
        raise NotImplementedError

class Rhn(ContentSourceType):
    name = 'Red Hat Network'
    authUrl = 'rpc/api'
    fields = [Name(), Username(), Password()]
    model = models.RhnSource
    sourceUrl = 'https://rhn.redhat.com'

    def status(self):
        url = self.sourceUrl
        if url.endswith('/'):
            url = url[:-1]
        url = "%s/%s" % (self.sourceUrl, self.authUrl)
        s = util.ServerProxy(url)
        try:
            s.auth.login(self.username, self.password)
            return (True, True, 'Validated Successfully.')
        except xmlrpclib.Fault, e:
            return (True, False, e.faultString)

class Satellite(Rhn):
    name = 'Red Hat Satellite'
    authUrl = '%s/rpc/api'
    fields = [Name(), Username(), Password(), SourceUrl()]
    model = models.SatelliteSource

class Proxy(Satellite):
    name = 'Red Hat Proxy'
    
contentSourceTypes = {'RHN' : Rhn,
                      'satellite' : Satellite,
                      'proxy' : Proxy}

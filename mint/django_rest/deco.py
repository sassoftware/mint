#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import base64

from django import http

from xobj import xobj

from mint.django_rest.rbuilder import modellib

class ACCESS(object):
    ANONYMOUS = 1
    AUTHENTICATED = 2
    ADMIN = 4
    EVENT_UUID = 8
    LOCALHOST = 16

def D(field, docstring):
    field.docstring = docstring
    return field

def _getXobjModel(request, model_names):
    xml = request.raw_post_data
    built_model = xobj.parse(xml)
    if not isinstance(model_names, list):
        model_names = [ model_names ]
    for model_name in model_names:
        submodel = getattr(built_model, model_name, None)
        if submodel is None:
            continue
        modelCls = modellib.type_map[model_name]
        return submodel, model_name, modelCls
    raise Exception("Unexpected XML")

def getHeaderValue(request, headerName):
    # HTTP_THANK_YOU_DJANGO_FOR_MANGLING_THE_HEADERS
    mangledHeaderName = 'HTTP_' + headerName.replace('-', '_').upper()
    return request.META.get(headerName, request.META.get(mangledHeaderName))

def requires(model_names, save=True, load=True):
    """
    Decorator that parses the post data on a request into the class
    specified by modelClass.
    We can specify multiple model names that we handle.
    """
    def decorate(function):

        def inner(*args, **kw):
            request = args[1]
            built_model, model_name, modelCls  = _getXobjModel(request, model_names)
            # Extract the pk field
            if modelCls._meta.has_auto_field:
                autoField = modelCls._meta.auto_field
                keyFieldName = autoField.name
                keyFieldValue = kw.get(keyFieldName)
                # This will also overwrite the field if it's present
                setattr(built_model, keyFieldName, keyFieldValue)
            # XXX This is not the ideal place to handle this
            _injectZone(request, built_model, model_name, modelCls)
            model = modelCls.objects.load_from_object(
                built_model, request, save=save, load=load)
            kw[model_name] = model
            return function(*args, **kw)
        
        return inner
    return decorate

def _injectZone(request, xobjModel, modelName, modelClass):
    if modelName != 'system' or request.method != 'POST':
        return
    headerName = 'X-rPath-Management-Zone'
    encZoneName = getHeaderValue(request, headerName)
    if encZoneName is None:
        return
    zoneName = base64.b64decode(encZoneName)
    zoneClass = modellib.type_map['zone']
    zones = list(zoneClass.objects.filter(name=zoneName))
    if not zones:
        return
    # Inject zone into xobjModel
    zone = zones[0]
    propName = 'managing_zone'
    mzone = zoneClass._xobjClass()
    mzone.href = zone.get_absolute_url(request)
    setattr(xobjModel, propName, mzone)

HttpAuthenticationRequired = http.HttpResponse(status=401)

class access(object):
    @classmethod
    def anonymous(cls, function):
        """
        Decorator that allows for anonymous access
        """
        function.ACCESS = getattr(function, 'ACCESS', 0) | ACCESS.ANONYMOUS
        return function

    @classmethod
    def admin(cls, function):
        """
        Decorator that enforces admin access
        """
        function.ACCESS = getattr(function, 'ACCESS', 0) | ACCESS.ADMIN
        return function

    @classmethod
    def authenticated(cls, function):
        """
        Decorator that enforces authenticated access
        """
        function.ACCESS = getattr(function, 'ACCESS', 0) | ACCESS.AUTHENTICATED
        return function

    @classmethod
    def event_uuid(cls, function):
        """
        Decorator that verifies a valid event id
        """
        function.ACCESS = getattr(function, 'ACCESS', 0) | ACCESS.EVENT_UUID
        return function

    @classmethod
    def localhost(cls, function):
        """
        Decorator that verifies localhost access (for management interfaces)
        """
        function.ACCESS = getattr(function, 'ACCESS', 0) | ACCESS.LOCALHOST
        return function

def return_xml(function):
    """
    Decorator that serializes a returned parser object into xml with a root
    node of modelName.
    """
    def inner(*args, **kw):
        ret_val = function(*args, **kw)
        if isinstance(ret_val, http.HttpResponse):
            return ret_val
        response = http.HttpResponse()
        response['Content-Type'] = 'text/xml'
        request = args[1]
        response.model = ret_val
        return response
    inner.__doc__ = function.__doc__
    return inner


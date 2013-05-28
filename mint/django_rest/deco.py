#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#
import base64
from django import http
from lxml import etree
from mint.django_rest.rbuilder import modellib

# Used by views too
Flags = modellib.Flags

class ACCESS(object):
    ANONYMOUS = 1
    AUTHENTICATED = 2
    ADMIN = 4
    AUTH_TOKEN = 8
    LOCALHOST = 16

def D(field, docstring, short=None):
    field.docstring = docstring
    field.shortname = short
    return field

def _getEtreeModel(request, model_names):
    xml = request.raw_post_data
    etreeModel = etree.fromstring(xml)
    if not isinstance(model_names, list):
        model_names = [ model_names ]
    for model_name in model_names:
        if etreeModel.tag != model_name:
            continue
        modelCls = modellib.type_map[model_name]
        return etreeModel, model_name, modelCls
    raise Exception("Unexpected XML")

def getHeaderValue(request, headerName):
    # HTTP_THANK_YOU_DJANGO_FOR_MANGLING_THE_HEADERS
    mangledHeaderName = 'HTTP_' + headerName.replace('-', '_').upper()
    return request.META.get(headerName, request.META.get(mangledHeaderName))

def requires(model_names, save=True, load=True, flags=None):
    """
    Decorator that parses the post data on a request into the class
    specified by modelClass.
    We can specify multiple model names that we handle.

    WARNING: load=False does not prevent database access, use xObjRequires
    instead if you're attempting to construct a model from user input
    and it's unlikely to be saveable.
    """
    if flags is None:
        flags = Flags(save=save, load=load, original_flags=None)
    def decorate(function):

        def inner(*args, **kw):
            request = args[1]
            etreeModel, model_name, modelCls  = _getEtreeModel(request, model_names)

            uqFields = dict((x.name, getattr(x, 'UpdatableKey', False))
                for x in modelCls._meta.fields if x.unique)
            uqkeyvals = [ x for x in kw.items() if x[0] in uqFields ]
            if len(uqkeyvals) > 1:
                raise Exception("Programming error: multiple unique keys present")
            if uqkeyvals:
                keyFieldName, keyFieldValue = uqkeyvals[0]
                updatable = uqFields[keyFieldName]
                # This will also overwrite the field if it's present
                if keyFieldName in modelCls._xobj.attributes:
                    if etreeModel.attrib.get(keyFieldName) is None or not updatable:
                        etreeModel.attrib[keyFieldName] = keyFieldValue
                else:
                    vals = etreeModel.xpath('/*/%s' % keyFieldName)
                    if not vals or not updatable:
                        for v in vals:
                            etreeModel.remove(v)
                        et = etreeModel.makeelement(keyFieldName)
                        et.text = keyFieldValue
                        etreeModel.append(et)
            # XXX This is not the ideal place to handle this
            _injectZone(request, etreeModel, model_name, modelCls)
            # We need to pass a new copy of the flags object, because
            # it gets modified down the road, and we don't want to
            # pollute further calls.
            model = modelCls.objects.load_from_object(
                etreeModel, request, flags=flags.copy())
            kw[model_name] = model
            return function(*args, **kw)
        
        return inner
    return decorate

def xObjRequires(model_names):
    """
    The normal requires will save an object in the database, this one
    just returns an xObj instance, because the serialization is 
    to entangled with saving/loading from the database to get Django
    instances that don't have database-relevance.

    The model required can be entirely abstract.

    Example usage:  submitting partially filled out objects
    that will rely on the view/manager to complete and act on.
    """
    def decorate(function):

        def inner(*args, **kw):
            request = args[1]
            etreeModel, model_name, modelCls  = _getEtreeModel(request, model_names)
            # is this needed here?
            _injectZone(request, etreeModel, model_name, modelCls)
            kw[model_name] = etreeModel
            return function(*args, **kw)

        return inner
    return decorate

def _injectZone(request, etreeModel, modelName, modelClass):
    systemModels = set(['system', 'systems'])
    if request.method != 'POST' or modelName not in systemModels:
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
    zone = zones[0]
    propName = 'managing_zone'
    # Inject zone into model. First remove all existing zones
    if modelName == 'system':
        systemEtrees = [ etreeModel ]
    else:
        systemEtrees = etreeModel.iterchildren('system')
    for systemEtree in systemEtrees:
        # Convert to a list since we're changing the model underneath
        for n in list(systemEtree.iterchildren(propName)):
            systemEtree.remove(n)
        systemEtree.append(systemEtree.makeelement(propName,
            id=zone.get_absolute_url(request)))

HttpAuthenticationRequired = http.HttpResponse(status=401)
HttpAuthorizationRequired  = http.HttpResponse(status=403)

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
    def auth_token(cls, function):
        """
        Decorator that verifies a valid auth token
        """
        function.ACCESS = getattr(function, 'ACCESS', 0) | ACCESS.AUTH_TOKEN
        return function

    @classmethod
    def localhost(cls, function):
        """
        Decorator that verifies localhost access (for management interfaces)
        """
        function.ACCESS = getattr(function, 'ACCESS', 0) | ACCESS.LOCALHOST
        return function

    @classmethod
    def job_token(cls, function):
        """
        Decorator that verifies a valid job token
        """
        function.ACCESS = getattr(function, 'ACCESS', 0) | ACCESS.JOB_TOKEN
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
        response.model = ret_val
        return response
    inner.__doc__ = function.__doc__
    return inner


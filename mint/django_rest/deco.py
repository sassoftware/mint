#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import re
from xml.dom import minidom

from django import http

from xobj import xobj

from mint.django_rest.rbuilder import modellib

class ACCESS(object):
    ANONYMOUS = 1
    AUTHENTICATED = 2
    ADMIN = 4
    EVENT_UUID = 8

def D(field, docstring):
    field.docstring = docstring
    return field

class Transformations(object):
    RE_StringToCamelCase = re.compile('(.)_([a-z])')
    RE_StringToUnderscore_1 = re.compile('(.)([A-Z][a-z]+)')
    RE_StringToUnderscore_2 = re.compile('([a-z0-9])([A-Z])')
    S_Group = r'\1_\2'

    @classmethod
    def strToCamelCase(cls, name):
        return cls.RE_StringToCamelCase.sub(cls._repl, name)

    @classmethod
    def nodeToCamelCase(cls, node):
        for name in cls._FieldNames:
            v = getattr(node, name, None)
            if v is not None:
                setattr(node, name, cls.strToCamelCase(v))
        for child in node.childNodes:
            cls.nodeToCamelCase(child)

    @classmethod
    def strToUnderscore(cls, name):
        s1 = cls.RE_StringToUnderscore_1.sub(cls.S_Group, name)
        return cls.RE_StringToUnderscore_2.sub(cls.S_Group, s1).lower()

    @classmethod
    def nodeToUnderscore(cls, node):
        for name in cls._FieldNames:
            v = getattr(node, name, None)
            if v is not None:
                setattr(node, name, cls.strToUnderscore(v))
        for child in node.childNodes:
            cls.nodeToUnderscore(child)

    @classmethod
    def _repl(cls, m):
        return m.group()[:-2] + m.group()[-1].upper()

    _FieldNames = ['tagName', 'nodeName']

def _getXobjModel(request, model_names):
    xml = request.raw_post_data
    doc = minidom.parseString(xml)
    root_node = doc.documentElement
    Transformations.nodeToUnderscore(root_node)
    underscore_xml = doc.toxml(encoding='UTF-8')
    built_model = xobj.parse(underscore_xml)
    if not isinstance(model_names, list):
        model_names = [ model_names ]
    for model_name in model_names:
        model_xml = Transformations.strToUnderscore(model_name)
        submodel = getattr(built_model, model_xml, None)
        if submodel is None:
            continue
        modelCls = modellib.type_map[model_name]
        return submodel, model_name, modelCls
    raise Exception("Unexpected XML")

def requires(model_names, save=True):
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
            model = modellib.type_map[model_name].objects.load_from_object(
                built_model, request, save=save)
            kw[model_name] = model
            return function(*args, **kw)

        return inner
    return decorate

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
        xml = ret_val.to_xml(request)
        doc = minidom.parseString(xml)
        Transformations.nodeToCamelCase(doc.documentElement)
        response.write(doc.toxml(encoding='UTF-8'))
        return response

    return inner

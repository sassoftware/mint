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

def str_to_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def to_underscore(node):
    for name in ['tagName', 'nodeName']:
        if hasattr(node, name):
            setattr(node, name, str_to_underscore(getattr(node, name)))

    for child in node.childNodes:
        for name in ['tagName', 'nodeName']:
            if hasattr(child, name):
                setattr(child, name, str_to_underscore(getattr(child, name)))
                to_underscore(child)

def str_to_camel_case(name):
    def repl(m):
        return m.group()[:-2] + m.group()[-1].upper()
    s1 = re.sub('(.)_([a-z])', repl, name)
    return s1

def to_camel_case(node):
    for name in ['tagName', 'nodeName']:
        if hasattr(node, name):
            setattr(node, name, str_to_camel_case(getattr(node, name)))
 
    for child in node.childNodes:
        for name in ['tagName', 'nodeName']:
            if hasattr(child, name):
                setattr(child, name, str_to_camel_case(getattr(child, name)))
                to_camel_case(child)

def _getXobjModel(request, model_names):
    xml = request.raw_post_data
    doc = minidom.parseString(xml)
    root_node = doc.documentElement
    to_underscore(root_node)
    underscore_xml = doc.toxml(encoding='UTF-8')
    built_model = xobj.parse(underscore_xml)
    if not isinstance(model_names, list):
        model_names = [ model_names ]
    for model_name in model_names:
        model_xml = str_to_underscore(model_name)
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
        to_camel_case(doc.documentElement)
        response.write(doc.toxml(encoding='UTF-8'))
        return response

    return inner

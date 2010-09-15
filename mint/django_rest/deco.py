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

def requires(model_name, save=True):
    """
    Decorator that parses the post data on a request into the class
    specified by modelClass.
    """
    def decorate(function):

        def inner(*args, **kw):
            request = args[1]
            xml = request.raw_post_data
            doc = minidom.parseString(xml)
            root_node = doc.documentElement
            to_underscore(root_node)
            underscore_xml = doc.toxml(encoding='UTF-8')
            built_model = xobj.parse(underscore_xml)
            model_xml = str_to_underscore(model_name)
            built_model = getattr(built_model, model_xml)
            model = modellib.type_map[model_name].objects.load_from_object(
                built_model, request, save=save)
            kw[model_name] = model
            return function(*args, **kw)

        return inner
    return decorate

def authErrorResponse():
    return http.HttpResponse(status=401)

def requires_admin(function):
    """
    Decorator that enforces admin access
    """
    def inner(*args, **kw):
        request = args[1]
        if not request._is_admin:
            return authErrorResponse()
        return function(*args, **kw)

    return inner

def requires_auth(function):
    """
    Decorator that enforces authenticated access
    """
    def inner(*args, **kw):
        request = args[1]
        if not request._is_authenticated:
            return authErrorResponse()
        return function(*args, **kw)

    return inner

def requires_auth_or_event_uuid(function):
    """
    Decorator that verifies authentication or a valid event id
    """
    def inner(*args, **kw):
        request = args[1]
        eventUuid = request.environ.get('X-rBuilder-Event-UUID')
        isAuthenticated = request._is_authenticated
        if not isAuthenticated:
            if request._auth != (None, None) or not eventUuid:
                # Bad authentication, or no eventUuid
                return authErrorResponse()
        if eventUuid:
            # Check if this system has such an event uuid
            systemId = args[2]
            sjobs = modellib.type_map['__systemJob'].objects.filter(
                system__pk=systemId, event_uuid=eventUuid)
            if not sjobs:
                return authErrorResponse()
        return function(*args, **kw)
    return inner

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

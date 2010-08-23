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
from mint.django_rest.rbuilder.inventory import models 

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

def requires(model_name):
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
            built_model = xobj.parse(underscore_xml)#, documentClass=DjangoDocument, typeMap=models.type_map)
            model_xml = str_to_underscore(model_name)
            built_model = getattr(built_model, model_xml)
            model = modellib.type_map[model_name].objects.load_from_object(built_model, request)
            # loaded_model = models.type_map[model_name].objects.load(built_model)
            # if not loaded_model:
                # built_model.save()
                # loaded_model = built_model
            # loaded_model.set_related()
            kw[model_name] = model
            return function(*args, **kw)

        return inner
    return decorate

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

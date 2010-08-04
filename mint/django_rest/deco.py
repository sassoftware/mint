#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import re
from xml.dom import minidom

from django import http

from rbuilder.inventory import models 

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
            xml = args[1].raw_post_data
            doc = minidom.parseString(xml)
            root_node = doc.documentElement
            to_underscore(root_node)
            underscore_xml = doc.toxml(encoding='UTF-8')
            built_model = xobj.parse(xml, typeMap=models.type_map)
            kw[model_name] = built_model
            return function(*args, **kw)

        return inner
    return decorate

def return_xml(function):
    """
    Decorator that serializes a returned parser object into xml with a root
    node of modelName.
    """
    def inner(*args, **kw):
        response = http.HttpResponse()
        response['Content-Type'] = 'text/xml'
        ret_val = function(*args, **kw)
        request = args[1]
        xml = ret_val.to_xml(request)
        doc = minidom.parseString(xm)
        to_camel_case(doc.documentElement)
        request.write(doc.toxml(encoding='UTF-8'))
        return request

    return inner

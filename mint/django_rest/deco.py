#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import StringIO
import re
import sys
import datetime
from xml.dom import minidom

from django import http
from django_restapi import resource

def unConvert(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def unCamelCase(node):
    for child in node.childNodes:
        if hasattr(child, 'tagName'):
            child.tagName = unConvert(child.tagName)
            unCamelCase(child)

def convert(name):
    def repl(m):
        return m.group()[:-2] + m.group()[-1].upper()
    s1 = re.sub('(.)_([a-z])', repl, name)
    return s1

def camelCase(node):
    for child in node.childNodes:
        if hasattr(child, 'tagName'):
            child.tagName = convert(child.tagName)
            camelCase(child)

def parserToString(parser, modelName):
    sio = StringIO.StringIO()
    parser.export(sio, 0, namespace_='', name_=modelName)
    xmlResp = sio.getvalue()
    doc = minidom.parseString(xmlResp)
    rootNode = doc.documentElement
    camelCase(rootNode)
    return doc.toprettyxml(encoding='UTF-8')

def requires(modelName, parserClass):
    """
    Decorator that parses the post data on a request into the class
    specified by modelClass.
    """
    def decorate(function):

        def inner(*args, **kw):
            doc = minidom.parseString(args[1].raw_post_data)
            rootNode = doc.documentElement
            unCamelCase(rootNode)
            parser = parserClass.factory()
            parser.build(rootNode)
            kw[modelName] = parser
            return function(*args, **kw)

        return inner
    return decorate

def returns(modelName):
    """
    Decorator that serializes a returned parser object into xml with a root
    node of modelName.
    """
    def decorate(function):

        def inner(*args, **kw):
            response = http.HttpResponse()
            response['Content-Type'] = 'text/xml'
            retVal = function(*args, **kw)
            response.write(parserToString(retVal, modelName))
            return response

        return inner
    return decorate

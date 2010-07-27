#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import StringIO
from lxml import etree
import re
from xml.dom import minidom

from django import http

SCHEMA_FILE_1_0 = "/usr/share/rpath_models/system-1.0.xsd"
SCHEMA_FILE = SCHEMA_FILE_1_0
SCHEMA_URL_1_0 = "http://www.rpath.com/permanent/inventory/system-1.0.xsd"
SCHEMA_URL = SCHEMA_URL_1_0

def unConvert(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def unCamelCase(node):
    for child in node.childNodes:
        for name in ['tagName', 'nodeName']:
            if hasattr(child, name):
                setattr(child, name, unConvert(getattr(child, name)))
                unCamelCase(child)

def convert(name):
    def repl(m):
        return m.group()[:-2] + m.group()[-1].upper()
    s1 = re.sub('(.)_([a-z])', repl, name)
    return s1

def camelCase(node):
    for child in node.childNodes:
        for name in ['tagName', 'nodeName']:
            if hasattr(child, name):
                setattr(child, name, convert(getattr(child, name)))
                camelCase(child)

def parserToString(parser):
    sio = StringIO.StringIO()
    parser.export(sio, 0, namespace_='')
    xmlResp = sio.getvalue()
    doc = minidom.parseString(xmlResp)
    rootNode = doc.documentElement
    camelCase(rootNode)
    return doc.toxml(encoding='UTF-8')

def validateXml(xmlContents, schemaFilePath=SCHEMA_FILE):
    schema = etree.XMLSchema(file=schemaFilePath)
    # Verify a default namespace is set in the input, if not, add it.
    # Otherwise, lxml will fail to validate against the schema.
    if 'xmlns=' not in xmlContents[0:xmlContents.index('>')]:
        xmlContents = xmlContents[:xmlContents.index('>')] + \
                        ' xmlns="%s"' % SCHEMA_URL + \
                        xmlContents[xmlContents.index('>'):]
    sio = StringIO.StringIO(xmlContents)
    xmlTree = etree.parse(sio)
    schema.assertValid(xmlTree)

def requires(modelName, parserClass):
    """
    Decorator that parses the post data on a request into the class
    specified by modelClass.
    """
    def decorate(function):

        def inner(*args, **kw):
            postData = args[1].raw_post_data
            validateXml(postData)
            doc = minidom.parseString(postData)
            rootNode = doc.documentElement
            unCamelCase(rootNode)
            parser = parserClass.factory()
            parser.build(rootNode)
            kw[modelName] = parser
            return function(*args, **kw)

        return inner
    return decorate

def returns():
    """
    Decorator that serializes a returned parser object into xml with a root
    node of modelName.
    """
    def decorate(function):

        def inner(*args, **kw):
            response = http.HttpResponse()
            response['Content-Type'] = 'text/xml'
            retVal = function(*args, **kw)
            response.write(parserToString(retVal))
            return response

        return inner
    return decorate

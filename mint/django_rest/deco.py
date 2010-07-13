#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import sys
import datetime
from xml.dom import minidom

from django import http
from django_restapi import resource

def requires(modelName, parserClass):
    """
    Decorator that parses the post data on a request into the class
    specified by modelClass.
    """
    def decorate(function):

        def inner(*args, **kw):
            doc = minidom.parseString(args[1].raw_post_data)
            rootNode = doc.documentElement
            parser = parserClass.factory()
            parser.build(rootNode)
            kw[modelName] = parser
            return function(*args, **kw)

        return inner
    return decorate


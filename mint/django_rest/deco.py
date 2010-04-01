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

from rreg.registration import models

def requires(modelName, modelClass):
    """
    Decorator that parses the post data on a request into the class
    specified by modelClass.
    """
    def decorate(function):
        def inner(*args, **kw):
            doc = minidom.parseString(args[1].raw_post_data)
            rootNode = doc.documentElement
            rootObj = modelClass.parser.factory()
            rootObj.build(rootNode)

            elemDict = dict((x.name, getattr(rootObj, x.name))
                for x in rootObj.member_data_items_)
            kw[modelName] = modelClass(**elemDict)

            return function(*args, **kw)
        return inner
    return decorate


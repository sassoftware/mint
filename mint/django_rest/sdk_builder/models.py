#
# Copyright (c) 2011 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#
from lxml import etree
from xobj import xobj

class XMLModel(object):
    """docstring for Model"""
    def __init__(self, xml=None, root_name=None):
        if xml:
            self.xml = etree.XML(xml)
        elif root_name:
            self.xml = etree.Element(root_name)
        else:
            raise Exception('Either xml or root_name must be specified')
       
    def serialize(self):
        """docstring for serialize"""
        return etree.tostring(self.xml, xml_declaration=True, pretty_print=True)
        

class DjangoModelWrapper(object):
    """docstring for DjangoModelWrapper"""
    
    def __new__(cls, django_model):
        """docstring for __new__"""
        _dict = self.getModelFields(django_model)
        return type(django_model.__name__, (xobj.XObj), _dict)
    
    @staticmethod
    def getModelFields(django_model):
        """docstring for getModelFields"""
        _dict = {}
        for field in sorted(django_model._meta.fields, key=lambda x: x.name):
            _dict[field.name] = field
        return _dict
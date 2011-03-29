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

from xobj import xobj
import string

def toSource(wrapped_cls):
    """
    Creates python source code for xobj class stubs
    """
    STUB = "class ${name}(xobj.XObj):\n"
    BODY = "    ${field_name} = ${field_value}\n"
    
    src = string.Template(STUB).substitute({'name':wrapped_cls.__name__})
    
    for k in wrapped_cls.__dict__:
        try:
            name = wrapped_cls.__dict__[k].__name__
            field = getattr(Fields, name, None)
            if not field:
                continue
            src += \
                string.Template(BODY).substitute(
                {'field_name':k, 'field_value':name})
        except AttributeError:
            continue   
    return src
      
    
REGISTRY = {}
   
        
class Fields(object):
            
    class CharField(xobj.XObj):
        pass
    
    class DecimalField(xobj.XObj):
        pass
        
    class FloatField(xobj.XObj):
        pass
    
    class IntegerField(xobj.XObj):
        pass

    class TextField(xobj.XObj):
        pass

    class ForeignKey(xobj.XObj):
        pass
    
    class ManyToManyField(xobj.XObj):
        pass
    
    class OneToOneField(xobj.XObj):
        pass

    class AutoField(xobj.XObj):
        pass

    class NullBooleanField(xobj.XObj):
        pass

    class DateTimeUtcField(xobj.XObj):
        pass
        
    class SerializedForeignKey(xobj.XObj):
        pass    
        
    class HrefField(xobj.XObj):
        pass

    class DeferredForeignKey(xobj.XObj):
        pass

    class SmallIntegerField(xobj.XObj):
        pass

    class XMLField(xobj.XObj):
        pass

    class InlinedDeferredForeignKey(xobj.XObj):
        pass

    class InlinedForeignKey(xobj.XObj):
        pass

    class BooleanField(xobj.XObj):
        pass

    class URLField(xobj.XObj):
        pass

class DjangoModelWrapper(object):
    """docstring for DjangoModelWrapper"""

    def __new__(cls, django_model):
        """docstring for __new__"""
        cls.model = django_model
        fields_dict = cls.getModelFields(django_model)
        if not fields_dict:
            return None
        fields_dict = cls.convertFields(fields_dict)
        return type(django_model.__name__, (xobj.XObj,), fields_dict)
    
    @staticmethod
    def getModelFields(django_model):
        """docstring for getModelFields"""
        d = {}
        try:
            for field in django_model._meta.fields:
                d[field.name] = field
            return d
        except AttributeError:
            return {}
    
    @staticmethod
    def convertFields(d):
        """
        Converts django fields to sdk classes
        """
        _d = {}
        for k in d:
            new_field = getattr(Fields, d[k].__class__.__name__)
            _d[k] = new_field
        return _d
    
    @staticmethod
    def resolveField(self, field):
        """docstring for resolveFields"""
        
# if list_fields is set then generate type list        

        
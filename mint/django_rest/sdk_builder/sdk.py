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

from mint.django_rest.rbuilder.inventory import models


def parseName(name):
    """
    ie: Changes management_nodes to ManagementNodes
    """
    return ''.join([s.capitalize() for s in name.split('_')])

def toSource(wrapped_cls):
    """
    Creates python source code for xobj class stubs
    """
    STUB = "class ${cls_name}(xobj.XObj):\n"
    BODY = "    ${field_name} = ${field_value}\n"
    
    src = string.Template(STUB).substitute({'cls_name':wrapped_cls.__name__})
    
    # k is name of field, v is cls that represents its value
    for k, v in wrapped_cls.__dict__.iteritems():
        try:
            if isinstance(v, list):
                name = '[%s]' % v[0].__name__
            else:
                name = v.__name__
        # happens when v is None or doesn't have __name__        
        except AttributeError: 
            continue
        src += \
            string.Template(BODY).substitute(
            {'field_name':k.lower(), 'field_value':name})
    return src


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
    """
    Takes a django model and creates the code for its corresponding
    class stub.  For each model with a list_fields attribute,
    DjangoModelWrapper is called on the listed model, and the result placed
    inside a list for xobj to find it.
    """
    
    def __new__(cls, django_model):
        """
        Takes care of generating the code for the class stub
        """
        fields_dict = cls.getModelFields(django_model)
        # if getModelFields returns an empty dictionary
        # then return None to indicate that the model
        # doesn't have a _meta attribute (which can 
        # happen if the cls passed to getModelFields
        # is not an actual django_model)
        if not fields_dict:
            return None
        fields_dict = cls.convertFields(fields_dict)
        try:
            dep_names = [parseName(m) for m in django_model.list_fields]
            for name in dep_names:
                model = getattr(models, name)
                fields_dict[name] = [DjangoModelWrapper(model)]
        except AttributeError:
            pass
        return type(django_model.__name__, (xobj.XObj,), fields_dict)
    
    @staticmethod
    def getModelFields(django_model):
        """
        Gets all of a django model's pre-converted fields
        """
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
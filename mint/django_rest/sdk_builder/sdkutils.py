# pyflakes=ignore
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

import inspect
import string

def parseName(name):
    """
    ie: Changes management_nodes to ManagementNodes
    """
    return ''.join([s.capitalize() for s in name.split('_')])

def toSource(wrapped_cls):
    """
    Creates python source code for xobj class stubs
    """
    if not wrapped_cls:
        return ''
    
    STUB = 'class ${cls_name}(xobj.XObj, XObjMixin):\n    """XObj Class Stub"""\n'
    ATTRS = '    __metaclass__ = GetSetItemMeta\n'
    FIELDS = '    ${field_name} = ${field_value}\n'
    
    src = string.Template(STUB).substitute({'cls_name':wrapped_cls.__name__})
    src += ATTRS
    
    # k is name of field, v is cls that represents its type
    for k, v in wrapped_cls.__dict__.items():
        # take this out if in the future you want the body of a method
        # to be written into the src
        if inspect.ismethod(v):
            continue
        if isinstance(v, list):
            name = '[%s]' % v[0].__name__
        else:
            # FIXME: as sdk grows, more non-field_type attrs
            # (which also implies that they are missing __name__)
            # could be attached to the wrapped_cls. Need to 
            # account for this.
            if k in ['__module__', '__doc__', '__name__']:
                continue
            name = v.__name__
        src += \
            string.Template(FIELDS).substitute(
            {'field_name':k.lower(), 'field_value':name})
    return src
    
    
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
        fields_dict = cls._getModelFields(django_model)
        fields_dict = cls._convertFields(fields_dict)
        if hasattr(django_model, 'list_fields'):
            dep_names = [parseName(m) for m in django_model.list_fields]
            for name in dep_names:
                # FIXME: here we use ...rbuilder.inventory.models directly
                # as a debugging hack. Need to do some magic to get around
                # hard coding this so that tool works on other models
                model = getattr(models, name)
                # Recursive call to DjangoModelWrapper
                fields_dict[name] = [DjangoModelWrapper(model)]
        return type(django_model.__name__, (xobj.XObj,), fields_dict)

    @staticmethod
    def _getModelFields(django_model):
        """
        Gets all of a django model's pre-converted fields
        """
        d = {}
        if hasattr(django_model, '_meta'):
            for field in django_model._meta.fields:
                d[field.name] = field
        return d

    @staticmethod
    def _convertFields(d):
        """
        Converts django fields to sdk Field classes
        """
        _d = {}
        for k in d:
            new_field = getattr(Fields, d[k].__class__.__name__)
            _d[k] = new_field
        return _d
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
from xobj import xobj
from mint.django_rest.sdk_builder.rSDK import Fields, GetSetXMLAttrMeta, XObjMixin


def indent(txt, n=1):
    """
    n is the number of times txt should be indented
    """
    if txt is None:
        return ''
    splitted = ['    ' + line + '\n' for line in txt.split('\n')]
    joined = ''.join(splitted)
    if n > 1:
        joined = indent(joined, n - 1)
    return joined

def parseName(name):
    """
    ie: Changes management_nodes to ManagementNodes
    """
    return ''.join([s.capitalize() for s in name.split('_')])

def sortByListFields(*models):
    registry = []
    for cls in models:
        listed = getattr(cls, 'list_fields', None)
        if listed:
            for c in listed:
                if cls not in registry:
                    registry.append(cls)
                else:
                    registry.remove(cls)
                    registry.append(cls)
        elif cls in registry:
            continue
        else:
            registry.insert(0, cls)
    return registry

FCN = \
"""
def %(name)s(%(args)s):
%(docstring)s
%(body)s
""".strip()

CLASS = \
"""
class %(name)s(%(bases)s):
%(doc)s
%(attrs)s
""".strip()


class ClassStub(object):
    def __init__(self, cls, key_parser=None, value_parser=None):
        self.cls = cls
        self.kp = key_parser
        self.vp = value_parser

    def doc2src(self):
        indented = indent(getattr(self.cls, '__doc__', ''))
        return '    \"\"\"\n' + indented + '    \"\"\"'

    def bases2src(self):
        return ', '.join(b.__name__ for b in self.cls.__bases__)

    def attrs2src(self):
        
        def getName(x):
            if inspect.isclass(x):
                return x.__name__
            else:
                return x.__class__.__name__
                
        def resolveDict(d):
            _d = {}
            for _k, _v in d.items():
                if isinstance(_v, (str, unicode, int, float)):
                    _d[_k] = _v
                elif isinstance(_v, dict):
                    _d[_k] = resolveDict(_v)
                elif isinstance(_v, list):
                    _d[_k] = resolveList(_v)
                else:
                    _d[k] = getName(_v)
            return _d

        def resolveList(L):
            _l = []
            for _v in L:
                if isinstance(_v, (str, unicode, int, float)):
                    _l.append(_v)
                elif isinstance(_v, dict):
                    _l.append(resolveDict(_v))
                elif isinstance(_v, list):
                    _l.append(resolveList(_v))
                else:
                    _l.append(getName(_v))
            return _l
            
        src = []
        EXCLUDED = ['__module__', '__doc__', '__name__', '__weakref__', '__dict__']
        
        for k, v in self.cls.__dict__.items():
            # don't inline magic methods
            text = ''
            if k in EXCLUDED or inspect.isfunction(v):
                continue
            if self.kp:
                k = self.kp(k)
            if self.vp:
                v = self.vp(v)
            
            if isinstance(v, dict):
                v = resolveDict(v)
                text = '%s = %s' % (k, v) 
            elif isinstance(v, list):
                v = resolveList(v)
                if isinstance(v, list):
                    text = '%s = [%s]' % (k, v[0])
                else:
                    text = '%s = %s' % (k, v)
            else:
                v = getName(v)
                text = '%s = %s' % (k, v)
                
            src.append(indent(text))
        return ''.join(src)

    def tosrc(self):
        name = self.cls.__name__
        bases = self.bases2src()
        doc = self.doc2src()
        attrs = self.attrs2src()
        src = CLASS % dict(name=name, bases=bases, doc=doc, attrs=attrs)
        return src


class DjangoModelsWrapper(object):
    """
    docstring here
    """

    def __new__(cls, module):
        """
        docstring here
        """
        registry = []
        django_models = [m for m in module.__dict__.values() if inspect.isclass(m)]
        for django_model in sortByListFields(*django_models):
            fields_dict = cls._getModelFields(django_model)
            fields_dict = cls._convertFields(fields_dict)
            if hasattr(django_model, 'list_fields'):
                dep_names = [parseName(m) for m in django_model.list_fields]
                for name in dep_names:
                    model = getattr(module, name, None)
                    if not model:
                        raise Exception('Extra-Model reference required')
                    new_fields = cls._getModelFields(model)
                    new_fields = cls._convertFields(new_fields)
                    new = type(model.__name__, (xobj.XObj, XObjMixin), new_fields)
                    fields_dict[name] = [new]
            if hasattr(django_model, '_xobj'):
                fields_dict['_xobj'] = getattr(django_model, '_xobj')
            registry.append(type(django_model.__name__, (xobj.XObj, XObjMixin), fields_dict))
        return registry

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





    
    
# class DjangoModelWrapper(object):
#     """
#     Takes a django model and creates the code for its corresponding
#     class stub.  For each model with a list_fields attribute,
#     DjangoModelWrapper is called on the listed model, and the result placed
#     inside a list for xobj to find it.
#     """
# 
#     def __new__(cls, django_model, module):
#         """
#         Takes care of generating the code for the class stub
#         """
#         fields_dict = cls._getModelFields(django_model)
#         fields_dict = cls._convertFields(fields_dict)
#         if hasattr(django_model, 'list_fields'):
#             dep_names = [parseName(m) for m in django_model.list_fields]
#             for name in dep_names:
#                 model = getattr(module, name, None)
#                 if not model:
#                     raise Exception('Extra-Model reference required')
#                 # Recursive call to DjangoModelWrapper
#                 # TESTME: check that fields_dict[name] should always
#                 # be a list of a wrapped django_model, ie that a model
#                 # with a list_fields attr must be represented as a list
#                 # inside the class stub
#                 fields_dict[name] = [DjangoModelWrapper(model, module)]
#         if hasattr(model, '_xobj'):
#             fields_dict['_xobj'] = getattr(model, '_xobj')
#         return type(django_model.__name__, (xobj.XObj,), fields_dict)
#         
#     @staticmethod
#     def _getModelFields(django_model):
#         """
#         Gets all of a django model's pre-converted fields
#         """
#         d = {}
#         if hasattr(django_model, '_meta'):
#             for field in django_model._meta.fields:
#                 d[field.name] = field
#         return d
# 
#     @staticmethod
#     def _convertFields(d):
#         """
#         Converts django fields to sdk Field classes
#         """
#         _d = {}
#         for k in d:
#             new_field = getattr(Fields, d[k].__class__.__name__)
#             _d[k] = new_field
#         return _d
#         
# def generateTypemap():
#     pass
#     
# # FIXME: can't account for non-list intra and extra field references
# def toSource(wrapped_cls, app_label):
#     """
#     Creates python source code for xobj class stubs.  Remember
#     that each class is actually a nested class whose out class
#     is named after the django app that it belongs to.
#     """
#     if not wrapped_cls:
#         return ''
# 
#     STUB = 'class ${cls_name}(xobj.XObj, XObjMixin):\n    """XObj Class Stub"""\n'
#     ATTRS = '    __metaclass__ = GetSetXMLAttrMeta\n'
#     FIELDS = '    ${field_name} = ${field_value}\n'
#     METADATA = '_xobj = xobj.XObjMetadata(${metadata})'
#     src = string.Template(STUB).substitute({'cls_name':wrapped_cls.__name__})
#     src += ATTRS
# 
#     # k is name of field, v is cls that represents its type
#     for k, v in wrapped_cls.__dict__.items():
#         # take this out if in the future you want the body of a method
#         # to be written into the src
#         if inspect.ismethod(v):
#             continue
#         # FIXME: while this will most likely not cause problems
#         # for our use case, as almost every complex field is not
#         # a base field but rather a user-defined one that lives
#         # in the same models.py.  However, this will not do the case
#         # that a complex field is of base field type
#         if isinstance(v, list):
#             name = '[%s]' % v[0].__name__
#         else:
#             # FIXME: as sdk grows, more non-field_type attrs
#             # (which also implies that they are missing __name__)
#             # could be attached to the wrapped_cls. Need to 
#             # account for this.
#             if k in ['__module__', '__doc__', '__name__']:
#                 continue
#             name = 'Fields.' + v.__name__
#         src += \
#             string.Template(FIELDS).substitute(
#             {'field_name':k.lower(), 'field_value':name})
#     return src
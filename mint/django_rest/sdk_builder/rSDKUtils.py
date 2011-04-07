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

# NOT TO BE INCLUDED IN CLIENT SIDE DISTRIBUTION #

import inspect
from xobj import xobj
from mint.django_rest.sdk_builder.rSDK import Fields, GetSetXMLAttrMeta, XObjMixin  # pyflakes=ignore


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
    return ''.join(s.capitalize() for s in name.split('_'))

def unparseName(name):
    """
    ie: Changes ManagementNodes to management_nodes
    """
    new_name = []
    for idx, char in enumerate(name):
        if char.isupper():
            if idx == 0:
                new_name.append(char.lower())
            else:
                new_name.append('_' + char.lower())
        else:
            new_name.append(char)
    return ''.join(new_name)

# TESTME: Not 100% sure this works
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

def getName(x):
    if inspect.isclass(x):
        return x.__name__
    else:
        return x.__class__.__name__

def resolveDict(d):
    """
    Breaks down contents of dict into a form suitable for string
    interpolation into the class stub.  ie:
        >>> class Tag(object): pass
        >>> d = {'id':1, 'cls':{'inner':Tag}}
        >>> print d 
        {'id': 1, 'cls': {'inner': <class '__main__.Tag'>}}
        >>> print resolveDict(d)
        {'id': 1, 'cls': {'inner': 'Tag'}}
    """
    _d = {}
    for _k, _v in d.items():
        if isinstance(_v, (str, unicode, int, float)):
            _d[_k] = _v
        elif isinstance(_v, dict):
            _d[_k] = resolveDict(_v)
        elif isinstance(_v, list):
            _d[_k] = resolveList(_v)
        else:
            _d[_k] = getName(_v)
    return _d

def resolveList(L):
    """
    Breaks down contents of list into a form suitable for string
    interpolation into the class stub.  ie:
        >>> class Tag(object): pass
        >>> L = list(Tag, 'a', 1, [Tag()])
        >>> print L
        [<class '__main__.Tag'>, 'a', 1, [<__main__.Tag object at 0x100541190>]]
        >>> print resolveList(L)
        ['Tag', 'a', 1, ['Tag']]
    """
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
    def __init__(self, cls):
        self.cls = cls

    def doc2src(self):
        indented = indent(getattr(self.cls, '__doc__', ''))
        return '    \"\"\"\n' + indented + '    \"\"\"'

    def bases2src(self):
        return ', '.join(b.__name__ for b in self.cls.__bases__)

    def attrs2src(self):
        src = []
        EXCLUDED = ['__module__', '__doc__', '__name__', '__weakref__', '__dict__']
        
        # because _xobj.XObjMetadata references fields defined in the class
        # stub, if the metadata declaration comes before the referenced field then
        # an error will be thrown.  therefore sort in reverse order to force the
        # metadata to be included last
        #
        # FIXME: _xobj appears after fields (correctly) but before listed
        # fields (incorrectly).
        # FIXME: not including metaclass declaration
        for k, v in sorted(self.cls.__dict__.items(), reverse=True):
            text = ''
            # don't inline methods (or magic attrs)
            if k in EXCLUDED or inspect.isfunction(v):
                continue
                
            k = unparseName(k)
            
            # TODO: this is an UGLY way to solve the problem,
            # come back and clean up
            if isinstance(v, dict):
                v = resolveDict(v)
                text = '%s = %s' % (k, v)
            elif isinstance(v, list):
                v = resolveList(v)
                if isinstance(v, list):
                    text = '%s = [\'%s\']' % (k, v[0])
                else:
                    text = '%s = %s' % (k, v)
            else:
                v = getName(v)
                text = '%s = %s' % (k, v)

            # OLD
            # Process v to handle the creation of quotation marks
            # during string interpolation
            # if isinstance(v, dict):
            #      v = resolveDict(v)
            #      text = '%s = %s' % (k, v) 
            #  elif isinstance(v, list):
            #      v = resolveList(v)
            #      if isinstance(v, list):
            #          text = '%s = [%s]' % (k, v[0])
            #      else:
            #          text = '%s = %s' % (k, v)
            #  else:
            #      v = getName(v)
            #      text = '%s = %s' % (k, v)
                
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
        # all generated classes go into wrapped, don't mess around
        # with the ordering of stuff in wrapped (except for sorting
        # it before iteration) as the ordering is important
        collected = []
        django_models = [m for m in module.__dict__.values() if inspect.isclass(m)]
        # TESTME: sortByListFields is kind of a lucky hack, not sure if it
        # will always work -- come back and test
        for django_model in sortByListFields(*django_models):
            fields_dict = cls._getModelFields(django_model)
            fields_dict = cls._convertFields(fields_dict)
            # process listed fields
            if hasattr(django_model, 'list_fields'):
                dep_names = [parseName(m) for m in django_model.list_fields]
                for name in dep_names:
                    # FIXME: this is totally possible, *CONFIRMED PROBLEM*
                    # dunno if its possible for a model to reference another model
                    # outside of the Models.py it lives in.  if it can, then 
                    # throw an error as that contingency is not covered
                    model = getattr(module, name, None)
                    if not model:
                        raise Exception('Extra-model reference required, only intra-model references supported')
                    # Generate new fields
                    new_fields = cls._getModelFields(model)
                    new_fields = cls._convertFields(new_fields)
                    # new class is a standin for the one in listed fields. this
                    # is *not* the corresponding class that exists in collected,
                    # it will not recieve an _xobj attr.  this isn't crucial but
                    # can be fixed at a later time.
                    new = type(model.__name__, (xobj.XObj, XObjMixin), new_fields)
                    fields_dict[name] = [new]
            # make sure to extract _xobj metadata
            if hasattr(django_model, '_xobj'):
                fields_dict['_xobj'] = getattr(django_model, '_xobj')
            # don't forget that the order of classes in collected is important
            collected.append(type(django_model.__name__, (xobj.XObj, XObjMixin), fields_dict))
        return collected

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
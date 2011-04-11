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
from mint.django_rest.sdk_builder.rSDK import Fields, XObjMixin  # pyflakes=ignore


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

def toCamelCase(name):
    """
    used to be parseName
    ie: Changes management_nodes to ManagementNodes
    """
    return ''.join(s.capitalize() for s in name.split('_'))

def toUnderscore(name):
    """
    used to be unparseName
    ie: Changes ManagementNodes to management_nodes
    """
    L = []
    F = lambda i, c: L.append(c.lower()) if i == 0 else L.append('_' + c.lower())
    for i, c in enumerate(name):
        if c.isupper():
            F(i, c)
        else:
            L.append(c)
    return ''.join(L)

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
        # HACK: hardcode __metaclass__
        src = [indent('__metaclass__ = RegistryMeta\n')]
        EXCLUDED = ['__module__', '__doc__', '__name__', '__weakref__', '__dict__']
        
        # because _xobj.XObjMetadata references fields defined in the class
        # stub, if the metadata declaration comes before the referenced field then
        # an error will be thrown.  therefore sort in reverse order to force the
        # metadata to be included last
        #
        # FIXME: _xobj appears after fields (correctly) but before listed
        # fields (incorrectly).
        # FIXME: not automatically including metaclass declaration
        
        module = inspect.getmodule(self.cls)
        
        for k, v in sorted(self.cls.__dict__.items(), reverse=True):
            text = ''
            # don't inline methods (or magic attrs)
            if k in EXCLUDED or inspect.isfunction(v):
                continue
            k = toUnderscore(k)
            # parse attrs and generate src code
            if isinstance(v, list):
                text = '%s = [\'%s\']' % (k, v[0].__name__)
            elif isinstance(v, xobj.XObjMetadata):
                text = '_xobj = ' + str(XObjMetadataResolver(v))
            else:
                text = '%s = \'%s\'' % (k, getName(v))
            # compile src
            src.append(indent(text))
        return ''.join(src)

    def tosrc(self):
        name = self.cls.__name__
        bases = self.bases2src()
        doc = self.doc2src()
        attrs = self.attrs2src()
        src = CLASS % dict(name=name, bases=bases, doc=doc, attrs=attrs)
        return src


class XObjMetadataResolver(object):
    def __init__(self, _xobj):
        self._xobj = _xobj
        self.fromTemplate = lambda (name, val): '%s%s%s' % (
                    name if val else '', '=' if val else '', val if val else '')

    def resolveTag(self):
        return "\'%s\'" % self._xobj.tag.lower() if self._xobj.tag else ''

    def resolveElements(self):
        return self._xobj.elements

    def resolveAttributes(self):
        d_body = []
        for k, v in self._xobj.attributes.items():
            d_body.append("\'%s\':%s" % (k, v.__name__))
        return '{' + ','.join(d_body) + '}' if d_body else ''

    def resolveText(self):
        return "\'%s\'" % self._xobj.text.strip() if self._xobj.text else ''

    def resolveMetadata(self):
        return [('tag', self.resolveTag()), ('attributes', self.resolveAttributes()), 
                ('text', self.resolveText()), ('elements', self.resolveElements())]

    def __str__(self):
        metadata = self.resolveMetadata()
        src = [s for s in map(self.fromTemplate, metadata) if s]
        if src: return 'xobj.XObjMetadata(' + ','.join(src) + ')'
        return ''

def DjangoModelsWrapper(module):
    """
    docstring here
    """
    # all generated classes go into collected, don't mess around
    # with the ordering of stuff in collected (except for sorting
    # it before iteration) as the ordering is important
    collected = []
    django_models = [m for m in module.__dict__.values() if inspect.isclass(m)]
    # TESTME: sortByListFields is kind of a lucky hack, not sure if it
    # will always work -- come back and test
    for django_model in sortByListFields(*django_models):
        fields_dict = _getModelFields(django_model)
        fields_dict = _convertFields(fields_dict)
        # process listed fields
        if hasattr(django_model, 'list_fields'):
            dep_names = [toCamelCase(m) for m in django_model.list_fields]
            for name in dep_names:
                # FIXME: this is totally possible, *CONFIRMED PROBLEM*
                # dunno if its possible for a model to reference another model
                # outside of the Models.py it lives in.  if it can, then 
                # throw an error as that contingency is not covered
                model = getattr(module, name, None)
                if not model:
                    raise Exception('Extra-model reference required, only intra-model references supported')
                # Generate new fields
                new_fields = _getModelFields(model)
                new_fields = _convertFields(new_fields)
                # new class is a standin for the one in listed fields. this
                # is *not* the corresponding class that exists in collected,
                # it will not recieve an _xobj attr.  this isn't crucial but
                # can be fixed at a later time.
                # new = type(model.__name__, (xobj.XObj, XObjMixin), new_fields)
                new = type(model.__name__, (xobj.XObj,), new_fields)
                fields_dict[name] = [new]
        # make sure to extract _xobj metadata
        if hasattr(django_model, '_xobj'):
            fields_dict['_xobj'] = getattr(django_model, '_xobj')
        # don't forget that the order of classes in collected is important
        # collected.append(type(django_model.__name__, (xobj.XObj, XObjMixin), fields_dict))
        collected.append(type(django_model.__name__, (xobj.XObj,), fields_dict))
    return collected

def _getModelFields(django_model):
    """
    Gets all of a django model's pre-converted fields
    """
    d = {}
    if hasattr(django_model, '_meta'):
        for field in django_model._meta.fields:
            d[field.name] = field
    return d

def _convertFields(d):
    """
    Converts django fields to sdk Field classes
    """
    new_d = {}
    for k in d:
        new_field = getattr(Fields, d[k].__class__.__name__)
        classes = (Fields.ForeignKey, Fields.ManyToManyField, Fields.DeferredForeignKey)
        if issubclass(new_field, classes):
            new_field = _getReferenced(d[k])
        new_d[k] = type(new_field.__name__, (xobj.XObj,), {})
    return new_d

def _getReferenced(field):
    return field.related.parent_model
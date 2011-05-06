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
from xobj2 import xobj2
from mint.django_rest.sdk_builder2 import Fields  # pyflakes=ignore
from mint.django_rest.sdk_builder2.sdk import toUnderscore, toCamelCaps
from mint.django_rest.rbuilder.modellib.collections import Collection


def sortByListFields(*models):
    reg = []
    for cls in models:
        listed = getattr(cls, 'list_fields', None)
        if listed:
            if cls not in reg:
                registry.append(cls)
            else:
                reg.remove(cls)
                reg.append(cls)
        elif cls in reg:
            continue
        else:
            reg.insert(0, cls)
    return reg


class DjangoMetadata(object):
    def __init__(self, django_model):
        self.django_model = django_model
        self.list_fields = getattr(django_model, 'list_fields', [])
        self.module = inspect.getmodule(django_model)
        self.getModelFields()
        self.getReferenced()
        self.getXObj()
        self.xobjToXobj2()
    
    def getReferenced(self):
        for field in self.fields.values():
            try:
                self.referenced[field.name] = field.related.parent_model
            except:
                pass
                
    def getXObj(self):
        self._xobj = getattr(self.django_model, '_xobj', None)

    def xobjToXobj2(self):
        self._xobjMeta = xobj2.XObjMetadata()
        for k, v in self._xobj.attributes.items():
            self._xobjMeta.attributes[k] = v
        for k, v in self.fields.items():
            self._xobjMeta.elements.append(xobj2.Field(k, v))

    def getModelFields(self):
        """
        Gets all of a django model's pre-converted fields
        """
        excluded_fields = [field.name for field in Collection._meta.fields]
        d = {}
        if hasattr(self.django_model, '_meta'):
            for field in self.django_model._meta.fields:
                if issubclass(self.django_model, Collection) and field.name in excluded_fields:
                    continue
                d[field.name] = field
        self.fields = d

        
def DjangoModelsWrapper(module):
    collected = []
    django_models = [m for m in module.__dict__.values() if inspect.isclass(m)]
    for django_model in sortByListFields(*django_models):
        fields_dict = _convert(django_model)
        if hasattr(django_model, 'list_fields'):
            dep_names = [toCamelCaps(m) for m in django_model.list_fields]
            for name in dep_names:
                model = getattr(module, name, None)
                new_fields = _convert(model)
                new = type(model.__name__, (object,), new_fields)
                fields_dict[name] = [new]
        if hasattr(django_model, '_xobj'):
            fields_dict['_xobj'] = getattr(django_model, '_xobj')
        klass = type(django_model.__name__, (object,), fields_dict)
        collected.append((klass, DjangoMetadata(django_model)))
    return collected


XOBJMETADATA = \
"""
_xobjMeta = XObjMetadata(
    tag = %(tag)s,
    elements = [
%(elements)s
    ],
    attributes = dict(
%(attributes)s
    ),
)
""".strip()


class xobj2MetadataResolver(object):
    def __init__(self, _xobjMeta):
        self._xobjMeta = _xobjMeta

    def resolveElements(self):
        elements = self._xobjMeta.elements
        L = []
        for e in elements:
            string = 'xobj2.Field(%r, %s)' if not e.isList else 'xobj2.Field(%r, [%s])'
            L.append(string % (e.name, e.type.__name__ if not 
                    isinstance(e.type, list) else e.type[0].__name__))
        return indent(',\n'.join(L) if L else '', 2).rstrip()
    
    def resolveAttributes(self):
        d_body = []
        for k, v in self._xobjMeta.attributes.items():
            d_body.append("%s=%s" % (k, v.__name__))
        return indent(',\n'.join(d_body) if d_body else '', 2).rstrip()
    
    def resolveMetadata(self):
        d = {'tag':repr(self._xobjMeta.tag), 'attributes':self.resolveAttributes(),
             'elements':self.resolveElements()
            }
        return d
    
    def __str__(self):
        return indent(XOBJMETADATA % self.resolveMetadata())
        
        
CLASS = \
"""
@register
class %(name)s(%(bases)s):
%(doc)s
%(attrs)s
""".strip()


class ClassStub(object):
    def __init__(self, cls, django_metadata):
        self.cls = cls
        self.metadata = django_metadata

    def docTosrc(self):
        doc = getattr(self.cls, '__doc__', '')
        if doc:
            indented = indent('\"\"\"\n') + indent(doc) + indent('\"\"\"')
        else:
            indented = indent('\"\"\" \"\"\"')
        return indented.rstrip()

    def basesTosrc(self):
        return 'SDKModel'

    def attrsTosrc(self):
        _xobjMeta = self.metadata._xobjMeta
        return str(xobj2MetadataResolver(_xobjMeta))

    def tosrc(self):
        name = self.cls.__name__
        bases = self.basesTosrc()
        doc = self.docTosrc()
        attrs = self.attrsTosrc()
        src = CLASS % dict(name=name, bases=bases, doc=doc, attrs=attrs)
        return src

    def resolveName(self, field):
        # FIXME: needs to account for case
        # that another module specifices model
        # of same name as one in current module
        metadata = self.metadata
        name = field.__name__
        if name in metadata.module.__dict__ or name in Fields.__dict__:
            return name
        else:
            name = _resolveDynamicClassModule(field)
            return name
            

def _getModelFields(django_model):
    """
    Gets all of a django model's pre-converted fields
    """
    excluded_fields = [field.name for field in Collection._meta.fields]
    d = {}
    if hasattr(django_model, '_meta'):
        for field in django_model._meta.fields:
            if issubclass(django_model, Collection) and field.name in excluded_fields:
                continue
            d[field.name] = field
    return d


def _convertFields(d):
    """
    Converts django fields to sdk Field classes.
    If django field is fk or m2m it will also be
    converted.
    """
    new_d = {}
    classes = (Fields.ForeignKey, Fields.ManyToManyField,
               Fields.DeferredForeignKey, Fields.SerializedForeignKey)
    for k in d:
        new_field = getattr(Fields, d[k].__class__.__name__)
        if issubclass(new_field, classes):
            ref = _getReferenced(d[k])
            if hasattr(d[k], 'list_fields'):
                new_field = [ref]
            else:
                new_field = ref
        new_d[k] = new_field
    return new_d


def _convert(model):
    fields_dict = _getModelFields(model)
    return _convertFields(fields_dict)


def _getReferenced(field):
    """
    Returns the model referenced by some variant of a
    fk or m2m field
    """
    return field.related.parent_model


def _resolveDynamicClassModule(field):
    """
    takes PackageVersions and mint.django_rest.rbuilder.packages.models
    to
    packages.PackageVersions
    """
    prefix = 'mint.django_rest.rbuilder.'
    import_path = inspect.getmodule(field).__name__.replace(prefix, '')
    # if is case then inside rbuilder
    if import_path.startswith('models'):
        new_path = 'rbuilder' + '.' + field.__name__
    else:
        new_path = '.'.join(import_path.split('.')[0:-1] + [field.__name__])
    return new_path
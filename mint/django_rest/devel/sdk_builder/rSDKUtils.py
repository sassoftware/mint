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
from mint.django_rest.sdk_builder import Fields  # pyflakes=ignore
from mint.django_rest.rbuilder.modellib.collections import Collection

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

class DjangoMetadata(object):
    def __init__(self, django_model):
        self.django_model = django_model
        self.module = inspect.getmodule(django_model)
        self.fields = _getModelFields(django_model)
        self.referenced = {}
        for field in self.fields.values():
            try:
                self.referenced[field.name] = field.related.parent_model
            except:
                pass
        self.list_fields = getattr(django_model, 'list_fields', [])
        self._xobj = getattr(django_model, '_xobj', None)

def sortByListFields(*models):
    registry = []
    for cls in models:
        listed = getattr(cls, 'list_fields', [])
        if listed:
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
    
    def doc2src(self):
        doc = getattr(self.cls, '__doc__', '')
        if doc:
            indented = indent('\"\"\"\n') + indent(doc) + indent('\"\"\"')
        else:
            indented = indent('\"\"\" \"\"\"')
        return indented

    
    def bases2src(self):
        # return ', '.join(b.__name__ for b in self.cls.__bases__)
        return 'SDKModel'
    
    def attrs2src(self):
        # hardcode __metaclass__
        src = []
        EXCLUDED = ['__module__', '__doc__', '__name__', '__weakref__', '__dict__']
        for k, v in sorted(self.cls.__dict__.items(), reverse=True):
            text = ''
            # don't inline methods (or magic attrs)
            if k in EXCLUDED or inspect.isfunction(v):
                continue
            else:
                k = toUnderscore(k)
                # parse attrs and generate src code
                if isinstance(v, list):
                    text = '%s = [%r]' % (k, self.resolveName(v[0]))
                elif isinstance(v, xobj.XObjMetadata):
                    meta_src = str(XObjMetadataResolver(v))
                    if not meta_src: continue
                    text = '_xobj = ' + meta_src
                else:
                    text = '%s = %r' % (k, self.resolveName(v))
                src.append(indent(text))
                
        return ''.join(src)
    
    def tosrc(self):
        name = self.cls.__name__
        bases = self.bases2src()
        doc = self.doc2src()
        attrs = self.attrs2src()
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
            
class XObjMetadataResolver(object):
    """
    converts _xobj = xobj.XObjMetadata( ... ) into src code
    """
    
    def __init__(self, _xobj):
        self._xobj = _xobj
        self.fromTemplate = lambda (name, val): '%s%s%s' % (
                    name if val else '', '=' if val else '', val if val else '')
    
    def resolveTag(self):
        return "%r" % self._xobj.tag.lower() if self._xobj.tag else ''
    
    def resolveElements(self):
        return self._xobj.elements
    
    def resolveAttributes(self):
        d_body = []
        for k, v in self._xobj.attributes.items():
            d_body.append("\'%s\':%s" % (k, v.__name__))
        return '{' + ','.join(d_body) + '}' if d_body else ''
    
    def resolveText(self):
        return "\'%s\'" % self._xobj.text.strip() if self._xobj.text else ''
    
    # def resolveMetadata(self):
    #     return [('tag', self.resolveTag()), ('attributes', self.resolveAttributes()),
    #             ('text', self.resolveText()), ('elements', self.resolveElements())]
    
    def resolveMetadata(self):
        return [('tag', self.resolveTag()), ('text', self.resolveText()),
                ('elements', self.resolveElements())]
    
    def __str__(self):
        metadata = self.resolveMetadata()
        src = [s for s in map(self.fromTemplate, metadata) if s]
        if src: return 'XObjMetadata(' + ','.join(src) + ')'
        return ''

def DjangoModelsWrapper(module):
    collected = []
    django_models = [m for m in module.__dict__.values() if inspect.isclass(m)]
    for django_model in sortByListFields(*django_models):
        fields_dict = _convert(django_model)
        if hasattr(django_model, 'list_fields'):
            dep_names = [toCamelCase(m) for m in django_model.list_fields]
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
    import_path = inspect.getmodule(field) .__name__.replace(prefix, '')
    # if is case then inside rbuilder
    if import_path.startswith('models'):
        new_path = 'rbuilder' + '.' + field.__name__
    else:
        new_path = '.'.join(import_path.split('.')[0:-1] + [field.__name__])
    return new_path
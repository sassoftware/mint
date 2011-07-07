
import inspect
import os
from django.db import models as djmodels
from django.core.management.base import BaseCommand
from mint.django_rest.urls import urlpatterns
from mint.django_rest import deco
import string

import settings

BASE_PATH = "rbuilder/inventory/docs"

METHODS = ['GET', 'POST', 'PUT', 'DELETE']

METHODS_TMPLT = string.Template(
"""
Methods:
    GET:
        ${GET}
    POST:
        ${POST}
    PUT:
        ${PUT}
    DELETE:
        ${DELETE}
"""
)

def parseName(name):
    """
    changes management_nodes to ManagementNodes
    """
    return ''.join([s.capitalize() for s in name.split('_')])

def readModels():
    allModels = {}
    for app in settings.INSTALLED_APPS:
        if not app.startswith('mint.'):
            continue
        m = __import__(app + '.models', {}, {}, ['models'])
        for objname in dir(m):
            obj = getattr(m, objname)
            if not inspect.isclass(obj) or not issubclass(obj, djmodels.Model):
                continue
            allModels[objname] = obj
    return allModels

class Command(BaseCommand):
    help = "Generate comments for the REST documentation"

    @property
    def models(self):
        if not hasattr(self, '_models'):
            self._models = readModels()
        return self._models

    def handle(self, *args, **options):
        for u in urlpatterns:
            # processView throws AttributeError if a view is missing
            # any of its rest_%s methods.  If it is missing its 
            # methods then u.name is most likely missing too.
            try:
                view_doc = self.processView(u.callback)
            except AttributeError:
                continue
            model = self.models.get(u.name)
            if model:
                model_doc = self.processModel(model)
            else:
                model_doc = ''
            filepath = os.path.join(BASE_PATH, u.callback.__class__.__name__)
            f = open(filepath + '.txt', 'w')
            try:
                docs = '\n'.join([model_doc, view_doc])
                f.write(docs)
            finally:
                f.close()

    def processModel(self, model):
        fdesc = ["%s properties:" % model.__name__]
        # NOTE: Below is the old way of iterating over the fields
        for field in sorted(model._meta.fields, key=lambda x: x.name):
                docstring = getattr(field, 'docstring', None)
                if docstring is None:
                    continue
                fdesc.append("    %s - %s" % (field.name, docstring))
        if len(fdesc) == 1:
            fdesc.append("    N/A")
        
        # Recursively retrieve documentation for all
        # models listed in listed_fields        
        listed = getattr(model, 'list_fields', None)
        if listed:
            for model_name in listed:
                parsed_name = parseName(model_name)
                sub_model = self.models.get(parsed_name)
                if sub_model is None:
                    print "Model missing: %s" % parsed_name
                    continue
                fdesc.append('\n')
                fdesc.append(self.processModel(sub_model))
        return '\n'.join(fdesc)

    def processView(self, view):
        docs_dict = {'GET':'', 'POST':'', 'PUT':'', 'DELETE':''}
        for m in METHODS:
            # Throws AttributeError if view is missing a
            # rest_%s method
            method = getattr(view, 'rest_%s' % m)
            if getattr(method, 'undefined', False):
                docs_dict[m] = 'not supported'
                continue
            access = getattr(method, 'ACCESS', deco.ACCESS.AUTHENTICATED)
            if access & deco.ACCESS.ANONYMOUS:
                auth = 'none'
            elif access & deco.ACCESS.AUTHENTICATED:
                auth = 'user'
            elif access & deco.ACCESS.ADMIN:
                auth = 'admin'
            docs_dict[m] = 'Authentication: ' + auth + docs_dict[m]
        return METHODS_TMPLT.substitute(docs_dict)


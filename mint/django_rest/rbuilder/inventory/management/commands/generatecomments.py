
import os
from django.core.management.base import BaseCommand
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.urls import urlpatterns
from mint.django_rest import deco
import string

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
    return ''.join([s.capitalize() for s in name.split('_')])

class Command(BaseCommand):
    help = "Generate comments for the REST documentation"

    def handle(self, *args, **options):
        for u in urlpatterns:
            # processView throws AttributeError if a view is missing
            # any of its rest_%s methods.  If it is missing its 
            # methods then u.name is most likely missing too.
            try:
                view_doc = self.processView(u.callback)
            except AttributeError:
                continue
            if u.name in models.__dict__:
                model_doc = self.processModel(models.__dict__[u.name])
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
                sub_model = models.__dict__[parsed_name]
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


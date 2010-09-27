
import os
import inspect
from django.core.management.base import BaseCommand

from mint.django_rest.rbuilder.inventory import models, views
from mint.django_rest import deco

class Command(BaseCommand):
    help = "Generate comments for the REST documentation"

    _methods = ['GET', 'POST', 'PUT', 'DELETE']

    def handle(self, *args, **options):
        self.processViews()
        self.processModel(models.System)

    def processViews(self):
        for view in self.listViews():
            self.processView(view)

    def processView(self, view):
        out = []
        out.append("Methods:")
        print "View: %s" % view
        subtempl = "    %s"
        for m in self._methods:
            method = getattr(view, 'rest_%s' % m)
            out.append("  %s:" % m)
            if getattr(method, 'undefined', False):
                out.append(subtempl % "not supported")
                out.append("")
                continue
            access = getattr(method, 'ACCESS', deco.ACCESS.AUTHENTICATED)
            if access & deco.ACCESS.ANONYMOUS:
                auth = "none"
            elif access & deco.ACCESS.AUTHENTICATED:
                auth = "user"
            elif access & deco.ACCESS.ADMIN:
                auth = "admin"
            out.append(subtempl % ("Authentication: %s" % auth))
            out.append("")
        print '\n'.join(out)


    def listViews(self):
        baseClass = views.AbstractInventoryService
        for k, v in views.__dict__.items():
            if v is baseClass or not inspect.isclass(v):
                continue
            if not issubclass(v, baseClass):
                continue
            yield v

    def processModel(self, model):
        XSL = getattr(model, "XSL", None)
        if XSL is None:
            return
        fname = os.path.join("rbuilder/inventory/models_xsl", XSL)
        templ = fname + '.tmpl'
        fdesc = []
        for field in sorted(model._meta.fields, key=lambda x: x.name):
            docstring = getattr(field, 'docstring', None)
            if docstring is None:
                continue
            fdesc.append("   %s - %s" % (field.name, docstring))
        fdesc = '\n'.join(fdesc)
        contents = file(templ).read().replace("@@FIELDS@@", fdesc)
        file(fname, "w").write(contents)

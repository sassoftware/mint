#
# Copyright (c) 2011 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#rSDKUtils
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

from django.core.management.base import BaseCommand
from mint.django_rest.sdk_builder import rSDKUtils
from django.db.models.loading import cache
import os
import inspect  # pyflakes=ignore

EXCLUDED_APPS = [
    'auth',
    'contenttypes',
    'redirects',
    'sessions',
    'sites',
    'debug_toolbar',
    'sdk_builder',
    ]

def wrapped2src(wrapped, app_label):
    src = 'class %(label)s(object):\n    """%(label)s"""\n\n' % {'label':app_label}
    for w in wrapped:
        lines = []
        for line in rSDKUtils.toSource(w).split('\n'):
            line = ' ' * 4 + line + '\n'
            lines.append(line)
        src += ''.join(lines)
    return src


class Command(BaseCommand):
    help = "Generates python sdk"

    def handle(self, *args, **options):
        """
        Generates Python SDK for REST API
        """
        # Get paths where module will be written on the filesystem
        current_location = os.path.dirname(__file__)
        index = current_location.find('sdk_builder')
        models_path = os.path.join(
                        current_location[0:index], 'sdk_builder/sdk/Models.py')
        # build class stubs then write them to the filesystem
        with open(models_path, 'w') as f:
            f.write('from sdk import Fields\n')
            f.write('from sdk import XObjMixin\n')
            f.write('from sdk import GetSetXMLAttrMeta\n')
            f.write('from xobj import xobj\n')
            f.write('\n\n')
            
            # FIXME: below should work except for the problem with
            # retrieving the list_fields attribute off the model
            for app_label, models in self.findAllModels().items():
                if app_label in EXCLUDED_APPS:
                    continue
                src = self.buildSDKModels(app_label, models)
                if src:
                    f.writelines(src.strip())
                    f.write('\n\n')

    def buildSDKModels(self, app_label, module):
        wrapped = [rSDKUtils.DjangoModelWrapper(m, module) \
            for m in module.__dict__.values() if inspect.isclass(m)]
        return wrapped2src(wrapped, app_label)
    
    def findAllModels(self):
        d = {}
        for app in cache.get_apps():
            app_label = app.__name__.split('.')[-2]
            # Doesn't work, leaves out some models
            # d[app_label] = cache.get_models(app)
            # Workaround:
            # d[app_label] = [m for m in app.__dict__.values() if inspect.isclass(m)]
            d[app_label] = app
        return d
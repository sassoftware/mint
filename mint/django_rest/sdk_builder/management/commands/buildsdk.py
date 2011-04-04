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

# for debugging purposes, only use mint.django_rest.rbuilder.inventory.models
# at first
# from mint.django_rest.rbuilder.inventory import models
from django.core.management.base import BaseCommand
from mint.django_rest.sdk_builder import rSDKUtils
import os
from django.db.models.loading import cache
import string


class Command(BaseCommand):
    help = "Generates python sdk"

    def handle(self, *args, **options):
        """
        Generates Python SDK for REST API
        """        
        # Get paths where modules will be written on the filesystem
        current_location = os.path.dirname(__file__)
        index = current_location.find('sdk_builder')
        models_path = os.path.join(
                        current_location[0:index], 'sdk_builder/sdk/Models.py')
        # First build class stubs then write them to the filesystem
        with open(models_path, 'w') as f:
            f.write('from sdk import Fields\n')
            f.write('from sdk import XObjMixin\n')
            f.write('from sdk import GetSetXMLAttrMeta\n')
            f.write('from xobj import xobj\n')
            f.write('\n\n')
            for app_label, models in self.findModels().items():
                src = self.buildSDKModels(app_label, models)
                if src:
                    f.writelines(src)
                    f.write('\n\n')
    
    def buildSDKModels(self, app_label, models):
        wrapped = [rSDKUtils.DjangoModelWrapper(m) for m in models]
        cls_header = 'class %{app_label}(object):\n    """%{app_label}"""\n'
        src = string.Template(cls_header).substitute({'app_label':app_label})
        for w in wrapped:
            lines = []
            for line in rSDKUtils.toSource(w).split('\n'):
                line = ' ' * 4 + line + '\n'
                lines.append(line)
            src += ''.join(lines)
        return src
        
    def findModels(self):
        d = {}
        for app in cache.get_apps():
            app_label = app.__name__.split('.')[-2]
            d[app_label] = cache.get_models(app)
        return d
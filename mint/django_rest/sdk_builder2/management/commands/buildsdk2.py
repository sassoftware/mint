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

# NOT TO BE INCLUDED IN CLIENT SIDE DISTRIBUTION #

from django.core.management.base import BaseCommand
from mint.django_rest.sdk_builder2 import rSDKUtils
from django.db.models.loading import cache
import os
import shutil

EXCLUDED_APPS = [
    'auth',
    'contenttypes',
    'redirects',
    'sessions',
    'sites',
    'debug_toolbar',
    'sdk_builder',
    'sdk_builder2',
    ]

MODULE_LEVEL_CODE = \
"""
# DO NOT TOUCH #
GLOBALS = globals()
DynamicImportResolver(GLOBALS).rebind()
""".strip()


class Command(BaseCommand):
    help = "Generates python sdk for xobj2"

    def handle(self, *args, **options):
        """
        Generates Python SDK for REST API
        """
        # Get paths where modules will be written on the filesystem
        current_location = os.path.dirname(__file__)
        index = current_location.find('sdk_builder2')
        # Generate src code for each Models.py and write it to
        # its own module
        for app_label, module in self.findAllModels().items():
            # Place everything inside sdk package, which lives in sdk_builder
            models_path = os.path.join(
                    current_location[0:index], 'sdk_builder2/rsdk/%s.py' % app_label)
            # Keep out extraneous crap
            if app_label in EXCLUDED_APPS:
                continue
            # Actually write the module
            with open(models_path, 'w') as f:
                f.write('from rsdk.Fields import *  # pyflakes=ignore\n')
                f.write('from rsdk.sdk import SDKModel, register, DynamicImportResolver  # pyflakes=ignore\n')
                f.write('from xobj2.xobj2 import XObj, XObjMetadata  # pyflakes=ignore\n')
                # f.write('from sdk.xobj_debug import XObj, XObjMetadata  # pyflakes=ignore\n')
                f.write('\n')
                f.write('REGISTRY = {}\n')
                src = self.buildSDKModels(module)
                if src:
                    f.writelines(src.strip())
                    f.write('\n\n')
                    f.writelines(MODULE_LEVEL_CODE)
                    f.write('\n\n')
                    
        # now copy over rSDK into sdk package
        rSDK_orig_path = os.path.join(
                current_location[0:index], 'sdk_builder2/sdk.py')
        rSDK_new_path = os.path.join(
                current_location[0:index], 'sdk_builder2/rsdk/sdk.py')
        shutil.copyfile(rSDK_orig_path, rSDK_new_path)
        
        # now copy over Fields into sdk package
        Fields_orig_path = os.path.join(
                current_location[0:index], 'sdk_builder2/Fields.py')
        Fields_new_path = os.path.join(
                current_location[0:index], 'sdk_builder2/rsdk/Fields.py')
        shutil.copyfile(Fields_orig_path, Fields_new_path)
            
    def buildSDKModels(self, module):
        wrapped = rSDKUtils.DjangoModelsWrapper(module)
        L = []
        for w in wrapped:
            L.append(rSDKUtils.ClassStub(*w).tosrc())
        return '\n'.join(L)

    def findAllModels(self):
        d = {}
        for app in cache.get_apps():
            app_label = app.__name__.split('.')[-2]
            d[app_label] = app
        return d
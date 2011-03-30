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

# for debugging purposes, only use mint.django_rest.rbuilder.inventory.models
# at first
from mint.django_rest.rbuilder.inventory import models

from django.core.management.base import BaseCommand
from mint.django_rest.sdk_builder import sdk

import inspect
from xobj import xobj
import os

###### Sample Crap For Testing Purposes ######
PKGS_XML = \
"""
<packages>
    <package id="http://localhost/api/packages/1">
        <name>Apache</name>
        <description>Server</description>
    </package>
    <package id="http://localhost/api/packages/2">
        <name>Nano</name>
        <description>Text Editor</description>
    </package>
</packages>
""".strip()

class Package(xobj.XObj):
    id = sdk.Fields.URLField
    name = sdk.Fields.CharField
    description = sdk.Fields.TextField

class Packages(xobj.XObj):
    package = [Package]

##############################################

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
                    current_location[0:index], 'sdk_builder/api/models.py')
        fields_path = os.path.join(
                        current_location[0:index], 'sdk_builder/api/fields.py')
                        
        # First build class stubs then write them to the filesystem
        self.models = self.findModels()
        wrapped = [sdk.DjangoModelWrapper(m) for m in self.models]
        self.buildSDKModels(models_path, wrapped)
        
        # Now generate a flattened copy of sdk.Fields and
        # save it inside the package api
        self.buildSDKFields(fields_path)
        
        ##### For testing purposes only #####
        # doc = xobj.parse(PKGS_XML, typeMap={'packages':Packages})
        # import pdb; pdb.set_trace()
        # pass
        #####################################
        
    def buildSDKModels(self, models_path, wrapped):
        with open(models_path, 'w') as f:
            # write import Fields
            f.write('from fields import *\n')
            f.write('from xobj import xobj\n')
            f.write('\n\n')
            for w in wrapped:
                src = sdk.toSource(w)
                if src:
                    f.writelines(src)
                    f.write('\n')
    
    def buildSDKFields(self, fields_path):
        with open(fields_path, 'w') as f:
            f.write('from xobj import xobj\n')
            f.write('\n\n')
            d = sdk.Fields.__dict__
            field_classes = [d[x] for x in d if inspect.isclass(d[x])]
            for cls in field_classes:
                src = sdk.toSource(cls)
                if src:
                    f.writelines(src)
                    f.write('\n')
        
    def findModels(self):
        return [m for m in models.__dict__.values() if inspect.isclass(m)]
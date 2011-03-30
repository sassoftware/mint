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
        self.models = self.findModels()
        wrapped = [sdk.DjangoModelWrapper(m) for m in self.models]
        current_location = os.path.dirname(__file__)
        index = current_location.find('sdk_builder')
        filepath = os.path.join(
                    current_location[0:index], 'sdk_builder/api/models.py')
        with open(filepath, 'w') as f:
            for w in wrapped:
                src = sdk.toSource(w)
                if src:
                    f.writelines(src)
                    f.write('\n')
        
        ##### For testing purposes only #####
        doc = xobj.parse(PKGS_XML, typeMap={'packages':Packages})
        # import pdb; pdb.set_trace()
        pass
        #####################################
        
    def buildSDK(self):
        pass
        
    def findModels(self):
        return [m for m in models.__dict__.values() if inspect.isclass(m)]
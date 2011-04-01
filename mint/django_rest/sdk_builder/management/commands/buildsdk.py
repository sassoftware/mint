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
    <data pid="1">my data</data>
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

# Only do assertion after initialization is complete
# during initialization, setattr always passed a string.
# The idea behind validation in setattr is that once
# the class is initialized, a class attribute may only
# be assigned to if the assigned value is an instance
# or an instance of a subclass of the original type.
class Data(xobj.XObj):
    """
    Ok. So when 'pid' is left out then everything except
    checking works (using uncommented checking).  However,
    when 'pid' is there, checking works (both ways) but
    doc.toxml lists data text as empty
    """
    pid = sdk.Fields.IntegerField

    def __setattr__(self, k, v):
        # Works
        try:
            assert(issubclass(v.__class__, Data.__dict__[k]))
        except KeyError:
            pass
        self.__dict__[k] = v

        # Works, is hack
        # if hasattr(self, '_isInitialized'):
        #     try:
        #         assert(issubclass(v.__class__, Data.__dict__[k]))
        #     except KeyError:
        #         pass
        # else:
        #     self.__dict__['_isInitialized'] = True
        # self.__dict__[k] = v

class Package(xobj.XObj):
    id = sdk.Fields.URLField
    name = sdk.Fields.CharField
    description = sdk.Fields.TextField

    def __setattr__(self, k, v):
        # Doesn't work
        # try:
        #     assert(issubclass(v.__class__, Data.__dict__[k]))
        # except KeyError:
        #     pass
        # self.__dict__[k] = v
        
        # Works, is hack
        if hasattr(self, '_isInitialized'):
            try:
                assert(issubclass(v.__class__, Data.__dict__[k]))
            except KeyError:
                pass
        else:
            self.__dict__['_isInitialized'] = True
        self.__dict__[k] = v

class Packages(xobj.XObj):
    package = [Package]
    data = Data
    
    # Doesn't work (I think)
    def __setattr__(self, k, v):
        try:
            assert(issubclass(v.__class__, Data.__dict__[k]))
        except KeyError:
            pass
        self.__dict__[k] = v
##############################################

class Command(BaseCommand):
    help = "Generates python sdk"

    def handle(self, *args, **options):
        """
        Generates Python SDK for REST API
        """
        
        ##### For testing purposes only #####
        doc = xobj.parse(PKGS_XML, typeMap={'packages':Packages, 'data':Data})  # pyflakes=ignore
        # assignment works but shouldn't work (should throw assertion error)
        doc.packages.package[0].name = 1
        # assignment fails but *should* fail (throws assertion error)
        doc.packages.data.pid = 1
        # assignment works and *should* work
        doc.packages.data.pid = sdk.Fields.IntegerField(1)
        # assignment works but shouldn't work (should throu assertion error)
        doc.packages.package[0].id = 2
        # notice that doc.toxml() leaves doc.packages.data empty
        # this is still most likely because Data is being registered
        # as a complexType.  Also is weird because if I leave the Data
        # class stub as empty, the data+id are correctly displayed.
        # This doesn't make sense because I don't have this problem
        # with Package.
        print doc.toxml()
        # notice that this should also fail, I should *not* be able to
        # assign an integer where instance of Data is needed.
        doc.packages.data = 3
        # however, the following works (and should work)
        doc.packages.data = Data('Hello World')
        # doc.toxml() correctly includes and renders doc.packages.data
        # however it is missing the id:
        print doc.toxml()
        # we can assign an id -- below does *not* work and shouldn't work
        doc.packages.data.id = 'X'
        # we can assign an id -- below *does* work and should work
        doc.packages.data.id = sdk.Fields.IntegerField(1)
        # doc.toxml() now renders what we expect to see
        print doc.toxml()
        ############## END ##################
        
        # # Get paths where modules will be written on the filesystem
        # current_location = os.path.dirname(__file__)
        # index = current_location.find('sdk_builder')
        # models_path = os.path.join(
        #                 current_location[0:index], 'sdk_builder/api/models.py')
        # fields_path = os.path.join(
        #                 current_location[0:index], 'sdk_builder/api/fields.py')
        #                 
        # # First build class stubs then write them to the filesystem
        # self.models = self.findModels()
        # wrapped = [sdk.DjangoModelWrapper(m) for m in self.models]
        # self.buildSDKModels(models_path, wrapped)
        # 
        # # Now generate a flattened copy of sdk.Fields and
        # # save it inside the package api
        # self.buildSDKFields(fields_path)
    
    # TODO: import * is messy, find another way to flatten out
    # Fields to avoid this
    def buildSDKModels(self, models_path, wrapped):
        with open(models_path, 'w') as f:
            # write import Fields
            f.write('from fields import *  # pyflakes=ignore\n')
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
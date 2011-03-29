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

class Command(BaseCommand):
    help = "Generates python sdk"

    def handle(self, *args, **options):
        self.models = self.findModels()
        wrapped = [sdk.DjangoModelWrapper(m) for m in self.models]
        
    def buildSDK(self):
        """docstring for buildSDK"""
        pass
        
    def findModels(self):
        """docstring for findModels"""
        return [m for m in models.__dict__.values() if inspect.isclass(m)]
        
    def buildModels(self):
        """docstring for buildModels"""
        pass
    
    def buildModel(self, model):
        """docstring for buildModel"""
        pass
        
    def analyzeModels(self):
        """docstring for analyzePackages"""
        pass

    def analyzeModel(self, model):
        """docstring for analyzePackage"""
        pass
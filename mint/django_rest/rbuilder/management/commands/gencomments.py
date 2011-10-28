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

import inspect
import os
from django.db import models as djmodels
from django.core.management.base import BaseCommand
from mint.django_rest.urls import urlpatterns
from mint.django_rest import settings_common as settings

AUTH_TEMPLATE = "%(ROLE)s: %(PERMS)s"
ATTRIBUTE_TEMPLATE = "%(ATTRNAME)s : %(DOCSTRING)s"
DOCUMENT_TEMPLATE = \
"""
Resource Name: %(NAME)s

REST Methods:

GET: %(GET_SUPPORTED)s
    Auth -- %(GET_AUTH)s
        
POST: %(POST_SUPPORTED)s  
    Auth -- %(POST_AUTH)s
        
PUT: %(PUT_SUPPORTED)s
    Auth -- %(PUT_AUTH)s
        
DELETE: %(DELETE_SUPPORTED)s
    Auth -- %(DELETE_AUTH)s
        
        
Attributes:
%(ATTRIBUTES)s


Notes:
%(NOTES)s
""".strip()

LEFT_ARROW = '--->'
VERTICAL = '|'

class DocTreeFactory(object):
    """
    Used to create pretty trees ie:
    
    Root
      |---> Subheading 1
      |---> Subheading 2
    
    """
    def __init__(self, data):
        self.lines = data
        
    @staticmethod
    def generateLeftArrow(line, spacer):
        return ' ' * spacer + VERTICAL + LEFT_ARROW + ' %s' % line
        
    def makeTree(self, spacer=6):
        collected = []
        for line in self.lines:
            arrow = self.generateLeftArrow(line, spacer)
            collected.append(arrow)
        return '\n'.join(collected)

class Command(BaseCommand):
    help = "Generate comments for the REST documentation"

    def handle(self, *args, **options):
        # Grab all models for all mint apps registered
        # inside of settings.py
        self.aggregateModels = self.findModels()
        
        for u in urlpatterns:
            view = u.callback
            # Name of model, taken from URL inside urlpatterns
            MODEL_NAME = getattr(u, 'model', None)
            # Skip all views that don't specify a model name
            if not MODEL_NAME:
                continue
            # dict indexed by REST methods for the model
            METHODS = self.getMethodsFromView(view)
            # text formed by concatenating attr name with value of the docstring
            ATTRIBUTES = self.getAttributesDocumentation(MODEL_NAME)
            # dict keyed by REST method type with value one of:
            # anonymous, authenticated, admin, or rbac
            AUTH = self.getAuthDocumentation(MODEL_NAME, view)
            # any raw text from a model's _NOTE class attribute
            NOTES = self.getNotes(MODEL_NAME)
            
            TEXT = {'NAME':MODEL_NAME,
                    'GET_SUPPORTED':METHODS['GET'],
                    'GET_AUTH':AUTH['GET'],
                    'POST_SUPPORTED':METHODS['POST'],
                    'POST_AUTH':AUTH['POST'],
                    'PUT_SUPPORTED':METHODS['PUT'],
                    'PUT_AUTH':AUTH['PUT'],
                    'DELETE_SUPPORTED':METHODS['DELETE'],
                    'DELETE_AUTH':AUTH['DELETE'],
                    'ATTRIBUTES':ATTRIBUTES,
                    'NOTES':NOTES,
                    }
            
            # absolute path to the containing pkg and
            # "app name" are the interpolated values
            BASE_PATH = "%s/rbuilder/docs/%s/" % (
                os.getcwd(), self.getPkgNameFromView(view))
            # create destination directory if needed, raises
            # exception if directory already exists, in which case
            # just continue onward
            try:
                os.makedirs(BASE_PATH)
            except OSError, e:
                pass
            
            filepath = os.path.join(
                BASE_PATH, view.__class__.__name__)

            f = open(filepath + '.txt', 'w')
            try:
                f.write(DOCUMENT_TEMPLATE % TEXT)
            finally:
                f.close()

    def getPkgNameFromView(self, view):
        cls = view.__class__
        # ie: path = ../../../include/mint/django_rest/rbuilder/users/views.pyc
        path = inspect.getfile(cls)
        # splitted path = [../../../include/mint/django_rest, users/views.pyc]
        path = path.split('/rbuilder/')[-1].split('/')[0]
        # now pull out name of the containing package for the view
        return path.split('/')[0]

    def getApps(self):
        """
        django's get_app and get_model are causing problems,
        this hack will do for now
        """
        apps = {}
        for fullName in settings.INSTALLED_APPS:
            if not fullName.startswith('mint.'): continue
            appName = fullName.split('.')[-1]
            apps[appName] = __import__(
                fullName + '.models', {}, {}, ['models'])
        return apps

    def findModels(self):
        allModels = {}
        for app in self.getApps().values():
            for objname in dir(app):
                obj = getattr(app, objname)
                if not inspect.isclass(obj) or not issubclass(obj, djmodels.Model):
                    continue
                allModels[objname] = obj
        return allModels

    def getAttributesDocumentation(self, modelName):
        text = []
        
        # start by getting model and processing its fields
        model = self.aggregateModels.get(modelName, None)
        if model is None:
            return ''
        for field in sorted(model._meta.fields, key=lambda x: x.name):
            name = field.name
            docstring = getattr(field, 'docstring', 'N/A')
            line = ATTRIBUTE_TEMPLATE % {'ATTRNAME':name, 'DOCSTRING':docstring}
            text.append(line)
        
        # look for items in the model's list_fields attribute, if any are
        # found then include them in the text.   
        listed = getattr(model, 'list_fields', None)
        if listed:
            for listedModelName in listed:
                parsed_name = self.parseName(listedModelName)
                subModel = self.aggregateModels.get(parsed_name, None)
                if subModel is None:
                    print Warning('Model %s has model %s as a listed field, '
                                    'which cannot be found' % (modelName, parsed_name))
                text.extend( self.getAttributesDocumentation(subModel) )
        
        return '\n'.join(text)

    def getAuthDocumentation(self, modelName, view):
        # FIXME: Come back and finish this
        methodsDict = {'GET':'Anonymous', 'POST':'Anonymous',
                       'PUT':'Anonymous', 'DELETE':'Anonymous'}
        # for m in methodsDict:
        #     method = getattr(view, 'rest_%s' % m, None)
        #     methodsDict[m] = 'Supported' if method else 'Not Supported'
        return  methodsDict
        
    def getNotes(self, modelName):
        # FIXME: Come back and finish this
        return ''

    def getMethodsFromView(self, view):
        methodsDict = {'GET':'', 'POST':'', 'PUT':'', 'DELETE':''}
        for m in methodsDict:
            method = getattr(view, 'rest_%s' % m, None)
            methodsDict[m] = 'Supported' if method else 'Not Supported'
        return  methodsDict

    def parseName(self, name):
        """
        changes management_nodes to ManagementNodes
        """
        return ''.join([s.capitalize() for s in name.split('_')])

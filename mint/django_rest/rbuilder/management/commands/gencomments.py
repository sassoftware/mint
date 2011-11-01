import inspect
import os
from django.db import models as djmodels
from django.core.management.base import BaseCommand
from mint.django_rest.urls import urlpatterns
from mint.django_rest import settings_common as settings
from mint.django_rest.deco import ACCESS

AUTH_TEMPLATE = "%(ROLE)s: %(PERMS)s"
ATTRIBUTE_TEMPLATE = "    %(ATTRNAME)s : %(DOCSTRING)s"
DOCUMENT_TEMPLATE = \
"""
Resource Name: %(NAME)s

GET: %(GET_SUPPORTED)s
    Auth [%(GET_AUTH)s]
        
POST: %(POST_SUPPORTED)s  
    Auth [%(POST_AUTH)s]
        
PUT: %(PUT_SUPPORTED)s
    Auth [%(PUT_AUTH)s]
        
DELETE: %(DELETE_SUPPORTED)s
    Auth [%(DELETE_AUTH)s]
        
Attributes:
%(ATTRIBUTES)s

Notes: %(NOTES)s
""".strip()

HORIZ_ARROW = '---'
VERTICAL = '|'

class DocTreeFactory(object):
    """
    Used to create pretty trees ie:
    
    Root
      |--- Subheading 1
      |--- Subheading 2
    
    """
    def __init__(self, data):
        self.lines = data
        
    @staticmethod
    def generateArrow(line, spacer):
        return ' ' * spacer + VERTICAL + HORIZ_ARROW + ' %s' % line
        
    def makeTree(self, spacer=6):
        collected = []
        for line in self.lines:
            arrow = self.generateArrow(line, spacer)
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
            currentModel = self.aggregateModels.get(MODEL_NAME, None)
            # Skip all views that don't specify a model name
            if not MODEL_NAME or not currentModel:
                continue
                
            # get tag name of model.  the tag may be different
            # than the underscored version of the model name,
            # which is implementation dependent.  user only
            # needs the requested resource's tag
            MODEL_TAG = currentModel.getTag()
            # dict indexed by REST methods for the model
            METHODS = self.getMethodsFromView(view)
            # text formed by concatenating attr name with value of the docstring
            ATTRIBUTES = self.getAttributesDocumentation(MODEL_NAME)
            # dict keyed by REST method type with value one of:
            # anonymous, authenticated, admin, or rbac
            AUTH = self.getAuthDocumentation(MODEL_NAME, view)
            # any raw text from a model's _NOTE class attribute
            NOTES = self.getNotes(MODEL_NAME)
            
            TEXT = {'NAME':MODEL_TAG,
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
                if not inspect.isclass(obj) or not \
                    issubclass(obj, djmodels.Model):
                    continue
                allModels[objname] = obj
        return allModels

    def getAttributesDocumentation(self, modelName):
        # getAttributesDocumentation is called recursively to
        # calculate the attributes of models included by a
        # collection.  The terminating condition is a model name
        # of None
        if modelName is None:
            return ''
            
        text = []
        
        # start by getting model and processing its fields
        model = self.aggregateModels.get(modelName, None)
        if model is None:
            return ''
            
        # begin compiling attributes text
        for field in sorted(model._meta.fields, key=lambda x: x.name):
            name = field.name
            if name.startswith('_'): continue
            docstring = getattr(field, 'docstring', 'N/A')
            line = ATTRIBUTE_TEMPLATE % {'ATTRNAME':name, 'DOCSTRING':docstring}
            text.append(line)
        
        # look for items in the model's list_fields attribute, if any are
        # found then include them in the text.   
        listed = getattr(model, 'list_fields', None)
        if listed:
            xobjTags = {}
            # FIXME: reverseXObjTags is probably not needed anymore as
            # model.getTag() makes it easier to get at the tag names.
            # Excellent candidate for cleanup in future iterations.
            reverseXObjTags = {}
            foundModels = self.findModels().items()
            # precompute _xobj tags in case we need them
            for mname, m in foundModels:
                _xobj = getattr(m, '_xobj', None)
                tag = _xobj.tag if _xobj else _xobj
                xobjTags[mname] = (tag, m)
                # compute child model's tags for "reverse lookup"
                if tag:
                    reverseXObjTags[tag] = (mname, m)
            
            # inline list_fields
            for listedModelName in listed:
                # Check to see if the parsed listed model name points to the default
                # CamelCase, or if the tag is custom defined.  This ordinarily isn't
                # an issue except in cases like ProjectVersions.  ProjectVersions have
                # ProjectVersion as a list field.  However, the tag name for
                # ProjectVersion is "project_branches", and ProjectVersion has the
                # tag "project_branch".
                parsed_name = self.parseName(listedModelName)
                subModel = self.aggregateModels.get(parsed_name, None)
                
                # FIXME: This code is ugly if nothing else, and is a
                #        prime candidate for refactoring.  Comeback
                #        and address this soon.
                # if not subModel then check to see if parent model
                # references its children through a different tag name
                subModelName = None
                if subModel is None:
                    # _xobjData := (tag name, model) or None
                    _xobjData = xobjTags.get(parsed_name, None)
                    if _xobjData is not None and _xobjData[0]:
                        subModel = _xobjData[1]
                        subModelName = subModel.__name__
                    # reverseXObjTags := (model name, model)
                    elif listedModelName in reverseXObjTags:
                        subModel = reverseXObjTags[listedModelName][1]
                        subModelName = reverseXObjTags[listedModelName][0]
                    else:
                        print Warning('Model %s has model %s as a listed field, '
                                        'which cannot be found' % (modelName, parsed_name))
                else:
                    subModelName = subModel.__name__
                
                text.append('\nXML SubElement [%s]:' % subModel.getTag())
                # recurse
                text.append( self.getAttributesDocumentation(subModelName) )
        
        return '\n'.join(text)

    def getAuthDocumentation(self, modelName, view):
        """
        ACCESS is the following (inlined from deco.py)
        
        class ACCESS(object):
            ANONYMOUS = 1
            AUTHENTICATED = 2
            ADMIN = 4
            AUTH_TOKEN = 8
            LOCALHOST = 16
        """
        # any unsupported rest method should have a N/A
        # AUTH flag.
        resultsDict = {'GET':'N/A', 'POST':'N/A',
                       'PUT':'N/A', 'DELETE':'N/A'} 
        # get permitted methods 
        methodsDict = self.getMethodsFromView(view)
        for method, isSupported in methodsDict.items():
            if isSupported == 'Supported':
                restMethod = getattr(view, 'rest_%s' % method, None)
                if restMethod is not None:
                    access = getattr(restMethod, 'ACCESS', None)
                    rbac = getattr(restMethod, 'RBAC', None)
                    if rbac:
                        resultsDict[method] = 'RBAC'
                    elif access == ACCESS.ANONYMOUS:
                        resultsDict[method] = 'ANONYMOUS'
                    elif access == ACCESS.AUTHENTICATED:
                        resultsDict[method] = 'AUTHENTICATED'
                    elif access == ACCESS.ADMIN:
                        resultsDict[method] = 'ADMIN'
                    else:
                        print Warning(
                            'View method %s has an unrecognized authentication method' % view)
        return resultsDict
        
    def getNotes(self, modelName):
        """
        Allows user to define a _NOTE attribute on the model with some
        text to insert.  Right now triple quoted text is encouraged to
        simplify the formatting process.
        """
        model = self.aggregateModels.get(modelName, None)
        return getattr(model, '_NOTE', 'Empty')

    def getMethodsFromView(self, view):
        methodsDict = {'GET':'Not Supported', 'POST':'Not Supported',
                       'PUT':'Not Supported', 'DELETE':'Not Supported'}
        permitted_methods = view._getPermittedMethods()
        for method in methodsDict:
            if method in permitted_methods:
                methodsDict[method] = 'Supported'
        return methodsDict

    def parseName(self, name):
        """
        changes management_nodes to ManagementNodes
        """
        return ''.join([s.capitalize() for s in name.split('_')])

    def toUnderscore(self, name):
        """
        used to be unparseName
        ie: Changes ManagementNodes to management_nodes
        """
        L = []
        F = lambda i, c: L.append(c.lower()) if i == 0 else L.append('_' + c.lower())
        for i, c in enumerate(name):
            if c.isupper():
                F(i, c)
            else:
                L.append(c)
        return ''.join(L)

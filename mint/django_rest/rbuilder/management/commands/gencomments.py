from django.db import models as djmodels
from django.core.management.base import BaseCommand
from mint.django_rest.urls import urlpatterns
from mint.django_rest import settings_common as settings
from mint.django_rest.deco import ACCESS
import inspect
import os

AUTH_TEMPLATE = "%(ROLE)s: %(PERMS)s"
ATTRIBUTE_TEMPLATE = "    %(ATTRNAME)s : %(DOCSTRING)s"
DOCUMENT_TEMPLATE = \
"""
GET: %(GET_SUPPORTED)s  [%(GET_AUTH)s]
        
POST: %(POST_SUPPORTED)s  [%(POST_AUTH)s]
        
PUT: %(PUT_SUPPORTED)s  [%(PUT_AUTH)s]
        
DELETE: %(DELETE_SUPPORTED)s  [%(DELETE_AUTH)s]

Attributes:
%(ATTRIBUTES)s
""".strip()

def toCamelCaps(name):
    """
    changes management_nodes to ManagementNodes
    """
    return ''.join([s.capitalize() for s in name.split('_')])

def toUnderscore(name):
    """
    changes ManagementNodes to management_nodes
    """
    L = []
    F = lambda i, c: L.append(c.lower()) if i == 0 else L.append('_' + c.lower())
    for i, c in enumerate(name):
        if c.isupper():
            F(i, c)
        else:
            L.append(c)
    return ''.join(L)

def getApps():
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

def getApp(appName):
    allApps = getApps()
    return allApps[appName]

def findModels():
    allModels = {}
    for appName, app in getApps().items():
        for objName in dir(app):
            obj = getattr(app, objName)
            if not inspect.isclass(obj) or not \
                issubclass(obj, djmodels.Model):
                continue

            if objName in [n.split('.')[-1] for n in allModels.keys()]:
                print Warning(
                    '%s in app %s shares the same name with '
                    'one or more other models in different apps' % (objName, appName))

            combinedName = appName + '.' + objName
            allModels[combinedName] = obj
    return allModels

###### Lot of similarity and repetition of code, refactor if possible ######

def _calculateAppModels(app):
    appModels = {}
    for objname in dir(app):
        obj = getattr(app, objname)
        if not inspect.isclass(obj) or not \
            issubclass(obj, djmodels.Model):
            continue
        appModels[objname] = obj
    return appModels

def _calculateModelApps(modelName):
    """
    Have to account for the rare but hazardous case that
    two different apps have models of the same name.
    """
    done = []
    modelApps = {}
    for appName, app in getApps().items():
        for modelName in dir(app):
            obj = getattr(app, modelName)
            if not inspect.isclass(obj): continue
            if issubclass(obj, djmodels.Model):
                if modelName in done:
                    modelApps[modelName].append(appName)
                else:
                    modelApps[modelName] = [appName]
                done.append(modelName)
    return modelApps

############################################################################

class DocMetadata(object):
    
    _allApps = getApps()
    _allModels = findModels()
    
    def __init__(self, view, model):
        # preprocess -- turn view into an instance of a view
        self.view = view() if not isinstance(view, object) else view
        self.model = model
        
        # get the actual models that correspond to the parent's
        # list fields.  Attaches attr listFieldsModels (a dict)
        # which contains the following information:
        # listFieldsModels[list_fields tag] = submodel
        self.listFieldsModels = self._calculateListFieldsModels()
    
    def _calculateXObjTags(self):
        """
        helper method for _calculateListFieldsModels, could
        be a staticmethod if it would be useful
        """
        xobjTags = {}
        reverseXObjTags = {}
        allModels = DocMetadata._allModels.items()
        for mname, m in allModels:
            xobjTags[mname] = m
            _xobj = getattr(m, '_xobj', None)
            tag = None if not _xobj else _xobj.tag
            appname, mname = mname.split('.')
            if tag:
                reverseXObjTags[appname + '.' + tag] = m
        return (xobjTags, reverseXObjTags)
    
    def _calculateListFieldsModels(self):
        """
        get all the models referenced in the parent's list_fields.  note
        that the tag name in list_fields has to match the tag name of the
        model's tag, which may be different from the default tag.
        
        1) if tag in current app, return model from current app
        2) if not (1) and tag in one and only one different app,
           return the model from that app
        
        ** ideally, we should have a (3) that does the following **
        
        3) if not (1) and not (2), then tag either exists in two or
           more different apps, or it doesn't exist at all.  Skip it.
        
        FIXME: can't have condition (3) right now as it mysteriously
        causes the code to invalidate the list fields for a number of
        unambiguous cases...
        
        In the meantime, we accept that the algorithm works in almost
        all cases but a few, and that there might be some slight
        inaccuracies 
        """
        xobjTags, reverseXObjTags = self._calculateXObjTags()
        
        listFieldsModels = {}
        if self.listFields:
            allApps = getApps()
            
            for listedModelTag in self.listFields:
                # from model tag, try to reconstruct the default
                # tag name for the listed model
                camelCasedName = toCamelCaps(listedModelTag)
                # ie jobs.Jobs
                fullName = self.appName + '.' + camelCasedName
                listedModel = DocMetadata._allModels.get(fullName, None)
                # listedModel is None when the default tag name isn't being used
                # or when the model is in a different app
                if listedModel is None:
                    # try and pull out the model by its overridden tag name
                    for appName in allApps.keys():
                        overridenFullName = appName + '.' + listedModelTag
                        # model having the tag name has been found
                        if overridenFullName in reverseXObjTags:
                            listedModel = reverseXObjTags[overridenFullName]
                # populate dictionary, don't worry too much whether
                # or not listedModel is None -- that will be handled
                # inside the gencomment command's getAttrDocumentation
                listFieldsModels[listedModelTag] = listedModel
        return listFieldsModels
            
    @property
    def modelName(self):
        return self.model.__name__
    
    @property
    def xobjTag(self):
        if hasattr(self.model, '_xobj'):
            return self.model._xobj.tag
        return None
        
    @property
    def modelTag(self):
        return self.model.getTag()
    
    @property
    def listFields(self):
        return getattr(self.model, 'list_fields', None)
    
    @property
    def fields(self):
        return sorted(self.model._meta.fields, key=lambda x: x.name)
        
    @property
    def simpleFields(self):
        return dict(
            (fld.name, fld) for fld in self.fields if not isinstance(fld, djmodels.ForeignKey))
    
    @property
    def forwardReferences(self):
        return dict(
            (fld.name, fld) for fld in self.fields if isinstance(fld, djmodels.ForeignKey))
        
    @property
    def backwardReferences(self):
        pass
    
    @property
    def readonlyFields(self):
        return dict(
            (fld.name, fld) for fld in self.fields if getattr(fld, 'APIReadOnly', False))
        
    @property
    def hiddenFields(self):
        return dict(
            (fld.name, fld) for fld in self.fields if getattr(fld, 'XObjHidden', False))

    @property
    def hiddenAccessors(self):
        return getattr(self.model, '_xobj_hidden_accessors', None)

    @property
    def urls(self):
        pass

    @property
    def viewAuth(self):
        pass

    @property
    def permittedMethods(self):
        methods = {'GET' : 'Not Supported', 'POST'   : 'Not Supported',
                   'PUT' : 'Not Supported', 'DELETE' : 'Not Supported'}
        permitted_methods = self.view._getPermittedMethods()
        for mthd in methods:
            if mthd in permitted_methods:
                methods[mthd] = 'Supported'
        return methods

    @property
    def appName(self):
        cls = self.view.__class__
        # ie: path = ../../../include/mint/django_rest/rbuilder/users/views.pyc
        path = inspect.getfile(cls)
        # splitted path = [../../../include/mint/django_rest, users/views.pyc]
        path = path.split('/rbuilder/')[-1].split('/')[0]
        # now pull out name of the containing package for the view
        return path.split('/')[0]

    @property
    def app(self):
        return getApp(self.appName)

class Command(BaseCommand):
    help = "Generate comments for the REST documentation"
    
    def handle(self, *args, **options):
        for u in urlpatterns:
            view = u.callback
            # Name of model, taken from URL inside urlpatterns
            MODEL_NAME = getattr(u, 'model', None)
            currentModel = DocMetadata._allModels.get(MODEL_NAME, None)
            docMetadata = DocMetadata(view, currentModel)
            # Skip all views that don't specify a model name
            if not MODEL_NAME or not currentModel: continue
        
            # dict indexed by REST methods for the model
            METHODS = docMetadata.permittedMethods
            # text formed by concatenating attr name with value of the docstring
            ATTRIBUTES = self.getAttributesDocumentation(docMetadata)
            # dict keyed by REST method type with value one of:
            # anonymous, authenticated, admin, or rbac
            AUTH = self.getAuthDocumentation(docMetadata)
        
            TEXT = {'GET_SUPPORTED':METHODS['GET'],
                    'GET_AUTH':AUTH['GET'],
                    'POST_SUPPORTED':METHODS['POST'],
                    'POST_AUTH':AUTH['POST'],
                    'PUT_SUPPORTED':METHODS['PUT'],
                    'PUT_AUTH':AUTH['PUT'],
                    'DELETE_SUPPORTED':METHODS['DELETE'],
                    'DELETE_AUTH':AUTH['DELETE'],
                    'ATTRIBUTES':ATTRIBUTES,
                    }

            # absolute path to the containing pkg and
            # "app name" are the interpolated values
            BASE_PATH = "%s/rbuilder/docs/%s/" % (
                os.getcwd(), docMetadata.appName)
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

    def getAttributesDocumentation(self, metadata):
        """
        getAttributesDocumentation is called recursively to calculate
        the attributes of models included by a collection.
        """
        text = []

        # begin compiling attributes text
        for fieldname, field in metadata.simpleFields.items():
            if fieldname.startswith('_'): continue
            if fieldname in metadata.hiddenFields: continue
            if fieldname in metadata.readonlyFields: 
                fieldname = fieldname + ' ' + '(Readonly)'

            docstring = getattr(field, 'docstring', 'N/A')
            line = ATTRIBUTE_TEMPLATE % {'ATTRNAME':fieldname, 'DOCSTRING':docstring}
            text.append(line)
    
        # do FK's and M2M's
        # for fieldname, field in metadata.forwardReferences.items():
        #     pass
        # 
        # # pickup all back refs
        # for fieldname, field in metadata.backwardReferences.items():
        #     pass
    
        # if subModel is None then its listFields refers to an indeterminate
        # model tag (ie a model that exists in two or more different apps)
        for subModel in metadata.listFieldsModels.values():
            if subModel:
                text.append('\nXML SubElement [%s]:' % subModel.getTag())
                # doesn't matter what view we pass in
                metadata = DocMetadata(metadata.view, subModel)
                # recurse
                text.append( self.getAttributesDocumentation(metadata) )

        return '\n'.join(text)

    def getAuthDocumentation(self, metadata):
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
        authDict = {'GET' : 'N/A', 'POST'   : 'N/A',
                    'PUT' : 'N/A', 'DELETE' : 'N/A'} 
        view = metadata.view
        # get permitted methods 
        for method, isSupported in metadata.permittedMethods.items():
            if isSupported == 'Supported':
                restMethod = getattr(view, 'rest_%s' % method, None)
                if restMethod is not None:
                    access = getattr(restMethod, 'ACCESS', None)
                    rbac = getattr(restMethod, 'RBAC', None)
                    # default to AUTHENTICATED if no AUTH
                    # is explicitly set
                    if rbac:
                        authDict[method] = 'RBAC'
                    elif access == ACCESS.ANONYMOUS:
                        authDict[method] = 'ANONYMOUS'
                    elif access == ACCESS.ADMIN:
                        authDict[method] = 'ADMIN'
                    else:
                        authDict[method] = 'AUTHENTICATED'
        return authDict

    def getAppNameFromView(self, view):
        cls = view.__class__
        # ie: path = ../../../include/mint/django_rest/rbuilder/users/views.pyc
        path = inspect.getfile(cls)
        # splitted path = [../../../include/mint/django_rest, users/views.pyc]
        path = path.split('/rbuilder/')[-1].split('/')[0]
        # now pull out name of the containing package for the view
        return path.split('/')[0]

# import inspect
# import os
# from django.db import models as djmodels
# from django.core.management.base import BaseCommand
# from mint.django_rest.urls import urlpatterns
# from mint.django_rest import settings_common as settings
# from mint.django_rest.deco import ACCESS
# 
# AUTH_TEMPLATE = "%(ROLE)s: %(PERMS)s"
# ATTRIBUTE_TEMPLATE = "    %(ATTRNAME)s : %(DOCSTRING)s"
# DOCUMENT_TEMPLATE = \
# """
# GET: %(GET_SUPPORTED)s
#     Auth [%(GET_AUTH)s]
#         
# POST: %(POST_SUPPORTED)s  
#     Auth [%(POST_AUTH)s]
#         
# PUT: %(PUT_SUPPORTED)s
#     Auth [%(PUT_AUTH)s]
#         
# DELETE: %(DELETE_SUPPORTED)s
#     Auth [%(DELETE_AUTH)s]
#         
# Attributes:
# %(ATTRIBUTES)s
# """.strip()
# 
# HORIZ_ARROW = '---'
# VERTICAL = '|'
# 
# class DocTreeFactory(object):
#     """
#     Used to create pretty trees ie:
#     
#     Root
#       |--- Subheading 1
#       |--- Subheading 2
#     
#     """
#     def __init__(self, data):
#         self.lines = data
#         
#     @staticmethod
#     def generateArrow(line, spacer):
#         return ' ' * spacer + VERTICAL + HORIZ_ARROW + ' %s' % line
#         
#     def makeTree(self, spacer=6):
#         collected = []
#         for line in self.lines:
#             arrow = self.generateArrow(line, spacer)
#             collected.append(arrow)
#         return '\n'.join(collected)
# 
# class Command(BaseCommand):
#     help = "Generate comments for the REST documentation"
# 
#     def handle(self, *args, **options):
#         # Grab all models for all mint apps registered
#         # inside of settings.py
#         self.aggregateModels = self.findModels()
#         
#         for u in urlpatterns:
#             view = u.callback
#             # Name of model, taken from URL inside urlpatterns
#             MODEL_NAME = getattr(u, 'model', None)
#             currentModel = self.aggregateModels.get(MODEL_NAME, None)
#             # Skip all views that don't specify a model name
#             if not MODEL_NAME or not currentModel: continue
#             
#             # dict indexed by REST methods for the model
#             METHODS = self.getMethodsFromView(view)
#             # text formed by concatenating attr name with value of the docstring
#             ATTRIBUTES = self.getAttributesDocumentation(MODEL_NAME)
#             # dict keyed by REST method type with value one of:
#             # anonymous, authenticated, admin, or rbac
#             AUTH = self.getAuthDocumentation(MODEL_NAME, view)
#             
#             TEXT = {'GET_SUPPORTED':METHODS['GET'],
#                     'GET_AUTH':AUTH['GET'],
#                     'POST_SUPPORTED':METHODS['POST'],
#                     'POST_AUTH':AUTH['POST'],
#                     'PUT_SUPPORTED':METHODS['PUT'],
#                     'PUT_AUTH':AUTH['PUT'],
#                     'DELETE_SUPPORTED':METHODS['DELETE'],
#                     'DELETE_AUTH':AUTH['DELETE'],
#                     'ATTRIBUTES':ATTRIBUTES,
#                     }
#             
#             # absolute path to the containing pkg and
#             # "app name" are the interpolated values
#             BASE_PATH = "%s/rbuilder/docs/%s/" % (
#                 os.getcwd(), self.getPkgNameFromView(view))
#             # create destination directory if needed, raises
#             # exception if directory already exists, in which case
#             # just continue onward
#             try:
#                 os.makedirs(BASE_PATH)
#             except OSError, e:
#                 pass
#             
#             filepath = os.path.join(
#                 BASE_PATH, view.__class__.__name__)
# 
#             f = open(filepath + '.txt', 'w')
#             try:
#                 f.write(DOCUMENT_TEMPLATE % TEXT)
#             finally:
#                 f.close()
# 
#     def getPkgNameFromView(self, view):
#         cls = view.__class__
#         # ie: path = ../../../include/mint/django_rest/rbuilder/users/views.pyc
#         path = inspect.getfile(cls)
#         # splitted path = [../../../include/mint/django_rest, users/views.pyc]
#         path = path.split('/rbuilder/')[-1].split('/')[0]
#         # now pull out name of the containing package for the view
#         return path.split('/')[0]
# 
#     def getApps(self):
#         """
#         django's get_app and get_model are causing problems,
#         this hack will do for now
#         """
#         apps = {}
#         for fullName in settings.INSTALLED_APPS:
#             if not fullName.startswith('mint.'): continue
#             appName = fullName.split('.')[-1]
#             apps[appName] = __import__(
#                 fullName + '.models', {}, {}, ['models'])
#         return apps
# 
#     def findModels(self):
#         allModels = {}
#         for app in self.getApps().values():
#             for objname in dir(app):
#                 obj = getattr(app, objname)
#                 if not inspect.isclass(obj) or not \
#                     issubclass(obj, djmodels.Model):
#                     continue
#                 allModels[objname] = obj
#         return allModels
# 
#     def getAttributesDocumentation(self, modelName):
#         """
#         after some experimentation, it's become apparent
#         that the tag name returned by getTag does not always
#         return the underscored model name in the case that an
#         _xobj is not explicitly specified.  Keep this in mind
#         when refactoring getAttributesDocumentation -- see
#         FIXME inside getAttributesDocumentation.
#         """
#         # getAttributesDocumentation is called recursively to
#         # calculate the attributes of models included by a
#         # collection.  The terminating condition is a model name
#         # of None
#         if modelName is None:
#             return ''
#             
#         text = []
#         
#         # start by getting model and processing its fields
#         model = self.aggregateModels.get(modelName, None)
#         if model is None:
#             return ''
#             
#         # begin compiling attributes text
#         for field in sorted(model._meta.fields, key=lambda x: x.name):
#             name = field.name
#             if name.startswith('_'): continue
#             if getattr(field, 'XObjHidden', False): continue
#             if getattr(field, 'APIReadOnly', False):
#                 name = name + ' ' + '(Readonly)'
#             docstring = getattr(field, 'docstring', 'N/A')
#             line = ATTRIBUTE_TEMPLATE % {'ATTRNAME':name, 'DOCSTRING':docstring}
#             text.append(line)
#         
#         # look for items in the model's list_fields attribute, if any are
#         # found then include them in the text.   
#         listed = getattr(model, 'list_fields', None)
#         if listed:
#             xobjTags = {}
#             # FIXME: reverseXObjTags is probably not needed anymore as
#             # model.getTag() makes it easier to get at the tag names.
#             # Excellent candidate for cleanup in future iterations.
#             reverseXObjTags = {}
#             foundModels = self.findModels().items()
#             # precompute _xobj tags in case we need them
#             for mname, m in foundModels:
#                 _xobj = getattr(m, '_xobj', None)
#                 tag = _xobj.tag if _xobj else _xobj
#                 xobjTags[mname] = (tag, m)
#                 # compute child model's tags for "reverse lookup"
#                 if tag:
#                     reverseXObjTags[tag] = (mname, m)
#             
#             # inline list_fields
#             for listedModelName in listed:
#                 # Check to see if the parsed listed model name points to the default
#                 # CamelCase, or if the tag is custom defined.  This ordinarily isn't
#                 # an issue except in cases like ProjectVersions.  ProjectVersions have
#                 # ProjectVersion as a list field.  However, the tag name for
#                 # ProjectVersion is "project_branches", and ProjectVersion has the
#                 # tag "project_branch".
#                 parsed_name = self.toCamelCaps(listedModelName)
#                 subModel = self.aggregateModels.get(parsed_name, None)
#                 
#                 # FIXME: This code is ugly if nothing else, and is a
#                 #        prime candidate for refactoring.  Comeback
#                 #        and address this soon.
#                 # if not subModel then check to see if parent model
#                 # references its children through a different tag name
#                 subModelName = None
#                 if subModel is None:
#                     # _xobjData[model name] := (tag name, model) or None
#                     _xobjData = xobjTags.get(parsed_name, None)
#                     if _xobjData is not None and _xobjData[0]:
#                         subModel = _xobjData[1]
#                         subModelName = subModel.__name__
#                     # reverseXObjTags[tag name] := (model name, model)
#                     elif listedModelName in reverseXObjTags:
#                         subModel = reverseXObjTags[listedModelName][1]
#                         subModelName = reverseXObjTags[listedModelName][0]
#                     else:
#                         print Warning('Model %s has model %s as a listed field, '
#                                         'which cannot be found' % (modelName, parsed_name))
#                 else:
#                     subModelName = subModel.__name__
#                 
#                 text.append('\nXML SubElement [%s]:' % subModel.getTag())
#                 # recurse
#                 text.append( self.getAttributesDocumentation(subModelName) )
#         
#         return '\n'.join(text)
# 
#     def getAuthDocumentation(self, modelName, view):
#         """
#         ACCESS is the following (inlined from deco.py)
#         
#         class ACCESS(object):
#             ANONYMOUS = 1
#             AUTHENTICATED = 2
#             ADMIN = 4
#             AUTH_TOKEN = 8
#             LOCALHOST = 16
#         """
#         # any unsupported rest method should have a N/A
#         # AUTH flag.
#         resultsDict = {'GET':'N/A', 'POST':'N/A',
#                        'PUT':'N/A', 'DELETE':'N/A'} 
#         # get permitted methods 
#         methodsDict = self.getMethodsFromView(view)
#         for method, isSupported in methodsDict.items():
#             if isSupported == 'Supported':
#                 restMethod = getattr(view, 'rest_%s' % method, None)
#                 if restMethod is not None:
#                     access = getattr(restMethod, 'ACCESS', None)
#                     rbac = getattr(restMethod, 'RBAC', None)
#                     # default to AUTHENTICATED if no AUTH
#                     # is explicitly set
#                     if rbac:
#                         resultsDict[method] = 'RBAC'
#                     elif access == ACCESS.ANONYMOUS:
#                         resultsDict[method] = 'ANONYMOUS'
#                     elif access == ACCESS.AUTHENTICATED:
#                         resultsDict[method] = 'AUTHENTICATED'
#                     elif access == ACCESS.ADMIN:
#                         resultsDict[method] = 'ADMIN'
#                     elif access == ACCESS.AUTH_TOKEN:
#                         resultsDict[method] = 'AUTH_TOKEN'
#                     elif access == ACCESS.LOCALHOST:
#                         resultsDict[method] = 'LOCALHOST'
#                     else:
#                         resultsDict[method] = 'AUTHENTICATED'
#         return resultsDict
# 
#     def getMethodsFromView(self, view):
#         methodsDict = {'GET':'Not Supported', 'POST':'Not Supported',
#                        'PUT':'Not Supported', 'DELETE':'Not Supported'}
#         permitted_methods = view._getPermittedMethods()
#         for method in methodsDict:
#             if method in permitted_methods:
#                 methodsDict[method] = 'Supported'
#         return methodsDict
# 
#     def toCamelCaps(self, name):
#         """
#         changes management_nodes to ManagementNodes
#         """
#         return ''.join([s.capitalize() for s in name.split('_')])
# 
#     def toUnderscore(self, name):
#         """
#         used to be unparseName
#         ie: Changes ManagementNodes to management_nodes
#         """
#         L = []
#         F = lambda i, c: L.append(c.lower()) if i == 0 else L.append('_' + c.lower())
#         for i, c in enumerate(name):
#             if c.isupper():
#                 F(i, c)
#             else:
#                 L.append(c)
#         return ''.join(L)

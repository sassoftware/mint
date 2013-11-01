#
# Copyright (c) 2008 rPath, Inc.
# All rights reserved
#

import os
from StringIO import StringIO

from conary.lib import util

from pcreator.backend import errors
from pcreator import callbacks
import pcreator.factorydata
import pcreator.config
import pcreator.shimclient
from pcreator.backend import FILETYPE_PRIMARY, FILETYPE_UPLOADED

import mint_error

PCREATOR_TMPDIR_PREFIX = 'rb-pc-upload-'

from mint import mint_error

def getUploadDir(cfg, id):
    """
    @param cfg: Mint Configuration Object
    @type cfg: MintConfig
    @param id: upload ID
    @type id: str
    """
    path = os.path.join(cfg.dataPath, 'tmp', '%s%s' % (PCREATOR_TMPDIR_PREFIX, id))
    return path

def expandme(value):
    if value is None:
        return False
    if ('\n' in value) or (len(value) >= 50):
        return True
    else:
        return False

def isSelected(field, value, prefilled, prevChoices):
    '''
    Determines whether a checkbox or select box item should be selected/checked.  It does this by comparing the prefilled value, or in its abscense the default with the value representing the item.

    @param field: The field, retrieved by parsing the factory definition object
    @type field: PresentationField
    @param value: The value to compare against the field.
    @type value: any comparable type
    @param prefilled: The value prefilled from the uploaded file.
    @type prefilled: any comparable type
    @return: True if "value" should be selected in the interface.  False otherwise.
    @rtype: boolean
    '''
    v, x = effectiveValue(field, prefilled, prevChoices)
    if v is None:
        return False
    return str(v) == str(value)

### default value could be "0" "False", etc.
### value could be "True" or "False"
def isChecked(field, value, prefilled, prevChoices):
    """
        Same as L{isSelected}, except meant to be used to compare possible boolean values
    """
    v, x = effectiveValue(field, prefilled, prevChoices)
    if v is None:
        return False
    vb = v.upper() in ('TRUE', '0')
    pb = value.upper() in ('TRUE', '0')
    return vb == pb

def effectiveValue(field, prefilled, prevChoices):
    """
        For the field provided, return what should be sent to the UI, as well
        as what the working value from the factory was.

        @param field: The field, retrieved by parsing the factory definition object
        @type field: PresentationField
        @param value: The value to compare against the field.
        @type value: any comparable type
        @param prefilled: The value prefilled from the uploaded file.
        @type prefilled: any comparable type
        @return: (display value, factory value)
        @rtype: tuple(str, str)
    """
    wv = workingValue(field, prefilled)
    #Get from the previous choices the previous value and whether it was
    #modified
    prev_val = prevChoices.get(field.name, (None, False))
    if prev_val[1]:
        return prev_val[0], wv
    else:
        return wv, wv

def workingValue(field, prefilled):
    '''
    In order to display the proper value when displaying UI elements, we have to determine which value should be given.  Prefer the prefilled value, but if it's not given, use the field's default.
    '''
    if prefilled is not None:
        return prefilled
    else:
        return field.default

def drawField(factoryIndex, field, values, prevChoices, drawingMethods): 
    """
    @param field: the field to draw
    @type field: X{pcreator.factorydata.PresentationField}
    @param values: the prefilled values
    @type values: dict
    @param drawingMethods: a dictionary of available drawing methods.  Used keys include C{unconstrained}, C{small_enumeration}, C{medium_enumeration}, C{large_enumeration} for the different types of fields.  The appropriate method will be called and the output returned
    @type drawingMethods: dict of method references
    """
    name = field.name
    prefilled = values.get(name, None)
    fieldId= "%d_%s_id" % (factoryIndex, name)
    constraints = field.constraints

    #Take care of Boolean types
    if field.type == 'bool':
        return drawingMethods['boolean'](fieldId, field, prefilled, prevChoices)

    if len(constraints) != 1:
        return drawingMethods['unconstrained'](fieldId, field, [], prefilled, prevChoices)
    if set(('regexp', 'length')).intersection(set([x['constraintName'] for x in constraints])):
        return drawingMethods['unconstrained'](fieldId, field, [], prefilled, prevChoices)

    #We only have one constraint, and it's a legalValues, or a range
    # Blow up the possible list
    constraint = constraints[0]
    if constraint['constraintName'] == 'range':
        possibles = range(constraint['min'], constraint['max'])
    elif constraint['constraintName'] == 'legalValues':
        possibles = constraint['values']
    if len(possibles) <= 7:
        return drawingMethods['small_enumeration'](fieldId, field, possibles, prefilled, prevChoices)
    elif 7 < len(possibles) and len(possibles) < 40:
        return drawingMethods['medium_enumeration'](fieldId, field, possibles, prefilled, prevChoices)
    else:
        #TODO: If it's an integer field, maybe we should use a slider
        return drawingMethods['large_enumeration'](fieldId, field, [], prefilled, prevChoices)

class _Method(object):
    def __init__(self, name, realMethod, authMethod):
        self.name = name
        self.realMethod = realMethod

    def __call__(self, *args, **kwargs):
        #We don't care about authentication for the DirectBackend
        return self.realMethod(*args, **kwargs)

class MinimalConaryConfiguration(pcreator.backend.MinimalConaryConfiguration):
    fields = ['name', 'contact', 'repositoryMap', 'buildLabel', 'user',
            'installLabelPath', 'searchPath', 'entitlement', 'conaryProxy']
    def __init__(self, conarycfg, rmakeUser):
        hidePasswords = conarycfg.getDisplayOption('hidePasswords')
        try:
            conarycfg.setDisplayOptions(hidePasswords = False)
            self.lines = []
            for key in self.fields:
                if not conarycfg[key]:
                    # list constructs always get displayed.
                    # this block protects against things like repositoryMap []
                    # however, contact must always be set, even to empty string.
                    if key == 'contact':
                        conarycfg.configLine('contact')
                    else:
                        continue
                strio = StringIO()
                conarycfg.displayKey(key, out = strio)
                lines = strio.getvalue().splitlines()
                newLines = []
                for line in lines:
                    newLines.append(util.ProtectedString(line))
                self.lines.extend(((len(newLines) and newLines) or lines))
            self.lines.append('rmakeUser %s %s' % rmakeUser)
        finally:
            conarycfg.setDisplayOptions(hidePasswords = hidePasswords)

###
### Convenience methods for working with the package creator service
###

def getPackageCreatorFactories(pc, sessionHandle):
    """
        Calls the getCandidateBuildFactories method, but translates the package
        creator error to a mint error
    """
    try:
        factories = pc.getCandidateBuildFactories(sessionHandle)
        data = pc.getExistingFactoryData(sessionHandle)
    except errors.UnsupportedFileFormat, e:
        raise mint_error.PackageCreatorError("Error gathering Candidate Build Factories: %s",
            "The file uploaded is not a supported file type")
    except errors.UnsupportedSPFMetadataFormat, e:
        raise mint_error.PackageCreatorError('Error gathering candidate '
            'factories: %s.', e)
    except errors.ConfigDescriptorSchemaValidationError, e:
        raise mint_error.PackageCreatorError('Error gathering candidate build '
            'factories: Failed to validate config descriptor %s', e)
    except errors.ConfigDescriptorInvalidXMLError, e:
        raise mint_error.PackageCreatorError('Error gathering candidate build '
            'factories: Failed to parse config descriptor %s', e)
    return factories, data

def getFactoryDataFromXML(xmldata):
    """
    Given an xml blob (e.g. from getPackageFactories), we need to parse it so that it's useful

    """
    from pcreator import factorydata
    
    if xmldata:
        prevChoices = factorydata.xmlToDictWithModified( \
                StringIO(xmldata))
        return prevChoices
    else:
        return {}

def getFactoryDataFromDataDict(pcclient, sesH, factH, dataDict):
    """
    This is a convenience method: since we always get a dictionary as a result
    of the interview, we need an easy way to convert it into a factory data xml
    stream.

    Put it here so that it can be tested independently.
    """
    xmlstream = StringIO(pcclient.getFactoryDataDefinition(sesH, factH))
    xmlstream.seek(0)
    factDef = pcreator.factorydata.FactoryDefinition(fromStream=xmlstream)
    factoryData = pcreator.factorydata.FactoryData(factoryDefinition = factDef)

    for field in factDef.getDataFields():
        name = field.name
        val = dataDict.get(name, '')
        rval = dataDict.get(name + "_reference", '')
        factoryData.addField(name, val, modified=rval != val)
    xmldatastream = StringIO()
    factoryData.serialize(xmldatastream)
    xmldatastream.seek(0)
    return xmldatastream

def setupPCBackendCall(func):
    """ This is useful if a private method is needed before a public method is called """
    def PCBackendCallWrapper(s, *args, **kwargs):
        #Grab the auth token if it exists
        auth = getattr(s.server, '_auth')
        if auth:
            s.server._server.auth(auth)
        return func(s, *args, **kwargs)
    PCBackendCallWrapper.__wrapped_func__ = func
    return PCBackendCallWrapper

class ShimClient(pcreator.shimclient.ShimPackageCreatorClient):
    @setupPCBackendCall
    def uploadData(self, sessionHandle, name, filePath, mimeType, arches = []):
        try:
            currentFiles = self.server._server._getSessionValue(sessionHandle, 'currentFiles')
        except errors.InvalidSessionHandle:
            currentFiles = {}
        # the first file uploaded will be the primary file
        fileType = len(currentFiles) and FILETYPE_UPLOADED or FILETYPE_PRIMARY

        name = self.server._server._osIndependentBasename(name)
        archSet = set()
        for flv in [deps.parseFlavor(x) for x in arches]:
            for archClass in [x.name for x in flv.iterDepsByClass( \
                    deps.dependencyClasses[deps.DEP_CLASS_IS])]:
                archSet.add(archClass)

        currentFiles[name] = (filePath, fileType, mimeType, list(archSet))
        self.server._server._storeSessionValue(sessionHandle, 'currentFiles', currentFiles)

def getPackageCreatorClient(mintCfg, authToken, callback=None,
        djangoManagerCallback=None):
    auth = {'user': authToken[0], 'passwd': authToken[1]}
    cfg = pcreator.config.PackageCreatorServiceConfiguration()
    cfg.storagePath = os.path.join(mintCfg.dataPath, 'tmp')
    cfg.tmpFileStorage = cfg.storagePath
    cfg.djangoManagerCallback = djangoManagerCallback
    return ShimClient(cfg, auth, callback = callback)

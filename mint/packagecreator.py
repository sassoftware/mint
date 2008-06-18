#
# Copyright (c) 2008 rPath, Inc.
# All rights reserved
#

import os
import simplejson
from StringIO import StringIO

from pcreator.backend import errors
import pcreator.factorydata
import pcreator.config
import pcreator.shimclient

PCREATOR_TMPDIR_PREFIX = 'rb-pc-upload-'

from mint import mint_error

def getWorkingDir(cfg, id):
    """
    @param cfg: Mint Configuration Object
    @type cfg: MintConfig
    @param id: upload ID
    @type id: str
    """
    path = os.path.join(cfg.dataPath, 'tmp', '%s%s' % (PCREATOR_TMPDIR_PREFIX, id))
    return path

def isSelected(field, value, prefilled):
    '''
    Determines whether a checkbox or select box item should be selected/checked.  It does this by comparing the prefilled value, or in its abscense the default with the value representing the item.

    @param field: The field, retrieved by parsing the factory definition object
    @type field: PresentationField
    @param value: The value to compare against the field.
    @type value: any comparable type
    @param prefilled: The value prefilled from the uploaded file.
    @type value: any comparable type
    @return: True if "value" should be selected in the interface.  False otherwise.
    @rtype: boolean
    '''
    v = workingValue(field, prefilled)
    if v is None:
        return False
    return str(v) == str(value)

### default value could be "0" "False", etc.
### value could be "True" or "False"
def isChecked(field, value, prefilled):
    """
        Same as L{isSelected}, except meant to be used to compare possible boolean values
    """
    v = workingValue(field, prefilled)
    if v is None:
        return False
    vb = v.upper() in ('TRUE', '0')
    pb = value.upper() in ('TRUE', '0')
    return vb == pb

def workingValue(field, prefilled):
    '''
    In order to display the proper value when displaying UI elements, we have to determine which value should be given.  Prefer the prefilled value, but if it's not given, use the field's default.
    '''
    if prefilled is not None:
        return prefilled
    else:
        return field.default

def drawField(factoryIndex, field, values, drawingMethods): 
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
        return drawingMethods['boolean'](fieldId, field, prefilled)

    if len(constraints) != 1:
        return drawingMethods['unconstrained'](fieldId, field, [], prefilled)
    if set(('regexp', 'length')).intersection(set([x['constraintName'] for x in constraints])):
        return drawingMethods['unconstrained'](fieldId, field, [], prefilled)

    #We only have one constraint, and it's a legalValues, or a range
    # Blow up the possible list
    constraint = constraints[0]
    if constraint['constraintName'] == 'range':
        possibles = range(constraint['min'], constraint['max'])
    elif constraint['constraintName'] == 'legalValues':
        possibles = constraint['values']
    if len(possibles) <= 7:
        return drawingMethods['small_enumeration'](fieldId, field, possibles, prefilled)
    elif 7 < len(possibles) and len(possibles) < 40:
        return drawingMethods['medium_enumeration'](fieldId, field, possibles, prefilled)
    else:
        #TODO: If it's an integer field, maybe we should use a slider
        return drawingMethods['large_enumeration'](fieldId, field, [], prefilled)

class _Method(object):
    def __init__(self, name, realMethod, authMethod):
        self.name = name
        self.realMethod = realMethod

    def __call__(self, *args, **kwargs):
        #We don't care about authentication for the DirectBackend
        return self.realMethod(*args, **kwargs)

class MinimalConaryConfiguration(pcreator.backend.MinimalConaryConfiguration):
    fields = ['name', 'contact', 'repositoryMap', 'buildLabel', 'user',
            'installLabelPath', 'searchPath']
    def __init__(self, conarycfg):
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
                self.lines.extend(strio.getvalue().splitlines())
        finally:
            conarycfg.setDisplayOptions(hidePasswords = hidePasswords)

def getFactoryDataFromDataDict(pcclient, sesH, factH, dataDict):
    """
    This is a convenience method: since we always get a dictionary as a result of the interview, we need an easy way to convert it into a factory data xml stream.

    Put it here so that it can be tested independently.
    """
    xmlstream = StringIO(pcclient.getFactoryDataDefinition(sesH, factH))
    xmlstream.seek(0)
    factDef = pcreator.factorydata.FactoryDefinition(fromStream=xmlstream)
    factoryData = pcreator.factorydata.FactoryData(factoryDefinition = factDef)

    for (k,v) in dataDict.iteritems():
        factoryData.addField(k,v)
    xmldatastream = StringIO()
    factoryData.serialize(xmldatastream)
    xmldatastream.seek(0)
    return xmldatastream

class ShimClient(pcreator.shimclient.ShimPackageCreatorClient):
    def uploadData(self, sessionHandle, filePath):
        self.server._server._storeSessionValue( \
                sessionHandle, 'filePath', filePath)


def getPackageCreatorClient(mintCfg, authToken):
    auth = {'user': authToken[0], 'passwd': authToken[1]}
    if mintCfg.packageCreatorURL:
        return pcreator.client.PackageCreatorClient( \
                mintCfg.packageCreatorURL, auth)
    cfg = pcreator.config.PackageCreatorServiceConfiguration()
    cfg.storagePath = os.path.join(mintCfg.dataPath, 'tmp')
    cfg.tmpFileStorage = cfg.storagePath
    return ShimClient(cfg, auth)

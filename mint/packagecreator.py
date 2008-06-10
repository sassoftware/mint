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
    v = workingValue(field, prefilled)
    if v is None:
        return False
    return str(v) == str(value)

### default value could be "0" "False", etc.
### value could be "True" or "False"
def isChecked(field, value, prefilled):
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

class ShimClient(pcreator.shimclient.ShimPackageCreatorClient):
    def uploadData(self, sessionHandle, filePath):
        self.server._server._storeSessionValue( \
                sessionHandle, 'filePath', filePath)


def getPackageCreatorClient(tmpdir, authToken):
    cfg = pcreator.config.PackageCreatorServiceConfiguration()
    cfg.storagePath = tmpdir
    cfg.tmpFileStorage = tmpdir
    auth = {'user': authToken[0], 'passwd': authToken[1]}
    return ShimClient(cfg, auth)


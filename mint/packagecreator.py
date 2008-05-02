#
# Copyright (c) 2008 rPath, Inc.
# All rights reserved
#

import os
from pcreator.backend import errors
import pcreator.backend
import pcreator.factorydata
import pcreator.config

def getWorkingDir(cfg, id):
    """
    @param cfg: Mint Configuration Object
    @type cfg: MintConfig
    @param id: upload ID
    @type id: str
    """
    path = os.path.join(cfg.dataPath, 'tmp', 'rb-pc-upload-%s' % id)
    return path

def isSelected(field, value, prefilled):
    if prefilled is not None:
        v = prefilled
    else:
        v = field.get('default', '')
    return str(v) == str(value)

def drawField(factoryIndex, field, values, drawingMethods): 
    """
    @param field: the field to draw (output from the package creator factories list)
    @type field: dict
    @param values: the prefilled values
    @type values: dict
    @param drawingMethods: a dictionary of available drawing methods.  Used keys include C{unconstrained}, C{small_enumeration}, C{medium_enumeration}, C{large_enumeration} for the different types of fields.  The appropriate method will be called and the output returned
    @type drawingMethods: dict of method references
    """
    name = field['name']
    prefilled = values.get(name, None)
    fieldId= "%d_%s_id" % (factoryIndex, name)
    constraints = field['constraints']
    if len(constraints) != 1:
        return drawingMethods['unconstrained'](fieldId, field, [], prefilled)
    if set(('regexp', 'length')).intersection(set([x[0] for x in field['constraints']])):
        return drawingMethods['unconstrained'](fieldId, field, [], prefilled)

    #We only have one constraint, and it's an Enumeration, or a range
    # Blow up the possible list
    constraint = constraints[0]
    if constraint[0] == 'range':
        possibles = range(constraint[1][0], constraint[1][1])
    elif constraint[0] == 'legalValues':
        possibles = constraint[1]
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

class MinimalConaryConfiguration:
    def __init__(self, conarycfg):
        self.cfg = conarycfg

    def createConaryConfig(self):
        return self.cfg

class DirectLibraryBackend(pcreator.backend.BaseBackend):
    methodClass = _Method

    def __init__(self, tmpdir):
        cfg = pcreator.config.PackageCreatorServiceConfiguration()
        cfg.storagePath = tmpdir
        cfg.tmpFileStorage = tmpdir
        pcreator.backend.BaseBackend.__init__(self, cfg)

    def _getStorageDir(self):
        return self.cfg.tmpFileStorage

    @pcreator.backend.public
    def _uploadFile(self, file):
        return file

    @pcreator.backend.public
    def _makeSourceTrove(self, mincfg, fileHandle, factoryHandle, destLabel, data):
        #convert the datadict to the XML document
        castData = self.castFactoryData(factoryHandle, mincfg, data)

        #Create the xml document
        factoryData=pcreator.factorydata.dictToFactoryData(data)

        sourcehandle = pcreator.backend.BaseBackend._makeSourceTrove(self, mincfg, factoryHandle, fileHandle, destLabel, factoryData)

        return sourcehandle


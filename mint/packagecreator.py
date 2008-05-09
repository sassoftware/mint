#
# Copyright (c) 2008 rPath, Inc.
# All rights reserved
#

import os
import simplejson
from StringIO import StringIO

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
                    continue
                strio = StringIO()
                conarycfg.displayKey(key, out = strio)
                self.lines.extend(strio.getvalue().splitlines())
        finally:
            conarycfg.setDisplayOptions(hidePasswords = hidePasswords)

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
    def _startSession(self, prodDefTroveSpec, mincfg):
        # this class already is already based in a tmpdir, so we'll just
        # re-use the tmpname for the session name. this alleviates the need
        # to track pointless data
        storageDir = self._getStorageDir()
        data = {'productDefinition' : prodDefTroveSpec,
                'mincfg': mincfg.freeze()}
        fileName = os.path.basename(storageDir).replace('rb-pc-upload-', '')
        path = os.path.join(storageDir, fileName)
        f = open(path, 'w')
        f.write(simplejson.dumps(data))
        f.close()
        return fileName

    @pcreator.backend.public
    def _uploadData(self, sessionHandle, filePath):
        self._storeSessionValue(sessionHandle, 'filePath', filePath)

    @pcreator.backend.public
    def _makeSourceTrove(self, sessionHandle, factoryHandle, destLabel, data):
        # XXX destLabel is probably bogus. shouldn't that come from prod def?
        #convert the datadict to the XML document
        cfgData = str(self._getSessionValue(sessionHandle, 'mincfg'))
        mincfg = MinimalConaryConfiguration.thaw(cfgData)

        castData = self.castFactoryData(sessionHandle, factoryHandle, data)

        #Create the xml document
        factoryData=pcreator.factorydata.dictToFactoryData(castData)

        pcreator.backend.BaseBackend._makeSourceTrove(self, sessionHandle, factoryHandle, destLabel, factoryData)

#
# Copyright (c) 2007 rPath, Inc.
#
# All Rights Reserved
#

import copy
import elementtree.ElementTree
import StringIO
import mint_error

from mint import buildtypes

def dictAggregate(a, b):
    """1 level recursive dict update

    This function behaves similarly to a.update(b). However, neither of the
    input dicts are modified. Dictionaries stored in the top level of a or b
    will also be merged."""
    a = copy.deepcopy(a)
    b = copy.deepcopy(b)
    for bIndex, bValue in b.iteritems():
        if bIndex in a:
            if isinstance(a[bIndex], dict) and isinstance(bValue, dict):
                a[bIndex].update(bValue)
            else:
                a[bIndex] = bValue
        else:
            a[bIndex] = bValue
    return a

def dictFromElem(elem):
    res = {}
    type = elem.attrib.get('type').upper()
    if type in buildtypes.validBuildTypes:
        res['type'] = buildtypes.validBuildTypes[type]
    elif type != 'DEFAULT':
        raise mint_error.BuildXmlInvalid('Invalid build type: %s' % str(type))

    for child in elem.getchildren():
        if child.tag == 'buildValue':
            if child.text:
                child.text = child.text.strip()
            res.setdefault('data', {})[child.attrib.get('name')] = \
                child.text
        else:
            res[child.tag] = child.text.strip()
    return res

def buildsFromXml(xmlData, splitDefault = False):
    xmlStringIO = StringIO.StringIO(xmlData)
    tree = elementtree.ElementTree.ElementTree(file = xmlStringIO)
    root = tree.getroot()
    res = []
    if root.attrib.get('version') == '1.0':
        # first we will collect data marked as default
        defaults = [x for x in tree.findall('build') if \
                        x.attrib.get('type') == 'default']
        if len(defaults) > 1:
            raise mint_error.BuildXmlInvalid( \
                'Only one defaults section is allowed')
        elif len(defaults) < 1:
            default = {}
        else:
            default = dictFromElem(defaults[0])
        if splitDefault:
            res.append(default)
        for elem in [x for x in root.getchildren() if x not in defaults]:
            if splitDefault:
                res.append(dictFromElem(elem))
            else:
                res.append(dictAggregate(copy.deepcopy(default),
                                         dictFromElem(elem)))
    else:
        raise mint_error.BuildXmlInvalid( \
            'Unable to determine buildDefinition version')
    return res

def validateResults(func):
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        # call buildsFromXml to ensure output is useable
        buildsFromXml(res)
        return res
    return wrapper

@validateResults
def xmlFromData(buildList, version = '1.0'):
    """Build an XML build description tree from a list of builds

    @param buildlist a list of dictionaries describing a build. Each dict can
    have any of the following:
    {'type': index from buildtemplates.validBuildTypes, Note this is an enum,
                 so should be an INT. Omitting it means 'default'
     'name': name of the build,
     'troveName':
     'baseFlavor':
     'data': a dict containing entries for the buildData table
     }

    the data dict will contain keys which match names of build options from
    buildtemplates.py and values as they would be stored in the buildData tbale
    eg. 0 and 1 for boolean values."""
    if version == '1.0':
        root = elementtree.ElementTree.Element('buildDefinition')
        root.set('version', version)
        root.tail = '\n'
        prevBuild = None
        for buildDict in buildList:
            root.text = '\n    '
            elem = elementtree.ElementTree.SubElement(root, 'build')
            elem.tail = '\n'
            buildType = buildDict.get('type')
            assert buildType in buildtypes.TYPES or buildType is None, \
                "'%s' is not a valid build type" % str(buildType)
            typeList = [x[0] for x in buildtypes.validBuildTypes.iteritems() \
                            if x[1] == buildType]
            buildType = typeList and typeList[0] or 'default'
            elem.set('type', buildType)
            prevElem = None
            for name, value in sorted([x for x in buildDict.iteritems() \
                                    if x[0] not in ('type', 'data')]):
                elem.text = '\n        '
                subElem = elementtree.ElementTree.SubElement(elem, name)
                subElem.text = value
                subElem.tail = '\n    '
                if prevElem is not None:
                    prevElem.tail = '\n        '
                prevElem = subElem
            for name, value in sorted(buildDict.get('data', {}).iteritems()):
                elem.text = '\n        '
                subElem = elementtree.ElementTree.SubElement(elem, 'buildValue')
                subElem.set('name', name)
                subElem.text = str(value)
                subElem.tail = '\n    '
                if prevElem is not None:
                    prevElem.tail = '\n        '
                prevElem = subElem
            if prevBuild:
                prevBuild.tail = '\n    '
            prevBuild = elem
        return elementtree.ElementTree.tostring(root)
    else:
        raise AssertionError("Unknown xml version %s" % version)

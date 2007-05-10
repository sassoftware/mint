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
            res.setdefault('data', {})[child.attrib.get('name')] = \
                child.text.strip()
        else:
            res[child.tag] = child.text.strip()
    return res

def buildsFromXml(xmlData):
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
        default = dictFromElem(defaults[0])
        for elem in [x for x in root.getchildren() if x not in defaults]:
            res.append(dictAggregate(copy.deepcopy(default),
                                     dictFromElem(elem)))
    else:
        raise mint_error.BuildXmlInvalid( \
            'Unable to determine buildDefinition version')
    return res

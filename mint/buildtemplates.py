# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
import sys
from mint.data import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM, RDT_TROVE
from mint import buildtypes

class BuildOption(tuple):
    def __new__(self):
        return tuple.__new__(tuple, (self.type, self.default, self.prompt))

class StringOption(BuildOption):
    type = RDT_STRING

class IntegerOption(BuildOption):
    type = RDT_INT

class BooleanOption(BuildOption):
    type = RDT_BOOL

class TroveOption(BuildOption):
    type = RDT_TROVE

class EnumOption(BuildOption):
    type = RDT_ENUM

    def __new__(self):
        return tuple.__new__(tuple, (self.type, self.default, self.prompt, self.options))

optionNameMap = {
    'anacondaCustomTrove': 'anaconda-custom',
    'anacondaTemplatesTrove': 'anaconda-templates',
    'mediaTemplateTrove': 'media-template',
}


class Template(dict):
    def __init__(self):
        for option in self.__slots__:
            newOption = optionNameMap.get(option, option)
            dict.__setitem__(self, newOption,
                             sys.modules[__name__].__dict__[option]())

# *** Extremely Important ***
# Changing the names or semantic meanings of option classes or templates is
# the same thing as making a schema upgrade! do not do this lightly.

###
# Option Classes
###

class bugsUrl(StringOption):
    default = 'http://issues.rpath.com/'
    prompt = 'Bug report URL'

class installLabelPath(StringOption):
    default = ''
    prompt = 'Custom Conary installLabelPath setting (leave blank for default)'

class autoResolve(BooleanOption):
    default = False
    prompt = 'Automatically install required dependencies during updates'

class baseFileName(StringOption):
    default = ''
    prompt = 'Custom output filename prefix (replaces name-version-arch)'

class showMediaCheck(BooleanOption):
    default = False
    prompt = 'Prompt to verify CD/DVD images during install'

class betaNag(BooleanOption):
    default = False
    prompt = 'This build is considered a beta'

class maxIsoSize(EnumOption):
    default = '681574400'
    prompt = 'ISO Size'
    options = buildtypes.discSizes

class freespace(IntegerOption):
    default = 250
    prompt = 'How many MB of free space should be allocated in the image?'

class swapSize(IntegerOption):
    default = 128
    prompt = 'How many MB swap space should be reserved in this image?'

class vmMemory(IntegerOption):
    default = 256
    prompt = 'How much memory should VMware use when running this image?'

class unionfs(BooleanOption):
    default = False
    prompt = "Enable copy-on-write for entire filesystem. To use this, your group must contain the unionfs kernel module. (unionfs is available in contrib (unsupported). The unionfs module you use must match your kernel version.)"

class zisofs(BooleanOption):
    default = True
    prompt = 'Compress filesystem'

class boolArg(BooleanOption):
    default = False
    prompt = 'Garbage Boolean'

class stringArg(StringOption):
    default = ''
    prompt = 'Garbage String'

class intArg(IntegerOption):
    default = 0
    prompt = 'Garbage Integer'

class enumArg(EnumOption):
    default = '2'
    prompt = 'Garbage Enum'
    options = {'foo' : '0', 'bar': '1', 'baz': '2'}

class mediaTemplateTrove(TroveOption):
    default = ''
    prompt  = 'Version of media-template to use when creating this image'

class anacondaCustomTrove(TroveOption):
    default = ''
    prompt  = 'Version of anaconda-custom to use when creating this image'

class anacondaTemplatesTrove(TroveOption):
    default = ''
    prompt  = 'Version of anaconda-templates to use when creating this image'

###
# Templates
# classes must end with 'Template' to be properly processed.
###

class StubImageTemplate(Template):
    __slots__ = ['boolArg', 'stringArg', 'intArg', 'enumArg']
    id = buildtypes.STUB_IMAGE

class RawHdTemplate(Template):
    __slots__ = ['autoResolve', 'freespace', 'baseFileName',
                 'installLabelPath', 'swapSize']
    id = buildtypes.RAW_HD_IMAGE

class RawFsTemplate(Template):
    __slots__ = ['autoResolve', 'freespace', 'baseFileName',
                 'installLabelPath', 'swapSize']
    id = buildtypes.RAW_FS_IMAGE

class VmwareImageTemplate(Template):
    __slots__ = ['autoResolve', 'freespace', 'baseFileName', 'vmMemory',
                 'installLabelPath', 'swapSize']
    id = buildtypes.VMWARE_IMAGE

class InstallableIsoTemplate(Template):
    __slots__ = ['autoResolve', 'maxIsoSize', 'baseFileName', 'bugsUrl',
                 'installLabelPath', 'showMediaCheck', 'betaNag',
                 'mediaTemplateTrove', 'anacondaCustomTrove', 'anacondaTemplatesTrove']
    id = buildtypes.INSTALLABLE_ISO

class NetbootTemplate(Template):
    __slots__ = ['autoResolve', 'baseFileName', 'installLabelPath']
    id = buildtypes.NETBOOT_IMAGE

class LiveIsoTemplate(Template):
    __slots__ = ['autoResolve', 'baseFileName', 'installLabelPath', 'zisofs',
                 'unionfs']
    id = buildtypes.LIVE_ISO

class TarballTemplate(Template):
    __slots__ = ['autoResolve', 'baseFileName', 'installLabelPath', 'swapSize']
    id = buildtypes.TARBALL

########################

dataHeadings = {}
dataTemplates = {}

for templateName in [x for x in sys.modules[__name__].__dict__.keys() \
                     if x.endswith('Template') and x != 'Template']:
    template = sys.modules[__name__].__dict__[templateName]()
    dataHeadings[template.id] = buildtypes.typeNames[template.id] + \
                                ' Settings'
    dataTemplates[template.id] = template


def getDataTemplate(buildType):
    if buildType:
        return dataTemplates[buildType]
    else:
        return {}

def getDisplayTemplates():
    return [(x, dataHeadings[x], dataTemplates[x]) \
            for x in dataTemplates.keys()]


# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
import sys
from mint.data import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM, RDT_TROVE
from mint import buildtypes
from mint.mint_error import InvalidBuildOption, BuildOptionValidationException

class BuildOption(tuple):
    errordesc = None
    def __new__(cls):
        return tuple.__new__(cls, (cls.type, cls.default, cls.prompt, cls.errordesc))
    def validate(self, value):
        pass

class StringOption(BuildOption):
    type = RDT_STRING

class IntegerOption(BuildOption):
    type = RDT_INT
    def validate(self, value):
        if not value or not value.isdigit() or value < 0:
            raise InvalidBuildOption(self[3])

class BooleanOption(BuildOption):
    type = RDT_BOOL

class TroveOption(BuildOption):
    type = RDT_TROVE

class EnumOption(BuildOption):
    type = RDT_ENUM

    def __new__(self):
        return tuple.__new__(EnumOption, (self.type, self.default, self.prompt, self.options))


optionNameMap = {
    'anacondaCustomTrove': 'anaconda-custom',
    'anacondaTemplatesTrove': 'anaconda-templates',
    'mediaTemplateTrove': 'media-template',
}

diskAdapters = {
    'IDE' : 'ide',
    'SCSI (LSILogic)' : 'lsilogic',
}

class Template(dict):
    def __init__(self):
        for option in self.__slots__:
            newOption = optionNameMap.get(option, option)
            dict.__setitem__(self, newOption,
                             sys.modules[__name__].__dict__[option]())

    def iteroptions(self):
        for optionName in self.__slots__:
            optionName = optionNameMap.get(optionName, optionName)
            option = self.get(optionName)
            yield optionName, option

    def validate(self, **kwargs):
        errors = []
        for optionName, option in self.iteroptions():
            if optionName not in kwargs:
                continue
            try:
                option.validate(kwargs[optionName])
            except InvalidBuildOption, e:
                errors.append(str(e))

        if len(errors):
            raise BuildOptionValidationException(errors)

    def getDefaultDict(self):
        d = {}
        for optionName, option in self.iteroptions():
            d[optionName] = option[1]
        return d


# *** Extremely Important ***
# Changing the names or semantic meanings of option classes or templates is
# the same thing as making a schema upgrade! do not do this lightly.

# *** Extremely Important ***
# adding options, or changing their meanings or defaults should be accompanied
# by a bump in serializationVersion.

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
    prompt = 'Custom image file name (replaces name-version-arch)'

class showMediaCheck(BooleanOption):
    default = False
    prompt = 'Prompt to verify CD/DVD images during install'

class betaNag(BooleanOption):
    default = False
    prompt = 'This image is considered a beta'

class maxIsoSize(EnumOption):
    default = '681574400'
    prompt = 'ISO Size'
    options = buildtypes.discSizes

class freespace(IntegerOption):
    default = 250
    prompt = 'How many MB of free space should be allocated in the image?'
    errordesc = "free space"

class swapSize(IntegerOption):
    default = 128
    prompt = 'How many MB swap space should be reserved in this image?'
    errordesc = "swap space"

class vmMemory(IntegerOption):
    default = 256
    prompt = 'How much memory should be used when running this image?'
    errordesc = "vmware memory"

class vmSnapshots(BooleanOption):
    default = False
    prompt = 'Allow snapshots to be created'

class diskAdapter(EnumOption):
    default = 'lsilogic'
    prompt = 'Which hard disk adapter should this image be built for?'
    options = diskAdapters

class natNetworking(BooleanOption):
    default = False
    prompt = 'Use NAT instead of bridged networking.'

class unionfs(BooleanOption):
    default = False
    prompt = "Enable UnionFS for the entire filesystem. (For this option, the UnionFS kernel module is required in the group. See rBuilder documentation for more information on this option.)"

class zisofs(BooleanOption):
    default = True
    prompt = 'Compress filesystem'

class vhdDiskType(EnumOption):
    default = 'dynamic'
    prompt = "VHD hard disk type"
    options = {'Fixed image' : 'fixed',
               'Dynamic image' : 'dynamic',
               'Difference image' : 'difference'}

class boolArg(BooleanOption):
    default = False
    prompt = 'Garbage Boolean'

class stringArg(StringOption):
    default = ''
    prompt = 'Garbage String'

class intArg(IntegerOption):
    default = 0
    prompt = 'Garbage Integer'
    errordesc = "garbage error"

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

class amiHugeDiskMountpoint(StringOption):
    default = ''
    prompt  = 'Mountpoint for scratch space (/dev/sda2) on AMI'

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
                 'installLabelPath', 'swapSize', 'natNetworking',
                 'diskAdapter', 'vmSnapshots']
    id = buildtypes.VMWARE_IMAGE

class VmwareESXImageTemplate(Template):
    __slots__ = ['autoResolve', 'freespace', 'baseFileName', 'vmMemory',
                 'installLabelPath', 'swapSize', 'natNetworking']
    id = buildtypes.VMWARE_ESX_IMAGE

class InstallableIsoTemplate(Template):
    __slots__ = ['autoResolve', 'maxIsoSize', 'baseFileName', 'bugsUrl',
                 'installLabelPath', 'showMediaCheck', 'betaNag',
                 'mediaTemplateTrove', 'anacondaCustomTrove',
                 'anacondaTemplatesTrove']
    id = buildtypes.INSTALLABLE_ISO

class UpdateIsoTemplate(Template):
    __slots__ = ['baseFileName', 'mediaTemplateTrove']
    id = buildtypes.UPDATE_ISO

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

class VirtualPCTemplate(Template):
    __slots__ = ['autoResolve', 'freespace', 'baseFileName', 'installLabelPath',
                 'swapSize', 'vhdDiskType']
    id = buildtypes.VIRTUAL_PC_IMAGE

class XenOVATemplate(Template):
    __slots__ = ['autoResolve', 'freespace', 'baseFileName', 'installLabelPath',
                 'swapSize', 'vmMemory']
    id = buildtypes.XEN_OVA

class VirtualIronVHDTemplate(Template):
    __slots__ = ['autoResolve', 'freespace', 'baseFileName', 'installLabelPath',
                 'swapSize', 'vhdDiskType']
    id = buildtypes.VIRTUAL_IRON

class AMITemplate(Template):
    __slots__ = ['autoResolve', 'freespace', 'baseFileName',
                 'amiHugeDiskMountpoint', 'installLabelPath']
    id = buildtypes.AMI

class ApplianceISOTemplate(Template):
    __slots__ = ['autoResolve', 'baseFileName', 'bugsUrl',
                 'installLabelPath', 'showMediaCheck', 'betaNag',
                 'mediaTemplateTrove', 'anacondaCustomTrove',
                 'anacondaTemplatesTrove']
    id = buildtypes.APPLIANCE_ISO

class ImagelessTemplate(Template):
    __slots__ = []
    id = buildtypes.IMAGELESS

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

def getDataTemplateByXmlName(xmlName):
    buildType = buildtypes.xmlTagNameImageTypeMap.get(xmlName)
    return dataTemplates.get(buildType, {})

def getDisplayTemplates():
    return [(x, dataHeadings[x], dataTemplates[x]) \
            for x in dataTemplates.keys()]

def getValueToTemplateIdMap():
    templateIdMap = dict()
    for id, dataHeading, dataTemplate in getDisplayTemplates():
        for optionName, option in dataTemplate.items():
            if optionName not in templateIdMap.keys():
                templateIdMap[optionName] = ([], option)
            templateIdMap[optionName][0].append(id)
    return templateIdMap

# code generator run by make to generate javascript constants
# should only be run by the makefile in mint/web/content/javascript
def codegen():
    import simplejson
    s = "// this Javascript was generated by mint/buildtemplates.py\n"
    s += "// do not edit or check into source control\n"

    blob = dict((x[0], x[2]) for x in getDisplayTemplates())
    s += "var defaultBuildOpts = %s;\n" % simplejson.dumps(blob)

    return s

if __name__ == "__main__": #pragma: no cover
    if len(sys.argv) > 1 and sys.argv[1] == "--genjs":
        print codegen()
        sys.exit(0)
    else:
        sys.exit(1)

#
# Copyright (c) 2011 rPath, Inc.
#

# pyflakes=ignore-file

import sys
from conary.deps import deps

validBuildTypes = {
    'BOOTABLE_IMAGE'    : 0,
    'INSTALLABLE_ISO'   : 1,
    'STUB_IMAGE'        : 2,
    'RAW_FS_IMAGE'      : 3,
    'NETBOOT_IMAGE'     : 4,
    'TARBALL'           : 5,
    'LIVE_ISO'          : 6,
    'RAW_HD_IMAGE'      : 7,
    'VMWARE_IMAGE'      : 8,
    'VMWARE_ESX_IMAGE'  : 9,
    'VIRTUAL_PC_IMAGE'  : 10,
    'XEN_OVA'           : 11,
    'VIRTUAL_IRON'      : 12,
    'PARALLELS'         : 13,
    'AMI'               : 14,
    'UPDATE_ISO'        : 15,
    'APPLIANCE_ISO'     : 16,
    'IMAGELESS'         : 17,
    'VMWARE_OVF_IMAGE'  : 18,
    'WINDOWS_ISO'       : 19,
    'WINDOWS_WIM'       : 20,
    'DEFERRED_IMAGE'    : 21,
}

TYPES = validBuildTypes.values()

# add all the defined image types directly to the module so that the standard
# approach of "buildtypes.IMAGE_TYPE" will result in the expected enum
sys.modules[__name__].__dict__.update(validBuildTypes)

deprecatedBuildTypes = {
    'QEMU_IMAGE' : RAW_HD_IMAGE
    }

windowsBuildTypes = set([
    WINDOWS_ISO,
    WINDOWS_WIM,
    ])

#
# These are identifying pieces of information that we can extract from the
# flavor of a build, but not necessarily tied to any particular build type.
#
# These can sometimes be used as a buildType, indexes starting at 100.
#
flavorFlags = {
    'XEN_DOMU':     100,
    'APPLIANCE':    101,
}

FLAG_TYPES = flavorFlags.values()

flavorFlagsFromId = dict((x[1], x[0]) for x in flavorFlags.items())

sys.modules[__name__].__dict__.update(flavorFlags)

flavorFlagFlavors = {
    XEN_DOMU:   "use: xen, domU",
    APPLIANCE:  "use: appliance",
}

flavorFlagNames = {
    XEN_DOMU:   "DomU",
    APPLIANCE:  "Appliance",
}

#BOOTABLE_IMAGE Should never get stored in the DB and therefore doesn't need a name

# NOTA BENE: Using Latin-1 here is harmful to XML-RPC which expects UTF-8
# Until we figure out the root cause, use "(R)" for registered trademark here.

typeNames = {
    NETBOOT_IMAGE:      "Netboot Image",
    INSTALLABLE_ISO:    "Installable CD/DVD",
    RAW_FS_IMAGE:       "Raw Filesystem Image",
    STUB_IMAGE:         "Stub Image",
    RAW_HD_IMAGE:       "Raw Hard Disk Image",
    VMWARE_IMAGE:       "VMware (R) Virtual Appliance",
    VMWARE_ESX_IMAGE:   "VMware (R) ESX Server Virtual Appliance",
    VMWARE_OVF_IMAGE:   "VMware (R) Virtual Appliance OVF",
    LIVE_ISO:           "Demo CD/DVD (Live CD/DVD)",
    TARBALL:            "Compressed Tar File",
    VIRTUAL_PC_IMAGE:   "VHD for Microsoft (R) Hyper-V",
    XEN_OVA:            "Citrix XenServer (TM) Appliance",
    VIRTUAL_IRON:       "Virtual Iron Virtual Appliance",
    PARALLELS:          "Parallels Virtual Appliance",
    AMI:                "Amazon Machine Image (EC2)",
    UPDATE_ISO:         "Update CD/DVD",
    APPLIANCE_ISO:      "Appliance Installable ISO",
    DEFERRED_IMAGE:     "Layered Image",
    WINDOWS_ISO:        "Windows Installable ISO",
    WINDOWS_WIM:        "Windows Imaging Format (WIM)",
    IMAGELESS:          "Online Update"
}

typeNamesShort = {
    NETBOOT_IMAGE:      "Netboot",
    INSTALLABLE_ISO:    "Inst CD/DVD",
    RAW_FS_IMAGE:       "Raw FS",
    STUB_IMAGE:         "Stub",
    RAW_HD_IMAGE:       "HDD",
    VMWARE_IMAGE:       "VMware (R)",
    VMWARE_ESX_IMAGE:   "VMware (R) ESX",
    LIVE_ISO:           "Demo CD/DVD",
    TARBALL:            "Tar",
    VIRTUAL_PC_IMAGE:   "Microsoft (R) Hyper-V",
    XEN_OVA:            "Citrix XenServer (TM)",
    VIRTUAL_IRON:       "Virtual Iron",
    PARALLELS:          "Parallels",
    AMI:                "AMI",
    UPDATE_ISO:         "Update CD/DVD",
    APPLIANCE_ISO:      "Appliance Inst",
    DEFERRED_IMAGE:     "Layered",
    WINDOWS_ISO:        "Windows Inst",
    WINDOWS_WIM:        "Windows WIM",
    IMAGELESS:          "Online Update",
    VMWARE_OVF_IMAGE:   "VMware (R) OVF",
}

# To be used to map image types ids from XML tag names
# used the build definition contained within the
# product definition.
#
# Note: Only supported image types are contained here.
# Thus you will not see XML tags for the following:
#   - STUB_IMAGE
#   - PARALLELS
#
# Furthermore, we don't support IMAGELESS builds
# in the context of a product definition.
#
xmlTagNameImageTypeMap = {
    'amiImage':            AMI,
    'applianceIsoImage':   APPLIANCE_ISO,
    'deferredImage':       DEFERRED_IMAGE,
    'installableIsoImage': INSTALLABLE_ISO,
    'liveIsoImage':        LIVE_ISO,
    'netbootImage':        NETBOOT_IMAGE,
    'rawFsImage':          RAW_FS_IMAGE,
    'rawHdImage':          RAW_HD_IMAGE,
    'tarballImage':        TARBALL,
    'updateIsoImage':      UPDATE_ISO,
    'vhdImage':            VIRTUAL_PC_IMAGE,
    'virtualIronImage':    VIRTUAL_IRON,
    'vmwareImage':         VMWARE_IMAGE,
    'vmwareEsxImage':      VMWARE_ESX_IMAGE,
    'vmwareOvfImage':      VMWARE_OVF_IMAGE,
    'xenOvaImage':         XEN_OVA,
    'imageless':           IMAGELESS,
    'windowsIsoImage':     WINDOWS_ISO,
    'wimImage':            WINDOWS_WIM, 
}

imageTypeXmlTagNameMap = dict([(v,k) for k,v in xmlTagNameImageTypeMap.iteritems()])

typeNamesMarketing = {
    NETBOOT_IMAGE:      "Netboot Image",
    INSTALLABLE_ISO:    "Legacy Installable CD/DVD",
    RAW_FS_IMAGE:       "Eucalyptus/Mountable Filesystem",
    STUB_IMAGE:         "Stub Image",
    RAW_HD_IMAGE:       "KVM/QEMU/Raw Hard Disk",
    VMWARE_IMAGE:       "VMware(R) Workstation/Fusion / Parallels(R) Virtual Appliance",
    VMWARE_ESX_IMAGE:   "VMware(R) ESX/VCD / Oracle(R) VirtualBox Virtual Appliance",
    VMWARE_OVF_IMAGE:   "VMware(R) Virtual Appliance OVF",
    LIVE_ISO:           "Demo CD/DVD (Live CD/DVD)",
    TARBALL:            "TAR File",
    VIRTUAL_PC_IMAGE:   "VHD for Microsoft(R) Hyper-V(R)",
    XEN_OVA:            "Citrix(R) XenServer(TM) Appliance",
    VIRTUAL_IRON:       "Virtual Iron Virtual Appliance",
    PARALLELS:          "Parallels(R) Virtual Appliance",
    AMI:                "Amazon Machine Image (EC2)",
    UPDATE_ISO:         "Update CD/DVD",
    APPLIANCE_ISO:      "Appliance Installable ISO",
    DEFERRED_IMAGE:     "Layered Image",
    WINDOWS_ISO:        "Installable CD/DVD (ISO)",
    WINDOWS_WIM:        "Windows Imaging Format (WIM)",
    IMAGELESS:          "Online Update",

    # flavor flags here
    XEN_DOMU:           "DomU",
    APPLIANCE:          "Appliance",
}

buildTypeExtra = {
    APPLIANCE_ISO:      "This image type will not work without using "
                        "a version of anaconda-templates based on "
                        "rPath Linux 2.",
    IMAGELESS:          "Select this image type to mark a group for "
                        "later publishing to an Update Service."
}

buildTypeIcons = {
    VMWARE_IMAGE: dict(
        icon="get-vmware-player.png",
        href="http://www.vmware.com/download/player/",
        text="Download VMware Player"),
    RAW_HD_IMAGE: dict(
        icon="get-parallels.png",
        href="http://www.parallels.com/",
        text="Try Parallels Workstation 2.2"),
    VIRTUAL_IRON: dict(
        icon="get-virtual-iron.png",
        href="http://www.virtualiron.com/free",
        text="Virtual Iron: Download Now"),
    XEN_OVA: dict(
        icon="get-xen-express.gif",
        href="http://www.citrix.com/xenserver/getexpress",
        text="Citrix XenServer Express Edition: Download Now",
        ),
    VIRTUAL_PC_IMAGE: dict(
        icon="get-hyper-v.png",
        href="http://www.microsoft.com/Hyper-V",
        text="Learn more about Microsoft Hyper-V",
        ),
}

typeFlavorOverride = {
    (RAW_HD_IMAGE, XEN_DOMU):   dict(
        marketingName="Raw Hard Disk Image",
        icon=False,
        ),
}


# sizes are listed in bytes...
discSizes = {
    'CD: 650 MB'  : '681574400',
    'CD: 700 MB'  : '734003200',
    'DVD: 4.7 GB' : '4700000000',
    'DVD: 8.5 GB' : '8500000000',
}

buildDefinitionFlavorTypes = {
    'BD_GENERIC_X86'    : 0,
    'BD_GENERIC_X86_64' : 1,
    'BD_DOM0_X86'       : 2,
    'BD_DOM0_X86_64'    : 3,
    'BD_DOMU_X86'       : 4,
    'BD_DOMU_X86_64'    : 5,
    'BD_VMWARE_X86'     : 6,
    'BD_VMWARE_X86_64'  : 7,
}

sys.modules[__name__].__dict__.update(buildDefinitionFlavorTypes)

buildDefinitionFlavorMap = {
    BD_GENERIC_X86      : '!dom0, !domU, !xen, !vmware is: x86',
    BD_GENERIC_X86_64   : '!dom0, !domU, !xen, !vmware is: x86_64',
    BD_DOM0_X86         : 'dom0, !domU, xen, !vmware is: x86',
    BD_DOM0_X86_64      : 'dom0, !domU, xen, !vmware is: x86_64',
    BD_DOMU_X86         : '!dom0, domU, xen, !vmware is: x86',
    BD_DOMU_X86_64      : '!dom0, domU, xen, !vmware is: x86_64',
    BD_VMWARE_X86       : '!dom0, !domU, !xen, vmware is: x86',
    BD_VMWARE_X86_64    : '!dom0, !domU, !xen, vmware is: x86_64',
}

def alphabatizeBuildTypes(visibleBuildTypes):
    sortedList = sorted([x for x in visibleBuildTypes if x != IMAGELESS],
            key = lambda x: typeNames.get(x))
    if IMAGELESS in visibleBuildTypes:
        sortedList.insert(0, IMAGELESS)
    return sortedList

def makeBuildFlavorMap(prd):
    baseFlavor = prd.getBaseFlavor() or prd.getPlatformBaseFlavor() or ''
    baseFlavor = deps.parseFlavor(baseFlavor)
    flavorSets = prd.getFlavorSets()
    architectures = prd.getArchitectures()
    if prd.platform:
        flavorSets += prd.platform.getFlavorSets()
        architectures = prd.platform.getArchitectures()
    res = {}
    for flavorSet in flavorSets:
        for architecture in architectures:
            flv = deps.parseFlavor(flavorSet.flavor)
            arch = deps.parseFlavor(architecture.flavor)
            flavor = deps.overrideFlavor(baseFlavor, flv)
            flavor = deps.overrideFlavor(flavor, arch)
            res[str(flavor)] = \
                    "%s %s" % (flavorSet.displayName, architecture.displayName)
    return res

def makeFlavorMap(prd):
    flavorSets = prd.getFlavorSets()
    architectures = prd.getArchitectures()
    if prd.platform:
        flavorSets += prd.platform.getFlavorSets()
        architectures += prd.platform.getArchitectures()
    return dict([("%s %s" % (x.displayName, y.displayName),
                  "%s,%s" % (x.name, y.name)) \
            for x in flavorSets for y in architectures])

def makeFlavorsForBuild(prd, key):
    # compose a flavor map much like above but filter illegal types
    flavorSets = prd.getFlavorSets()
    architectures = prd.getArchitectures()
    buildTemplates = prd.getBuildTemplates()
    if prd.platform:
        flavorSets += prd.platform.getFlavorSets()
        architectures += prd.platform.getArchitectures()
        buildTemplates += prd.platform.getBuildTemplates()
    containerTemplateRef = imageTypeXmlTagNameMap.get(key)
    if not containerTemplateRef:
        return makeFlavorMap(prd)

    # for arch and flavorSet, if None is encountered, all available types
    # are legal
    arches = set([x.architectureRef for x in buildTemplates \
            if x.containerTemplateRef == containerTemplateRef])
    arches = [x for x in architectures if None in arches or x.name in arches]

    flavors = set([x.flavorSetRef for x in buildTemplates \
            if x.containerTemplateRef == containerTemplateRef])
    flavors = [x for x in flavorSets if None in flavors or x.name in flavors]

    return dict([("%s %s" % (x.displayName, y.displayName),
                  "%s,%s" % (x.name, y.name)) \
            for x in flavors for y in arches])

# generate mapping of flavors to flavor names
buildDefinitionFlavorToFlavorMapRev = \
    dict((x[1], x[0]) for x in buildDefinitionFlavorMap.iteritems())

buildDefinitionFlavorNameMap = {
    BD_GENERIC_X86      : 'Generic x86 (32-bit)',
    BD_GENERIC_X86_64   : 'Generic x86 (64-bit)',
    BD_DOM0_X86         : 'dom0 x86 (32-bit)',
    BD_DOM0_X86_64      : 'dom0 x86 (64-bit)',
    BD_DOMU_X86         : 'domU x86 (32-bit)',
    BD_DOMU_X86_64      : 'domU x86 (64-bit)',
    BD_VMWARE_X86       : 'VMware x86 (32-bit)',
    BD_VMWARE_X86_64    : 'VMware x86 (64-bit)',
}

# a mapping of build types to supported flavors.  If a build type does not
# exist in this map, it is assumed it supports all flavors.  The first flavor
# is assumed to be the default.
buildDefinitionSupportedFlavorsMap = {
    VMWARE_IMAGE       : [BD_VMWARE_X86, BD_VMWARE_X86_64],
    VMWARE_ESX_IMAGE   : [BD_VMWARE_X86, BD_VMWARE_X86_64],
    XEN_OVA            : [BD_DOMU_X86, BD_DOMU_X86_64],
    AMI                : [BD_DOMU_X86, BD_DOMU_X86_64],
}

# code generator run by make to generate javascript constants
# should only be run by the makefile in mint/web/content/javascript
def codegen():
    s = "// this Javascript was generated by mint/buildtypes.py\n"
    s += "// do not edit or check into source control\n"

    s += "var maxBuildType = %d;" % max(validBuildTypes.values())

    s += "var buildTypeNames = {"
    i = []
    for k, v in typeNames.items():
        i.append("    '%d':  '%s'" % (k, v,))
    s += ", ".join(i)
    s += "};"

    s += "var buildTypeNamesShort = {"
    i = []
    for k, v in typeNamesShort.items():
        i.append("    '%d':  '%s'" % (k, v,))
    s += ", ".join(i)
    s += "};"

    s += "var buildTypeNamesMarketing = {"
    i = []
    for k, v in typeNamesMarketing.items():
        i.append("    '%d':  '%s'" % (k, v,))
    s += ", ".join(i)
    s += "};"

    for k, v in validBuildTypes.items():
        s += "%s = %d;\n" % (k, v)
    return s

if __name__ == "__main__": #pragma: no cover
    if len(sys.argv) > 1 and sys.argv[1] == "--genjs":
        print codegen()
        sys.exit(0)
    else:
        sys.exit(1)



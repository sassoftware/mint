#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

import sys

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
}

TYPES = validBuildTypes.values()

# add all the defined image types directly to the module so that the standard
# approach of "buildtypes.IMAGE_TYPE" will result in the expected enum
sys.modules[__name__].__dict__.update(validBuildTypes)

deprecatedBuildTypes = {
    'QEMU_IMAGE' : RAW_HD_IMAGE
    }

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
    XEN_DOMU:   "Xen Virtual Appliance",
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
    LIVE_ISO:           "Demo CD/DVD (Live CD/DVD)",
    TARBALL:            "Compressed Tar File",
    VIRTUAL_PC_IMAGE:   "Microsoft (R) VHD Virtual Appliance",
    XEN_OVA:            "Citrix XenServer (TM) Appliance",
    VIRTUAL_IRON:       "Virtual Iron Virtual Appliance",
    PARALLELS:          "Parallels Virtual Appliance",
    AMI:                "Amazon Machine Image",
    UPDATE_ISO:         "Update CD/DVD",
    APPLIANCE_ISO:      "Appliance Installable ISO",
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
    VIRTUAL_PC_IMAGE:   "Virtual Server",
    XEN_OVA:            "Citrix XenServer (TM)",
    VIRTUAL_IRON:       "Virtual Iron",
    PARALLELS:          "Parallels",
    AMI:                "AMI",
    UPDATE_ISO:         "Update CD/DVD",
    APPLIANCE_ISO:      "Appliance Inst",
}

typeNamesMarketing = {
    NETBOOT_IMAGE:      "Netboot Image",
    INSTALLABLE_ISO:    "Installable CD/DVD",
    RAW_FS_IMAGE:       "Mountable Filesystem",
    STUB_IMAGE:         "Stub Image",
    RAW_HD_IMAGE:       "Parallels, QEMU (Raw Hard Disk)",
    VMWARE_IMAGE:       "VMware (R) Virtual Appliance",
    VMWARE_ESX_IMAGE:   "VMware (R) ESX Server Virtual Appliance",
    LIVE_ISO:           "Demo CD/DVD (Live CD/DVD)",
    TARBALL:            "TAR File",
    VIRTUAL_PC_IMAGE:   "Microsoft (R) VHD Virtual Server",
    XEN_OVA:            "Citrix XenServer (TM) Appliance",
    VIRTUAL_IRON:       "Virtual Iron Virtual Appliance",
    PARALLELS:          "Parallels Virtual Appliance",
    AMI:                "Amazon Machine Image",
    UPDATE_ISO:         "Update CD/DVD",
    APPLIANCE_ISO:      "Appliance Installable ISO",

    # flavor flags here
    XEN_DOMU:           "Xen DomU",
    APPLIANCE:          "Appliance",
}

buildTypeExtra = {
    APPLIANCE_ISO:      "This build type will not work without using "
                        "a version of anaconda-templates based on "
                        "rPath Linux 2.",
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



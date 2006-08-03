#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

import sys

validBuildTypes = {
    'BOOTABLE_IMAGE'   : 0,
    'INSTALLABLE_ISO'  : 1,
    'STUB_IMAGE'       : 2,
    'RAW_FS_IMAGE'     : 3,
    'NETBOOT_IMAGE'    : 4,
    'TARBALL'          : 5,
    'LIVE_ISO'         : 6,
    'RAW_HD_IMAGE'     : 7,
    'VMWARE_IMAGE'     : 8,
    }

TYPES = validBuildTypes.values()

# add all the defined image types directly to the module so that the standard
# approach of "buildtypes.IMAGE_TYPE" will result in the expected enum
sys.modules[__name__].__dict__.update(validBuildTypes)

deprecatedBuildTypes = {
    'QEMU_IMAGE' : RAW_HD_IMAGE
    }


#BOOTABLE_IMAGE Should never get stored in the DB and therefore doesn't need a name

# NOTA BENE. If you want to put in special characters (e.g. a copyright or
# registered trademark) in typeNames{,Short,Marketing}, please use the 
# equivalent ISO-LATIN-1 escape (e.g. \xae for registered trademark).

typeNames = {
    NETBOOT_IMAGE:      "Netboot Image",
    INSTALLABLE_ISO:    "Installable CD/DVD",
    RAW_FS_IMAGE:       "Raw Filesystem Image",
    STUB_IMAGE:         "Stub Image",
    RAW_HD_IMAGE:       "Raw Hard Disk Image",
    VMWARE_IMAGE:       "VMware\xae Player Image",
    LIVE_ISO:           "Demo CD/DVD (Live CD/DVD)",
    TARBALL:            "Compressed Tar File"
}

typeNamesShort = {
    NETBOOT_IMAGE:      "Netboot",
    INSTALLABLE_ISO:    "Inst CD/DVD",
    RAW_FS_IMAGE:       "Raw FS",
    STUB_IMAGE:         "Stub",
    RAW_HD_IMAGE:       "HDD",
    VMWARE_IMAGE:       "VMware\xae",
    LIVE_ISO:           "Demo CD/DVD",
    TARBALL:            "Tar"
}

typeNamesMarketing = {
    NETBOOT_IMAGE:      "Netboot Image",
    INSTALLABLE_ISO:    "Installable CD/DVD",
    RAW_FS_IMAGE:       "Mountable Filesystem",
    STUB_IMAGE:         "Stub Image",
    RAW_HD_IMAGE:       "Parallels, QEMU (Raw Hard Disk)",
    VMWARE_IMAGE:       "VMware\xae",
    LIVE_ISO:           "Demo CD/DVD (Live CD/DVD)",
    TARBALL:            "TAR File"
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
    return s


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--genjs":
        print codegen()
        sys.exit(0)
    else:
        sys.exit(1)



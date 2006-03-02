#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

import sys

validImageTypes = {
    'BOOTABLE_IMAGE'   : 0,
    'INSTALLABLE_ISO'  : 1,
    'STUB_IMAGE'       : 2,
    'LIVE_CF_IMAGE'    : 3,
    'NETBOOT_IMAGE'    : 4,
    'GROUP_TROVE_COOK' : 5,
    'LIVE_ISO'         : 6,
    'RAW_HD_IMAGE'     : 7,
    'VMWARE_IMAGE'     : 8,
    }

TYPES = validImageTypes.values()

# add all the defined image types directly to the module so that the standard
# approach of "releasetypes.IMAGE_TYPE" will result in the expected enum
sys.modules[__name__].__dict__.update(validImageTypes)

#BOOTABLE_IMAGE Should never get stored in the DB and therefore doesn't need a name
typeNames = {
    NETBOOT_IMAGE:      "Netboot Image",
    INSTALLABLE_ISO:    "Installable CD",
    LIVE_CF_IMAGE:      "Live CF Image",
    STUB_IMAGE:         "Stub Image (for testing)",
    RAW_HD_IMAGE:       "Raw Hard Disk Image",
    VMWARE_IMAGE:       "VMware Player Image",
    LIVE_ISO:           "Live CD",
}

typeNamesShort = {
    NETBOOT_IMAGE:      "Netboot",
    INSTALLABLE_ISO:    "Inst CD",
    LIVE_CF_IMAGE:      "Live CF",
    STUB_IMAGE:         "Stub",
    RAW_HD_IMAGE:       "HDD",
    VMWARE_IMAGE:       "VMware",
    LIVE_ISO:           "Live CD",
}

# code generator run by make to generate javascript constants
# should only be run by the makefile in mint/web/content/javascript
if __name__ == "__main__":
    if sys.argv[1] == "--genjs":
        print "// this Javascript was generated by mint/releasestypes.py"
        print "// do not edit or check into source control"

        print "var releaseImageTypeNames = { "
        i = []
        for k, v in typeNames.items():
            i.append("    '%d':  '%s'" % (k, v,))
        print ",\n".join(i)
        print "};"

        print "var releaseImageTypeNamesShort = { "
        i = []
        for k, v in typeNamesShort.items():
            i.append("    '%d':  '%s'" % (k, v,))
        print ",\n".join(i)
        print "};"

        sys.exit(0)
    else:
        sys.exit(1)



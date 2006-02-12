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
    'QEMU_IMAGE'       : 7,
    'VMWARE_IMAGE'     : 8
    }

TYPES = validImageTypes.values()

# add all the defined image types directly to the module so that the standard
# approach of "releasetypes.IMAGE_TYPE" will result in the expected enum
sys.modules[__name__].__dict__.update(validImageTypes)

#BOOTABLE_IMAGE Should never get stored in the DB and therefore doesn't need a name
typeNames = {
    NETBOOT_IMAGE:      "Netboot Image",
    INSTALLABLE_ISO:    "Installable ISO",
    LIVE_CF_IMAGE:      "Live CF Image",
    STUB_IMAGE:         "Stub Image (for testing)",
    QEMU_IMAGE:         "Bootable QEMU image",
    VMWARE_IMAGE:         "Bootable VMware Player image",
    LIVE_ISO:           "Live ISO",
}

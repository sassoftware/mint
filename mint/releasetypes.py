#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

BOOTABLE_IMAGE, INSTALLABLE_ISO, STUB_IMAGE, LIVE_CF_IMAGE, NETBOOT_IMAGE, GROUP_TROVE_COOK, LIVE_ISO, QEMU_IMAGE = range(0, 8)
TYPES = range(0, 8)

#This array contains the imageTypes that are to be displayed on the release creation page
visibleImageTypes = [ INSTALLABLE_ISO, QEMU_IMAGE ]

#BOOTABLE_IMAGE Should never get stored in the DB and therefore doesn't need a name
typeNames = {
    NETBOOT_IMAGE:      "Netboot Image",
    INSTALLABLE_ISO:    "Installable ISO",
    LIVE_CF_IMAGE:      "Live CF Image",
    STUB_IMAGE:         "Stub Image (for testing)",
    QEMU_IMAGE:         "Bootable Qemu image",
    LIVE_ISO:           "Live ISO",
}

#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

TYPES = range(0, 9)
BOOTABLE_IMAGE, INSTALLABLE_ISO, STUB_IMAGE, LIVE_CF_IMAGE, NETBOOT_IMAGE, GROUP_TROVE_COOK, LIVE_ISO, QEMU_IMAGE, VMWARE_IMAGE = TYPES


#This array contains the imageTypes that are to be displayed on the release creation page
visibleImageTypes = ( INSTALLABLE_ISO, ) # , QEMU_IMAGE, VMWARE_IMAGE )

#BOOTABLE_IMAGE Should never get stored in the DB and therefore doesn't need a name
typeNames = {
    NETBOOT_IMAGE:      "Netboot Image",
    INSTALLABLE_ISO:    "Installable ISO",
    LIVE_CF_IMAGE:      "Live CF Image",
    STUB_IMAGE:         "Stub Image (for testing)",
    QEMU_IMAGE:         "Bootable Qemu image",
    VMWARE_IMAGE:         "Bootable VMWare Player image",
    LIVE_ISO:           "Live ISO",
}

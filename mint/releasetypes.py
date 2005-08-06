#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

LIVE_ISO, INSTALLABLE_ISO, LIVE_CF_IMAGE, STUB_IMAGE, NETBOOT_IMAGE = range(0, 5)
TYPES = range(0, 5)

typeNames = {
    NETBOOT_IMAGE:      "Netboot Image",
    LIVE_ISO:           "Live ISO",
    INSTALLABLE_ISO:    "Installable ISO",
    LIVE_CF_IMAGE:      "Live CF Image",
    STUB_IMAGE:         "Stub Image (for testing)",
}

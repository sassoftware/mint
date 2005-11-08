#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

LIVE_ISO, INSTALLABLE_ISO, LIVE_CF_IMAGE, STUB_IMAGE, NETBOOT_IMAGE, GROUP_TROVE_COOK = range(0, 6)
TYPES = range(0, 6)

typeNames = {
    NETBOOT_IMAGE:      "Netboot Image",
    LIVE_ISO:           "Live ISO",
    INSTALLABLE_ISO:    "Installable ISO",
    LIVE_CF_IMAGE:      "Live CF Image",
    STUB_IMAGE:         "Stub Image (for testing)",
}

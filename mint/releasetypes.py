#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

LIVE_ISO, INSTALLABLE_ISO, LIVE_CF_IMAGE, STUB_IMAGE = range(0, 4)
TYPES = range(0, 4)

typeNames = {
    LIVE_ISO:           "Live ISO",
    INSTALLABLE_ISO:    "Installable ISO",
    LIVE_CF_IMAGE:      "Live CF Image [stub]",
    STUB_IMAGE:         "Stub Image (for testing)",
}

#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

import sys

communityTypes = {
    'VMWARE_VAM'           : 0
    }

TYPES = communityTypes.values()

# add all the defined image types directly to the module so that the standard
# approach of "communitytypes.URL_TYPE" will result in the expected enum
sys.modules[__name__].__dict__.update(communityTypes)


#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

import sys

validCookTypes = {
    'DUMMY_COOK'    : 0,
    'GROUP_BUILDER' : 1
    }

TYPES = validCookTypes.values()

# add all the defined image types directly to the module so that the standard
# approach of "cooktypes.COOK_TYPE" will result in the expected enum
sys.modules[__name__].__dict__.update(validCookTypes)

typeNames = {
    DUMMY_COOK    : 'Dummy Cook',
    GROUP_BUILDER : 'Group Builder',
    }

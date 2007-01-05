#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

import sys

urlTypes = {
    'LOCAL'           : 0,
    'AMAZONS3'        : 1,
    'AMAZONS3TORRENT' : 2,
    'GENERICMIRROR'   : 999
    }

TYPES = urlTypes.values()

# add all the defined image types directly to the module so that the standard
# approach of "urltypes.URL_TYPE" will result in the expected enum
sys.modules[__name__].__dict__.update(urlTypes)

typeNames = {
    LOCAL           : 'Locally Stored',
    AMAZONS3        : 'Amazon S3',
    AMAZONS3TORRENT : 'Amazon S3 BitTorrent',
    GENERICMIRROR   : 'Generic Mirror Site'
    }

displayNames = {
    LOCAL           : 'Download',
    AMAZONS3        : 'Download',
    AMAZONS3TORRENT : 'BitTorrent',
    GENERICMIRROR   : 'Download'
}

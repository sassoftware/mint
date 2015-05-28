#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
    AMAZONS3TORRENT : 'Download (BitTorrent)',
    GENERICMIRROR   : 'Download'
}

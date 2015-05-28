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


import os

from xobj import xobj

if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'mint.django_rest.settings'

class LinkElement(object):
    _xobj = xobj.XObjMetadata(
	        attributes = {
				           'href' : str,
				         },
	    )

    def __init__(self, uri, value=None):
        self.href = "%(uri)s" % vars()
        self._xobj.text = value
        
    def __repr__(self):
        return unicode(self._value)
        
class IDElement(object):
    _xobj = xobj.XObjMetadata(
	        attributes = {
				           'id' : str,
				         },
	    )

    def __init__(self, uri):
        self.id = "%(uri)s" % vars()
        
    def __repr__(self):
        return unicode(self.id)  

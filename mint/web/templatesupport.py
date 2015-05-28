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


"""A handful of functions useful inside kid templates."""

import time
from mint.helperfuncs import getArchFromFlavor, getProjectText

import conary
from conary.conaryclient.cmdline import parseTroveSpec
from conary import versions

def downloadTracker(cfg, url):
    if cfg.googleAnalyticsTracker:
        return {"onclick": "javascript:urchinTracker('%s');" % url}
    else:
        return {}

def injectVersion(version):
    parts = version.split('/')
    parts[-1] = str(time.time()) + ':' + parts[-1]
    return '/'.join(parts)

def dictToJS(d):
    """Returns dict as a str with keys converted to str as well"""
    return str(dict([(str(x[0]), x[1]) for x in d.iteritems()]))

def shortTroveSpec(spec):
    n, v, f = parseTroveSpec(spec)
    try:
        v = versions.VersionFromString(v)
    except conary.errors.ParseError: # we got a frozen version string
        v = versions.ThawVersion(v)
    return "%s=%s (%s)" % (n, str(v.trailingRevision()), getArchFromFlavor(f))

def projectText():
    return getProjectText()

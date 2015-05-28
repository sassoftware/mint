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


import json
from conary.lib.http import connection
from conary.lib.http import opener
from conary.lib.http.http_error import ResponseError


class Connection(connection.Connection):
    connectTimeout = 5


class Opener(opener.URLOpener):
    connectionFactory = Connection
    connectAttempts = 1


def process(repos, cfg, commitList, srcMap, pkgMap, grpMap, argv, otherArgs):
    url = argv[0]
    body = json.dumps(commitList)
    try:
        response = Opener().open(url, body,
                headers=[('Content-Length', 'application/json')])
        response.read()
    except ResponseError as err:
        if err.errcode != 204:
            raise
    return 0

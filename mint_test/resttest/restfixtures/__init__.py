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

from mint_test import fixtures

class _RestFixture(object):
    def __init__(self, test):
        self.test = test

    def load(self, mintCfg):
        self.test.mintCfg = mintCfg
        self._load()
        return mintCfg, {}

    def __getattr__(self, key):
        return getattr(self.test, key)

    def _load(self):
        raise NotImplementedError

class EmptyFixture(_RestFixture):
    name = 'empty'
    def _load(self):
        self.createUser('admin', admin=True)


fixtures = {}
for val in sys.modules[__name__].__dict__.values():
    if (val != _RestFixture and isinstance(val, type) 
            and issubclass(val, _RestFixture)):
        fixtures[val.name] = val

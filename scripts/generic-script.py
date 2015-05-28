#!/usr/bin/python
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
import sys

maybeRoot = os.path.dirname(os.path.dirname(__file__))
if os.path.exists(os.path.join(maybeRoot, 'mint', 'lib')):
    sys.path.insert(0, maybeRoot)

from mint.scripts import some_module
sys.exit(some_module.Script().run())

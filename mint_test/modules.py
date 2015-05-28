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


from testrunner.loadmodules import PythonModule

modules = [
PythonModule('conary', setup='make'),
PythonModule('mcp'),
PythonModule('xobj', pythonPath='py/xobj'),
PythonModule('rpath-xmllib',
      test='',
      setup='make'),
PythonModule('rpath-product-definition', 
      test='from rpath_proddef import api1 as proddef',
      setup='make'),
PythonModule('rpath-xmllib', 
      test='from rpath_xmllib import api1 as xmllib',
      setup='make'),
PythonModule('catalog-service', reposName='catalog/catalog-service',
      test='import catalogService'),
PythonModule('mint', setup='make'),
PythonModule('dnspython', test='import dns', shouldClone=False),
PythonModule('python-pgsql', test='import pgsql', shouldClone=False),
PythonModule('restlib'),
PythonModule('rpath-storage', test='import rpath_storage'),
PythonModule('rpath-job', test='import rpath_job'),
PythonModule('crest', test='import crest'),
PythonModule('smartform', pythonPath= 'py/smartform', test='import smartform'),
PythonModule('rmake', test='import rmake'),
]

testModules = [
PythonModule('conary-test', setup='make', test=''), # cannot test because
                                              # it creates some recursion
                                              # problems.
PythonModule('mcp-test', modulePath='mcp/test', test='import mcp_test.mcp_helper'),
PythonModule('mint-test', modulePath='mint/mint_test', test=''),
]

flexModules = [
PythonModule('flexlibs', setup='make', test=''),
PythonModule('catalog-client', setup='make', reposName='catalog/catalog-client',
             test=''),
]

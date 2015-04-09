from testrunner.loadmodules import PythonModule

modules = [
PythonModule('conary', setup='make'),
PythonModule('mcp'),
PythonModule('xobj', pythonPath='py/xobj'),
PythonModule('raa', test='import raa', reposName='raa'),
PythonModule('raaplugins', environName='RAA_PLUGINS_PATH', modulePath='raa/raaplugins'),
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
PythonModule('rpath-capsule-indexer', test='import rpath_capsule_indexer',
      pythonPath='rpath_capsule_indexer'),
PythonModule('rpath-storage', test='import rpath_storage'),
PythonModule('rpath-job', test='import rpath_job'),
PythonModule('repodata', test='import repodata'),
PythonModule('crest', test='import crest'),
PythonModule('smartform', pythonPath= 'py/smartform', test='import smartform'),
PythonModule('rmake', test='import rmake'),
]

testModules = [
PythonModule('conary-test', setup='make', test=''), # cannot test because
                                              # it creates some recursion
                                              # problems.
PythonModule('mcp-test', modulePath='mcp/test', test='import mcp_test.mcp_helper'),
PythonModule('raa-test', test='import raa', reposName='raa-test'),
PythonModule('mint-test', modulePath='mint/mint_test', test=''),
]

flexModules = [
PythonModule('flexlibs', setup='make', test=''),
PythonModule('catalog-client', setup='make', reposName='catalog/catalog-client',
             test=''),
]

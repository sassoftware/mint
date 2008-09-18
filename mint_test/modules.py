from testrunner.loadmodules import PythonModule

modules = [
PythonModule('conary', setup='make'),
PythonModule('mcp'),
PythonModule('jobslave'),
PythonModule('raa', test='import raa', reposName='raa-2.1'),
PythonModule('raaplugins', environName='RAA_PLUGINS_PATH'),
PythonModule('rpath-xmllib',
      environName='XMLLIB_PATH',
      test='',
      setup='make'),
PythonModule('rpath-product-definition', 
      environName='PRODUCT_DEFINITION_PATH',
      test='from rpath_common import proddef,xmllib',
      setup='make'),
PythonModule('catalog-service', reposName='catalog/catalog-service',
      test='import catalogService'),
PythonModule('package-creator/package-creator-service', 
             test='import pcreator'),
PythonModule('mint', modulePath='..'),
PythonModule('conary-test', setup='make', test=''), # cannot test because 
                                              # it creates some recursion
                                              # problems.
PythonModule('raa-test', test='import raa', reposName='raa-test-2.1'),
PythonModule('dnspython', test='import dns', shouldClone=False),
PythonModule('python-pgsql', test='import pgsql', shouldClone=False),
PythonModule('conary-factory-test', test='import factory_test'), 
PythonModule('mcp-test', modulePath='mcp/test', test='import mcp_helper'),
PythonModule('mint-test', modulePath='mint/test', test='')
]

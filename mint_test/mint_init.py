import os
import sys
import __builtin__
# needs to be in a separate file from testsuite.py or else it gets run
# twice - once as __main__, once as testsuite.py

def setup_paths():
    conaryPath      = os.getenv('CONARY_PATH',      os.path.realpath('../../conary'))
    conaryTestPath  = os.getenv('CONARY_TEST_PATH', os.path.realpath(os.path.join(conaryPath, '..', 'conary-test')))
    mcpPath         = os.getenv('MCP_PATH',         os.path.realpath('../../mcp'))
    mcpTestPath     = os.getenv('MCP_TEST_PATH',    os.path.realpath(os.path.join(mcpPath, 'test')))
    jobslavePath    = os.getenv('JOB_SLAVE_PATH',   os.path.realpath('../../jobslave'))
    mintPath        = os.getenv('MINT_PATH',        os.path.realpath('..'))
    mintTestPath    = os.getenv('MINT_TEST_PATH',   os.path.realpath('.'))
    raaPath         = os.getenv('RAA_PATH',         os.path.realpath('../../raa-2.1'))
    raaTestPath     = os.getenv('RAA_TEST_PATH',    os.path.realpath('../../raa-test-2.1'))
    raaPluginsPath  = os.getenv('RAA_PLUGINS_PATH', os.path.realpath('../raaplugins'))
    proddefPath     = os.getenv('PRODUCT_DEFINITION_PATH',     os.path.realpath('../../rpath-product-definition'))
    coveragePath    = os.getenv('COVERAGE_PATH',    os.path.realpath('../../utils'))
    catalogServicePath = os.getenv('CATALOG_SERVICE_PATH', os.path.realpath('../../catalog-service'))
    restlibPath = os.getenv('RESTLIB_PATH', os.path.realpath('../../restlib'))

    #Package creator
    packageCreatorPath = os.getenv('PACKAGE_CREATOR_SERVICE_PATH',    os.path.realpath('../../package-creator-service'))
    if not os.path.exists(packageCreatorPath):
        print >> sys.stderr, "Please set PACKAGE_CREATOR_SERVICE_PATH"
        sys.exit(1)
    conaryFactoryTestPath = os.getenv('CONARY_FACTORY_TEST_PATH',    os.path.realpath('../../conary-factory-test'))
    if not os.path.exists(conaryFactoryTestPath):
        print >> sys.stderr, "Please set CONARY_FACTORY_TEST_PATH"
        sys.exit(1)

    sys.path = [os.path.realpath(x) for x in (mintPath, mintTestPath,
        mcpPath, mcpTestPath, jobslavePath, conaryPath, conaryTestPath,
        raaPath, raaTestPath, raaPluginsPath, proddefPath, coveragePath,
        packageCreatorPath, conaryFactoryTestPath, catalogServicePath,
        restlibPath)] \
                + sys.path
    os.environ.update(dict(CONARY_PATH=conaryPath,
        RESTLIB_PATH=restlibPath,
        CONARY_TEST_PATH=conaryTestPath,
        MCP_PATH=mcpPath, MCP_TEST_PATH=mcpTestPath,
        MINT_PATH=mintPath, MINT_TEST_PATH=mintTestPath,
        JOB_SLAVE_PATH=jobslavePath, RAA_PATH=raaPath,
        RAA_TEST_PATH=raaTestPath, RAA_PLUGINS_PATH=raaPluginsPath,
        PRODUCT_DEFINITION_PATH=proddefPath,
        COVERAGE_PATH=coveragePath, 
        PACKAGE_CREATOR_SERVICE_PATH=packageCreatorPath,
        CONARY_FACTORY_TEST_PATH=conaryFactoryTestPath,
        CATALOG_SERVICE_PATH=catalogServicePath,
        PYTHONPATH=(':'.join(sys.path))))

_initialized = False
def initialize():
    global _initialized
    if _initialized:
        return
    setup_paths()
    _initialized = True

    from testrunner import testhelp
    from testrunner import resources

    resources.testPath = testPath = testhelp.getTestPath()
    resources.mintArchivePath = archivePath = testPath + '/' + "mint_archive"

    # Set conary's archivePath as well
    conaryTestPath = os.environ['CONARY_TEST_PATH']
    resources.archivePath = conaryTestPath + '/archive'
    resources.conaryDir = conaryDir = os.environ['CONARY_PATH']

    # if we're running with COVERAGE_DIR, we'll start covering now
    from conary.lib import coveragehook

    # ensure shim client errors on types that can't be sent over xml-rpc
    from mint import shimclient
    shimclient._ShimMethod.__call__ = filteredCall

def enforceBuiltin(result):
    failure = False
    if isinstance(result, (list, tuple)):
        for item in result:
            failure = failure or enforceBuiltin(item)
    elif isinstance(result, dict):
        for item in result.values():
            failure = failure or enforceBuiltin(item)
    failure =  failure or (result.__class__.__name__ \
                           not in __builtin__.__dict__)
    return failure


def filteredCall(self, *args, **kwargs):
    from mint.client import VERSION_STRING
    args = [VERSION_STRING] + list(args)
    isException, result = self._server.callWrapper(self._name,
                                                   self._authToken, args)

    if not isException:
        if enforceBuiltin(result):
            # if the return type appears to be correct, check the types
            # some items get cast to look like built-ins for str()
            # an extremely common example is sql result rows.
            raise AssertionError('XML cannot marshall return value: %s '
                                 'for method %s' % (str(result), self._name))
        return result
    else:
        self.handleError(result)


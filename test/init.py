import os
# needs to be in a separate file from testsuite.py or else it gets run 
# twice - once as __main__, once as testsuite.py

from testrunner import loadmodules
import modules

_initialized = False
def initialize():
    global _initialized
    if _initialized:
        return
    _initialized = True
    loadmodules.loadModules(modules.modules, '../modules')

    from testrunner import testhelp
    from testrunner import resources

    resources.testPath = testPath = testhelp.getTestPath()
    resources.mintArchivePath = archivePath = testPath + '/' + "archive"

    # Set conary's archivePath as well
    conaryTestPath = os.environ['CONARY_TEST_PATH']
    resources.archivePath = conaryTestPath + '/archive'
    resources.conaryDir = conaryDir = os.environ['CONARY_PATH']

    # if we're running with COVERAGE_DIR, we'll start covering now
    from conary.lib import coveragehook



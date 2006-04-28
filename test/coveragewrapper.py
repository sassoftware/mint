#!/usr/bin/python
import imp
import os.path
import sys
import re

conaryPath = os.environ.get('CONARY_PATH', None)
if not conaryPath:
    print >>sys.stderr, 'please set CONARY_PATH'
    sys.exit(1)

if conaryPath not in sys.path:
    sys.path.insert(0, conaryPath)

from conary.lib import util

class CoverageWrapper(object):
    def __init__(self, executable, dataPath, annotatePath):
        self._executable = executable
        self._dataPath = dataPath
        self._annotatePath = annotatePath
        os.environ['COVERAGE_DIR'] = dataPath # yuck
        util.mkdirChain(dataPath)

    def reset(self):
        if os.path.exists(self._dataPath):
            util.rmtree(self._dataPath)
        if os.path.exists(self._annotatePath):
            util.rmtree(self._annotatePath)

    def execute(self, testProgram):
        util.execute('python2.4 %s' % testProgram)

    def displayReport(self, files, displayMissingLines=False):
        assert(not displayMissingLines)
        util.execute('python2.4 %s -r %s' % (self._executable, ' '.join(files)))

    def writeAnnotatedFiles(self, files):
        annotatePath = self._annotatePath
        util.execute('python2.4 %s -d %s -a %s' % (self._executable,
                                                   self._annotatePath,
                                                   ' '.join(files)))

        if annotatePath.startswith(os.getcwd() + '/'):
            annotatePath = '.' + annotatePath[len(os.getcwd()):]
        print
        print '*** %s file(s) annotated in %s' % (len(files), annotatePath)

    def iterAnalysis(self, paths):
        coverage = imp.load_source('coverage', self._executable)
        coverage = coverage.the_coverage
        coverage.cache = self._dataPath
        coverage.restore()
        for path in paths:
            _, statements, excluded, missing, missingFmted = coverage.analysis2(path)
            total = len(statements)
            covered = total - len(missing)
            if covered < total:
                percentCovered = 100.0 * covered / total
            else:
                percentCovered = 100.0
            yield path, total, covered, percentCovered, missingFmted

    def getTotals(self, paths):
        totalLines = 0
        totalCovered = 0
        for _, pathLines, coveredLines, _, _ in self.iterAnalysis(paths):
            totalLines += pathLines
            totalCovered += coveredLines

        if totalCovered != totalLines:
            percentCovered = 100.0 * totalCovered / totalLines
        else:
            percentCovered = 100.0
        return totalLines, totalCovered, percentCovered

def getEnviron():
    conaryPath = os.environ.get('CONARY_PATH', None)
    coveragePath = os.environ.get('COVERAGE_TOOL', None)
    mintPath = os.path.abspath("../") + "/"
    print "mintPath: ", mintPath
    policyPath = os.environ.get('CONARY_POLICY_PATH', '/usr/lib/conary/policy')
    if not coveragePath:
        print "Please set COVERAGE_TOOL"
        sys.exit(1)
    elif not policyPath:
        print "Please set CONARY_POLICY_PATH"
        sys.exit(1)
    return {'conary'   : conaryPath,
            'policy'   : policyPath,
            'coverage' : coveragePath,
            'mint'     : mintPath}

def getFilesToAnnotate(baseDirs=[], filesToFind=[]):
    notExists = set(filesToFind)
    addAll = not filesToFind

    allFiles = set(x for x in filesToFind if os.path.exists(x))
    filesToFind = [ x for x in filesToFind if x not in allFiles ]

    posFilters = [r'\.py$']
    negFilters = ['sqlite', 'test', 'scripts']
    

    for baseDir in baseDirs:
        for root, dirs, pathList in os.walk(baseDir):
            for path in filesToFind:
                if os.path.exists(os.path.join(root, path)):
                    allFiles.add(os.path.join(root, path))
                    notExists.discard(path)

            if addAll:
                for path in pathList:
                    fullPath = '/'.join((root, path))
                    found = False
                    for posFilter in posFilters:
                        if re.search(posFilter, fullPath):
                            found = True
                            break
                    if not found:
                        continue
                    foundNeg = False
                    for negFilter in negFilters:
                        if re.search(negFilter, fullPath):
                            foundNeg = True
                            break
                    if foundNeg:
                        continue
                    else:
                        allFiles.add(fullPath)
    return allFiles, notExists

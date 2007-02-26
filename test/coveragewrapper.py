#!/usr/bin/python
import imp
import os.path
import sys
import re
import types

conaryPath = os.environ.get('CONARY_PATH', None)
if not conaryPath:
    print >>sys.stderr, 'please set CONARY_PATH'
    sys.exit(1)

if conaryPath not in sys.path:
    sys.path.insert(0, conaryPath)

from conary.lib import util


class CoverageWrapper(object):
    def __init__(self, coveragePath, dataPath, annotatePath):
        self._coveragePath = coveragePath
        self._executable = coveragePath + '/coverage.py'
        self._dataPath = dataPath
        self._annotatePath = annotatePath
        os.environ['COVERAGE_DIR'] = dataPath # yuck
        util.mkdirChain(dataPath)
        self.coverage = None

    def reset(self):
        if os.path.exists(self._dataPath):
            util.rmtree(self._dataPath)
        if os.path.exists(self._annotatePath):
            util.rmtree(self._annotatePath)

    def execute(self, testProgram):
        os.system('python2.4 %s' % testProgram) # we don't care about the 
                                                # exit code here.

    def getCoverage(self):
        if self.coverage:
            return self.coverage
        coverage = imp.load_source('coverage', self._executable)
        coverage = coverage.the_coverage
        coverage.cacheDir = self._dataPath
        coverage.restoreDir()
        return coverage

    def displayReport(self, files, displayMissingLines=False):
        assert(not displayMissingLines)
        missingSortKey = lambda x: (len(x[2]), len(x[1]))
        sortFn = lambda a,b: cmp(missingSortKey(a), missingSortKey(b))
        coverage = self.getCoverage()
        coverage.report(files, show_missing=False)

    def writeAnnotatedFiles(self, files):
        if os.path.exists(self._annotatePath):
            util.rmtree(self._annotatePath)
        annotatePath = self._annotatePath
        coverage = self.getCoverage()
        coverage.annotate(files, self._annotatePath)
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
    coveragePath = os.environ.get('COVERAGE_PATH', None)
    policyPath = os.environ.get('CONARY_POLICY_PATH', '/usr/lib/conary/policy')
    mintPath = os.environ.get('MINT_PATH', None)
    if not coveragePath:
        print "Please set COVERAGE_PATH to the dir in which coverage.py is located"
        sys.exit(1)
    elif not policyPath:
        print "Please set CONARY_POLICY_PATH"
        sys.exit(1)
    elif not mintPath:
        print "Please set MINT_PATH"
        sys.exit(1)
    return {'conary'   : conaryPath,
            'policy'   : policyPath,
            'coverage' : coveragePath,
            'mint'     : mintPath}

def _isPythonFile(fullPath, posFilters=[r'\.py$'], negFilters=['sqlite']):
    found = False
    for posFilter in posFilters:
        if re.search(posFilter, fullPath):
            found = True
            break
    if not found:
        return False

    foundNeg = False
    for negFilter in negFilters:
        if re.search(negFilter, fullPath):
            foundNeg = True
            break
    if foundNeg:
        return False
    return True

def getFilesToAnnotate(baseDirs=[], filesToFind=[], exclude=[]):
    notExists = set(filesToFind)
    addAll = not filesToFind

    allFiles = set(x for x in filesToFind if os.path.exists(x))
    filesToFind = [ x for x in filesToFind if x not in allFiles ]

    if not isinstance(exclude, list):
        exclude = [ exclude ]
    negFilters = ['sqlite'] + exclude

    baseDirs = [ os.path.realpath(x) for x in baseDirs ]
    for baseDir in baseDirs:
        for root, dirs, pathList in os.walk(baseDir):
            for path in filesToFind:
                if os.path.exists(os.path.join(root, path)):
                    allFiles.add(os.path.join(root, path))
                    notExists.discard(path)

            if addAll:
                for path in pathList:
                    fullPath = '/'.join((root, path))
                    if _isPythonFile(fullPath, negFilters=negFilters):
                        allFiles.add(fullPath)
    return list(allFiles), notExists

def getFilesToAnnotateByPatch(baseDirs=[], patchLevel=2):
    files = {}
    curDir = os.getcwd()
    patchReaderPath = os.environ['COVERAGE_PATH'] + '/patchreader'

    try:
        for baseDir in baseDirs:
            os.chdir(baseDir)
            output = os.popen('hg diff | %s -p%s' % (patchReaderPath, patchLevel))
            while True:
                fileName = output.readline().strip()
                if not fileName:
                    break
                lines = [ int(x) for x in output.readline().split()]
                files[fileName] = lines
    finally:
        os.chdir(curDir)

    for fullPath in files.keys():
        if not _isPythonFile(fullPath):
            del files[fullPath]
    return files, []



def getFilesToAnnotateByPatch(baseDir, patchInput, filesDict=None):
    if filesDict is None:
        files = {}
    else:
        files = filesDict
    cwd = os.getcwd()
    try:
        os.chdir(baseDir)
        patchReaderPath = os.environ['COVERAGE_PATH'] + '/patchreader'
        stdin, output = os.popen2('%s -p' % (patchReaderPath,), 'w')
        stdin.write(patchInput.read())
        stdin.flush()
        stdin.close()
    finally:
        os.chdir(cwd)
    while True:
        fileName = output.readline().strip()
        if not fileName:
            break
        lines = [ int(x) for x in output.readline().split()]
        files[fileName] = lines

def getFilesToAnnotateFromPatchFile(path, baseDirs=[]):
    return _getFilesToAnnotateFromFn(baseDirs, open, path)
    
def getFilesToAnnotateFromHg(baseDirs=[]):
    return _getFilesToAnnotateFromFn(baseDirs, os.popen, "hg diff")

def getFilesToAnnotateFromHgOut(baseDirs=[]):
    return _getFilesToAnnotateFromFn(baseDirs, os.popen, "hg diff -r $(hg parents -r $(hg outgoing | awk '/changeset/ { print $2}' | head -1  | cut -d: -f1)  | awk '/changeset/ { print $2}' | cut -d: -f1)")

def _getFilesToAnnotateFromFn(baseDirs, fn, *args, **kw):
    files = {}
    curDir = os.getcwd()
    try:
        for baseDir in baseDirs:
            os.chdir(baseDir)
            output = fn(*args, **kw)
            getFilesToAnnotateByPatch(baseDir, output, files)
    finally:
        os.chdir(curDir)

    for fullPath in files.keys():
        if not _isPythonFile(fullPath):
            del files[fullPath]
    
    return files, []


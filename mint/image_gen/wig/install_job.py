#
# Copyright (c) 2011 rPath, Inc.
#

"""
Provides a self-contained API for accessing files and data from the group from
which an image is being built.
"""

import itertools
import logging
import os
from collections import namedtuple
from conary import callbacks
from conary import files as cny_files
from conary import trove as cny_trove
from conary.lib import util as cny_util
from lxml import builder
from xobj import xobj

from mint.image_gen.util import FileWithProgress

log = logging.getLogger(__name__)

RTIS_PACKAGES = set(('rTIS:msi', 'rTIS.NET:msi', 'rPathTools:msi'))
CRITICAL_PACKAGES = set(RTIS_PACKAGES)


class InstallJob(object):

    def __init__(self, conaryClient, troveList):
        self.conaryClient = conaryClient
        self.troveList = troveList
        self.fileMap = None

    def load(self):
        if self.fileMap is not None:
            return

        # Use update code to get a complete list of included troves.
        job = self.conaryClient.newUpdateJob()
        self.conaryClient.prepareUpdateJob(job,
                [(name, (None, None), (version, flavor), True)
                    for (name, version, flavor) in self.troveList],
                checkPathConflicts=False)
        jobList = [ x for x in itertools.chain(*job.jobs) ]
        orderedTups = [ (x[0], x[2][0], x[2][1]) for x in jobList ]
        names = set(x[0] for x in orderedTups)

        # Fetch a changeset with files but no contents so that individual files
        # can be selected.
        repos = self.conaryClient.getRepos()
        changeSet = repos.createChangeSet(jobList, recurse=False,
                withFiles=True, withFileContents=False)

        # Collect a file mapping with relevant trove information for each.
        fileMap = {}
        for trvCs in changeSet.iterNewTroveList():
            for fileTup in trvCs.getNewFileList():
                fileTup = FileTuple._make(fileTup)
                fileData = self._getFileData(changeSet, trvCs, fileTup)
                if fileData is not None:
                    fileMap.setdefault(type(fileData), []).append(fileData)
            else:
                troveTup = trvCs.getNewNameVersionFlavor()
                if ('%s:msi' % troveTup[0] in names or
                    troveTup[0].startswith('group-')):

                    fileMap.setdefault(MSIData, []).append(
                        PackageData(troveTup))

        for dataType, fileList in fileMap.iteritems():
            if dataType is MSIData:
                fileList.sort(key=lambda d: orderedTups.index(d.troveTuple))
            else:
                fileList.sort(key=lambda d: d.fileTup.fileId)
        self.fileMap = fileMap

    def _getFileData(self, changeSet, trvCs, fileTup):
        pathId, path, fileId, fileVer = fileTup
        fileStream = changeSet.getFileChange(None, fileId)
        if not cny_files.frozenFileHasContents(fileStream):
            # No contents
            return None
        if '.' not in path:
            # No extension on the filename
            return None
        name = os.path.basename(path)
        extension = name.split('.')[-1].lower()

        fileInfo = cny_files.ThawFile(fileStream, pathId)
        flags = fileInfo.flags
        if (flags.isEncapsulatedContent()
                and not flags.isCapsuleOverride()):
            # Encapsulated files also have no contents
            return None

        size = fileInfo.contents.size()
        sha1 = fileInfo.contents.sha1()
        if pathId == cny_trove.CAPSULE_PATHID:
            # Capsule file
            if extension == 'msi':
                # MSI package to be installed
                return MSIData(self.conaryClient, fileTup, size,
                        sha1=sha1,
                        troveTuple=trvCs.getNewNameVersionFlavor(),
                        msiInfo=trvCs.getTroveInfo().capsule.msi,
                        )
            elif extension == 'wim':
                # Base platform WIM
                return WIMData(self.conaryClient, fileTup, size,
                        wimInfo=trvCs.getTroveInfo().capsule.wim,
                        )
        else:
            # Regular file
            if path.lower() == '/platform-isokit.zip':
                # WinPE and associated ISO generation tools
                return RegularFileData(self.conaryClient, fileTup, size)
            elif extension in ('reg', 'exe'):
                # Legacy rTIS bootstrap, used for bootable image types.
                return RegularFileData(self.conaryClient, fileTup, size)

    def getFilesByClass(self, fileClass):
        if not issubclass(fileClass, RegularFileData):
            raise TypeError("Expected a subclass of RegularFileData")
        return list(self.fileMap.get(fileClass, ()))

    def getRegularFilesByName(self, path):
        out = []
        for fileData in self.getFilesByClass(RegularFileData):
            if fileData.fileTup.path == path:
                out.append(fileData)
        return out


FileTuple = namedtuple('FileTuple', 'pathId path fileId fileVer')


class RegularFileData(object):

    def __init__(self, conaryClient, fileTup, size):
        self.conaryClient = conaryClient
        self.fileTup = fileTup
        self.size = size

    def getContents(self, progressCallback=None):
        class FetchCallback(callbacks.ChangesetCallback):
            def downloadingFileContents(cbself, transferred, _):
                if not progressCallback:
                    return
                if self.size:
                    percent = 50.0 * transferred / self.size
                else:
                    percent = 0.0
                progressCallback(percent)
        def sendCallback(transferred):
            if not progressCallback:
                return
            if self.size:
                percent = 50.0 + 50.0 * transferred / self.size
            else:
                percent = 50.0
            progressCallback(percent)
        log.info("Retrieving file %s, %d bytes", self.fileTup.path, self.size)
        repos = self.conaryClient.getRepos()
        fobj = repos.getFileContents(
                [(self.fileTup.fileId, self.fileTup.fileVer)],
                callback=FetchCallback(),
                )[0].get()
        wrapper = FileWithProgress(fobj, sendCallback)
        return wrapper

    def storeContents(self, outF, progressCallback=None):
        # The initial download constitutes the first 50% of progress
        def initialCallback(percent):
            if progressCallback:
                progressCallback(percent / 2)
        fobj = self.getContents(progressCallback=initialCallback)
        # Uncompressing the contents makes up the other 50%
        def uncompressCallback(byteCount, rate):
            if not progressCallback:
                return
            if self.size:
                percent = 50.0 + 50.0 * byteCount / self.size
            else:
                percent = 50.0
            progressCallback(percent)
        return cny_util.copyfileobj(fobj, outF, callback=uncompressCallback)


class MSIData(RegularFileData):

    def __init__(self, conaryClient, fileTup, size, sha1, troveTuple, msiInfo):
        RegularFileData.__init__(self, conaryClient, fileTup, size)
        self.sha1 = sha1
        self.troveTuple = troveTuple
        self.msiInfo = msiInfo
        self.fileName = os.path.basename(self.fileTup.path)

    def getProductCode(self):
        return self.msiInfo.productCode()

    def getPackageXML(self, seqNum):
        E = builder.ElementMaker()
        manifest = '%s=%s[%s]' % (self.troveTuple[0],
                self.troveTuple[1].freeze(), self.troveTuple[2])

        msi = self.msiInfo
        return E.package(
                E.type('msi'),
                E.sequence(str(seqNum)),
                E.logFile('install.log'),
                E.operation('install'),
                E.productCode(msi.productCode()),
                E.productName(msi.name()),
                E.productVersion(msi.version()),
                E.file(self.fileName),
                E.manifestEntry(manifest),
                E.previousManifestEntry(''),
                E.critical(str(self.isCritical()).lower()),
                )

    def isCritical(self):
        return self.troveTuple[0] in CRITICAL_PACKAGES

    def isRtis(self):
        return self.troveTuple[0] in RTIS_PACKAGES


class PackageData(RegularFileData):
    def __init__(self, troveTuple):
        RegularFileData.__init__(self, None, None, 0)
        self.troveTuple = troveTuple
        self.sha1 = None
        self.fileName = None

    def getPackageXML(self, seqNum):
        E = builder.ElementMaker()
        manifest = '%s=%s[%s]' % (self.troveTuple[0],
                self.troveTuple[1].freeze(), self.troveTuple[2])

        return E.package(
            E.type('package'),
            E.sequence(str(seqNum)),
            E.logFile('install.log'),
            E.operation('install'),
            E.manifestEntry(manifest),
            E.previousManifestEntry(''),
            E.critical(str(self.isCritical()).lower()),
        )

    def isCritical(self):
        return self.troveTuple[0] in CRITICAL_PACKAGES

    def isRtis(self):
        return self.troveTuple[0] in RTIS_PACKAGES


class WIMData(RegularFileData):

    def __init__(self, conaryClient, fileTup, size, wimInfo):
        RegularFileData.__init__(self, conaryClient, fileTup, size)
        self.wimInfo = wimInfo
        self.version, self.arch = self._getPlatVerAndArch(wimInfo)

    @staticmethod
    def _getPlatVerAndArch(wimInfo):
        wimXml = xobj.parse(wimInfo.infoXml())

        # Find the 'main' image in the WIM
        imageIndex = str(wimInfo.volumeIndex())
        images = wimXml.WIM.IMAGE
        if not isinstance(images, list):
            images = [images]
        for image in images:
            if image.INDEX == imageIndex:
                break
        else:
            raise RuntimeError("Image index %s was not found." % (imageIndex,))

        arch = image.WINDOWS.ARCH
        if arch == '0':
            archPart = 'x86'
        elif arch == '9':
            archPart = 'x64'

        version = [int(x) for x in wimInfo.version().split('.')][:2]
        if version >= [6, 1]:
            versionPart = '2008R2'
        elif version >= [6, 0]:
            versionPart = '2008'
        else:
            versionPart = '2003'

        return versionPart, archPart

    def getVmwareOS(self):
        if self.version == '2003':
            vmwareOS = 'winNetStandard'
        else:
            vmwareOS = 'windows7srv'
        if self.arch == 'x64':
            vmwareOS += '-64'
        return vmwareOS

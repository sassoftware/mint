#
# Copyright (c) 2011 rPath, Inc.
#

import os
import time
import zipfile
from conary.lib import util
from lxml import builder
from lxml import etree
from mint.image_gen import constants as iconst
from mint.image_gen.wig import generator as genmod
from mint.image_gen.wig import install_job
from mint.lib.subprocutil import logCall


class IsoGenerator(genmod.ImageGenerator):

    def run(self):
        self.setConfiguration()
        self.runJob()
        self.upload()
        self.sendStatus(iconst.WIG_JOB_DONE, "Image built")

    def setStepList(self):
        self.stepList = [
                iconst.WIG_JOB_QUEUED,
                iconst.WIG_JOB_FETCHING,
                iconst.WIG_JOB_SENDING,
                iconst.WIG_JOB_RUNNING,
                iconst.WIG_JOB_UPLOADING,
                iconst.WIG_JOB_DONE,
                ]

    def runJob(self):
        self.sendStatus(iconst.WIG_JOB_FETCHING, "Retrieving image contents")
        self.installJob.load()

        isoDir = os.path.join(self.workDir, 'iso')
        updateDir = os.path.join(isoDir, 'rPath/DeploymentUpdate')

        # Gather a list of files to fetch so that we fail fast if something is
        # missing and so that the progress reporting has an accurate total.
        files = self.installJob.getFilesByClass(install_job.WIMData)
        if not files:
            raise RuntimeError("A WIM must be present in order to build "
                    "Windows images")
        self.wimData = files[0]

        files = self.installJob.getRegularFilesByName('/platform-isokit.zip')
        if not files:
            raise RuntimeError("A platform-isokit.zip must be present in "
                    "order to build Installable ISO images")
        self.isokitData = files[0]

        msis = self.installJob.getFilesByClass(install_job.MSIData)
        self.fileCount = 2 + len(msis)
        self.filesTransferred = 0

        # Download isokit first and extract the basic ISO directory structure.
        self.unpackIsokit()

        # Download WIM directly into the output directory.
        progressCallback = self._startFileProgress(self.wimData)
        outF = open(isoDir + '/sources/image.wim', 'wb')
        self.wimData.storeContents(outF, progressCallback)
        outF.close()

        # Download and store MSIs.
        packageLists, rtisPath = self._downloadPackages(msis, updateDir)

        self._writeServicing(packageLists, updateDir)
        self._writeScripts(isoDir, rtisPath)

        # Build ISO
        last = [time.time()]
        self.sendStatus(iconst.WIG_JOB_RUNNING, "Creating ISO", "0%")
        def _mkisofs_callback(pipe, line):
            if pipe == 'stderr' and '% done' in line:
                if time.time() - last[0] < 2:
                    return
                last[0] = time.time()
                percent = line.split('% done')[0].strip()
                percent = int(float(percent))
                self.sendStatus(iconst.WIG_JOB_RUNNING,
                        "Creating ISO", "%d%%" % percent)
        logCall(['mkisofs',
            '-udf',
            '-b', 'boot/etfsboot.com',
            '-no-emul-boot',
            '-o', self.workDir + '/output.iso',
            isoDir,
            ], callback=_mkisofs_callback)

    def _downloadPackages(self, msis, updateDir):
        criticalPackageList = []
        packageList = []
        rtisPath = None
        for msiData in msis:
            name = os.path.basename(msiData.fileTup.path)

            # Append package to either the critical or regular package list.
            if msiData.isCritical():
                targetList = criticalPackageList
            else:
                targetList = packageList
            pkgXml = msiData.getPackageXML(seqNum=len(targetList))
            targetList.append(pkgXml)

            # Store MSI directly to the output directory.
            relPath = os.path.join(msiData.getProductCode(), name)
            destPath = os.path.join(updateDir, relPath)
            util.mkdirChain(os.path.dirname(destPath))

            outF = open(destPath, 'wb')
            progressCallback = self._startFileProgress(msiData)
            msiData.storeContents(outF, progressCallback)
            outF.close()

            # Remember the path to rTIS so it can be pre-installed on first
            # boot.
            if msiData.troveTuple[0].lower() == 'rtis:msi':
                rtisPath = relPath

        packageLists = criticalPackageList, packageList
        return packageLists, rtisPath

    def _writeServicing(self, packageLists, updateDir):
        E = builder.ElementMaker()
        criticalPackageList, packageList = packageLists

        sysModel = 'install %s=%s\n' % (
            self.troveTup.name, str(self.troveTup.version))
        pollingManifest = '%s=%s[%s]\n' % (
            self.troveTup.name, self.troveTup.version.freeze(),
            str(self.troveTup.flavor))

        jobs = []
        if criticalPackageList:
            jobs.append(E.updateJob(
                    E.sequence('0'),
                    E.logFile('install.log'),
                    E.packages(*criticalPackageList),
                    ))
        if packageList:
            jobs.append(E.updateJob(
                    E.sequence('1'),
                    E.logFile('install.log'),
                    E.packages(*packageList),
                    ))
        root = E.update(
            E.logFile('install.log'),
            E.systemModel(sysModel),
            E.pollingManifest(pollingManifest),
            E.updateJobs(*jobs)
            )
        doc = etree.tostring(root)
        fobj = open(updateDir + '/servicing.xml', 'w')
        fobj.write(doc)
        fobj.close()

    def _writeScripts(self, isoDir, rtisPath):
        osName = self.wimData.version
        if osName.startswith('2003'):
            # XXX FIXME
            raise NotImplementedError
        else:
            # 2008, 2008R2
            winFirstBootPath = 'C:\\Windows\\Setup\\Scripts\\SetupComplete.cmd'
            winUpdateDir = 'C:\\ProgramData\\rPath\\Updates\\DeploymentUpdate'

        fobj = open(isoDir + '/rPath/copymsi.bat', 'w')
        fobj.write('xcopy /e /y '
                '%%binpath%%\\DeploymentUpdate %(winUpdateDir)s\\\r\n'
                % dict(winUpdateDir=winUpdateDir))
        fobj.write('md %(winFirstBootDir)s\r\n'
                % dict(winFirstBootDir=winFirstBootPath.rsplit('\\', 1)[0]))
        fobj.write('copy /y %%binpath%%\\firstboot.bat '
                '"%(winFirstBootPath)s"\r\n'
                % dict(winFirstBootPath=winFirstBootPath))
        fobj.close()

        # Write first-boot script to bootstrap rTIS.
        fobj = open(isoDir + '/rPath/firstboot.bat', 'w')
        if rtisPath:
            rtisPath = rtisPath.replace('/', '\\')
            fobj.write('msiexec /i '
                    '"%(winUpdateDir)s\\%(rtisPath)s" '
                    '/quiet /norestart '
                    '/l*v "%(winUpdateDir)s\\%(rtisLog)s" '
                    '\r\n' % dict(
                        winUpdateDir=winUpdateDir,
                        rtisPath=rtisPath,
                        rtisLog=rtisPath.rsplit('.', 1)[0] + '.Install.log',
                        ))
            fobj.write('net start "rPath Tools Installer Servce"\n')
        fobj.close()

    def unpackIsokit(self):
        ikData = self.isokitData
        ikPath = os.path.join(self.workDir, 'isokit.zip')
        outF = open(ikPath, 'wb')
        progressCallback = self._startFileProgress(ikData)
        ikData.storeContents(outF, progressCallback)
        outF.close()

        zf = zipfile.ZipFile(ikPath, 'r')
        for name in zf.namelist():
            norm = os.path.normpath(name)
            if not norm.startswith('isoKit/'):
                raise RuntimeError("Invalid isokit.zip")
            path = os.path.join(self.workDir, norm)
            if name.endswith('/'):
                util.mkdirChain(path)
            else:
                util.mkdirChain(os.path.dirname(path))
                f_in = zf.open(name)
                f_out = open(path, 'wb')
                util.copyfileobj(f_in, f_out)
                f_in.close()
                f_out.close()
        zf.close()

        # Move directory structures into place
        isoDir = os.path.join(self.workDir, 'iso')
        ikDir = os.path.join(self.workDir, 'isoKit')
        osName = self.wimData.version
        os.rename(ikDir + '/ISO', isoDir)
        os.rename(ikDir + '/os/' + osName, isoDir + '/rPath/os')

    def upload(self):
        kind = 'iso'
        title = "Installable CD/DVD (ISO)"
        outputName = '%s.%s' % (self.jobData['baseFileName'], kind)
        fObj = open(self.workDir + '/output.iso', 'rb')
        fileSize = os.fstat(fObj.fileno()).st_size
        self.postResults([(fObj, fileSize, outputName, title)])



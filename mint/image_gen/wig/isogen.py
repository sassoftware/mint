#
# Copyright (c) 2011 rPath, Inc.
#

import os
import time
import zipfile
from conary.lib import util
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
        progressCallback = self._startFileProgress('image.wim')
        outF = open(isoDir + '/sources/image.wim', 'wb')
        self.wimData.storeContents(outF, progressCallback)
        outF.close()

        # Download and store MSIs.
        rtisPath = self._downloadPackages(msis, updateDir)
        self._writeServicing(msis, updateDir)
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
            '-allow-limited-size',
            '-no-emul-boot',
            '-o', self.workDir + '/output.iso',
            isoDir,
            ], callback=_mkisofs_callback)

    def _downloadPackages(self, msis, updateDir):
        rtisPath = None
        for msiData in msis:
            name = os.path.basename(msiData.fileTup.path)

            # Store MSI directly to the output directory.
            relPath = os.path.join(msiData.getProductCode(), name)
            destPath = os.path.join(updateDir, relPath)
            util.mkdirChain(os.path.dirname(destPath))

            outF = open(destPath, 'wb')
            progressCallback = self._startFileProgress(name)
            msiData.storeContents(outF, progressCallback)
            outF.close()

            # Remember the path to rTIS so it can be pre-installed on first
            # boot.
            if msiData.isRtis():
                rtisPath = relPath
        return rtisPath

    def _writeServicing(self, msis, updateDir):
        doc = self._getServicingXml(msis)
        fobj = open(updateDir + '/servicing.xml', 'w')
        fobj.write(doc)
        fobj.close()

    def _writeScripts(self, isoDir, rtisPath):
        # Write deployment script to copy the MSIs and first-boot script onto
        # the target system.
        self._writeRpathrc(isoDir)
        copymsi = open(isoDir + '/rPath/copymsi.bat', 'w')

        osName = self.wimData.version
        m = {}
        if osName.startswith('2003'):
            # 2003 requires another level of indirection
            m['winFirstBootDir'] = 'C:\\Windows\\Temp'
            progData = 'C:\\Documents and Settings\\All Users\\Application Data'
            cmdlines = open(isoDir + '/rPath/cmdlines.txt', 'w')
            cmdlines.write(
                '[Commands]\r\n'
                '"%(winFirstBootDir)s\\SetupComplete.cmd"\r\n'
                % m)
            cmdlines.close()

            m['cmdDir'] = 'C:\\sysprep\\i386\\$OEM$'
            copymsi.write(
                'md "%(cmdDir)s"\r\n'
                'copy /y "%%binpath%%\\cmdlines.txt" '
                    '"%(cmdDir)s\\cmdlines.txt"\r\n'
                % m)
        else:
            # 2008, 2008R2
            m['winFirstBootDir'] = 'C:\\Windows\\Setup\\Scripts'
            progData = 'C:\\ProgramData'
        m['rpathDir'] = progData + '\\rPath'
        m['winUpdateDir'] = m['rpathDir'] + '\\Updates\\DeploymentUpdate'

        copymsi.write(
                'xcopy /e /y '
                    '"%%binpath%%\\DeploymentUpdate" "%(winUpdateDir)s"\\\r\n'
                'copy /y "%%binpath%%\\rpathrc" "%(rpathDir)s\\rpathrc"\r\n'
                'md "%(winFirstBootDir)s"\r\n'
                'copy /y "%%binpath%%\\firstboot.bat" '
                    '"%(winFirstBootDir)s\\SetupComplete.cmd"\r\n'
                % m)
        copymsi.close()

        # Write first-boot script to bootstrap rTIS.
        firstboot = open(isoDir + '/rPath/firstboot.bat', 'w')
        if rtisPath:
            m['rtisPath'] = rtisPath.replace('/', '\\')
            m['rtisLog'] = m['rtisPath'].rsplit('.', 1)[0] + '.Install.log'
            if osName.startswith('2003'):
                # 2003 reboots at the end of OOBE gui setup automatically, leave the /norestart param in.
                firstboot.write(
                    'schtasks.exe /create /tn rTISOnStart /tr "net start \\\"rPath Tools Installer Service\\\"" /sc ONSTART /ru system\r\n'
                    'msiexec /i '
                        '"%(winUpdateDir)s\\%(rtisPath)s" /qn /norestart '
                        '/l*v "%(winUpdateDir)s\\%(rtisLog)s"\r\n'
                    % m)
            else:
                # 2008 + does not restart at the end of OOBE gui setup.
                firstboot.write(
                    'schtasks.exe /create /tn rTISOnStart /tr "net start \\\"rPath Tools Installer Service\\\"" /sc ONSTART /ru system\r\n'
                    'msiexec /i '
                        '"%(winUpdateDir)s\\%(rtisPath)s" /qn /forcerestart '
                        '/l*v "%(winUpdateDir)s\\%(rtisLog)s"\r\n'
                    % m)
        firstboot.close()

    def _writeRpathrc(self, isoDir):
        if not self.inventoryNode:
            return
        rpathrc = file(os.path.join(isoDir, "rPath", "rpathrc"), "w")
        tmpl = "%s %s\r\n"
        rpathrc.write(tmpl % ("directMethod", "[]"))
        rpathrc.write(tmpl % ("directMethod", self.inventoryNode))
        rpathrc.close()

    def unpackIsokit(self):
        ikData = self.isokitData
        ikPath = os.path.join(self.workDir, 'isokit.zip')
        outF = open(ikPath, 'wb')
        progressCallback = self._startFileProgress('isokit.zip')
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



#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#
import os
import subprocess
import sys

from conary.lib import util


def call(*cmds):
    print >> sys.stderr, " ".join(cmds)
    sys.stderr.flush()
    subprocess.call(cmds)


class Image(object):
    def run(self, cmd, *args):
        try:
            func = self.__getattribute__(cmd)
        except AttributeError:
            raise RuntimeError, "Invalid anaconda templates manifest image command: %s" % (cmd)

        if len(args) == 3:
            mode = args.pop(-1)
        else:
            mode = 0644

        output = args[1]
        util.mkdirChain(os.path.dirname(output))
        retcode = func(*args)
        os.chmod(output, mode)
        return retcode

    def cpiogz(self, inputDir, output):
        cwd = os.getcwd()
        try:
            os.chdir(inputDir)
            cpioCmd = ['cpio', '-o']
            gzip = ['gzip']

            outputFile = file(output, "w")
            files = subprocess.Popen(['find', '.', '-print', '-depth'],
                                     stdout = subprocess.PIPE)
            gzip = subprocess.Popen(['gzip'], stdin = subprocess.PIPE,
                                    stdout = outputFile)
            cpio = subprocess.Popen(['cpio', '-o'],
                                    stdin = files.stdout,
                                    stdout = gzip.stdin)

            cpio.communicate()
            outputFile.close()
        finally:
            try:
                os.chdir(cwd)
            except:
                pass

    def mkisofs(self, inputDir, output):
        cmd = ['mkisofs', '-quiet', '-o', output,
            '-b', 'isolinux/isolinux.bin',
            '-c', 'isolinux/boot.cat',
            '-no-emul-boot',
            '-boot-load-size', '4',
            '-boot-info-table',
            '-R', '-J', '-T',
            '-V', 'rPath Linux',
            inputDir]
        call(cmd)

    def mkcramfs(self, inputDir, output):
        cmd = ['mkcramfs', inputDir, output]
        call(cmd)

    def mkdosfs(self, inputDir, output):
        call('dd', 'if=/dev/zero', 'of=%s' % output, 'bs=1M', 'count=8')
        call('/sbin/mkdosfs', output)

        files = [os.path.join(inputDir, x) for x in os.listdir(inputDir)]
        cmds = ['mcopy', '-i', output] + files + ['::']
        call(*cmds)

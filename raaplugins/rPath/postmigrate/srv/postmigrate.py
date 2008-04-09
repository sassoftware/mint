#
# Copyright (C) 2006-2007 rPath, Inc.
# All rights reserved.
#

import os
import pwd
import stat
import re
import tarfile
import tempfile

from raa.modules.raasrvplugin import rAASrvPlugin
from raaplugins.backup import lib
from raa.lib import mount

magicLabel = "RBA_MIGRATE_3TO4"
markerFile = os.path.join(os.path.sep, 'tmp', 'rbuilder_migration')

def getPartitions(filter = "sd", source = "/proc/partitions"):
    f = open(source, "r")

    partitions = []
    partLine = re.compile(".*(%s\w+\d+)" % filter)

    for x in f.readlines():
        match = partLine.match(x.strip())
        if match:
            partitions.append(match.groups()[0])

    f.close()
    return [os.path.join(os.path.sep, 'dev', x) for x in partitions]

def getLabel(device):
    try:
        p = os.popen('e2label %s 2>/dev/null' % device)
        return p.read().strip()
    except:
        return ''

def getBackupScripts(backupDir = None):
    if not backupDir:
        backupDir = os.path.join(os.path.sep,'etc', 'raa', 'backup.d')
    backupfiles = [os.path.join(backupDir, x) for x in os.listdir(backupDir)]
    return [x for x in backupfiles if os.stat(x)[stat.ST_MODE] & 0100]

def touchMarkerFile(markerFile = markerFile):
    open(markerFile, 'w').write('')
    os.chown(markerFile, *pwd.getpwnam('raa-web')[2:4])

class rBuilderMigration(rAASrvPlugin):
    def getBackups(self, schedId, execId):
        # return value is tuple of (devicePresent, numBackups)
        # devicePresent is a boolean
        # numBackups is an integer
        backups = []
        partitions = getPartitions()
        labels = dict([(getLabel(x), x) for x in partitions])
        device = labels.get(magicLabel, '')
        scripts = getBackupScripts()
        if device:
            tmpDir = tempfile.mkdtemp()
            try:
                mount.mount(device, tmpDir)
                try:
                    allBackups = [x for x in os.listdir(tmpDir) \
                            if x.startswith('backup')]
                    backups = []
                    for backup in allBackups:
                        try:
                            tar = tarfile.TarFile(os.path.join(tmpDir, backup))
                            metadata = tar.extractfile('metadata_v1').read()
                            if lib.isValid(scripts, metadata,
                                    raiseError = False):
                                backups.append(backup)
                        finally:
                            if tar:
                                tar.close()
                finally:
                    mount.umount_point(tmpDir)
            finally:
                if tmpDir: 
                    os.rmdir(tmpDir)
        return bool(device), backups

    def doRestore(self, schedId, execId, filename):
        def reportCallback(message):
            self.reportMessage(execId, message)
        jobData = {}
        try:
            jobData.update({
                    'filename': filename,
                    'settings': {
                        'backup.file_format': 'backup-%Y%m%d-%H%M-%Z.tgz',
                        'backup.local_storage': '/var/lib/raa/backups/',
                        'backup.tmp_dir': '/tmp',
                        'backup.disabled_types': ['URL'],
                        'backup.file_list_dir': '/etc/raa/backup.d'},
                    'plugin_properties': {
                        'enableBackupSchedule': False,
                        'numBackups': 1,
                        'locationType': 'LABEL',
                        'locationPassword': '',
                        'locationUsername': '',
                        'locationHost': '',
                        'locationLabel': magicLabel,
                        'locationPath': '/'},
                    'debug': False
                    })
            touchMarkerFile()
            lib.doRestore(jobData, reportCallback)
        except Exception, e:
            res = {'errors' : 'Error occured during backup: %s' % str(e)}
        else:
            res = {'message' : 'Completed successfully.'}
        res.update({'schedId' : schedId})
        return res

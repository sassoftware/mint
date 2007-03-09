#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
from mint import config
from mint import database
from mint import projects
from mint import scriptlibrary
from mint import server
from mint import pkgindex

from conary import conaryclient
from conary import conarycfg
from conary import dbstore
from conary import versions
from conary.repository import repository

import os
import sys
import time

hiddenLabels = [
    versions.Label('conary.rpath.com@rpl:rpl1'),
    versions.Label('conary.rpath.com@ravenous:bugblatterbeast')
]

class PackageIndexer(scriptlibrary.SingletonScript):
    db = None
    cfgPath = config.RBUILDER_CONFIG

    def __init__(self, aLockPath = scriptlibrary.DEFAULT_LOCKPATH):
        self.cfg = config.MintConfig()
        self.cfg.read(self.cfgPath)
        if self.logFileName:
            self.logPath = os.path.join(self.cfg.dataPath, 'logs', self.logFileName)
        # throwaway server to update database tables if needed (RBL-1434)
        self._server = server.MintServer(self.cfg)

        scriptlibrary.SingletonScript.__init__(self, aLockPath)

    def cleanup(self):
        if self.db:
            self.db.close()


class UpdatePackageIndex(PackageIndexer):
    logFileName = 'package-index.log'

    def action(self):
        self.log.info("Updating package index")

        self.db = dbstore.connect(self.cfg.dbPath, driver = self.cfg.dbDriver)
        self.db.loadSchema()
        cu = self.db.cursor()

        try:
            cu.execute('SELECT COUNT(*) FROM PackageIndexMark')
            if not cu.fetchone()[0]:
                cu.execute('INSERT INTO PackageIndexMark VALUES(0)')
            cu.execute("SELECT IFNULL(MAX(timestamp), 0) FROM Commits")
            newMark = cu.fetchone()[0]

            # Clear out Package index if the timestamp in PackageIndexMark == 0
            cu.execute("""DELETE FROM PackageIndex WHERE
                              (SELECT mark FROM PackageIndexMark) = 0""")

            cu.execute("""SELECT Projects.projectId, troveName, version,
                                 timestamp
                              FROM Commits
                              LEFT JOIN Projects
                                  ON Commits.projectId=Projects.projectId
                              WHERE (troveName NOT LIKE '%:%' OR troveName LIKE '%:source')
                              AND hidden=0 AND disabled=0
                              AND timestamp >=
                                  (SELECT mark FROM PackageIndexMark)""")

            res = cu.fetchall()
            numPkgs = len(res) - 1
            if numPkgs > 0:
                self.log.info("Indexing %d packages" % numPkgs)
            else:
                self.log.info("Package index is up to date")
            packageDict = {}
            labelMap = {}
            for projectId, troveName, verStr, timeStamp in res:
                troveEntry = packageDict.setdefault(troveName, {})
                version = versions.VersionFromString(verStr)
                label = str(version.branch().label())
                versionList = troveEntry.setdefault(label, [])

                version.resetTimeStamps(timeStamp)
                versionList.append(version)
                labelMap[label] = projectId

            packageIndex = []
            for troveName in packageDict:
                for label in packageDict[troveName]:
                    packageIndex.append((labelMap[label], troveName,
                                         max(packageDict[troveName][label])))

            inserts = []
            updates = []
            for projectId, troveName, version in packageIndex:
                cu.execute("""SELECT pkgId, version FROM PackageIndex
                                  WHERE projectId=? AND name=?""",
                           projectId, troveName)

                res = [x[0] for x in cu.fetchall() if \
                       versions.VersionFromString(x[1]).branch().label() == \
                       version.branch().label()]

                label = version.branch().label()
                serverName = label.getHost()
                branchName = label.getNamespace() + ":" + label.getLabel()

                if not res:
                    inserts.append((projectId, troveName, str(version), serverName,
                        branchName, troveName.endswith(':source')))
                else:
                    pkgId = res[0]
                    updates.append((projectId, troveName, str(version), serverName,
                        branchName, troveName.endswith(':source'), pkgId))

            self.db.transaction()
            cu.executemany("""INSERT INTO PackageIndex
                              (projectId, name, version,
                               serverName, branchName, isSource)
                              VALUES (?, ?, ?, ?, ?, ?)""", inserts)
            cu.executemany("""UPDATE PackageIndex SET
                                  projectId=?, name=?, version=?,
                                  serverName=?, branchName=?, isSource=?
                                  WHERE pkgId=?""", updates)
            self.db.commit()

            cu.execute("UPDATE PackageIndexMark SET mark=?", newMark)
        except Exception, e:
            self.log.error("Error occured: %s" % str(e))
            self.db.rollback()
            exitcode = 1
            raise
        else:
            self.log.info("Completed successfully: %d" % len(inserts))
            exitcode = 0
            self.db.commit()
        return exitcode


class UpdatePackageIndexExternal(PackageIndexer):
    logFileName = 'package-index-external.log'

    def action(self):
        self.log.info("Updating package index")

        self.db = dbstore.connect(self.cfg.dbPath, driver = self.cfg.dbDriver)
        self.db.connect()
        self.db.loadSchema()
        cu = self.db.cursor()
        pkgIdx = pkgindex.PackageIndexTable(self.db)
        labelsTable = projects.LabelsTable(self.db, self.cfg)
        self.db.commit()

        cu = self.db.cursor()
        cu.execute("""SELECT projectId, %s
                         FROM Projects
                         WHERE external=1 AND hidden=0 AND disabled=0""" % \
                   database.concat(self.db, 'hostname', "'.'", 'domainname'))

        labels = {}
        projectIds = {}
        netclients = {}

        for r in cu.fetchall():
            projectId, hostname = r

            self.log.info("Retrieving labels from %s...", hostname)
            l, repMap, userMap = labelsTable.getLabelsForProject(projectId,
                overrideAuth = True, newUser = 'anonymous', newPass = 'anonymous')

            hostname = repMap.keys()[0]
            labels[hostname] = versions.Label(l.keys()[0])
            projectIds[hostname] = projectId

            ccfg = conarycfg.ConaryConfiguration()
            conarycfgFile = os.path.join(self.cfg.dataPath, 'conaryrc')
            if os.path.exists(conarycfgFile):
                ccfg.read(conarycfgFile)
            ccfg.root = ccfg.dbPath = ':memory:'
            ccfg.repositoryMap = repMap
            repos = conaryclient.ConaryClient(ccfg).getRepos()
            netclients[hostname] = repos

        rows = []
        for host in netclients.keys():
            self.log.info("Retrieving trove list from %s...", host)
            try:
                names = netclients[host].troveNamesOnServer(host)
                names = dict((x, None) for x in names if ':' not in x or x.endswith(':source'))
                troves = netclients[host].getAllTroveLeaves(host, names)

            except repository.errors.OpenError, e:
                self.log.warning("unable to access %s: %s", host, str(e))
                continue

            packageDict = {}
            labelMap = {}
            for pkg in troves:
                troveEntry = packageDict.setdefault(pkg, {})
                verList = troves[pkg].keys()
                for ver in verList:
                    label = ver.branch().label()
                    if label in hiddenLabels:
                        continue

                    versionList = troveEntry.setdefault(label, [])
                    versionList.append(ver)

            for troveName in packageDict:
                for label in packageDict[troveName]:
                    serverName = label.getHost()
                    branchName = label.getNamespace() + ":" + label.getLabel()

                    isSource = troveName.endswith(':source')
                    row = (projectIds[host], troveName, str(max(packageDict[troveName][label])),
                        serverName, branchName, isSource)
                    rows.append(row)

            self.log.info("Retrieved %d trove%s from %s.", len(rows), ((len(rows) != 1) and 's' or ''), host)

        self.log.info("Updating database...")
        updates = []
        inserts = []
        for row in rows:
            cu.execute("SELECT pkgId FROM PackageIndex WHERE projectId=? AND name=? AND version=?", *row[:3])
            r = cu.fetchone()
            if r:
                pkgId = r[0]
                updates.append((row[0], row[1], row[2], row[3], row[4], row[5], pkgId))
            else:
                inserts.append(row)

        st = time.time()
        self.db.transaction()
        cu.executemany("""
            UPDATE PackageIndex SET
                projectId=?, name=?, version=?,
                serverName=?, branchName=?, isSource=?
            WHERE pkgId=?""", updates)
        cu.executemany("""
            INSERT INTO PackageIndex
                (pkgId, projectId, name, version, serverName, branchName, isSource)
            VALUES (NULL, ?, ?, ?, ?, ?, ?)""", inserts)
        self.db.commit()
        self.log.info("Update complete: %.2fs" % (time.time() - st))
        return 0

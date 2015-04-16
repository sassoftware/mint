#
# Copyright (c) SAS Institute Inc.
#

import os
import string
import time

from mint import buildtypes
from mint.lib import database
from mint.lib import data as mintdata
from mint import helperfuncs
from mint import userlevels
from mint.mint_error import (ItemNotFound, DuplicateItem, DuplicateName,
        DuplicateShortname, DuplicateHostname, DuplicateLabel, LabelMissing,
        RepositoryAlreadyExists)

from conary import dbstore
from conary.lib import util

# functions to convert a repository name to a database-safe name string
transTables = {
    'sqlite':       string.maketrans("", ""),
    'mysql':        string.maketrans("-.:", "___"),
    'postgresql':   string.maketrans("-.:", "___").lower(),
    'pgpool':       string.maketrans("-.:", "___").lower(),
    'psycopg2':     string.maketrans("-.:", "___").lower(),
}

class ProjectsTable(database.KeyedTable):
    name = 'Projects'
    key = 'projectId'
    fields = ['projectId', 'creatorId', 'name', 'hostname', 'domainname',
        'namespace', 'projecturl', 'description', 'disabled', 'hidden',
        'external', 'isAppliance', 'timeCreated', 'timeModified',
        'commitEmail', 'backupExternal', 'shortname', 'prodtype', 'version',
        'fqdn', 'database']

    def __init__(self, db, cfg):
        self.cfg = cfg

        # XXX: This doesn't even begin to handle alternates; it's only
        # hanging around until it gets replaced with the new repo logic.
        defaultDriver = self.cfg.database[self.cfg.defaultDatabase][0]
        self.reposDB = getFactoryForRepos(defaultDriver)(cfg)

        database.DatabaseTable.__init__(self, db)

    def new(self, **kwargs):
        try:
            id = database.KeyedTable.new(self, **kwargs)
        except DuplicateItem:
            self.db.rollback()
            cu = self.db.cursor()
            cu.execute("SELECT projectId FROM Projects WHERE hostname=?", kwargs['hostname'])
            results = cu.fetchall()
            if len(results) > 0:
                raise DuplicateHostname()
            cu.execute("SELECT projectId FROM Projects WHERE shortname=?", kwargs['shortname'])
            results = cu.fetchall()
            if len(results) > 0:
                raise DuplicateShortname()
            cu.execute("SELECT projectId FROM Projects WHERE name=?", kwargs['name'])
            results = cu.fetchall()
            if len(results) > 0:
                raise DuplicateName()
        return id
    
    def deleteProject(self, projectId, projectFQDN, commit=True):
        try:
            # try deleteing the repository
            self.reposDB.delete(projectFQDN)

            for contentsDir in self.cfg.reposContentsDir.split():
                contentsDir = contentsDir % projectFQDN
                if os.path.isdir(contentsDir):
                    util.rmtree(contentsDir)

                # If the parent dir is empty, delete that too.
                # (e.g. /srv/rbuilder/repos/hostname.rbuilder.com)
                parentDir = os.path.dirname(os.path.normpath(contentsDir))
                if os.path.isdir(parentDir) and not os.listdir(parentDir):
                    try:
                        os.rmdir(parentDir)
                    except OSError:
                        pass
            
            # try removing the project
            cu = self.db.cursor()
            cu.execute("DELETE FROM Projects WHERE projectId=?", projectId)
        except:
            self.db.rollback()
            raise
        else:
            if commit:
                self.db.commit()

    def getProjectsList(self):
        cu = self.db.cursor()

        # audited for SQL injection.
        sql = """
            SELECT projectId, hidden, %s
            FROM Projects
            ORDER BY hostname
        """ % database.concat(self.db, "hostname", "' - '", "name")
        cu.execute(sql)

        results = cu.fetchall()
        return [(int(x[0]), x[1], x[2]) for x in results]

    def getProjectIdByFQDN(self, fqdn):
        cu = self.db.cursor()
        cu.execute("SELECT projectId FROM Projects WHERE fqdn = ?", fqdn)

        r = cu.fetchone()
        if not r:
            raise ItemNotFound
        else:
            return r[0]

    def getProjectIdByHostname(self, hostname):
        cu = self.db.cursor()

        cu.execute("SELECT projectId FROM Projects WHERE hostname=?", hostname)

        r = cu.fetchone()
        if not r:
            raise ItemNotFound
        else:
            return r[0]

    def getProjectIdsByMember(self, userId, filter = False):
        cu = self.db.cursor()
        # audited for sql injection. check sat.
        # We used to filter these results with another condition that if the
        # project was hidden, you had to be a userlevels.WRITER.  That has
        # been changed to allow normal users to browse hidden projects of
        # which they are a member.
        stmt = """SELECT ProjectUsers.projectId, level FROM ProjectUsers
                    LEFT JOIN Projects
                        ON Projects.projectId=ProjectUsers.projectId
                    WHERE ProjectUsers.userId=?"""
        if filter:
            stmt += " AND NOT hidden"
        cu.execute(stmt, userId)

        return [tuple(x) for x in cu.fetchall()]

    def getProjectDataByMember(self, userId, filter = False):
        cu = self.db.cursor()
        # We used to filter these results with another condition that if the
        # project was hidden, you had to be a userlevels.WRITER.  That has
        # been changed to allow normal users to browse hidden projects of
        # which they are a member.
        stmt = """
SELECT ep.*, grouped.level FROM (
SELECT allperms.project_id, MIN(allperms.level) AS level
FROM (
    -- Permissions from a project set
    SELECT qpt.project_id, CASE rpt.name
            WHEN 'ReadMembers' THEN 2
            WHEN 'ModMembers' THEN 0
            ELSE NULL
        END AS level
    FROM rbac_user_role rur
    JOIN rbac_permission rp
        ON rp.role_id = rur.role_id
    JOIN rbac_permission_type rpt
        ON rpt.permission_type_id = rp.permission_type_id
    JOIN querysets_projecttag qpt
        ON qpt.query_set_id = rp.queryset_id
    WHERE rur.user_id = :user_id
    AND rpt.name in ('ReadMembers', 'ModMembers')

    UNION ALL

    -- Permissions from a project stage set
    SELECT pbs.project_id, CASE rpt.name
            WHEN 'ReadMembers' THEN 2
            WHEN 'ModMembers' THEN 0
            ELSE NULL
        END AS level
    FROM rbac_user_role rur
    JOIN rbac_permission rp
        ON rp.role_id = rur.role_id
    JOIN rbac_permission_type rpt
        ON rpt.permission_type_id = rp.permission_type_id
    JOIN querysets_stagetag qst
        ON qst.query_set_id = rp.queryset_id
    JOIN project_branch_stage pbs
        ON pbs.stage_id = qst.stage_id
    WHERE rur.user_id = :user_id
    AND rpt.name in ('ReadMembers', 'ModMembers')

    UNION ALL

    -- Oldschool project membership
    SELECT projectid AS project_id, level
    FROM ProjectUsers pu
    WHERE userId = :user_id
) allperms
GROUP BY allperms.project_id
) grouped
JOIN Projects ep
    ON ep.projectId = grouped.project_id
"""
        cu.execute(stmt, dict(user_id=userId))
        ret = []
        for x in cu:
            level = x.pop('level')
            hasRequests = False
            if x['creatorId'] is None:
                del x['creatorId']
            ret.append((x, level, hasRequests))
        return ret

    @database.dbWriter
    def hide(self, cu, projectId):
        # Anonymous user is added/removed in server
        cu.execute("UPDATE Projects SET hidden=true, timeModified=? WHERE projectId=?", time.time(), projectId)
        cu.execute("DELETE FROM PackageIndex WHERE projectId=?", projectId)

    def unhide(self, projectId):
        # Anonymous user is added/removed in server
        cu = self.db.cursor()

        cu.execute("UPDATE Projects SET hidden=false, timeModified=? WHERE projectId=?", time.time(), projectId)
        self.db.commit()

    def isHidden(self, projectId):
        cu = self.db.cursor()
        cu.execute("SELECT COALESCE(hidden, 0) from Projects WHERE projectId=?", projectId)
        res = cu.fetchone()
        return res and res[0] or 0

    def get(self, *args, **kwargs):
        ret = database.KeyedTable.get(self, *args, **kwargs)
        ret['external'] = bool(ret['external'])
        return ret


class LabelsTable(database.KeyedTable):
    name = 'Labels'
    key = 'labelId'
    fields = ['labelId', 'projectId', 'label', 'url', 'authType', 'username',
        'password', 'entitlement']

    def __init__(self, db, cfg):
        database.DatabaseTable.__init__(self, db)
        self.cfg = cfg

    def _getAllLabelsForProjects(self, projectId = None,
            overrideAuth = False, newUser = '', newPass = ''):
        cu = self.db.cursor()

        if projectId:
            cu.execute("""SELECT l.labelId, l.label, p.fqdn, p.shortname, l.url, l.authType,
                                    l.username, l.password, l.entitlement,
                                    p.external
                            FROM Labels l, Projects p
                            WHERE p.projectId=? AND l.projectId=p.projectId""", projectId)
        else:
            cu.execute("""SELECT l.labelId, l.label, p.fqdn, p.shortname, l.url, l.authType,
                                    l.username, l.password, l.entitlement,
                                    p.external
                            FROM Labels l, Projects p
                            WHERE l.projectId=p.projectId""")

        repoMap = {}
        labelIdMap = {}
        userMap = []
        entMap = []
        for (labelId, label, host, shortname, url, authType, username, password,
                entitlement, external) in cu.fetchall():
            if overrideAuth:
                authType = 'userpass'
                username = newUser
                password = newPass

            if not label:
                label = host + '@dummy:label'
            labelIdMap[label] = labelId
            if not url:
                url = 'https://%s/repos/%s/' % (self.cfg.siteHost, shortname)
            repoMap[host] = url

            if authType == 'userpass':
                userMap.append((host, (username, password)))
            elif authType == 'entitlement':
                entMap.append((host, ('', entitlement)))
            else:
                userMap.append((host, (self.cfg.authUser, self.cfg.authPass)))

        return labelIdMap, repoMap, userMap, entMap

    def getLabelsForProject(self, projectId,
            overrideAuth = False, newUser = '', newPass = ''):
        return self._getAllLabelsForProjects(projectId, overrideAuth, newUser, newPass)

    def getLabel(self, labelId):
        cu = self.db.cursor()
        cu.execute("""SELECT label, shortname, url, authType, username, password,
                entitlement, fqdn
                FROM Labels
                JOIN Projects USING (projectId)
                WHERE labelId=?
                """, labelId)

        p = cu.fetchone()
        if not p:
            raise LabelMissing
        else:
            label, shortname, url, authType, username, password, entitlement, fqdn = p
            if not label:
                label = fqdn + '@dummy:label'
            if not url:
                url = 'https://%s/repos/%s/' % (self.cfg.siteHost, shortname)
            out = dict(
                    label=label,
                    url=url,
                    authType=authType,
                    username=username,
                    password=password,
                    entitlement=entitlement)
            for key, value in out.items():
                if value is None:
                    out[key] = ''
            return out

    @database.dbWriter
    def addLabel(self, cu, projectId, label, url=None, authType='none',
            username=None, password=None, entitlement=None):
        cu.execute("""SELECT count(labelId) FROM Labels WHERE label=? and projectId=?""",
                   label, projectId)
        c = cu.fetchone()[0]
        if c > 0:
            raise DuplicateLabel

        cu.execute("""INSERT INTO Labels (projectId, label, url, authType,
            username, password, entitlement)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", projectId, label, url,
                    authType, username, password, entitlement)
        return cu.lastid()

    @database.dbWriter
    def editLabel(self, cu, labelId, label, url, authType='none',
            username=None, password=None, entitlement=None):
        if not url:
            url = None
        if not username:
            username = password = None
        if not entitlement:
            entitlement = None
        cu.execute("""UPDATE Labels SET label=?, url=?, authType=?,
            username=?, password=?, entitlement=? WHERE labelId=?""",
            label, url, authType, username, password, entitlement, labelId)

    @database.dbWriter
    def removeLabel(self, cu, projectId, labelId):
        cu.execute("""DELETE FROM Labels WHERE projectId=? AND labelId=?""", projectId, labelId)
        return False

    def deleteLabels(self, projectId, commit=True):
        try:
            cu = self.db.cursor()
            cu.execute("DELETE FROM Labels WHERE projectId=?", projectId)
        except:
            self.db.rollback()
            raise
        else:
            if commit:
                self.db.commit()


class RepositoryDatabase:
    def __init__(self, cfg):
        self.cfg = cfg

    def _getTemplate(self):
        # This is wrong, but it will hold us over until this is properly
        # integrated with the new logic.
        return self.cfg.database[self.cfg.defaultDatabase]

    def create(self, name):
        # this used to pre-initialize the cache for test suite purposes
        # but there is no longer a cache db
        pass

    def getRepositoryDB(self, name, db = None):
        database = None
        if db:
            cu = db.cursor()
            if db.driver == 'mysql':
                cu.execute("SELECT `database` FROM Projects WHERE hostname = ?",
                        name.split('.')[0])
            else:
                cu.execute("SELECT database FROM Projects WHERE hostname = ?",
                        name.split('.')[0])
            database = cu.fetchone()
            if database:
                database = database[0]
        if database is None:
            database = self.cfg.defaultDatabase

        if ' ' in database:
            driver, path = database.split(' ', 1)
        else:
            driver, path = self.cfg.database[database]

        if '%s' in path:
            path %= self.translate(name)
        return driver, path

    def translate(self, x):
        return x


class SqliteRepositoryDatabase(RepositoryDatabase):
    driver = "sqlite"

    def create(self, name):
        util.mkdirChain(os.path.dirname(self._getTemplate()[1] % name))
        RepositoryDatabase.create(self, name)
        
    def delete(self, name):
        path = self._getTemplate()[1] % name
        if os.path.exists(path):
            util.rmtree(path)


class PostgreSqlRepositoryDatabase(RepositoryDatabase):
    tableOpts = "ENCODING 'UTF8'"
    driver = 'postgresql'

    def translate(self, x):
        return x.translate(transTables[self.driver])

    def create(self, name):
        path = self._getTemplate()[1] % 'postgres'
        db = dbstore.connect(path, self.driver)

        dbName = self.translate(name)

        cu = db.cursor()
        # this check should never be required outside of the test suite,
        # and it could be kind of dangerous being called in production.
        cu.execute("SELECT datname FROM pg_database")
        createDb = True
        if dbName in [x[0] for x in cu.fetchall()]:
            createDb = False
            db.close()
            if self.cfg.debugMode:
                import gc
                while gc.collect():
                    pass

                reposDb = dbstore.connect(
                        self._getTemplate()[1] % dbName, self.driver)
                reposDb.loadSchema()
                reposCu = reposDb.cursor()
                for t in reposDb.tempTables:
                    reposCu.execute("DROP TABLE %s" % (t,))
                for t in reposDb.tables:
                    reposCu.execute("DROP TABLE %s CASCADE" % (t,))
                reposDb.close()
            else:
                raise RepositoryAlreadyExists(name)
            
        if createDb:
            cu.execute("CREATE DATABASE %s %s" % (dbName, self.tableOpts))
        db.close()
        RepositoryDatabase.create(self, name)
        
    def delete(self, name):
        path = self._getTemplate()[1] % 'postgres'
        db = dbstore.connect(path, 'postgresql')
        reposName = self.translate(name)

        cu = db.cursor()
        cu.execute("DROP DATABASE %s" % reposName)
        util.rmtree(path + reposName, ignore_errors = True)


class PGPoolRepositoryDatabase(PostgreSqlRepositoryDatabase):
    driver = 'pgpool'


class PsycoRepositoryDatabase(PostgreSqlRepositoryDatabase):
    driver = 'psycopg2'


class MySqlRepositoryDatabase(RepositoryDatabase):
    tableOpts = "character set latin1 collate latin1_bin"
    driver = "mysql"

    def translate(self, x):
        return x.translate(transTables['mysql'])

    def create(self, name):
        path = self._getTemplate()[1] % 'mysql'
        db = dbstore.connect(path, 'mysql')

        dbName = self.translate(name)

        cu = db.cursor()
        # this check should never be required outside of the test suite,
        # and it could be kind of dangerous being called in production.
        # audited for SQL injection
        cu.execute("SHOW DATABASES")
        if dbName in [x[0] for x in cu.fetchall()]:
            if self.cfg.debugMode:
                cu.execute("DROP DATABASE %s" % dbName)
            else:
                raise RepositoryAlreadyExists(name)
        cu.execute("CREATE DATABASE %s %s" % (dbName, self.tableOpts))
        db.close()
        RepositoryDatabase.create(self, name)
        
    def delete(self, name):
        path = self._getTemplate()[1] % 'mysql'
        db = dbstore.connect(path, 'mysql')
        reposName = self.translate(name)

        cu = db.cursor()
        cu.execute("DROP DATABASE %s" % reposName)
        util.rmtree(path + reposName, ignore_errors = True)


def getFactoryForRepos(driver):
    if driver == 'sqlite':
        return SqliteRepositoryDatabase
    elif driver == 'mysql':
        return MySqlRepositoryDatabase
    elif driver == 'postgresql':
        return PostgreSqlRepositoryDatabase
    elif driver == 'pgpool':
        return PGPoolRepositoryDatabase
    elif driver == 'psycopg2':
        return PsycoRepositoryDatabase


class ProductVersionsTable(database.KeyedTable):
    name = 'ProductVersions'
    key = 'productVersionId'
    fields = [ 'productVersionId',
               'projectId',
               'namespace',
               'name',
               'description',
               'label',
             ]

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.KeyedTable.__init__(self, db)

    def getProductVersionListForProduct(self, projectId):
        cu = self.db.cursor()
        fields = self.fields[:5]  # rbuild compatibility
        cu.execute("""SELECT %s FROM %s
                      WHERE projectId = ?""" % (', '.join(fields),
                            self.name),
                      projectId)
        return [ list(x) for x in cu.fetchall() ]

class ProjectUsersTable(database.DatabaseTable):
    name = "ProjectUsers"
    fields = ["projectId", "userId", "level"]

    def getUserlevelForProjectMember(self, projectId, userId):
        cu = self.db.cursor()
        cu.execute("""SELECT level FROM ProjectUsers
                      WHERE projectId = ? AND userId = ?""",
                      projectId, userId)
        res = cu.fetchone()
        if res:
            return res[0]
        else:
            raise ItemNotFound()

    def getEC2AccountNumbersForProjectUsers(self, projectId):
        writers = set()
        readers = set()
        cu = self.db.cursor()
        cu.execute("""
            SELECT CASE WHEN pu.level <= 1 THEN 1 ELSE 0 END AS isWriter,
                tc.credentials AS creds
              FROM projectUsers AS pu
              JOIN TargetUserCredentials AS tuc USING (userId)
              JOIN TargetCredentials AS tc USING (targetCredentialsId)
              JOIN Targets ON (tuc.targetId=Targets.targetId)
              JOIN target_types USING (target_type_id)
             WHERE pu.projectId = ?
               AND target_types.name = ?
               AND Targets.name = ?""", projectId, 'ec2', 'aws')
        for isWriter, creds in cu.fetchall():
            val = mintdata.unmarshalTargetUserCredentials(None, creds).get('accountId')
            if val is None:
                continue
            if isWriter:
                writers.add(val)
            else:
                readers.add(val)
        return sorted(writers), sorted(readers)

    def new(self, projectId, userId, level, commit=True):
        assert(level in userlevels.LEVELS)
        cu = self.db.cursor()

        cu.execute("SELECT * FROM ProjectUsers WHERE projectId=? AND userId = ?",
                   projectId, userId)
        if cu.fetchall():
            self.db.rollback()
            raise DuplicateItem("membership")

        cu.execute("INSERT INTO ProjectUsers VALUES(?, ?, ?)", projectId,
                   userId, level)
        if commit:
            self.db.commit()

    def delete(self, projectId, userId, commit=True, force=False):
        cu = self.db.cursor()
        cu.execute("DELETE FROM ProjectUsers WHERE projectId=? AND userId=?", projectId, userId)
        if commit:
            self.db.commit()


#
# Copyright (c) 2005-2009 rPath, Inc.
#
# All Rights Reserved
#
import base64
import os
import string
import sys
import time

from mint import buildtypes
from mint.lib import database
from mint.lib import data as mintdata
from mint.helperfuncs import truncateForDisplay, rewriteUrlProtocolPort, \
        hostPortParse, configureClientProxies, getProjectText
from mint import helperfuncs
from mint import searcher
from mint import userlevels
from mint.mint_error import *

from conary import dbstore
from conary.deps import deps
from conary.lib import util
from conary.repository.netrepos import netserver
from conary.conarycfg import ConaryConfiguration

# functions to convert a repository name to a database-safe name string
transTables = {
    'sqlite':       string.maketrans("", ""),
    'mysql':        string.maketrans("-.:", "___"),
    'postgresql':   string.maketrans("-.:", "___").lower(),
    'pgpool':       string.maketrans("-.:", "___").lower(),
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
        except DuplicateItem, e:
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
        for x in cu.fetchall_dict():
            level = x.pop('level')
            hasRequests = False
            if x['creatorId'] is None:
                del x['creatorId']
            ret.append((x, level, hasRequests))
        return ret

    def getNewProjects(self, limit, showFledgling):
        cu = self.db.cursor()

        if showFledgling:
            fledgeQuery = ""
        else:
            fledgeQuery = "AND EXISTS(SELECT troveName FROM Commits WHERE projectId=Projects.projectId LIMIT 1)"

        cu.execute("""SELECT projectId, hostname, name, description, timeModified
                FROM Projects WHERE NOT hidden AND NOT external %s ORDER BY timeCreated DESC
                LIMIT ?""" % fledgeQuery, limit)

        ids = []
        for x in cu.fetchall():
            ids.append(list(x))

            # cast id and timestamp to int
            ids[-1][0] = int(ids[-1][0])
            ids[-1][4] = int(ids[-1][4])
            ids[-1][3] = helperfuncs.truncateForDisplay(ids[-1][3])

        return ids

    def search(self, terms, modified, limit, offset, includeInactive=False, byPopularity=True, filterNoDownloads = True):
        """
        Returns a list of projects matching L{terms} of length L{limit}
        starting with item L{offset}.
        @param terms: Search terms
        @param modified: Code for the period within which the project must have been modified to include in the search results.
        @param offset: Count at which to begin listing
        @param limit:  Number of items to return
        @param includeInactive:  Include hidden and fledgling projects
        @param byPopularity: Sort by popularity metric. (OBSOLETE)
        @return:       a dictionary of the requested items.
                       each entry will contain four bits of data:
                        The hostname for use with linking,
                        The project name,
                        The project's description
                        The date last modified.
                        The projects popularity rank.
        """
        columns = ['Projects.projectId', 'Projects.hostname',
                   'Projects.name', 'Projects.description',
                   """Projects.timeCreated AS timeModified""",
                   """0 AS rank""",
                   """COALESCE(tmpLatestReleases.timePublished, 0) AS lastRelease"""
        ]

        searchcols = ['Projects.name', 'Projects.description', 'hostname']
        leftJoins = [ ('tmpLatestReleases', 'projectId'),
                      ('TopProjects', 'projectId') ]

        cu = self.db.cursor()

        self.db.loadSchema()
        found = False
        if 'tmpLatestReleases' in self.db.tempTables:
            cu.execute("DELETE FROM tmpLatestReleases")
            found = True

        if not found:
            cu.execute("""CREATE TEMPORARY TABLE tmpLatestReleases (
                projectId       INTEGER NOT NULL,
                timePublished   NUMERIC(14,3))""")

        cu.execute("""INSERT INTO tmpLatestReleases (projectId, timePublished)
            SELECT projectId as projectId, MAX(timePublished) AS timePublished FROM PublishedReleases
            GROUP BY projectId""")

        # extract a list of build types to search for.
        # these are additive, unlike other search limiters.
        buildTypes = []
        flavorFlagTypes = []
        terms, limiters = searcher.parseTerms(terms, limiterNames=['buildtype'])
        for limiter in limiters:
            try:
                key, val = limiter.split("=")
            except ValueError:
                continue # ignore malformed limiters

            if not val:
                continue

            if key == "buildtype":
                if int(val) in buildtypes.TYPES:
                    buildTypes.append(int(val))
                elif int(val) in buildtypes.FLAG_TYPES:
                    flavorFlagTypes.append(buildtypes.flavorFlagsFromId[int(val)])

        # build the extra SQL bits from the build types list
        extras = ""
        extraSubs = []
        if buildTypes:
            extras += """ AND (EXISTS(SELECT buildId FROM Builds
                                        LEFT JOIN PublishedReleases USING(pubReleaseId)
                                        WHERE buildType IN (%s)
                                            AND pubReleaseId IS NOT NULL
                                            AND Builds.projectId=Projects.projectId
                                            AND PublishedReleases.timePublished IS NOT NULL)""" % \
                (", ".join("?" * len(buildTypes)))
            extraSubs += buildTypes
        if flavorFlagTypes:
            sql = """EXISTS(SELECT Builds.buildId FROM Builds
                                LEFT JOIN PublishedReleases USING(pubReleaseId)
                                JOIN BuildData ON Builds.buildId=BuildData.buildId
                              WHERE BuildData.name in (%s)
                                AND Builds.projectId=Projects.projectId
                                AND pubReleaseId IS NOT NULL
                                AND PublishedReleases.timePublished IS NOT NULL)""" % \
                (", ".join("?" * len(flavorFlagTypes)))
            extraSubs += flavorFlagTypes
            # append as an OR if we are already filtering by some build types,
            # or an AND if we are only searching flavor flags
            if extras:
                extras += "OR " + sql + ")"
            else:
                extras = "AND " + sql
        elif buildTypes:
            extras += ")"

        if not includeInactive:
            extras += " AND NOT Projects.hidden"

        terms = " ".join(terms)

        # if there are no query terms, show only projects
        # that have something downloadable.
        if filterNoDownloads:
            filterNoDownloads = (terms.strip() == "")

            # if we aren't asking for a specific build type, but we are
            # asking for only projects with downloadable stuff, filter
            # by the existence of a published release.
            if not buildTypes and not flavorFlagTypes and filterNoDownloads:
                extras += """ AND EXISTS(SELECT Builds.buildId FROM Builds
                                            LEFT JOIN PublishedReleases USING(pubReleaseId)
                                            WHERE Builds.projectId=Projects.projectId
                                              AND pubReleaseId IS NOT NULL
                                              AND timePublished IS NOT NULL)"""

        whereClause = searcher.Searcher.where(terms, searchcols, extras, extraSubs)

        orderByClause = searcher.Searcher.order(terms, searchcols, 'UPPER(Projects.name)')

        ids, count = database.KeyedTable.search(self, columns, 'Projects',
                whereClause,
                orderByClause,
                searcher.Searcher.lastModified('timeModified', modified),
                limit, offset, leftJoins)
        for i, x in enumerate(ids[:]):
            ids[i] = list(x)
            ids[i][2] = searcher.Searcher.truncate(x[2], terms)

        cu.execute("DROP TABLE tmpLatestReleases")

        return [x[1] for x in [(x[2].lower(),x) for x in ids]], count

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

    def getDefaultProjectLabel(self, projectId):
        cu = self.db.cursor()

        cu.execute ("""SELECT label 
                      FROM Labels 
                      WHERE projectId=?
                      ORDER BY projectId LIMIT 1""", projectId)

        label = cu.fetchone()
        return label[0]

    def _getAllLabelsForProjects(self, projectId = None,
            overrideAuth = False, newUser = '', newPass = ''):
        cu = self.db.cursor()

        if projectId:
            cu.execute("""SELECT l.labelId, l.label, p.fqdn, l.url, l.authType,
                                    l.username, l.password, l.entitlement,
                                    p.external
                            FROM Labels l, Projects p
                            WHERE p.projectId=? AND l.projectId=p.projectId""", projectId)
        else:
            cu.execute("""SELECT l.labelId, l.label, p.fqdn, l.url, l.authType,
                                    l.username, l.password, l.entitlement,
                                    p.external
                            FROM Labels l, Projects p
                            WHERE l.projectId=p.projectId""")

        repoMap = {}
        labelIdMap = {}
        userMap = []
        entMap = []
        for (labelId, label, host, url, authType, username, password,
                entitlement, external) in cu.fetchall():
            if overrideAuth:
                authType = 'userpass'
                username = newUser
                password = newPass

            if not label:
                label = host + '@dummy:label'
            labelIdMap[label] = labelId
            host = label[:label.find('@')]
            if url:
                if not external:
                    if self.cfg.SSL:
                        protocol = "https"
                        newHost, newPort = hostPortParse(self.cfg.secureHost, 443)
                    else:
                        protocol = "http"
                        newHost, newPort = hostPortParse(self.cfg.projectDomainName, 80)

                    url = rewriteUrlProtocolPort(url, protocol, newPort)

                map = url
            else:
                map = "http://%s/conary/" % (host)

            repoMap[host] = map

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

    def getAllLabelsForProjects(self,
            overrideAuth = False, newUser = '', newPass = ''):
        return self._getAllLabelsForProjects(overrideAuth=overrideAuth, newUser=newUser, newPass=newPass)

    def getLabel(self, labelId):
        cu = self.db.cursor()
        cu.execute('''SELECT label, url, authType, username, password,
            entitlement FROM Labels WHERE labelId=?''', labelId)

        p = cu.fetchone()
        if not p:
            raise LabelMissing
        else:
            label = p[0] or ''
            username = p[3] is not None and p[3] or ''
            password = p[4] is not None and p[4] or ''
            entitlement = p[5] is not None and p[5] or ''
            url = p[1] or ''  # seems to be unused
            return dict(label=label, url=url, authType=p[2],
                username=username, password=password, entitlement=entitlement)

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
                tableList = []
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


class ProductVersionsTable(database.KeyedTable):
    name = 'ProductVersions'
    key = 'productVersionId'
    fields = [ 'productVersionId',
               'projectId',
               'namespace',
               'name',
               'description',
             ]

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.KeyedTable.__init__(self, db)

    def getProductVersionListForProduct(self, projectId):
        cu = self.db.cursor()
        cu.execute("""SELECT %s FROM %s
                      WHERE projectId = ?""" % (', '.join(self.fields),
                            self.name),
                      projectId)
        return [ list(x) for x in cu.fetchall() ]

class ProjectUsersTable(database.DatabaseTable):
    name = "ProjectUsers"
    fields = ["projectId", "userId", "level"]

    def getOwnersByProjectName(self, projectname):
        cu = self.db.cursor()
        cu.execute("""SELECT u.username, u.email
                      FROM Projects pr, ProjectUsers p, Users u
                      WHERE pr.projectId=p.projectId AND p.userId=u.userId
                      AND pr.hostname=?
                      AND p.level=? AND pr.disabled=0""", projectname,
                   userlevels.OWNER)
        data = []
        for r in cu.fetchall():
            data.append(list(r))
        return data

    def getMembersByProjectId(self, projectId):
        cu = self.db.cursor()
        cu.execute("""SELECT p.userId, u.username, p.level
                      FROM ProjectUsers p, Users u
                      WHERE p.userId=u.userId AND p.projectId=?
                      ORDER BY p.level, u.username""",
                   projectId)
        data = []
        for r in cu.fetchall():
            data.append( [r[0], r[1], r[2]] )
        return data

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
            val = mintdata.unmarshalTargetUserCredentials(creds).get('accountId')
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

    def onlyOwner(self, projectId, userId):
        cu = self.db.cursor()
        # verify userId is an owner of the project.
        cu.execute("SELECT level from ProjectUsers where projectId=? and userId = ?", projectId, userId)
        res = cu.fetchall()
        if (not bool(res)) or (res[0][0] != userlevels.OWNER):
            return False
        cu.execute("SELECT count(userId) FROM ProjectUsers WHERE projectId=? AND userId<>? and LEVEL = ?", projectId, userId, userlevels.OWNER)
        return not cu.fetchone()[0]

    def lastOwner(self, projectId, userId):
        cu = self.db.cursor()
        # check that there are developers
        cu.execute("SELECT count(userId) FROM ProjectUsers WHERE projectId=? AND userId<>? and LEVEL = ?", projectId, userId, userlevels.DEVELOPER)
        if not cu.fetchone()[0]:
            return False
        return self.onlyOwner(projectId, userId)

    def delete(self, projectId, userId, commit=True, force=False):
        if self.lastOwner(projectId, userId):
            if not force:
                raise LastOwner()
        cu = self.db.cursor()
        cu.execute("DELETE FROM ProjectUsers WHERE projectId=? AND userId=?", projectId, userId)
        if commit:
            self.db.commit()


#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#
import os
import string
import sys
import time

from mint import buildtypes
from mint.lib import database
from mint.helperfuncs import truncateForDisplay, rewriteUrlProtocolPort, \
        hostPortParse, configureClientProxies, getProjectText, \
        addUserToRepository
from mint import helperfuncs
from mint import mailinglists
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
    'postgresql':   string.maketrans("-.:", "___"),
    'pgpool':       string.maketrans("-.:", "___"),
}

class ProjectsTable(database.KeyedTable):
    name = 'Projects'
    key = 'projectId'
    fields = ['projectId', 'creatorId', 'name', 'hostname', 'domainname',
        'namespace', 'projecturl', 'description', 'disabled', 'hidden',
        'external', 'isAppliance', 'timeCreated', 'timeModified',
        'commitEmail', 'backupExternal', 'shortname', 'prodtype', 'version']

    def __init__(self, db, cfg):
        self.cfg = cfg

        # poor excuse for a switch statement
        self.reposDB = {'sqlite': SqliteRepositoryDatabase,
                        'mysql':  MySqlRepositoryDatabase,
                        'postgresql':  PostgreSqlRepositoryDatabase,
                        'pgpool': PGPoolRepositoryDatabase,
                       }[self.cfg.reposDBDriver](cfg)
        # call init last so that we can use reposDB during schema upgrades
        database.DatabaseTable.__init__(self, db)

    def new(self, **kwargs):
        try:
            id = database.KeyedTable.new(self, **kwargs)
        except DuplicateItem, e:
            cu = self.db.cursor()
            cu.execute("SELECT projectId FROM Projects WHERE hostname=?", kwargs['hostname'])
            results = cu.fetchall()
            if len(results) > 0:
                raise DuplicateHostname()
            cu.execute("SELECT projectId FROM Projects WHERE name=?", kwargs['name'])
            results = cu.fetchall()
            if len(results) > 0:
                raise DuplicateName()
        return id
    
    def deleteProject(self, projectId, projectFQDN, commit=True):
        try:
            # try deleteing the repository
            self.reposDB.delete(projectFQDN)
            
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

        # audited for SQL injection.
        fqdnConcat = database.concat(self.db, "hostname", "'.'", "domainname")
        cu.execute("""SELECT projectId FROM Projects
                      WHERE %s=?""" % fqdnConcat, fqdn)

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
            stmt += " AND hidden=0"
        cu.execute(stmt, userId)

        return [tuple(x) for x in cu.fetchall()]

    def getProjectDataByMember(self, userId, filter = False):
        cu = self.db.cursor()
        # audited for sql injection. check sat.
        # We used to filter these results with another condition that if the
        # project was hidden, you had to be a userlevels.WRITER.  That has
        # been changed to allow normal users to browse hidden projects of
        # which they are a member.
        stmt = """SELECT Projects.*, ProjectUsers.level,
                     EXISTS(SELECT 1 FROM MembershipRequests
                            WHERE projectId=Projects.projectid) AS hasRequests
                  FROM ProjectUsers
                  JOIN Projects ON Projects.projectId=ProjectUsers.projectId
                  WHERE ProjectUsers.userId=?"""
        if filter:
            stmt += " AND hidden=0"
        cu.execute(stmt, userId)
        ret = []
        for x in cu.fetchall_dict():
            level = x.pop('level')
            hasRequests = x.pop('hasRequests')
            ret.append((x, level, hasRequests))
        return ret

    def getNewProjects(self, limit, showFledgling):
        cu = self.db.cursor()

        if showFledgling:
            fledgeQuery = ""
        else:
            fledgeQuery = "AND EXISTS(SELECT troveName FROM Commits WHERE projectId=Projects.projectId LIMIT 1)"

        cu.execute("""SELECT projectId, hostname, name, description, timeModified
                FROM Projects WHERE hidden=0 AND external=0 %s ORDER BY timeCreated DESC
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
        @param byPopularity: Sort by popularity metric.
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
                   """COALESCE(LatestCommit.commitTime, Projects.timeCreated) AS timeModified""",
                   """COALESCE(TopProjects.rank, (SELECT COUNT(projectId) FROM Projects)) AS rank""",
                   """COALESCE(tmpLatestReleases.timePublished, 0) AS lastRelease"""
        ]

        searchcols = ['Projects.name', 'Projects.description', 'hostname']
        leftJoins = [ ('tmpLatestReleases', 'projectId'),
                      ('LatestCommit', 'projectId'),
                      ('TopProjects', 'projectId') ]

        cu = self.db.cursor()
        cu.execute("""CREATE TEMPORARY TABLE tmpLatestReleases (
            projectId       INTEGER NOT NULL,
            timePublished   NUMERIC(14,3))""")

        cu.execute("""INSERT INTO tmpLatestReleases (projectId, timePublished)
            SELECT projectId as projectId, MAX(timePublished) AS timePublished FROM PublishedReleases
            GROUP BY projectId""")

        self.db.commit()

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
            extras += """ AND (EXISTS(SELECT buildId FROM BuildsView
                                        LEFT JOIN PublishedReleases USING(pubReleaseId)
                                        WHERE buildType IN (%s)
                                            AND pubReleaseId IS NOT NULL
                                            AND BuildsView.projectId=Projects.projectId
                                            AND PublishedReleases.timePublished IS NOT NULL)""" % \
                (", ".join("?" * len(buildTypes)))
            extraSubs += buildTypes
        if flavorFlagTypes:
            sql = """EXISTS(SELECT BuildsView.buildId FROM BuildsView
                                LEFT JOIN PublishedReleases USING(pubReleaseId)
                                JOIN BuildData ON BuildsView.buildId=BuildData.buildId
                              WHERE BuildData.name in (%s)
                                AND BuildsView.projectId=Projects.projectId
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
            extras += " AND Projects.hidden=0"

        terms = " ".join(terms)

        # if there are no query terms, show only projects
        # that have something downloadable.
        if filterNoDownloads:
            filterNoDownloads = (terms.strip() == "")

            # if we aren't asking for a specific build type, but we are
            # asking for only projects with downloadable stuff, filter
            # by the existence of a published release.
            if not buildTypes and not flavorFlagTypes and filterNoDownloads:
                extras += """ AND EXISTS(SELECT BuildsView.buildId FROM BuildsView
                                            LEFT JOIN PublishedReleases USING(pubReleaseId)
                                            WHERE BuildsView.projectId=Projects.projectId
                                              AND pubReleaseId IS NOT NULL
                                              AND timePublished IS NOT NULL)"""

        whereClause = searcher.Searcher.where(terms, searchcols, extras, extraSubs)

        if byPopularity:
            orderByClause = 'rank ASC'
        else:
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
        self.db.commit()

        return [x[1] for x in [(x[2].lower(),x) for x in ids]], count

    def createRepos(self, reposPath, contentsDirs, hostname, domainname, username = None, password = None):
        dbPath = os.path.join(reposPath, hostname + "." + domainname)
        tmpPath = os.path.join(dbPath, 'tmp')
        util.mkdirChain(tmpPath)

        cfg = netserver.ServerConfig()

        name = "%s.%s" % (hostname, domainname)
        self.reposDB.create(name)

        cfg.repositoryDB = self.reposDB.getRepositoryDB(name)
        cfg.tmpDir = tmpPath
        cfg.serverName = hostname + "." + domainname
        cfg.repositoryMap = {}
        cfg.contentsDir = " ".join(x % name for x in contentsDirs.split(" "))

        # create the initial repository schema
        db = dbstore.connect(cfg.repositoryDB[1], cfg.repositoryDB[0])
        from conary.server import schema
        schema.loadSchema(db)
        db.commit()

        repos = netserver.NetworkRepositoryServer(cfg, '', db)

        if username:
            addUserToRepository(repos, username, password, username)
            repos.auth.addAcl(username, None, None, write=True, remove=False)
            repos.auth.setAdmin(username, True)

        anon = "anonymous"
        addUserToRepository(repos, anon, anon, anon)
        repos.auth.addAcl(anon, None, None, write=False, remove=False)

        # make it possible to use the auth user account to create a project
        # used to create the rMake repository (RBL-3810)
        if username != self.cfg.authUser:
            # add the mint auth user so we can add additional permissions
            # to this repository
            addUserToRepository(repos, self.cfg.authUser, self.cfg.authPass,
                self.cfg.authUser)
            repos.auth.addAcl(self.cfg.authUser, None, None, write=True,
                remove=False)
        repos.auth.setAdmin(self.cfg.authUser, True)
        repos.auth.setMirror(self.cfg.authUser, True)
        if username:
            repos.auth.setMirror(username, True)

        db.close()

    def addProjectRepositoryUser(self, username, password, hostName, 
                                 domainName, reposPath, contentsDir):
        name = "%s.%s" % (hostName, domainName)
        dbPath = os.path.join(reposPath, name)

        cfg = netserver.ServerConfig()
        cfg.serverName = name
        cfg.tmpDir = os.path.join(dbPath, 'tmp')
        cfg.repositoryMap = {}
        cfg.contentsDir = " ".join(x % name for x in contentsDir.split(" "))
        cfg.repositoryDB = self.reposDB.getRepositoryDB(name)

        repos = netserver.NetworkRepositoryServer(cfg, '')
        addUserToRepository(repos, username, password, username)
        repos.auth.addAcl(username, None, None, write=True, remove=False)
        repos.auth.setAdmin(username, True)

        return username

    @database.dbWriter
    def hide(self, cu, projectId):
        # Anonymous user is added/removed in server
        cu.execute("UPDATE Projects SET hidden=1, timeModified=? WHERE projectId=?", time.time(), projectId)
        cu.execute("DELETE FROM PackageIndex WHERE projectId=?", projectId)

    def unhide(self, projectId):
        # Anonymous user is added/removed in server
        cu = self.db.cursor()

        cu.execute("UPDATE Projects SET hidden=0, timeModified=? WHERE projectId=?", time.time(), projectId)
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
            cu.execute("""SELECT l.labelId, l.label, l.url, l.authType, 
                                    l.username, l.password, l.entitlement,
                                    p.external
                            FROM Labels l, Projects p
                            WHERE p.projectId=? AND l.projectId=p.projectId""", projectId)
        else:
            cu.execute("""SELECT l.labelId, l.label, l.url, l.authType, 
                                    l.username, l.password, l.entitlement,
                                    p.external
                            FROM Labels l, Projects p
                            WHERE l.projectId=p.projectId""")

        repoMap = {}
        labelIdMap = {}
        userMap = []
        entMap = []
        for labelId, label, url, authType, username, password, entitlement, \
                external in cu.fetchall():
            if overrideAuth:
                authType = 'userpass'
                username = newUser
                password = newPass

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
            username = p[3] is not None and p[3] or ''
            password = p[4] is not None and p[4] or ''
            entitlement = p[5] is not None and p[5] or ''
            return dict(label=p[0], url=p[1], authType=p[2],
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
        return cu._cursor.lastrowid

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

class Databases(database.KeyedTable):
    name = "ReposDatabases"
    key = "databaseId"

    fields = ['databaseId', 'driver', 'path']


class ProjectDatabase(database.DatabaseTable):
    name = "ProjectDatabase"
    fields = ['projectId', 'databaseId']


class RepositoryDatabase:
    def __init__(self, cfg):
        self.cfg = cfg

    def create(self, name):
        # this used to pre-initialize the cache for test suite purposes
        # but there is no longer a cache db
        pass

    def getRepositoryDB(self, name, db = None):
        if db:
            cu = db.cursor()
            cu.execute("""SELECT driver, path
                FROM ReposDatabases JOIN ProjectDatabase USING (databaseId)
                WHERE projectId=(SELECT projectId FROM Projects WHERE hostname=?)""", name.split(".")[0])

            r = cu.fetchone()
        else:
            r = None

        if r:
            return r[0], r[1]
        else:
            name = self.translate(name)
            return self.cfg.reposDBDriver, self.cfg.reposDBPath % name

    def translate(self, x):
        return x


class SqliteRepositoryDatabase(RepositoryDatabase):
    driver = "sqlite"

    def create(self, name):
        util.mkdirChain(os.path.dirname(self.cfg.reposDBPath % name))
        RepositoryDatabase.create(self, name)
        
    def delete(self, name):
        util.rmtree(self.cfg.reposDBPath + name, ignore_errors = True)


class PostgreSqlRepositoryDatabase(RepositoryDatabase):
    tableOpts = "ENCODING 'UTF8'"
    driver = 'postgresql'

    def translate(self, x):
        return x.translate(transTables[self.driver].lower())

    def create(self, name):
        path = self.cfg.reposDBPath % 'postgres'
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
                        self.cfg.reposDBPath % dbName.lower(), self.driver)
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
        path = self.cfg.reposDBPath % 'postgres'
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
        path = self.cfg.reposDBPath % 'mysql'
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
        path = self.cfg.reposDBPath % 'mysql'
        db = dbstore.connect(path, 'mysql')
        reposName = self.translate(name)

        cu = db.cursor()
        cu.execute("DROP DATABASE %s" % reposName)
        util.rmtree(path + reposName, ignore_errors = True)

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
        writers = []
        readers = []
        cu = self.db.cursor()
        cu.execute("""
            SELECT CASE WHEN MIN(pu.level) <= 1 THEN 1 ELSE 0 END AS isWriter,
                ud.value AS awsAccountNumber
            FROM projectUsers AS pu
                JOIN userData AS ud
                    ON ud.name = 'awsAccountNumber'
                       AND pu.userId = ud.userId
                       AND length(ud.value) > 0
            WHERE pu.projectId = ?
            GROUP BY ud.value""", projectId)
        for res in cu.fetchall():
            if res[0]:
                writers.append(res[1])
            else:
                readers.append(res[1])
        return writers, readers

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


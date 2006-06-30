#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import os
import string
import sys
import time

from mint import database
from mint.helperfuncs import truncateForDisplay, rewriteUrlProtocolPort, \
        hostPortParse
from mint import mailinglists
from mint import projectlisting
from mint import searcher
from mint import userlevels
from mint import releases
from mint.mint_error import MintError

from conary import dbstore
from conary import sqlite3
from conary import versions
from conary.lib import util
from conary.repository.netrepos import netserver
from conary.conarycfg import ConaryConfiguration


class InvalidHostname(MintError):
    def __str__(self):
        return "invalid hostname: must start with a letter and contain only letters, numbers, and hyphens."

class DuplicateHostname(MintError):
    def __str__(self):
        return "A project using this hostname already exists"

class DuplicateName(MintError):
    def __str__(self):
        return "A project using this project title already exists"

class LabelMissing(MintError):
    def __str__(self):
        return "Project label does not exist"

mysqlTransTable = string.maketrans("-.:", "___")

class Project(database.TableObject):
    # XXX: disabled is slated for removal next schema upgrade --sgp
    __slots__ = ('projectId', 'creatorId', 'name',
                 'description', 'hostname', 'domainname', 'projecturl', 
                 'hidden', 'external', 'disabled',
                 'timeCreated', 'timeModified')

    def getItem(self, id):
        return self.server.getProject(id)

    def getCreatorId(self):
        return self.creatorId

    def getName(self):
        return self.name

    def getNameForDisplay(self, maxWordLen = 15):
        return truncateForDisplay(self.name, maxWordLen = maxWordLen)

    def getDomainname(self):
        return self.domainname

    def getProjectUrl(self):
        return self.projecturl

    def getHostname(self):
        return self.hostname

    def getFQDN(self):
        return '.'.join((self.hostname, self.domainname))

    def getLabel(self):
        return self.server.getDefaultProjectLabel(self.id)

    def getDesc(self):
        return self.description

    def getDescForDisplay(self):
        return truncateForDisplay(self.description, maxWords=100)

    def getTimeCreated(self):
        return self.timeCreated

    def getTimeModified(self):
        return self.timeModified

    def getMembers(self):
        return self.server.getMembersByProjectId(self.id)

    def getReleases(self, showUnpublished = False):
        return [releases.Release(self.server, x) for x \
                in self.server.getReleasesForProject(self.id, showUnpublished)]

    def getCommits(self):
        return self.server.getCommitsForProject(self.id)

    def getUserLevel(self, userId):
        try:
            return self.server.getUserLevel(userId, self.id)
        except database.ItemNotFound:
            return userlevels.NONMEMBER

    def updateUserLevel(self, userId, level):
        return self.server.setUserLevel(userId, self.id, level)

    def addMemberById(self, userId, level):
        assert(level in userlevels.LEVELS)
        return self.server.addMember(self.id, userId, "", level)

    def addMemberByName(self, username, level):
        assert(level in userlevels.LEVELS)
        return self.server.addMember(self.id, 0, username, level)

    def listJoinRequests(self):
        return self.server.listJoinRequests(self.id)

    def delMemberById(self, userId):
        return self.server.delMember(self.id, userId)

    def editProject(self, projecturl, desc, name):
        return self.server.editProject(self.id, projecturl, desc, name)

    def updateUser(self, userId, **kwargs):
        return self.users.update(userId, **kwargs)

    def getLabelIdMap(self):
        """Returns a dictionary mapping of label names to database IDs"""
        labelPath, repoMap, userMap = self.server.getLabelsForProject(self.id, False, '', '')
        return labelPath

    def getConaryConfig(self, overrideAuth = False, newUser = '', newPass = ''):

        labelPath, repoMap, userMap = self.server.getLabelsForProject(self.id, overrideAuth, newUser, newPass)

        cfg = ConaryConfiguration(readConfigFiles=False)
        cfg.root = ":memory:"
        cfg.dbPath = ":memory:"

        cfg.initializeFlavors()

        installLabelPath = " ".join(x for x in labelPath.keys())
        cfg.configLine("installLabelPath %s" % installLabelPath)

        for server, auth in userMap.items():
            cfg.user.addServerGlob(server, auth[0], auth[1])

        cfg.repositoryMap.update(dict((x[0], x[1]) for x in repoMap.items()))
        return cfg

    def addLabel(self, label, url, username="", password=""):
        return self.server.addLabel(self.id, label, url, username, password)

    def editLabel(self, labelId, label, url, username, password):
        return self.server.editLabel(labelId, label, url, username, password)

    def removeLabel(self, labelId):
        return self.server.removeLabel(self.id, labelId)

    def addUserKey(self, username, keydata):
        return self.server.addUserKey(self.id, username, keydata)

    def projectAdmin(self, userName):
        return self.server.projectAdmin(self.id, userName)

    def lastOwner(self, userId):
        return self.server.lastOwner(self.id, userId)

    def onlyOwner(self, userId):
        return self.server.onlyOwner(self.id, userId)

    def orphan(self, mlenabled, mlbaseurl, mlpasswd):
        if mlenabled:
            #Take care of mailing lists
            # FIXME: mailing lists should be handled elsewhere
            mlists = mailinglists.MailingListClient(mlbaseurl + 'RPC2')
            mlists.orphan_lists(mlpasswd, self.getHostname())

    def adopt(self, auth, mlenabled, mlbaseurl, mlpasswd):
        self.addMemberByName(auth.username, userlevels.OWNER)
        if mlenabled:
            # Take care of mailing lists
            # FIXME: mailing lists should be handled elsewhere
            mlists = mailinglists.MailingListClient(mlbaseurl + 'RPC2')
            mlists.adopt_lists(auth, mlpasswd, self.getHostname())

    def getUrl(self):
        if self.external: # we control all external projects, so use externalSiteHost
            return "http://%s%sproject/%s/" % (self.server._cfg.externalSiteHost, self.server._cfg.basePath, self.hostname)
        else:
            return "http://%s%sproject/%s/" % (self.server._cfg.projectSiteHost, self.server._cfg.basePath, self.hostname)


class ProjectsTable(database.KeyedTable):
    name = 'Projects'
    key = 'projectId'
    # XXX: disabled is slated for removal next schema upgrade --sgp
    createSQL= """CREATE TABLE Projects (
                    projectId       %(PRIMARYKEY)s,
                    creatorId       INT,
                    name            varchar(128) UNIQUE,
                    hostname        varchar(128) UNIQUE,
                    domainname      varchar(128) DEFAULT '' NOT NULL,
                    projecturl      varchar(128) DEFAULT '' NOT NULL,
                    description     text NOT NULL DEFAULT '',
                    disabled        INT DEFAULT 0,
                    hidden          INT DEFAULT 0,
                    external        INT DEFAULT 0,
                    timeCreated     INT,
                    timeModified    INT DEFAULT 0
                )"""

    # XXX: disabled is slated for removal next schema upgrade --sgp
    fields = ['projectId', 'creatorId', 'name', 'hostname', 'domainname', 'projecturl', 
              'description', 'disabled', 'hidden', 'external', 'timeCreated', 'timeModified']
    indexes = { "ProjectsHostnameIdx": "CREATE INDEX ProjectsHostnameIdx ON Projects(hostname)",
                "ProjectsDisabledIdx": "CREATE INDEX ProjectsDisabledIdx ON Projects(disabled)",
                "ProjectsHiddenIdx": "CREATE INDEX ProjectsHiddenIdx ON Projects(hidden)"
              }

    def __init__(self, db, cfg):
        self.cfg = cfg

        # poor excuse for a switch statement
        self.reposDB = {'sqlite': SqliteRepositoryDatabase,
                        'mysql':  MySqlRepositoryDatabase,
                       }[self.cfg.reposDBDriver](cfg)
        # call init last so that we can use reposDB during schema upgrades
        database.DatabaseTable.__init__(self, db)

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            cu = self.db.cursor()
            if dbversion == 0 and not self.initialCreation:
                cu.execute("""ALTER TABLE Projects
                             ADD COLUMN hidden INT DEFAULT 0""")
            if dbversion == 2 and not self.initialCreation:
                cu.execute("""ALTER TABLE Projects
                                ADD COLUMN external INT DEFAULT 0""")
                cu.execute("UPDATE Projects SET external=0")
            if dbversion == 4 and not self.initialCreation:
                cu.execute("ALTER TABLE Projects ADD COLUMN description STR")
                cu.execute("UPDATE Projects SET description=desc")
            if dbversion == 15:
                # logic to upgrade mirror ACLs in project repos
                cu = self.db.cursor()
                cu.execute("""SELECT projectId, hostname, domainName, external
                                  FROM Projects""")
                projList = [(x[0], x[1] + '.' + x[2]) for x in cu.fetchall() \
                            if not x[3]]
                rDb = None
                if self.cfg.reposDBDriver != 'sqlite':
                    needDb = True
                else:
                    needDb = False
                for projectId, FQDN in projList:
                    dbCon = self.reposDB.getRepositoryDB(FQDN)
                    try:
                        if self.cfg.reposDBDriver == 'sqlite' or needDb:
                            rDb = dbstore.connect(dbCon[1], dbCon[0])
                            needDb = False
                        else:
                            rDb.use(dbCon[1].split('/')[1])
                    except:
                        from conary.lib import log
                        log.warning('could not connect to: %s' % FQDN)
                        # skip missing repo DB's
                        continue
                    rCu = rDb.cursor()
                    cu.execute("""SELECT userName
                                      FROM ProjectUsers
                                      LEFT JOIN Users ON
                                          Users.userId=ProjectUsers.userId
                                      WHERE projectId=? AND level=?""",
                               projectId, userlevels.OWNER)
                    userList = [x[0] for x in cu.fetchall()] + \
                               [self.cfg.authUser]
                    rCu.execute("""SELECT userGroupId
                                       FROM Users
                                       LEFT JOIN UserGroupMembers
                                       ON UserGroupMembers.userId =
                                              Users.userId
                                       WHERE username IN %s""" % \
                                str(tuple(userList)).replace(",)", ")"))
                    userGroups = [int(x[0]) for x in rCu.fetchall()]
                    rCu.execute("""UPDATE UserGroups
                                       SET canMirror=1
                                       WHERE userGroupId IN %s""" % \
                                str(tuple(userGroups)).replace(",)", ")"))
                    rDb.commit()
                    if self.cfg.reposDBDriver == 'sqlite':
                        rDb.close()
                if rDb:
                    rDb.close()
            return dbversion >= 15
        return True

    def new(self, **kwargs):
        try:
            id = database.KeyedTable.new(self, **kwargs)
        except database.DuplicateItem, e:
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
            raise database.ItemNotFound
        else:
            return r[0]

    def getProjectIdByHostname(self, hostname):
        cu = self.db.cursor()

        cu.execute("SELECT projectId FROM Projects WHERE hostname=?", hostname)

        r = cu.fetchone()
        if not r:
            raise database.ItemNotFound
        else:
            return r[0]

    def getProjectIdsByMember(self, userId, filter = False):
        cu = self.db.cursor()
        # audited for sql injection. check sat.
        stmt = """SELECT ProjectUsers.projectId, level FROM ProjectUsers
                    LEFT JOIN Projects
                        ON Projects.projectId=ProjectUsers.projectId
                    WHERE ProjectUsers.userId=? AND
                    NOT (hidden=1 AND level not in %s)""" % \
            str(tuple(userlevels.WRITERS))
        if filter:
            stmt += " AND hidden=0"
        cu.execute(stmt, userId)

        return [tuple(x) for x in cu.fetchall()]

    def getNumProjects(self, includeInactive=False):
        cu = self.db.cursor()
        whereClause = ""
        if not includeInactive:
            whereClause += "hidden=0 "
        if self.cfg.hideFledgling and not includeInactive:
            whereClause += "%s %s" % ((whereClause and "AND" or ""),
                """(EXISTS(SELECT * FROM Commits WHERE Commits.projectId =
                                                    Projects.projectId)
                    OR external=1)""")
        if whereClause:
            whereClause = "WHERE " + whereClause

        cmd = """SELECT COUNT(name) FROM Projects %s """ % whereClause

        cu.execute(cmd)

        return cu.fetchone()[0]

    def getProjects(self, sortOrder, limit, offset, includeInactive=False):
        """ Return a list of projects with no filtering whatsoever
        @param sortOrder: Order the projects by this criteria
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @param includeInactive: Include hidden projects and fledglings
        """
        cu = self.db.cursor()

        # XXX: This is intimately tied together to the ridiculous ball of SQL
        # inside mint/projectlisting.py. Here there be dragons. --sgp
        innerWhereClause = outerWhereClause = ""
        if not includeInactive:
            innerWhereClause = "WHERE hidden=0"
        if self.cfg.hideFledgling and not includeInactive:
            outerWhereClause = "WHERE (fledgling=0 OR external=1)"

        # audited for sql injection. this is safe only because the params to
        # this function are ensured to be ints by mintServer typeChecking.
        SQL = projectlisting.sqlbase % (innerWhereClause, outerWhereClause,
            projectlisting.ordersql[sortOrder])
        cu.execute(SQL, limit, offset)

        ids = []
        for x in cu.fetchall():
            ids.append(list(x))

            # cast id and timestamp to int
            ids[-1][0] = int(ids[-1][0])
            ids[-1][4] = int(ids[-1][4])
            if len(ids[-1][projectlisting.descindex]) > projectlisting.desctrunclength:
                ids[-1][projectlisting.descindex] = ids[-1][projectlisting.descindex][:projectlisting.desctrunclength] + "..."

        return ids

    def search(self, terms, modified, limit, offset, includeInactive=False):
        """
        Returns a list of projects matching L{terms} of length L{limit}
        starting with item L{offset}.
        @param terms: Search terms
        @param modified: Code for the period within which the project must have been modified to include in the search results.
        @param offset: Count at which to begin listing
        @param limit:  Number of items to return
        @param includeInactive:  Include hidden and fledgling projects
        @return:       a dictionary of the requested items.
                       each entry will contain four bits of data:
                        The hostname for use with linking,
                        The project name,
                        The project's description
                        The date last modified.
        """
        columns = ['projectId', 'hostname', 'name', 'description',
                   """IFNULL(
                       (SELECT MAX(Commits.timestamp) FROM Commits
                       WHERE Commits.projectId=Projects.projectId),
                   Projects.timeCreated) AS timeModified"""]
        searchcols = ['name', 'description', 'hostname']

        if includeInactive:
            whereClause = searcher.Searcher.where(terms, searchcols)
        else:
            whereClause = searcher.Searcher.where(terms, searchcols, "AND hidden=0")

        ids, count = database.KeyedTable.search(self, columns, 'Projects',
                whereClause,
                searcher.Searcher.order(terms, searchcols, 'UPPER(name)'),
                searcher.Searcher.lastModified('timeModified', modified),
                limit, offset)
        for i, x in enumerate(ids[:]):
            ids[i] = list(x)
            ids[i][2] = searcher.Searcher.truncate(x[2], terms)

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
        db.close()

        repos = netserver.NetworkRepositoryServer(cfg, '')

        if username:
            repos.auth.addUser(username, password)
            repos.auth.addAcl(username, None, None, True, False,
                              self.cfg.projectAdmin)

        repos.auth.addUser("anonymous", "anonymous")
        repos.auth.addAcl("anonymous", None, None, False, False, False)

        # add the mint auth user so we can add additional permissions
        # to this repository
        repos.auth.addUser(self.cfg.authUser, self.cfg.authPass)
        repos.auth.addAcl(self.cfg.authUser, None, None, True, False, True)
        repos.auth.setMirror(self.cfg.authUser, True)
        if username:
            repos.auth.setMirror(username, True)

    def hide(self, projectId):
        # Anonymous user is added/removed in server
        cu = self.db.cursor()

        cu.execute("UPDATE Projects SET hidden=1, timeModified=? WHERE projectId=?", time.time(), projectId)
        cu.execute("DELETE FROM PackageIndex WHERE projectId=?", projectId)
        self.db.commit()

    def unhide(self, projectId):
        # Anonymous user is added/removed in server
        cu = self.db.cursor()

        cu.execute("UPDATE Projects SET hidden=0, timeModified=? WHERE projectId=?", time.time(), projectId)
        self.db.commit()

    def isHidden(self, projectId):
        cu = self.db.cursor()
        cu.execute("SELECT IFNULL(hidden, 0) from Projects WHERE projectId=?", projectId)
        return cu.fetchone()[0]

class LabelsTable(database.KeyedTable):
    name = 'Labels'
    key = 'labelId'

    createSQL = """CREATE TABLE Labels (
                    labelId         %(PRIMARYKEY)s,
                    projectId       INT,
                    label           VARCHAR(255),
                    url             VARCHAR(255),
                    username        VARCHAR(255),
                    password        VARCHAR(255)
                )"""

    fields = ['labelId', 'projectId', 'label', 'url', 'username', 'password']

    indexes = {"LabelsPackageIdx": """CREATE INDEX LabelsPackageIdx
                                          ON Labels(projectId)"""}

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

    def getLabelsForProject(self, projectId,
            overrideAuth = False, newUser = '', newPass = ''):
        cu = self.db.cursor()

        cu.execute("""SELECT l.labelId, l.label, l.url, l.username, l.password,
                             p.external
                      FROM Labels l, Projects p
                      WHERE p.projectId=? AND l.projectId=p.projectId""",
                      projectId)

        repoMap = {}
        labelIdMap = {}
        userMap = {}
        for labelId, label, url, username, password, external in cu.fetchall():
            if overrideAuth:
                username = newUser
                password = newPass

            labelIdMap[label] = labelId
            host = label[:label.find('@')]
            if url:
                if username and password:
                    if not external:
                        if self.cfg.SSL:
                            protocol = "https"
                            newHost, newPort = hostPortParse(self.cfg.secureHost, 443)
                        else:
                            protocol = "http"
                            newHost, newPort = hostPortParse(self.cfg.projectDomainName, 80)

                        url = rewriteUrlProtocolPort(url, protocol)

                map = url
            else:
                map = "http://%s/conary/" % (host)

            repoMap[host] = map
            userMap[host] = (username, password)

        return labelIdMap, repoMap, userMap

    def getLabel(self, labelId):
        cu = self.db.cursor()
        cu.execute("SELECT label, url, username, password FROM Labels WHERE labelId=?", labelId)

        p = cu.fetchone()
        if not p:
            raise LabelMissing
        else:
            return p[0], p[1], p[2], p[3]

    def addLabel(self, projectId, label, url=None, username=None, password=None):
        cu = self.db.cursor()

        cu.execute("""SELECT count(labelId) FROM Labels WHERE label=? and projectId=?""",
                   label, projectId)
        c = cu.fetchone()[0]
        if c > 0:
            raise DuplicateLabel

        cu.execute("""INSERT INTO Labels (projectId, label, url, username, password)
                      VALUES (?, ?, ?, ?, ?)""", projectId, label, url, username, password)
        self.db.commit()
        return cu._cursor.lastrowid

    def editLabel(self, labelId, label, url, username=None, password=None):
        cu = self.db.cursor()
        cu.execute("""UPDATE Labels SET label=?, url=?, username=?, password=?
                      WHERE labelId=?""", label, url, username, password, labelId)
        self.db.commit()

    def removeLabel(self, projectId, labelId):
        cu = self.db.cursor()

        cu.execute("""SELECT p.troveVersion, l.label
                      FROM Releases p, Labels l
                      WHERE p.projectId=?
                        AND l.projectId=p.projectId
                        AND l.labelId=?""",
                   projectId, labelId)

        for versionStr, label in cu.fetchall():
            if versionStr:
                v = versions.ThawVersion(versionStr)
                if v.branch().label().asString() == label:
                    raise LabelInUse

        cu.execute("""DELETE FROM Labels WHERE projectId=? AND labelId=?""", projectId, labelId)
        return False

class RepositoryDatabase:
    def __init__(self, cfg):
        self.cfg = cfg

    def create(self, name):
        # pre-initialize the cache for test suite purposes
        cache = os.path.dirname("%s/%s/cache.sql" % (self.cfg.reposPath, name))
        if not os.path.exists(cache):
            util.mkdirChain(os.path.dirname(cache))
        from conary.repository.netrepos import cacheset
        cacheset.CacheSet(('sqlite', cache + "/cache.sql"), None)

    def getRepositoryDB(self, name):
        raise NotImplementedError

    def translate(self, x):
        return x


class SqliteRepositoryDatabase(RepositoryDatabase):
    def create(self, name):
        util.mkdirChain(os.path.dirname(self.cfg.reposDBPath % name))
        RepositoryDatabase.create(self, name)

    def getRepositoryDB(self, name):
        return ('sqlite', self.cfg.reposDBPath % name)


class MySqlRepositoryDatabase(RepositoryDatabase):
    def translate(self, x):
        return x.translate(mysqlTransTable)

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
                # raise an error that alomst certainly won't be trapped,
                # so that a traceback will be generated.
                raise AssertionError( \
                    "Attempted to delete an existing project database.")
        cu.execute("CREATE DATABASE %s" % dbName)
        db.close()
        RepositoryDatabase.create(self, name)

    def getRepositoryDB(self, name):
        dbName = self.translate(name)
        return ('mysql', self.cfg.reposDBPath % dbName)

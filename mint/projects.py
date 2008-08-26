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
from mint import database
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
    'sqlite': string.maketrans("", ""),
    'mysql': string.maketrans("-.:", "___"),
    'postgresql': string.maketrans("-.:", "___")
}

class Project(database.TableObject):
    # XXX: the disabled column is slated for removal next schema upgrade --sgp
    __slots__ = ('projectId', 'creatorId', 'name', 'description', 'hostname',
        'domainname', 'namespace', 'projecturl', 'hidden', 'external',
        'isAppliance', 'disabled', 'timeCreated', 'timeModified',
        'commitEmail', 'shortname', 'prodtype', 'version', 'backupExternal')

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
    
    def getNamespace(self):
        return self.namespace

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

    def getShortname(self):
        return self.shortname

    def getProdType(self):
        return self.prodtype

    def getVersion(self):
        return self.version

    def getMembers(self):
        return self.server.getMembersByProjectId(self.id)

    def getCommits(self):
        return self.server.getCommitsForProject(self.id)

    def getCommitEmail(self):
        return self.commitEmail

    def getUserLevel(self, userId):
        try:
            return self.server.getUserLevel(userId, self.id)
        except ItemNotFound:
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

    def setNamespace(self, namespace):
        return self.server.setProjectNamespace(self.id, namespace)

    def setCommitEmail(self, commitEmail):
        return self.server.setProjectCommitEmail(self.id, commitEmail)

    def setBackupExternal(self, backupExternal):
        return self.server.setBackupExternal(self.id, backupExternal)

    def getLabelIdMap(self):
        """Returns a dictionary mapping of label names to database IDs"""
        return self.server.getLabelsForProject(self.id, False, '', '')[0]

    def getConaryConfig(self, overrideAuth = False, newUser = '', newPass = ''):
        '''Creates a ConaryConfiguration object suitable for repository access
        from the same server as MintServer'''

        labelPath, repoMap, userMap, entMap = self.server.getLabelsForProject(self.id, overrideAuth, newUser, newPass)

        cfg = ConaryConfiguration(readConfigFiles=False)
        #cfg.root = ":memory:"
        #cfg.dbPath = ":memory:"

        #cfg.initializeFlavors()
        cfg.buildFlavor = deps.parseFlavor('')

        installLabelPath = " ".join(x for x in labelPath.keys())
        cfg.configLine("installLabelPath %s" % installLabelPath)

        cfg.repositoryMap.update(dict((x[0], x[1]) for x in repoMap.items()))
        for host, authInfo in userMap:
            cfg.user.addServerGlob(host, authInfo[0], authInfo[1])
        for host, entitlement in entMap:
            cfg.entitlement.addEntitlement(host, entitlement[1])

        useInternalConaryProxy, httpProxies = self.server.getProxies()
        cfg = helperfuncs.configureClientProxies(cfg, useInternalConaryProxy,
                httpProxies)
        return cfg

    def addLabel(self, label, url, authType='none', username='', password='', entitlement=''):
        return self.server.addLabel(self.id, label, url, authType, username, password, entitlement)

    def editLabel(self, labelId, label, url, authType, username, password,
            entitlement):
        return self.server.editLabel(labelId, label, url, authType, username,
            password, entitlement)

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

    def getBuilds(self):
        return self.server.getBuildsForProject(self.id)

    def getUnpublishedBuilds(self):
        return self.server.getUnpublishedBuildsForProject(self.id)

    def getPublishedReleases(self):
        return self.server.getPublishedReleasesByProject(self.id)

    def getApplianceValue(self):
        if not self.isAppliance:
            if self.isAppliance == 0:
                return "no"
            else:
                return "unknown"
        else:
            return "yes"

    def getProductVersionList(self):
        return self.server.getProductVersionListForProduct(self.id)

    def getDefaultImageGroupName(self):
        return "group-%s-dist" % self.shortname.lower()

    def resolveExtraTrove(self, specialTroveName, imageGroupVersion,
            imageGroupFlavor, specialTroveVersion='', specialTroveFlavor=''):
        """ 
        Resolves an extra trove for a build. Returns a full TroveSpec
        for that trove if found, or an empty string if not found.

        Note that this function is used to resolve the following troves
        commonly used for builds:
        - I{anaconda-custom}
        - I{anaconda-templates}
        - I{media-template}

        In the case of resolving I{anaconda-templates}, the C{MintConfig}
        parameter I{anacondaTemplatesFallback} is used as the default
        searchPath for the trove if all else fails.

        @param specialTroveName: the name of the special trove (e.g.
            'anaconda-templates')
        @type specialTroveName: C{str}
        @param imageGroupVersion: a frozen Version object for the image
            group intended to be used with the build
        @type imageGroupVersion: C{str} (frozen Version object)
        @param imageGroupFlavor: a frozen Flavor object for the image
            group intended to be used with the build
        @type imageGroupFlavor: C{str} (frozen Flavor object)
        @param specialTroveVersion: (optional) A version of the special trove,
            often a label. If no version is given, the imageGroupVersion is used
            instead.
        @type specialTroveVersion: C{str}
        @param specialTroveFlavor: (optional) A flavor string for the special trove
            (e.g. 'is: x86'). If no flavor string is used, the imageGroupFlavor
            is used instead.
        @type specialTroveVersion: C{str}
        @returns The TroveSpec of the special trove, or an empty string
            if no suitable trove was found.
        @rtype C{str}
        """
        if imageGroupVersion is None:
            imageGroupVersion = ''
        elif hasattr(imageGroupVersion, 'asString'):
            imageGroupVersion = imageGroupVersion.asString()
        if imageGroupFlavor is None:
            imageGroupFlavor = ''
        elif hasattr(imageGroupFlavor, 'freeze'):
            imageGroupFlavor = imageGroupFlavor.freeze()

        if specialTroveVersion is None:
            specialTroveVersion = ''
        elif hasattr(specialTroveVersion, 'asString'):
            specialTroveVersion = specialTroveVersion.asString()
        if specialTroveFlavor is None:
            specialTroveFlavor = ''
        elif hasattr(specialTroveFlavor, 'freeze'):
            specialTroveFlavor = specialTroveFlavor.freeze()

        return self.server.resolveExtraTrove(self.id,
                specialTroveName, specialTroveVersion, specialTroveFlavor,
                imageGroupVersion, imageGroupFlavor)

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
                        'postgresql':  PostgreSqlRepositoryDatabase
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
            timePublished   DOUBLE)""")

        cu.execute("""INSERT INTO tmpLatestReleases (projectId, timePublished)
            SELECT projectId as projectId, MAX(timePublished) AS timePublished FROM PublishedReleases
            GROUP BY projectId""")

        self.db.commit()

        # extract a list of build types to search for.
        # these are additive, unlike other search limiters.
        buildTypes = []
        flavorFlagTypes = []
        terms, limiters = searcher.parseTerms(terms)
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
        db.close()

        repos = netserver.NetworkRepositoryServer(cfg, '')

        if username:
            addUserToRepository(repos, username, password, username)
            repos.auth.addAcl(username, None, None, write=True, remove=False)
            repos.auth.setAdmin(username, True)

        anon = "anonymous"
        addUserToRepository(repos, anon, anon, anon)
        repos.auth.addAcl(anon, None, None, write=False, remove=False)

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

                    url = rewriteUrlProtocolPort(url, protocol)

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

    def addLabel(self, projectId, label, url=None, authType='none',
            username=None, password=None, entitlement=None):
        cu = self.db.cursor()

        cu.execute("""SELECT count(labelId) FROM Labels WHERE label=? and projectId=?""",
                   label, projectId)
        c = cu.fetchone()[0]
        if c > 0:
            raise DuplicateLabel

        cu.execute("""INSERT INTO Labels (projectId, label, url, authType,
            username, password, entitlement)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", projectId, label, url,
                    authType, username, password, entitlement)
        self.db.commit()
        return cu._cursor.lastrowid

    def editLabel(self, labelId, label, url, authType='none',
            username=None, password=None, entitlement=None):
        cu = self.db.cursor()
        cu.execute("""UPDATE Labels SET label=?, url=?, authType=?,
            username=?, password=?, entitlement=? WHERE labelId=?""",
            label, url, authType, username, password, entitlement, labelId)
        self.db.commit()

    def removeLabel(self, projectId, labelId):
        cu = self.db.cursor()

        cu.execute("""DELETE FROM Labels WHERE projectId=? AND labelId=?""", projectId, labelId)
        return False


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
            print >> sys.stderr, "using alternate database:", r[0], r[1]
            sys.stderr.flush()
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


class PostgreSqlRepositoryDatabase(RepositoryDatabase):
    tableOpts = "ENCODING 'UTF8'"
    driver = 'postgresql'

    def translate(self, x):
        return x.translate(transTables['postgresql'].lower())

    def create(self, name):
        path = self.cfg.reposDBPath % 'postgres'
        db = dbstore.connect(path, 'postgresql')

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

                reposDb = dbstore.connect(self.cfg.reposDBPath % dbName.lower(),
                                          'postgresql')
                reposDb.loadSchema()
                reposCu = reposDb.cursor()
                tableList = []
                for t in reposDb.tempTables:
                    reposCu.execute("DROP TABLE %s" % (t,))
                for t in reposDb.tables:
                    reposCu.execute("DROP TABLE %s CASCADE" % (t,))
                reposDb.close()
            else:
                # raise an error that alomst certainly won't be trapped,
                # so that a traceback will be generated.
                raise AssertionError( \
                    "Attempted to delete an existing %s database."%getProjectText().lower())
        if createDb:
            cu.execute("CREATE DATABASE %s %s" % (dbName, self.tableOpts))
        db.close()
        RepositoryDatabase.create(self, name)

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
                # raise an error that alomst certainly won't be trapped,
                # so that a traceback will be generated.
                raise AssertionError( \
                    "Attempted to delete an existing %s database."%getProjectText().lower())
        cu.execute("CREATE DATABASE %s %s" % (dbName, self.tableOpts))
        db.close()
        RepositoryDatabase.create(self, name)

class ProductVersions(database.TableObject):

    __slots__ = ( 'productVersionId',
                  'projectId',
                  'namespace',
                  'name',
                  'description',
                )

    def getItem(self, id):
        return self.server.getProductVersion(id)

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


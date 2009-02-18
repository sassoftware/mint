import time

from mint import userlevels
from mint.rest.db import reposmgr

# FIXME - really shouldn't be any SQL in this file.

class ProductManager(object):
    def __init__(self, cfg, db, server, publisher=None):
        self.cfg = cfg
        self.db = db
        self.server = server
        self.reposMgr = reposmgr.RepositoryManager(cfg, self.db.projects.reposDB)
        self.publisher = publisher

    def createProduct(self, name, description, hostname,
                      domainname, namespace, isAppliance,
                      projecturl, shortname, prodtype,
                      commitEmail, isPrivate):
        # All database operations must abort cleanly, especially when
        # creating the repository fails. Otherwise, we'll end up with
        # a completely broken project that may not even delete cleanly.
        #
        # No database operation inside this block may commit the
        # transaction.
        self.db.transaction()
        try:
            createTime = time.time()
            projectId = self.db.projects.new(
                name=name,
                creatorId=self.server.userId, 
                description=description, 
                hostname=hostname,
                domainname=domainname, 
                namespace=namespace,
                isAppliance=isAppliance, 
                projecturl=projecturl,
                timeModified=createTime, 
                timeCreated=createTime,
                shortname=shortname, 
                prodtype=prodtype, 
                commitEmail=commitEmail, 
                hidden=isPrivate,
                commit=False)

            # add to RepNameMap if projectDomainName != domainname
            fqdn = ".".join((hostname, domainname))
            projectDomainName = self.cfg.projectDomainName.split(':')[0]
            if domainname != projectDomainName:
                self.db.repNameMap.new(fromName='%s.%s' % (hostname, projectDomainName),
                                       toName=fqdn, commit=False)
            self.db.labels.addLabel(projectId, fqdn + '@rpl:1',
                "http://%s%srepos/%s/" % (
                self.cfg.projectSiteHost, self.cfg.basePath, hostname),
                authType='userpass', username=self.cfg.authUser, password=self.cfg.authPass, commit=False)


            # add to RepNameMap if projectDomainName != domainname
            projectDomainName = self.cfg.projectDomainName.split(':')[0]
            if domainname != projectDomainName:
                self.db.repNameMap.new(fromName='%s.%s' % (hostname, projectDomainName),
                                       toName=fqdn, commit=False)
            self.reposMgr.createRepository(hostname, domainname, isPrivate=isPrivate)
            # have to set member level after the repository is set up right so the 
            self.setMemberLevel(projectId, self.server.userId, userlevels.OWNER)
        except:
            self.db.rollback()
            raise
        self.db.commit()
        self.publisher.notify('ProjectCreated', self.server.auth, projectId)
        return projectId

    def isMember(self, projectId, userId):
        cu = self.db.cursor()
        cu.execute("""SELECT level FROM ProjectUsers
                      WHERE projectId = ? AND userId = ?""",
                      projectId, userId)
        if cu.fetchone():
            return True
        return False

    def _getPassword(self, userId):
        cu = self.db.cursor()
        cu.execute('SELECT passwd, salt from Users where userId=?', userId)
        return cu.next()

    def setMemberLevel(self, projectId, userId, level):
        fqdn = self.server.getProductFQDN(projectId)
        username = self.server.getUsername(userId)
        isMember = self.isMember(projectId, userId)
        write = level in userlevels.WRITERS
        mirror = level == userlevels.OWNER
        admin = level == userlevels.OWNER and self.cfg.projectAdmin

        self.db.transaction()
        try:
            if isMember:
                if self.db.projectUsers.onlyOwner(projectId, userId) and \
                       (level != userlevels.OWNER):
                    raise users.LastOwner
                cu = self.db.cursor()

                cu.execute("""UPDATE ProjectUsers SET level=? WHERE userId=? 
                              AND projectId=?""", level, userId, projectId)
                self.reposMgr.editUser(fqdn, username, write=write,
                                       mirror=mirror, admin=admin)
            else:
                password, salt = self._getPassword(userId)
                self.db.projectUsers.new(userId=userId, projectId=projectId,
                                      level=level, commit=False)
                self.reposMgr.addUserByMd5(fqdn, username, salt, password, 
                                           write=True,
                                           mirror=True, admin=admin)
        except:
            self.db.rollback()
            raise
        self.db.commit()
        if isMember:
            self.publisher.notify('UserProjectChanged', self.server.auth, 
                                  userId, projectId, level)
            return False
        else:
            self.publisher.notify('UserProjectAdded', self.server.auth, 
                                  userId, projectId, level)
            return True

    def removeMember(self, projectId, userId):
        fqdn = self.server.getProductFQDN(projectId)
        username = self.server.getUsername(userId)
        if self.db.projectUsers.onlyOwner(projectId, userId):
            raise users.LastOwner
        self.reposMgr.deleteUser(fqdn, username)
        self.db.projectUsers.delete(projectId, userId)
        self.publisher.notify('UserProjectRemoved', self.server.auth, userId, 
                              projectId)

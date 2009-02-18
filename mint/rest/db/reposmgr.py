import os

from conary import dbstore
from conary.lib import util
from conary.repository import errors
from conary.repository.netrepos import netserver
from conary.server import schema

class RepositoryManager(object):
    def __init__(self, cfg, reposDB):
        self.cfg = cfg
        self.reposDB = reposDB

    def _getRepositoryServer(self, fqdn):
        dbPath = os.path.join(self.cfg.reposPath, fqdn)
        tmpPath = os.path.join(dbPath, 'tmp')
        cfg = netserver.ServerConfig()
        cfg.repositoryDB = self.reposDB.getRepositoryDB(fqdn)
        cfg.tmpDir = tmpPath
        cfg.serverName = fqdn
        cfg.repositoryMap = {}

        contentsDirs = self.cfg.reposContentsDir
        cfg.contentsDir = " ".join(x % fqdn for x in contentsDirs.split(" "))
        repos = netserver.NetworkRepositoryServer(cfg, '')
        return repos
        
    def createRepository(self, hostname, domainname, isPrivate=False):
        fqdn = "%s.%s" % (hostname, domainname)
        dbPath = os.path.join(self.cfg.reposPath, fqdn)
        tmpPath = os.path.join(dbPath, 'tmp')
        util.mkdirChain(tmpPath)
        self.reposDB.create(fqdn)

        repositoryDB =  self.reposDB.getRepositoryDB(fqdn)
        db = dbstore.connect(repositoryDB[1], repositoryDB[0])
        schema.loadSchema(db)
        db.commit()
        db.close()

        if not isPrivate:
            self.addUser(fqdn, 'anonymous', password='anonymous')

        # add the auth user so we can add additional permissions
        # to this repository
        self.addUser(fqdn, self.cfg.authUser, 
                     password=self.cfg.authPass,
                     write=True, mirror=True, admin=True)

    def deleteRepository(self, fqdn):
        self.reposDB.delete(projectFQDN)

    def addUserByMd5(self, fqdn, username, salt, password, 
                     write=False, mirror=False,
                     admin=False):
        repos = self._getRepositoryServer(fqdn)
        try:
            repos.auth.addUserByMD5(username, salt, password)
        except errors.UserAlreadyExists:
            repos.auth.deleteUserByName(username)
            repos.auth.addUserByMD5(username, salt, password)
        self._setUserPermissions(fqdn, username, write=write, 
                                 mirror=mirror, admin=admin)

    def addUser(self, fqdn, username, password, write=False, mirror=False,
                admin=False):
        repos = self._getRepositoryServer(fqdn)
        try:
            repos.auth.addUser(username, password)
        except errors.UserAlreadyExists:
            repos.auth.deleteUserByName(username)
            repos.auth.addUser(username, password)

        self._setUserPermissions(fqdn, username, write=write, 
                                 mirror=mirror, admin=admin)

    def editUser(self, fqdn, username, write=False, mirror=False,
                 admin=False):
        repos = self._getRepositoryServer(fqdn)
        self._setUserPermissions(fqdn, username, write=write, 
                                 mirror=mirror, admin=admin)

    def deleteUser(self, fqdn, username):
        repos = self._getRepositoryServer(fqdn)
        repos.auth.deleteUserByName(username)
        try:
            # TODO: This will go away when using role-based permissions
            # instead of one-role-per-user. Without this, admin users'
            # roles would not be deleted due to CNY-2775
            repos.auth.deleteRole(username)
        except errors.RoleNotFound:
            # Conary deleted the (unprivileged) role for us
            pass

    def changePassword(self, repos, username, password):
        repos = self._getRepositoryServer(fqdn)
        repos.auth.changePassword(username, newPassword)

    def _setUserPermissions(self, fqdn, username, write=False, mirror=False,
                            admin=False):

        repos = self._getRepositoryServer(fqdn)

        # create a role with the same name as this user
        # with the permissions we want.
        role = username
        try:
            repos.auth.addRole(role)
        except errors.RoleAlreadyExists:
            repos.auth.editAcl(role, None, None, None, None,
                               write=write, canRemove=False)
        else:
            repos.auth.addAcl(role, trovePattern=None, label=None, 
                              write=write, remove=False)
            repos.auth.addRoleMember(role, username)
        repos.auth.setMirror(role, mirror)
        repos.auth.setAdmin(role, admin)

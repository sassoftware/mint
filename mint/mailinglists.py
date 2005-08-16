#
# Copyright (c) 2005 rpath, Inc.
#
# All rights reserved
#
import xmlrpclib
from mint_error import MintError

(PROJECT, PROJECT_COMMITS, PROJECT_DEVEL, PROJECT_BUGS) = range(0, 4)

defaultlists = [ PROJECT, PROJECT_COMMITS, ]

optionallists = [ PROJECT_DEVEL, PROJECT_BUGS, ]

listnames = {
    PROJECT:        "%s",
    PROJECT_COMMITS:"%s-commits",
    PROJECT_DEVEL:  "%s-devel",
    PROJECT_BUGS:   "%s-bugs",
}

listdesc = {
    PROJECT:        "General discussion of the %s project",
    PROJECT_COMMITS:"Commits to the %s repository",
    PROJECT_DEVEL:  "Technical discussion about the development of %s",
    PROJECT_BUGS:   "Bug reports/summaries for %s",
}

listmoderation = {
    PROJECT:        False,
    PROJECT_COMMITS:True,
    PROJECT_DEVEL:  False,
    PROJECT_BUGS:   True,
}

def GetLists(projectName, lists):
    returner = {}
    for item in lists:
        returner[listnames[item]%projectName] = {
                'description' : listdesc[item]%projectName,
                'moderate' : listmoderation[item]
            }
    return returner

def DefaultLists(projectName):
    return  GetLists(defaultlists)

class MailingListException(MintError):
    def __init__(self, mesg):
        self.mesg = mesg

    def __str__(self):
        return self.mesg

class MailingListClient:
    def __init__(self, server):
        """
        @param server: URL to the mailing list server's XMLRPC interface
        """
        self.server = xmlrpclib.ServerProxy(server)

    def list_lists(self, projectName):
        """
        Lists the mailing lists matching L{projectName} on the mailing list
        server.
        @param projectName: name of the project from which to list lists.
        """
        class listobj: pass
        pcre = "^%s$|^%s-" % (projectName, projectName)
        lists = self._servercall(self.server.list_lists(pcre))
        returner = []
        for listname in lists:
            list = listobj()
            list.name = listname
            list.description = self._servercall(self.server.description(listname))
            returner.append(list)
        return returner

    def add_list(self, adminpw, listname, listpw, description, owners, notify=True, moderate=False):
        listpw = self._servercall(self.server.add_list(adminpw, listname, owners, listpw, notify, moderate))
        if not listpw:
            return False
        else:
            return self._servercall(self.server.set_list_settings(listname, listpw, {'description': description}))
            

    def delete_list(self, password, listname, delarchives = True):
        return self._servercall(self.server.delete_list(password, listname, delarchives))

    def set_owners(self, listname, listpw, owners=[]):
        return self._servercall(self.server.set_owners(listname, listpw, {'owner' :owners}))

    def orphan_lists(self, password, projectname):
        lists = self.list_lists(projectname)
        settings = {
            ### XXX Come up with orphanage settings
                'emergency': 1,
                'member_moderation_action': 1,
                'generic_nonmember_action': 2,
                'member_moderation_notice': "This list has been disabled because the project to which it belongs has been orphaned.  Please visit the project's web page if you wish to adopt this project and take control of its mailing lists."
            }
        for list in lists:
            if not self._servercall(self.server.get_owner(list.name,password)):
                self._servercall(self.server.set_list_settings(list.name, password, settings))
                self.reset_list_password(list.name, password)
        return True

    def adopt_lists(self, auth, password, projectname):
        lists = self.list_lists(projectname)
        settings = {
                'emergency': 0,
                'member_moderation_action': 0,
                'generic_nonmember_action': 1,
                'member_moderation_notice': "",
                'owner': [auth.email]
            }
        for list in lists:
            self._servercall(self.server.set_list_settings(list.name, password, settings))
            self.reset_list_password(list.name, password)

    def reset_list_password(self, list, password, newpasswd=''):
        return self._servercall(self.server.reset_password(list, password, newpasswd))

    def _servercall(self, returnvalue):
        if returnvalue[0]:
            raise Exception(returnvalue[1])
        else:
            return returnvalue[1]


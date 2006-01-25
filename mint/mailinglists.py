#
# Copyright (c) 2005-2006 rPath, Inc.
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

    def list_all_lists(self):
        lists = self.server.Mailman.listAdvertisedLists()
        lists.remove('mailman')
        return lists

    def list_lists(self, projectName):
        """
        Lists the mailing lists matching L{projectName} on the mailing list
        server.
        @param projectName: name of the project from which to list lists.
        """
        class listobj: pass
        pcre = "^%s$|^%s-" % (projectName, projectName)
        lists = self.server.Mailman.listAdvertisedLists(pcre)
        returner = []
        for listname, description in lists:
            list = listobj()
            list.name = listname
            list.description = description
            returner.append(list)
        return returner

    def add_list(self, adminpw, listname, listpw, description, owners, notify=True, moderate=False, domain=''):
        listpw = self.server.Mailman.createList(adminpw, listname,
            domain, moderate, owners, listpw, notify, ['en'])
        if not listpw:
            return False
        else:
            return self.server.Mailman.setOptions(listname, listpw, {'description': description})

    def delete_list(self, adminpw, listname, delarchives = True):
        return self.server.Mailman.deleteList(adminpw, listname, delarchives)

    def set_owners(self, listname, listpw, owners=[]):
        return self.server.Mailman.setOptions(listname, listpw, {'owner' :owners})

    def get_owners(self, listname, listpw):
        return self.server.Mailman.getOptions(listname, listpw, ['owner'])['owner']

    def orphan_lists(self, adminpw, projectname):
        lists = self.list_lists(projectname)
        settings = {
            ### XXX Come up with orphanage settings
                'emergency': 1,
                'member_moderation_action': 1,
                'generic_nonmember_action': 2,
                'member_moderation_notice': "This list has been disabled because the project to which it belongs has been orphaned.  Please visit the project's web page if you wish to adopt this project and take control of its mailing lists."
            }
        for list in lists:
            if not self.get_owners(list.name, adminpw):
                self.server.Mailman.setOptions(list.name, adminpw, settings)
                self.server.Mailman.resetListPassword(list.name, adminpw, '')
        return True

    def adopt_lists(self, auth, adminpw, projectname):
        lists = self.list_lists(projectname)
        settings = {
                'emergency': 0,
                'member_moderation_action': 0,
                'generic_nonmember_action': 1,
                'member_moderation_notice': "",
                'owner': [auth.email]
            }
        for list in lists:
            self.server.Mailman.setOptions(list.name, adminpw, settings)
            self.server.Mailman.resetListPassword(list.name, adminpw, '')

    def reset_list_password(self, listname, adminpw):
        return self.server.Mailman.resetListPassword(listname, adminpw, '')


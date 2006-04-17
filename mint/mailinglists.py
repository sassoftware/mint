#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
import re
import sys
import xmlrpclib

from mint.mint_error import MintError

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
        try:
            lists = self.server.Mailman.listAdvertisedLists()
        except:
            raise MailingListException("Mailing List Error")
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
        try:
            lists = self.server.Mailman.listAdvertisedLists(pcre)
        except:
            raise MailingListException("Mailing List Error")
        returner = []
        for listname, description in lists:
            list = listobj()
            list.name = listname
            list.description = description
            returner.append(list)
        return returner

    def add_list(self, adminpw, listname, listpw, description, owners, notify=True, moderate=False, domain=''):
        try:
            listpw = self.server.Mailman.createList(adminpw, listname,
                domain, moderate, owners, listpw, notify, ['en'])
        except:
            exc_data = sys.exc_info()
            if not re.search("Errors\.BadListNameError", str(exc_data)):
                raise MailingListException("Mailing List Error")
        if not listpw:
            return False
        else:
            try:
                return self.server.Mailman.setOptions(listname, listpw, {'description': description})
            except:
                raise MailingListException("Mailing List Error")

    def delete_list(self, adminpw, listname, delarchives = True):
        try:
            return self.server.Mailman.deleteList(adminpw, listname, delarchives)
        except:
            raise MailingListException("Mailing List Error")

    def set_owners(self, listname, listpw, owners=[]):
        try:
            return self.server.Mailman.setOptions(listname, listpw, {'owner' :owners})
        except:
            raise MailingListException("Mailing List Error")

    def get_owners(self, listname, listpw):
        try:
            return self.server.Mailman.getOptions(listname, listpw, ['owner'])['owner']
        except:
            raise MailingListException("Mailing List Error")

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
                try:
                    self.server.Mailman.setOptions(list.name, adminpw, settings)
                except:
                    raise MailingListException("Mailing List Error")
                try:
                    self.server.Mailman.resetListPassword(list.name, adminpw, '')
                except:
                    raise MailingListException("Mailing List Error")
        return True

    def adopt_lists(self, auth, adminpw, projectname):
        lists = self.list_lists(projectname)
        settings = {
                'emergency': 0,
                'member_moderation_action': 0,
                'generic_nonmember_action': 2, # refuse all nonmember posts
                'member_moderation_notice': "",
                'owner': [auth.email]
            }
        for list in lists:
            try:
                self.server.Mailman.setOptions(list.name, adminpw, settings)
            except:
                raise MailingListException("Mailing List Error")
            try:
                self.server.Mailman.resetListPassword(list.name, adminpw, '')
            except:
                raise MailingListException("Mailing List Error")

    def reset_list_password(self, listname, adminpw):
        try:
            return self.server.Mailman.resetListPassword(listname, adminpw, '')
        except:
            raise MailingListException("Mailing List Error")


#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

class MailInterface:
    """Interface to mailman."""
    def newList(self, hostname, listName, adminEmails):
        """
        Request that a new list be created: <hostname>-<listName>
        @param hostname: the project hostname
        @type hostname: str
        @param listName: the name of the requested list
        @type listName: str
        @param adminEmails: a list of initial mailing list administrators
        @type adminEmails: list
        """
        pass

    def projectOrphaned(self, hostname):
        """
        Signal that a project identified by L{hostname} has been orphaned,
        to set all of its lists read-only.
        @param hostname: the project hostname
        @type hostname: str
        """
        pass

    def projectAdopted(self, hostname, adminEmails):
        """
        Signal that a project identified by L{hostname} has been adopted,
        to set its lists read-write, and set the lists' adminstrators to
        L{adminEmails}.
        @param hostname: the project hostname
        @type hostname: str
        @param adminEmails: list of new mailing list administrators
        @type adminEmails: list
        """
        pass

    def resetAdminPass(self, hostname):
        """
        Reset the administator password for a set of project lists.
        @param hostname: the project hostname
        @type hostname: str
        """
        pass

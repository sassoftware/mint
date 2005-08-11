#!/usr/bin/python

# This script requires the pythonpath to include the mailman directory
# Mailman is installed to /var/mailman by default

import sys
import getopt

from Mailman import Utils, MailList, Errors, mm_cfg

class InvalidSetting(Exception):
    def __init__(self, list = "list", errors = []):
        self.list = list
        self.errors = errors

    def __str__(self):
        returner = "InvalidSetting: %s" % self.list
        for i in self.errors:
            returner += "\n\t%s" % i
        return returner


PrivateArchiveError = """Archives cannot be made private"""

ArchiveConfigurationError = """Reduce the maximum message size below 2048K or disable archiving"""

NotAdvertisedError = """Mailing lists must be advertised"""

InvalidSubscriptionPolicy = """Mailing lists may not require approval for subscription"""

def checkVals(mlist):
    errors = []
    if mlist.archive_private == True:
        errors.append( PrivateArchiveError )

    if mlist.max_message_size > 2048 and mlist.archive:
        errors.append( ArchiveConfigurationError )

    if not mlist.advertised:
        errors.append( NotAdvertisedError )

    if mlist.subscribe_policy not in [1]:
        errors.append( InvalidSubscriptionPolicy )

    if errors:
        raise InvalidSetting(list = mlist.real_name, errors=errors)
    return True

def setVals(mlist):
    print "Setting values"
    mlist.Lock()
    mlist.archive_private = False
    mlist.max_message_size = 2048
    mlist.advertised = True
    mlist.subscribe_policy = 1
    mlist.Save()
    mlist.Unlock()


def usage(code, msg=''):
    if code:
        out = sys.stderr
    else:
        out = sys.stdout
    print >> out, """
mmsettingspolicy.py: Set the policy for mailing lists on this machine
"""
    sys.exit(code)

def main():
    listnames = Utils.list_names()

    for listname in listnames:
        #ignore "mailman" list
        if listname != 'mailman':
            try:
                mlist = MailList.MailList(listname, lock=0)
            except Errors.MMListError, e:
                print >>sys.stderr, 'No such list "%s"' % listname
                continue
            try:
                checkVals(mlist)
            except InvalidSetting, e:
                ##Some kind of error reporting.  For now just output to stderr
                print >>sys.stderr, str(e)
                sys.stderr.flush()
                #Now set the values
                setVals(mlist)

if __name__ == '__main__':
    main()

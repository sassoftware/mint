#!python

# This script requires the pythonpath to include the mailman directory
# Mailman is installed to /var/mailman by default

import sys, getopt
import xmlrpclib

from Mailman import MailList, Utils

def FixOwners(mlist, minturl):
    mlist.Lock()
    projectname = mlist._internal_name
    idx = projectname.find('-')
    if idx != -1:
        projectname = projectname[0:idx]
    server = xmlrpclib.ServerProxy(minturl)
    owners = server.getOwnersByProjectName(projectname)
    if owners:
        #Set the project owners to be list owners
        mlist.owner = [x[1] for x in owners]
    else:
        #set the list read only.  See mint/mailinglists.py for the
        #current settings
        mlist.emergency = 1
        mlist.member_moderation_action = 2
        mlist.generic_nonmember_action = 2
        mlist.member_moderation_notice = """
This list has been disabled because the project to which it belongs
has been orphaned.  Please visit the project's web page if you wish
to adopt this project and take control of its mailing lists.
"""
    #Now save the list
    mlist.Save()
    mlist.Unlock()

def usage(code, msg=''):
    if code:
        out = sys.stderr
    else:
        out = sys.stdout
    print >>out, """
Usage: fixowners.py -U <MintRPCInterface>
"""

def main():
    xmlrpcurl = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'U:h?', ['URL=', 'help'])
    except getopt.error, msg:
        usage(1, msg)

    for opt, arg in opts:
        if opt in ('-U', '--URL'):
            xmlrpcurl = arg
        elif opt in ('-h', '--help', '-?')
            usage(0)

    listnames = Utils.list_names()

    for listname in listnames:
        #ignore the mailman list
        if listname != 'mailman':
           try:
                mlist = MailList.MailList(listname, lock=0)
            except Errors.MMListError, e:
                print >>sys.stderr, 'No such list "%s"' % listname
                continue
            if not mlist.owner:
                # XXX: Do real error reporting
                print >>sys.stderr, "No owners for %s" % listname
                FixOwners(mlist, xmlrpcurl) 

if __name__ == '__main__':
    main()

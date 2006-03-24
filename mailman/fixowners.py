#!/usr/bin/python

# This script requires the pythonpath to include the mailman directory
# Mailman is installed to /var/mailman by default

import sys, getopt, os
import xmlrpclib
from fixownersconfig import FixOwnersConfig

from Mailman import MailList, Utils, Errors

def FixOwners(cfg, mlist, minturl):
    projectname = mlist._internal_name
    idx = projectname.find('-')
    if idx != -1:
        projectname = projectname[0:idx]
    server = xmlrpclib.ServerProxy(minturl)
    try:
        error, owners = server.getOwnersByProjectName(projectname)
        if error:
            raise Exception(owners)
    except Exception, e:
        print >>sys.stderr, "Error retrieving the project owners for %s: %s"%(projectname, e)
        return False
    try:
        mlist.Lock()
        if owners:
            #Set the project owners to be list owners
            mlist.owner = [x[1] for x in owners]
            mlist.emergency = 0
            mlist.member_moderation_action = 0
            mlist.generic_nonmember_action = 1
            mlist.member_moderation_notice = ""
        else:
            #set the list read only.  See mint/mailinglists.py for the
            #current settings
            mlist.emergency = 1
            mlist.member_moderation_action = 1
            mlist.generic_nonmember_action = 2
            mlist.member_moderation_notice = """
This list has been disabled because the project to which it belongs
has been orphaned.  Please visit the project's web page if you wish
to adopt this project and take control of its mailing lists.
"""
        #Now save the list
        mlist.Save()
    finally:
        mlist.Unlock()

def usage(code, msg=''):
    if code:
        out = sys.stderr
    else:
        out = sys.stdout
    print >>out, """
Usage: fixowners.py -U <MintRPCInterface>
"""
    sys.exit(code)

def main():
    cfg = FixOwnersConfig()
    xmlrpcurl = None
    cfgFile = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'C:U:h?', ['config=', 'URL=', 'help'])
    except getopt.error, msg:
        usage(1, msg)

    for opt, arg in opts:
        if opt in ('-C', '--config'):
            cfgFile = arg
        elif opt in ('-U', '--URL'):
            xmlrpcurl = arg
        elif opt in ('-h', '--help', '-?'):
            usage(0)

    if cfgFile is None:
        cfgFile = 'fixowners.conf'
        if not os.access(cfgFile, os.R_OK) or not os.path.isfile(cfgFile):
            cfgFile = None
    if not cfgFile is None:
        cfg.read(cfgFile)

    if xmlrpcurl is None:
        if not cfg.privateUrl:
            usage(1, "you must specify the URL either on the command line or in the configuration file")
        else:
            xmlrpcurl = cfg.privateUrl

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
               FixOwners(cfg, mlist, xmlrpcurl) 

if __name__ == '__main__':
    main()

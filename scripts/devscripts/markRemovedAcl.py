#!/usr/bin/python

from conary import dbstore
from mint import config
from mint import database

import optparse

cfg = config.MintConfig()
cfg.read(config.RBUILDER_CONFIG)
cfg.read(config.RBUILDER_GENERATED_CONFIG)
cfg.read(config.RBUILDER_GENERATED_CONFIG.replace('generated', 'custom'))

def printAcls(db, userGroup = None):
    cu = db.cursor()
    query = """SELECT userGroup, canRemove
                   FROM Permissions
                   LEFT JOIN UserGroups
                       ON UserGroups.userGroupId=Permissions.userGroupId
                   WHERE userGroup<>?"""
    if userGroup:
        query += " AND userGroup=?"
        cu.execute(query, cfg.authUser, userGroup)
    else:
        cu.execute(query, cfg.authUser)
    for userGroup, canRemove in cu.fetchall():
        print "%s: %s" % (userGroup, canRemove and 'enabled' or 'disabled')

def setAcl(db, userGroup, canRemove):
    """Set the canRemove ACL for a userGroup.

       userGroup is a string.
       canRemove is a boolean."""
    canRemove = int(canRemove)
    cu = db.cursor()
    cu.execute("""SELECT userGroupId
                      FROM UserGroups
                      WHERE userGroup=?
                      AND userGroup<>?""",
               userGroup, cfg.authUser)
    res = cu.fetchall()
    if not res:
        raise database.ItemNotFound('user')
    userGroupId = res[0][0]
    try:
        cu.execute('UPDATE Permissions SET canRemove=? WHERE userGroupId=?',
                   canRemove, userGroupId)
    except:
        db.rollback()
        raise
    else:
        db.commit()

def main():
    usage = "usage: markRemovedAcl.pyc -p <project> [-u <username>] [canRemove]"
    parser = optparse.OptionParser(usage)
    parser.add_option('-p', '--project', dest = 'project',
                      help = "Project Name, as it appears in a URL")

    parser.add_option('-u', '--user', dest = 'user',
                      help = "Username to inspect or manipulate")

    (options, args) = parser.parse_args()

    if not options.project:
        #parser.print_help()
        parser.error("Project is required")

    domainName = options.project + '.' + cfg.projectDomainName

    db = dbstore.connect(cfg.reposDBPath % domainName, cfg.reposDBDriver)

    if not args:
        printAcls(db, options.user)
    elif len(args) == 1:
        answers = ('1', 'TRUE', 'T', 'Y', 'YES', '0', 'FALSE', 'F', 'N', 'NO')
        if args[0].upper() not in answers:
            parser.print_help()
            parser.error("canRemove must be one of: %s" % ', '.join(answers))

        canRemove = args[0].upper() in ('1', 'TRUE', 'T', 'Y', 'YES')
        setAcl(db, options.user, canRemove)

if __name__ == '__main__':
    main()

#!/usr/bin/python

import os, sys

cfgPath = "/srv/mint/mint.conf"

if os.getuid():
    print >> sys.stderr, "Error: %s must be run as root" % sys.argv[0]
    sys.stderr.flush()
    sys.exit(1)

from mint import config
from mint import database
from conary import dbstore
from conary.lib import util

def rmtree(path):
    status("Deleting: %s" % path)
    try:
        return util.rmtree(path)
    except OSError, e:
        if e.errno != 2:
            raise

def status(output):
    print >> sys.stdout, output, ' ' * (78-len(output)), chr(13),
    sys.stdout.flush()

def deleteProject(projectName):
    # properly delete a given project by ensuring we walk the entire schema.
    # this script is verified accurate as of schema version 12.
    global cfg
    db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
    cu = db.cursor()
    print "Deleting Project: %s" % projectName

    cu.execute("""SELECT projectId, hostname, domainname, external 
                  FROM Projects
                  WHERE hostname = ?""", projectName)
    res = cu.fetchone()
    if not res:
        status("Project %s not found in the database; skipping" % projectName)
        print >> sys.stdout, ""
        return

    (projectId, hostname, domainname, external) = res

    projectFQDN = '%s.%s' % (hostname, domainname)

    if not external:
        # step one is to delete the repos database.
        if cfg.reposDBDriver == 'mysql':
            # we need to delete the database manually with a drop database command
            dbName = projectFQDN.replace('.', '_').replace('-','_')
            status("Dropping Database: " + dbName)
            try:
                cu.execute("DROP DATABASE %s" % dbName)
            except dbstore.sqlerrors.DatabaseError, e:
                if e.args[0][1] != 1008:
                    raise

        # delete the actual repos directory
        rmtree(cfg.reposPath + projectFQDN)

    # delete the images directory
    imagesPath = cfg.imagesPath .split('/')[:-1]
    imagesPath.append('images')
    imagesPath.append(projectName)
    imagesPath.insert(0, '/')
    imagesPath = os.path.join(*imagesPath)
    rmtree(imagesPath)

    # delete the finished images directory
    imagesPath = os.path.join(cfg.imagesPath, projectName)
    rmtree(imagesPath)

    status("Deleting Group Troves")
    # get all group trove Ids
    cu.execute("SELECT groupTroveId FROM GroupTroves WHERE projectId=?",
               projectId)
    for groupTroveId in [x[0] for x in cu.fetchall()]:
        # grab appropriate jobs and kill them
        status("Deleting Jobs")
        cu.execute("SELECT jobId FROM Jobs WHERE groupTroveId=?",
                   groupTroveId)
        for jobId in [x[0] for x in cu.fetchall()]:
            cu.execute("DELETE FROM JobData WHERE jobId=?", jobId)
            cu.execute("DELETE FROM Jobs WHERE jobId=?", jobId)
        # now delete all group trove items for that group trove
        cu.execute("DELETE FROM GroupTroveItems WHERE groupTroveId=?",
                   groupTroveId)
    status("Deleting Group Trove Items")
    # then delete all group troves for this project
    cu.execute("DELETE FROM GroupTroves WHERE projectId=?", projectId)

    status("Deleting Releases")
    # now grab all release Ids for this project
    cu.execute("SELECT releaseId FROM Releases WHERE projectId=?",
               projectId)
    for releaseId in [x[0] for x in cu.fetchall()]:
        status("Deleting Jobs")
        # grab appropriate jobs and kill them
        cu.execute("SELECT jobId FROM Jobs WHERE releaseId=?",
                   releaseId)
        for jobId in [x[0] for x in cu.fetchall()]:
            cu.execute("DELETE FROM JobData WHERE jobId=?", jobId)
            cu.execute("DELETE FROM Jobs WHERE jobId=?", jobId)

        status("Deleting Image Files")
        cu.execute("DELETE FROM ImageFiles WHERE releaseId=?", releaseId)
        status("Deleting Release Data")
        cu.execute("DELETE FROM ReleaseData WHERE releaseId=?", releaseId)
        status("Deleting Release Image Types")
        cu.execute("DELETE FROM ReleaseImageTypes WHERE releaseId=?",
                   releaseId)
    # now delete all releases for this project
    cu.execute("DELETE FROM Releases WHERE projectId=?", projectId)

    status("Deleting Labels")
    # delete from all other tables that refer to projectId directly
    cu.execute("DELETE FROM Labels WHERE projectId=?", projectId)
    status("Deleting Membership requests")
    cu.execute("DELETE FROM MembershipRequests WHERE projectId=?",
               projectId)
    status("Deleting Commits")
    cu.execute("DELETE FROM Commits WHERE projectId=?", projectId)
    status("Deleting Package Index")
    cu.execute("DELETE FROM PackageIndex WHERE projectId=?", projectId)
    status("Deleting Project Users")
    cu.execute("DELETE FROM ProjectUsers WHERE projectId=?", projectId)
    status("Deleting Project Entry")
    cu.execute("DELETE FROM Projects WHERE projectId=?", projectId)
    db.commit()
    status('')

global cfg
cfg = config.MintConfig()
cfg.read(cfgPath)

if not sys.argv[1:]:
    print >> sys.stderr, "Usage: %s project [project] [project] ..." % \
          sys.argv[0]
    print >> sys.stderr, "    each project is referred to by short name only."
    print >> sys.stderr, '    for instance "rpath" vice "rPath Linux"'
    sys.stderr.flush()
    sys.exit(1)

print "Executing this script will completely eradicate the following Projects:"
print '\n'.join(sys.argv[1:])
print "If you do not have backups, it will be impossible to recover from this."
print "are you ABSOLUTELY SURE you want to do this? [yes/N]"
answer = sys.stdin.readline()[:-1]
if answer.upper() != 'YES':
    if answer.upper() not in ('', 'N', 'NO'):
        print >> sys.stderr, "you must type 'yes' if you truly want to delete",
        print >> sys.stderr, "these projects."
    print >> sys.stderr, "aborting."
    sys.exit(1)

for projectName in sys.argv[1:]:
    deleteProject(projectName)
print >> sys.stdout, "done."



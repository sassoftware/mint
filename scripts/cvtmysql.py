#!/usr/bin/python

from config import MintConfig
from conary import dbstore
from conary.lib import util
import sys

reload(sys)
sys.setdefaultencoding("utf-8")

sys.excepthook = util.genExcepthook()

srcDb = dbstore.connect("/srv/mint/data/db", "sqlite")
destDb = dbstore.connect("mintauth:mintpass@localhost.localdomain/mint", "mysql")

cfg = MintConfig()
cfg.read('/srv/mint/mint.conf')

def cvt(Table, srcDb, destDb, cfg):
    try:
        srcTable = Table(srcDb)
        destTable = Table(destDb)
    except TypeError:
        srcTable = Table(srcDb, cfg)
        destTable = Table(destDb, cfg)

    print "Converting", srcTable.name
    src = srcDb.cursor()
    dest = destDb.cursor()

    fields = ", ".join(srcTable.fields)
    src.execute("SELECT %s FROM %s" % (fields, srcTable.name))

    for x in src.fetchall():
        values = []
        for key, val in zip(srcTable.fields, x):
            values.append(val)
                
        subs = ", ".join(['?'] * len(values))
        dest.execute("INSERT INTO %s (%s) VALUES (%s)" % (srcTable.name, fields, subs), *values)

from dbversion import VersionTable
from grouptrove import GroupTroveTable, GroupTroveItemsTable
from jobs import JobsTable, ImageFilesTable
from news import NewsCacheTable, NewsCacheInfoTable
from pkgindex import PackageIndexTable
from projects import ProjectsTable, LabelsTable
from users import UsersTable, ProjectUsersTable, UserGroupsTable, UserGroupMembersTable, ConfirmationsTable
from stats import CommitsTable
from requests import MembershipRequestTable
from releases import ReleasesTable
from sessiondb import SessionsTable
from data import JobDataTable, ReleaseDataTable

for t in VersionTable, GroupTroveTable, GroupTroveItemsTable, JobsTable, ImageFilesTable, NewsCacheTable, PackageIndexTable,\
    ProjectsTable, LabelsTable, ReleasesTable, ConfirmationsTable, UsersTable, UserGroupsTable, UserGroupMembersTable, CommitsTable,\
    NewsCacheInfoTable, MembershipRequestTable, SessionsTable, ProjectUsersTable, JobDataTable, ReleaseDataTable:
    cvt(t, srcDb, destDb, cfg)
    

#Commits             JobData             PackageIndex        Test
#Confirmations       Jobs                ProjectUsers        UserGroupMembers
#DatabaseVersion     Labels              Projects            UserGroups
#GroupTroveItems     MembershipRequests  ReleaseData         Users
#GroupTroves         NewsCache           Releases            foo
#ImageFiles          NewsCacheInfo       Sessions



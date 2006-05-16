#!/usr/bin/python

import sys

from conary import dbstore
from conary.lib import util

from mint.config import MintConfig, RBUILDER_CONFIG

reload(sys)
sys.setdefaultencoding("utf-8")

sys.excepthook = util.genExcepthook()

srcDb = dbstore.connect("/srv/rbuilder/data/db", "sqlite")
destDb = dbstore.connect("mintdb:mintdbpass@localhost.localdomain/mint", "mysql")

cfg = MintConfig()
cfg.read(RBUILDER_CONFIG)

fieldExceptions = {}

def checkFields(found, want, tab):
    found = found[:]
    if tab in fieldExceptions:
        for field in fieldExceptions[tab]:
            found.remove(field)
    for field in want:
        found.remove(field)
    if found:
        raise AssertionError("Extra fields: %s\nIn table: %s" \
                             %(str(fields), tab))

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

    if 'key' in srcTable.__dict__ and srcTable.key:
        tableFields = list(set(srcTable.fields) | set([srcTable.key]))
    else:
        tableFields = srcTable.fields
    
    fields = ", ".join(tableFields)
    cu = src.execute("SELECT %s FROM %s" % (fields, srcTable.name))
    dest.execute("DELETE FROM %s" % destTable.name)

    checkFields(cu.fields(), tableFields, srcTable.name)

    for x in src.fetchall():
        values = []
        for key, val in zip(tableFields, x):
            values.append(val)

        subs = ", ".join(['?'] * len(values))
        dest.execute("INSERT INTO %s (%s) VALUES (%s)" % (srcTable.name, fields, subs), *values)

from mint.dbversion import VersionTable
from mint.grouptrove import GroupTroveTable, GroupTroveItemsTable
from mint.jobs import JobsTable, ImageFilesTable
from mint.news import NewsCacheTable, NewsCacheInfoTable
from mint.pkgindex import PackageIndexTable
from mint.projects import ProjectsTable, LabelsTable
from mint.users import UsersTable, ProjectUsersTable, UserGroupsTable, UserGroupMembersTable, ConfirmationsTable
from mint.stats import CommitsTable
from mint.requests import MembershipRequestTable
from mint.releases import ReleasesTable
from mint.sessiondb import SessionsTable
from mint.data import JobDataTable, ReleaseDataTable

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



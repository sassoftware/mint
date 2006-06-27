#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

from mint import database

class PublishedReleasesTable(database.KeyedTable):

    name = "PublishedReleases"
    key  = "pubReleaseId"

    createSQL = """
                CREATE TABLE PublishedReleases (
                    pubReleaseId        %(PRIMARYKEY)s,
                    projectId           INTEGER,
                    name                VARCHAR(255),
                    description         TEXT,
                    visibility          SMALLINT,
                    timeCreated         DOUBLE,
                    createdBy           INTEGER,
                    timeUpdated         DOUBLE,
                    updatedBy           INTEGER
                )"""

    fields = [ 'pubReleaseId', 'projectId', 'name', 'description',
               'visibility', 'timeCreated', 'createdBy', 'timeUpdated',
               'updatedBy' ]

    indexes = { "PubReleasesProjectIdIdx": \
                   """CREATE INDEX PubReleasesProjectIdIdx
                          ON PublishedReleases(projectId)""" }


class PublishedRelease(database.TableObject):
    # TODO


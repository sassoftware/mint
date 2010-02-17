#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

"""
This script is called by cron periodically to mark jobs as failed in the
database if the build system no longer has a record of them.
"""

import logging
import mcp.client
import optparse
import time
from mcp.mcp_error import BuildSystemUnreachableError
from mint import config
from mint import jobstatus
from mint.db import database
from mint.lib.scriptlibrary import GenericScript

log = logging.getLogger(__name__)


class JobCleanupScript(GenericScript):
    logFileName = 'scripts.log'
    newLogger = True
    timeout = 120

    def action(self):
        parser = optparse.OptionParser()
        parser.add_option('-c', '--config-file',
                default=config.RBUILDER_CONFIG)
        parser.add_option('-q', '--quiet', action='store_true')
        options, args = parser.parse_args()
        self.loadConfig(options.config_file)
        self.resetLogging(quiet=options.quiet)

        try:
            client = mcp.client.Client(self.cfg.queueHost, self.cfg.queuePort)
            jobs = set(client.list_jobs())
        except BuildSystemUnreachableError:
            log.warning("Build system is unreachable; not doing job cleanup")
            return

        db = database.Database(self.cfg).db
        cu = db.transaction()
        cu2 = db.cursor()
        cu.execute("""
            SELECT b.buildId, b.timeCreated,
                u.value AS uuid, f.title, a.value AS amiId, status
            FROM Builds b
                LEFT JOIN BuildFiles f USING ( buildId )
                LEFT JOIN BuildData u ON ( b.buildId = u.buildId
                        AND u.name = 'uuid')
                LEFT JOIN BuildData a ON ( b.buildId = a.buildId
                        AND a.name = 'amiId')
            WHERE status < ? OR status = ?
            ORDER BY buildId ASC
            """, jobstatus.BUILT, jobstatus.NO_JOB)

        # Skip builds newer than 1 minute, as there is a window between when
        # the job is created and when it is submitted to the dispatcher.
        cutoff = time.time() - 60

        for buildId, timeCreated, uuid, title, amiId, status in cu:
            if timeCreated > cutoff:
                continue
            newStatus = jobstatus.FAILED
            newMessage = 'Unknown error'

            if uuid:
                if uuid in jobs:
                    # Job is running.
                    continue
                # Job is definitely dead.
                newMessage = 'Job terminated unexpectedly'

            elif status in (jobstatus.UNKNOWN, jobstatus.NO_JOB):
                # Migrate from previous versions.
                # An AMI id or a file that is not a failed build log means the
                # job was probably successful.
                if amiId or (title and not title.startswith('Failed')):
                    newMessage = 'Job Finished'
                    newStatus = jobstatus.FINISHED

            log.info("Setting build %d status to %d %s", buildId, newStatus,
                    newMessage)
            cu2.execute("""UPDATE Builds SET status = ?, statusMessage = ?
                    WHERE buildId = ?""", newStatus, newMessage, buildId)

        db.commit()

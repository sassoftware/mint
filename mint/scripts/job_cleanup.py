#
# Copyright (c) rPath, Inc.
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
from mint.lib.scriptlibrary import SingletonScript
from rmake3 import errors as rmk_errors
from rmake3 import client as rmk_client

log = logging.getLogger(__name__)

JOB_LOST = "Job terminated unexpectedly"


class Script(SingletonScript):
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

        # FIXME: hardcoded localhost
        rmake = rmk_client.RmakeClient('http://localhost:9998')

        db = database.Database(self.cfg).db
        cu = db.transaction()
        cu2 = db.cursor()
        cu.execute("""
            SELECT b.buildId, b.timeCreated, b.job_uuid::text,
                u.value AS mcp_uuid, f.title, a.value AS amiId, status
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
        runningBuilds = set()

        for (buildId, timeCreated, rmk_uuid, mcp_uuid, title, amiId, status,
                ) in cu:
            # As a failsafe, start by assuming every build is running then try
            # to prove that assumption wrong.
            runningBuilds.add(buildId)
            if timeCreated > cutoff:
                continue
            newStatus = jobstatus.FAILED
            newMessage = 'Unknown error'

            if rmk_uuid:
                try:
                    job = rmake.getJob(rmk_uuid)
                except rmk_errors.OpenError, err:
                    # rMake is down. , assume the job is gone.
                    log.warning("rMake is unreachable: %s", str(err))
                except:
                    # Can't connect to rMake for some other reason, so defer
                    # flagging the build for now.
                    log.warning("rMake is unreachable:", exc_info=1)
                    continue
                else:
                    if job and not job.status.final:
                        # Job is running.
                        continue
                # Job is unknown or is not running.
                newMessage = JOB_LOST

            elif mcp_uuid:
                if mcp_uuid in jobs:
                    # Job is running.
                    continue
                # Job is definitely dead.
                newMessage = JOB_LOST

            elif status in (jobstatus.UNKNOWN, jobstatus.NO_JOB):
                # Migrate from previous versions.
                # An AMI id or a file that is not a failed build log means the
                # job was probably successful.
                if amiId or (title and not title.startswith('Failed')):
                    newMessage = 'Job Finished'
                    newStatus = jobstatus.FINISHED

            else:
                # No idea what this is, so don't kill it.
                continue

            log.info("Setting build %d status to %d %s", buildId, newStatus,
                    newMessage)
            cu2.execute("""UPDATE Builds SET status = ?, statusMessage = ?
                    WHERE buildId = ?""", newStatus, newMessage, buildId)
            runningBuilds.remove(buildId)

        # Sweep up dead authentication tokens that are related to images. Other
        # tokens can be checked here once such a thing exists.
        if runningBuilds:
            # NOTE: This "NOT IN" implies that image_id is not NULL.
            # NOTE 2: Injection safe because %d forces an integer type check
            ids = ','.join(['%d' % x for x in runningBuilds])
            cu.execute("DELETE FROM auth_tokens WHERE image_id NOT IN (%s)" %
                    ids)
        else:
            cu.execute("DELETE FROM auth_tokens WHERE image_id IS NOT NULL")
        cu.execute("DELETE FROM auth_tokens WHERE expires_date < now()")

        db.commit()

        # Clean up other rmake3 jobs
        cu.execute("""SELECT job_uuid FROM jobs_job
            LEFT JOIN jobs_job_state USING (job_state_id)
            WHERE now() - greatest(time_created, time_updated) > '10 minutes'
            AND jobs_job_state.name NOT IN ('Completed', 'Failed')
            """)
        uuids = sorted(x[0] for x in cu)
        cu.execute("""SELECT job_state_id FROM jobs_job_state
                WHERE name = 'Failed'""")
        failed = cu.fetchone()[0]
        try:
            jobs = rmake.getJobs(uuids)
        except rmk_errors.OpenError, err:
            # rMake is down, assume no jobs are running
            log.warning("rMake is unreachable: %s", str(err))
            jobs = [None for x in uuids]

        for uuid, job in zip(uuids, jobs):
            newCode = 504
            newMessage = JOB_LOST
            newDetail = None
            if job:
                if not job.status.final:
                    # Still running
                    continue
                elif job.status.failed:
                    # The rmake job failed so use the final status of that,
                    # instead of a generic error
                    newCode = job.status.code
                    newMessage = job.status.text
                    newDetail = job.status.detail
            log.info("Setting job %s status to %s '%s' "
                    "because job result was lost", uuid, newCode, newMessage)
            cu.execute("""UPDATE jobs_job
                SET job_state_id = ?, status_code = ?, status_text = ?,
                status_detail = ?  WHERE job_uuid = ?""",
                failed, newCode, newMessage, newDetail, uuid)
        db.commit()

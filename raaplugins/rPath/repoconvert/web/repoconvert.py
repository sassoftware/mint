#
# Copyright (c) 2006 rPath, Inc
# All rights reserved
#

from gettext import gettext as _

import raa
import time
import logging
from raa import rpath_error
from raa import constants
from raa.db import schedule, data
from raa.lib import repeatschedules
from raa.modules.raawebplugin import rAAWebPlugin, disablePlugin
import raa.web
from mint import config

log = logging.getLogger('rPath.repoconvert')

class SqliteToPgsql(rAAWebPlugin):
    """
    Takes a sqlite repository and converts it to postgresql
    """

    # Name to be displayed in the side bar.
    displayName = _("PostgreSQL Conversion")

    # Name to be displayed on mouse over in the side bar.
    tooltip = _("Convert your repository to use Postgres")

    def _readConfig(self, repoconfig):
        cfg = config.MintConfig()
        cfg.read(repoconfig)
        return cfg

    def _getConfig(self):
        ret = dict()

        repoCfg = self._readConfig(config.RBUILDER_CONFIG)
        ret['converted'] = (repoCfg.reposDBDriver == 'postgresql')
        ret['finalized'] = self.getPropertyValue('FINALIZED', False)
        if ret['finalized'] and not ret['converted']:
            self.setPropertyValue('raa.hidden', False, data.RDT_BOOL)
            log.warning('Fixing up finalized state')
            self.deletePropertyValue('FINALIZED')
            ret['finalized'] = False

        #Figure out if a job is currently running
        listTasks = raa.web.getWebRoot().execution.getUnfinishedSchedules(
            schedule.typesValid,
            constants.TASKS_UNFINISHED, taskId = self.taskId)
        listTasks.reverse()
        running = False
        for (execId, schedId) in listTasks:
            status = raa.web.getWebRoot().getStatus(schedId)
            statusCode = status['status']
            statusmsg = status['statusmsg']
            if statusCode == constants.TASK_RUNNING:
                running = True
                break
        ret['running'] = running
        if running:
            ret.update(dict(schedId=schedId, status=statusCode, statusmsg=statusmsg))
        return ret

    @raa.web.expose(allow_xmlrpc=True, template="rPath.repoconvert.templates.index")
    def index(self):
        return self._getConfig()

    @raa.web.expose(allow_json=True)
    def convert(self, confirm=False):
        if confirm:
            self.setPropertyValue('FINALIZED', False, data.RDT_BOOL)
            sched = schedule.ScheduleNow()
            schedId = self.schedule(sched)
            return dict(schedId=schedId)
        else:
            return dict(error=_('Conversion not confirmed'))

    @raa.web.expose(allow_json=True)
    def finalize(self, confirm=False):
        if confirm:
            self.setPropertyValue('FINALIZED', True, data.RDT_BOOL)
            # TODO: Clean up the wasted space
            self.setPropertyValue('raa.hidden', True, data.RDT_BOOL)
            return dict(message=_("Conversion finalized"))
        else:
            return dict(error=_('Finalize step not confirmed'))

    def initPlugin(self):
        repoCfg = self._readConfig(config.RBUILDER_CONFIG)
        val = self.getPropertyValue('FINALIZED')
        if repoCfg.reposDBDriver == 'postgresql' and (val==0 or val):
                #val is 0 if this is a fresh install, True if we've
                #already finalized
            # self.setPropertyValue('raa.hidden', True, data.RDT_BOOL)
            self.setPropertyValue('raa.hidden', False, data.RDT_BOOL)
        else:
            self.setPropertyValue('raa.hidden', False, data.RDT_BOOL)

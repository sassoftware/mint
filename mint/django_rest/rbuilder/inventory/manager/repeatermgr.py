#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging

from mint.django_rest.rbuilder.manager import basemanager

log = logging.getLogger(__name__)

try:
    from rpath_repeater import client as repeater_client
except:
    log.info("Failed loading repeater client, expected in local mode only")
    repeater_client = None  # pyflakes=ignore

class RepeaterManager(basemanager.BaseManager):
    @property
    def repeaterClient(self):
        if repeater_client is None:
            return None
        return repeater_client.RepeaterClient()

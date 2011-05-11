#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging

from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.manager import basemanager

log = logging.getLogger(__name__)
exposed = basemanager.exposed

class JobManager(basemanager.BaseManager):



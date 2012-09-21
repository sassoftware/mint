#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#

import logging
import os
import exceptions
import time

from mint import helperfuncs
from mint import mint_error

from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.xmlresources import models


log = logging.getLogger(__name__)


class XmlResourceManager(basemanager.BaseManager):

    def __init__(self, *args, **kwargs):
        basemanager.BaseManager.__init__(self, *args, **kwargs)

    @exposed
    def validateXmlResource(self, xml_resource):
        # validate stuff

        xml_resource.error = models.XmlResourceError()

        return xml_resource

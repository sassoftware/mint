#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging
# from xobj import xobj
# from django.db import connection
# from django.conf import settings
# from django.contrib.redirects import models as redirectmodels
# from django.contrib.sites import models as sitemodels
# from django.core.exceptions import ObjectDoesNotExist
# from mint.lib import uuid, x509
# from mint.lib import data as mintdata
# from mint.django_rest import signals, timeutils
# from mint.django_rest.rbuilder import models as rbuildermodels
# from mint.django_rest.rbuilder.inventory import errors
#from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory import survey_models
# from mint.django_rest.rbuilder.inventory import zones as zmodels
# from mint.django_rest.rbuilder.targets import models as targetmodels
from mint.django_rest.rbuilder.manager import basemanager
# from mint.django_rest.rbuilder.querysets import models as querysetmodels
# from mint.django_rest.rbuilder.jobs import models as jobmodels
# from mint.django_rest.rbuilder.images import models as imagemodels
# from mint.rest import errors as mint_rest_errors
#from smartform import descriptor

log = logging.getLogger(__name__)
exposed = basemanager.exposed


class SurveyManager(basemanager.BaseManager):

    @exposed
    def getSurvey(self, uuid):
        survey = survey_models.Survey.objects.get(uuid=uuid)
        return survey


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
from mint.django_rest.rbuilder.users import models as user_models
from mint.django_rest.rbuilder.inventory import models as inventory_models
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
        return survey_models.Survey.objects.get(uuid=uuid)

    @exposed
    def getSurveysForSystem(self, system_id):
       surveys = survey_models.Surveys()
       surveys.survey = survey_models.Survey.objects.filter(system__pk=system_id)
       return surveys
   
    @exposed
    def addSurveyForSystem(self, system_id, survey, by_user):
       system = inventory_models.System.objects.get(system_id)
       survey.system = system
       if survey.created_by is None or survey.modified_by is None:
           users = user_models.objects.order_by('user_id').all()
           if survey.created_by is None:
               survey.created_by = users[0]
           if survey.modified_by is None:
               survey.modified_by = users[0]
   
       # how to spin the survey IDs back in?

       survey.conary_packages.clear()
       survey.rpm_packages.clear()
       survey.services.clear()

       for scp in survey.conary_packages.all():
            scp.survey_id = survey
            scp.save()
       for srp in survey.rpm_packages.all():
            srp.survey_id = survey
            srp.save()
       for ss in survey.services.all():
            ss.survey_id = survey
            ss.save()

       # TODO: any other validation/added info?
       # this is probably already done, but anyway
       survey.save()
       return survey
       #survey2 = survey_models.Survey.object.get(pk=survey.__pk)
       #return survey2

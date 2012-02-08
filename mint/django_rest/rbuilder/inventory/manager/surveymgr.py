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
from xobj import xobj
import datetime

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

    # bunch of boilerplate so IDs to micro-survey obejcts will be valid
    # not really that useful for API but need to work:

    @exposed
    def getSurveyRpmPackage(self, id):
        return survey_models.SurveyRpmPackage.objects.get(pk=id)

    @exposed
    def getSurveyConaryPackage(self, id):
        return survey_models.SurveyConaryPackage.objects.get(pk=id)

    @exposed
    def getSurveyService(self, id):
        return survey_models.SurveyService.objects.get(pk=id)

    @exposed
    def getSurveyRpmPackageInfo(self, id):
        return survey_models.RpmPackageInfo.objects.get(pk=id)

    @exposed
    def getSurveyConaryPackageInfo(self, id):
        return survey_models.ConaryPackageInfo.objects.get(pk=id)

    @exposed
    def getSurveyServiceInfo(self, id):
        return survey_models.ServiceInfo.objects.get(pk=id)
    
    @exposed
    def getSurveyTag(self, id):
        return survey_models.SurveyTag.objects.get(pk=id)
  
    # xobj hack
    @classmethod
    def _listify(cls, foo):
        if isinstance(foo, list):
            return foo
        if isinstance(foo, None):
            return []
        return [ foo ]

    # more hacks for possible missing elements
    @classmethod
    def _subel(cls, obj, *path):
        """
        Walk over all the path items, return the last one as a list,
        gracefully handling missing intermediate ones
        """
        for item in path:
            subelem = getattr(obj, item, None)
            if subelem is None:
                return []
            obj = subelem
        return cls._listify(obj)

    @exposed
    def addSurveyForSystemFromXml(self, system_id, xml):
        '''
        a temporary low level attempt at saving surveys
        which are not completely filled out.
        '''
        model = xobj.parse(xml)
        return self.addSurveyForSystemFromXobj(system_id, model)

    @exposed
    def addSurveyForSystemFromXobj(self, system_id, model):
        system = inventory_models.System.objects.get(pk=system_id)
        xsurvey          = model.survey
        xrpm_packages = self._subel(xsurvey, 'rpm_packages', 'rpm_package')
        xconary_packages = self._subel(xsurvey, 'conary_packages', 'conary_package')
        xservices = self._subel(xsurvey, 'services', 'service')
        xtags = self._subel(xsurvey, 'tags', 'tag')

        name    = getattr(xsurvey, 'name',        "")
        desc    = getattr(xsurvey, 'description', "")
        comment = getattr(xsurvey, 'comment',     "")

        survey = survey_models.Survey(
            name        = name,
            uuid        = xsurvey.uuid,
            description = desc,
            comment     = comment,
            removable   = True,
            system      = system
        )
        survey.save()

        rpm_info_by_id     = {}

        for xmodel in xrpm_packages:
            xinfo = xmodel.rpm_package_info

            # be tolerant of the way epoch comes back from node XML
            epoch = getattr(xinfo, 'epoch', 0)
            if epoch is None or str(epoch) == 'None':
                epoch = 0
            info, created = survey_models.RpmPackageInfo.objects.get_or_create(
               name         = xinfo.name,
               version      = xinfo.version,
               epoch        = epoch,
               release      = xinfo.release,
               architecture = xinfo.architecture,
               description  = xinfo.description,
               signature    = str(xinfo.signature),
            )

            rpm_info_by_id[xmodel.id] = info
            pkg = survey_models.SurveyRpmPackage(
               survey           = survey,
               rpm_package_info = info,
            )
            idate = None
            try:
                idate = datetime.datetime.utcfromtimestamp(int(xmodel.install_date))
            except ValueError:
                # happens when posting Englishey dates and is not the normal route
                idate = xmodel.install_date

            pkg.install_date = idate
            pkg.save()

        for xmodel in xconary_packages:
            xinfo = xmodel.conary_package_info
            info, created = survey_models.ConaryPackageInfo.objects.get_or_create(
                name         = xinfo.name,
                version      = xinfo.version,
                flavor       = xinfo.flavor,
                description  = xinfo.description,
                revision     = xinfo.revision,
                architecture = xinfo.architecture,
                signature    = str(xinfo.signature)
            )
            encap = getattr(xinfo, 'rpm_package_info', None)
            if encap is not None:
                info.rpm_package_info = rpm_info_by_id[encap.id]
                info.save()
            pkg = survey_models.SurveyConaryPackage(
                conary_package_info = info,
                survey              = survey,
                # TODO: not yet available in conary
                install_date        = datetime.datetime.fromtimestamp(0)
                # None # xmodel.install_date     
            )
            pkg.save()

        for xmodel in xservices:
            xinfo = xmodel.service_info
            info, created = survey_models.ServiceInfo.objects.get_or_create(
                name      = xinfo.name,
                autostart = xinfo.autostart,
                runlevels = xinfo.runlevels
            ) 
            service = survey_models.SurveyService(
                service_info = info,
                survey       = survey,
                running      = xmodel.running,
                status       = xmodel.status 
            )
            service.save()

        for xmodel in xtags:
            tag = survey_models.SurveyTag(
                survey       = survey,
                name         = xmodel.name
            )
            tag.save()

        survey = survey_models.Survey.objects.get(pk=survey.pk)
        return survey
        
    @exposed
    # TEMPORARILY NOT USED until we can get modellib recursive
    # craziness sorted out
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

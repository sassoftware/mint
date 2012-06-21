#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

import logging
from mint.django_rest.rbuilder.inventory import survey_models
from mint.django_rest.rbuilder.users import models as user_models
from mint.django_rest.rbuilder.inventory import models as inventory_models
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.inventory.manager.surveydiff import SurveyDiffRender
from mint.django_rest import timeutils
from xobj import xobj
import datetime

log = logging.getLogger(__name__)
exposed = basemanager.exposed


class SurveyManager(basemanager.BaseManager):

    @exposed
    def getSurvey(self, uuid):
        return survey_models.Survey.objects.get(uuid=uuid)

    @exposed
    def deleteSurvey(self, uuid, force=False):
        ''' 
        Deletes a survey.  Returns a tuple of (found, deleted) as
        the survey either might not exist or it might not be marked
        removable.  See views.py usage.
        '''

        surveys = survey_models.Survey.objects.filter(uuid=uuid)
        if len(surveys) == 0:
            return (False, False)
        survey = surveys[0]
        if not survey.removable and not force:
            return (True, False)
        else:
            matching_diffs = survey_models.SurveyDiff.objects.filter(
                left_survey = survey
            ).distinct() | survey_models.SurveyDiff.objects.filter(
                right_survey = survey
            ).distinct()
            matching_diffs.delete()
            sys = survey.system
            survey.delete()
            # point latest_survey to new latest
            # if there are other surveys
            surveys = survey_models.Survey.objects.filter(system=sys)
            surveys.order_by('-created_date')
            if len(surveys) > 0:
                inventory_models.System.objects.filter(pk=sys.pk).update(latest_survey=surveys[0])
            return (True, True)

    @exposed
    def getSurveysForSystem(self, system_id):
       surveys = survey_models.Surveys()
       surveys.survey = survey_models.ShortSurvey.objects.filter(
           system__pk=system_id
       ).order_by('-created_date')
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
    def getSurveyWindowsPackage(self,id):
        return survey_models.SurveyWindowsPackage.objects.get(pk=id)

    @exposed
    def getSurveyWindowsPatch(self,id):
        return survey_models.SurveyWindowsPatch.objects.get(pk=id)

    @exposed
    def getSurveyService(self, id):
        return survey_models.SurveyService.objects.get(pk=id)
    
    @exposed
    def getSurveyWindowsService(self, id):
        return survey_models.SurveyWindowsService.objects.get(pk=id)

    @exposed
    def getSurveyRpmPackageInfo(self, id):
        return survey_models.RpmPackageInfo.objects.get(pk=id)

    @exposed
    def getSurveyConaryPackageInfo(self, id):
        return survey_models.ConaryPackageInfo.objects.get(pk=id)

    @exposed
    def getSurveyWindowsPackageInfo(self, id):
        return survey_models.WindowsPackageInfo.objects.get(pk=id)

    @exposed
    def getSurveyWindowsPatchInfo(self, id):
        return survey_models.WindowsPatchInfo.objects.get(pk=id)

    @exposed
    def getSurveyServiceInfo(self, id):
        return survey_models.ServiceInfo.objects.get(pk=id)

    @exposed
    def getSurveyWindowsServiceInfo(self, id):
        return survey_models.WindowsServiceInfo.objects.get(pk=id)
    
    @exposed
    def getSurveyTag(self, id):
        return survey_models.SurveyTag.objects.get(pk=id)
  
    # xobj hack
    @classmethod
    def _listify(cls, foo):
        if isinstance(foo, list):
            return foo
        if foo is None:
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

    @classmethod
    def _xobjAsUnicode(cls, obj):
        if obj is None:
            return None
        return unicode(obj)

    @classmethod
    def _xobjAsInt(cls, obj):
        if obj is None or str(obj) == '' or str(obj) == 'None':
            return None
        return int(obj)

    @exposed
    def addSurveyForSystemFromXml(self, system_id, xml):
        '''
        a temporary low level attempt at saving surveys
        which are not completely filled out.
        '''
        xmodel = xobj.parse(xml)
        return self.addSurveyForSystemFromXobj(system_id, xmodel)

    def _bool(self, x):
        return str(x).lower() == 'true'

    def _date(self, x):
        if x == '':
            return datetime.datetime.utcfromtimestamp(0)
        try:
            idate = datetime.datetime.utcfromtimestamp(int(x))
        except ValueError:
            # happens when posting Englishey dates and is not the normal route
            idate = x
        return idate

    @exposed
    def updateSurveyFromXml(self, survey_uuid, xml):
        xmodel = xobj.parse(xml)
        xmodel = xmodel.survey
        survey = survey_models.Survey.objects.get(uuid=survey_uuid)
        xtags  = self._subel(xmodel, 'tags', 'tag')
       
        survey_models.SurveyTag.objects.filter(survey=survey).delete()

        for xtag in xtags:
            tag = survey_models.SurveyTag(
                survey       = survey,
                name         = xtag.name
            )
            tag.save() 

        survey.name          = getattr(xmodel, 'name', None)
        survey.description   = getattr(xmodel, 'description', None)
        survey.comment       = getattr(xmodel, 'comment', None)
        survey.removable     = self._bool(getattr(xmodel, 'removable', True))
        survey.modified_date = timeutils.now()

        survey.save()
        return survey

    def _toxml(self, what):
        if what is None:
            return ''
        else:
            try:
                return xobj.toxml(what)
            except TypeError:
                # catch attempt to serialize an empty tag like <foo/>
                return ''

    def xwalk(self, xvalues, position='', results=None):
        ''' find the leaf nodes in an xobj config model. '''
        if type(xvalues) == list:
            for i, elt in enumerate(xvalues):
                position = "%s/%d" % (position, i)
                self.xwalk(elt, position, results)
        else:
            eltNames = xvalues._xobj.elements
            if len(eltNames) == 0:
                results.append([position, xvalues])
            else:
                for eltName in eltNames:
                    position = "%s/%s" % (position, eltName)
                    self.xwalk(getattr(xvalues, eltName), position, results)            


    def _saveShreddedValues(self, survey, xvalues, valueType):
        ''' store config elements in the database so they are searchable, even if they are not surfaced this way '''

        results = []
        self.xwalk(xvalues, "", results)
        for x in results:
           (path, value) = x
           if path == '':
               continue
           (obj, created) = survey_models.SurveyValues.objects.get_or_create(
               survey = survey,
               type   = valueType,
               key    = path,
               value  = value
           )
           if created:
               obj.save()
        
    def _computeCompliance(self, survey, discovered_properties, validation_report, preview):
        ''' create the compliance summary block for the survey '''

        has_errors = False
        updates_pending = False
        config_execution_failed = False
        config_execution_failures = 0

        # process the validation report
        if validation_report is not None:
            status = getattr(validation_report, 'status', None)
            if status and status.lower() == 'fail':
                has_errors = True
                config_execution_failures = True

            errors = getattr(validation_report, 'errors', None)
            if errors is not None:
                elementNames = errors._xobj.elements
                for x in elementNames:
                    errorElement = getattr(errors, x)
                    success = getattr(errorElement, 'success', None)
                    subErrors = getattr(errorElement, 'error_list', None)
                    if success and success.lower() == 'false':
                        has_errors = True
                        config_execution_failed = True
                    if subErrors is not None:
                        eCount = len(subErrors._xobj.elements)
                        config_execution_failures += eCount

        # process the preview (pending software updates)        
        added = 0
        removed = 0
        changed = 0
        if preview is not None:

            observed = getattr(preview, 'observed', None)
            desired = getattr(preview, 'desired', None)
            if (observed is None) or (desired is None):
                pass
            else:
                if observed != desired:
                    updates_pending = True
                    changes = preview.conary_package_changes.conary_package_change
                    # xobj hack
                    if type(changes) != list: 
                        changes = [ changes ]
                    for x in changes:
                        typ = x.type
                        if type == 'added':
                           added = added+1
                        elif type == 'removed':
                           removed = removed+1
                        elif type == 'changed':
                           changed = changed+1

        config_sync_message = "%s added, %s removed, %s changed" % (added, removed, changed)

        # TODO: process and count deltas versus "readerators" with matching keys
        # and include summary results

        compliance_xml = """
        <compliance_summary>
        <config_execution>
           <compliant>%(config_execution_compliant)s</compliant>
           <failure_count>%(config_execution_failures)s</failure_count>
        </config_execution>
        <config_sync>
           <compliant>%(config_sync_compliant)s</compliant>
        </config_sync>
        <software>
           <compliant>%(config_sync_compliant)s</compliant>
           <message>%(config_sync_message)s</message>
        </software>
        <overall>
           <compliant>%(overall)s</compliant>
        </overall>
        </compliance_summary>
        """ % dict(
            overall = ((not has_errors) and (not updates_pending)),
            config_execution_compliant = (not config_execution_failed),
            config_execution_failures = config_execution_failures,
            config_sync_compliant = (not updates_pending),
            config_sync_message = config_sync_message
        )
        return (has_errors, updates_pending, compliance_xml)


    @exposed
    def addSurveyForSystemFromXobj(self, system_id, model):
        # shortcuts
        _u = self._xobjAsUnicode
        _int = self._xobjAsInt

        system = inventory_models.System.objects.get(pk=system_id)

        xsurvey            = model.survey
        xrpm_packages      = self._subel(xsurvey, 'rpm_packages', 'rpm_package')
        xconary_packages   = self._subel(xsurvey, 'conary_packages', 'conary_package')
        xwindows_packages  = self._subel(xsurvey, 'windows_packages', 'windows_package')
        xwindows_patches   = self._subel(xsurvey, 'windows_patches', 'windows_patch')
        xservices          = self._subel(xsurvey, 'services', 'service')
        xwindows_services  = self._subel(xsurvey, 'windows_services', 'windows_service')
        xtags              = self._subel(xsurvey, 'tags', 'tag')

        if getattr(xsurvey, 'values', None):
            raise Exception("version 7.0 or later style surveys are required")

        xconfig_properties     = self._toxml(getattr(xsurvey, 'config_properties', None))
        xdesired_properties    = self._toxml(getattr(xsurvey, 'desired_properties', None))
        xobserved_properties   = self._toxml(getattr(xsurvey, 'observed_properties', None))
        xdiscovered_properties = self._toxml(getattr(xsurvey, 'discovered_properties', None))
        xvalidation_report     = self._toxml(getattr(xsurvey, 'validation_report', None))
        xpreview               = self._toxml(getattr(xsurvey, 'preview', None))
        xconfig_descriptor     = self._toxml(getattr(xsurvey, 'config_properties_descriptor', None))

        created_date = getattr(xsurvey, 'created_date', 0)
        created_date = datetime.datetime.utcfromtimestamp(int(created_date))

        desc    = getattr(xsurvey, 'description', "")
        comment = getattr(xsurvey, 'comment',     "")

        desired_descriptor = self.mgr.getConfigurationDescriptor(system)

        survey = survey_models.Survey(
            name          = system.name,
            uuid          = _u(xsurvey.uuid),
            description   = desc,
            comment       = comment,
            removable     = True,
            system        = system,
            created_date  = created_date,
            modified_date = created_date,
            config_properties     = xconfig_properties,
            desired_properties    = xdesired_properties,
            observed_properties   = xobserved_properties,
            discovered_properties = xdiscovered_properties,
            validation_report     = xvalidation_report,
            preview               = xpreview,
            config_properties_descriptor = xconfig_descriptor,
            desired_properties_descriptor = desired_descriptor
        )
        survey.save()
        
        self._saveShreddedValues(survey, xsurvey.config_properties, survey_models.CONFIG_VALUES)
        self._saveShreddedValues(survey, xsurvey.desired_properties, survey_models.DESIRED_VALUES)
        self._saveShreddedValues(survey, xsurvey.observed_properties, survey_models.OBSERVED_VALUES)
        self._saveShreddedValues(survey, xsurvey.discovered_properties, survey_models.DISCOVERED_VALUES)
        self._saveShreddedValues(survey, xsurvey.validation_report, survey_models.VALIDATOR_VALUES)        

        # update system.latest_survey if and only if it's
        # the latest
        if system.latest_survey is None or survey.created_date > system.latest_survey.created_date:
            system.latest_survey = survey
            system.save()

        rpm_info_by_id     = {}
        rpms_by_info_id    = {}

        for xmodel in xrpm_packages:
            xinfo = xmodel.rpm_package_info

            # be tolerant of the way epoch comes back from node XML
            epoch = _int(getattr(xinfo, 'epoch', None))
            info, created = survey_models.RpmPackageInfo.objects.get_or_create(
               name         = _u(xinfo.name),
               version      = _u(xinfo.version),
               epoch        = epoch,
               release      = _u(xinfo.release),
               architecture = _u(xinfo.architecture),
               description  = _u(xinfo.description),
               signature    = _u(xinfo.signature),
            )

            rpm_info_by_id[xmodel.id] = info
            pkg = survey_models.SurveyRpmPackage(
               survey           = survey,
               rpm_package_info = info,
            )

            rpms_by_info_id[info.pk] = pkg

            pkg.install_date = self._date(xmodel.install_date)
            pkg.save()

        for xmodel in xconary_packages:
            xinfo = xmodel.conary_package_info
            info, created = survey_models.ConaryPackageInfo.objects.get_or_create(
                name         = _u(xinfo.name),
                version      = _u(xinfo.version),
                flavor       = _u(xinfo.flavor),
                description  = _u(xinfo.description),
                revision     = _u(xinfo.revision),
                architecture = _u(xinfo.architecture),
                signature    = _u(xinfo.signature)
            )
            encap = getattr(xinfo, 'rpm_package_info', None)

            use_date = self._date(xmodel.install_date)
            top_level = _u(getattr(xmodel, 'is_top_level', ''))
            is_top_level = False
            if top_level.lower() == 'true':
                is_top_level = True

            if encap is not None:
                info.rpm_package_info = rpm_info_by_id[encap.id]
                info.save()
                # conary may not support install_date yet so cheat
                # and get it from the RPM if available
                if xmodel.install_date in [ 0, '', None ]:
                    rpm_package = rpms_by_info_id.get(info.rpm_package_info.pk, None)
                    if rpm_package is not None:
                        use_date = rpm_package.install_date
 
            pkg = survey_models.SurveyConaryPackage(
                conary_package_info = info,
                survey              = survey,
                install_date        = use_date,
                is_top_level        = is_top_level
            )
            pkg.save()

        for xmodel in xwindows_packages:
            xinfo = xmodel.windows_package_info
            info,created = survey_models.WindowsPackageInfo.objects.get_or_create(
                publisher    = _u(xinfo.publisher),
                product_code = _u(xinfo.product_code),
                package_code = _u(xinfo.package_code),
                type         = _u(xinfo.type),
                upgrade_code = _u(xinfo.upgrade_code),
                version      = _u(xinfo.version)
            )
            pkg = survey_models.SurveyWindowsPackage(
                windows_package_info = info,
                survey = survey,
                install_source = _u(xmodel.install_source),
                local_package  = _u(xmodel.local_package),
                install_date   = self._date(xmodel.install_date), 
            )
            pkg.save()

        for xmodel in xwindows_patches:
            # NOTE DEPENDENT SERVICES!!!
            xinfo = xmodel.windows_patch_info
            info,created = survey_models.WindowsPatchInfo.objects.get_or_create(
                display_name   = _u(xinfo.display_name),
                uninstallable  = self._bool(xinfo.uninstallable),
                patch_code     = _u(xinfo.patch_code),
                product_code   = _u(xinfo.product_code),
                transforms     = _u(xinfo.transforms),
            )
            referenced_packages = self._subel(xinfo, 'windows_packages_info', 'windows_package_info')
            packages_info = []
            if created:
                for rp in referenced_packages:
                    package_infos = survey_models.WindowsPackageInfo.objects.filter(
                        publisher    = _u(rp.publisher),
                        product_code = _u(rp.product_code),
                        package_code = _u(rp.package_code),
                        type         = _u(rp.type),
                        upgrade_code = _u(rp.upgrade_code),
                        version      = _u(rp.version)
                    )
                    if len(package_infos) > 0:
                        link, created_link = survey_models.SurveyWindowsPatchPackageLink.objects.get_or_create(
                            windows_patch_info   = info,
                            windows_package_info = package_infos[0]
                        )
                    else:
                        # the XML's package reference was bad, but let's upload what we can
                        # shouldn't really happen
                        pass
            pkg = survey_models.SurveyWindowsPatch(
                survey             = survey,
                windows_patch_info = info,
                local_package      = _u(xmodel.local_package),
                install_date       = self._date(xmodel.install_date),
                is_installed       = self._bool(xmodel.is_installed)
            )
            pkg.save() 
                

        for xmodel in xservices:
            xinfo = xmodel.service_info
            info, created = survey_models.ServiceInfo.objects.get_or_create(
                name      = _u(xinfo.name),
                autostart = _u(xinfo.autostart),
                runlevels = _u(xinfo.runlevels),
            ) 
            service = survey_models.SurveyService(
                service_info = info,
                survey       = survey,
                running      = self._bool(xmodel.running),
                status       = _u(xmodel.status),
            )
            service.save()

        for xmodel in xwindows_services:
            xinfo = xmodel.windows_service_info
            info, created = survey_models.WindowsServiceInfo.objects.get_or_create(
                name         = _u(xinfo.name),
                display_name = _u(xinfo.display_name),
                type         = _u(xinfo.type),
                handle       = _u(xinfo.handle),
                # this will be rendered more properly later, but we're saving it
                # flat to avoid a lot of ordering complexity
                _required_services = _u(xinfo.required_services) 
            )
            service = survey_models.SurveyWindowsService(
                windows_service_info = info,
                survey               = survey,
                status               = _u(xmodel.status),
            )
            service.save()

        for xmodel in xtags:
            tag = survey_models.SurveyTag(
                survey       = survey,
                name         = _u(xmodel.name),
            )
            tag.save()
        
        (has_errors, updates_pending, compliance_xml) = self._computeCompliance(survey, 
            discovered_properties=getattr(xsurvey, 'discovered_properties', None),
            validation_report=getattr(xsurvey, 'validation_report', None),
            preview=getattr(xsurvey, 'preview', None)
        )
        survey.has_errors = has_errors
        survey.updates_pending = updates_pending
        survey.compliance_summary = compliance_xml
        survey.save()       

        survey = survey_models.Survey.objects.get(pk=survey.pk)
        return survey

    @exposed
    def diffSurvey(self, left, right, request):
        ''' 
        If the diff has already been calculated, return it, otherwise
        save it and return it.  The diff will be pregenerated before 
        returning the job result.
        '''

        left = survey_models.Survey.objects.select_related().get(uuid=left)
        right = survey_models.Survey.objects.select_related().get(uuid=right)
        # is there a cached copy?
        diffs = survey_models.SurveyDiff.objects.filter(
             left_survey  = left,
             right_survey = right
        )
        if len(diffs) == 0:
            # not cached yet, calculate, save, and return
            differ = SurveyDiffRender(left, right, request)
            diff = survey_models.SurveyDiff(
                left_survey  = left,
                right_survey = right,
                xml          = differ.render()
            )
            diff.save()
            return diff.xml
        else:
            # return cached copy
            return diffs[0].xml



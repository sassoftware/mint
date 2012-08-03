#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

import logging
from mint.django_rest.rbuilder.inventory import survey_models
from mint.django_rest.rbuilder.inventory import models as inventory_models
from mint.django_rest.rbuilder.projects import models as project_models
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.inventory.manager.surveydiff import SurveyDiffRender
from mint.django_rest import timeutils
from conary import versions
from xobj import xobj
from datetime import datetime, timedelta

log = logging.getLogger(__name__)
exposed = basemanager.exposed


class SurveyManager(basemanager.BaseManager):

    @exposed
    def getSurvey(self, uuid):
        return survey_models.Survey.objects.get(uuid=uuid)

    @exposed
    def deleteSurvey(self, uuid):
        ''' 
        Deletes a survey.  Returns a tuple of (found, deleted) as
        the survey either might not exist.  Previously allowed locking
        surveys down to be not removable, but that is now just a UI hint.
        '''

        surveys = survey_models.Survey.objects.filter(uuid=uuid)
        if len(surveys) == 0:
            return (False, False)
        survey = surveys[0]
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
    def deleteRemovableSurveys(self, olderThanDays=None):
        if olderThanDays is None:
            olderThanDays = self.cfg.surveyMaxAge
        max_date = datetime.now() - timedelta(days=olderThanDays)

        # We do 2 separate queries below because max_date is timezone offset
        # naive whereas survey.created_date is timezone offset aware. Python
        # doesn't handle this well: "TypeError: can't compare offset-naive and
        # offset-aware datetimes". If the 2 query approach becomes untenable,
        # the Python issue could be solved by using the pytz library.

        # Determine latest survey for each system
        all_surveys = survey_models.Survey.objects.order_by('system', 'created_date')
        system_latest = {}
        for survey in all_surveys:
            system_latest[survey.system.system_id] = survey.survey_id
        del all_surveys

        # Delete all old removable surveys unless they are the latest for
        # a system
        surveys = survey_models.Survey.objects.filter(
            removable=True, created_date__lte=max_date
        ).exclude(survey_id__in=system_latest.values())

        for survey in surveys:
            self.deleteSurvey(survey.uuid)

        return surveys


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
    def getSurveyWindowsOsPatch(self,id):
        return survey_models.SurveyWindowsOsPatch.objects.get(pk=id)

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
    def getSurveyWindowsOsPatchInfo(self, id):
        return survey_models.WindowsOsPatchInfo.objects.get(pk=id)

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
            return datetime.utcfromtimestamp(0)
        try:
            idate = datetime.utcfromtimestamp(float(x))
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

    def _toxml(self, what, tag_override=None):
        ''' wrapper around xobj xml conversions and various cleanup'''
        if what is None:
            return ''
        else:
            try:
                if tag_override is None:
                    return xobj.toxml(what)
                else:
                    return xobj.toxml(what, tag_override)
            except TypeError:
                # catch attempt to serialize an empty tag like <foo/>
                return ''

    def xwalk(self, xvalues, position='', results=None):
        ''' find the leaf nodes in an xobj config model. '''
        if type(xvalues) == list:
            for i, elt in enumerate(xvalues):
                newPosition = "%s/%d" % (position, i)
                self.xwalk(elt, newPosition, results)
        else:
            eltNames = xvalues._xobj.elements
            if len(eltNames) == 0:
                results.append([position, xvalues])
            else:
                for eltName in eltNames:
                    newPosition = "%s/%s" % (position, eltName)
                    self.xwalk(getattr(xvalues, eltName), newPosition, results)            


    def _saveShreddedValues(self, survey, xvalues, valueType):
        ''' store config elements in the database so they are searchable, even if they are not surfaced this way '''

        if xvalues is None:
            raise Exception("missing required survey element")
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
                    changes = getattr(preview.conary_package_changes, 'conary_package_change', None)
                    if changes is not None:
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

    
    def _computeConfigDelta(self, survey):
        left = survey_models.SurveyValues.objects.filter(
            survey = survey, type = survey_models.DESIRED_VALUES 
        )
        right = survey_models.SurveyValues.objects.filter(
            survey = survey, type = survey_models.OBSERVED_VALUES
        )
        delta = "<config_compliance><config_values>"
        compliant = True

        for rightKey in right:
            for leftKey in left:
                # may have to be some magic to drop /extensions/, etc and do semi-fuzzy
                # matches on bits
                if leftKey.key.find("/errors/") != -1:
                    continue

                if leftKey.key == rightKey.key.replace("/extensions","") and leftKey.value != rightKey.value:
                   compliant = False
                   tokens = leftKey.key.split("/")
                   keyShortName = tokens[-1]
                   delta += "  <config_value>"
                   delta += "     <keypath>%s</keypath>" % leftKey.key
                   delta += "     <key>%s</key>" % keyShortName
                   delta += "     <read>%s</read>" % rightKey.value
                   delta += "     <desired>%s</desired>" % leftKey.value
                   delta += "  </config_value>"

        delta += "</config_values><compliant>%s</compliant>" % compliant
        delta += "</config_compliance>"
        return delta

    @exposed
    def addSurveyForSystemFromXobj(self, system_id, model):
        # shortcuts
        _u = self._xobjAsUnicode
        _int = self._xobjAsInt

        system = inventory_models.System.objects.get(pk=system_id)

        xsurvey              = model.survey
        xrpm_packages        = self._subel(xsurvey, 'rpm_packages', 'rpm_package')
        xconary_packages     = self._subel(xsurvey, 'conary_packages', 'conary_package')
        xwindows_packages    = self._subel(xsurvey, 'windows_packages', 'windows_package')
        xwindows_patches     = self._subel(xsurvey, 'windows_patches', 'windows_patch')
        xwindows_os_patches  = self._subel(xsurvey, 'windows_os_patches', 'windows_os_patch')
        xservices            = self._subel(xsurvey, 'services', 'service')
        xwindows_services    = self._subel(xsurvey, 'windows_services', 'windows_service')
        xtags                = self._subel(xsurvey, 'tags', 'tag')

        if getattr(xsurvey, 'values', None):
            raise Exception("version 7.0 or later style surveys are required")

        xconfig_properties     = getattr(xsurvey, 'config_properties', None)

        # desired_properties comes in from the server configuration, not the survey
        # where the XML tag must be changed for the shredder
        xdesired_properties    = None
        if system.configuration is not None:
            config = self.mgr.getSystemConfiguration(system_id)
            xdesired_properties = xobj.parse(config)
        if xdesired_properties is None or getattr(xdesired_properties, 'configuration', None) is None:
            xdesired_properties = xobj.parse('<configuration/>')

        origin = getattr(xsurvey, 'origin', 'scanner')

        xobserved_properties   = getattr(xsurvey, 'observed_properties', None)
        xdiscovered_properties = getattr(xsurvey, 'discovered_properties', None)
        xvalidation_report     = getattr(xsurvey, 'validation_report', None)
        xpreview               = getattr(xsurvey, 'preview', None)
        xconfig_descriptor     = getattr(xsurvey, 'config_properties_descriptor', None)
        systemModel            = getattr(xsurvey, 'system_model', None)

        if systemModel is None:
            systemModelContents = None
            systemModelModifiedDate = None
            hasSystemModel = False
        else:
            systemModelContents = getattr(systemModel, 'contents', None)
            systemModelModifiedDate = datetime.utcfromtimestamp(int(
                getattr(systemModel, 'modified_date', 0)))
            hasSystemModel = (systemModelContents is not None)

        created_date = getattr(xsurvey, 'created_date', 0)
        created_date = datetime.utcfromtimestamp(int(created_date))

        desc    = getattr(xsurvey, 'description', "")
        comment = getattr(xsurvey, 'comment',     "")


        # default to removable for registration surveys, but not manual ones
        removable = (origin != 'scanner')

        # WIP...

        system_snapshot_xml = system.to_xml()
        project_snapshot_xml = None
        stage_snapshot_xml = None
        
        if system.project:
            project_snapshot_xml = system.project.to_xml()
        if system.project_branch_stage:
            stage_snapshot_xml = system.project_branch_stage.to_xml()

        survey = survey_models.Survey(
            name = system.name,
            uuid = _u(xsurvey.uuid),
            description = desc,
            comment = comment,
            removable = removable,
            system = system,
            created_date = created_date,
            modified_date = created_date,
            config_properties = self._toxml(xconfig_properties),
            desired_properties = self._toxml(xdesired_properties, 'desired_properties'),
            observed_properties = self._toxml(xobserved_properties),
            discovered_properties = self._toxml(xdiscovered_properties),
            validation_report = self._toxml(xvalidation_report),
            preview = self._toxml(xpreview),
            config_properties_descriptor = self._toxml(xconfig_descriptor),
            system_model = systemModelContents,
            system_model_modified_date = systemModelModifiedDate,
            has_system_model = hasSystemModel,
            system_snapshot = system_snapshot_xml,
            project_snapshot = project_snapshot_xml,
            stage_snapshot = stage_snapshot_xml,
        )

        survey.save()
 
        self._saveShreddedValues(survey, xconfig_properties, survey_models.CONFIG_VALUES)
        self._saveShreddedValues(survey, xdesired_properties, survey_models.DESIRED_VALUES)
        self._saveShreddedValues(survey, xobserved_properties, survey_models.OBSERVED_VALUES)
        self._saveShreddedValues(survey, xdiscovered_properties, survey_models.DISCOVERED_VALUES)
        self._saveShreddedValues(survey, xvalidation_report, survey_models.VALIDATOR_VALUES)        

        # update system.latest_survey if and only if it's
        # the latest
        if system.latest_survey is None or survey.created_date > system.latest_survey.created_date:
            system.__class__.objects.filter(system_id=system_id).update(latest_survey=survey)

        rpm_info_by_id     = {}
        rpms_by_info_id    = {}
        windows_packages_by_id = {}

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

        topLevelItems = set()
        for xmodel in xconary_packages:
            xinfo = xmodel.conary_package_info

            unfrozen = ''
            try:
                conary_version = versions.ThawVersion(_u(xinfo.version))
                unfrozen = conary_version.asString()
            except:
                pass

            info, created = survey_models.ConaryPackageInfo.objects.get_or_create(
                name         = _u(xinfo.name),
                version      = _u(xinfo.version),
                flavor       = _u(xinfo.flavor),
                description  = _u(xinfo.description),
                revision     = _u(xinfo.revision),
                architecture = _u(xinfo.architecture),
                signature    = _u(xinfo.signature),
            )
            # unfrozen might not be set on old survey data, but update it if we have data now
            # (hence not inside the get_or_create)
            info.unfrozen    = unfrozen
            encap = getattr(xinfo, 'rpm_package_info', None)

            use_date = self._date(xmodel.install_date)
            top_level = _u(getattr(xmodel, 'is_top_level', ''))
            is_top_level = False
            if top_level.lower() == 'true' or (info.name.startswith('group-') and info.name.find("-appliance") != -1):
                is_top_level = True
                topLevelItems.add('%s=%s[%s]' %
                    (info.name, info.version, info.flavor))
                ver = versions.VersionFromString(unfrozen)
                label = ver.trailingLabel()
                labelstr = label.asString()
                # TODO: if somehow the system is in a stage that got deleted
                # be cool and just set it back to NULL
                stages = project_models.Stage.objects.filter(label=labelstr)
                if len(stages) > 0:
                    stage = stages[0]
                    project = stage.project
                    branch = stage.project_branch
                    system.project = project
                    system.project_branch = branch
                    system.project_branch_stage = stage
                    system.save()
 
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

        # If no desired state is saved in the db, set it from the survey
        count = system.desired_top_level_items.count()
        if count == 0:
            for troveSpec in topLevelItems:
                obj = inventory_models.SystemDesiredTopLevelItem(system=system, trove_spec=troveSpec)
                obj.save()

        for xmodel in xwindows_packages:
            xinfo = xmodel.windows_package_info
            xid = xmodel.id
            info, created = survey_models.WindowsPackageInfo.objects.get_or_create(
                publisher    = _u(xinfo.publisher),
                product_code = _u(xinfo.product_code),
                product_name = _u(xinfo.product_name),
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
            windows_packages_by_id[xid] = pkg
            pkg.save()

        for xmodel in xwindows_os_patches:
            xinfo = xmodel.windows_os_patch_info
            info, created = survey_models.WindowsOsPatchInfo.objects.get_or_create(
                hotfix_id    = _u(xinfo.hotfix_id),
                name         = _u(xinfo.name),
                fix_comments = _u(xinfo.fix_comments),
                description  = _u(xinfo.description),
                caption      = _u(xinfo.caption)
            )
            if created:
                info.save()
            pkg = survey_models.SurveyWindowsOsPatch(
                survey                = survey,
                windows_os_patch_info = info,
                status                = _u(xmodel.status),
                install_date          = self._date(xmodel.install_date),
                installed_by          = _u(xmodel.installed_by),
                cs_name               = _u(xmodel.cs_name),
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

            # Windows client is sending back wrong XML elements but compensate by allowing this element
            # in the wrong nesting topology to basically work.  Needed for demo.   TODO: get Windows client
            # to send a package info object here, not a package, and remove this hack.
            referenced_packages_hack = self._subel(xinfo, 'windows_packages_info', 'windows_package')

            packages_info = []
            if created:
                for rp in referenced_packages_hack:
                    pkg = windows_packages_by_id[rp.id]
                    package_info = pkg.windows_package_info
                    link, created_link = survey_models.SurveyWindowsPatchPackageLink.objects.get_or_create(
                        windows_patch_info   = info,
                        windows_package_info = package_info
                    )
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
                # getattr can be removed once supplied by newer Windows survey code (7/4/11 or so)
                # no windows survey code is otherwise released
                running              = self._bool(getattr(xmodel, 'running', 'false')),
                start_account        = _u(getattr(xmodel, 'start_account', '')),
                start_mode           = _u(getattr(xmodel, 'start_mode', ''))
            )
            service.save()

        for xmodel in xtags:
            tag = survey_models.SurveyTag(
                survey       = survey,
                name         = _u(xmodel.name),
            )
            tag.save()
        
        (has_errors, updates_pending, compliance_xml) = self._computeCompliance(survey, 
            discovered_properties=xdiscovered_properties,
            validation_report=xvalidation_report,
            preview=xpreview,
        )
        survey.has_errors = has_errors
        survey.updates_pending = updates_pending
        survey.compliance_summary = compliance_xml
        survey.config_compliance = self._computeConfigDelta(survey)
        survey.save()

        # required to avoid some first survey Catch-22 issues
        system.latest_survey = survey
        system.save()

        desired_descriptor = self.mgr.getConfigurationDescriptor(system)
        survey.desired_properties_descriptor = desired_descriptor
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



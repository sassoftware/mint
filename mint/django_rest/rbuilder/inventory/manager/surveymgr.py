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
from django.db.models import F

log = logging.getLogger(__name__)
exposed = basemanager.exposed


class SurveyManager(basemanager.BaseManager):
    """ retrieves, saves (generates), and updates surveys.  For diff logic see surveydiff.py """

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

        # point latest_survey to new latest if there are other surveys
        surveys = survey_models.Survey.objects.filter(system=sys)
        surveys.order_by('-created_date')
        if len(surveys) > 0:
            sys.update(latest_survey=surveys[0])
        return (True, True)

    @exposed
    def deleteRemovableSurveys(self, olderThanDays=None):
        ''' 
        there's a crontab that deletes surveys older than a set age that are marked
        removable.  This is for that. 
        '''

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
       ''' return all surveys for a given system, ordered by creation date '''

       surveys = survey_models.Surveys()
       surveys.survey = survey_models.ShortSurvey.objects.filter(
           system__pk=system_id
       ).order_by('-created_date')
       return surveys

    @exposed 
    def getLatestSurveys(self):
       # all the latest surveys
       surveys = survey_models.Surveys()
       surveys.survey = survey_models.ShortSurvey.objects.filter(
           pk=F('system__latest_survey__pk')
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
        """ if foo is not a list, make foo a list of one """
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
    def _u(cls, obj):
        """ ensure obj is cast to unicode """
        if obj is None:
            return None
        return unicode(obj)

    @classmethod
    def _i(cls, obj):
        """ ensure obj is cast to an integer """
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
        """ convert string x to a boolean value """
        return str(x).lower() == 'true'

    def _date(self, x):
        """ convert an XML date to a datetime """
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
        """ only portions of a survey are editable on POST """

        xmodel = xobj.parse(xml)
        xmodel = xmodel.survey
        survey = survey_models.Survey.objects.get(uuid=survey_uuid)
        xtags  = self._subel(xmodel, 'tags', 'tag')

        # delete any previous tags and save new ones
        # TODO: delete only the ones that need to be removed, insert only those
        # that need to be inserted.  
        survey_models.SurveyTag.objects.filter(survey=survey).delete()
        for xtag in xtags:
            tag = survey_models.SurveyTag(survey = survey, name = xtag.name)
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
            # the XML of a None object is an empty string
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

        # we start walking from xvalues, which is either a list-xobj or a regular node
        # position keeps track of a pseudo-XPath like path
        
        if type(xvalues) == list:
            for i, elt in enumerate(xvalues):
                newPosition = "%s/%d" % (position, i)
                # recurse down each item in the list
                self.xwalk(elt, newPosition, results)
        else:
            eltNames = xvalues._xobj.elements
            if len(eltNames) == 0:
                # it's a leaf node, record the xobj element found at this path
                results.append([position, xvalues])
            else:
                # recurse on children of the element
                for eltName in eltNames:
                    newPosition = "%s/%s" % (position, eltName)
                    self.xwalk(getattr(xvalues, eltName), newPosition, results)

    def _saveShreddedValues(self, survey, xvalues, valueType):
        ''' store config elements in the database so they are searchable, even if they are not surfaced this way '''

        if xvalues is None:
            raise Exception("missing required survey element")
        results = []
        # find all leaf nodes of the xvalues tag
        self.xwalk(xvalues, "", results)
        for x in results:
           (path, value) = x
           if path == '':
               # forget what this does -- if the root node is a leaf node, don't save it (?)
               continue
           # save all leaf nodes
           (obj, created) = survey_models.SurveyValues.objects.get_or_create(
               survey = survey, type = valueType, key = path, value = value
           )
           # if a key appears twice, don't save it twice.  Could happen with complex list types.  Maybe.
           if created:
               obj.save()

    def _computeValidationReportCompliance(self, validation_report):
        '''
        given the <validation_report> element of a survey, walk through it and decide whether any errors are marked fatal
        or the overall report is fatal.  Return this information + error counts
        '''

        # process the validation report
        has_errors = False
        overall_validation = False
        config_execution_failed = False
        config_execution_failures = 0

        if validation_report is not None:

            # if there is a top level status tag and the status is 'fail', the client has decided to fail
            # the validation report.
            status = getattr(validation_report, 'status', None)
            if status and status.lower() == 'fail':
                has_errors = True
                config_execution_failed = True
            else:
                overall_validation = True        
     
            # errors represent things like tracebacks, not overt failures, but an individual error can mark
            # the validation report as a fatal or non-fatal error.  This is respected if for some reason
            # it didn't set the overall status, but the survey really SHOULD set the overall status.  We
            # also have to count errors anyway.   Refer to RCE-11 and RCE-303 in JIRA for XML context.

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
        return (has_errors, config_execution_failed, config_execution_failures, overall_validation) 

    def _computePackageChangeCounts(self, preview):
        '''
        determine if a <preview> has pending changes, and count up the number of additions, removals, and changes
        a preview is the difference between the observed (client) group and the desired (server selected) group and
        indicates package drift 
        '''

        added = 0
        removed = 0
        changed = 0
        updates_pending = False

        # there is really no reason for a survey to NOT include a preview anymore, but we don't choke if
        # it is not sent.
        if preview is not None:

            # observed and desired are presently trove spec strings
            observed = getattr(preview, 'observed', None)
            desired = getattr(preview, 'desired', None)
            if (observed is None) or (desired is None):
                pass
            else:
                # the survey is going to be non-compliant if the observed version does not match the desired
                # OR there are any packages in the list of conary package changes.  Note survey XML is also
                # shared with the update action and follows the same format.

                if observed != desired:
                    updates_pending = True
                changes = getattr(preview.conary_package_changes, 'conary_package_change', None)
                if changes is not None:
                    updates_pending = True
                    # xobj hack
                    if type(changes) != list:
                        changes = [ changes ]
                    # count how many package changes we've had of each type
                    for x in changes:
                        typ = x.type
                        if typ == 'added':
                            added = added+1
                        elif typ == 'removed':
                            removed = removed+1
                        elif typ == 'changed':
                            changed = changed+1
        return (added, removed, changed, updates_pending)

    def _computeCompliance(self, survey, discovered_properties, validation_report, preview, config_diff_ct):
        ''' 
        create the compliance summary block for the survey.  This is a rollup of various survey attributes
        and indicates whether the survey is overall in compliance or not.
        '''

        # compliance is the summation of the validation report, package changes (preview XML) and whether
        # or not we've had any config errors.  

        results = self._computeValidationReportCompliance(validation_report)
        (has_errors, config_execution_failed, config_execution_failures, overall_validation) = results
        (added, removed, changed, updates_pending) = self._computePackageChangeCounts(preview)
        config_sync_message = "%s added, %s removed, %s changed" % (added, removed, changed)

        config_sync_compliant = (config_diff_ct == 0)
        software_sync_compliant = (not updates_pending)
        config_execution_compliant = (not config_execution_failed)
        overall = config_sync_compliant and software_sync_compliant and config_execution_compliant
        
        compliance_xml = self._generateComplianceXml(overall, config_execution_failures, 
            software_sync_compliant, config_sync_compliant, config_execution_compliant, 
            config_sync_message)
   
        return (has_errors, updates_pending, compliance_xml, overall, config_execution_failures, overall_validation)

    def _generateComplianceXml(self, overall, config_execution_failures, software_sync_compliant, 
        config_sync_compliant, config_execution_compliant, config_sync_message):
        ''' helper function generating XML block from _computeCompliance '''

        # to avoid xobj fun, here's an XML-template for the compliance block
        return """
        <compliance_summary>
        <config_execution>
            <compliant>%(config_execution_compliant)s</compliant>
            <failure_count>%(config_execution_failures)s</failure_count>
        </config_execution>
        <config_sync>
            <compliant>%(config_sync_compliant)s</compliant>
            <message>%(config_sync_message)s</message>
        </config_sync>
        <software>
            <compliant>%(software_sync_compliant)s</compliant>
        </software>
        <overall>
            <compliant>%(overall)s</compliant>
        </overall>
        </compliance_summary>
        """ %  dict(
             overall = overall, config_execution_failures = config_execution_failures, software_sync_compliant = software_sync_compliant,
             config_sync_compliant = config_sync_compliant, config_execution_compliant = config_execution_compliant,
             config_sync_message = config_sync_message
        )


    def _computeConfigDelta(self, survey):
        ''' 
        the config_compliance section is a summary of how observed configuration values (client read.d) are different from desired values (set by
        answering the configuration descriptor smartform questionaire on the server).
        '''

        # we also have other types of configuration saved in this format, though spec says to only diff DESIRED vs OBSERVED here.
        # the diff code uses this elsewhere to show, between two surveys, how DESIRED has changed over time.

        left = survey_models.SurveyValues.objects.filter(survey = survey, type = survey_models.DESIRED_VALUES)
        right = survey_models.SurveyValues.objects.filter(survey = survey, type = survey_models.OBSERVED_VALUES)
        delta = "<config_compliance><config_values>"
        compliant = True
        config_diff_ct = 0

        for rightKey in right:
            for leftKey in left:
                # may have to be some magic to drop /extensions/, etc and do semi-fuzzy
                # matches on bits
                if leftKey.key.find("/errors/") != -1:
                    # don't include error information in the diff block
                    continue
                if leftKey.key == rightKey.key.replace("/extensions","") and leftKey.value != rightKey.value:
                    # the left hand side doesn't have any 'extensions' in the server XML and the right does, so try to
                    # normalize to get a decent diff.  This may need work if the config XML from the configuration descriptor (Flex)
                    # starts sending down XML differently to the nodes -- but if we do that, I imagine we've also broken
                    # customer configurators.
                    config_diff_ct += 1
                    compliant = False
                    tokens = leftKey.key.split("/")
                    keyShortName = tokens[-1]
                    # NOTE: the config compliance block format is not quite the same as the XML diffs in diffs.
                    delta += "  <config_value>"
                    delta += "     <keypath>%s</keypath>" % leftKey.key
                    delta += "     <key>%s</key>" % keyShortName
                    delta += "     <read>%s</read>" % rightKey.value
                    delta += "     <desired>%s</desired>" % leftKey.value
                    delta += "  </config_value>"

        delta += "</config_values><compliant>%s</compliant>" % compliant
        delta += "</config_compliance>"
        return (delta, config_diff_ct)

    def _store_rpm_packages(self, survey, xrpm_packages, rpms_by_info_id, rpm_info_by_id):
        ''' 
        saves all rpm package references in the survey.  As with other types of saving below
        The Info version of the object stores the definition of that object, the non-Info version
        stores information about the instance, such as the install time on that particular system.
        The Info version of the object can be the same across every system, the non-Info version
        is the act of actually installing it.
        '''

        for xmodel in xrpm_packages:

            xinfo = xmodel.rpm_package_info
            # be tolerant of the way epoch comes back from client XML
            epoch = self._i(getattr(xinfo, 'epoch', None))
            info, created = survey_models.RpmPackageInfo.objects.get_or_create(
               name         = self._u(xinfo.name),
               version      = self._u(xinfo.version),
               epoch        = epoch,
               release      = self._u(xinfo.release),
               architecture = self._u(xinfo.architecture),
               description  = self._u(xinfo.description),
               signature    = self._u(xinfo.signature),
            )

            # the ID's coming back from the client are obviously not database IDs and we are storing
            # them here to later associate references in the client XML to associate rpm packages
            # with the conary packages that encapsulate them.
 
            rpm_info_by_id[xmodel.id] = info
            pkg = survey_models.SurveyRpmPackage(survey=survey, rpm_package_info = info)
            rpms_by_info_id[info.pk] = pkg
            pkg.install_date = self._date(xmodel.install_date)
            pkg.save()

    def _store_conary_packages(self, survey, xconary_packages, topLevelItems, rpm_info_by_id, rpms_by_info_id):
        '''
        stores all conary packages, keeping track of references to encapsulated RPM packages.  Note that windows
        packages do not have such references to their conary packages.
        '''

        for xmodel in xconary_packages:
            xinfo = xmodel.conary_package_info

            # XML from the client comes back frozen every time, but there are tables that have only
            # the unfrozen versions, so we compute that here so we can do lookups into those tables.  This 
            # was done for inventory_trove, which may or may not exist in Harpoon, but still useful to store
            # for search purposes.

            unfrozen = ''
            try:
                conary_version = versions.ThawVersion(self._u(xinfo.version))
                unfrozen = conary_version.asString()
            except:
                pass

            info, created = survey_models.ConaryPackageInfo.objects.get_or_create(
                name         = self._u(xinfo.name), version = self._u(xinfo.version),
                flavor       = self._u(xinfo.flavor), description = self._u(xinfo.description),
                revision     = self._u(xinfo.revision), architecture = self._u(xinfo.architecture),
                signature    = self._u(xinfo.signature),
            )
            # unfrozen might not be set on old survey data, but update it if we have data now
            # (hence not inside the get_or_create)
            info.unfrozen    = unfrozen

            encap = getattr(xinfo, 'rpm_package_info', None)
            use_date = self._date(xmodel.install_date)
            top_level = self._u(getattr(xmodel, 'is_top_level', ''))

            # client should send back flags of what's top level or not, but in case it doesn't, group-foo-appliance
            # is also used to mark something top level.  We'll probably have to revisit this when we have to do
            # more with system model.
            is_top_level = False
            if top_level.lower() == 'true' or (info.name.startswith('group-') and info.name.find("-appliance") != -1):
                is_top_level = True
                topLevelItems.add('%s=%s[%s]' % (info.name, info.version, info.flavor))

            # conary package encapsulated an RPM, so store those relations
            if encap is not None:
                info.rpm_package_info = rpm_info_by_id[encap.id]
                info.save()
                # conary may not support install_date yet so cheat and get it from the RPM if available
                if xmodel.install_date in [ 0, '', None ]:
                    rpm_package = rpms_by_info_id.get(info.rpm_package_info.pk, None)
                    if rpm_package is not None:
                        use_date = rpm_package.install_date

            pkg = survey_models.SurveyConaryPackage(
                conary_package_info = info, survey = survey, install_date = use_date, is_top_level = is_top_level
            )
            pkg.save()

    def _save_windows_packages(self, survey, xwindows_packages, windows_packages_by_id):
        ''' store all windows packages '''

        for xmodel in xwindows_packages:
            survey.os_type = 'windows'

            xinfo = xmodel.windows_package_info
            xid = xmodel.id
            info, created = survey_models.WindowsPackageInfo.objects.get_or_create(
                publisher    = self._u(xinfo.publisher), product_code = self._u(xinfo.product_code), product_name = self._u(xinfo.product_name),
                package_code = self._u(xinfo.package_code), type = self._u(xinfo.type), upgrade_code = self._u(xinfo.upgrade_code),
                version      = self._u(xinfo.version)
            )
            pkg = survey_models.SurveyWindowsPackage(
                windows_package_info = info, survey = survey, install_source = self._u(xmodel.install_source), local_package = self._u(xmodel.local_package),
                install_date   = self._date(xmodel.install_date),
            )
            windows_packages_by_id[xid] = pkg
            pkg.save()

    def _save_windows_os_patches(self, survey, xwindows_os_patches):
        ''' save all windows OS patches. '''

        for xmodel in xwindows_os_patches:
            survey.os_type = 'windows'

            xinfo = xmodel.windows_os_patch_info
            info, created = survey_models.WindowsOsPatchInfo.objects.get_or_create(
                hotfix_id    = self._u(xinfo.hotfix_id), name = self._u(xinfo.name), fix_comments = self._u(xinfo.fix_comments),
                description  = self._u(xinfo.description), caption = self._u(xinfo.caption)
            )
            if created:
                info.save()
            pkg = survey_models.SurveyWindowsOsPatch(
                survey        = survey, windows_os_patch_info = info, status = self._u(xmodel.status),
                install_date  = self._date(xmodel.install_date), installed_by = self._u(xmodel.installed_by),
                cs_name       = self._u(xmodel.cs_name),
            )
            pkg.save()

    def _save_windows_patches(self, survey, xwindows_patches, windows_packages_by_id):
        ''' saves all windows patches with references to what windows_packages they patch '''     

        for xmodel in xwindows_patches:
            survey.os_type = 'windows'

            xinfo = xmodel.windows_patch_info
            info,created = survey_models.WindowsPatchInfo.objects.get_or_create(
                display_name   = self._u(xinfo.display_name),
                uninstallable  = self._bool(xinfo.uninstallable),
                patch_code     = self._u(xinfo.patch_code),
                product_code   = self._u(xinfo.product_code),
                transforms     = self._u(xinfo.transforms),
            )
            referenced_packages = self._subel(xinfo, 'windows_packages_info', 'windows_package_info')
            
            # at one point the windows client sent back the wrong XML tags, so also look in this location
            referenced_packages_hack = self._subel(xinfo, 'windows_packages_info', 'windows_package')

            if created:
                # supporting the 'wrong' format... (possibly safe to remove now)
                for rp in referenced_packages_hack:
                    pkg = windows_packages_by_id[rp.id]
                    package_info = pkg.windows_package_info
                    # storing association of the windows patch to the package it patches
                    link, created_link = survey_models.SurveyWindowsPatchPackageLink.objects.get_or_create(
                        windows_patch_info   = info,
                        windows_package_info = package_info
                    )
                # if we get the 'right' format...
                for rp in referenced_packages:
                    package_infos = survey_models.WindowsPackageInfo.objects.filter(
                        publisher    = self._u(rp.publisher), product_code = self._u(rp.product_code), package_code = self._u(rp.package_code),
                        type         = self._u(rp.type), upgrade_code = self._u(rp.upgrade_code), version = self._u(rp.version)
                    )
                    if len(package_infos) > 0:
                        link, created_link = survey_models.SurveyWindowsPatchPackageLink.objects.get_or_create(
                            windows_patch_info = info, windows_package_info = package_infos[0]
                        )
                    else:
                        # the XML's package reference was bad, but let's upload what we can
                        # shouldn't really happen
                        pass
            pkg = survey_models.SurveyWindowsPatch(
                survey = survey, windows_patch_info = info, local_package = self._u(xmodel.local_package),
                install_date = self._date(xmodel.install_date), is_installed = self._bool(xmodel.is_installed)
            )
            pkg.save()

    def _save_services(self, survey, xservices):
        ''' saves all (Linux) services '''

        for xmodel in xservices:
            xinfo = xmodel.service_info
            info, created = survey_models.ServiceInfo.objects.get_or_create(
                name      = self._u(xinfo.name), autostart = self._u(xinfo.autostart), runlevels = self._u(xinfo.runlevels),
            )
            service = survey_models.SurveyService(
                service_info = info, survey = survey, running = self._bool(xmodel.running), status = self._u(xmodel.status),
            )
            service.save()

    def _save_windows_services(self, survey, xwindows_services):
        ''' saves all windows services '''

        for xmodel in xwindows_services:
            xinfo = xmodel.windows_service_info
            info, created = survey_models.WindowsServiceInfo.objects.get_or_create(
                name = self._u(xinfo.name), display_name = self._u(xinfo.display_name), type = self._u(xinfo.type), 
                handle = self._u(xinfo.handle), _required_services = self._u(xinfo.required_services)
            )
            autostart = (self._u(getattr(xmodel, 'autostart', 'false')) != 'false')
            service = survey_models.SurveyWindowsService(
                windows_service_info = info, survey = survey, status = self._u(xmodel.status),
                running = self._bool(getattr(xmodel, 'running', 'false')), start_account = self._u(getattr(xmodel, 'start_account', '')),
                start_mode = self._u(getattr(xmodel, 'start_mode', '')), autostart = autostart
            )
            service.save()

    def _save_tags(self, survey, xtags):
        ''' saves any tags the user has applied.  These will probably only come on edits but are supported on initial POST as well. '''
 
        for xmodel in xtags:
            tag = survey_models.SurveyTag(survey = survey, name = self._u(xmodel.name))
            tag.save()

    @exposed
    def addSurveyForSystemFromXobj(self, system_id, model):
        ''' 
        given an XML (xobj) model for a survey as POSTed to inventory/systems/N/surveys from a Linux or Windows client, process
        the survey, fix various associations, update various details (see inline comments), and save the survey.  The survey
        cannot be saved directly like other resource objects because the version coming from the clients needs lots of
        additional processing.
        '''

        system = inventory_models.System.objects.get(pk=system_id)

        # get shortcut references to the various XML tags in the survey.  The subel function is used to get data that are lists.
        xsurvey              = model.survey
        xrpm_packages        = self._subel(xsurvey, 'rpm_packages', 'rpm_package')
        xconary_packages     = self._subel(xsurvey, 'conary_packages', 'conary_package')
        xwindows_packages    = self._subel(xsurvey, 'windows_packages', 'windows_package')
        xwindows_patches     = self._subel(xsurvey, 'windows_patches', 'windows_patch')
        xwindows_os_patches  = self._subel(xsurvey, 'windows_os_patches', 'windows_os_patch')
        xservices            = self._subel(xsurvey, 'services', 'service')
        xwindows_services    = self._subel(xsurvey, 'windows_services', 'windows_service')
        xtags                = self._subel(xsurvey, 'tags', 'tag')

        # if we recieved a top level <values> this is a sign this is an pre-Goad survey, which we no longer support
        if getattr(xsurvey, 'values', None):
            raise Exception("version 7.0 or later style surveys are required")

        # config-properites replaces <values> in Goad-and-later version surveys
        xconfig_properties     = getattr(xsurvey, 'config_properties', None)

        # hack: if <config_properties> has a <values> as a subelement, this is the client sending it weird, and attempt
        # to rename it to configuration
        values = getattr(xconfig_properties, 'values', None)
        if values is not None:
             values._xobj.tag = 'configuration'        

        # hack: desired_properties comes in from the server configuration, not the survey
        # where the XML tag must be changed to follow the same tag hierarchy
        xdesired_properties    = None
        if system.configuration is not None:
            config = self.mgr.getSystemConfiguration(system_id)
            xdesired_properties = xobj.parse(config)
        # if we recieved no configuration back, fill in an empty one
        if xdesired_properties is None or getattr(xdesired_properties, 'configuration', None) is None:
            xdesired_properties = xobj.parse('<configuration/>')

        # get xobj handles to various other XML elements
        origin                 = getattr(xsurvey, 'origin', 'scanner')
        xobserved_properties   = getattr(xsurvey, 'observed_properties', None)
        xdiscovered_properties = getattr(xsurvey, 'discovered_properties', None)
        xvalidation_report     = getattr(xsurvey, 'validation_report', None)
        xpreview               = getattr(xsurvey, 'preview', None)
        xconfig_descriptor     = getattr(xsurvey, 'config_properties_descriptor', None)
        systemModel            = getattr(xsurvey, 'system_model', None)

        # determine if we have a system model or not, as we need to note that in the survey
        if systemModel is None:
            systemModelContents = None
            systemModelModifiedDate = None
            hasSystemModel = False
        else:
            systemModelContents = getattr(systemModel, 'contents', None)
            systemModelModifiedDate = datetime.utcfromtimestamp(int(getattr(systemModel, 'modified_date', 0)))
            hasSystemModel = (systemModelContents is not None)

        # get the date, description, and time off the survey XML
        created_date = getattr(xsurvey, 'created_date', 0)
        created_date = datetime.utcfromtimestamp(int(created_date))
        desc    = getattr(xsurvey, 'description', "")
        comment = getattr(xsurvey, 'comment',     "")

        # we keep track of whether a survey comes from rpath-register or a CIM/WMI initiated scan.
        # surveys coming from registration are marked such that they can be automatically purged, but not ones
        # the user manually initiated.
        removable = (origin != 'scanner')

        # the suryey contains a full capture of the system XML, project XML, and stage XML at the point the
        # survey was taken
        system_snapshot_xml = system.to_xml()
        project_snapshot_xml = None
        stage_snapshot_xml = None
        if system.project:
            project_snapshot_xml = system.project.to_xml()
        if system.project_branch_stage:
            stage_snapshot_xml = system.project_branch_stage.to_xml()

        # save what we know about the survey so far
        survey = survey_models.Survey(
            name = system.name, uuid = self._u(xsurvey.uuid), description = desc, comment = comment,
            removable = removable, system = system, created_date = created_date, modified_date = created_date,
            config_properties = self._toxml(xconfig_properties), desired_properties = self._toxml(xdesired_properties, 'desired_properties'),
            observed_properties = self._toxml(xobserved_properties), discovered_properties = self._toxml(xdiscovered_properties),
            validation_report = self._toxml(xvalidation_report), preview = self._toxml(xpreview),
            config_properties_descriptor = self._toxml(xconfig_descriptor), system_model = systemModelContents,
            system_model_modified_date = systemModelModifiedDate, has_system_model = hasSystemModel,
            system_snapshot = system_snapshot_xml, project_snapshot = project_snapshot_xml, stage_snapshot = stage_snapshot_xml,
        )
        survey.save()

        # to enable queryset search (systems with these config attributes, etc) as well as config compliance diffing,
        # we save each of the config elements in the database by XML path of each element and value.  It's pseudo-XPathey
        # and allows us to say later, find me all the systems with Apache on port 80, etc.

        self._saveShreddedValues(survey, xconfig_properties, survey_models.CONFIG_VALUES)
        self._saveShreddedValues(survey, xdesired_properties, survey_models.DESIRED_VALUES)
        self._saveShreddedValues(survey, xobserved_properties, survey_models.OBSERVED_VALUES)
        self._saveShreddedValues(survey, xdiscovered_properties, survey_models.DISCOVERED_VALUES)
        self._saveShreddedValues(survey, xvalidation_report, survey_models.VALIDATOR_VALUES)

        # update system.latest_survey if and only if this survey is now the latest.
        # though this should always be the latest, shouldn't it?  I guess you could post an old one later
        # but the client tools currently don't enable this.
        if system.latest_survey is None or survey.created_date > system.latest_survey.created_date:
            system.update(latest_survey=survey)

        # getting ready to save packages and need to keep track of various references.  We'll assume
        # the system is Linux until we find out that it is not.
        survey.os_type = 'linux'
        rpm_info_by_id = {}
        rpms_by_info_id = {}
        windows_packages_by_id = {}

        # save packages, keeping track of which packages are top level in conary-land
        topLevelItems = set()
        self._store_rpm_packages(survey, xrpm_packages, rpms_by_info_id, rpm_info_by_id)
        self._store_conary_packages(survey, xconary_packages, topLevelItems, rpm_info_by_id, rpms_by_info_id)
        self._save_windows_packages(survey, xwindows_packages, windows_packages_by_id)

        # if we do not have a record of what the server thinks should be installed on the box,
        # this is an initial survey and we will set it from the current observed values to declare that the system
        # is as intended.  We'll always update the observed top level items though.
        count = system.desired_top_level_items.count()
        if count == 0:
            # server has no copy of desired top level items, so we must set this... otherwise don't
            self.mgr.setDesiredTopLevelItems(system, topLevelItems)
        self.mgr.setObservedTopLevelItems(system, topLevelItems)

        # save patch information (windows only)
        self._save_windows_os_patches(survey, xwindows_os_patches)
        self._save_windows_patches(survey, xwindows_patches, windows_packages_by_id)

        # save service info
        self._save_services(survey, xservices)
        self._save_windows_services(survey, xwindows_services)

        # user could have supplied some tags on upload (client tools don't do this yet)
        self._save_tags(survey, xtags)

        # see if the configuration observed values are different from desired values (if any)
        (survey.config_compliance, config_diff_ct) = self._computeConfigDelta(survey)

        # each survey has an overall compliance summary block.  Generate it.
        results = self._computeCompliance(survey,
            discovered_properties=xdiscovered_properties, validation_report=xvalidation_report,
            preview=xpreview, config_diff_ct=config_diff_ct,
        )
        (has_errors, updates_pending, compliance_xml, overall, execution_error_count, overall_validation) = results

        # update the survey object with what we've learned about complaince and save it again
        survey.has_errors = has_errors
        survey.updates_pending = updates_pending
        survey.compliance_summary = compliance_xml
        survey.config_diff_count = config_diff_ct
        survey.overall_compliance = overall
        survey.overall_validation = overall_validation
        survey.execution_error_count = int(execution_error_count)
        survey.save()

        # the survey contains a copy of the configuration descriptor at the point of survey time as it may change later and we need
        # it to render the config properties form.
        desired_descriptor = self.mgr.getSystemConfigurationDescriptor(system)
        survey.desired_properties_descriptor = desired_descriptor
        survey.save()

        # return the survey as we have saved it.
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



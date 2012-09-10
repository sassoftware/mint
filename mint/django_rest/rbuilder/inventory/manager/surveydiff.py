#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

from xml.etree.ElementTree import Element, tostring, fromstring
from mint.django_rest.rbuilder.inventory import survey_models
import datetime
import difflib

# lines of context for unified diff
DIFF_CONTEXT = 10

# for things changed, but not added/removed, what fields to show in the diff?  
# this only applies to "_info" objects which represent the definition of something that can apply to multiple hosts
# state information, like install_time is not included in a survey-to-survey diff.

DIFF_FIELDS = {
   'rpm_package_info'      : [ 'epoch', 'version', 'release', 'signature' ], 
   'conary_package_info'   : [ 'version', 'architecture', 'signature' ],
   'service_info'          : [ 'autostart', 'runlevels' ],
   'windows_package_info'  : [ 'publisher', 'product_code', 'package_code', 'product_name', 'type', 'upgrade_code', 'version' ],  
   'windows_patch_info'    : [ 'display_name', 'uninstallable', 'patch_code', 'product_code', 'transforms' ],
   'windows_os_patch_info' : [ 'hotfix_id', 'name', 'fix_comments', 'description', 'caption' ],
   'windows_service_info'  : [ 'name', 'display_name', 'type', 'handle' ]
}

# not really about the infos, but the state of the things themselves
# see usage below

DIFF_TOP_LEVEL_FIELDS = {
   'windows_service_info' : [ 'running' ],
   'service_info' : [ 'running' ],
}


class SurveyDiff(object):
    ''' Compare two surveys and return a list or xobj model of their differences '''

    def __init__(self, left, right):
        ''' contruct a diff object from two surveys, then call compare '''
        self.left = left
        self.right = right

        # used to control some potential redundant lookups when trying to find
        # names of configurator extensions for particular configurator XML paths
        # (very much a minor corner case)
        self.name_key_map = {} 

    def compare(self):
        ''' 
        Compute survey differences, but don't return XML.  Sets side
        effects for usage by SurveyDiffRender class.
        '''

        # basic objects
        self.rpmDiff            = self._computeRpmPackages()
        self.conaryDiff         = self._computeConaryPackages()
        self.serviceDiff        = self._computeServices()
        self.windowsPackageDiff = self._computeWindowsPackages()
        self.windowsPatchDiff   = self._computeWindowsPatches()
        self.windowsOsPatchDiff = self._computeWindowsOsPatches()
        self.windowsServiceDiff = self._computeWindowsServices()

        # configuration
        self.configDiff         = self._computeConfigDiff()
        self.desiredDiff        = self._computeDesiredDiff()
        self.observedDiff       = self._computeObservedDiff()
        self.discoveredDiff     = self._computeDiscoveredDiff()
        self.validatorDiff      = self._computeValidatorDiff()

    def _name(self, obj):
        ''' the name of the object to show in the diff is usually a name, except when it's not '''

        t = type(obj)
        if t == survey_models.WindowsPatchInfo:
            return obj.display_name
        elif t == survey_models.WindowsPackageInfo:
            return obj.product_name
        return obj.name
 
    def _uniqueNames(self, infoName, left, right):
        ''' return all the object names in left and right '''

        leftNames  = set([ self._name(getattr(x,infoName)) for x in left  ])
        rightNames = set([ self._name(getattr(x,infoName)) for x in right ])
        return leftNames | rightNames

    def _computeGeneric(self, collectedName, infoName):
        ''' 
        Supporting code behind arbitrary object diffs 
        '''

        added, changed, removed = ([], [], [])
        leftItems   = getattr(self.left, collectedName).all()
        rightItems  = getattr(self.right, collectedName).all()
        allNames    = self._uniqueNames(infoName, leftItems, rightItems) 

        for name in allNames:

            # process things one set of names at a time to prevent extra iteration
            leftMatches   = [ x for x in leftItems  if self._name(getattr(x, infoName)) == name ]
            rightMatches  = [ x for x in rightItems if self._name(getattr(x, infoName)) == name ]

            # for things with this same name, what's different?
            localAdded, localChanged, localRemoved = self._diff(infoName, leftMatches, rightMatches)

            # add to the big list for the overall diff of survey documents
            added.extend(localAdded)
            changed.extend(localChanged)
            removed.extend(localRemoved)

        return (added, changed, removed)


    def _isChanged(self, infoName, a, b):
        '''
        for a given resource, we can move to having 1 item on the left side of a diff
        and multiple items on the right.  Only one is a change, the rest are additions
        and removals.   This is for resources that have more than one type with
        same name -- to decide if this is a change event instead of an addition/removal.
        '''

        aInfo = getattr(a, infoName)
        bInfo = getattr(b, infoName)

        if self._name(aInfo) != self._name(bInfo):
            # this shouldn't really get hit in the way we are using it
            return False

        if infoName == 'rpm_package_info':
            # RPMs don't show up as changed, they are always added or removed only
            return False
        elif infoName == 'conary_package_info':
            # like conary packages can have the same name, arch, and flavor
            return (aInfo.architecture == bInfo.architecture and aInfo.flavor == bInfo.flavor)
        elif infoName == 'windows_package_info':
            # windows uses product codes...
            return (aInfo.product_code == bInfo.product_code)
        elif infoName == 'windows_patch_info':
            return (aInfo.product_code == bInfo.product_code)
        elif infoName == 'windows_os_patch_info':
            # except for patches, which use 'hotfix_id'
            return (aInfo.hotfix_id == bInfo.hotfix_id) 
        elif infoName == 'service_info':
            # services are always changes if the name is the same ...
            return True
        elif infoName == 'windows_service_info':
            return True
        else:
            # we added a new type of object to the diff and need to add another stanza here
            raise Exception("unknown info mode: %s" % infoName)

    def _in(self, infoName, itemList, infoPk):
        '''
        Something is "IN" a list if the primary key related to the definition
        of the resource is in the list.  If it's not, it's an addition, removal,
        or change.
        '''
        for x in itemList:
            if getattr(x, infoName).pk == infoPk:
               return True
        return False

    def _flag_changed(self, infoName, before, after):
        '''
        go through lists of things named foo of a given type in both before and after
        results and flag ones that are markable as being a 'change'
        '''
        for x in before:
            for y in after:
                if self._isChanged(infoName, x, y):
                    x._changed = y
                    y._changed = x

    def _diff(self, infoName, before, after):
        ''' 
        given the changes for one specific name of object, ex: rpms named 'foo' or services named 'bar'
        identify what additions, changes, and removals there were.  This is somewhat tricky as multiple
        installations of something named foo are legal.    
        '''

        added, changed, removed = ([], [], [])
    
        self._flag_changed(infoName, before, after)
    
        # added are things in after but not before that also are NOT marked changed
        for x in after:
            afterInfo = getattr(x, infoName)
            if not self._in(infoName, before, afterInfo.pk):
                changedTo = getattr(x, "_changed", None)
                if changedTo is None:
                    added.append(x)

        # removed are things in before but not after that also are NOT marked changed
        for x in before:
            beforeInfo = getattr(x, infoName)
            if not self._in(infoName, after, beforeInfo.pk):
                changedTo = getattr(x, "_changed", None)
                if changedTo is None:
                    removed.append(x)

        # anything marked changed is changed        
        for x in before:
            changedTo = getattr(x, "_changed", None) 
            if changedTo is not None:
                differences = self._computeChanges(infoName, x, changedTo)
                if differences is not None:
                    changed.append([x, changedTo, differences]) 

        return (added, changed, removed)

    def _computeChanges(self, mode, leftItem, rightItem):
        '''
        return a dict where each key is the name of a field and the each value
        is a tuple of the left value and right value
        '''

        # fields of the _info objects to scan -- representing the definition of something
        fields = DIFF_FIELDS[mode]

        # fields referencing the instance of something -- which are generally not diffed
        # with a few exceptions (see top of file) 
        top_level_fields = DIFF_TOP_LEVEL_FIELDS.get(mode,[])

        differences = {}
        
        # 'mode' here is the name of the info field for the object
        leftInfo = getattr(leftItem, mode)
        rightInfo = getattr(rightItem, mode)

        # if there are no top level fields to diff, and the info objects are the same, 
        # there are no changes
        if leftInfo.pk == rightInfo.pk and len(top_level_fields) == 0:
            return None

        # the info object is different, so record every field that is different
        # in the list of info fields to diff
        if leftInfo.pk != rightInfo.pk:
            for f in fields:
                lval = getattr(leftInfo, f)
                rval = getattr(rightInfo, f)
                if lval != rval:
                    differences[f] = (lval, rval)

        # if there are any top level fields to diff... 
        # we are not actually diffing the info, but also a state change in the way the 
        # object exists presently.  This only happens with services because they can be 
        # running or not running even though they are installed the same.  Packages
        # do not behave this way.   
        for f in top_level_fields:
            lval = getattr(leftItem, f, None)
            rval = getattr(rightItem, f, None)
            if lval != rval:
                differences[f] = (lval, rval)

        if len(differences) == 0:
            return None
        return differences

    # basic wrapper functions around diff calculation for various objects:
    def _computeRpmPackages(self):
        return self._computeGeneric('rpm_packages', 'rpm_package_info')

    def _computeConaryPackages(self):
        return self._computeGeneric('conary_packages', 'conary_package_info')

    def _computeServices(self):
        return self._computeGeneric('services', 'service_info')

    def _computeWindowsPackages(self):
        return self._computeGeneric('windows_packages', 'windows_package_info')

    def _computeWindowsPatches(self):
        return self._computeGeneric('windows_patches', 'windows_patch_info')

    def _computeWindowsOsPatches(self):
        return self._computeGeneric('windows_os_patches', 'windows_os_patch_info')

    def _computeWindowsServices(self):
        return self._computeGeneric('windows_services', 'windows_service_info')

    def _computeValueDiff(self, value_type):
        ''' 
        various config values are stored xpath-ish in the SurveyValues table.
        this determines how they have changed in-between surveys.
        '''

        added = []
        removed = []
        changed = []      

        # get all values of the given type for both the left and right survey
        left = survey_models.SurveyValues.objects.filter(survey=self.left, type=value_type).order_by('key')
        right = survey_models.SurveyValues.objects.filter(survey=self.right, type=value_type).order_by('key')

        lkeys = [ x.key for x in left ]
        rkeys = [ x.key for x in right ] 

        # attempt to get the name of the extension out of the database
        # FIXME: smarter caching
        all_keys = []
        all_keys.extend(lkeys)
        all_keys.extend(rkeys)

        key_extension_map = {}
        for x in all_keys:
            tokens = x.split('/')
            if (len(tokens) > 2) and tokens[1] == 'extensions':
                name_key = "/extensions/%s/name" % tokens[2]
                if not (name_key in self.name_key_map):
                    name_values = survey_models.SurveyValues.objects.filter(survey__in = [self.left, self.right ], key=name_key)
                    if len(name_values):
                        value = name_values[0].value
                        key_extension_map[x] = value
                        self.name_key_map[name_key] = value
                    else:
                        self.name_key_map[name_key] = None
                else:
                    key_extension_map[x] = self.name_key_map[name_key]

        # whether the key is there or not decides added/removed
        for x in right:
           if x.key not in lkeys:
               x._extension_name = key_extension_map.get(x.key, None)
               added.append(x)
        for x in left:
           if x.key not in rkeys:
               x._extension_name = key_extension_map.get(x.key, None)
               removed.append(x)

        # if the key is in both, it's changed
        for x in left:
           for y in right:
              if x.key == y.key:
                  if x.value != y.value:
                      delta = dict(
                         value = (x.value, y.value)
                      )
                      x._extension_name = key_extension_map.get(x.key, None)
                      y._extension_name = key_extension_map.get(y.key, None)
                      self._flagged = True
                      changed.append((x,y,delta))

        result = (added, changed, removed)
        return result

    # wrappers that just call configValueDiff for each of the config types 
    def _computeConfigDiff(self):
        return self._computeValueDiff(survey_models.CONFIG_VALUES)

    def _computeDesiredDiff(self):
        return self._computeValueDiff(survey_models.DESIRED_VALUES)

    def _computeObservedDiff(self):
        return self._computeValueDiff(survey_models.OBSERVED_VALUES)

    def _computeDiscoveredDiff(self):
        return self._computeValueDiff(survey_models.DISCOVERED_VALUES)

    def _computeValidatorDiff(self):
        return self._computeValueDiff(survey_models.VALIDATOR_VALUES)
   
class SurveyDiffRender(object):

    def __init__(self, left, right, request=None):
        ''' 
        Render a XML diff between two surveys.  Caching on diffs 
        already computed is handled in surveymgr.py
        '''
        self.left    = left
        self.right   = right
        self.request = request # for URL reversal and REST ids (optional)
        self.differ  = SurveyDiff(left, right)

    def _makeId(self, obj):
        ''' render URL for various elements '''
        if self.request is None:
            return { 'id' : str(obj.pk) }
        else:
            return { 'id' : obj.get_absolute_url(self.request) }

    def _renderSurvey(self, tag, survey):
        ''' serializes the left_survey or right_survey elements '''
        node = self._xmlNode(tag, about=survey,
             keys='name description removable created_date comment overall_validation updates_pending has_errors overall_compliance'
        )
        xtags = Element('tags')
        for tag in survey.tags.all():
            xtag = self._element('tag')
            xname = self._element('name', tag.name)
            xtag.append(xname)
            xtags.append(xtag)
        node.append(xtags)
        return node

    def _element(self, name, text=None):
        ''' shorthand around etree element creation due to lame constructor API '''
        e = Element(name)
        if text is not None:
           e.text = str(text)
        return e

    def _addElement(self, to, name, value):
        to.append(self._element(name, value))

    def _addElements(self, to, **kwargs):
        [ self._addElement(to,k,v) for (k,v) in kwargs.items() ]

    def _xmlNode(self, elemName, about=None, keys=[], parent=None):
        if type(keys) != list:
            keys = keys.split()
        id_dict = self._makeId(about)
        if id_dict.get("id",None) is None:
            # this is for the various properties elements, which are not REST resources
            # TODO: fix in above function
            id_dict={}
        elem = Element(elemName, attrib=id_dict)
        elts = dict([ (x, getattr(about, x)) for x in keys])
        self._addElements(elem, **elts)

        if parent:
            parent.append(elem)
        return elem

    def _renderRoot(self, left, right):
        ''' make root note for survey diffs '''
        attribs = {}
        if self.request is not None:
            attribs = { 'id' : "https://%s%s" % (
                self.request.META['SERVER_NAME'], 
                self.request.META['PATH_INFO']
            ) }
        elem = Element('survey_diff', attrib=attribs)
        elem.append(self._renderSurvey('left_survey', left))
        elem.append(self._renderSurvey('right_survey', right))
        elem.append(self._element('created_date', str(datetime.datetime.now())))
        return elem

    def _renderComplianceDiff(self):
        from mint.django_rest.rbuilder import errors
        elem = Element('compliance_summary_diff')
        msg = "Survey %s is from a previous version that no longer supports diffs, please take a new survey"
        if self.left.compliance_summary is None:
            raise errors.Conflict(msg=msg % self.left.uuid)
        elif self.right.compliance_summary is None:
            raise errors.Conflict(msg=msg % self.right.uuid)
        left = fromstring(self.left.compliance_summary)
        left.tag = 'left'
        right = fromstring(self.right.compliance_summary)
        right.tag = 'right'
        elem.append(left)
        elem.append(right)
        return elem

    def _renderDiff(self, tag, changeList):
        ''' generate the part of the diffs that contains the actual changes 
 
        <changes> <---------------------- returns this
            <rpm_package_changes/>
            <conary_package_changes/>
            <service_changes/>
        </changes>
        '''

        elem = Element(tag)
        (added, changed, removed) = changeList
            
        lname = self.left.name
        rname = self.right.name
        ldate = str(self.left.created_date)
        rdate = str(self.right.created_date)

        if tag.startswith('discovered_properties'):

            all_diffs = []
            for item in added:
                if not item.key.endswith('/value'):
                    continue
                left = [ '' ]
                right = item.value.split('\n')
                diff = '\n'.join(list(difflib.unified_diff(left, right, lname, rname, ldate, rdate, DIFF_CONTEXT)))
                all_diffs.append( [ item, diff ] )
            for item in removed:
                if not item.key.endswith('/value'):
                    continue
                left = item.value.split('\n')
                right = [ '' ]
                diff = '\n'.join(list(difflib.unified_diff(left, right, lname, rname, ldate, rdate, DIFF_CONTEXT)))
                all_diffs.append( [ item, diff ] )
            for item in changed:
                if not item[0].key.endswith('/value'):
                    continue
                left = item[0].value.split('\n')
                right = item[1].value.split('\n')
                diff = '\n'.join(list(difflib.unified_diff(left, right, lname, rname, ldate, rdate, DIFF_CONTEXT)))
                all_diffs.append( [ item[0], diff ] )
            self._renderSubDiffs(tag, elem, all_diffs)

        else:

            self._renderAdditions(tag, elem, added)
            self._renderChanges(tag, elem, changed)
            self._renderRemovals(tag, elem, removed)

        return elem

    def _changeElement(self, parentTag, mode):
        ''' 
        generate the tag corresponding to a single change entry, ex:
           <something_something_changes>
              <change> <------------------- returns this
                 <type>added</type>
        ''' 
        elem = Element("".join(parentTag[0:-1]))
        elem.append(self._element('type', mode))
        return elem

    def _serializeRpmPackage(self, elemName, item):
        elem = self._xmlNode(elemName, about=item, keys='install_date')
        self._xmlNode('rpm_package_info', 
            about=item.rpm_package_info, parent=elem,
            keys="name epoch version release architecture signature"
        )
        return elem 

    def _serializeConaryPackage(self, elemName, item):
        elem = self._xmlNode(elemName, about=item, keys='install_date')
        self._xmlNode('conary_package_info', 
            about=item.conary_package_info, parent=elem,
            keys="name version flavor revision architecture signature"
        )
        return elem

    def _serializeWindowsPackage(self, elemName, item):
        elem = self._xmlNode(elemName, about=item,
            keys='install_source local_package install_date'
        )
        self._xmlNode('windows_package_info', 
            about=item.windows_package_info, parent=elem,
            keys='publisher product_code package_code type upgrade_code version'
        )
        return elem

    def _serializeWindowsOsPatch(self, elemName, item):
        elem = self._xmlNode(elemName, about=item,
            keys='status install_date installed_by cs_name'
        )
        self._xmlNode('windows_os_patch_info', 
            about=item.windows_os_patch_info, parent=elem,
            keys='hotfix_id name fix_comments description caption'
        )
        return elem

    def _serializeWindowsPatch(self, elemName, item):
        elem = self._xmlNode(elemName, about=item,
            keys = 'local_package install_date is_installed'
        )
        info = self._xmlNode('windows_patch_info', 
            about=item.windows_patch_info, parent=elem,
            keys='display_name uninstallable patch_code product_code transforms'
        )
        package_elts = Element('windows_package_infos')
        links = survey_models.SurveyWindowsPatchPackageLink.objects.filter(
            windows_patch_info = item.windows_patch_info
        )
        package_objs = [ x.windows_package_info for x in links ]
        for x in package_objs:
            self._xmlNode('windows_package_info', about=x, parent=package_elts,
                keys='publisher product_code package_code type upgrade_code version'
            )
        info.append(package_elts)
        return elem

    def _serializeService(self, elemName, item):
        elem = self._xmlNode(elemName, about=item,
            keys = 'running status'
        )
        self._xmlNode('service_info', 
            about=item.service_info, parent=elem,
            keys='name autostart runlevels'
        )
        return elem

    def _serializeWindowsService(self, elemName, item):
        elem = self._xmlNode(elemName, about=item,
            keys='status start_account start_mode running'
        )
        subElt = self._xmlNode('windows_service_info', 
            about=item.windows_service_info, parent=elem,
            keys='name type handle display_name'
        )
        services = item.windows_service_info._required_services.split(",")
        required_objs = survey_models.WindowsServiceInfo.objects.filter(name__in=services)
        required_elts = Element('required_services')
        for x in required_objs:
            self._xmlNode('windows_service_info', about=x, parent=required_elts,
                keys='name display_name type handle '
            )
        subElt.append(required_elts)
        return elem

    def _serializeSurveyValue(self, elemName, item):
        '''
        diff element serialization for config/observed/desired/discovered/validation values
        '''
        elem = self._xmlNode(elemName, about=item, 
            keys='key value'
        )
        extension = getattr(item, '_extension_name', None)
        return elem

    def _serializeItem(self, elemName, item):
        ''' 
        wrappers around item serialization.  TODO: find ways to leap into xobj nicely
        and pass in a request?  this is temporary.
        '''
        serializers = {
            survey_models.SurveyRpmPackage: self._serializeRpmPackage,
            survey_models.SurveyConaryPackage: self._serializeConaryPackage,
            survey_models.SurveyWindowsPackage: self._serializeWindowsPackage,
            survey_models.SurveyWindowsPatch: self._serializeWindowsPatch,
            survey_models.SurveyWindowsOsPatch: self._serializeWindowsOsPatch,
            survey_models.SurveyService: self._serializeService,
            survey_models.SurveyWindowsService: self._serializeWindowsService,
            survey_models.SurveyValues: self._serializeSurveyValue,
        }
        return serializers[type(item)](elemName, item)

    def _fromElement(self, parentTag, item):
        ''' generate a tag with an item serialized in it 
        ex:
              <from_rpm_package> <- return this
                   <rpm_package>
        '''
        return self._serializeItem(
            "from_%s" % parentTag.replace("_changes",""), item
        )

    def _toElement(self, parentTag, item):
        ''' generate a tag with an item serialized in it '''
        return self._serializeItem(
            "to_%s" % parentTag.replace("_changes", ""), item
        )

    def _addedElement(self, parentTag, item):
        ''' generate a tag with an item serialized in it '''
        return self._serializeItem(
            "added_%s" % parentTag.replace("_changes", ""), item
        )

    def _removedElement(self, parentTag, item):
        ''' generate a tag with an item serialized in it '''
        return self._serializeItem(
            "removed_%s" % parentTag.replace("_changes",""), item
        )

    def _diffElement(self, parentTag, deltas):
        ''' differences!  these look different from the other tags 

        ex:
            <rpm_package_diff> <-------------- returns this 
                <field_name_that_changed>
                    <from>X</from>
                    <to>Y</to>
        '''

        tagName = "%s_diff" % parentTag.replace("_changes","")
        elem = Element(tagName)
        for changedField, values in deltas.iteritems():
            (left, right) = values
            subElem = Element(changedField)
            subElem.append(self._element('from', left))
            subElem.append(self._element('to', right))
            elem.append(subElem)
        return elem

    def _subDiffElement(self, parentTag, key, diff_text):
         '''
         these are real diff format diffs inside the diff.  Confused yet?
         They are only used for discovered_properties which return text like blocks.

            <diff_text>
                <key>path/to/key/thing</key>
                <value>output from diff</value>
            <diff_text>
         '''
         tagName = "%s_unified_diff" % parentTag.replace("_changes", "")
         elem = Element(tagName)
         elem.append(self._element('key', key))
         elem.append(self._element('value', diff_text))
         return elem

    def _renderACR(self, parentTag, parentElem, items, mode):
        ''' 
        abstraction around rendering out all the different possible changes
        for a given object type.
        '''
        for x in items:
            change = self._changeElement(parentTag, mode)
            if getattr(x, 'key', None) and mode in [ 'added', 'removed' ]:
                if x.key in [ '/configuration', '/errors' ]:
                    # skip empty config nodes
                    continue
            if mode == 'added':
                change.append(self._addedElement(parentTag, x))
                extension = getattr(x, '_extension_name', None)
                if extension is not None:
                    change.append(self._element('extension', extension)),
            elif mode == 'removed':
                change.append(self._removedElement(parentTag, x))
                extension = getattr(x, '_extension_name', None)
                if extension is not None:
                    change.append(self._element('extension', extension)),
            elif mode == 'changed':
                (left, right, delta) = x
                if getattr(left, 'key', None) in [ '/configuration', '/errors' ]:
                    continue
                if getattr(right, 'key', None) in [ '/configuration', '/errors' ]:
                    continue
                change.append(self._fromElement(parentTag, left))
                change.append(self._toElement(parentTag, right))
                extension = getattr(left, '_extension_name', None)
                if extension is not None:
                    change.append(self._element('extension', extension)),
                if delta is not None:
                    change.append(self._diffElement(parentTag, delta))
            parentElem.append(change)

    def _renderSubDiffs(self, parentTag, parentElem, items):
        '''
        render textual diffs -- used for block fields like discovered_properties only
        '''
        for x in items:
            change = self._changeElement(parentTag, 'unified_diff')
            (item, diff_text) = x
            key = item.key
            extension = getattr(item, '_extension_name')
            if extension is not None:
                change.append(self._element('extension', extension))
            change.append((self._subDiffElement(parentTag, key, diff_text)))
            #self._DEBUG_FLAGGED = True
            parentElem.append(change)

    def _renderAdditions(self, parentTag, parentElem, items):
        ''' 
        render all of what's been added for an object type
        these all go directly under the foo_changes element     
        '''
        if len(items) > 0:
            self._renderACR(parentTag, parentElem, items, 'added')

    def _renderChanges(self, parentTag, parentElem, items):
        ''' render all of what's been changed (and how) for an object type '''
        if len(items) > 0:
            self._renderACR(parentTag, parentElem, items, 'changed')
   
    def _renderRemovals(self, parentTag, parentElem, items):
        ''' render all of what's been removed for an object type '''
        if len(items) > 0:
            self._renderACR(parentTag, parentElem, items, 'removed')
        

    def render(self):
        ''' return XML representation of survey differences after calling compute '''

        self.differ.compare()
        root = self._renderRoot(self.left, self.right)

        elts = [
            self._renderDiff('rpm_package_changes', self.differ.rpmDiff),
            self._renderDiff('conary_package_changes', self.differ.conaryDiff),
            self._renderDiff('service_changes', self.differ.serviceDiff),
            self._renderDiff('windows_package_changes', self.differ.windowsPackageDiff),
            self._renderDiff('windows_patch_changes', self.differ.windowsPatchDiff),
            self._renderDiff('windows_os_patch_changes', self.differ.windowsOsPatchDiff),
            self._renderDiff('windows_service_changes', self.differ.windowsServiceDiff),
            self._renderDiff('config_properties_changes', self.differ.configDiff),
            self._renderDiff('observed_properties_changes', self.differ.observedDiff),
            self._renderDiff('desired_properties_changes', self.differ.desiredDiff),
            self._renderDiff('discovered_properties_changes', self.differ.discoveredDiff),
            self._renderDiff('validation_report_changes', self.differ.validatorDiff),
            self._renderComplianceDiff()
        ]

        for elt in elts:
            root.append(elt)

        result = tostring(root)

        return result




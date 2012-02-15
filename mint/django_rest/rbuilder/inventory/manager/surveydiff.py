#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from xml.etree.ElementTree import Element, tostring
from xml.dom.minidom import parseString
from mint.django_rest.rbuilder.inventory import survey_models
import datetime

# for things changed, but not added/removed, what fields to show in the diff?
DIFF_FIELDS = {
   'rpm_package_info'    : [ 'epoch', 'version', 'release', 'signature' ], 
   'conary_package_info' : [ 'version', 'architecture', 'signature' ],
   'service_info'        : [ 'autostart', 'runlevels' ]
}

class SurveyDiff(object):
    ''' Compare two surveys and return a list or xobj model of their differences '''

    def __init__(self, left, right):
        ''' contruct a diff object from two surveys, then call compare '''
        self.left = left
        self.right = right

    # FIXME: fix underscore/camel conventions
    def compare(self):
        ''' 
        Compute survey differences, but don't return XML.  Sets side
        effects for usage by SurveyDiffRender class.
        '''
        self.rpmDiff     = self._computeRpmPackages()
        self.conaryDiff  = self._computeConaryPackages()
        self.serviceDiff = self._computeServices()
      
    def _uniqueNames(self, infoName, left, right):
        ''' return all the object names in left and right '''
        names = {}
        for x in left:
            names[getattr(x, infoName).name] = 1
        for x in right:
            names[getattr(x, infoName).name] = 1
        return names.keys()

    def _matches(self, name, infoName, items):
        ''' return items in the list with the named *name* '''
        return [ x for x in items if getattr(x, infoName).name == name ]
  
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
            leftMatches  = self._matches(name, infoName, leftItems)
            rightMatches = self._matches(name, infoName, rightItems)
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
        and removals
        '''

        aInfo = getattr(a, infoName)
        bInfo = getattr(b, infoName)
        if aInfo.name != bInfo.name:
            # this shouldn't really get hit in the way we are using it
            return False
        if infoName == 'rpm_package_info':
            return (aInfo.architecture == bInfo.architecture)
        elif infoName == 'conary_package_info':
            return (aInfo.architecture == bInfo.architecture and aInfo.flavor == bInfo.flavor)
        elif infoName == 'service_info':
            return True
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
        given the changes for one specific name of object, ex: rpms named 'foo' or services named 'foo'
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
        fields = DIFF_FIELDS[mode]
        differences = {}
        leftInfo = getattr(leftItem, mode)
        rightInfo = getattr(rightItem, mode)
        if leftInfo.pk == rightInfo.pk:
            return None
        for f in fields:
            lval = getattr(leftInfo, f)
            rval = getattr(rightInfo, f)
            if lval != rval:
                differences[f] = (lval, rval)
        return differences

    def _computeRpmPackages(self):
        return self._computeGeneric('rpm_packages', 'rpm_package_info')

    def _computeConaryPackages(self):
        return self._computeGeneric('conary_packages', 'conary_package_info')

    def _computeServices(self):
        return self._computeGeneric('services', 'service_info')

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
        elem = Element(tag, attrib=self._makeId(survey))
        elem.append(self._element('name', survey.name))
        elem.append(self._element('description', survey.description))
        elem.append(self._element('removable', survey.removable))
        elem.append(self._element('created_date', survey.created_date))
        return elem

    def _element(self, name, text=None):
        ''' shorthand around etree element creation due to lame constructor API '''
        e = Element(name)
        if text is not None:
           e.text = str(text)
        return e

    def _renderRoot(self, left, right):
        ''' make root note for survey diffs '''
        elem = Element('survey_diff')
        elem.append(self._renderSurvey('left_survey', left))
        elem.append(self._renderSurvey('right_survey', right))
        elem.append(self._element('created_date', str(datetime.datetime.now())))
        return elem

    def _renderDiff(self, tag, changeList):
        ''' generate the part of the diffs that contains the actual changes 
 
        <changes> <---------------------- returns this
            <rpm_package_changes/>
            <conary_package_changes/>
            <service_changes/>
        </changes>
        '''

        (added, changed, removed) = changeList
        elem = Element(tag)
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


    def _serializeItem(self, parent, item):
        ''' 
        wrappers around item serialization.  TODO: find ways to leap into xobj nicely
        and pass in a request?  this is temporary.
        '''
        typ = type(item)
        elem = None
        if typ == survey_models.SurveyRpmPackage:
            # FIXME: ids
            elem = Element('rpm_package', attrib=self._makeId(item))
            elem.append(self._element('install_date', item.install_date))
            info = item.rpm_package_info
            subElt = Element('rpm_package_info', attrib=self._makeId(info))
            subElt.append(self._element('name', info.name))
            subElt.append(self._element('epoch', info.epoch))
            subElt.append(self._element('version', info.version))
            subElt.append(self._element('release', info.release))
            subElt.append(self._element('architecture', info.architecture))
            subElt.append(self._element('signature', info.signature))
            elem.append(subElt)
        elif typ == survey_models.SurveyConaryPackage:
            elem = Element('conary_package', attrib=self._makeId(item))
            elem.append(self._element('install_date', item.install_date))
            info = item.conary_package_info
            subElt = Element('conary_package_info', attrib=self._makeId(info))
            subElt.append(self._element('name', info.name))
            subElt.append(self._element('version', info.version))
            subElt.append(self._element('flavor', info.flavor))
            subElt.append(self._element('revision', info.revision))
            subElt.append(self._element('architecture', info.architecture))
            subElt.append(self._element('signature', info.signature))
            elem.append(subElt)
        elif typ == survey_models.SurveyService:
            elem = Element('service', attrib=self._makeId(item))
            elem.append(self._element('running', item.running))
            elem.append(self._element('status', item.status))
            info = item.service_info
            subElt = Element('service_info', attrib=self._makeId(info))
            subElt.append(self._element('name', info.name))
            subElt.append(self._element('autostart', info.autostart))
            subElt.append(self._element('runlevels', info.runlevels))
            elem.append(subElt)
        else:
            raise Exception("unsupported type")

        parent.append(elem)
        return parent

    def _fromElement(self, parentTag, item):
        ''' generate a tag with an item serialized in it 

        ex:
              <from_rpm_package> <- return this
                   <rpm_package>
        '''
        return self._serializeItem(
            Element("from_%s" % parentTag.replace("_changes","")),
            item
        )

    def _toElement(self, parentTag, item):
        ''' generate a tag with an item serialized in it '''
        return self._serializeItem(
            Element("to_%s" % parentTag.replace("_changes", "")),
            item
        )

    def _addedElement(self, parentTag, item):
        ''' generate a tag with an item serialized in it '''
        return self._serializeItem(
            Element("added_%s" % parentTag.replace("_changes", "")),
            item
        )

    def _removedElement(self, parentTag, item):
        ''' generate a tag with an item serialized in it '''
        return self._serializeItem(
            Element("removed_%s" % parentTag.replace("_changes","")),
            item
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

    def _renderACR(self, parentTag, parentElem, items, mode):
        ''' 
        abstraction around rendering out all the different possible changes
        for a given object type.
        '''
        for x in items:
            change = self._changeElement(parentTag, mode)
            if mode == 'added':
                change.append(self._addedElement(parentTag, x))
            elif mode == 'removed':
                change.append(self._removedElement(parentTag, x))
            elif mode == 'changed':
                (left, right, delta) = x
                change.append(self._fromElement(parentTag, left))
                change.append(self._toElement(parentTag, right))
                change.append(self._diffElement(parentTag, delta))
            parentElem.append(change)

    def _renderAdditions(self, parentTag, parentElem, items):
        ''' 
        render all of what's been added for an object type
        these all go directly under the foo_changes element     
        '''
        self._renderACR(parentTag, parentElem, items, 'added')

    def _renderChanges(self, parentTag, parentElem, items):
        ''' render all of what's been changed (and how) for an object type '''
        self._renderACR(parentTag, parentElem, items, 'changed')
    
    def _renderRemovals(self, parentTag, parentElem, items):
        ''' render all of what's been removed for an object type '''
        self._renderACR(parentTag, parentElem, items, 'removed')

    def render(self):
        ''' return XML representation of survey differences after calling compute '''

        # TODO: don't compare or regenerate if already in DB
        self.differ.compare()

        root = self._renderRoot(self.left, self.right)

        root.append(
            self._renderDiff('rpm_package_changes', self.differ.rpmDiff),
        )
        root.append(
            self._renderDiff('conary_package_changes', self.differ.conaryDiff),
        )
        root.append(
            self._renderDiff('service_changes', self.differ.serviceDiff),
        )

        return parseString(tostring(root)).toprettyxml() 



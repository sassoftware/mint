#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder.inventory import survey_models

class SurveyDiff(object):
    ''' Compare two surveys and return a list or xobj model of their differences '''

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def compare(self):
        ''' Compute survey differences, but don't return XML '''
        self.rpm_diff     = self._compute_rpm_packages()
        self.conary_diff  = self._compute_conary_packages()
        self.service_diff = self._compute_services()

    def _compute_generic(self, collected_items_name, info_name):
        ''' 
        Supporting code behind arbitrary object diffs 
        TODO -- list of fields and values that have changed between them if changed
        '''

        leftItems    = getattr(self.left, collected_items_name).all()
        rightItems   = getattr(self.right, collected_items_name).all()
        leftByName   = dict([ (getattr(x, info_name).name, x) for x in leftItems  ])
        rightByName  = dict([ (getattr(x, info_name).name, x) for x in rightItems ])

        added, removed, changed = ([], [], [])

        for leftItem in leftItems:
            leftInfo  = getattr(leftItem, info_name)
            right     = rightByName.get(leftInfo.name, None)
            if not right:
                removed.append(leftItem)
            else:
                rightInfo = getattr(right, info_name)
                if leftInfo.pk != rightInfo.pk:
                    changed.append((leftItem,right))
 
        for right in rightItems:
            rightInfo = getattr(right, info_name)
            leftItem = leftByName.get(rightInfo.name, None)
            if not leftItem:
                added.append(right)

        return (added, removed, changed)        
    
    def _compute_rpm_packages(self):
        return self._compute_generic('rpm_packages', 'rpm_package_info')

    def _compute_conary_packages(self):
        return self._compute_generic('conary_packages', 'conary_package_info')

    def _compute_services(self):
        return self._compute_generic('services', 'service_info')

    def render(self):
        ''' return XML representation of survey differences after calling compute '''
        return '<wrong></wrong>'


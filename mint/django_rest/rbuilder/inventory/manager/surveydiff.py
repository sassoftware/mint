#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder.inventory import survey_models
#from mint.django_rest.rbuilder.users import models as user_models
#from mint.django_rest.rbuilder.inventory import models as inventory_models
#import datetime

class SurveyDiff(object):

    def __init__(self, left, right):
        self.left = left
        self.right = right

        if type(self.left) == int:
            self.left = survey_models.Survey.objects.get(uuid=self.left)
        if type(self.right) == int:
            self.right = survey_models.Survey.objects.get(uuid=self.right)
       
    def compare(self):
        self.rpm_diff     = self._compute_rpm_packages()
        self.conary_diff  = self._compute_conary_packages()
        self.service_diff = self._compute_services()

    # TODO: make generic so we can reuse w/ conary_packages & services
    def _compute_rpm_packages(self):

        leftItems   = self.left.rpm_packages.all()
        rightItems  = self.right.rpm_packages.all()
        leftByName  = dict([ (x.rpm_package_info.name, x) for x in leftItems  ])
        rightByName = dict([ (x.rpm_package_info.name, x) for x in rightItems ])
        added       = []
        removed     = []
        changed     = []

        for left in leftItems:
            right = rightByName.get(left.rpm_package_info.name, None)
            if not right:
                self.removed.append(left)
            elif left.rpm_package_info.pk != right.rpm_package_info.pk:
                self.changed.append((left,right))
 
        for right in rightItems:
            left = leftByName.get(left.rpm_package_info.name, None)
            if not left:
                self.added.append(right)
        
        return (added, removed, changed)        

    def _compute_conary_packages(self):
        return ([], [], [])

    def _compute_services(self):
        return ([], [], [])
    
    def render(self):
        # TODO: implement
        return '<survey_diff></survey_diff>'


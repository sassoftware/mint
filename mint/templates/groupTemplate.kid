<?xml version='1.0' encoding='UTF-8'?>
<plain xmlns:py="http://purl.org/kid/ns#">
# vim: ts=4 sw=4 expandtab ai

#
# Copyright (c) 2007 rPath, Inc.
# This file is distributed under the terms of the MIT License.
# A copy is available at http://www.rpath.com/permanent/mit-license.html
#

# This is a sample group recipe created automatically by ${cfg.productName}
# Please extend this group with the components you need to create your product.

# APPLIANCE CUSTOMIZATION INSTRUCTIONS

# This group defines what other packages or groups to include in the final
# appliance.  The main modification that will be made to this group is the
# inclusion of additional packages which will be done by adding r.add() commands
# in the setup section below.
#
# In addition, it is possible to call scripts from this group that will be 
# run either before or after updates to perform certain actions on the appliance.
# There is an example of such a script in this group.
#
# This group contains some packages or elements that you may want to remove
# from your final appliance build but which are included here as examples.
#
# Bear in mind this a python syntax file so the sections are delimited by the
# spaces they are indented from the left margin. The default settings at the 
# top of this file configure Vim to deal with spacing correctly.
#
# Sections that will commonly be modified for typical appliance construction
# are marked with the word CUSTOMIZE and a description of what should be
# modified in most cases.

loadSuperClass('group-appliance=${groupApplianceLabel}')
class Group${projectName.title()}(ApplianceGroupRecipe):
    name = '${groupName}'

    # CUSTOMIZE:  VERSION NUMBER
    # Change the version number as needed
    version = '${version}'
    # END CUSTOMIZE

    autoResolve = True

    def setup(r):
        ourLabel = r.macros.get('buildlabel', '')
        rapaLabel = '${rapaLabel}'

        r.macros.coreFlavor = r.groupCoreFlavor

        r.setSearchPath( ourLabel, rapaLabel,
<p py:if="not cfg.rBuilderOnline">            'group-rap-packages=rap.rpath.com@rpath:linux-1[%(coreFlavor)s]' % r.macros,</p>
            'group-os=conary.rpath.com@rpl:1')

        # CUSTOMIZE: LOCKING VERSIONS DOWN
        # To limit the resolution to a specific version replace the end of the
        # setSearchPath with an explicit version and override the 
        # r.groupLabel setting from the superclass as in the following
        # examples:
        # r.setSearchPath('group-os=conary.rpath.com@rpl:1/1.0.7-0.7-3')
        # r.groupLabel='conary.rpath.com@rpl:1/1.0.7-0.7-3'
        # END CUSTOMIZE

        r.addAppliancePlatform()
        r.add('group-raa', rapaLabel)

        # CUSTOMIZE: REMOVE UNWANTED RAPA COMPONENTS
        # To remove plugins that you do not wish to be included in the
        # appliance, but that are included in the default distribution of rAPA,
        # remove them as illustrated below
        r.remove('raa-plugin-flipflop')
        # END CUSTOMIZE

        # CUSTOMIZE: POST UPDATE SCRIPTS
        # This is a script that will execute after the updates
        # for the group are applied to a running system.  This should be 
        # modified to match the needs of your appliance.
        #r.addPostUpdateScript(
        #    contents = '#!/bin/bash\n/sbin/service foundation-config condrestart\n')
        # END CUSTOMIZE


</plain>

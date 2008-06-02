<?xml version='1.0' encoding='UTF-8'?>
<plain xmlns:py="http://purl.org/kid/ns#">
# vim: ts=4 sw=4 expandtab ai
#
# Copyright (c) 2008 rPath, Inc.
# This file is distributed under the terms of the MIT License.
# A copy is available at http://www.rpath.com/permanent/mit-license.html
#
#
# This is a sample group recipe created automatically by rBuilder at rpath.org
# Please extend this group with the components you need to create your product.
#
# APPLIANCE CUSTOMIZATION INSTRUCTIONS
#
# This group defines what other packages or groups to include in the final
# appliance.  The main modification that will be made to this group is the
# inclusion of additional packages which will be done by adding r.add()
# commands in the addPackages() method below.
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

loadSuperClass('group-appliance=conary.rpath.com@rpl:1')
class Group${projectName.capitalize()}Dist(ApplianceGroupRecipe):
    name = '${groupName}'

    # CUSTOMIZE:  VERSION NUMBER
    # This is the version of your appliance
    version = '1'
    # END CUSTOMIZE
    
    def addPackages(r):
        '''
        This is where you can specify the things that make your appliance
        unique.  Some examples of tasks you may wish to perform:
        
        Adding a Package:
           Adding "foundation-config" that is built on the appliance
           label specifically for this appliance (this is the
           core software that defines your appliance):
           r.add('foundation-config')
        
        Replacing a Package:
           Replacing the distro-release package with a customized
           version build specifically for this appliance (this is
           usually not necessary):
           r.replace('distro-release')
        
        Removing Unwanted rAPA Components:
           To remove plugins that you do not wish to be included in the
           appliance, but that are included in the default distribution of rAPA,
           remove them as illustrated below
           r.remove('raa-plugin-flipflop')

        Adding a Post Update Script:
           This is a script that will execute after the updates
           for the group are applied to a running system.  This should be 
           modified to match the needs of your appliance.
           r.addPostUpdateScript(
              contents = '#!/bin/bash\n/sbin/service foundation-config condrestart\n')
        '''

</plain>

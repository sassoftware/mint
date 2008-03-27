#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#

from mint import constants

baseConaryLabel = 'conary.rpath.com@rpl:1'

fallbackTroves = ['anaconda-templates']

labelDict = {baseConaryLabel :
              [('group-appliance-platform',
                'A basic set of packages required for a functional system.'),
               ('group-base', 'Basic but non-essential packages.'),
               ('group-devel', 'Software development tools.'),
               ('group-dist-extras', 'Some assorted extra packages.'),
               ('group-gnome', 'The GNOME desktop environment.'),
               ('group-kde', 'The KDE desktop environment.'),
               ('group-netserver', 'Network servers, tools, and support.'),
               ('group-xorg', 'The X.org windowing system.')
              ]

            }
if constants.rBuilderOnline:
    labelDict.update({
        'raa.rpath.org@rpath:raa-2':
            [('group-raa', 'The rPath Appliance Agent')]
    })

messageDict = {baseConaryLabel: 'These groups come from rPath Linux on the %s label' % baseConaryLabel
              }
if constants.rBuilderOnline:
    messageDict.update({
               'raa.rpath.org@rpath:raa-2': 'The following group comes from the raa.rpath.org@rpath:raa-2 label'
        })

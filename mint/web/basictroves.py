#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#

labelDict = {'conary.rpath.com@rpl:1' :
              [('group-core',
                'A basic set of packages required for a functional system.'),
               ('group-base', 'Basic but non-essential packages.'),
               ('group-devel', 'Software development tools.'),
               ('group-dist-extras', 'Some assorted extra packages.'),
               ('group-gnome', 'The GNOME desktop environment.'),
               ('group-kde', 'The KDE desktop environment.'),
               ('group-netserver', 'Network servers, tools, and support.'),
               ('group-xorg', 'The X.org windowing system.')
              ],

             'raa.rpath.org@rpl:1':
              [('group-raa', 'The rPath Appliance Agent')]
            }

messageDict = {'conary.rpath.com@rpl:1': 'These troves come from rPath Linux on the conary.rpath.com@rpl:1 label',
               'raa.rpath.org@rpl:1': 'The following trove comes from the raa.rpath.org@rpl:1 label'
              }

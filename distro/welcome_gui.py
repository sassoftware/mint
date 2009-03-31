#
# welcome_gui.py: gui welcome screen.
#
# Copyright 2000-2002 Red Hat, Inc.
#
# This software may be freely redistributed under the terms of the GNU
# library public license.
#
# You should have received a copy of the GNU Library Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import gtk
import gui
import autopart

from partitioning import partitionObjectsInitialize

from iw_gui import *
from rhpl.translate import _, N_

class WelcomeWindow (InstallWindow):		

    windowTitle = "" #N_("Welcome")

    def __init__ (self, ics):
        InstallWindow.__init__ (self, ics)
        ics.setGrabNext (1)

    # WelcomeWindow tag="wel"
    def getScreen (self, anaconda):
        # Store a reference to the anaconda object for use elsewhere.
        self.anaconda = anaconda

        # Go ahead and initialize partition objects so that we can display
        # dialogues that mention the correct devices.
        if self.advanced_supported():
            partitionObjectsInitialize(anaconda)
            anaconda.dispatch.skipStep('partitionobjinit')

        # this is a bit ugly... but scale the image if we're not at 800x600
        (w, h) = self.ics.cw.window.get_size_request()
        if w >= 800:
            height = None
            width = None
        else:
            width = 500
            height = 258
        pix = gui.readImageFromFile("splash.png", width, height, dither=False)

        box = gtk.EventBox()
        box.add(pix)

        vbox = gtk.VBox()
        vbox.add(box)

        if self.advanced_supported():
            checkbox = gtk.CheckButton(label='Advanced Mode')
            checkbox.connect('clicked', self.box_checked)
            checkbox.set_active(self.anaconda.id.instClass.in_advanced_mode)
            vbox.add(checkbox)

        return vbox

    def getNext(self):
        # If in advanced mode, need to make sure it is ok to format the system.
        if (self.advanced_supported() and
            not self.anaconda.id.instClass.in_advanced_mode and
            not autopart.queryAutoPartitionOK(self.anaconda)):

            # If not ok to format system, go into advanced mode to allow the
            # user the chance to change partitioning.
            self.anaconda.id.instClass.set_advanced(True, self.anaconda)

    def advanced_supported(self):
        if hasattr(self.anaconda.id.instClass, 'set_advanced'):
            return True
        return False

    def box_checked(self, widget, **kwargs):
        self.anaconda.id.instClass.set_advanced(
            widget.get_active(),
            self.ics.cw.anaconda
        )

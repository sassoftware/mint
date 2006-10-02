# -*- python -*-

# Copyright (C) 1998,1999,2000,2001,2002 by the Free Software Foundation, Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software 
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

"""This module contains your site-specific settings.

From a brand new distribution it should be copied to mm_cfg.py.  If you
already have an mm_cfg.py, be careful to add in only the new settings you
want.  Mailman's installation procedure will never overwrite your mm_cfg.py
file.

The complete set of distributed defaults, with documentation, are in the file
Defaults.py.  In mm_cfg.py, override only those you want to change, after the

  from Defaults import *

line (see below).

Note that these are just default settings; many can be overridden via the
administrator and user interfaces on a per-list or per-user basis.

"""

###############################################
# Here's where we get the distributed defaults.

from Defaults import *
import pwd, grp

##################################################
# Put YOUR site-specific settings below this line.

##############################################################
#    Here's where we override shipped defaults with settings #
#    suitable for the RPM package.                           #
MAILMAN_UID = pwd.getpwnam('mailman')[2]
MAILMAN_GID = grp.getgrnam('mailman')[2]

##############################################################
#    Set URL and email domain names                          #
# 
# Mailman needs to know about (at least) two fully-qualified domain
# names (fqdn)
#
# 1) the hostname used in your urls (DEFAULT_URL_HOST)
# 2) the hostname used in email addresses for your domain (DEFAULT_EMAIL_HOST)
#
# For example, if people visit your Mailman system with
# "http://www.dom.ain/mailman" then your url fqdn is "www.dom.ain",
# and if people send mail to your system via "yourlist@dom.ain" then
# your email fqdn is "dom.ain".  DEFAULT_URL_HOST controls the former,
# and DEFAULT_EMAIL_HOST controls the latter.  Mailman also needs to
# know how to map from one to the other (this is especially important
# if you're running with virtual domains).  You use
# "add_virtualhost(urlfqdn, emailfqdn)" to add new mappings.

# Default to using the FQDN of machine mailman is running on.
# If this is not correct for your installation delete the following 5
# lines that acquire the FQDN and manually edit the hosts instead.

from socket import *
try:
    fqdn = getfqdn()
except:
    fqdn = 'mm_cfg_has_unknown_host_domains'

DEFAULT_URL_HOST   = fqdn
DEFAULT_EMAIL_HOST = fqdn

# Because we've overriden the virtual hosts above add_virtualhost
# MUST be called after they have been defined.

add_virtualhost(DEFAULT_URL_HOST, DEFAULT_EMAIL_HOST)


##############################################################
# Put YOUR site-specific configuration below, in mm_cfg.py . #
# See Defaults.py for explanations of the values.	     #

# Almost all the colors used in Mailman's web interface are parameterized via
# the following variables.  This lets you easily change the color schemes for
# your preferences without having to do major surgery on the source code.
# Note that in general, the template colors are not included here since it is
# easy enough to override the default template colors via site-wide,
# vdomain-wide, or list-wide specializations.

WEB_BG_COLOR = 'white'                            # Page background
WEB_HEADER_COLOR = '#99ccff'                      # Major section headers
WEB_SUBHEADER_COLOR = '#fff0d0'                   # Minor section headers
WEB_ADMINITEM_COLOR = '#dddddd'                   # Option field background
WEB_ADMINPW_COLOR = '#99cccc'                     # Password box color
WEB_ERROR_COLOR = 'red'                           # Error message foreground
WEB_LINK_COLOR = ''                               # If true, forces LINK=
WEB_ALINK_COLOR = ''                              # If true, forces ALINK=
WEB_VLINK_COLOR = ''                              # If true, forces VLINK=
WEB_HIGHLIGHT_COLOR = '#dddddd'                   # If true, alternating rows
                                                  # in listinfo & admin display


# MTA should name a module in Mailman/MTA which provides the MTA specific
# functionality for creating and removing lists.  Some MTAs like Exim can be
# configured to automatically recognize new lists, in which case the MTA
# variable should be set to None.  Use 'Manual' to print new aliases to
# standard out (or send an email to the site list owner) for manual twiddling
# of an /etc/aliases style file.  Use 'Postfix' if you are using the Postfix
# MTA -- but then also see POSTFIX_STYLE_VIRTUAL_DOMAINS.
#MTA = 'Postfix'

DEFAULT_LIST_ADVERTISED = Yes
DEFAULT_MAX_NUM_RECIPIENTS = 10
DEFAULT_MAX_MESSAGE_SIZE = 100

OLD_STYLE_PREFIXING = No

DEFAULT_FORWARD_AUTO_DISCARDS = No

# Private_roster == 0: anyone can see, 1: members only, 2: admin only.
DEFAULT_PRIVATE_ROSTER = 2

# SUBSCRIBE POLICY
# 0 - open list (only when ALLOW_OPEN_SUBSCRIBE is set to 1) **
# 1 - confirmation required for subscribes
DEFAULT_SUBSCRIBE_POLICY = 1

# Defaults for content filtering on mailing lists.  DEFAULT_FILTER_CONTENT is
# a flag which if set to true, turns on content filtering.
DEFAULT_FILTER_CONTENT = Yes

# DEFAULT_PASS_MIME_TYPES is a list of MIME types to be passed through.
# Format is the same as DEFAULT_FILTER_MIME_TYPES
DEFAULT_PASS_MIME_TYPES = ['multipart/mixed',
                           'multipart/alternative',
                           'multipart/signed',
                           'text/plain',
                           'text/xml',
                           'text/html',
                           'text/x-sh',
                           'text/x-csh',
                           'text/x-ksh',
                           'text/x-zsh',
                           'text/x-perl',
                           'text/x-python',
                           'text/x-patch',
                           'text/vcard',
                           'message/rfc822',
                           'application/pgp-signature',
                           'application/pdf',
                           'application/rtf',
                           'application/x-gzip',
                           'application/x-bzip',
                           'application/postscript' ] 

# RFC 2369 defines List-* headers which are added to every message sent
# through to the mailing list membership.  These are a very useful aid to end
# users and should always be added.  However, not all MUAs are compliant and
# if a list's membership has many such users, they may clamor for these
# headers to be suppressed.  By setting this variable to Yes, list owners will
# be given the option to suppress these headers.  By setting it to No, list
# owners will not be given the option to suppress these headers (although some
# header suppression may still take place, i.e. for announce-only lists, or
# lists with no archives).
ALLOW_RFC2369_OVERRIDES = Yes


# Note - if you're looking for something that is imported from mm_cfg, but you
# didn't find it above, it's probably in Defaults.py.

#
# Copyright (c) 2011 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

users_post_xml = \
"""
<user>
<full_name>Dan Cohn</full_name>
<display_email>True</display_email>
<passwd>12345</passwd>
<user_name>dcohn</user_name>
<time_accessed>1283530322.49</time_accessed>
<time_created>1283523987.85</time_created>
<active>1</active>
<email>dcohn@rpath.com</email>
<blurb>something here</blurb>
</user>
""".strip()


users_put_xml = \
"""
<user>
<full_name>Super Devil</full_name>
<blurb>fear me</blurb>
</user>
""".strip()

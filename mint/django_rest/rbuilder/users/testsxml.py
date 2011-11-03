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
<display_email>true</display_email>
<password>12345</password>
<user_name>dcohn</user_name>
<time_accessed>1283530322.49</time_accessed>
<time_created>1283523987.85</time_created>
<active>1</active>
<email>dcohn@rpath.com</email>
<blurb>something here</blurb>
<is_admin>true</is_admin>
</user>
""".strip()

users_post_xml_can_create = \
"""
<user>
<user_name>cancreatestuff</user_name>
<full_name>Ima UserWhoCanCreate</full_name>
<display_email>true</display_email>
<password>12345</password>
<active>1</active>
<email>cancreatestuff@example.com</email>
<blurb>...</blurb>
<is_admin>0</is_admin>
<can_create>true</can_create>
</user>
"""

users_put_xml = \
"""
<user>
<full_name>Changed Full Name</full_name>
<blurb>fear me</blurb>
</user>
""".strip()

user_update_password = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<user>
  <modified_date>1316699037.18</modified_date>
  <user_id>2004</user_id>
  <display_email></display_email>
  <roles id="http://testserver/api/v1/users/2004/roles"/>
  <is_admin>true</is_admin>
  <full_name>Jim Phoo</full_name>
  <created_date>1316699037.18</created_date>
  <user_name>jphoo</user_name>
  <email>jphoo@noreply.com</email>
  <password>%s</password>
  <blurb></blurb>
</user>
""".strip()

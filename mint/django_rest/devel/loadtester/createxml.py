#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


createRole = """
<role>
   <name>%(name)s</name>
   <description>%(name)s</description>
</role>
"""

createQuerySet = """
<query_set>
  <filter_entries>
  </filter_entries>
  <children/>
  <name>%(name)s</name>
  <resource_type>%(resourceType)s</resource_type>
  <description>%(name)s</description>
</query_set>
"""

createGrant = """
<grant>
  <permission id="http://testserver/api/v1/rbac/permissions/%(permissionId)s"/>
  <queryset id="http://testserver/api/v1/query_sets/%(querySetId)s"/>
  <role id="http://testserver/api/v1/rbac/roles/%(roleId)s"/>
</grant>
"""

createUser = """
<user>
   <user_name>%(name)s</user_name>
   <full_name>%(name)s</full_name>
   <display_email>true</display_email>
   <password>12345</password>
   <active>1</active>
   <email>testuser@rpath.com</email>
   <blurb>...</blurb>
   <is_admin>0</is_admin>
   <can_create>true</can_create>
</user>
"""

addUserToRole = """
<user id="https://127.0.0.1/api/v1/users/%(userId)s"/>
"""

# not used, to avoid lots of seperate postgresql databases
# though we need to test that too
createProjectNonExternal = """
  <project>
    <commit_email>nospam@rpath.com</commit_email>
    <project_url>http://</project_url>
    <disabled>0</disabled>
    <isAppliance>1</isAppliance>
    <short_name>%(name)s</short_name>
    <hostname>%(name)s</hostname>
    <namespace>rpath</namespace>
    <domain_name>eng.rpath.com</domain_name>
    <hidden>false</hidden>
    <description>%(name)s description</description>
    <backup_external>0</backup_external>
    <repository_hostname>%(name)s</repository_hostname>
    <external>false</external>
    <name>%(name)s</name>
  </project>
"""

createProject = """
  <project>
    <project_url>http://</project_url>
    <short_name>%(name)s</short_name>
    <hostname>%(name)s</hostname>
    <namespace>rpath</namespace>
    <domain_name>eng.rpath.com</domain_name>
    <hidden>false</hidden>
    <description>test project description</description>
    <external>true</external>
    <name>%(name)s</name>
    <auth_type>userpass</auth_type>
    <entitlement/>
    <upstream_url>https://rb.rpath.com/repos/rwbs/browse</upstream_url>
    <label>rwbs.rb.rpath.com@rpath:rwbs-1-devel</label>
    <password>somepassword</password>
    <user_name>someuser</user_name>
  </project>
"""

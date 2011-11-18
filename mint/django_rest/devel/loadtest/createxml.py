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


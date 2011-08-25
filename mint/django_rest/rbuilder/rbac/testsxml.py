# createa  system placeholder queryset
datacenter_xml = """
<query_set>
    <name>datacenter</name>
    <resource_type>system</resource_type>
    <filter_entries/>
</query_set>
"""

user_post_xml = """
<user>
<full_name>%s</full_name>
<display_email>True</display_email>
<password>password</password>
<user_name>%s</user_name>
<time_accessed>1283530322.49</time_accessed>
<time_created>1283523987.85</time_created>
<active>1</active>
<email>email@example.com</email>
<blurb>something here</blurb>
<is_admin>%s</is_admin>
</user>
"""

user_get_xml_with_roles = """
<user id="http://testserver/api/v1/users/2003">
  <blurb>something here</blurb>
  <display_email>True</display_email>
  <email>email@example.com</email>
  <full_name>ExampleIntern</full_name>
  <is_admin>false</is_admin>
  <rbac_user_roles>
    <rbac_user_role id="/api/v1/rbac/users/2003/roles/intern">
      <rbac_user_role_id>3</rbac_user_role_id>
      <role id="http://testserver/api/v1/rbac/roles/intern"/>
      <user id="http://testserver/api/v1/users/2003"/>
    </rbac_user_role>
  </rbac_user_roles>
  <user_groups/>
  <user_id>2003</user_id>
  <user_name>ExampleIntern</user_name>
</user>
"""

# create a lab placeholder queryset
lab_xml = """
<query_set>
    <name>lab</name>
    <resource_type>system</resource_type>
    <filter_entries/>
</query_set>
"""

# create a tradingfloor placeholder queryset
tradingfloor_xml = """
<query_set>
    <name>tradingfloor</name>
    <resource_type>system</resource_type>
    <filter_entries/>
</query_set>
"""


role_put_xml_input = """
<rbac_role id="http://testserver/api/v1/rbac/roles/rocketsurgeon">
   <permissions/>
   <role_id>rocketsurgeon</role_id>
</rbac_role>
"""

# TODO, ID should come back on this element
role_put_xml_output = """
<rbac_role id="http://testserver/api/v1/rbac/roles/rocketsurgeon">
   <permissions/>
   <role_id>rocketsurgeon</role_id>
</rbac_role>
"""

role_list_xml = """
<rbac_roles count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <rbac_role id="http://testserver/api/v1/rbac/roles/sysadmin">
    <permissions/>
    <role_id>sysadmin</role_id>
  </rbac_role>
  <rbac_role id="http://testserver/api/v1/rbac/roles/developer">
    <permissions/>
    <role_id>developer</role_id>
  </rbac_role>
  <rbac_role id="http://testserver/api/v1/rbac/roles/intern">
    <permissions/>
    <role_id>intern</role_id>
  </rbac_role>
</rbac_roles>
"""

role_get_xml = """
<rbac_role id="http://testserver/api/v1/rbac/roles/developer">
  <permissions/>
  <role_id>developer</role_id>
</rbac_role>
"""

permission_list_xml = """
<rbac_permissions count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/permissions" id="http://testserver/api/v1/rbac/permissions;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <rbac_permission id="http://testserver/api/v1/rbac/permissions/1">
    <permission_id>1</permission_id>
    <action>wmember</action>
    <queryset id="http://testserver/api/v1/query_sets/14"/>
    <rbac_role id="http://testserver/api/v1/rbac/roles/sysadmin"/>
  </rbac_permission>
  <rbac_permission id="http://testserver/api/v1/rbac/permissions/2">
    <action>rmember</action>
    <queryset id="http://testserver/api/v1/query_sets/14"/>
    <permission_id>2</permission_id>
    <rbac_role id="http://testserver/api/v1/rbac/roles/developer"/>
  </rbac_permission>
  <rbac_permission id="http://testserver/api/v1/rbac/permissions/3">
    <action>wmember</action>
    <queryset id="http://testserver/api/v1/query_sets/13"/>
    <permission_id>3</permission_id>
    <rbac_role id="http://testserver/api/v1/rbac/roles/developer"/>
  </rbac_permission>
</rbac_permissions>
"""

permission_get_xml = """
<rbac_permission id="http://testserver/api/v1/rbac/permissions/1">
  <action>wmember</action>
  <permission_id>1</permission_id>
  <queryset id="http://testserver/api/v1/query_sets/14"/>
  <rbac_role id="http://testserver/api/v1/rbac/roles/sysadmin"/>
</rbac_permission>
"""

permission_post_xml_input="""
<rbac_permission>
  <action>wmember</action>
  <queryset id="http://testserver/api/v1/query_sets/12"/>
  <rbac_role id="http://testserver/api/v1/rbac/roles/intern"/>
</rbac_permission>
"""

permission_post_xml_output="""
<rbac_permission id="http://testserver/api/v1/rbac/permissions/4">
  <action>wmember</action>
  <queryset id="http://testserver/api/v1/query_sets/12"/>
  <permission_id>4</permission_id>
  <rbac_role id="http://testserver/api/v1/rbac/roles/intern"/>
</rbac_permission>
"""

permission_put_xml_input="""
<rbac_permission id="http://testserver/api/v1/rbac/permissions/1">
  <action>wmember</action>
  <queryset id="http://testserver/api/v1/query_sets/14"/>
  <rbac_role id="http://testserver/api/v1/rbac/roles/intern"/>
</rbac_permission>
"""

permission_put_xml_output="""
 <rbac_permission id="http://testserver/api/v1/rbac/permissions/1">
   <action>wmember</action>
   <permission_id>1</permission_id>
   <queryset id="http://testserver/api/v1/query_sets/14"/>
   <rbac_role id="http://testserver/api/v1/rbac/roles/intern"/>
 </rbac_permission>
"""

user_role_list_xml = """
<rbac_roles count="2" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/v1/rbac/roles" end_index="1" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" start_index="0">
  <rbac_role id="http://testserver/api/v1/rbac/roles/developer">
    <permissions/>
    <role_id>developer</role_id>
  </rbac_role>
  <rbac_role id="http://testserver/api/v1/rbac/roles/sysadmin">
    <permissions/>
    <role_id>sysadmin</role_id>
  </rbac_role>
</rbac_roles>
"""

user_role_get_xml = """
<rbac_role id="http://testserver/api/v1/rbac/roles/developer">
  <permissions/>
  <role_id>developer</role_id>
</rbac_role>
"""

user_role_post_xml_input = """
<rbac_role id="http://testserver/api/v1/rbac/roles/intern">
  <permissions/>
  <role_id>intern</role_id>
</rbac_role>
"""

user_role_post_xml_output = """
<rbac_role id="http://testserver/api/v1/rbac/roles/intern">
  <permissions/>
  <role_id>intern</role_id>
</rbac_role>
"""

user_role_get_list_xml_after_delete = """
<rbac_roles count="1" end_index="0" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <rbac_role id="http://testserver/api/v1/rbac/roles/sysadmin">
    <permissions/>
    <role_id>sysadmin</role_id>
  </rbac_role>
</rbac_roles>
"""


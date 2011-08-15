# createa  system placeholder queryset
datacenter_xml = """
<query_set>
    <name>datacenter</name>
    <resource_type>system</resource_type>
    <filter_entries/>
</query_set>
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
   <role_id>rocketsurgeon</role_id>
</rbac_role>
"""

# TODO, ID should come back on this element
role_put_xml_output = """
<rbac_role id="http://testserver/api/v1/rbac/roles/rocketsurgeon">
   <role_id>rocketsurgeon</role_id>
</rbac_role>
"""

role_list_xml = """
<rbac_roles count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <rbac_role id="http://testserver/api/v1/rbac/roles/sysadmin">
    <role_id>sysadmin</role_id>
  </rbac_role>
  <rbac_role id="http://testserver/api/v1/rbac/roles/developer">
    <role_id>developer</role_id>
  </rbac_role>
  <rbac_role id="http://testserver/api/v1/rbac/roles/intern">
    <role_id>intern</role_id>
  </rbac_role>
</rbac_roles>
"""

role_get_xml = """
<rbac_role id="http://testserver/api/v1/rbac/roles/developer">
  <role_id>developer</role_id>
</rbac_role>
"""

permission_list_xml = """
<rbac_permissions count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/permissions" id="http://testserver/api/v1/rbac/permissions;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <rbac_permission id="http://testserver/api/v1/rbac/permissions/1">
    <permission_id>1</permission_id>
    <action>write</action>
    <queryset id="http://testserver/api/v1/query_sets/14"/>
    <rbac_role id="http://testserver/api/v1/rbac/roles/sysadmin"/>
  </rbac_permission>
  <rbac_permission id="http://testserver/api/v1/rbac/permissions/2">
    <action>read</action>
    <queryset id="http://testserver/api/v1/query_sets/14"/>
    <permission_id>2</permission_id>
    <rbac_role id="http://testserver/api/v1/rbac/roles/developer"/>
  </rbac_permission>
  <rbac_permission id="http://testserver/api/v1/rbac/permissions/3">
    <action>write</action>
    <queryset id="http://testserver/api/v1/query_sets/13"/>
    <permission_id>3</permission_id>
    <rbac_role id="http://testserver/api/v1/rbac/roles/developer"/>
  </rbac_permission>
</rbac_permissions>
"""

permission_get_xml = """
<rbac_permission id="http://testserver/api/v1/rbac/permissions/1">
  <action>write</action>
  <permission_id>1</permission_id>
  <queryset id="http://testserver/api/v1/query_sets/14"/>
  <rbac_role id="http://testserver/api/v1/rbac/roles/sysadmin"/>
</rbac_permission>
"""

permission_post_xml_input="""
<rbac_permission>
  <action>write</action>
  <queryset id="http://testserver/api/v1/query_sets/12"/>
  <rbac_role id="http://testserver/api/v1/rbac/roles/intern"/>
</rbac_permission>
"""

permission_post_xml_output="""
<rbac_permission id="http://testserver/api/v1/rbac/permissions/4">
  <action>write</action>
  <queryset id="http://testserver/api/v1/query_sets/12"/>
  <permission_id>4</permission_id>
  <rbac_role id="http://testserver/api/v1/rbac/roles/intern"/>
</rbac_permission>
"""

permission_put_xml_input="""
<rbac_permission id="http://testserver/api/v1/rbac/permissions/1">
  <action>write</action>
  <queryset id="http://testserver/api/v1/query_sets/14"/>
  <rbac_role id="http://testserver/api/v1/rbac/roles/intern"/>
</rbac_permission>
"""

permission_put_xml_output="""
 <rbac_permission id="http://testserver/api/v1/rbac/permissions/1">
   <action>write</action>
   <permission_id>1</permission_id>
   <queryset id="http://testserver/api/v1/query_sets/14"/>
   <rbac_role id="http://testserver/api/v1/rbac/roles/intern"/>
 </rbac_permission>
"""

user_role_list_xml = """
<rbac_roles count="2" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/v1/rbac/roles" end_index="1" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" start_index="0">
  <rbac_role id="http://testserver/api/v1/rbac/roles/sysadmin">
    <role_id>sysadmin</role_id>
  </rbac_role>
  <rbac_role id="http://testserver/api/v1/rbac/roles/developer">
    <role_id>developer</role_id>
  </rbac_role>
</rbac_roles>
"""

user_role_get_xml = """
<rbac_role id="http://testserver/api/v1/rbac/roles/developer">
  <role_id>developer</role_id>
</rbac_role>
"""

user_role_post_xml_input = """
<rbac_role id="http://testserver/api/v1/rbac/roles/intern">
  <role_id>intern</role_id>
</rbac_role>
"""

user_role_post_xml_output = """
<rbac_role id="http://testserver/api/v1/rbac/roles/intern">
  <role_id>intern</role_id>
</rbac_role>
"""

user_role_get_list_xml_after_delete = """
<rbac_roles count="1" end_index="0" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <rbac_role id="http://testserver/api/v1/rbac/roles/sysadmin">
    <role_id>sysadmin</role_id>
  </rbac_role>
</rbac_roles>
"""


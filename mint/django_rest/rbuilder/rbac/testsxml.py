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

context_put_xml_input = """
<rbac_context id="http://testserver/api/v1/rbac/contexts/datacenter2">
   <context_id>datacenter2</context_id>
</rbac_context>
"""

context_put_xml_output = """
<rbac_context id="http://testserver/api/v1/rbac/contexts/datacenter2">
   <context_id>datacenter2</context_id>
</rbac_context>
"""

context_list_xml = """
<rbac_contexts count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/contexts" id="http://testserver/api/v1/rbac/contexts;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <rbac_context id="http://testserver/api/v1/rbac/contexts/datacenter">
    <context_id>datacenter</context_id>
  </rbac_context>
  <rbac_context id="http://testserver/api/v1/rbac/contexts/lab">
    <context_id>lab</context_id>
  </rbac_context>
  <rbac_context id="http://testserver/api/v1/rbac/contexts/tradingfloor">
    <context_id>tradingfloor</context_id>
  </rbac_context>
</rbac_contexts>
"""

context_get_xml = """
<rbac_context id="http://testserver/api/v1/rbac/contexts/datacenter">
  <context_id>datacenter</context_id>
</rbac_context>
"""

permission_list_xml = """
<rbac_permissions count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/permissions" id="http://testserver/api/v1/rbac/permissions;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <rbac_permission id="http://testserver/api/v1/rbac/permissions/1">
    <action>write</action>
    <permission_id>1</permission_id>
    <rbac_context id="http://testserver/api/v1/rbac/contexts/datacenter"/>
    <rbac_role id="http://testserver/api/v1/rbac/roles/sysadmin"/>
  </rbac_permission>
  <rbac_permission id="http://testserver/api/v1/rbac/permissions/2">
    <action>read</action>
    <permission_id>2</permission_id>
    <rbac_context id="http://testserver/api/v1/rbac/contexts/datacenter"/>
    <rbac_role id="http://testserver/api/v1/rbac/roles/developer"/>
  </rbac_permission>
  <rbac_permission id="http://testserver/api/v1/rbac/permissions/3">
    <action>write</action>
    <permission_id>3</permission_id>
    <rbac_context id="http://testserver/api/v1/rbac/contexts/lab"/>
    <rbac_role id="http://testserver/api/v1/rbac/roles/developer"/>
  </rbac_permission>
</rbac_permissions>
"""

permission_get_xml = """
<rbac_permission id="http://testserver/api/v1/rbac/permissions/1">
  <action>write</action>
  <permission_id>1</permission_id>
  <rbac_context id="http://testserver/api/v1/rbac/contexts/datacenter"/>
  <rbac_role id="http://testserver/api/v1/rbac/roles/sysadmin"/>
</rbac_permission>
"""

permission_post_xml_input="""
<rbac_permission>
  <action>write</action>
  <rbac_context id="http://testserver/api/v1/rbac/contexts/tradingfloor"/>
  <rbac_role id="http://testserver/api/v1/rbac/roles/intern"/>
</rbac_permission>
"""

permission_post_xml_output="""
<rbac_permission id="http://testserver/api/v1/rbac/permissions/4">
  <action>write</action>
  <permission_id>4</permission_id>
  <rbac_context id="http://testserver/api/v1/rbac/contexts/tradingfloor"/>
  <rbac_role id="http://testserver/api/v1/rbac/roles/intern"/>
</rbac_permission>
"""

permission_put_xml_input="""
<rbac_permission id="http://testserver/api/v1/rbac/permissions/1">
  <action>write</action>
  <rbac_context id="http://testserver/api/v1/rbac/contexts/tradingfloor"/>
  <rbac_role id="http://testserver/api/v1/rbac/roles/intern"/>
</rbac_permission>
"""

permission_put_xml_output="""
<rbac_permission id="http://testserver/api/v1/rbac/permissions/1">
  <action>write</action>
  <permission_id>1</permission_id>
  <rbac_context id="http://testserver/api/v1/rbac/contexts/tradingfloor"/>
  <rbac_role id="http://testserver/api/v1/rbac/roles/intern"/>
</rbac_permission>
"""
